#!/usr/bin/env python3
"""Build ODOSv5 Patreon tier folders from generated PNG assets.

This script assembles PDFs by embedding existing PNG pages. It does not render,
typeset, redraw, or screenshot packet pages.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import struct
import zlib
from pathlib import Path
from datetime import datetime, timezone
from zipfile import ZIP_DEFLATED, ZipFile


TIERS = ("basic", "deluxe", "premium")
TIER_LABELS = {"basic": "Basic", "deluxe": "Deluxe", "premium": "Premium"}
PAGE_ROLES = {"cover", "core_page", "appendix_page"}


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def desktop_path() -> Path:
    candidates = []
    if os.environ.get("OneDrive"):
        candidates.append(Path(os.environ["OneDrive"]) / "Desktop")
    candidates.extend([Path.home() / "OneDrive" / "Desktop", Path.home() / "Desktop"])
    for candidate in candidates:
        if candidate.is_dir():
            return candidate
    raise SystemExit("Cannot locate the actual Desktop folder, including OneDrive redirection.")


def publish_desktop_archives(packet_dir: Path, title: str, run: dict) -> Path:
    target = desktop_path() / "New Adventures" / title
    resolved_parent = (desktop_path() / "New Adventures").resolve()
    if target.resolve().parent != resolved_parent:
        raise SystemExit(f"Unsafe Desktop export target: {target}")
    if target.exists():
        shutil.rmtree(target)
    target.mkdir(parents=True)
    for tier in TIERS:
        archive = packet_dir / f"{title} - {TIER_LABELS[tier]}.zip"
        if not archive.is_file():
            raise SystemExit(f"Finished tier archive is missing: {archive}")
        shutil.copy2(archive, target / archive.name)
    (target / "Ready.txt").write_text(
        f"Ready {now()} - ODOSv5.1 run {run['run_id']}\n",
        encoding="ascii",
    )
    return target


def write_json_atomic(path: Path, data: dict) -> None:
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    os.replace(tmp, path)


def clean_name(value: str) -> str:
    value = re.sub(r'[<>:"/\\|?*]', "-", value).strip()
    value = re.sub(r"\s+", " ", value)
    return value or "ODOS Packet"


def read_map(packet_dir: Path) -> dict:
    map_path = packet_dir / "distribution-map.json"
    if not map_path.exists():
        raise SystemExit(f"Missing distribution map: {map_path}")
    data = json.loads(map_path.read_text(encoding="utf-8-sig"))
    if not data.get("title") or not isinstance(data.get("items"), list):
        raise SystemExit("distribution-map.json must contain title and items[]")
    return data


def tier_list(item: dict) -> set[str]:
    return {str(t).lower() for t in item.get("tiers", [])}


def item_path(packet_dir: Path, item: dict) -> Path:
    source = item.get("source")
    if not source:
        raise SystemExit(f"Map item lacks source: {item}")
    path = packet_dir / source
    if not path.exists():
        raise SystemExit(f"Mapped source does not exist: {path}")
    return path


def load_locked_state(packet_dir: Path, data: dict) -> tuple[dict, dict, dict]:
    required = {
        "manifest": packet_dir / "manifest.json",
        "run": packet_dir / "run-state.json",
        "assets": packet_dir / "asset-status.json",
    }
    missing = [str(path) for path in required.values() if not path.exists()]
    if missing:
        raise SystemExit("Locked packaging requires state files: " + ", ".join(missing))
    manifest = json.loads(required["manifest"].read_text(encoding="utf-8-sig"))
    run = json.loads(required["run"].read_text(encoding="utf-8-sig"))
    assets = json.loads(required["assets"].read_text(encoding="utf-8-sig"))
    if manifest.get("status") not in {"approved", "packaged"}:
        raise SystemExit(f"Manifest must be approved before packaging; status is {manifest.get('status')}")
    if run.get("status") not in {"approved", "packaged"}:
        raise SystemExit(f"Run must be approved before packaging; status is {run.get('status')}")
    unapproved = [name for name, status in run.get("gates", {}).items() if status != "approved"]
    if unapproved:
        raise SystemExit("Packaging blocked by gates: " + ", ".join(unapproved))
    records = assets.get("assets", {})
    for item in data["items"]:
        source = item.get("source")
        record = records.get(source)
        if not record:
            raise SystemExit(f"Mapped source lacks asset-status record: {source}")
        if record.get("status") != "approved" or not record.get("current"):
            raise SystemExit(f"Mapped source is not approved/current: {source}")
        for key, revision in record.get("dependency_revisions", {}).items():
            if run.get("revisions", {}).get(key) != revision:
                raise SystemExit(f"Mapped source is stale for {key}: {source}")
        path = item_path(packet_dir, item)
        actual_hash = sha256(path)
        if actual_hash != record.get("output_sha256"):
            raise SystemExit(f"Mapped source hash changed after approval: {source}")
    return manifest, run, assets


def display_name(item: dict) -> str:
    name = item.get("display_name") or item.get("source")
    return clean_name(str(name))


def tier_subdir(tier: str, item: dict) -> str | None:
    role = item.get("role")
    if role == "cover" or role == "core_page":
        return "PNG Pages"
    if role == "appendix_page":
        return "Appendix Pages" if tier == "premium" else None
    if role == "battle_map":
        return "Battle Maps"
    if role == "token":
        return "Tokens"
    return None


def copy_tier_files(packet_dir: Path, dist_dir: Path, data: dict, asset_state: dict) -> dict:
    manifests: dict[str, list[dict]] = {tier: [] for tier in TIERS}
    for item in data["items"]:
        src = item_path(packet_dir, item)
        for tier in TIERS:
            if tier not in tier_list(item):
                continue
            subdir = tier_subdir(tier, item)
            if not subdir:
                continue
            dst_dir = dist_dir / TIER_LABELS[tier] / subdir
            dst_dir.mkdir(parents=True, exist_ok=True)
            dst = dst_dir / display_name(item)
            shutil.copy2(src, dst)
            manifests[tier].append(
                {
                    "source": item["source"],
                    "source_sha256": asset_state["assets"][item["source"]]["output_sha256"],
                    "prompt_sha256": asset_state["assets"][item["source"]].get("attempts", [{}])[-1].get("prompt_sha256"),
                    "dependency_revisions": asset_state["assets"][item["source"]].get("dependency_revisions", {}),
                    "file": str(dst.relative_to(dist_dir / TIER_LABELS[tier])),
                    "role": item.get("role"),
                    "pdf_order": item.get("pdf_order"),
                }
            )
    return manifests


def parse_png(path: Path) -> dict:
    data = path.read_bytes()
    if not data.startswith(b"\x89PNG\r\n\x1a\n"):
        raise SystemExit(f"Not a PNG: {path}")
    pos = 8
    width = height = bit_depth = color_type = None
    idat = []
    while pos < len(data):
        length = struct.unpack(">I", data[pos : pos + 4])[0]
        kind = data[pos + 4 : pos + 8]
        chunk = data[pos + 8 : pos + 8 + length]
        pos += 12 + length
        if kind == b"IHDR":
            width, height, bit_depth, color_type = struct.unpack(">IIBB", chunk[:10])
        elif kind == b"IDAT":
            idat.append(chunk)
        elif kind == b"IEND":
            break
    if width is None or height is None or bit_depth != 8:
        raise SystemExit(f"Unsupported PNG header: {path}")
    return {
        "path": path,
        "width": width,
        "height": height,
        "bit_depth": bit_depth,
        "color_type": color_type,
        "idat": b"".join(idat),
    }


def paeth(a: int, b: int, c: int) -> int:
    p = a + b - c
    pa = abs(p - a)
    pb = abs(p - b)
    pc = abs(p - c)
    if pa <= pb and pa <= pc:
        return a
    if pb <= pc:
        return b
    return c


def unfilter_png(raw: bytes, width: int, height: int, channels: int) -> list[bytearray]:
    bpp = channels
    stride = width * channels
    rows: list[bytearray] = []
    pos = 0
    prev = bytearray(stride)
    for _ in range(height):
        filter_type = raw[pos]
        pos += 1
        row = bytearray(raw[pos : pos + stride])
        pos += stride
        for i in range(stride):
            left = row[i - bpp] if i >= bpp else 0
            up = prev[i]
            upper_left = prev[i - bpp] if i >= bpp else 0
            if filter_type == 1:
                row[i] = (row[i] + left) & 255
            elif filter_type == 2:
                row[i] = (row[i] + up) & 255
            elif filter_type == 3:
                row[i] = (row[i] + ((left + up) // 2)) & 255
            elif filter_type == 4:
                row[i] = (row[i] + paeth(left, up, upper_left)) & 255
            elif filter_type != 0:
                raise SystemExit(f"Unsupported PNG filter: {filter_type}")
        rows.append(row)
        prev = row
    return rows


def pdf_image_stream(png: dict) -> tuple[bytes, int, int]:
    color_type = png["color_type"]
    if color_type == 2:
        params = (
            f"<< /Predictor 15 /Colors 3 /BitsPerComponent 8 /Columns {png['width']} >>"
        )
        image = (
            f"<< /Type /XObject /Subtype /Image /Width {png['width']} "
            f"/Height {png['height']} /ColorSpace /DeviceRGB /BitsPerComponent 8 "
            f"/Filter /FlateDecode /DecodeParms {params} /Length {len(png['idat'])} >>\n"
        ).encode("ascii")
        return image + b"stream\n" + png["idat"] + b"\nendstream", png["width"], png["height"]
    if color_type == 6:
        raw = zlib.decompress(png["idat"])
        rows = unfilter_png(raw, png["width"], png["height"], 4)
        out = bytearray()
        for row in rows:
            out.append(0)
            for i in range(0, len(row), 4):
                r, g, b, a = row[i], row[i + 1], row[i + 2], row[i + 3]
                alpha = a / 255
                out.extend(
                    (
                        int(r * alpha + 255 * (1 - alpha)),
                        int(g * alpha + 255 * (1 - alpha)),
                        int(b * alpha + 255 * (1 - alpha)),
                    )
                )
        comp = zlib.compress(bytes(out), 9)
        params = (
            f"<< /Predictor 15 /Colors 3 /BitsPerComponent 8 /Columns {png['width']} >>"
        )
        image = (
            f"<< /Type /XObject /Subtype /Image /Width {png['width']} "
            f"/Height {png['height']} /ColorSpace /DeviceRGB /BitsPerComponent 8 "
            f"/Filter /FlateDecode /DecodeParms {params} /Length {len(comp)} >>\n"
        ).encode("ascii")
        return image + b"stream\n" + comp + b"\nendstream", png["width"], png["height"]
    raise SystemExit(f"Unsupported PNG color type {color_type}: {png['path']}")


def write_pdf(pdf_path: Path, page_paths: list[Path]) -> None:
    objects: list[bytes] = []
    page_refs: list[int] = []
    catalog_ref = 1
    pages_ref = 2
    objects.extend([b"", b""])
    for page_path in page_paths:
        image_obj, width, height = pdf_image_stream(parse_png(page_path))
        image_ref = len(objects) + 1
        objects.append(image_obj)
        content = f"q {width} 0 0 {height} 0 0 cm /Im0 Do Q\n".encode("ascii")
        content_ref = len(objects) + 1
        objects.append(
            f"<< /Length {len(content)} >>\n".encode("ascii")
            + b"stream\n"
            + content
            + b"endstream"
        )
        page_ref = len(objects) + 1
        page_refs.append(page_ref)
        objects.append(
            f"<< /Type /Page /Parent {pages_ref} 0 R /MediaBox [0 0 {width} {height}] "
            f"/Resources << /XObject << /Im0 {image_ref} 0 R >> >> "
            f"/Contents {content_ref} 0 R >>".encode("ascii")
        )
    kids = " ".join(f"{ref} 0 R" for ref in page_refs)
    objects[catalog_ref - 1] = f"<< /Type /Catalog /Pages {pages_ref} 0 R >>".encode("ascii")
    objects[pages_ref - 1] = (
        f"<< /Type /Pages /Kids [{kids}] /Count {len(page_refs)} >>".encode("ascii")
    )
    pdf = bytearray(b"%PDF-1.4\n%\xe2\xe3\xcf\xd3\n")
    offsets = [0]
    for idx, obj in enumerate(objects, start=1):
        offsets.append(len(pdf))
        pdf.extend(f"{idx} 0 obj\n".encode("ascii"))
        pdf.extend(obj)
        pdf.extend(b"\nendobj\n")
    xref = len(pdf)
    pdf.extend(f"xref\n0 {len(objects) + 1}\n".encode("ascii"))
    pdf.extend(b"0000000000 65535 f \n")
    for offset in offsets[1:]:
        pdf.extend(f"{offset:010d} 00000 n \n".encode("ascii"))
    pdf.extend(
        f"trailer\n<< /Size {len(objects) + 1} /Root {catalog_ref} 0 R >>\n"
        f"startxref\n{xref}\n%%EOF\n".encode("ascii")
    )
    pdf_path.parent.mkdir(parents=True, exist_ok=True)
    pdf_path.write_bytes(pdf)


def page_items_for_tier(data: dict, tier: str) -> list[dict]:
    items = [
        item
        for item in data["items"]
        if item.get("role") in PAGE_ROLES and tier in tier_list(item)
    ]
    return sorted(items, key=lambda item: int(item.get("pdf_order", 9999)))


def write_tier_manifests(dist_dir: Path, manifests: dict, data: dict, run: dict) -> None:
    for tier in TIERS:
        tier_dir = dist_dir / TIER_LABELS[tier]
        manifest = {
            "title": data["title"],
            "tier": TIER_LABELS[tier],
            "run_id": run["run_id"],
            "skill_version": run["skill_version"],
            "dependency_revisions": run["revisions"],
            "built_at": now(),
            "files": sorted(manifests[tier], key=lambda row: row["file"]),
        }
        (tier_dir / f"manifest-{tier}.json").write_text(
            json.dumps(manifest, indent=2), encoding="utf-8"
        )


def build(packet_dir: Path) -> None:
    data = read_map(packet_dir)
    manifest, run, asset_state = load_locked_state(packet_dir, data)
    title = clean_name(data["title"])
    staging_root = packet_dir / "working" / "distribution-staging" / run["run_id"]
    if staging_root.exists():
        shutil.rmtree(staging_root)
    dist_dir = staging_root / "distribution"
    for tier in TIERS:
        for subdir in ("PDF", "PNG Pages", "Appendix Pages", "Battle Maps", "Tokens"):
            (dist_dir / TIER_LABELS[tier] / subdir).mkdir(parents=True, exist_ok=True)
    manifests = copy_tier_files(packet_dir, dist_dir, data, asset_state)
    for tier in TIERS:
        pages = [item_path(packet_dir, item) for item in page_items_for_tier(data, tier)]
        if not pages:
            raise SystemExit(f"No PDF pages mapped for {TIER_LABELS[tier]}")
        pdf_name = f"{title} - {TIER_LABELS[tier]}.pdf"
        write_pdf(dist_dir / TIER_LABELS[tier] / "PDF" / pdf_name, pages)
        manifests[tier].append({"file": f"PDF/{pdf_name}", "role": "pdf"})
    write_tier_manifests(dist_dir, manifests, data, run)
    staged_zips: dict[str, Path] = {}
    for tier in TIERS:
        tier_dir = dist_dir / TIER_LABELS[tier]
        zip_path = staging_root / f"{title} - {TIER_LABELS[tier]}.zip"
        with ZipFile(zip_path, "w", ZIP_DEFLATED) as archive:
            for path in sorted(tier_dir.rglob("*")):
                if path.is_file():
                    archive.write(path, path.relative_to(tier_dir.parent))
        staged_zips[tier] = zip_path

    live_dist = packet_dir / "distribution"
    backup_dist = packet_dir / "working" / f"distribution-backup-{run['run_id']}"
    if backup_dist.exists():
        shutil.rmtree(backup_dist)
    if live_dist.exists():
        live_dist.rename(backup_dist)
    try:
        dist_dir.rename(live_dist)
        for tier, staged_zip in staged_zips.items():
            final_zip = packet_dir / f"{title} - {TIER_LABELS[tier]}.zip"
            os.replace(staged_zip, final_zip)
    except Exception:
        if live_dist.exists():
            shutil.rmtree(live_dist)
        if backup_dist.exists():
            backup_dist.rename(live_dist)
        raise
    if backup_dist.exists():
        shutil.rmtree(backup_dist)
    if staging_root.exists():
        shutil.rmtree(staging_root)

    desktop_export = publish_desktop_archives(packet_dir, title, run)

    manifest["status"] = "packaged"
    manifest["packaged_at"] = now()
    manifest["updated_at"] = now()
    run["status"] = "packaged"
    run["packaged_at"] = now()
    run["updated_at"] = now()
    run.setdefault("events", []).append({"at": now(), "event": "distribution_packaged"})
    write_json_atomic(packet_dir / "manifest.json", manifest)
    write_json_atomic(packet_dir / "run-state.json", run)
    print(f"Built locked distribution in {live_dist}")
    print(f"Published customer archives to {desktop_export}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--packet-dir", required=True, type=Path)
    args = parser.parse_args()
    build(args.packet_dir.resolve())


if __name__ == "__main__":
    main()

