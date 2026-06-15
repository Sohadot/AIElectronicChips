#!/usr/bin/env python3
"""Run all repository validators and the commercial trust-language scan."""

from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"

RISKY_TERMS = [
    "sovereignty score",
    "ranking",
    "benchmark",
    "certification",
    "guarantee",
    "guaranteed",
    "checkout",
    "price",
    "pricing",
    "affiliate",
    "product review",
    "best AI chips",
    "best HBM",
    "investment advice",
    "legal advice",
    "procurement advice",
    "national-security advice",
    "national security advice",
    "sponsored conclusion",
    "predetermined conclusion",
]

BOUNDARY_DATA_FILES = {
    "strategic-offerings.json",
    "chip-dependency-model.json",
}

GOVERNANCE_FILES = {
    "STRATEGIC_AVAILABILITY_TRUST_GATE.md",
    "COMMERCIAL_TRUST_AUDIT.md",
    "STRATEGIC_AVAILABILITY_PROTOCOL.md",
    "PREMIUM_BRIEF_BOUNDARY.md",
    "MONETIZATION_BOUNDARY.md",
    "COMPUTE_SOVEREIGNTY_STANDARD.md",
    "COMPUTE_SOVEREIGNTY_ONTOLOGY.md",
    "CHIP_DEPENDENCY_MAP_MODEL.md",
    "CHIP_DEPENDENCY_MAP_PROTOCOL.md",
    "SOURCE_REGISTRY_PROTOCOL.md",
    "SOURCE_POLICY.md",
    "CLAIM_POLICY.md",
    "CATEGORY_THESIS.md",
    "BUYER_LOGIC.md",
    "MODEL_COHERENCE_AUDIT.md",
    "DECISION_LOG.md",
    "README.md",
    "ASSET_INTELLIGENCE_FACTORY_PLAN.md",
    "CLAIM_BOUNDARY_MATRIX.md",
    "PUBLIC_LAUNCH_READINESS_CHECKLIST.md",
    "INDEXATION_HARDENING_AUDIT.md",
}

PROHIBITED_OUTPUT_TOKEN = re.compile(
    r'^\s*"(?:[a-z_]*(?:score|ranking|benchmark|certification|guarantee|checkout|price|affiliate|advice|conclusion)[a-z_]*)",?\s*$',
    re.IGNORECASE,
)

PROHIBITION_MARKERS = re.compile(
    r"(?:"
    r"\bnot\b|\bno\b|\bnon-|\bcannot\b|\bcan't\b|\bmust not\b|\bdoes not\b|\bdo not\b|"
    r"\bdon't\b|\bdoesn't\b|\bwithout\b|\bprohibited\b|\bprohibits\b|\bprohibition\b|"
    r"\bexcluded\b|\bexclusion\b|\bexclude\b|\bboundary\b|\blimitation\b|\bnever\b|"
    r"\bout of\b|\bunsuitable\b|\bprevented\b|\babsent\b|\bdecline\b|"
    r"\bcannot purchase\b|\bcannot support\b|\bcannot buy\b|\bcannot establish\b|"
    r"\bcannot create\b|\bcannot offer\b|\bnot offer\b|\bnot implement\b|"
    r"\bnot provide\b|\bnot create\b|\bnot assign\b|\bnot support\b|"
    r"\bnot establish\b|\bnot automatically\b|\bnot eligible\b|\bnot turn\b|"
    r"\bnot make\b|\bnot purchase\b|\bnot suitable\b|\bnot a\b|\bnot an\b|"
    r"\brequires\b|\bexpects\b|\bseeks\b|\bThe client\b|\bThe party\b|\bThe request\b|"
    r"Cannot purchase|Cannot support|No public|No predetermined|No sovereignty|"
    r"product-review|predetermin|operating guarantees|use_limitations|"
    r"prohibited_outputs|not_suitable_when|trust_constraints|deliverable_boundary|"
    r"MUST NOT|must not include|Must not include|Excluded Models|Prohibited"
    r")",
    re.IGNORECASE,
)

SCAN_SUFFIXES = {".html", ".md", ".json"}
SKIP_FILES = {"validate_all.py"}


def run_validator(script_name: str) -> tuple[bool, str]:
    script = SCRIPTS / script_name
    result = subprocess.run(
        [sys.executable, str(script)],
        capture_output=True,
        text=True,
        cwd=ROOT,
        check=False,
    )
    output = (result.stdout + result.stderr).strip()
    return result.returncode == 0, output


def is_prohibition_context(line: str, path: Path, previous_line: str = "") -> bool:
    if path.name in GOVERNANCE_FILES or path.name in BOUNDARY_DATA_FILES:
        return True
    combined = f"{previous_line} {line}"
    if PROHIBITION_MARKERS.search(combined):
        return True
    if path.suffix == ".json" and PROHIBITED_OUTPUT_TOKEN.match(line):
        return True
    if path.suffix == ".json" and any(
        marker in line
        for marker in (
            "prohibited",
            "boundary",
            "not_suitable_when",
            "use_limitations",
            "trust_constraints",
            "deliverable_boundary",
        )
    ):
        return True
    return False


def scan_risky_language() -> tuple[list[str], list[tuple[str, int, str, str]]]:
    errors: list[str] = []
    accepted: list[tuple[str, int, str, str]] = []

    for path in sorted(ROOT.rglob("*")):
        if not path.is_file() or path.suffix not in SCAN_SUFFIXES:
            continue
        if path.parts[0] == ".git":
            continue
        if path.name in SKIP_FILES:
            continue

        try:
            lines = path.read_text(encoding="utf-8").splitlines()
        except OSError as exc:
            errors.append(f"could not read {path.relative_to(ROOT)}: {exc}")
            continue

        previous_line = ""
        for line_no, line in enumerate(lines, 1):
            lowered = line.lower()
            for term in RISKY_TERMS:
                if term.lower() not in lowered:
                    continue
                rel = str(path.relative_to(ROOT))
                if is_prohibition_context(line, path, previous_line):
                    accepted.append((rel, line_no, term, line.strip()))
                else:
                    errors.append(
                        f"{rel}:{line_no}: risky term '{term}' outside prohibition context: {line.strip()}"
                    )
            previous_line = line

    return errors, accepted


def main() -> None:
    validator_scripts = [
        "validate_chip_dependency_model.py",
        "validate_source_registry.py",
        "validate_strategic_offerings.py",
        "validate_compute_sovereignty_standard.py",
    ]

    failures: list[str] = []

    for script in validator_scripts:
        ok, output = run_validator(script)
        if ok:
            print(output)
        else:
            failures.append(f"{script} failed")
            if output:
                print(output, file=sys.stderr)

    language_errors, accepted_matches = scan_risky_language()
    if language_errors:
        failures.extend(language_errors)
        for error in language_errors:
            print(f"FAIL: {error}", file=sys.stderr)
    else:
        term_counts: dict[str, int] = {}
        for _, _, term, _ in accepted_matches:
            term_counts[term] = term_counts.get(term, 0) + 1
        if term_counts:
            summary = ", ".join(f"{term} ({count})" for term, count in sorted(term_counts.items()))
            print(f"PASS: Risky commercial terms scanned in prohibition/boundary contexts: {summary}")
        else:
            print("PASS: No risky commercial terms found in scanned files.")

    if failures:
        print(f"FAIL: validate_all.py completed with {len(failures)} issue(s).", file=sys.stderr)
        raise SystemExit(1)

    print("PASS: All validators and commercial trust-language checks passed.")


if __name__ == "__main__":
    main()
