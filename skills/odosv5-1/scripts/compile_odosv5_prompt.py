#!/usr/bin/env python3
"""Compile one immutable ODOSv5.1 prompt from approved locks and an asset spec."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path


SKILL_ROOT = Path(__file__).resolve().parent.parent
ART_STYLE_DIR = SKILL_ROOT / "assets" / "art-style-samples"
PAGE_SAMPLE_DIR = SKILL_ROOT / "assets" / "page-samples"
LOGO_PATH = SKILL_ROOT / "assets" / "logos" / "Logo 4.png"
IMAGE_SUFFIXES = {".png", ".jpg", ".jpeg", ".webp"}
STYLE_ANCHORED_TYPES = {
    "core_page",
    "appendix_page",
    "art_plate",
    "cast_crop",
    "cast_sheet",
    "map",
    "storyboard",
    "token",
}
SCENE_PAGE_SAMPLE = "ig_0037031b75f5be41016a4b799ff8388194b04ded71a7e313f8.png"
FLOW_PAGE_SAMPLE = "ig_08e5f85f801b3b79016a4b8342672481968fd37f4b8bd2fee6.png"
COVER_PAGE_SAMPLE = "Rumble TM Cover.png"


def read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def resolve(packet: Path, value: str) -> Path:
    path = Path(value)
    return path.resolve() if path.is_absolute() else (packet / path).resolve()


def clean_slug(value: str) -> str:
    value = re.sub(r"[^A-Za-z0-9._-]+", "-", value).strip("-")
    return value or "asset"


def require_approved(lock: dict, name: str) -> None:
    if lock.get("status") != "approved":
        raise SystemExit(f"{name} lock is provisional. Obtain explicit approval before compiling production prompts.")


def image_files(folder: Path) -> list[Path]:
    return sorted(
        path.resolve()
        for path in folder.iterdir()
        if path.is_file() and path.suffix.lower() in IMAGE_SUFFIXES
    )


def expected_page_sample(asset: str) -> Path:
    filename = Path(asset).name
    if filename == "page-00-cover.png":
        sample = COVER_PAGE_SAMPLE
    elif filename == "page-04-scene-flow-overview.png":
        sample = FLOW_PAGE_SAMPLE
    else:
        sample = SCENE_PAGE_SAMPLE
    return (PAGE_SAMPLE_DIR / sample).resolve()


def validate_reference_routing(
    packet: Path,
    asset: str,
    asset_type: str,
    references: list[dict],
    style: dict,
) -> None:
    paths = {resolve(packet, ref["path"]) for ref in references}
    is_handout = asset.replace("\\", "/").startswith("handouts/")

    if asset_type in STYLE_ANCHORED_TYPES and not is_handout:
        approved_style_paths = set(image_files(ART_STYLE_DIR))
        if not paths & approved_style_paths:
            raise SystemExit(
                "Visual prompt must directly reference at least one original image from "
                f"{ART_STYLE_DIR}; generated proofs and art plates never replace the style authority."
            )

    if asset_type in {"core_page", "appendix_page"} and not is_handout:
        expected = expected_page_sample(asset)
        if expected not in paths:
            raise SystemExit(
                f"Page prompt must reference its routed ODOSv5 page sample: {expected}"
            )
        if LOGO_PATH.resolve() not in paths:
            raise SystemExit(f"Packet page prompt must reference the exact ODOS logo: {LOGO_PATH}")

    if asset_type == "map":
        proof = style.get("proofs", {}).get("battle_map") or style.get("proofs", {}).get("battle_map_tile")
        if not proof:
            raise SystemExit("Approved style lock lacks a battle-map proof.")
        proof_path = resolve(packet, proof["path"])
        if proof_path not in paths:
            raise SystemExit(
                "Battle-map prompt must directly reference the approved battle-map proof: "
                f"{proof_path}"
            )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--packet-dir", required=True, type=Path)
    parser.add_argument("--spec", required=True, type=Path)
    args = parser.parse_args()

    packet = args.packet_dir.resolve()
    spec_path = args.spec.resolve()
    spec = read_json(spec_path)
    run = read_json(packet / "run-state.json")
    style = read_json(packet / "style-lock.json")
    cast = read_json(packet / "cast-lock.json")
    scene = read_json(packet / "scene-lock.json")
    plates = read_json(packet / "art-plates.json") if (packet / "art-plates.json").exists() else {"status": "pending", "plates": {}}

    asset = spec.get("asset")
    asset_type = spec.get("asset_type")
    if not asset or not asset_type:
        raise SystemExit("Prompt spec requires asset and asset_type.")
    require_approved(style, "Style")
    characters = list(spec.get("characters", []))
    if characters:
        require_approved(cast, "Cast")
        unknown = sorted(set(characters) - set(cast.get("characters", {})))
        if unknown:
            raise SystemExit("Characters absent from approved cast lock: " + ", ".join(unknown))
    scene_id = spec.get("scene")
    if scene_id:
        require_approved(scene, "Scene")
        if scene_id not in scene.get("scenes", {}):
            raise SystemExit(f"Scene absent from approved scene lock: {scene_id}")
    requested_plates = spec.get("art_plates", [])
    if asset_type in {"core_page", "appendix_page"}:
        if not requested_plates:
            raise SystemExit("Page prompt specs must name at least one approved art plate.")
        for plate_id in requested_plates:
            plate = plates.get("plates", {}).get(plate_id)
            if not plate or plate.get("status") != "approved" or not plate.get("current"):
                raise SystemExit(f"Required art plate is not approved/current: {plate_id}")

    references = spec.get("references", [])
    if len(references) > 5:
        raise SystemExit("Reference budget exceeded: image calls permit at most five references.")
    validate_reference_routing(packet, asset, asset_type, references, style)
    reference_lines = []
    reference_records = []
    for ref in references:
        path = resolve(packet, ref["path"])
        if not path.is_file():
            raise SystemExit(f"Reference does not exist: {path}")
        record = {"role": ref["role"], "path": str(path), "sha256": sha256(path)}
        reference_records.append(record)
        reference_lines.append(f"- {ref['role']}: {path}")

    character_lines = []
    for name in characters:
        attrs = cast["characters"][name]
        crop = cast["crops"][name]
        character_lines.append(
            f"- {name}: {json.dumps(attrs, ensure_ascii=False, sort_keys=True)}; identity crop {crop['path']} sha256={crop['sha256']}"
        )
    scene_line = "None"
    if scene_id:
        scene_line = json.dumps(scene["scenes"][scene_id], ensure_ascii=False, sort_keys=True)

    required_text = spec.get("required_text", [])
    text_lines = "\n".join(f'- "{value}"' for value in required_text) or "- None"
    prompt = f"""Generate one final raster PNG for ODOSv5.

