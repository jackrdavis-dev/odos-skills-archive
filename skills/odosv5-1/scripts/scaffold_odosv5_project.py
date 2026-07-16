#!/usr/bin/env python3
"""Scaffold a stateful ODOSv5.1 packet workspace."""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path


SKILL_VERSION = "5.1.0"


def write_json(path: Path, data: dict) -> None:
    path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("output_dir", type=Path)
    parser.add_argument("--title", default="")
    parser.add_argument("--slug", default="")
    parser.add_argument("--run-id")
    args = parser.parse_args()

    out = args.output_dir.resolve()
    run_id = args.run_id or datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    created_at = datetime.now(timezone.utc).isoformat()
    folders = [
        out,
        out / "core-pages",
        out / "appendix",
        out / "tokens",
        out / "maps",
        out / "working",
        out / "working" / "candidates" / run_id,
        out / "working" / "prompts" / run_id,
        out / "working" / "qa" / run_id,
        out / "working" / "contact-sheets" / run_id,
        out / "working" / "distribution-staging",
    ]
    for folder in folders:
        folder.mkdir(parents=True, exist_ok=True)

    core_pages = [
        "core-pages/page-00-cover.png",
        "core-pages/page-01-adventure-overview.png",
        "core-pages/page-02-npcs.png",
        "core-pages/page-03-monsters-main-villain.png",
        "core-pages/page-04-scene-flow-overview.png",
        "core-pages/page-05-scene-01.png",
        "core-pages/page-06-scenes-02-03.png",
        "core-pages/page-07-finale-scene.png",
        "core-pages/page-08-clues-secrets-dm-tools.png",
        "core-pages/page-09-rewards-carry-forward.png",
    ]
    manifest = {
        "skill": "odosv5-1",
        "skill_version": SKILL_VERSION,
        "title": args.title,
        "slug": args.slug,
        "run_id": run_id,
        "status": "scaffolded",
        "created_at": created_at,
        "updated_at": created_at,
        "core_pages": core_pages,
    }
    run_state = {
        "schema_version": 1,
        "skill_version": SKILL_VERSION,
        "run_id": run_id,
        "status": "scaffolded",
        "created_at": created_at,
        "updated_at": created_at,
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
        "schema_version": 1,
        "run_id": run_id,
        "status": "provisional",
        "revision": 0,
        "approved_at": None,
        "approved_by": None,
    }
    write_json(out / "manifest.json", manifest)
    write_json(out / "run-state.json", run_state)
    write_json(
        out / "approval-policy.json",
        {
            "schema_version": 1,
            "run_id": run_id,
            "mode": "single_visual_checkpoint",
            "authorized_by": "skill-default",
            "authorized_at": created_at,
            "scope": [
                "art_plates",
                "asset_promotion",
                "cast_approval",
                "locked_packaging",
                "run_approval",
                "scene_storyboard",
            ],
            "stop_conditions": [
                "the four-proof visual checkpoint has not been explicitly approved",
                "a requested style or cast change",
                "source ambiguity that changes story meaning",
                "three failed candidates for the same asset",
                "a hash mismatch or stale dependency",
                "packaging validation failure",
            ],
            "notes": "Require one explicit four-proof visual checkpoint, then continue with autonomous QA.",
        },
    )
    write_json(out / "style-lock.json", {**provisional, "proofs": {}, "references": {}})
    write_json(out / "cast-lock.json", {**provisional, "cast_sheet": None, "crops": {}, "characters": {}})
    write_json(out / "scene-lock.json", {**provisional, "storyboard": None, "scenes": {}})
    write_json(out / "art-plates.json", {"schema_version": 1, "run_id": run_id, "status": "pending", "plates": {}})
    write_json(out / "asset-status.json", {"schema_version": 1, "run_id": run_id, "updated_at": created_at, "assets": {}})
    write_json(
        out / "distribution-map.json",
        {"title": args.title, "slug": args.slug, "version": SKILL_VERSION, "items": [], "tier_rules": {}},
    )
    write_json(
        out / "page-copy-pack.json",
        {
            "schema_version": 1,
            "status": "not_built",
            "adventure": {"title": args.title},
            "core_pages": {},
            "appendix": {},
            "assets": {},
        },
    )
    (out / "qa-report.md").write_text("# ODOSv5 QA Report\n\nRun not started.\n", encoding="utf-8")
    print(f"Scaffolded ODOSv5.1 run {run_id} in {out}")


if __name__ == "__main__":
    main()
