#!/usr/bin/env python3
"""Atomic checkpoint manager for Codex-generated ODOS text packets."""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
import os
import re
import shutil
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


DEFAULT_ROOT = Path(
    os.environ.get("ODOS_TEXT_PACKET_ROOT")
    or Path.home() / "OneDrive" / "Desktop" / "New Text Packet"
)

STAGE_FILES = {
    "monthly_options": "monthly_options.md",
    "adventure_skeleton": "adventure_skeleton.md",
    "dm_packet": "dm_packet.md",
    "npc_suite": "npc_suite.md",
    "clue_web": "clue_web.md",
    "stat_blocks": "stat_blocks.md",
    "handouts": "player_handouts.md",
    "visual_asset_brief": "visual_asset_brief.md",
}
STAGE_ORDER = list(STAGE_FILES)
STAGE_HEADINGS = {
    "adventure_skeleton": "# Adventure Skeleton",
    "dm_packet": "# DM Packet Draft",
    "npc_suite": "# NPC Suite",
    "clue_web": "# Clue Web",
    "stat_blocks": "# Stat Blocks",
    "handouts": "# Player Handouts",
    "visual_asset_brief": "# Visual Asset Brief",
}
STAGE_LABELS = {
    "monthly_options": "Monthly Options",
    "adventure_skeleton": "Adventure Skeleton",
    "dm_packet": "DM Packet Draft",
    "npc_suite": "NPC Suite",
    "clue_web": "Clue Web",
    "stat_blocks": "Stat Blocks",
    "handouts": "Player Handouts",
    "visual_asset_brief": "Visual Asset Brief",
}
VISUAL_BOUNDARY = (
    "This file is subject inventory only. ODOSv4 owns image references, page samples, "
    "final art style, visual-noise controls, and image prompt construction."
)


class PacketError(RuntimeError):
    pass


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


def history_stamp() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")


def atomic_write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.{uuid.uuid4().hex}.tmp")
    try:
        with temporary.open("w", encoding="utf-8", newline="\n") as handle:
            handle.write(text)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
    finally:
        if temporary.exists():
            temporary.unlink()


def atomic_write_json(path: Path, data: dict[str, Any]) -> None:
    atomic_write_text(path, json.dumps(data, indent=2, ensure_ascii=True) + "\n")