ASSET
- Path: {asset}
- Type: {asset_type}
- Purpose: {spec.get('purpose', '')}

LOCK REVISIONS
- Run: {run['run_id']}
- Style: {style['revision']}
- Cast: {cast['revision']}
- Scene: {scene['revision']}
- Copy: {run['revisions']['copy']}

REFERENCE BUDGET ({len(references)}/5)
{chr(10).join(reference_lines) or '- None'}
Reference roles are strict. ODOSv5 page samples control page composition, density, title placement, panel shapes, and illustration-to-text balance only. Original art-style samples control rendering and must remain directly present in every visual call. Cast sheets/crops control identity only. Art plates control composition only. The logo controls the logo only. Generated intermediates never become style authority.

APPROVED STYLE
{json.dumps(style, ensure_ascii=False, sort_keys=True)}

APPROVED CHARACTERS
{chr(10).join(character_lines) or '- None'}

APPROVED SCENE
{scene_line}

CONTENT
{spec.get('content', '')}

ART DIRECTION
{spec.get('art_direction', '')}

REQUIRED TEXT
{text_lines}

INVARIANTS
{chr(10).join('- ' + value for value in spec.get('invariants', [])) or '- Preserve all approved locks.'}

HARD FAILS
- Do not copy characters from reusable style references.
- Do not invent or reinterpret recurring character identity.
- Do not copy characters, scenery, titles, or story content from page samples; use them strictly for layout and hierarchy.
- Do not imitate a generated proof, crop, storyboard, or art plate in place of the original art-style sample.
- Do not exceed the approved scene camera, geography, palette, action, or clue plan.
- Do not use gritty, painterly, realistic, noisy, stippled, speckled, grainy, or micro-textured rendering.
- Do not omit, alter, or invent required text, names, or mechanics.
- Do not add unauthorized branding, placeholder text, random words, or watermarks.
"""

    prompt_bytes = prompt.encode("utf-8")
    prompt_hash = hashlib.sha256(prompt_bytes).hexdigest()
    out_dir = packet / "working" / "prompts" / run["run_id"]
    out_dir.mkdir(parents=True, exist_ok=True)
    stem = clean_slug(Path(asset).name)
    prompt_path = out_dir / f"{stem}--{prompt_hash[:12]}.txt"
    metadata_path = prompt_path.with_suffix(".json")
    if not prompt_path.exists():
        prompt_path.write_bytes(prompt_bytes)
        dependency_revisions = {"style": run["revisions"]["style"]}
        if characters:
            dependency_revisions["cast"] = run["revisions"]["cast"]
        if scene_id:
            dependency_revisions["scene"] = run["revisions"]["scene"]
        if spec.get("copy_keys"):
            dependency_revisions["copy"] = run["revisions"]["copy"]
        metadata = {
            "asset": asset,
            "asset_type": asset_type,
            "prompt_path": str(prompt_path),
            "prompt_sha256": prompt_hash,
            "spec_path": str(spec_path),
            "spec_sha256": sha256(spec_path),
            "references": reference_records,
            "dependency_revisions": dependency_revisions,
            "characters": characters,
            "scene": scene_id,
            "art_plates": requested_plates,
            "copy_keys": spec.get("copy_keys", []),
        }
        metadata_path.write_text(json.dumps(metadata, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"prompt": str(prompt_path), "metadata": str(metadata_path), "sha256": prompt_hash}, indent=2))


if __name__ == "__main__":
    main()
