#!/usr/bin/env python3
"""Validate the immutable ODOSv5.1 page, style, logo, and map-reference setup."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
REQUIRED_PAGE_SAMPLES = {
    "Rumble TM Cover.png",
    "ig_0037031b75f5be41016a4b799ff8388194b04ded71a7e313f8.png",
    "ig_08e5f85f801b3b79016a4b8342672481968fd37f4b8bd2fee6.png",
}
REQUIRED_STYLE_SAMPLES = {
    "generated-hero-pantheria-cartoon-v6.png",
    "Saedaxi Midnight Escape.png",
    "Tavern People.png",
}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def require_files(folder: Path, names: set[str]) -> list[dict]:
    missing = sorted(name for name in names if not (folder / name).is_file())
    if missing:
        raise SystemExit(f"Missing required reference assets in {folder}: {', '.join(missing)}")
    return [
        {"path": str(folder / name), "sha256": sha256(folder / name)}
        for name in sorted(names)
    ]


def main() -> None:
    page_samples = require_files(ROOT / "assets" / "page-samples", REQUIRED_PAGE_SAMPLES)
    style_samples = require_files(ROOT / "assets" / "art-style-samples", REQUIRED_STYLE_SAMPLES)
    logo = ROOT / "assets" / "logos" / "Logo 4.png"
    if not logo.is_file():
        raise SystemExit(f"Missing exact ODOS logo: {logo}")
    routing = ROOT / "references" / "page-reference-routing.json"
    map_schema = ROOT / "references" / "battle-map-qa-schema.json"
    json.loads(routing.read_text(encoding="utf-8-sig"))
    json.loads(map_schema.read_text(encoding="utf-8-sig"))
    print(
        json.dumps(
            {
                "status": "pass",
                "page_samples": page_samples,
                "style_samples": style_samples,
                "logo": {"path": str(logo), "sha256": sha256(logo)},
                "routing": str(routing),
                "battle_map_qa_schema": str(map_schema),
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