def load_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise PacketError(f"Required file is missing: {path}") from exc
    except json.JSONDecodeError as exc:
        raise PacketError(f"Invalid JSON in {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise PacketError(f"Expected a JSON object in {path}.")
    return value


def archive_file(path: Path) -> Path | None:
    if not path.exists():
        return None
    history = path.parent / ".history"
    history.mkdir(parents=True, exist_ok=True)
    archived = history / f"{path.stem}.{history_stamp()}{path.suffix}"
    shutil.copy2(path, archived)
    return archived


def safe_windows_name(value: str, fallback: str = "ODOS Packet") -> str:
    cleaned = re.sub(r"[<>:\"/\\|?*\x00-\x1f]", " ", value or "")
    cleaned = re.sub(r"\s+", " ", cleaned).strip(" .")
    reserved = {
        "CON",
        "PRN",
        "AUX",
        "NUL",
        *(f"COM{i}" for i in range(1, 10)),
        *(f"LPT{i}" for i in range(1, 10)),
    }
    if not cleaned or cleaned.upper() in reserved:
        cleaned = fallback
    return cleaned[:100].rstrip(" .") or fallback


def packet_folder(value: str) -> Path:
    folder = Path(value).expanduser().resolve()
    if not folder.is_dir():
        raise PacketError(f"Packet folder does not exist: {folder}")
    if not (folder / "progress.json").is_file():
        raise PacketError(f"Not an ODOS Text Studio packet folder: {folder}")
    return folder


def packet_documents(folder: Path) -> tuple[dict[str, Any], dict[str, Any]]:
    return load_json(folder / "progress.json"), load_json(folder / "project.json")


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def markdown_cells(line: str) -> list[str]:
    return [cell.strip() for cell in line.strip().strip("|").split("|")]


def parse_monthly_options(text: str) -> list[dict[str, str]]:
    nonblank = [line.strip() for line in text.splitlines() if line.strip()]
    if len(nonblank) != 22:
        raise PacketError("Monthly Options must contain one header, one separator, and exactly 20 rows.")

    header = markdown_cells(nonblank[0])
    expected = ["#", "Adventure Style / Structure", "Main Quest Premise", "Antagonist"]
    if header != expected:
        raise PacketError(f"Monthly Options header must be exactly: | {' | '.join(expected)} |")

    separator = markdown_cells(nonblank[1])
    if len(separator) != 4 or any(not re.fullmatch(r":?-{3,}:?", cell) for cell in separator):
        raise PacketError("Monthly Options has an invalid Markdown table separator.")

    rows: list[dict[str, str]] = []
    for expected_number, line in enumerate(nonblank[2:], start=1):
        cells = markdown_cells(line)
        if len(cells) != 4:
            raise PacketError(f"Monthly Options row {expected_number} must have four table cells.")
        if cells[0] != str(expected_number):
            raise PacketError(f"Monthly Options rows must be numbered 1-20; expected {expected_number}.")
        if any(not cell for cell in cells[1:]):
            raise PacketError(f"Monthly Options row {expected_number} contains an empty option.")
        rows.append(
            {
                "number": cells[0],
                "style": cells[1],
                "quest": cells[2],
                "antagonist": cells[3],
            }
        )
    return rows


def validate_stage(stage: str, text: str) -> None:
    normalized = text.replace("\r\n", "\n").strip()
    if not normalized:
        raise PacketError(f"{STAGE_LABELS[stage]} is empty.")

    if stage == "monthly_options":
        parse_monthly_options(normalized)
        return

    first_line = normalized.splitlines()[0].strip()
    if first_line != STAGE_HEADINGS[stage]:
        raise PacketError(f"{STAGE_LABELS[stage]} must start with: {STAGE_HEADINGS[stage]}")

    if stage == "handouts":
        handouts = re.findall(r"^## Handout ([123])\s*$", normalized, flags=re.MULTILINE)
        if handouts != ["1", "2", "3"]:
            raise PacketError("Player Handouts must contain exactly Handout 1, Handout 2, and Handout 3.")

    if stage == "visual_asset_brief":
        if normalized.count(VISUAL_BOUNDARY) != 1:
            raise PacketError("Visual Asset Brief must contain the exact ODOSv4 use-boundary sentence once.")


def computed_next(progress: dict[str, Any]) -> str:
    stages = progress.get("stages", {})
    if stages.get("monthly_options", {}).get("status") != "complete":
        return "monthly_options"
    if not progress.get("selectedOption"):
        return "awaiting_selection"
    for stage in STAGE_ORDER[1:]:
        if stages.get(stage, {}).get("status") != "complete":
            return stage
    return "finalize"


def refresh_packet_status(progress: dict[str, Any]) -> None:
    next_step = computed_next(progress)
    if progress.get("status") == "complete" and next_step == "finalize":
        return
    if next_step == "awaiting_selection":
        progress["status"] = "awaiting_selection"
    elif next_step == "finalize":
        progress["status"] = "ready_to_finalize"
    else:
        progress["status"] = "generating"


def sync_project_stage(
    project_doc: dict[str, Any], stage: str, stage_state: dict[str, Any]
) -> None:
    sections = project_doc.setdefault("sections", {})
    sections[stage] = {
        "file": STAGE_FILES[stage],
        "status": stage_state.get("status", "pending"),
        "updatedAt": stage_state.get("updatedAt"),
        "sha256": stage_state.get("sha256"),
        "revision": stage_state.get("revision", 0),
    }


def command_init(args: argparse.Namespace) -> None:
    root = Path(args.root).expanduser().resolve()
    saved = root / "Saved"
    exported = root / "Exported"
    saved.mkdir(parents=True, exist_ok=True)
    exported.mkdir(parents=True, exist_ok=True)

    title = args.title.strip() or "Untitled One-Shot"
    base = safe_windows_name(f"{title} [working]")
    folder = saved / base
    suffix = 2
    while folder.exists():
        folder = saved / safe_windows_name(f"{title} [working {suffix}]")
        suffix += 1
    folder.mkdir(parents=False)

    created = now_iso()
    packet_id = uuid.uuid4().hex
    project_values = {
        "workingTitle": title,
        "releaseMonth": args.release_month,
        "levelRange": args.level_range,
        "partySize": args.party_size,
        "tone": args.tone,
        "difficulty": args.difficulty,
        "themeNotes": args.theme_notes,
        "bannedConcepts": args.banned_concepts,
    }
    stages = {
        stage: {
            "file": file_name,
            "status": "pending",
            "updatedAt": None,
            "sha256": None,
            "revision": 0,
        }
        for stage, file_name in STAGE_FILES.items()
    }
    progress = {
        "schemaVersion": 1,
        "generator": "odos-text-studio",
        "packetId": packet_id,
        "status": "generating",
        "createdAt": created,
        "updatedAt": created,
        "selectedOption": None,
        "stages": stages,
        "exportedPath": None,
    }
    project_doc = {
        "schemaVersion": 1,
        "generator": "odos-text-studio",
        "packetId": packet_id,
        "storageRoot": str(root),
        "createdAt": created,
        "updatedAt": created,
        "project": project_values,
        "selectedOption": None,
        "sections": {
            stage: {
                "file": file_name,
                "status": "pending",
                "updatedAt": None,
                "sha256": None,
                "revision": 0,
            }
            for stage, file_name in STAGE_FILES.items()
        },
    }
    atomic_write_json(folder / "project.json", project_doc)
    atomic_write_json(folder / "progress.json", progress)
    print(
        json.dumps(
            {
                "ok": True,
                "packet": str(folder),
                "packetId": packet_id,
                "next": "monthly_options",
            },
            indent=2,
        )
    )


def command_save_stage(args: argparse.Namespace) -> None:
    folder = packet_folder(args.packet)
    progress, project_doc = packet_documents(folder)
    input_path = Path(args.input).expanduser().resolve()
    try:
        text = input_path.read_text(encoding="utf-8")
    except FileNotFoundError as exc:
        raise PacketError(f"Draft file does not exist: {input_path}") from exc

    validate_stage(args.stage, text)
    normalized = text.replace("\r\n", "\n").rstrip() + "\n"
    target = folder / STAGE_FILES[args.stage]
    archived = archive_file(target)
    atomic_write_text(target, normalized)

    updated = now_iso()
    prior = progress.setdefault("stages", {}).setdefault(args.stage, {})
    stage_state = {
        "file": STAGE_FILES[args.stage],
        "status": "complete",
        "updatedAt": updated,
        "sha256": sha256_text(normalized),
        "revision": int(prior.get("revision") or 0) + 1,
    }
    progress["stages"][args.stage] = stage_state
    progress["updatedAt"] = updated
    refresh_packet_status(progress)

    project_doc["updatedAt"] = updated
    sync_project_stage(project_doc, args.stage, stage_state)
    atomic_write_json(folder / "project.json", project_doc)
    atomic_write_json(folder / "progress.json", progress)

    print(
        json.dumps(
            {
                "ok": True,
                "stage": args.stage,
                "file": str(target),
                "revision": stage_state["revision"],
                "archived": str(archived) if archived else None,
                "next": computed_next(progress),
            },
            indent=2,
        )
    )


def selected_concept_markdown(project_doc: dict[str, Any], selected: dict[str, Any]) -> str:
    project = project_doc.get("project", {})
    return "\n".join(
        [
            "# Selected Concept",
            "",
            "## Project",
            "",
            f"Working title: {project.get('workingTitle', '')}",
            f"Release month: {project.get('releaseMonth', '')}",
            f"Level range: {project.get('levelRange', '')}",
            f"Party size: {project.get('partySize', '')}",
            f"Tone: {project.get('tone', '')}",
            f"Difficulty: {project.get('difficulty', '')}",
            f"Theme notes: {project.get('themeNotes', '')}",
            f"Banned concepts: {project.get('bannedConcepts', '')}",
            "",
            "## Adventure Style / Structure",
            "",
            selected["style"],
            "",
            "## Main Quest Premise",
            "",
            selected["quest"],
            "",
            "## Antagonist",
            "",
            selected["antagonist"],
            "",
            "## Selection Indexes",
            "",
            f"Style: {selected['styleIndex']}",
            f"Quest: {selected['questIndex']}",
            f"Antagonist: {selected['antagonistIndex']}",
            "",
        ]
    )


def command_select(args: argparse.Namespace) -> None:
    folder = packet_folder(args.packet)
    progress, project_doc = packet_documents(folder)
    options_path = folder / STAGE_FILES["monthly_options"]
    try:
        rows = parse_monthly_options(options_path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise PacketError("Generate and save Monthly Options before selecting.") from exc

    for label, value in (
        ("style", args.style),
        ("quest", args.quest),
        ("antagonist", args.antagonist),
    ):
        if value < 1 or value > 20:
            raise PacketError(f"{label.title()} selection must be between 1 and 20.")

    selected = {
        "styleIndex": args.style,
        "questIndex": args.quest,
        "antagonistIndex": args.antagonist,
        "style": rows[args.style - 1]["style"],
        "quest": rows[args.quest - 1]["quest"],
        "antagonist": rows[args.antagonist - 1]["antagonist"],
    }
    updated = now_iso()
    progress["selectedOption"] = selected
    progress["updatedAt"] = updated
    refresh_packet_status(progress)
    project_doc["selectedOption"] = selected
    project_doc["updatedAt"] = updated

    atomic_write_text(folder / "selected_concept.md", selected_concept_markdown(project_doc, selected))
    atomic_write_json(folder / "project.json", project_doc)
    atomic_write_json(folder / "progress.json", progress)
    print(
        json.dumps(
            {
                "ok": True,
                "packet": str(folder),
                "selectedOption": selected,
                "next": computed_next(progress),
            },
            indent=2,
        )
    )


def packet_summary(folder: Path) -> dict[str, Any]:
    progress, project_doc = packet_documents(folder)
    project = project_doc.get("project", {})
    completed = [
        stage
        for stage in STAGE_ORDER
        if progress.get("stages", {}).get(stage, {}).get("status") == "complete"
    ]
    return {
        "packet": str(folder),
        "title": project.get("workingTitle", folder.name),
        "status": progress.get("status", "unknown"),
        "next": computed_next(progress),
        "completedStages": completed,
        "completedCount": len(completed),
        "stageCount": len(STAGE_ORDER),
        "updatedAt": progress.get("updatedAt"),
        "exportedPath": progress.get("exportedPath"),
    }


def command_status(args: argparse.Namespace) -> None:
    print(json.dumps(packet_summary(packet_folder(args.packet)), indent=2))


def command_next(args: argparse.Namespace) -> None:
    progress, _ = packet_documents(packet_folder(args.packet))
    print(computed_next(progress))


def command_list(args: argparse.Namespace) -> None:
    root = Path(args.root).expanduser().resolve()
    saved = root / "Saved"
    packets = []
    if saved.is_dir():
        for child in saved.iterdir():
            if child.is_dir() and (child / "progress.json").is_file():
                try:
                    packets.append(packet_summary(child.resolve()))
                except PacketError:
                    continue
    packets.sort(key=lambda item: item.get("updatedAt") or "", reverse=True)
    print(json.dumps({"root": str(root), "packets": packets}, indent=2))


def command_invalidate(args: argparse.Namespace) -> None:
    folder = packet_folder(args.packet)
    progress, project_doc = packet_documents(folder)
    index = STAGE_ORDER.index(args.from_stage)
    invalidated: list[str] = []
    for stage in STAGE_ORDER[index + 1 :]:
        state = progress.get("stages", {}).get(stage, {})
        target = folder / STAGE_FILES[stage]
        if target.exists():
            archive_file(target)
            target.unlink()
        if state.get("status") == "complete" or state.get("status") == "stale":
            state["status"] = "stale"
            state["updatedAt"] = now_iso()
            state["sha256"] = None
            progress["stages"][stage] = state
            sync_project_stage(project_doc, stage, state)
            invalidated.append(stage)

    updated = now_iso()
    progress["updatedAt"] = updated
    progress["exportedPath"] = None
    progress["status"] = "generating"
    refresh_packet_status(progress)
    project_doc["updatedAt"] = updated
    project_doc.pop("exportedPath", None)
    atomic_write_json(folder / "project.json", project_doc)
    atomic_write_json(folder / "progress.json", progress)
    print(json.dumps({"ok": True, "invalidated": invalidated, "next": computed_next(progress)}, indent=2))


def extract_names_from_npc_suite(path: Path) -> set[str]:
    try:
        text = path.read_text(encoding="utf-8")
    except (OSError, UnicodeError):
        return set()

    names: set[str] = set()
    in_roster = False
    for line in text.splitlines():
        stripped = line.strip()
        if stripped == "## NPC Roster Table":
            in_roster = True
            continue
        if in_roster and stripped.startswith("## "):
            in_roster = False
        if in_roster and stripped.startswith("|"):
            cells = markdown_cells(stripped)
            if cells and cells[0] and cells[0].lower() not in {"name", "npc", "---"}:
                candidate = re.sub(r"[*_`]", "", cells[0]).strip()
                if re.fullmatch(r"[A-Z][A-Za-z' -]{2,60}", candidate):
                    names.add(candidate)
        match = re.match(r"^###\s+([A-Z][A-Za-z' -]{2,60})\s*$", stripped)
        if match:
            candidate = match.group(1).strip()
            if candidate.lower() not in {
                "handout type",
                "player-facing artifact",
                "image-heavy description",
                "readable text on the handout",
                "physical / digital use",
            }:
                names.add(candidate)
    return names


def command_history_names(args: argparse.Namespace) -> None:
    root = Path(args.root).expanduser().resolve()
    candidates: list[Path] = []
    for base in (root / "Saved", root / "Exported"):
        if base.is_dir():
            candidates.extend(base.rglob("npc_suite.md"))
    candidates.sort(key=lambda path: path.stat().st_mtime, reverse=True)

    names: list[str] = []
    seen: set[str] = set()
    for path in candidates:
        for name in sorted(extract_names_from_npc_suite(path)):
            key = name.casefold()
            if key not in seen:
                seen.add(key)
                names.append(name)
        if len(names) >= args.limit:
            break
    print(json.dumps({"root": str(root), "names": names[: args.limit]}, indent=2))


def next_export_folder(root: Path, title: str) -> Path:
    exported = root / "Exported"
    exported.mkdir(parents=True, exist_ok=True)
    safe_title = safe_windows_name(title)
    pattern = re.compile(
        rf"^{re.escape(safe_title)} v(\d+) \d{{2}}-\d{{2}}-\d{{2}}$", re.IGNORECASE
    )
    version = 0
    for child in exported.iterdir():
        if not child.is_dir():
            continue
        match = pattern.match(child.name)
        if match:
            version = max(version, int(match.group(1)))
    date_stamp = datetime.now().astimezone().strftime("%d-%m-%y")
    return exported / f"{safe_title} v{version + 1} {date_stamp}"


def handoff_markdown(project_doc: dict[str, Any]) -> str:
    project = project_doc.get("project", {})
    selected = project_doc.get("selectedOption") or {}
    source_lines = [f"- {STAGE_LABELS[stage]}: `{file_name}`" for stage, file_name in STAGE_FILES.items()]
    return "\n".join(
        [
            "# ODOS Packet Build Handoff",
            "",
            "## Goal",
            "",
            "Build a complete One Dollar One Shots-style D&D 5e production packet from this text-only export.",
            "",
            "## Project Constraints",
            "",
            f"Working title: {project.get('workingTitle', '')}",
            f"Release month: {project.get('releaseMonth', '')}",
            f"Level range: {project.get('levelRange', '')}",
            f"Party size: {project.get('partySize', '')}",
            f"Tone: {project.get('tone', '')}",
            f"Difficulty: {project.get('difficulty', '')}",
            f"Theme notes: {project.get('themeNotes', '')}",
            f"Banned concepts: {project.get('bannedConcepts', '')}",
            "",
            "## Selected Concept",
            "",
            f"Adventure Style / Structure: {selected.get('style', '')}",
            f"Main Quest Premise: {selected.get('quest', '')}",
            f"Antagonist: {selected.get('antagonist', '')}",
            "",
            "## Source Files",
            "",
            *source_lines,
            "",
            "## Production Boundary",
            "",
            "Read the source files in generation order and treat them as the source of truth for premise, scene flow, clues, names, handouts, and mechanics.",
            "",
            "`visual_asset_brief.md` is subject inventory only. It is not an image prompt or style authority.",
            "",
            "This export intentionally contains no image assets, page samples, visual reference folders, or page-layout assets.",
            "",
        ]
    )


def command_finalize(args: argparse.Namespace) -> None:
    folder = packet_folder(args.packet)
    progress, project_doc = packet_documents(folder)
    if not progress.get("selectedOption"):
        raise PacketError("Select one option from each Monthly Options column before finalizing.")

    missing: list[str] = []
    for stage, file_name in STAGE_FILES.items():
        path = folder / file_name
        if progress.get("stages", {}).get(stage, {}).get("status") != "complete" or not path.is_file():
            missing.append(stage)
            continue
        validate_stage(stage, path.read_text(encoding="utf-8"))
    if missing:
        raise PacketError("Cannot finalize; incomplete stages: " + ", ".join(missing))

    handoff_path = folder / "codex_handoff.md"
    atomic_write_text(handoff_path, handoff_markdown(project_doc))

    root = Path(project_doc.get("storageRoot") or DEFAULT_ROOT).expanduser().resolve()
    title = str(project_doc.get("project", {}).get("workingTitle") or "ODOS Packet")
    destination = next_export_folder(root, title)
    temporary = destination.parent / f".building-{uuid.uuid4().hex}"
    temporary.mkdir(parents=False)
    try:
        export_project = copy.deepcopy(project_doc)
        export_project["status"] = "complete"
        export_project["exportedPath"] = str(destination)
        export_project["updatedAt"] = now_iso()
        atomic_write_json(temporary / "project.json", export_project)
        shutil.copy2(folder / "selected_concept.md", temporary / "selected_concept.md")
        for file_name in STAGE_FILES.values():
            shutil.copy2(folder / file_name, temporary / file_name)
        shutil.copy2(handoff_path, temporary / "codex_handoff.md")
        os.replace(temporary, destination)
    finally:
        if temporary.exists():
            shutil.rmtree(temporary)

    updated = now_iso()
    progress["status"] = "complete"
    progress["updatedAt"] = updated
    progress["exportedPath"] = str(destination)
    project_doc["status"] = "complete"
    project_doc["updatedAt"] = updated
    project_doc["exportedPath"] = str(destination)
    atomic_write_json(folder / "project.json", project_doc)
    atomic_write_json(folder / "progress.json", progress)
    print(json.dumps({"ok": True, "workingPacket": str(folder), "exportedPacket": str(destination)}, indent=2))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)

    init_parser = subparsers.add_parser("init", help="Create a new working packet.")
    init_parser.add_argument("--root", default=str(DEFAULT_ROOT))
    init_parser.add_argument("--title", required=True)
    init_parser.add_argument("--release-month", default="Unspecified")
    init_parser.add_argument("--level-range", default="3-8")
    init_parser.add_argument("--party-size", default="2-6")
    init_parser.add_argument("--tone", default="Unspecified")
    init_parser.add_argument("--difficulty", default="Moderate")
    init_parser.add_argument("--theme-notes", default="None")
    init_parser.add_argument("--banned-concepts", default="None")
    init_parser.set_defaults(func=command_init)

    save_parser = subparsers.add_parser("save-stage", help="Validate and atomically checkpoint a stage.")
    save_parser.add_argument("--packet", required=True)
    save_parser.add_argument("--stage", choices=STAGE_ORDER, required=True)
    save_parser.add_argument("--input", required=True)
    save_parser.set_defaults(func=command_save_stage)

    select_parser = subparsers.add_parser("select", help="Choose one option from each Monthly Options column.")
    select_parser.add_argument("--packet", required=True)
    select_parser.add_argument("--style", type=int, required=True)
    select_parser.add_argument("--quest", type=int, required=True)
    select_parser.add_argument("--antagonist", type=int, required=True)
    select_parser.set_defaults(func=command_select)

    status_parser = subparsers.add_parser("status", help="Show checkpoint status for one packet.")
    status_parser.add_argument("--packet", required=True)
    status_parser.set_defaults(func=command_status)

    next_parser = subparsers.add_parser("next", help="Print the next required stage.")
    next_parser.add_argument("--packet", required=True)
    next_parser.set_defaults(func=command_next)

    list_parser = subparsers.add_parser("list", help="List saved working packets.")
    list_parser.add_argument("--root", default=str(DEFAULT_ROOT))
    list_parser.set_defaults(func=command_list)

    invalidate_parser = subparsers.add_parser("invalidate", help="Archive and mark downstream stages stale.")
    invalidate_parser.add_argument("--packet", required=True)
    invalidate_parser.add_argument("--from-stage", choices=STAGE_ORDER, required=True)
    invalidate_parser.set_defaults(func=command_invalidate)

    names_parser = subparsers.add_parser("history-names", help="List prior NPC names to avoid.")
    names_parser.add_argument("--root", default=str(DEFAULT_ROOT))
    names_parser.add_argument("--limit", type=int, default=200)
    names_parser.set_defaults(func=command_history_names)

    finalize_parser = subparsers.add_parser("finalize", help="Create a versioned text-only export.")
    finalize_parser.add_argument("--packet", required=True)
    finalize_parser.set_defaults(func=command_finalize)

    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    try:
        args.func(args)
    except PacketError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    except OSError as exc:
        print(f"error: filesystem operation failed: {exc}", file=sys.stderr)
        return 3
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
