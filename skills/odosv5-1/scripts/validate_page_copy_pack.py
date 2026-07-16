#!/usr/bin/env python3
"""Validate the canonical ODOSv5.1 page-copy-pack shape without external packages."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("page_copy_pack", type=Path)
    args = parser.parse_args()
    data = json.loads(args.page_copy_pack.read_text(encoding="utf-8-sig"))
    required = {"schema_version", "status", "adventure", "core_pages", "appendix", "assets"}
    missing = required - set(data)
    if missing:
        raise SystemExit("Missing keys: " + ", ".join(sorted(missing)))
    if data["schema_version"] != 1:
        raise SystemExit("schema_version must be 1")
    if data["status"] not in {"not_built", "draft", "validated", "stale"}:
        raise SystemExit("Unsupported page-copy status")
    if not isinstance(data["adventure"], dict) or not str(data["adventure"].get("title", "")).strip():
        raise SystemExit("adventure.title is required")
    if not isinstance(data["core_pages"], dict):
        raise SystemExit("core_pages must be an object")
    if data["status"] == "validated" and not data["core_pages"]:
        raise SystemExit("validated page copy must contain core_pages")
    if not isinstance(data["appendix"], dict) or not isinstance(data["assets"], dict):
        raise SystemExit("appendix and assets must be objects")
    print(f"PASS {args.page_copy_pack}")


if __name__ == "__main__":
    main()
