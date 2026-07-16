#!/usr/bin/env python3
"""Discover, initialize, checkpoint, and validate ODOS media campaigns."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import zipfile
from collections import Counter
from datetime import date, datetime, time, timedelta, timezone
from pathlib import Path, PurePosixPath
from typing import Any


TIERS = ("Basic", "Deluxe", "Premium")
ISO_RE = re.compile(r"20\d{2}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?(?:Z|[+-]\d{2}:\d{2})")
RUN_RE = re.compile(r"\brun\s+([A-Za-z0-9_-]+)", re.IGNORECASE)
WORD_RE = re.compile(r"\b[\w'’-]+\b", re.UNICODE)
DELIVERABLE_STATES = {
    "planned",
    "drafted",
    "media_ready",
    "qa_passed",
    "approved",
    "scheduled",
    "published",
    "blocked",
    "failed",
}
CAMPAIGN_PHASES = (
    "source_locked",
    "brief_complete",
    "copy_complete",
    "media_complete",
    "qa_complete",
    "approved",
    "publishing",
    "complete",
)
IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".webp"}


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def parse_datetime(value: str) -> datetime:
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    return parsed if parsed.tzinfo else parsed.replace(tzinfo=timezone.utc)


def iso_utc(value: datetime) -> str:
    return value.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def read_json(path: Path, default: Any = None) -> Any:
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding="utf-8"))


def atomic_write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_suffix(path.suffix + ".tmp")
    temp.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    os.replace(temp, path)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def fingerprint(payload: Any) -> str:
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def slugify(value: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
    return slug or "adventure"


def safe_member(name: str) -> bool:
    normalized = name.replace("\\", "/")
    path = PurePosixPath(normalized)
    return not path.is_absolute() and ".." not in path.parts and not re.match(r"^[A-Za-z]:", normalized)


def version_tuple(value: str) -> tuple[int, ...]:
    return tuple(int(item) for item in re.findall(r"\d+", value)[:3])


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
        except (ImportError, OSError):
            pass

    candidates: list[Path] = []
    for variable in ("OneDrive", "OneDriveConsumer", "OneDriveCommercial"):
        root = os.environ.get(variable)
        if root:
            candidates.append(Path(root) / "Desktop")
    candidates.append(Path.home() / "Desktop")
    for candidate in candidates:
        if candidate.exists():
            return candidate
    raise FileNotFoundError("Could not resolve the Windows Desktop directory")


def default_output_root() -> Path:
    configured = os.environ.get("ODOS_MEDIA_OUTPUT_ROOT")
    return Path(configured).expanduser() if configured else Path.cwd() / "outputs" / "odos-media"


def marker_metadata(path: Path) -> dict[str, Any]:
    text_value = path.read_text(encoding="utf-8", errors="replace")[:4096]
    iso_match = ISO_RE.search(text_value)
    ready_at = (
        parse_datetime(iso_match.group(0))
        if iso_match
        else datetime.fromtimestamp(path.stat().st_mtime, timezone.utc)
    )
    run_match = RUN_RE.search(text_value)
    return {
        "text": text_value.strip(),
        "ready_at": iso_utc(ready_at),
        "selected_by": "Ready.txt embedded timestamp" if iso_match else "Ready.txt filesystem timestamp fallback",
        "run_hint": run_match.group(1) if run_match else None,
    }


def load_config(path: Path | None) -> dict[str, Any]:
    skill_root = Path(__file__).resolve().parents[1]
    config_path = path or skill_root / "references" / "channel-config.json"
    config = read_json(config_path, {})
    if not isinstance(config, dict) or not config.get("campaign"):
        raise ValueError(f"Invalid channel configuration: {config_path}")
    return config


def public_inventory(members: set[str], tier: str) -> set[str]:
    prefix = tier + "/"
    result = set()
    for member in members:
        relative = member[len(prefix) :] if member.startswith(prefix) else member
        lowered = relative.lower()
        if lowered.startswith("manifest-") or lowered.startswith("pdf/"):
            continue
        result.add(relative)
    return result


def validate_zip(path: Path, tier: str, title: str, minimum_version: str, verify_crc: bool) -> dict[str, Any]:
    errors: list[str] = []
    manifest: dict[str, Any] = {}
    members: set[str] = set()
    inventory: list[dict[str, Any]] = []
    try:
        with zipfile.ZipFile(path, "r") as archive:
            infos = [item for item in archive.infolist() if not item.is_dir()]
            members = {item.filename.replace("\\", "/") for item in infos}
            if not infos:
                errors.append(f"{tier} ZIP is empty")
            unsafe = sorted(item for item in members if not safe_member(item))
            if unsafe:
                errors.append(f"{tier} ZIP contains unsafe paths: {unsafe[:3]}")
            rejected = sorted(item for item in members if "failed" in item.lower())
            if rejected:
                errors.append(f"{tier} ZIP contains rejected proof files: {rejected[:3]}")
            wrong_roots = sorted(item for item in members if not item.startswith(tier + "/"))
            if wrong_roots:
                errors.append(f"{tier} ZIP has files outside the {tier}/ root")
            if verify_crc:
                bad_member = archive.testzip()
                if bad_member:
                    errors.append(f"{tier} ZIP CRC failed at {bad_member}")

            expected_manifest = f"{tier}/manifest-{tier.lower()}.json"
            found = [item for item in members if item.lower() == expected_manifest.lower()]
            if len(found) != 1:
                errors.append(f"{tier} ZIP must contain exactly one {expected_manifest}")
            else:
                expected_manifest = found[0]
                try:
                    manifest = json.loads(archive.read(expected_manifest).decode("utf-8"))
                except (UnicodeDecodeError, json.JSONDecodeError) as exc:
                    errors.append(f"{tier} manifest is invalid JSON: {exc}")

            if manifest:
                if manifest.get("title") != title:
                    errors.append(f"{tier} manifest title does not match folder title")
                if manifest.get("tier") != tier:
                    errors.append(f"{tier} manifest tier is {manifest.get('tier')!r}")
                actual_version = version_tuple(str(manifest.get("skill_version", "")))
                required_version = version_tuple(minimum_version)
                if not actual_version or actual_version < required_version:
                    errors.append(
                        f"{tier} manifest skill version {manifest.get('skill_version')!r} is below {minimum_version}"
                    )
                files = manifest.get("files")
                if not isinstance(files, list) or not files:
                    errors.append(f"{tier} manifest has no file inventory")
                    files = []
                expected_members = {expected_manifest}
                has_cover = False
                for item in files:
                    relative = str(item.get("file", "")).replace("\\", "/").lstrip("/")
                    if not relative or not safe_member(relative):
                        errors.append(f"{tier} manifest contains an invalid file path")
                        continue
                    archive_member = f"{tier}/{relative}"
                    expected_members.add(archive_member)
                    has_cover = has_cover or item.get("role") == "cover"
                    inventory.append(
                        {
                            "archive_member": archive_member,
                            "relative_path": relative,
                            "role": item.get("role", "unknown"),
                            "source": item.get("source"),
                            "source_sha256": item.get("source_sha256"),
                            "prompt_sha256": item.get("prompt_sha256"),
                            "pdf_order": item.get("pdf_order"),
                        }
                    )
                missing = sorted(expected_members - members)
                extra = sorted(members - expected_members)
                if missing:
                    errors.append(f"{tier} ZIP is missing manifest files: {missing[:3]}")
                if extra:
                    errors.append(f"{tier} ZIP has unmanifested files: {extra[:3]}")
                if not has_cover:
                    errors.append(f"{tier} manifest has no approved cover")
                expected_pdf = f"PDF/{title} - {tier}.pdf"
                pdfs = [item for item in files if item.get("role") == "pdf"]
                if len(pdfs) != 1 or str(pdfs[0].get("file", "")).replace("\\", "/") != expected_pdf:
                    errors.append(f"{tier} ZIP does not contain the expected tier PDF")
    except (OSError, RuntimeError, zipfile.BadZipFile) as exc:
        errors.append(f"{tier} ZIP cannot be read: {exc}")

    return {
        "edition": tier,
        "path": str(path.resolve()),
        "size_bytes": path.stat().st_size if path.exists() else None,
        "sha256": sha256_file(path) if path.exists() else None,
        "entry_count": len(members),
        "run_id": manifest.get("run_id") if manifest else None,
        "skill_version": manifest.get("skill_version") if manifest else None,
        "built_at": manifest.get("built_at") if manifest else None,
        "role_counts": dict(sorted(Counter(str(item.get("role", "unknown")) for item in manifest.get("files", [])).items())),
        "inventory": sorted(public_inventory(members, tier)),
        "manifest_inventory": inventory,
        "errors": errors,
    }


def find_text_source(title: str, ready_at: str, text_root: Path) -> dict[str, Any]:
    base = {
        "status": "missing",
        "search_root": str(text_root.resolve()) if text_root.exists() else str(text_root),
        "project_path": None,
        "project_sha256": None,
        "packet_id": None,
        "updated_at": None,
        "source_files": [],
        "errors": [],
    }
    if not text_root.exists():
        base["errors"].append("Text Studio saved-project root does not exist")
        return base

    matches: list[tuple[Path, dict[str, Any]]] = []
    for project_path in text_root.rglob("project.json"):
        try:
            payload = read_json(project_path, {})
        except (OSError, json.JSONDecodeError):
            continue
        if payload.get("project", {}).get("workingTitle") != title or payload.get("status") != "complete":
            continue
        updated_at = payload.get("updatedAt")
        if updated_at and parse_datetime(updated_at) > parse_datetime(ready_at):
            continue
        matches.append((project_path, payload))

    if len(matches) > 1:
        base["status"] = "ambiguous"
        base["errors"].append(f"Found {len(matches)} complete exact-title Text Studio projects")
        base["candidates"] = [str(item[0].resolve()) for item in matches]
        return base
    if not matches:
        base["errors"].append("No complete exact-title Text Studio project found")
        return base

    project_path, project = matches[0]
    source_files: list[dict[str, Any]] = []
    errors: list[str] = []
    for section_name, section in project.get("sections", {}).items():
        if section.get("status") != "complete":
            errors.append(f"Text section {section_name} is not complete")
            continue
        relative = section.get("file")
        source_path = project_path.parent / str(relative)
        if not source_path.is_file():
            errors.append(f"Text section file is missing: {relative}")
            continue
        actual_hash = sha256_file(source_path)
        expected_hash = section.get("sha256")
        if expected_hash and actual_hash != expected_hash:
            errors.append(f"Text section hash mismatch: {relative}")
        source_files.append(
            {
                "section": section_name,
                "path": str(source_path.resolve()),
                "relative_path": str(relative),
                "sha256": actual_hash,
                "revision": section.get("revision"),
            }
        )

    base.update(
        {
            "status": "invalid" if errors else "matched",
            "project_path": str(project_path.resolve()),
            "project_sha256": sha256_file(project_path),
            "packet_id": project.get("packetId"),
            "updated_at": project.get("updatedAt"),
            "project": project.get("project", {}),
            "selected_option": project.get("selectedOption", {}),
            "source_files": source_files,
            "errors": errors,
        }
    )
    return base


def validate_release(folder: Path, config: dict[str, Any], verify_crc: bool, text_root: Path) -> dict[str, Any]:
    title = folder.name
    source_config = config["source"]
    marker_name = source_config["ready_marker"]
    marker_path = folder / marker_name
    marker = marker_metadata(marker_path)
    expected_names = {marker_name, *(f"{title} - {tier}.zip" for tier in TIERS)}
    children = list(folder.iterdir())
    files = {child.name for child in children if child.is_file()}
    directories = [child.name for child in children if child.is_dir()]
    errors: list[str] = []
    if source_config.get("require_exact_release_files", True):
        missing = sorted(expected_names - files)
        extra = sorted(files - expected_names)
        if missing:
            errors.append(f"Missing required files: {missing}")
        if extra:
            errors.append(f"Unexpected files: {extra}")
        if directories:
            errors.append(f"Unexpected subdirectories: {directories}")

    tier_reports: dict[str, dict[str, Any]] = {}
    for tier in TIERS:
        path = folder / f"{title} - {tier}.zip"
        if not path.exists():
            continue
        report = validate_zip(path, tier, title, source_config["minimum_odos_version"], verify_crc)
        tier_reports[tier] = report
        errors.extend(report["errors"])

    run_ids = {item.get("run_id") for item in tier_reports.values() if item.get("run_id")}
    if len(run_ids) != 1:
        errors.append(f"Tier manifests do not share one run ID: {sorted(run_ids)}")
    run_id = next(iter(run_ids), marker.get("run_hint"))
    if marker.get("run_hint") and run_id and marker["run_hint"] != run_id:
        errors.append("Ready.txt run ID does not match the embedded manifests")

    if all(tier in tier_reports for tier in TIERS):
        basic = set(tier_reports["Basic"]["inventory"])
        deluxe = set(tier_reports["Deluxe"]["inventory"])
        premium = set(tier_reports["Premium"]["inventory"])
        if not basic < deluxe:
            errors.append("Deluxe must strictly include every Basic asset plus additional assets")
        if not deluxe < premium:
            errors.append("Premium must strictly include every Deluxe asset plus additional assets")

    text_source = find_text_source(title, marker["ready_at"], text_root)
    if text_source["status"] == "invalid":
        errors.extend(text_source["errors"])

    campaign_id = f"{slugify(title)}--{run_id or 'unknown-run'}"
    compact_tiers = {
        tier: {key: value for key, value in report.items() if key not in {"errors", "manifest_inventory"}}
        for tier, report in tier_reports.items()
    }
    premium_media = tier_reports.get("Premium", {}).get("manifest_inventory", [])
    lock_payload = {
        "campaign_id": campaign_id,
        "ready": marker,
        "zip_sha256": {tier: report.get("sha256") for tier, report in compact_tiers.items()},
        "premium_media": premium_media,
        "text_project_sha256": text_source.get("project_sha256"),
        "text_sections": {item["relative_path"]: item["sha256"] for item in text_source.get("source_files", [])},
    }
    return {
        "title": title,
        "campaign_id": campaign_id,
        "run_id": run_id,
        "source_folder": str(folder.resolve()),
        "ready": marker,
        "tiers": compact_tiers,
        "premium_media": premium_media,
        "text_source": text_source,
        "source_fingerprint": fingerprint(lock_payload),
        "valid": not errors,
        "errors": errors,
    }


def discover(config: dict[str, Any], new_adventures: Path | None, text_root: Path | None, verify_crc: bool) -> dict[str, Any]:
    desktop = resolve_windows_desktop()
    adventures_root = new_adventures or desktop / config["source"]["new_adventures_folder"]
    texts_root = text_root or desktop / Path(config["source"]["text_packet_relative"])
    context: dict[str, Any] = {
        "schema_version": 1,
        "checked_at": utc_now(),
        "status": None,
        "new_adventures": str(adventures_root.resolve()) if adventures_root.exists() else str(adventures_root),
        "text_root": str(texts_root.resolve()) if texts_root.exists() else str(texts_root),
        "selection_log": [],
        "selected": None,
    }
    if not adventures_root.exists():
        context["status"] = "no_ready"
        context["message"] = "New Adventures directory does not exist"
        return context

    marker_name = config["source"]["ready_marker"]
    candidates = [path for path in adventures_root.iterdir() if path.is_dir() and (path / marker_name).is_file()]
    candidates.sort(key=lambda item: parse_datetime(marker_metadata(item / marker_name)["ready_at"]), reverse=True)
    context["selection_log"] = [
        {
            "folder": str(item.resolve()),
            "title": item.name,
            "ready_at": marker_metadata(item / marker_name)["ready_at"],
        }
        for item in candidates
    ]
    if not candidates:
        context["status"] = "no_ready"
        context["message"] = "No Ready.txt adventure was found"
        return context

    selected = validate_release(candidates[0], config, verify_crc=verify_crc, text_root=texts_root)
    context["selected"] = selected
    context["status"] = "ready" if selected["valid"] else "invalid"
    if not selected["valid"]:
        context["message"] = "The newest Ready.txt candidate is invalid; no older adventure was selected"
    return context


def next_monday(today: date) -> date:
    return today + timedelta(days=(7 - today.weekday()) % 7)


def local_publish_at(day_value: date, local_time: str) -> str:
    parsed_time = time.fromisoformat(local_time)
    return datetime.combine(day_value, parsed_time).isoformat(timespec="minutes")


def base_deliverable(
    identifier: str,
    concept_id: str,
    platform: str,
    channel: str,
    week: int,
    slot: str,
    format_name: str,
    pillar: str,
    publish_at: str,
    audience: str,
    tier: str,
    spoiler_level: str,
) -> dict[str, Any]:
    return {
        "id": identifier,
        "concept_id": concept_id,
        "platform": platform,
        "channel": channel,
        "week": week,
        "slot": slot,
        "format": format_name,
        "content_pillar": pillar,
        "title": "",
        "hook": "",
        "status": "planned",
        "publish_at": publish_at,
        "audience": audience,
        "tier": tier,
        "spoiler_level": spoiler_level,
        "source_refs": [],
        "asset_refs": [],
        "output_files": [],
        "copy": {
            "caption": "",
            "body_file": "",
            "excerpt": "",
            "hashtags": [],
            "tags": [],
            "seo_title": "",
            "meta_description": "",
            "slug": "",
            "internal_links": [],
        },
        "accessibility": {
            "alt_text": "",
            "panel_alt_text": [],
            "transcript_file": "",
            "subtitle_file": "",
            "poster_file": "",
            "burned_in_captions": False,
            "flashing_check": "pending",
            "contrast_check": "pending",
        },
        "cta": {
            "type": "",
            "label": "",
            "target_url": "",
            "route": "",
            "utm_source": "",
            "utm_medium": "",
            "utm_campaign": "",
            "utm_content": "",
        },
        "rights": {"source_media": "pending", "audio": "not_applicable", "fonts": "pending"},
        "publication": {
            "target_account": "",
            "remote_id": "",
            "remote_url": "",
            "published_at": "",
            "error": "",
        },
        "qa": {"checks": [], "result": "pending", "reviewed_at": "", "reviewer": "", "media_probe": {}},
    }


def seed_deliverables(start_date: date, config: dict[str, Any]) -> list[dict[str, Any]]:
    instagram = config["campaign"]["instagram"]
    instagram_specs = [
        ("video", "launch-trailer", "Launch trailer"),
        ("carousel", "character-spotlight", "Character spotlight"),
        ("image", "design-education", "Adventure-design education"),
        ("image", "adventure-meme", "Adventure-specific meme"),
        ("video", "monster-encounter-video", "Monster or encounter spotlight"),
        ("carousel", "meet-the-monster", "Meet the monster"),
        ("image", "product-ad", "Product or adventure ad"),
        ("carousel", "clue-handout-teaser", "Clue, map, prop, or handout teaser"),
        ("video", "designer-developer-video", "Designer or developer insight"),
        ("carousel", "developer-education", "Developer education"),
        ("image", "scene-location", "Scene or location spotlight"),
        ("image", "community-cta", "Community and final CTA"),
    ]
    day_offsets = (0, 2, 4)
    deliverables: list[dict[str, Any]] = []
    for index, (format_name, concept, pillar) in enumerate(instagram_specs, start=1):
        week = ((index - 1) // 3) + 1
        slot_index = (index - 1) % 3
        publish_day = start_date + timedelta(days=(week - 1) * 7 + day_offsets[slot_index])
        deliverables.append(
            base_deliverable(
                f"IG-{index:02d}",
                concept,
                "instagram",
                "feed" if format_name != "video" else "reels",
                week,
                instagram["days"][slot_index],
                format_name,
                pillar,
                local_publish_at(publish_day, instagram["local_time"]),
                "public",
                "public",
                "spoiler-light",
            )
        )

    patreon = config["campaign"]["patreon"]
    patreon_pillars = (
        ("design-promise", "Design promise, creative constraints, and structure"),
        ("mechanics-and-table-use", "Mechanics, pacing, clues, encounters, and table usability"),
        ("development-retrospective", "Development decisions, iteration lessons, and reusable takeaways"),
    )
    for index, (concept, pillar) in enumerate(patreon_pillars, start=1):
        publish_day = start_date + timedelta(days=(index - 1) * 7 + 1)
        deliverables.append(
            base_deliverable(
                f"PAT-{index:02d}",
                concept,
                "patreon",
                "editorial",
                index,
                patreon["day"],
                "article",
                pillar,
                local_publish_at(publish_day, patreon["local_time"]),
                "members",
                "configure-before-publish",
                "member-spoilers",
            )
        )

    blog = config["campaign"]["blog"]
    deliverables.append(
        base_deliverable(
            "BLOG-01",
            "public-design-story",
            "dicestory-website",
            "blog",
            1,
            blog["day"],
            "article",
            "Public adventure design story and exciting table possibilities",
            local_publish_at(start_date + timedelta(days=3), blog["local_time"]),
            "public",
            "public",
            "spoiler-light",
        )
    )
    return deliverables


def campaign_directories(root: Path) -> list[Path]:
    names = (
        "source/media",
        "source/text",
        "instagram/images",
        "instagram/videos",
        "instagram/captions",
        "instagram/covers",
        "instagram/transcripts",
        "instagram/subtitles",
        "patreon",
        "blog",
        "publishing",
        "working/briefs",
        "working/prompts",
        "working/candidates",
        "working/qa",
        "working/contact-sheets",
    )
    return [root / name for name in names]


def stage_sources(campaign_root: Path, selected: dict[str, Any]) -> list[dict[str, Any]]:
    staged_inventory: list[dict[str, Any]] = []
    premium_path = Path(selected["tiers"]["Premium"]["path"])
    with zipfile.ZipFile(premium_path, "r") as archive:
        members = {item.filename.replace("\\", "/"): item for item in archive.infolist()}
        for item in selected["premium_media"]:
            archive_member = item["archive_member"].replace("\\", "/")
            relative = item["relative_path"].replace("\\", "/")
            if not safe_member(relative) or archive_member not in members:
                raise ValueError(f"Cannot stage unsafe or missing Premium member: {archive_member}")
            target = campaign_root / "source" / "media" / Path(*PurePosixPath(relative).parts)
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(archive.read(archive_member))
            staged = dict(item)
            staged.update(
                {
                    "staged_path": str(target.relative_to(campaign_root)).replace("\\", "/"),
                    "staged_sha256": sha256_file(target),
                    "size_bytes": target.stat().st_size,
                }
            )
            staged_inventory.append(staged)

    text_source = selected.get("text_source", {})
    if text_source.get("status") == "matched":
        project_path = Path(text_source["project_path"])
        project_target = campaign_root / "source" / "text" / "project.json"
        shutil.copy2(project_path, project_target)
        if sha256_file(project_target) != text_source["project_sha256"]:
            raise ValueError("Staged Text Studio project hash mismatch")
        for source in text_source.get("source_files", []):
            source_path = Path(source["path"])
            target = campaign_root / "source" / "text" / source["relative_path"]
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source_path, target)
            if sha256_file(target) != source["sha256"]:
                raise ValueError(f"Staged text hash mismatch: {source['relative_path']}")
    return staged_inventory


def init_campaign(
    context: dict[str, Any], output_root: Path, start_date: date, config: dict[str, Any]
) -> dict[str, Any]:
    if context.get("status") != "ready" or not context.get("selected", {}).get("valid"):
        raise ValueError("Discovery context is not a valid ready adventure")
    selected = context["selected"]
    campaign_root = output_root / selected["campaign_id"]
    manifest_path = campaign_root / "campaign-manifest.json"
    if manifest_path.exists():
        manifest = read_json(manifest_path, {})
        if manifest.get("source", {}).get("fingerprint") != selected["source_fingerprint"]:
            raise ValueError("Existing campaign source fingerprint differs from the selected adventure")
        return {
            "status": "resumed",
            "campaign_id": selected["campaign_id"],
            "campaign_root": str(campaign_root.resolve()),
            "manifest": str(manifest_path.resolve()),
        }

    for directory in campaign_directories(campaign_root):
        directory.mkdir(parents=True, exist_ok=True)
    staged_inventory = stage_sources(campaign_root, selected)
    atomic_write_json(campaign_root / "source" / "media-inventory.json", staged_inventory)
    atomic_write_json(campaign_root / "source" / "context.json", context)

    now = utc_now()
    manifest = {
        "schema_version": "1.0.0",
        "campaign": {
            "id": selected["campaign_id"],
            "adventure_id": selected["run_id"],
            "adventure_title": selected["title"],
            "slug": slugify(selected["title"]),
            "adventure_completed_at": selected["ready"]["ready_at"],
            "selected_by": selected["ready"]["selected_by"],
            "created_at": now,
            "updated_at": now,
            "campaign_start": start_date.isoformat(),
            "timezone": config["timezone"],
            "status": "active",
            "spoiler_policy": "Public content is spoiler-light; Patreon may use labeled member spoilers.",
        },
        "source": {
            "root_path": selected["source_folder"],
            "context_file": "source/context.json",
            "media_inventory": "source/media-inventory.json",
            "fingerprint": selected["source_fingerprint"],
            "zip_sha256": {tier: selected["tiers"][tier]["sha256"] for tier in TIERS},
            "text_source_status": selected["text_source"]["status"],
            "text_project": selected["text_source"].get("project_path"),
        },
        "brand_profile": config["brand"],
        "deliverables": seed_deliverables(start_date, config),
        "approval": {"status": "pending", "approved_at": "", "approved_by": "", "notes": ""},
        "qa_summary": {
            "inventory_result": "pending",
            "media_result": "pending",
            "copy_result": "pending",
            "accessibility_result": "pending",
            "rights_result": "pending",
            "link_result": "pending",
            "visual_result": "pending",
            "approval_result": "pending",
        },
        "publication": {"status": "not_requested", "last_verified_at": ""},
    }
    state = {
        "schema_version": 1,
        "campaign_id": selected["campaign_id"],
        "source_fingerprint": selected["source_fingerprint"],
        "phase": "source_locked",
        "status": "active",
        "created_at": now,
        "updated_at": now,
        "history": [{"phase": "source_locked", "at": now, "note": "Validated and staged immutable sources"}],
        "last_error": None,
    }
    atomic_write_json(manifest_path, manifest)
    atomic_write_json(campaign_root / "run-state.json", state)

    output_root.mkdir(parents=True, exist_ok=True)
    ledger_path = output_root / "campaign-ledger.json"
    ledger = read_json(ledger_path, {"schema_version": 1, "campaigns": {}})
    ledger.setdefault("campaigns", {})[selected["campaign_id"]] = {
        "campaign_id": selected["campaign_id"],
        "title": selected["title"],
        "run_id": selected["run_id"],
        "ready_at": selected["ready"]["ready_at"],
        "source_fingerprint": selected["source_fingerprint"],
        "campaign_root": str(campaign_root.resolve()),
        "status": "active",
        "updated_at": now,
    }
    atomic_write_json(ledger_path, ledger)
    return {
        "status": "initialized",
        "campaign_id": selected["campaign_id"],
        "campaign_root": str(campaign_root.resolve()),
        "manifest": str(manifest_path.resolve()),
        "staged_media": len(staged_inventory),
        "text_source_status": selected["text_source"]["status"],
    }


def deep_merge(target: dict[str, Any], patch: dict[str, Any]) -> dict[str, Any]:
    for key, value in patch.items():
        if isinstance(value, dict) and isinstance(target.get(key), dict):
            deep_merge(target[key], value)
        else:
            target[key] = value
    return target


def update_deliverable(campaign_root: Path, identifier: str, data_path: Path) -> dict[str, Any]:
    manifest_path = campaign_root / "campaign-manifest.json"
    manifest = read_json(manifest_path, {})
    patch = read_json(data_path, {})
    if not isinstance(patch, dict):
        raise ValueError("Deliverable patch must be a JSON object")
    if "id" in patch and patch["id"] != identifier:
        raise ValueError("Deliverable patch cannot change its ID")
    deliverable = next((item for item in manifest.get("deliverables", []) if item.get("id") == identifier), None)
    if deliverable is None:
        raise ValueError(f"Unknown deliverable ID: {identifier}")
    deep_merge(deliverable, patch)
    if deliverable.get("status") not in DELIVERABLE_STATES:
        raise ValueError(f"Invalid deliverable state: {deliverable.get('status')}")
    manifest["campaign"]["updated_at"] = utc_now()
    atomic_write_json(manifest_path, manifest)
    return deliverable


def advance_phase(campaign_root: Path, target: str, note: str) -> dict[str, Any]:
    state_path = campaign_root / "run-state.json"
    state = read_json(state_path, {})
    if state.get("source_fingerprint") != read_json(campaign_root / "campaign-manifest.json", {}).get("source", {}).get(
        "fingerprint"
    ):
        raise ValueError("Run-state and manifest source fingerprints differ")
    current = state.get("phase")
    if current not in CAMPAIGN_PHASES or target not in CAMPAIGN_PHASES:
        raise ValueError("Unknown campaign phase")
    current_index = CAMPAIGN_PHASES.index(current)
    target_index = CAMPAIGN_PHASES.index(target)
    if target_index == current_index:
        return state
    if target_index != current_index + 1:
        raise ValueError(f"Cannot advance from {current} to {target}; expected {CAMPAIGN_PHASES[current_index + 1]}")
    now = utc_now()
    state["phase"] = target
    state["status"] = "complete" if target == "complete" else "active"
    state["updated_at"] = now
    state.setdefault("history", []).append({"phase": target, "at": now, "note": note})
    state["last_error"] = None
    atomic_write_json(state_path, state)
    return state


def summarize(manifest: dict[str, Any]) -> dict[str, Any]:
    deliverables = manifest.get("deliverables", [])
    return {
        "campaign_id": manifest.get("campaign", {}).get("id"),
        "adventure_title": manifest.get("campaign", {}).get("adventure_title"),
        "total": len(deliverables),
        "by_platform": dict(sorted(Counter(item.get("platform", "unknown") for item in deliverables).items())),
        "by_format": dict(sorted(Counter(item.get("format", "unknown") for item in deliverables).items())),
        "by_status": dict(sorted(Counter(item.get("status", "unknown") for item in deliverables).items())),
        "next_item": min(
            (item for item in deliverables if item.get("status") not in {"published", "scheduled"}),
            key=lambda item: item.get("publish_at", "9999"),
            default=None,
        ),
    }


def approval_snapshot_hash(manifest: dict[str, Any]) -> str:
    locked_deliverables = []
    for source in manifest.get("deliverables", []):
        item = {key: value for key, value in source.items() if key not in {"status", "publication"}}
        locked_deliverables.append(item)
    payload = {
        "schema_version": manifest.get("schema_version"),
        "campaign_id": manifest.get("campaign", {}).get("id"),
        "campaign_start": manifest.get("campaign", {}).get("campaign_start"),
        "timezone": manifest.get("campaign", {}).get("timezone"),
        "source_fingerprint": manifest.get("source", {}).get("fingerprint"),
        "brand_profile": manifest.get("brand_profile"),
        "deliverables": locked_deliverables,
    }
    return fingerprint(payload)


def approve_campaign(campaign_root: Path, approved_by: str, notes: str) -> dict[str, Any]:
    report = validate_campaign(campaign_root, "ready")
    if not report["valid"]:
        raise ValueError(f"Campaign cannot be approved; ready validation has {report['error_count']} error(s)")
    manifest_path = campaign_root / "campaign-manifest.json"
    manifest = read_json(manifest_path, {})
    now = utc_now()
    for item in manifest.get("deliverables", []):
        if item.get("status") == "qa_passed":
            item["status"] = "approved"
        elif item.get("status") not in {"approved", "scheduled", "published"}:
            raise ValueError(f"{item.get('id')}: status must be qa_passed before approval")
    snapshot_hash = approval_snapshot_hash(manifest)
    manifest["approval"] = {
        "status": "approved",
        "approved_at": now,
        "approved_by": approved_by.strip(),
        "notes": notes,
        "snapshot_hash": snapshot_hash,
    }
    manifest["campaign"]["updated_at"] = now
    manifest["qa_summary"]["approval_result"] = "passed"
    atomic_write_json(manifest_path, manifest)
    return manifest["approval"]


def resolve_campaign_file(campaign_root: Path, value: str) -> Path:
    if not value:
        raise ValueError("Blank campaign-relative path")
    candidate = (campaign_root / value).resolve()
    try:
        candidate.relative_to(campaign_root.resolve())
    except ValueError as exc:
        raise ValueError(f"Path escapes campaign root: {value}") from exc
    return candidate


def word_count(path: Path) -> int:
    return len(WORD_RE.findall(path.read_text(encoding="utf-8", errors="replace")))


def image_dimensions(path: Path) -> tuple[int, int] | None:
    try:
        from PIL import Image

        with Image.open(path) as image:
            return image.size
    except (ImportError, OSError):
        return None


def ffprobe_video(path: Path) -> dict[str, Any] | None:
    executable = shutil.which("ffprobe")
    if not executable:
        return None
    command = [
        executable,
        "-v",
        "error",
        "-select_streams",
        "v:0",
        "-show_entries",
        "stream=codec_name,width,height,avg_frame_rate:format=duration",
        "-of",
        "json",
        str(path),
    ]
    result = subprocess.run(command, capture_output=True, text=True, check=False)
    if result.returncode != 0:
        return {"error": result.stderr.strip() or "ffprobe failed"}
    payload = json.loads(result.stdout)
    stream = (payload.get("streams") or [{}])[0]
    numerator, _, denominator = str(stream.get("avg_frame_rate", "0/1")).partition("/")
    fps = float(numerator) / float(denominator or 1) if float(denominator or 1) else 0
    return {
        "codec": stream.get("codec_name"),
        "width": stream.get("width"),
        "height": stream.get("height"),
        "fps": round(fps, 3),
        "duration_seconds": float(payload.get("format", {}).get("duration", 0)),
    }


def require_text(errors: list[str], identifier: str, label: str, value: Any, minimum: int = 1) -> None:
    if len(str(value or "").strip()) < minimum:
        errors.append(f"{identifier}: missing or too-short {label}")


def validate_plan(manifest: dict[str, Any], campaign_root: Path) -> list[str]:
    errors: list[str] = []
    deliverables = manifest.get("deliverables", [])
    ids = [item.get("id") for item in deliverables]
    expected_ids = [*(f"IG-{index:02d}" for index in range(1, 13)), *(f"PAT-{index:02d}" for index in range(1, 4)), "BLOG-01"]
    if sorted(ids) != sorted(expected_ids):
        errors.append("Deliverable IDs must be exactly IG-01..IG-12, PAT-01..PAT-03, and BLOG-01")
    if len(ids) != len(set(ids)):
        errors.append("Deliverable IDs are not unique")
    concepts = [item.get("concept_id") for item in deliverables]
    if len(concepts) != len(set(concepts)):
        errors.append("concept_id values are not unique")

    instagram = [item for item in deliverables if item.get("platform") == "instagram"]
    patreon = [item for item in deliverables if item.get("platform") == "patreon"]
    blogs = [item for item in deliverables if item.get("platform") == "dicestory-website"]
    videos = [item for item in instagram if item.get("format") == "video"]
    static = [item for item in instagram if item.get("format") in {"image", "carousel"}]
    if len(instagram) != 12 or len(videos) != 3 or len(static) != 9:
        errors.append("Inventory must contain 12 Instagram posts: exactly 3 video and 9 image/carousel")
    if len(patreon) != 3:
        errors.append("Inventory must contain exactly 3 Patreon posts")
    if len(blogs) != 1:
        errors.append("Inventory must contain exactly 1 DiceStory blog post")

    for item in deliverables:
        identifier = item.get("id", "unknown")
        if item.get("status") not in DELIVERABLE_STATES:
            errors.append(f"{identifier}: invalid status {item.get('status')!r}")
        if not item.get("publish_at"):
            errors.append(f"{identifier}: missing publish_at")
        if not item.get("week") or not item.get("slot"):
            errors.append(f"{identifier}: missing schedule week/slot")
        for value in item.get("output_files", []):
            try:
                resolve_campaign_file(campaign_root, value)
            except ValueError as exc:
                errors.append(f"{identifier}: {exc}")

    context_path = campaign_root / "source" / "context.json"
    if not context_path.is_file():
        errors.append("Missing source/context.json")
    else:
        context = read_json(context_path, {})
        expected_fingerprint = context.get("selected", {}).get("source_fingerprint")
        if expected_fingerprint != manifest.get("source", {}).get("fingerprint"):
            errors.append("Manifest source fingerprint does not match staged context")
    if not (campaign_root / "source" / "media-inventory.json").is_file():
        errors.append("Missing source/media-inventory.json")
    return errors


def validate_common_ready(item: dict[str, Any], campaign_root: Path, errors: list[str]) -> list[Path]:
    identifier = item["id"]
    require_text(errors, identifier, "title", item.get("title"), 4)
    require_text(errors, identifier, "hook", item.get("hook"), 8)
    if not item.get("source_refs"):
        errors.append(f"{identifier}: source_refs must not be empty")
    cta = item.get("cta", {})
    for field in (
        "type",
        "label",
        "target_url",
        "utm_source",
        "utm_medium",
        "utm_campaign",
        "utm_content",
    ):
        require_text(errors, identifier, f"cta.{field}", cta.get(field))
    files: list[Path] = []
    if not item.get("output_files"):
        errors.append(f"{identifier}: output_files must not be empty")
    for value in item.get("output_files", []):
        try:
            path = resolve_campaign_file(campaign_root, value)
        except ValueError as exc:
            errors.append(f"{identifier}: {exc}")
            continue
        if not path.is_file():
            errors.append(f"{identifier}: output file does not exist: {value}")
        else:
            files.append(path)
    if item.get("qa", {}).get("result") != "passed":
        errors.append(f"{identifier}: qa.result must be passed")
    return files


def validate_ready(manifest: dict[str, Any], campaign_root: Path) -> list[str]:
    errors = validate_plan(manifest, campaign_root)
    for item in manifest.get("deliverables", []):
        identifier = item["id"]
        output_paths = validate_common_ready(item, campaign_root, errors)
        accessibility = item.get("accessibility", {})
        copy = item.get("copy", {})
        rights = item.get("rights", {})
        if rights.get("source_media") != "cleared" or rights.get("fonts") != "cleared":
            errors.append(f"{identifier}: source-media and font rights must be cleared")

        if item["platform"] == "instagram":
            require_text(errors, identifier, "copy.caption", copy.get("caption"), 20)
            hashtags = copy.get("hashtags", [])
            if not isinstance(hashtags, list) or not 3 <= len(hashtags) <= 8:
                errors.append(f"{identifier}: hashtags must contain 3–8 entries")
            if item["format"] == "video":
                video_files = [path for path in output_paths if path.suffix.lower() == ".mp4"]
                if len(video_files) != 1:
                    errors.append(f"{identifier}: exactly one MP4 must be present in output_files")
                for field in ("transcript_file", "subtitle_file", "poster_file"):
                    value = accessibility.get(field)
                    try:
                        path = resolve_campaign_file(campaign_root, value)
                    except ValueError as exc:
                        errors.append(f"{identifier}: {field}: {exc}")
                        continue
                    if not path.is_file():
                        errors.append(f"{identifier}: missing {field}: {value}")
                if accessibility.get("burned_in_captions") is not True:
                    errors.append(f"{identifier}: burned_in_captions must be true")
                if rights.get("audio") not in {"cleared", "silent"}:
                    errors.append(f"{identifier}: audio rights must be cleared or silent")
                if video_files:
                    actual_probe = ffprobe_video(video_files[0])
                    probe = actual_probe or item.get("qa", {}).get("media_probe", {})
                    if not probe or probe.get("error"):
                        errors.append(f"{identifier}: no valid video media probe is available")
                    else:
                        if probe.get("width") != 1080 or probe.get("height") != 1920:
                            errors.append(f"{identifier}: video must be 1080x1920")
                        if str(probe.get("codec", "")).lower() not in {"h264", "avc1"}:
                            errors.append(f"{identifier}: video codec must be H.264")
                        duration = float(probe.get("duration_seconds", 0))
                        if not 15 <= duration <= 45:
                            errors.append(f"{identifier}: video duration must be 15–45 seconds")
                        fps = float(probe.get("fps", 0))
                        if not (23.9 <= fps <= 24.1 or 29.9 <= fps <= 30.1):
                            errors.append(f"{identifier}: video frame rate must be 24 or 30 fps")
            else:
                images = [path for path in output_paths if path.suffix.lower() in IMAGE_EXTENSIONS]
                if not images:
                    errors.append(f"{identifier}: image/carousel has no image output")
                for image in images:
                    dimensions = image_dimensions(image)
                    if dimensions != (1080, 1350):
                        errors.append(f"{identifier}: {image.name} must be 1080x1350, found {dimensions}")
                if item["format"] == "carousel":
                    panel_alt = accessibility.get("panel_alt_text", [])
                    if len(panel_alt) != len(images):
                        errors.append(f"{identifier}: carousel requires one alt-text entry per panel")
                else:
                    require_text(errors, identifier, "accessibility.alt_text", accessibility.get("alt_text"), 12)

        elif item["platform"] == "patreon":
            body_value = copy.get("body_file")
            try:
                body_path = resolve_campaign_file(campaign_root, body_value)
            except ValueError as exc:
                errors.append(f"{identifier}: body_file: {exc}")
            else:
                if not body_path.is_file():
                    errors.append(f"{identifier}: body_file does not exist")
                else:
                    count = word_count(body_path)
                    if not 700 <= count <= 1200:
                        errors.append(f"{identifier}: Patreon body must be 700–1,200 words, found {count}")
            require_text(errors, identifier, "copy.excerpt", copy.get("excerpt"), 40)
            require_text(errors, identifier, "accessibility.alt_text", accessibility.get("alt_text"), 12)
            if item.get("tier") in {"", "configure-before-publish"}:
                errors.append(f"{identifier}: Patreon tier must be configured")

        elif item["platform"] == "dicestory-website":
            body_value = copy.get("body_file")
            try:
                body_path = resolve_campaign_file(campaign_root, body_value)
            except ValueError as exc:
                errors.append(f"{identifier}: body_file: {exc}")
            else:
                if not body_path.is_file():
                    errors.append(f"{identifier}: body_file does not exist")
                else:
                    count = word_count(body_path)
                    if not 1000 <= count <= 1600:
                        errors.append(f"{identifier}: blog body must be 1,000–1,600 words, found {count}")
            for field in ("excerpt", "seo_title", "slug"):
                require_text(errors, identifier, f"copy.{field}", copy.get(field), 4)
            meta = str(copy.get("meta_description", ""))
            if not 140 <= len(meta) <= 160:
                errors.append(f"{identifier}: meta_description must be 140–160 characters, found {len(meta)}")
            require_text(errors, identifier, "accessibility.alt_text", accessibility.get("alt_text"), 12)
            json_files = [path for path in output_paths if path.suffix.lower() == ".json"]
            required_keys = {
                "id",
                "title",
                "slug",
                "dek",
                "author",
                "status",
                "category",
                "tags",
                "image",
                "featured",
                "publishedAt",
                "updatedAt",
                "body",
            }
            if not json_files:
                errors.append(f"{identifier}: output_files must include a DiceStory blog JSON object")
            else:
                try:
                    blog_payload = read_json(json_files[0], {})
                    if not required_keys.issubset(blog_payload):
                        errors.append(f"{identifier}: blog JSON object is missing required website fields")
                except json.JSONDecodeError as exc:
                    errors.append(f"{identifier}: blog JSON is invalid: {exc}")

        if accessibility.get("contrast_check") != "passed":
            errors.append(f"{identifier}: contrast_check must be passed")
        if item.get("format") == "video" and accessibility.get("flashing_check") != "passed":
            errors.append(f"{identifier}: flashing_check must be passed")
    return errors


def validate_campaign(campaign_root: Path, phase: str) -> dict[str, Any]:
    manifest = read_json(campaign_root / "campaign-manifest.json", {})
    if not manifest:
        raise ValueError(f"Missing campaign manifest: {campaign_root}")
    errors = validate_plan(manifest, campaign_root) if phase == "plan" else validate_ready(manifest, campaign_root)
    if phase == "publish":
        if manifest.get("approval", {}).get("status") != "approved":
            errors.append("Campaign approval.status must be approved before publishing")
        approved_hash = manifest.get("approval", {}).get("snapshot_hash")
        current_hash = approval_snapshot_hash(manifest)
        if not approved_hash or approved_hash != current_hash:
            errors.append("Campaign content no longer matches the approved snapshot")
        for item in manifest.get("deliverables", []):
            if item.get("status") not in {"approved", "scheduled", "published"}:
                errors.append(f"{item.get('id')}: status must be approved, scheduled, or published before publishing")
    report = {
        "schema_version": 1,
        "checked_at": utc_now(),
        "phase": phase,
        "campaign_id": manifest.get("campaign", {}).get("id"),
        "valid": not errors,
        "error_count": len(errors),
        "errors": errors,
        "summary": summarize(manifest),
    }
    report_path = campaign_root / "working" / "qa" / f"validation-{phase}.json"
    atomic_write_json(report_path, report)
    report["report_path"] = str(report_path.resolve())
    return report


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, help="Optional channel configuration override")
    subparsers = parser.add_subparsers(dest="command", required=True)

    discover_parser = subparsers.add_parser("discover", help="Select and validate the newest Ready.txt adventure")
    discover_parser.add_argument("--new-adventures", type=Path)
    discover_parser.add_argument("--text-root", type=Path)
    discover_parser.add_argument("--skip-crc", action="store_true")
    discover_parser.add_argument("--json-out", type=Path)

    init_parser = subparsers.add_parser("init", help="Initialize or resume a source-locked campaign")
    init_parser.add_argument("--new-adventures", type=Path)
    init_parser.add_argument("--text-root", type=Path)
    init_parser.add_argument("--skip-crc", action="store_true")
    init_parser.add_argument("--context", type=Path)
    init_parser.add_argument("--output-root", type=Path, default=default_output_root())
    init_parser.add_argument("--start-date", type=date.fromisoformat)

    show_parser = subparsers.add_parser("show", help="Show campaign status and next item")
    show_parser.add_argument("--campaign", type=Path, required=True)

    update_parser = subparsers.add_parser("update", help="Atomically merge a deliverable patch")
    update_parser.add_argument("--campaign", type=Path, required=True)
    update_parser.add_argument("--id", required=True)
    update_parser.add_argument("--data", type=Path, required=True)

    advance_parser = subparsers.add_parser("advance", help="Advance the campaign phase by one checkpoint")
    advance_parser.add_argument("--campaign", type=Path, required=True)
    advance_parser.add_argument("--phase", choices=CAMPAIGN_PHASES, required=True)
    advance_parser.add_argument("--note", default="")

    approve_parser = subparsers.add_parser("approve", help="Lock a human-approved, ready-valid campaign snapshot")
    approve_parser.add_argument("--campaign", type=Path, required=True)
    approve_parser.add_argument("--approved-by", required=True)
    approve_parser.add_argument("--notes", default="")

    validate_parser = subparsers.add_parser("validate", help="Validate plan, ready, or publish gates")
    validate_parser.add_argument("--campaign", type=Path, required=True)
    validate_parser.add_argument("--phase", choices=("plan", "ready", "publish"), default="plan")
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    config = load_config(args.config)
    if args.command == "discover":
        output = discover(config, args.new_adventures, args.text_root, verify_crc=not args.skip_crc)
        if args.json_out:
            atomic_write_json(args.json_out, output)
        code = 2 if output.get("status") == "invalid" else 0
    elif args.command == "init":
        context = read_json(args.context, {}) if args.context else discover(
            config, args.new_adventures, args.text_root, verify_crc=not args.skip_crc
        )
        start_date = args.start_date or next_monday(datetime.now().date())
        output = init_campaign(context, args.output_root, start_date, config)
        code = 0
    elif args.command == "show":
        manifest = read_json(args.campaign / "campaign-manifest.json", {})
        state = read_json(args.campaign / "run-state.json", {})
        output = {"campaign_root": str(args.campaign.resolve()), "state": state, "summary": summarize(manifest)}
        code = 0
    elif args.command == "update":
        output = update_deliverable(args.campaign, args.id, args.data)
        code = 0
    elif args.command == "advance":
        output = advance_phase(args.campaign, args.phase, args.note)
        code = 0
    elif args.command == "approve":
        output = approve_campaign(args.campaign, args.approved_by, args.notes)
        code = 0
    elif args.command == "validate":
        output = validate_campaign(args.campaign, args.phase)
        code = 0 if output["valid"] else 2
    else:
        raise AssertionError(args.command)
    print(json.dumps(output, indent=2, ensure_ascii=False))
    return code


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (KeyError, OSError, ValueError, json.JSONDecodeError, zipfile.BadZipFile) as exc:
        print(json.dumps({"status": "error", "error": str(exc)}, indent=2), file=sys.stderr)
        raise SystemExit(3)
