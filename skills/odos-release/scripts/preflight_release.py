#!/usr/bin/env python3
"""Select and validate the oldest unpublished ODOSv5.1 release."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sys
import zipfile
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path, PurePosixPath
from typing import Any
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError


TIERS = ("Basic", "Deluxe", "Premium")
ISO_RE = re.compile(r"20\d{2}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?(?:Z|[+-]\d{2}:\d{2})")
RUN_RE = re.compile(r"\brun\s+([A-Za-z0-9_-]+)", re.IGNORECASE)


def read_json(path: Path, default: Any) -> Any:
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_suffix(path.suffix + ".tmp")
    temp.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    os.replace(temp, path)


def parse_datetime(value: str) -> datetime:
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    return parsed if parsed.tzinfo else parsed.replace(tzinfo=timezone.utc)


def iso_utc(value: datetime) -> str:
    return value.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def resolve_windows_desktop() -> Path:
    if os.name == "nt":
        try:
            import winreg  # type: ignore

            key_path = r"Software\Microsoft\Windows\CurrentVersion\Explorer\User Shell Folders"
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path) as key:
                raw, _ = winreg.QueryValueEx(key, "Desktop")
            resolved = Path(os.path.expandvars(str(raw))).expanduser()
            if resolved.exists():
                return resolved
        except (OSError, ImportError):
            pass

    candidates = []
    for variable in ("OneDrive", "OneDriveConsumer", "OneDriveCommercial"):
        root = os.environ.get(variable)
        if root:
            candidates.append(Path(root) / "Desktop")
    candidates.append(Path.home() / "Desktop")
    for candidate in candidates:
        if candidate.exists():
            return candidate
    raise FileNotFoundError("Could not resolve the Windows Desktop directory")


def expand_config_path(value: str) -> Path:
    return Path(os.path.expandvars(value.replace("/", os.sep))).expanduser()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def marker_metadata(path: Path) -> dict[str, Any]:
    text = path.read_text(encoding="utf-8", errors="replace")[:4096]
    iso_match = ISO_RE.search(text)
    ready_at = parse_datetime(iso_match.group(0)) if iso_match else datetime.fromtimestamp(path.stat().st_mtime, timezone.utc)
    run_match = RUN_RE.search(text)
    return {"text": text.strip(), "ready_at": iso_utc(ready_at), "run_hint": run_match.group(1) if run_match else None}


def slugify(value: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
    return slug or "release"


def safe_member(name: str) -> bool:
    normalized = name.replace("\\", "/")
    path = PurePosixPath(normalized)
    return not path.is_absolute() and ".." not in path.parts and not re.match(r"^[A-Za-z]:", normalized)


def public_inventory(entries: set[str], tier: str) -> set[str]:
    prefix = tier + "/"
    result = set()
    for name in entries:
        relative = name[len(prefix) :] if name.startswith(prefix) else name
        lowered = relative.lower()
        if lowered.startswith("manifest-") or lowered.startswith("pdf/"):
            continue
        result.add(relative)
    return result


def validate_zip(path: Path, tier: str, title: str, verify_crc: bool) -> dict[str, Any]:
    errors: list[str] = []
    manifest: dict[str, Any] = {}
    members: set[str] = set()
    cover_member = None
    overview_member = None

    try:
        with zipfile.ZipFile(path, "r") as archive:
            infos = [info for info in archive.infolist() if not info.is_dir()]
            members = {info.filename.replace("\\", "/") for info in infos}
            if not infos:
                errors.append(f"{tier} ZIP is empty")
            unsafe = sorted(name for name in members if not safe_member(name))
            if unsafe:
                errors.append(f"{tier} ZIP contains unsafe paths: {unsafe[:3]}")
            rejected = sorted(name for name in members if "failed" in name.lower())
            if rejected:
                errors.append(f"{tier} ZIP contains rejected proof files: {rejected[:3]}")
            wrong_roots = sorted(name for name in members if not name.startswith(tier + "/"))
            if wrong_roots:
                errors.append(f"{tier} ZIP has files outside the {tier}/ root")
            if verify_crc:
                bad_member = archive.testzip()
                if bad_member:
                    errors.append(f"{tier} ZIP CRC failed at {bad_member}")

            manifest_name = f"{tier}/manifest-{tier.lower()}.json"
            found = [name for name in members if name.lower() == manifest_name.lower()]
            if len(found) != 1:
                errors.append(f"{tier} ZIP must contain exactly one {manifest_name}")
            else:
                manifest_name = found[0]
                try:
                    manifest = json.loads(archive.read(manifest_name).decode("utf-8"))
                except (UnicodeDecodeError, json.JSONDecodeError) as exc:
                    errors.append(f"{tier} manifest is invalid JSON: {exc}")

            if manifest:
                if manifest.get("title") != title:
                    errors.append(f"{tier} manifest title does not match folder title")
                if manifest.get("tier") != tier:
                    errors.append(f"{tier} manifest tier is {manifest.get('tier')!r}")
                if not str(manifest.get("skill_version", "")).startswith("5.1"):
                    errors.append(f"{tier} manifest is not an ODOSv5.1 package")
                files = manifest.get("files")
                if not isinstance(files, list) or not files:
                    errors.append(f"{tier} manifest has no file inventory")
                    files = []

                expected = {manifest_name}
                for item in files:
                    relative = str(item.get("file", "")).replace("\\", "/").lstrip("/")
                    if not relative or not safe_member(relative):
                        errors.append(f"{tier} manifest contains an invalid file path")
                        continue
                    expected.add(f"{tier}/{relative}")
                    role = item.get("role")
                    if role == "cover":
                        cover_member = f"{tier}/{relative}"
                    if "adventure overview" in relative.lower():
                        overview_member = f"{tier}/{relative}"

                missing = sorted(expected - members)
                extra = sorted(members - expected)
                if missing:
                    errors.append(f"{tier} ZIP is missing manifest files: {missing[:3]}")
                if extra:
                    errors.append(f"{tier} ZIP has unmanifested files: {extra[:3]}")
                if not cover_member or cover_member not in members:
                    errors.append(f"{tier} ZIP has no manifest-approved cover")
                pdfs = [item for item in files if item.get("role") == "pdf"]
                expected_pdf = f"PDF/{title} - {tier}.pdf"
                if len(pdfs) != 1 or str(pdfs[0].get("file", "")).replace("\\", "/") != expected_pdf:
                    errors.append(f"{tier} ZIP does not contain the expected tier PDF")
    except (OSError, zipfile.BadZipFile, RuntimeError) as exc:
        errors.append(f"{tier} ZIP cannot be read: {exc}")

    files = manifest.get("files", []) if manifest else []
    role_counts = Counter(str(item.get("role", "unknown")) for item in files)
    return {
        "edition": tier,
        "path": str(path.resolve()),
        "size_bytes": path.stat().st_size if path.exists() else None,
        "sha256": sha256_file(path) if path.exists() else None,
        "entry_count": len(members),
        "run_id": manifest.get("run_id") if manifest else None,
        "skill_version": manifest.get("skill_version") if manifest else None,
        "built_at": manifest.get("built_at") if manifest else None,
        "role_counts": dict(sorted(role_counts.items())),
        "inventory": sorted(public_inventory(members, tier)),
        "cover_member": cover_member,
        "overview_member": overview_member,
        "manifest": manifest,
        "errors": errors,
    }


def validate_release(folder: Path, config: dict[str, Any], verify_crc: bool) -> dict[str, Any]:
    title = folder.name
    marker_name = config["source"]["ready_marker"]
    expected_names = {marker_name, *(f"{title} - {tier}.zip" for tier in TIERS)}
    children = list(folder.iterdir())
    actual_files = {child.name for child in children if child.is_file()}
    directories = [child.name for child in children if child.is_dir()]
    errors: list[str] = []
    if config["source"].get("require_exactly_four_files", True):
        missing = sorted(expected_names - actual_files)
        extra = sorted(actual_files - expected_names)
        if missing:
            errors.append(f"Missing required files: {missing}")
        if extra:
            errors.append(f"Unexpected files: {extra}")
        if directories:
            errors.append(f"Unexpected subdirectories: {directories}")

    marker = folder / marker_name
    marker_info = marker_metadata(marker) if marker.exists() else {"text": "", "ready_at": None, "run_hint": None}
    tier_reports = {}
    for tier in TIERS:
        path = folder / f"{title} - {tier}.zip"
        if path.exists():
            tier_reports[tier] = validate_zip(path, tier, title, verify_crc)
            errors.extend(tier_reports[tier]["errors"])

    run_ids = {report.get("run_id") for report in tier_reports.values() if report.get("run_id")}
    if len(run_ids) != 1:
        errors.append(f"Tier manifests do not share one run ID: {sorted(run_ids)}")
    run_id = next(iter(run_ids), marker_info.get("run_hint"))
    if marker_info.get("run_hint") and run_id and marker_info["run_hint"] != run_id:
        errors.append("Ready.txt run ID does not match the embedded manifests")

    if all(tier in tier_reports for tier in TIERS):
        basic = set(tier_reports["Basic"]["inventory"])
        deluxe = set(tier_reports["Deluxe"]["inventory"])
        premium = set(tier_reports["Premium"]["inventory"])
        if not basic < deluxe:
            errors.append("Deluxe must strictly include all Basic assets plus additional assets")
        if not deluxe < premium:
            errors.append("Premium must strictly include all Deluxe assets plus additional assets")

    release_id = f"{slugify(title)}--{run_id or 'unknown-run'}"
    compact_tiers = {}
    for tier, report in tier_reports.items():
        compact_tiers[tier] = {key: value for key, value in report.items() if key not in {"manifest", "errors"}}

    return {
        "title": title,
        "release_id": release_id,
        "run_id": run_id,
        "source_folder": str(folder.resolve()),
        "ready": marker_info,
        "tiers": compact_tiers,
        "valid": not errors,
        "errors": errors,
        "_tier_reports": tier_reports,
    }


def same_source(record: dict[str, Any], folder: Path) -> bool:
    value = record.get("source_folder")
    if not value:
        return False
    try:
        return Path(value).resolve() == folder.resolve()
    except OSError:
        return False


def completed_this_week(ledger: dict[str, Any], now: datetime, timezone_name: str) -> list[dict[str, Any]]:
    zone = ZoneInfo(timezone_name)
    local_week = now.astimezone(zone).isocalendar()[:2]
    completed = []
    for record in ledger.get("releases", {}).values():
        if record.get("status") != "complete" or not record.get("completed_at"):
            continue
        finished = parse_datetime(record["completed_at"]).astimezone(zone)
        if finished.isocalendar()[:2] == local_week:
            completed.append(record)
    return completed


def extract_staging(selected: dict[str, Any], stage_root: Path, report: dict[str, Any]) -> Path:
    stage = stage_root / selected["release_id"]
    stage.mkdir(parents=True, exist_ok=True)
    basic_path = Path(selected["tiers"]["Basic"]["path"])
    cover_member = selected["tiers"]["Basic"].get("cover_member")
    overview_member = selected["tiers"]["Basic"].get("overview_member")
    with zipfile.ZipFile(basic_path, "r") as archive:
        if cover_member:
            (stage / "cover.png").write_bytes(archive.read(cover_member))
        if overview_member:
            (stage / "overview.png").write_bytes(archive.read(overview_member))
    write_json(stage / "release-context.json", report)
    return stage


def main() -> int:
    skill_root = Path(__file__).resolve().parents[1]
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, default=skill_root / "references" / "release-config.json")
    parser.add_argument("--new-adventures", type=Path)
    parser.add_argument("--ledger", type=Path)
    parser.add_argument("--prepare", action="store_true")
    parser.add_argument("--prepare-root", type=Path)
    parser.add_argument("--skip-crc", action="store_true")
    parser.add_argument("--now", help="ISO timestamp override for deterministic testing")
    parser.add_argument("--json-out", type=Path)
    args = parser.parse_args()

    config = read_json(args.config, {})
    state_dir = expand_config_path(config["state"]["default_directory"])
    ledger_path = args.ledger or state_dir / config["state"]["ledger_filename"]
    new_adventures = args.new_adventures or resolve_windows_desktop() / config["source"]["desktop_parent_folder"]
    now = parse_datetime(args.now) if args.now else datetime.now(timezone.utc)
    ledger = read_json(ledger_path, {"schema_version": 1, "releases": {}})

    report: dict[str, Any] = {
        "schema_version": 1,
        "checked_at": iso_utc(now),
        "timezone": config["timezone"],
        "new_adventures": str(new_adventures.resolve()) if new_adventures.exists() else str(new_adventures),
        "ledger": str(ledger_path),
        "status": None,
        "selected": None,
    }

    weekly = completed_this_week(ledger, now, config["timezone"])
    maximum = int(config["schedule"]["maximum_completed_releases_per_iso_week"])
    if len(weekly) >= maximum:
        report["status"] = "weekly_limit_reached"
        report["completed_this_week"] = [item.get("release_id") for item in weekly]
    elif not new_adventures.exists():
        report["status"] = "no_ready"
        report["message"] = "New Adventures directory does not exist"
    else:
        marker_name = config["source"]["ready_marker"]
        candidates = [folder for folder in new_adventures.iterdir() if folder.is_dir() and (folder / marker_name).is_file()]
        candidates.sort(key=lambda folder: parse_datetime(marker_metadata(folder / marker_name)["ready_at"]))
        complete_records = [record for record in ledger.get("releases", {}).values() if record.get("status") == "complete"]
        complete_ids = {record.get("release_id") for record in complete_records}
        filtered_candidates = []
        for folder in candidates:
            marker = marker_metadata(folder / marker_name)
            hinted_id = f"{slugify(folder.name)}--{marker.get('run_hint')}" if marker.get("run_hint") else None
            if any(same_source(record, folder) for record in complete_records) or hinted_id in complete_ids:
                continue
            filtered_candidates.append(folder)
        candidates = filtered_candidates

        if not candidates:
            report["status"] = "no_ready"
            report["message"] = "No unpublished Ready.txt adventure was found"
        else:
            selected_internal = validate_release(candidates[0], config, verify_crc=not args.skip_crc)
            tier_reports = selected_internal.pop("_tier_reports")
            report["selected"] = selected_internal
            if not selected_internal["valid"]:
                report["status"] = "invalid"
            else:
                report["status"] = "ready"
                if args.prepare:
                    stage_root = args.prepare_root or state_dir / config["state"]["staging_folder"]
                    stage = extract_staging(selected_internal, stage_root, report)
                    report["staging_directory"] = str(stage.resolve())
                    write_json(stage / "release-context.json", report)

    if args.json_out:
        write_json(args.json_out, report)
    print(json.dumps(report, indent=2, ensure_ascii=False))
    return 2 if report["status"] == "invalid" else 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (KeyError, OSError, ValueError, ZoneInfoNotFoundError) as exc:
        print(json.dumps({"status": "error", "error": str(exc)}, indent=2), file=sys.stderr)
        raise SystemExit(3)
