#!/usr/bin/env python3
"""Build a QA-only contact sheet and hash manifest for an ODOS generation batch."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
from datetime import datetime, timezone
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", action="append", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--columns", type=int, default=4)
    parser.add_argument("--cell-width", type=int, default=320)
    parser.add_argument("--cell-height", type=int, default=460)
    args = parser.parse_args()

    paths = [path.resolve() for path in args.input]
    missing = [str(path) for path in paths if not path.is_file()]
    if missing:
        raise SystemExit("Missing contact-sheet inputs: " + ", ".join(missing))
    columns = max(1, args.columns)
    rows = math.ceil(len(paths) / columns)
    label_height = 34
    sheet = Image.new(
        "RGB",
        (columns * args.cell_width, rows * (args.cell_height + label_height)),
        (20, 24, 31),
    )
    draw = ImageDraw.Draw(sheet)
    font = ImageFont.load_default()
    records = []
    for index, path in enumerate(paths):
        column = index % columns
        row = index // columns
        x = column * args.cell_width
        y = row * (args.cell_height + label_height)
        with Image.open(path) as source:
            image = source.convert("RGB")
            image.thumbnail((args.cell_width - 12, args.cell_height - 12), Image.Resampling.LANCZOS)
            offset_x = x + (args.cell_width - image.width) // 2
            offset_y = y + (args.cell_height - image.height) // 2
            sheet.paste(image, (offset_x, offset_y))
        label = path.name
        draw.rectangle(
            (x, y + args.cell_height, x + args.cell_width, y + args.cell_height + label_height),
            fill=(38, 45, 58),
        )
        draw.text((x + 8, y + args.cell_height + 10), label[:48], fill=(245, 239, 214), font=font)
        records.append({"path": str(path), "sha256": sha256(path)})

    args.output.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(args.output, format="PNG")
    manifest_path = args.output.with_suffix(".json")
    manifest_path.write_text(
        json.dumps(
            {
                "schema_version": 1,
                "created_at": datetime.now(timezone.utc).isoformat(),
                "contact_sheet": str(args.output.resolve()),
                "inputs": records,
                "review_status": "pending",
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    print(f"Built {args.output} and {manifest_path}")


if __name__ == "__main__":
    main()
