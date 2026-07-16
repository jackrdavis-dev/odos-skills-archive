#!/usr/bin/env python3
"""Build a labeled PNG contact sheet for ODOS media visual QA."""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont, ImageOps


IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".webp"}


def read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def safe_campaign_path(campaign: Path, value: str) -> Path | None:
    candidate = (campaign / value).resolve()
    try:
        candidate.relative_to(campaign.resolve())
    except ValueError:
        return None
    return candidate


def campaign_images(campaign: Path) -> list[tuple[str, Path]]:
    manifest_path = campaign / "campaign-manifest.json"
    found: list[tuple[str, Path]] = []
    if manifest_path.is_file():
        manifest = read_json(manifest_path)
        for item in manifest.get("deliverables", []):
            identifier = item.get("id", "unknown")
            for value in item.get("output_files", []):
                path = safe_campaign_path(campaign, value)
                if path and path.is_file() and path.suffix.lower() in IMAGE_EXTENSIONS:
                    found.append((identifier, path))
            poster = item.get("accessibility", {}).get("poster_file", "")
            path = safe_campaign_path(campaign, poster) if poster else None
            if path and path.is_file() and path.suffix.lower() in IMAGE_EXTENSIONS:
                found.append((identifier + " poster", path))
    if found:
        return found
    source_root = campaign / "source" / "media"
    return [("source", path) for path in sorted(source_root.rglob("*")) if path.suffix.lower() in IMAGE_EXTENSIONS]


def input_images(root: Path) -> list[tuple[str, Path]]:
    return [("input", path) for path in sorted(root.rglob("*")) if path.suffix.lower() in IMAGE_EXTENSIONS]


def fit_image(path: Path, width: int, height: int) -> Image.Image:
    with Image.open(path) as source:
        converted = source.convert("RGB")
        fitted = ImageOps.contain(converted, (width, height), Image.Resampling.LANCZOS)
    canvas = Image.new("RGB", (width, height), "#f3ecdf")
    x = (width - fitted.width) // 2
    y = (height - fitted.height) // 2
    canvas.paste(fitted, (x, y))
    return canvas


def build_sheet(items: list[tuple[str, Path]], output: Path, columns: int, max_items: int) -> dict:
    items = items[:max_items]
    if not items:
        raise ValueError("No image files were found")
    cell_width = 320
    image_height = 360
    label_height = 76
    padding = 18
    rows = math.ceil(len(items) / columns)
    width = padding + columns * (cell_width + padding)
    height = padding + rows * (image_height + label_height + padding)
    sheet = Image.new("RGB", (width, height), "#21102f")
    draw = ImageDraw.Draw(sheet)
    font = ImageFont.load_default(size=18)
    small_font = ImageFont.load_default(size=14)

    for index, (label, path) in enumerate(items):
        row, column = divmod(index, columns)
        x = padding + column * (cell_width + padding)
        y = padding + row * (image_height + label_height + padding)
        try:
            preview = fit_image(path, cell_width, image_height)
            sheet.paste(preview, (x, y))
        except OSError:
            draw.rectangle((x, y, x + cell_width, y + image_height), fill="#5a2b91")
            draw.text((x + 12, y + 12), "Unreadable image", fill="white", font=font)
        draw.rectangle((x, y + image_height, x + cell_width, y + image_height + label_height), fill="#fffdf7")
        draw.text((x + 10, y + image_height + 8), label[:34], fill="#5a2b91", font=font)
        name = path.name if len(path.name) <= 42 else path.name[:39] + "..."
        draw.text((x + 10, y + image_height + 39), name, fill="#21102f", font=small_font)

    output.parent.mkdir(parents=True, exist_ok=True)
    temp = output.with_suffix(".tmp.png")
    sheet.save(temp, format="PNG", optimize=True)
    temp.replace(output)
    return {"status": "created", "output": str(output.resolve()), "items": len(items), "columns": columns}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument("--campaign", type=Path)
    source.add_argument("--input-dir", type=Path)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--columns", type=int, default=4)
    parser.add_argument("--max-items", type=int, default=80)
    args = parser.parse_args()
    if args.columns < 1 or args.max_items < 1:
        raise ValueError("columns and max-items must be positive")

    if args.campaign:
        items = campaign_images(args.campaign)
        output = args.output or args.campaign / "working" / "contact-sheets" / "campaign-contact-sheet.png"
    else:
        items = input_images(args.input_dir)
        output = args.output or args.input_dir / "contact-sheet.png"
    print(json.dumps(build_sheet(items, output, args.columns, args.max_items), indent=2))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(json.dumps({"status": "error", "error": str(exc)}, indent=2))
        raise SystemExit(2)
