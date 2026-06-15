#!/usr/bin/env python3
"""Validate the Compute Sovereignty Standard v1 document."""

from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
STANDARD_PATH = ROOT / "COMPUTE_SOVEREIGNTY_STANDARD.md"

REQUIRED_LAYERS = [
    "Design Layer",
    "Fabrication Layer",
    "Packaging Layer",
    "Memory Layer",
    "Interconnect Layer",
    "Power / Thermal Layer",
    "Export-Control Layer",
    "Deployment Layer",
]

REQUIRED_POSTURE_LEVELS = [
    "Documented",
    "Partially Documented",
    "Source-Constrained",
    "Not Assessable",
]

REQUIRED_PHRASES = [
    "does not assign sovereignty",
    "## Prohibited Uses",
    "## Evidence Posture Levels",
    "## The Eight Standard Dimensions",
]

RISKY_TERMS = [
    "best chip",
    "most sovereign",
    "ranking",
    "score",
    "winner",
    "investment recommendation",
]

PROHIBITION_MARKERS = re.compile(
    r"(?:"
    r"\bnot\b|\bno\b|\bnon-|\bprohibited\b|\bmust not\b|\bdoes not\b|"
    r"\bcannot\b|\bwithout\b|\bnot a\b|\bnot an\b|\bdo not\b|"
    r"Prohibited Uses|does not assign|not scores|not rankings|"
    r"Misinterpretation risk|Claim boundary|must not support|"
    r"winners or losers|league tables|numeric sovereignty|performance scores|"
    r"superiority marketing|non-conforming|produce a score|compare products|"
    r"public or private rankings|Chip Sovereignty Score|best-chip|best-HBM"
    r")",
    re.IGNORECASE,
)

ALLOWED_SECTIONS = (
    "## What the Standard Does Not Do",
    "## Prohibited Uses",
    "## Responsible Interpretation Rules",
)


def in_allowed_section(lines: list[str], line_no: int) -> bool:
    current = ""
    for idx in range(line_no - 1, -1, -1):
        line = lines[idx].strip()
        if line.startswith("## "):
            current = line
            break
    return any(marker in current for marker in ALLOWED_SECTIONS)


def main() -> None:
    errors: list[str] = []

    if not STANDARD_PATH.is_file():
        print("FAIL: COMPUTE_SOVEREIGNTY_STANDARD.md is missing", file=sys.stderr)
        raise SystemExit(1)

    content = STANDARD_PATH.read_text(encoding="utf-8")
    lines = content.splitlines()

    if "Compute Sovereignty Standard v1.0.0" not in content:
        errors.append("missing title version Compute Sovereignty Standard v1.0.0")

    for layer in REQUIRED_LAYERS:
        if layer not in content:
            errors.append(f"missing layer section: {layer}")

    for level in REQUIRED_POSTURE_LEVELS:
        if level not in content:
            errors.append(f"missing evidence posture level: {level}")

    for phrase in REQUIRED_PHRASES:
        if phrase not in content:
            errors.append(f"missing required phrase/section: {phrase}")

    previous = ""
    for line_no, line in enumerate(lines, 1):
        lowered = line.lower()
        for term in RISKY_TERMS:
            if term.lower() not in lowered:
                continue
            combined = f"{previous} {line}"
            if in_allowed_section(lines, line_no) or PROHIBITION_MARKERS.search(combined):
                continue
            errors.append(
                f"line {line_no}: risky term '{term}' outside allowed context"
            )
        previous = line

    if errors:
        for error in errors:
            print(f"FAIL: {error}", file=sys.stderr)
        raise SystemExit(1)

    print("PASS: Compute Sovereignty Standard v1 is valid (8 layers, 4 posture levels).")


if __name__ == "__main__":
    main()
