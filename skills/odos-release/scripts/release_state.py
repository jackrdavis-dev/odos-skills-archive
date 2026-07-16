#!/usr/bin/env python3
"""Maintain an atomic, resumable ODOS Release ledger."""

from __future__ import annotations

import argparse
import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


PHASES = (
    "validated",
    "content_staged",
    "shop_created",
    "shop_edited",
    "shop_files_assigned",
    "shop_verified",
    "patreon_premium",
    "patreon_deluxe",
    "patreon_basic",
    "patreon_announcement",
    "homepage_deferred",
    "verified",
    "complete",
)


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def read_json(path: Path, default: Any) -> Any:
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding="utf-8"))


def atomic_write(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_suffix(path.suffix + ".tmp")
    temp.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    os.replace(temp, path)


def default_ledger() -> Path:
    root = Path(os.path.expandvars(r"%LOCALAPPDATA%\ODOSRelease"))
    return root / "release-ledger.json"


def parse_data(values: list[str]) -> dict[str, str]:
    result = {}
    for value in values:
        if "=" not in value:
            raise ValueError(f"Data must use key=value syntax: {value}")
        key, item = value.split("=", 1)
        if not key.strip():
            raise ValueError("Data key cannot be blank")
        result[key.strip()] = item.strip()
    return result


def selected_from_context(context: dict[str, Any]) -> dict[str, Any]:
    selected = context.get("selected")
    if context.get("status") != "ready" or not isinstance(selected, dict) or not selected.get("valid"):
        raise ValueError("Context is not a successful ready preflight")
    return selected


def hashes_from_selected(selected: dict[str, Any]) -> dict[str, str]:
    return {tier: selected["tiers"][tier]["sha256"] for tier in ("Basic", "Deluxe", "Premium")}


def command_start(ledger: dict[str, Any], context_path: Path) -> dict[str, Any]:
    context = read_json(context_path, {})
    selected = selected_from_context(context)
    release_id = selected["release_id"]
    releases = ledger.setdefault("releases", {})
    hashes = hashes_from_selected(selected)
    existing = releases.get(release_id)
    if existing:
        if existing.get("zip_sha256") != hashes:
            raise ValueError("Source ZIP hashes changed after this release entered the ledger")
        return existing

    now = utc_now()
    record = {
        "release_id": release_id,
        "title": selected["title"],
        "run_id": selected["run_id"],
        "source_folder": selected["source_folder"],
        "ready_at": selected["ready"]["ready_at"],
        "zip_sha256": hashes,
        "status": "active",
        "phase": "validated",
        "started_at": now,
        "updated_at": now,
        "completed_at": None,
        "phase_history": [{"phase": "validated", "at": now}],
        "artifacts": {},
        "failures": [],
    }
    releases[release_id] = record
    return record


def get_record(ledger: dict[str, Any], release_id: str) -> dict[str, Any]:
    record = ledger.get("releases", {}).get(release_id)
    if not record:
        raise ValueError(f"Unknown release ID: {release_id}")
    return record


def command_advance(record: dict[str, Any], target: str, data: dict[str, str]) -> None:
    if target not in PHASES:
        raise ValueError(f"Unknown phase: {target}")
    current = record["phase"]
    current_index = PHASES.index(current)
    target_index = PHASES.index(target)
    if target_index == current_index:
        record.setdefault("artifacts", {}).update(data)
        record["updated_at"] = utc_now()
        return
    if target_index != current_index + 1:
        raise ValueError(f"Cannot advance from {current} to {target}; expected {PHASES[current_index + 1]}")
    now = utc_now()
    record["phase"] = target
    record["status"] = "complete" if target == "complete" else "active"
    record["updated_at"] = now
    record.setdefault("phase_history", []).append({"phase": target, "at": now})
    record.setdefault("artifacts", {}).update(data)
    record["last_error"] = None
    if target == "complete":
        record["completed_at"] = now


def command_fail(record: dict[str, Any], message: str) -> None:
    now = utc_now()
    failure = {"phase": record["phase"], "at": now, "message": message}
    record.setdefault("failures", []).append(failure)
    record["last_error"] = failure
    record["status"] = "failed"
    record["updated_at"] = now


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--ledger", type=Path, default=default_ledger())
    subparsers = parser.add_subparsers(dest="command", required=True)

    start = subparsers.add_parser("start")
    start.add_argument("--context", type=Path, required=True)

    show = subparsers.add_parser("show")
    show.add_argument("--release-id")

    advance = subparsers.add_parser("advance")
    advance.add_argument("--release-id", required=True)
    advance.add_argument("--phase", choices=PHASES, required=True)
    advance.add_argument("--data", action="append", default=[])

    fail = subparsers.add_parser("fail")
    fail.add_argument("--release-id", required=True)
    fail.add_argument("--message", required=True)

    args = parser.parse_args()
    ledger = read_json(args.ledger, {"schema_version": 1, "releases": {}})

    if args.command == "start":
        output = command_start(ledger, args.context)
        atomic_write(args.ledger, ledger)
    elif args.command == "show":
        output = get_record(ledger, args.release_id) if args.release_id else ledger
    elif args.command == "advance":
        output = get_record(ledger, args.release_id)
        command_advance(output, args.phase, parse_data(args.data))
        atomic_write(args.ledger, ledger)
    elif args.command == "fail":
        output = get_record(ledger, args.release_id)
        command_fail(output, args.message)
        atomic_write(args.ledger, ledger)
    else:
        raise AssertionError(args.command)

    print(json.dumps(output, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (KeyError, OSError, ValueError, json.JSONDecodeError) as exc:
        print(json.dumps({"status": "error", "error": str(exc)}, indent=2))
        raise SystemExit(2)
