#!/usr/bin/env python3
"""Manage ODOSv5.1 gates, candidates, approvals, and invalidation."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import tempfile
from datetime import datetime, timezone
from pathlib import Path


SCHEMA_VERSION = 1
SKILL_VERSION = "5.1.0"
MANIFEST_STATUSES = {
    "scaffolded",
    "calibrating",
    "generating",
    "qa_failed",
    "approved",
    "packaged",
    "stale",
}
VISUAL_TYPES = {
    "proof",
    "cast_sheet",
    "cast_crop",
    "storyboard",
    "art_plate",
    "core_page",
    "appendix_page",
    "token",
    "map",
}
FINAL_TYPES = {"core_page", "appendix_page", "token", "map"}
PAGE_TYPES = {"core_page", "appendix_page"}
DELEGATED_ACTOR = "codex-delegated-under-user-policy"
AUTONOMOUS_ACTOR = "codex-autonomous-qa"
DELEGATED_SCOPES = {
    "scene_storyboard",
    "art_plates",
    "asset_promotion",
    "run_approval",
    "locked_packaging",
}
AUTONOMOUS_SCOPES = DELEGATED_SCOPES | {"style_calibration", "cast_approval"}
CHECKPOINT_SCOPES = DELEGATED_SCOPES | {"cast_approval"}
MAP_QA_CHECKS = {
    "strict_top_down",
    "grid_alignment",
    "tactical_zones",
    "entrances_exits",
    "cover_and_hazards",
    "route_connectivity",
    "encounter_space",
    "no_text_or_labels",
    "no_creatures",
    "original_style_match",
    "approved_map_match",
    "density_balance",
    "vtt_readability",
}
SKILL_ROOT = Path(__file__).resolve().parent.parent
IMAGE_SUFFIXES = {".png", ".jpg", ".jpeg", ".webp"}


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


def read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def write_json(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    os.replace(tmp, path)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def resolve_path(packet: Path, value: str) -> Path:
    path = Path(value)
    return path.resolve() if path.is_absolute() else (packet / path).resolve()


def relative_or_absolute(packet: Path, path: Path) -> str:
    try:
        return path.relative_to(packet).as_posix()
    except ValueError:
        return str(path)


def state_paths(packet: Path) -> dict[str, Path]:
    return {
        "manifest": packet / "manifest.json",
        "run": packet / "run-state.json",
        "policy": packet / "approval-policy.json",
        "style": packet / "style-lock.json",
        "cast": packet / "cast-lock.json",
        "scene": packet / "scene-lock.json",
        "assets": packet / "asset-status.json",
        "plates": packet / "art-plates.json",
    }


def require_state(packet: Path) -> tuple[dict[str, Path], dict, dict, dict, dict, dict]:
    paths = state_paths(packet)
    missing = [str(path) for key, path in paths.items() if key not in {"plates", "policy"} and not path.exists()]
    if missing:
        raise SystemExit("Missing ODOSv5 state files: " + ", ".join(missing))
    run = read_json(paths["run"])
    if not paths["policy"].exists():
        write_json(paths["policy"], default_approval_policy(run["run_id"]))
    return (
        paths,
        read_json(paths["manifest"]),
        run,
        read_json(paths["style"]),
        read_json(paths["cast"]),
        read_json(paths["scene"]),
    )


def set_manifest_status(manifest: dict, status: str) -> None:
    if status not in MANIFEST_STATUSES:
        raise SystemExit(f"Unsupported manifest status: {status}")
    manifest["status"] = status
    manifest["updated_at"] = now()


def parse_names(values: list[str] | None) -> list[str]:
    result: list[str] = []
    for value in values or []:
        result.extend(part.strip() for part in value.split(",") if part.strip())
    return sorted(set(result))


def default_approval_policy(run_id: str) -> dict:
    return {
        "schema_version": SCHEMA_VERSION,
        "run_id": run_id,
        "mode": "single_visual_checkpoint",
        "authorized_by": "skill-default",
        "authorized_at": now(),
        "scope": sorted(CHECKPOINT_SCOPES),
        "stop_conditions": [
            "the four-proof visual checkpoint has not been explicitly approved",
            "a requested style or cast change",
            "source ambiguity that changes story meaning",
            "three failed candidates for the same asset",
            "a hash mismatch or stale dependency",
            "packaging validation failure",
        ],
        "notes": "Require one explicit four-proof visual checkpoint, then continue with autonomous QA.",
    }


def validate_approval_actor(
    paths: dict[str, Path],
    run: dict,
    approved_by: str,
    scope: str,
    *,
    explicit_required: bool = False,
) -> None:
    if approved_by not in {DELEGATED_ACTOR, AUTONOMOUS_ACTOR}:
        return
    if explicit_required and approved_by in {DELEGATED_ACTOR, AUTONOMOUS_ACTOR}:
        raise SystemExit("The four-proof visual checkpoint must be approved explicitly by the user.")
    policy = read_json(paths["policy"])
    if approved_by == AUTONOMOUS_ACTOR:
        allowed_modes = {"autonomous_full_run", "single_visual_checkpoint"}
    else:
        allowed_modes = {"delegated_after_style_and_cast"}
    if policy.get("mode") not in allowed_modes:
        raise SystemExit(
            "Approval actor is not authorized by policy mode: "
            + ", ".join(sorted(allowed_modes))
        )
    if scope not in set(policy.get("scope", [])):
        raise SystemExit(f"Approval scope is not authorized: {scope}")
    if approved_by == DELEGATED_ACTOR:
        for gate in ("style_calibration", "cast_approval"):
            if run["gates"].get(gate) != "approved":
                raise SystemExit("Delegated approval requires approved style and cast locks.")
    if approved_by == AUTONOMOUS_ACTOR and policy.get("mode") == "single_visual_checkpoint":
        if run["gates"].get("style_calibration") != "approved":
            raise SystemExit("Autonomous continuation requires the user-approved four-proof visual checkpoint.")


def validate_map_qa_evidence(packet: Path, report_value: str | None) -> dict:
    if not report_value:
        raise SystemExit("Passing battle-map QA requires --visual-report.")
    report = resolve_path(packet, report_value)
    if not report.is_file():
        raise SystemExit(f"Battle-map visual QA report does not exist: {report}")
    data = read_json(report)
    if data.get("status") != "pass":
        raise SystemExit("Battle-map visual QA status must be pass.")
    checks = data.get("checks", {})
    failed = sorted(name for name in MAP_QA_CHECKS if checks.get(name) not in {True, "pass", "passed"})
    if failed:
        raise SystemExit("Battle-map QA is missing passing checks: " + ", ".join(failed))
    return {"path": relative_or_absolute(packet, report), "sha256": sha256(report)}


def validate_qa_evidence(
    packet: Path,
    approved_by: str,
    qa_report: str | None,
    required_checks: set[str],
) -> dict | None:
    if not qa_report:
        if approved_by == AUTONOMOUS_ACTOR:
            raise SystemExit("Autonomous approval requires a persisted QA evidence report.")
        return None
    report = resolve_path(packet, qa_report)
    if not report.is_file():
        raise SystemExit(f"QA evidence report does not exist: {report}")
    data = read_json(report)
    if data.get("status") != "pass":
        raise SystemExit("QA evidence status must be pass.")
    checks = data.get("checks", {})
    failed = sorted(
        name
        for name in required_checks
        if checks.get(name) not in {True, "pass", "passed"}
    )
    if failed:
        raise SystemExit("QA evidence is missing passing checks: " + ", ".join(failed))
    return {"path": relative_or_absolute(packet, report), "sha256": sha256(report)}


def hashed_file(packet: Path, value: str) -> dict:
    path = resolve_path(packet, value)
    if not path.is_file():
        raise SystemExit(f"Approval artifact does not exist: {path}")
    return {"path": relative_or_absolute(packet, path), "sha256": sha256(path)}


def reference_images(folder: Path) -> set[Path]:
    return {
        path.resolve()
        for path in folder.iterdir()
        if path.is_file() and path.suffix.lower() in IMAGE_SUFFIXES
    }


def validate_checkpoint_references(paths: set[Path]) -> None:
    required = (
        reference_images(SKILL_ROOT / "assets" / "art-style-samples")
        | reference_images(SKILL_ROOT / "assets" / "page-samples")
        | {(SKILL_ROOT / "assets" / "logos" / "Logo 4.png").resolve()}
    )
    missing = sorted(str(path) for path in required - paths)
    if missing:
        raise SystemExit(
            "Four-proof checkpoint must hash-lock every original art sample, page sample, and exact logo. Missing: "
            + ", ".join(missing)
        )


def cmd_init(args: argparse.Namespace) -> None:
    packet = args.packet_dir.resolve()
    packet.mkdir(parents=True, exist_ok=True)
    paths = state_paths(packet)
    if paths["run"].exists() and not args.force:
        raise SystemExit("State already exists. Use --force only when intentionally resetting it.")
    run_id = args.run_id or datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    manifest = read_json(paths["manifest"]) if paths["manifest"].exists() else {}
    manifest.update(
        {
            "skill": "odosv5-1",
            "skill_version": SKILL_VERSION,
            "status": "scaffolded",
            "run_id": run_id,
            "updated_at": now(),
        }
    )
    run_state = {
        "schema_version": SCHEMA_VERSION,
        "skill_version": SKILL_VERSION,
        "run_id": run_id,
        "status": "scaffolded",
        "created_at": now(),
        "updated_at": now(),
        "revisions": {"style": 0, "cast": 0, "scene": 0, "copy": 0},
        "gates": {
            "style_calibration": "pending",
            "cast_approval": "pending",
            "scene_storyboard": "pending",
            "art_plates": "pending",
        },
        "events": [],
    }
    provisional = {
        "schema_version": SCHEMA_VERSION,
        "run_id": run_id,
        "status": "provisional",
        "revision": 0,
        "approved_at": None,
        "approved_by": None,
    }
    write_json(paths["manifest"], manifest)
    write_json(paths["run"], run_state)
    write_json(paths["policy"], default_approval_policy(run_id))
    write_json(paths["style"], {**provisional, "proofs": {}, "references": {}})
    write_json(paths["cast"], {**provisional, "cast_sheet": None, "crops": {}, "characters": {}})
    write_json(paths["scene"], {**provisional, "storyboard": None, "scenes": {}})
    write_json(
        paths["assets"],
        {"schema_version": SCHEMA_VERSION, "run_id": run_id, "updated_at": now(), "assets": {}},
    )
    write_json(paths["plates"], {"schema_version": SCHEMA_VERSION, "run_id": run_id, "status": "pending", "plates": {}})
    print(f"Initialized ODOSv5.1 state for run {run_id}")


def load_assets(path: Path) -> dict:
    data = read_json(path)
    data.setdefault("assets", {})
    return data


def save_bundle(paths: dict[str, Path], manifest: dict, run: dict, **extra: dict) -> None:
    run["updated_at"] = now()
    write_json(paths["manifest"], manifest)
    write_json(paths["run"], run)
    for key, value in extra.items():
        write_json(paths[key], value)


def cmd_set_approval_policy(args: argparse.Namespace) -> None:
    packet = args.packet_dir.resolve()
    paths, manifest, run, _, _, _ = require_state(packet)
    if args.mode == "delegated_after_style_and_cast":
        for gate in ("style_calibration", "cast_approval"):
            if run["gates"].get(gate) != "approved":
                raise SystemExit("Approve style and cast before enabling delegated mode.")
        scope = sorted(DELEGATED_SCOPES)
    elif args.mode == "autonomous_full_run":
        scope = sorted(AUTONOMOUS_SCOPES)
    elif args.mode == "single_visual_checkpoint":
        scope = sorted(CHECKPOINT_SCOPES)
    else:
        scope = []
    policy = default_approval_policy(run["run_id"])
    policy.update(
        {
            "mode": args.mode,
            "authorized_by": args.authorized_by,
            "authorized_at": now(),
            "scope": scope,
            "notes": args.notes or policy["notes"],
        }
    )
    run["events"].append(
        {
            "at": now(),
            "event": "approval_policy_changed",
            "mode": args.mode,
            "authorized_by": args.authorized_by,
        }
    )
    save_bundle(paths, manifest, run, policy=policy)
    print(f"Approval policy set to {args.mode}")


def cmd_approve_style(args: argparse.Namespace) -> None:
    packet = args.packet_dir.resolve()
    paths, manifest, run, style, _, _ = require_state(packet)
    validate_approval_actor(paths, run, args.approved_by, "style_calibration", explicit_required=True)
    qa_evidence = validate_qa_evidence(
        packet,
        args.approved_by,
        args.qa_report,
        {
            "reference_hashes",
            "line_weight",
            "anatomy",
            "cel_shading",
            "palette",
            "scene_style",
            "page_layout",
            "battle_map_quality",
            "noise_limits",
        },
    )
    proofs = {
        "character": hashed_file(packet, args.character_proof),
        "multi_character_scene": hashed_file(packet, args.scene_proof),
        "complete_scene_page": hashed_file(packet, args.page_proof),
        "battle_map": hashed_file(packet, args.map_proof),
    }
    references = {}
    reference_paths = set()
    for item in args.reference or []:
        name, separator, value = item.partition("=")
        if not separator:
            raise SystemExit("--reference must use name=path")
        reference_paths.add(resolve_path(packet, value))
        references[name] = hashed_file(packet, value)
    validate_checkpoint_references(reference_paths)
    style.update(
        {
            "status": "approved",
            "revision": run["revisions"]["style"],
            "proofs": proofs,
            "references": references,
            "approved_at": now(),
            "approved_by": args.approved_by,
            "qa_evidence": qa_evidence,
            "notes": args.notes or "",
        }
    )
    run["gates"]["style_calibration"] = "approved"
    run["status"] = "calibrating"
    set_manifest_status(manifest, "calibrating")
    run["events"].append({"at": now(), "event": "style_approved", "by": args.approved_by})
    save_bundle(paths, manifest, run, style=style)
    print("Four-proof visual checkpoint approved")


def cmd_approve_cast(args: argparse.Namespace) -> None:
    packet = args.packet_dir.resolve()
    paths, manifest, run, _, cast, _ = require_state(packet)
    validate_approval_actor(paths, run, args.approved_by, "cast_approval")
    qa_evidence = validate_qa_evidence(
        packet,
        args.approved_by,
        args.qa_report,
        {"exact_roster", "source_attributes", "identity_distinctness", "style_match", "isolated_crops", "equipment_logic", "no_reference_copying"},
    )
    if run["gates"]["style_calibration"] != "approved":
        raise SystemExit("Style calibration must be approved before the cast gate.")
    characters = read_json(resolve_path(packet, args.characters_json))
    crops = read_json(resolve_path(packet, args.crops_json))
    if not isinstance(characters, dict) or not characters:
        raise SystemExit("characters JSON must be a non-empty object")
    crop_records = {name: hashed_file(packet, path) for name, path in crops.items()}
    missing = sorted(set(characters) - set(crop_records))
    if missing:
        raise SystemExit("Missing character crops: " + ", ".join(missing))
    cast.update(
        {
            "status": "approved",
            "revision": run["revisions"]["cast"],
            "cast_sheet": hashed_file(packet, args.cast_sheet),
            "crops": crop_records,
            "characters": characters,
            "approved_at": now(),
            "approved_by": args.approved_by,
            "qa_evidence": qa_evidence,
            "notes": args.notes or "",
        }
    )
    run["gates"]["cast_approval"] = "approved"
    run["events"].append({"at": now(), "event": "cast_approved", "by": args.approved_by})
    save_bundle(paths, manifest, run, cast=cast)
    print("Cast approved")


def cmd_approve_scenes(args: argparse.Namespace) -> None:
    packet = args.packet_dir.resolve()
    paths, manifest, run, _, _, scene = require_state(packet)
    validate_approval_actor(paths, run, args.approved_by, "scene_storyboard")
    qa_evidence = validate_qa_evidence(
        packet,
        args.approved_by,
        args.qa_report,
        {"source_mapping", "character_presence", "action_energy", "geography", "scene_differentiation", "materials"},
    )
    scenes = read_json(resolve_path(packet, args.scenes_json))
    required = {"camera", "geography", "palette", "action", "visible_clues"}
    for name, spec in scenes.items():
        missing = required - set(spec)
        if missing:
            raise SystemExit(f"Scene {name} is missing: {', '.join(sorted(missing))}")
    scene.update(
        {
            "status": "approved",
            "revision": run["revisions"]["scene"],
            "storyboard": hashed_file(packet, args.storyboard),
            "scenes": scenes,
            "approved_at": now(),
            "approved_by": args.approved_by,
            "qa_evidence": qa_evidence,
            "notes": args.notes or "",
        }
    )
    run["gates"]["scene_storyboard"] = "approved"
    run["events"].append({"at": now(), "event": "scenes_approved", "by": args.approved_by})
    save_bundle(paths, manifest, run, scene=scene)
    print("Scene storyboard approved")


def cmd_approve_plates(args: argparse.Namespace) -> None:
    packet = args.packet_dir.resolve()
    paths, manifest, run, style, cast, scene = require_state(packet)
    validate_approval_actor(paths, run, args.approved_by, "art_plates")
    qa_evidence = validate_qa_evidence(
        packet,
        args.approved_by,
        args.qa_report,
        {"source_presence", "identity_continuity", "action_energy", "scene_differentiation", "simple_materials", "cross_page_contact_sheet"},
    )
    for gate in ("style_calibration", "cast_approval", "scene_storyboard"):
        if run["gates"][gate] != "approved":
            raise SystemExit(f"Gate must be approved first: {gate}")
    plate_map = read_json(resolve_path(packet, args.plates_json))
    plates = {}
    for name, value in plate_map.items():
        spec = {"path": value} if isinstance(value, str) else dict(value)
        record = hashed_file(packet, spec["path"])
        characters = parse_names(spec.get("characters", []))
        scene_id = spec.get("scene")
        dependencies = {"style": style["revision"]}
        if characters:
            dependencies["cast"] = cast["revision"]
        if scene_id:
            dependencies["scene"] = scene["revision"]
        plates[name] = {
            **record,
            "status": "approved",
            "current": True,
            "characters": characters,
            "scene": scene_id,
            "dependency_revisions": dependencies,
        }
    data = {
        "schema_version": SCHEMA_VERSION,
        "run_id": run["run_id"],
        "status": "approved",
        "approved_at": now(),
        "approved_by": args.approved_by,
        "qa_evidence": qa_evidence,
        "dependency_revisions": {
            "style": style["revision"],
            "cast": cast["revision"],
            "scene": scene["revision"],
        },
        "plates": plates,
        "notes": args.notes or "",
    }
    run["gates"]["art_plates"] = "approved"
    run["status"] = "generating"
    set_manifest_status(manifest, "generating")
    run["events"].append({"at": now(), "event": "art_plates_approved", "by": args.approved_by})
    save_bundle(paths, manifest, run, plates=data)
    print(f"Approved {len(plates)} art plates")


def current_dependencies(
    run: dict,
    asset_type: str,
    characters: list[str],
    scene_id: str | None,
    copy_keys: list[str],
) -> dict:
    dependencies: dict[str, int] = {}
    if asset_type in VISUAL_TYPES:
        dependencies["style"] = run["revisions"]["style"]
    if characters:
        dependencies["cast"] = run["revisions"]["cast"]
    if scene_id:
        dependencies["scene"] = run["revisions"]["scene"]
    if copy_keys:
        dependencies["copy"] = run["revisions"]["copy"]
    return dependencies


def cmd_register(args: argparse.Namespace) -> None:
    packet = args.packet_dir.resolve()
    paths, manifest, run, _, _, _ = require_state(packet)
    assets = load_assets(paths["assets"])
    candidate = resolve_path(packet, args.candidate)
    prompt = resolve_path(packet, args.prompt)
    if not candidate.is_file() or not prompt.is_file():
        raise SystemExit("Candidate and immutable prompt files must both exist.")
    references = [hashed_file(packet, value) for value in args.reference or []]
    if len(references) > 5:
        raise SystemExit("ODOSv5 permits at most five references per image call.")
    characters = parse_names(args.characters)
    copy_keys = parse_names(args.copy_keys)
    record = assets["assets"].get(args.asset, {})
    attempts = list(record.get("attempts", []))
    attempt = {
        "number": len(attempts) + 1,
        "created_at": now(),
        "candidate": relative_or_absolute(packet, candidate),
        "candidate_sha256": sha256(candidate),
        "prompt": relative_or_absolute(packet, prompt),
        "prompt_sha256": sha256(prompt),
        "references": references,
        "qa": {"status": "pending", "notes": ""},
    }
    attempts.append(attempt)
    assets["assets"][args.asset] = {
        "asset_type": args.asset_type,
        "status": "candidate",
        "current": False,
        "characters": characters,
        "scene": args.scene,
        "art_plates": parse_names(args.art_plates),
        "copy_keys": copy_keys,
        "dependency_revisions": current_dependencies(
            run, args.asset_type, characters, args.scene, copy_keys
        ),
        "attempts": attempts,
        "active_attempt": len(attempts),
        "updated_at": now(),
    }
    assets["updated_at"] = now()
    set_manifest_status(manifest, "generating")
    run["status"] = "generating"
    write_json(paths["assets"], assets)
    save_bundle(paths, manifest, run)
    print(f"Registered candidate {args.asset} attempt {len(attempts)}")


def cmd_qa(args: argparse.Namespace) -> None:
    packet = args.packet_dir.resolve()
    paths, manifest, run, _, _, _ = require_state(packet)
    assets = load_assets(paths["assets"])
    record = assets["assets"].get(args.asset)
    if not record or not record.get("active_attempt"):
        raise SystemExit(f"No active candidate: {args.asset}")
    attempt = record["attempts"][record["active_attempt"] - 1]
    visual_report = None
    if args.result == "pass" and record.get("asset_type") == "map":
        visual_report = validate_map_qa_evidence(packet, args.visual_report)
    attempt["qa"] = {
        "status": args.result,
        "notes": args.notes or "",
        "ocr_report": args.ocr_report,
        "visual_report": visual_report,
        "checked_at": now(),
        "checked_by": args.checked_by,
    }
    if args.result == "fail":
        record["status"] = "qa_failed"
        set_manifest_status(manifest, "qa_failed")
        run["status"] = "qa_failed"
    else:
        record["status"] = "candidate"
    assets["updated_at"] = now()
    write_json(paths["assets"], assets)
    save_bundle(paths, manifest, run)
    print(f"Recorded QA {args.result} for {args.asset}")


def verify_dependencies(record: dict, run: dict) -> None:
    expected = record.get("dependency_revisions", {})
    for key, value in expected.items():
        if run["revisions"].get(key) != value:
            raise SystemExit(f"Candidate is stale: {key} revision {value} != {run['revisions'].get(key)}")


def require_gates(record: dict, run: dict, plates: dict) -> None:
    asset_type = record["asset_type"]
    if asset_type in VISUAL_TYPES and run["gates"]["style_calibration"] != "approved":
        raise SystemExit("Style calibration is not approved.")
    if record.get("characters") and run["gates"]["cast_approval"] != "approved":
        raise SystemExit("Cast is provisional; recurring-character assets cannot be promoted.")
    if record.get("scene") and run["gates"]["scene_storyboard"] != "approved":
        raise SystemExit("Scene storyboard is not approved.")
    if asset_type in PAGE_TYPES:
        requested = record.get("art_plates", [])
        if not requested:
            raise SystemExit("Packet pages must declare their approved art-plate dependencies.")
        for plate_id in requested:
            plate = plates.get("plates", {}).get(plate_id)
            if not plate or plate.get("status") != "approved" or not plate.get("current"):
                raise SystemExit(f"Art plate is not approved/current: {plate_id}")


def cmd_promote(args: argparse.Namespace) -> None:
    packet = args.packet_dir.resolve()
    paths, manifest, run, _, _, _ = require_state(packet)
    validate_approval_actor(paths, run, args.approved_by, "asset_promotion")
    assets = load_assets(paths["assets"])
    plates = read_json(paths["plates"])
    record = assets["assets"].get(args.asset)
    if not record or not record.get("active_attempt"):
        raise SystemExit(f"No active candidate: {args.asset}")
    attempt = record["attempts"][record["active_attempt"] - 1]
    if attempt.get("qa", {}).get("status") != "pass":
        raise SystemExit("Candidate cannot be promoted until QA status is pass.")
    require_gates(record, run, plates)
    verify_dependencies(record, run)
    candidate = resolve_path(packet, attempt["candidate"])
    if sha256(candidate) != attempt["candidate_sha256"]:
        raise SystemExit("Candidate hash changed after registration.")
    destination = resolve_path(packet, args.asset)
    destination.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(dir=destination.parent, delete=False) as handle:
        tmp = Path(handle.name)
    try:
        shutil.copy2(candidate, tmp)
        os.replace(tmp, destination)
    finally:
        if tmp.exists():
            tmp.unlink()
    record.update(
        {
            "status": "approved",
            "current": True,
            "final_path": relative_or_absolute(packet, destination),
            "output_sha256": sha256(destination),
            "approved_at": now(),
            "approved_by": args.approved_by,
            "updated_at": now(),
        }
    )
    assets["updated_at"] = now()
    write_json(paths["assets"], assets)
    save_bundle(paths, manifest, run)
    print(f"Promoted approved candidate to {destination}")


def mark_stale(record: dict, reason: str) -> None:
    if record.get("status") == "approved" or record.get("current"):
        record["status"] = "stale"
        record["current"] = False
        record["stale_reason"] = reason
        record["updated_at"] = now()


def cmd_invalidate(args: argparse.Namespace) -> None:
    packet = args.packet_dir.resolve()
    paths, manifest, run, style, cast, scene = require_state(packet)
    assets = load_assets(paths["assets"])
    plates = read_json(paths["plates"]) if paths["plates"].exists() else {"status": "pending", "plates": {}}
    names = set(parse_names(args.names))
    reason = args.reason or f"{args.kind} dependency changed"
    run["revisions"][args.kind] += 1
    affected = 0
    if args.kind == "style":
        style.update({"status": "provisional", "revision": run["revisions"]["style"], "approved_at": None, "approved_by": None})
        run["gates"]["style_calibration"] = "pending"
    elif args.kind == "cast":
        cast.update({"status": "provisional", "revision": run["revisions"]["cast"], "approved_at": None, "approved_by": None})
        run["gates"]["cast_approval"] = "pending"
    elif args.kind == "scene":
        scene.update({"status": "provisional", "revision": run["revisions"]["scene"], "approved_at": None, "approved_by": None})
        run["gates"]["scene_storyboard"] = "pending"
    stale_plates = 0
    if args.kind in {"style", "cast", "scene"}:
        for plate in plates.get("plates", {}).values():
            match = args.kind == "style"
            if args.kind == "cast":
                chars = set(plate.get("characters", []))
                match = bool(chars and (not names or chars & names))
            elif args.kind == "scene":
                match = bool(plate.get("scene") and (not names or plate.get("scene") in names))
            if match and plate.get("status") == "approved":
                plate["status"] = "stale"
                plate["current"] = False
                plate["stale_reason"] = reason
                stale_plates += 1
        if stale_plates:
            plates["status"] = "stale"
            run["gates"]["art_plates"] = "pending"
    for record in assets["assets"].values():
        match = False
        if args.kind == "style":
            match = record.get("asset_type") in VISUAL_TYPES
        elif args.kind == "cast":
            chars = set(record.get("characters", []))
            match = bool(chars and (not names or chars & names))
        elif args.kind == "scene":
            match = bool(record.get("scene") and (not names or record.get("scene") in names))
        elif args.kind == "copy":
            keys = set(record.get("copy_keys", []))
            match = bool(keys and (not names or keys & names))
        if match:
            before = record.get("status")
            mark_stale(record, reason)
            affected += before != record.get("status")
    set_manifest_status(manifest, "stale")
    run["status"] = "stale"
    run["events"].append({"at": now(), "event": f"invalidate_{args.kind}", "reason": reason, "names": sorted(names), "affected": affected})
    assets["updated_at"] = now()
    write_json(paths["assets"], assets)
    save_bundle(paths, manifest, run, style=style, cast=cast, scene=scene, plates=plates)
    print(
        f"Invalidated {affected} assets and {stale_plates} art plates "
        f"for {args.kind} revision {run['revisions'][args.kind]}"
    )


def verify_asset_current(packet: Path, source: str, record: dict, run: dict) -> None:
    if record.get("status") != "approved" or not record.get("current"):
        raise SystemExit(f"Asset is not approved/current: {source}")
    verify_dependencies(record, run)
    path = resolve_path(packet, source)
    if not path.is_file() or sha256(path) != record.get("output_sha256"):
        raise SystemExit(f"Asset hash mismatch: {source}")


def cmd_approve_run(args: argparse.Namespace) -> None:
    packet = args.packet_dir.resolve()
    paths, manifest, run, style, cast, scene = require_state(packet)
    validate_approval_actor(paths, run, args.approved_by, "run_approval")
    qa_evidence = validate_qa_evidence(
        packet,
        args.approved_by,
        args.qa_report,
        {"assets_current", "source_hashes", "ocr", "contact_sheets", "tier_inventory", "archive_test"},
    )
    for gate, status in run["gates"].items():
        if status != "approved":
            raise SystemExit(f"Cannot approve run; gate {gate} is {status}.")
    distribution = read_json(packet / "distribution-map.json")
    assets = load_assets(paths["assets"])
    for item in distribution.get("items", []):
        source = item.get("source")
        record = assets["assets"].get(source)
        if not record:
            raise SystemExit(f"Mapped asset lacks status record: {source}")
        verify_asset_current(packet, source, record, run)
    set_manifest_status(manifest, "approved")
    run["status"] = "approved"
    run["approved_at"] = now()
    run["approved_by"] = args.approved_by
    run["qa_evidence"] = qa_evidence
    run["events"].append({"at": now(), "event": "run_approved", "by": args.approved_by})
    save_bundle(paths, manifest, run)
    print("Run approved and ready for locked packaging")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--packet-dir", required=True, type=Path)
    sub = parser.add_subparsers(dest="command", required=True)

    init = sub.add_parser("init")
    init.add_argument("--run-id")
    init.add_argument("--force", action="store_true")
    init.set_defaults(func=cmd_init)

    policy = sub.add_parser("set-approval-policy")
    policy.add_argument(
        "--mode",
        required=True,
        choices=(
            "single_visual_checkpoint",
            "autonomous_full_run",
            "explicit_all_gates",
            "delegated_after_style_and_cast",
        ),
    )
    policy.add_argument("--authorized-by", required=True)
    policy.add_argument("--notes")
    policy.set_defaults(func=cmd_set_approval_policy)

    style = sub.add_parser("approve-style")
    style.add_argument("--character-proof", required=True)
    style.add_argument("--scene-proof", required=True)
    style.add_argument("--page-proof", required=True)
    style.add_argument("--map-proof", required=True)
    style.add_argument("--reference", action="append")
    style.add_argument("--approved-by", required=True)
    style.add_argument("--qa-report")
    style.add_argument("--notes")
    style.set_defaults(func=cmd_approve_style)

    cast = sub.add_parser("approve-cast")
    cast.add_argument("--cast-sheet", required=True)
    cast.add_argument("--crops-json", required=True)
    cast.add_argument("--characters-json", required=True)
    cast.add_argument("--approved-by", required=True)
    cast.add_argument("--qa-report")
    cast.add_argument("--notes")
    cast.set_defaults(func=cmd_approve_cast)

    scenes = sub.add_parser("approve-scenes")
    scenes.add_argument("--storyboard", required=True)
    scenes.add_argument("--scenes-json", required=True)
    scenes.add_argument("--approved-by", required=True)
    scenes.add_argument("--qa-report")
    scenes.add_argument("--notes")
    scenes.set_defaults(func=cmd_approve_scenes)

    plates = sub.add_parser("approve-art-plates")
    plates.add_argument("--plates-json", required=True)
    plates.add_argument("--approved-by", required=True)
    plates.add_argument("--qa-report")
    plates.add_argument("--notes")
    plates.set_defaults(func=cmd_approve_plates)

    register = sub.add_parser("register-candidate")
    register.add_argument("--asset", required=True)
    register.add_argument("--asset-type", required=True, choices=sorted(VISUAL_TYPES))
    register.add_argument("--candidate", required=True)
    register.add_argument("--prompt", required=True)
    register.add_argument("--reference", action="append")
    register.add_argument("--characters", action="append")
    register.add_argument("--scene")
    register.add_argument("--art-plates", action="append")
    register.add_argument("--copy-keys", action="append")
    register.set_defaults(func=cmd_register)

    qa = sub.add_parser("record-qa")
    qa.add_argument("--asset", required=True)
    qa.add_argument("--result", required=True, choices=("pass", "fail"))
    qa.add_argument("--checked-by", required=True)
    qa.add_argument("--notes")
    qa.add_argument("--ocr-report")
    qa.add_argument("--visual-report")
    qa.set_defaults(func=cmd_qa)

    promote = sub.add_parser("promote")
    promote.add_argument("--asset", required=True)
    promote.add_argument("--approved-by", required=True)
    promote.set_defaults(func=cmd_promote)

    invalidate = sub.add_parser("invalidate")
    invalidate.add_argument("--kind", required=True, choices=("style", "cast", "scene", "copy"))
    invalidate.add_argument("--names", action="append")
    invalidate.add_argument("--reason")
    invalidate.set_defaults(func=cmd_invalidate)

    approve = sub.add_parser("approve-run")
    approve.add_argument("--approved-by", required=True)
    approve.add_argument("--qa-report")
    approve.set_defaults(func=cmd_approve_run)
    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
