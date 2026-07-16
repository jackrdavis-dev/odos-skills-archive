#!/usr/bin/env python3
"""OCR an ODOS page and compare required titles, names, mechanics, and sections."""

from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
import tempfile
from datetime import datetime, timezone
from pathlib import Path


def normalize(value: str) -> str:
    value = value.upper().replace("—", "-").replace("–", "-")
    value = re.sub(r"[^A-Z0-9+\-/ ]+", " ", value)
    return re.sub(r"\s+", " ", value).strip()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--image", required=True, type=Path)
    parser.add_argument("--expected", required=True, type=Path)
    parser.add_argument("--report", required=True, type=Path)
    parser.add_argument("--tesseract")
    parser.add_argument("--node")
    parser.add_argument("--tesseract-js")
    parser.add_argument("--psm", default="6")
    args = parser.parse_args()

    image = args.image.resolve()
    expected = json.loads(args.expected.read_text(encoding="utf-8-sig"))
    executable = args.tesseract or shutil.which("tesseract")
    if not image.is_file():
        raise SystemExit(f"Image does not exist: {image}")

    with tempfile.TemporaryDirectory(prefix="odosv5-ocr-") as temp_dir:
        output_base = Path(temp_dir) / "page"
        if executable:
            command = [str(executable), str(image), str(output_base), "--psm", str(args.psm), "-l", "eng"]
            result = subprocess.run(command, capture_output=True, text=True)
            if result.returncode:
                raise SystemExit(f"Tesseract failed: {result.stderr.strip()}")
            text = output_base.with_suffix(".txt").read_text(encoding="utf-8", errors="replace")
        else:
            home = Path.home()
            node_candidates = list(home.glob(".cache/codex-runtimes/**/dependencies/node/bin/node.exe"))
            module_candidates = sorted(
                home.glob(".cache/codex-runtimes/**/dependencies/node/node_modules/**/tesseract.js"),
                key=lambda path: (".pnpm" not in str(path), len(str(path))),
            )
            node = Path(args.node) if args.node else (Path(shutil.which("node")) if shutil.which("node") else (node_candidates[0] if node_candidates else None))
            module = Path(args.tesseract_js) if args.tesseract_js else (module_candidates[0] if module_candidates else None)
            if not node or not module:
                raise SystemExit("OCR requires either Tesseract CLI or Node.js with tesseract.js.")
            output_text = output_base.with_suffix(".txt")
            helper = Path(__file__).with_name("qa_ocr_tesseract.mjs")
            result = subprocess.run(
                [str(node), str(helper), str(image), str(output_text), str(module)],
                capture_output=True,
                text=True,
            )
            if result.returncode:
                raise SystemExit(f"tesseract.js failed: {result.stderr.strip()}")
            text = output_text.read_text(encoding="utf-8", errors="replace")

    normalized = normalize(text)
    exact_results = []
    for value in expected.get("exact", []):
        wanted = normalize(value)
        exact_results.append({"expected": value, "found": wanted in normalized})
    regex_results = []
    for pattern in expected.get("regex", []):
        regex_results.append({"pattern": pattern, "found": bool(re.search(pattern, normalized, re.IGNORECASE))})
    required_sections = []
    for value in expected.get("sections", []):
        wanted = normalize(value)
        required_sections.append({"expected": value, "found": wanted in normalized})

    checks = exact_results + regex_results + required_sections
    found = sum(bool(item["found"]) for item in checks)
    ratio = found / len(checks) if checks else 1.0
    threshold = float(expected.get("minimum_ratio", 1.0))
    critical = {normalize(value) for value in expected.get("critical", [])}
    critical_missing = [
        item["expected"]
        for item in exact_results + required_sections
        if normalize(item["expected"]) in critical and not item["found"]
    ]
    passed = ratio >= threshold and not critical_missing
    report = {
        "schema_version": 1,
        "checked_at": datetime.now(timezone.utc).isoformat(),
        "image": str(image),
        "status": "pass" if passed else "fail",
        "ratio": ratio,
        "minimum_ratio": threshold,
        "critical_missing": critical_missing,
        "exact": exact_results,
        "regex": regex_results,
        "sections": required_sections,
        "ocr_text": text,
    }
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"status": report["status"], "ratio": ratio, "report": str(args.report)}, indent=2))
    if not passed:
        raise SystemExit(2)


if __name__ == "__main__":
    main()
