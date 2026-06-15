#!/usr/bin/env python3
"""Validate the Chip Dependency Map foundation model and v1 document."""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
JSON_PATH = ROOT / "data" / "chip-dependency-model.json"
MODEL_PATH = ROOT / "CHIP_DEPENDENCY_MAP_MODEL.md"
README_PATH = ROOT / "README.md"
DECISION_LOG_PATH = ROOT / "DECISION_LOG.md"

EXPECTED_LAYERS = {
    "design",
    "fabrication",
    "packaging",
    "memory",
    "interconnect",
    "power_thermal",
    "controls",
    "deployment",
}
EXPECTED_EXPOSURES = {
    "concentration_exposure",
    "access_exposure",
    "capacity_exposure",
    "technology_exposure",
    "operational_exposure",
    "evidence_exposure",
}
EXPECTED_CONFIDENCE = {"high", "medium", "low", "insufficient"}
EXPECTED_ARTIFACTS = {
    "compute_sovereignty_brief",
    "chip_dependency_audit",
    "infrastructure_readiness_brief",
    "premium_reference_dossier",
}
REQUIRED_JSON_SECTIONS = {
    "model_id",
    "version",
    "status",
    "purpose",
    "prohibited_outputs",
    "layers",
    "exposure_types",
    "confidence_levels",
    "artifact_outputs",
    "artifact_boundaries",
    "answer_options",
    "questions",
}

REQUIRED_ONTOLOGY_LAYERS = [
    "Design",
    "Fabrication",
    "Packaging",
    "Memory",
    "Interconnect",
    "Power / Thermal",
    "Export-Control",
    "Deployment",
]

REQUIRED_DEPENDENCY_STATES = [
    "Direct Dependency",
    "Layered Dependency",
    "Constrained Dependency",
    "Opaque Dependency",
    "Not Assessable",
]

REQUIRED_MODEL_PHRASES = [
    "does not score sovereignty",
    "## Named Entity Governance",
    "## Prohibited Uses",
    "## Dependency Types",
    "Map dependencies before scoring sovereignty",
]

RISKY_TERMS = [
    "best ai chip",
    "most sovereign",
    "ranking",
    "score",
    "winner",
    "investment recommendation",
    "country ranking",
    "company ranking",
    "product comparison",
]

PROHIBITION_MARKERS = re.compile(
    r"(?:"
    r"\bnot\b|\bno\b|\bnon-|\bprohibited\b|\bmust not\b|\bdoes not\b|"
    r"\bcannot\b|\bwithout\b|\bnot a\b|\bnot an\b|\bdo not\b|"
    r"Prohibited Uses|does not score|not scores|not rankings|"
    r"Misinterpretation risk|Claim boundary|must not support|"
    r"winners or losers|league tables|Chip Sovereignty Score|"
    r"Named Entity Governance|Prohibited named-entity|market-news|"
    r"company-led|country assessment|product comparison|"
    r"sovereign company|sovereign country|best AI chip"
    r")",
    re.IGNORECASE,
)

ALLOWED_SECTIONS = (
    "## What the Model Does Not Do",
    "## Prohibited Uses",
    "## Map Interpretation Rules",
    "## Named Entity Governance",
    "## Versioning Notes",
)


def fail(errors: list[str]) -> None:
    for error in errors:
        print(f"FAIL: {error}", file=sys.stderr)
    raise SystemExit(1)


def in_allowed_section(lines: list[str], line_no: int) -> bool:
    current = ""
    for idx in range(line_no - 1, -1, -1):
        line = lines[idx].strip()
        if line.startswith("## "):
            current = line
            break
    return any(marker in current for marker in ALLOWED_SECTIONS)


def validate_json_model(model: dict) -> list[str]:
    errors: list[str] = []
    missing = REQUIRED_JSON_SECTIONS - model.keys()
    if missing:
        errors.append(f"json missing required sections: {sorted(missing)}")

    controlled = [
        ("layers", EXPECTED_LAYERS),
        ("exposure_types", EXPECTED_EXPOSURES),
        ("confidence_levels", EXPECTED_CONFIDENCE),
        ("artifact_outputs", EXPECTED_ARTIFACTS),
    ]
    for field, expected in controlled:
        actual = set(model.get(field, []))
        if actual != expected:
            errors.append(
                f"json {field} must exactly match the governed vocabulary; "
                f"missing={sorted(expected - actual)}, extra={sorted(actual - expected)}"
            )

    prohibited = set(model.get("prohibited_outputs", []))
    for required in {"sovereignty_score", "ranking"}:
        if required not in prohibited:
            errors.append(f"json prohibited_outputs must include {required}")

    boundaries = model.get("artifact_boundaries", {})
    if not isinstance(boundaries, dict) or set(boundaries) != EXPECTED_ARTIFACTS:
        errors.append("json artifact_boundaries must define exactly the four governed artifact outputs")
    else:
        for artifact, definition in boundaries.items():
            if not isinstance(definition, dict):
                errors.append(f"json artifact boundary for {artifact} must be an object")
                continue
            for field in {"purpose", "boundary"}:
                if not isinstance(definition.get(field), str) or not definition[field].strip():
                    errors.append(f"json artifact boundary for {artifact} requires non-empty {field}")

    questions = model.get("questions", [])
    if not isinstance(questions, list) or not 8 <= len(questions) <= 16:
        errors.append("json questions must be a list containing 8 to 16 items")
        return errors

    ids: set[str] = set()
    covered_layers: set[str] = set()
    for index, question in enumerate(questions, start=1):
        label = f"json question {index}"
        if not isinstance(question, dict):
            errors.append(f"{label} must be an object")
            continue
        for field in {"id", "prompt", "layers", "exposure_types", "suggested_artifacts"}:
            if field not in question:
                errors.append(f"{label} missing {field}")
        question_id = question.get("id")
        if not isinstance(question_id, str) or not question_id:
            errors.append(f"{label} has invalid id")
        elif question_id in ids:
            errors.append(f"duplicate question id: {question_id}")
        else:
            ids.add(question_id)

        references = [
            ("layers", EXPECTED_LAYERS),
            ("exposure_types", EXPECTED_EXPOSURES),
            ("suggested_artifacts", EXPECTED_ARTIFACTS),
        ]
        for field, allowed in references:
            values = question.get(field, [])
            if not isinstance(values, list) or not values:
                errors.append(f"{label} {field} must be a non-empty list")
                continue
            invalid = set(values) - allowed
            if invalid:
                errors.append(f"{label} has invalid {field}: {sorted(invalid)}")
        covered_layers.update(question.get("layers", []))

    missing_coverage = EXPECTED_LAYERS - covered_layers
    if missing_coverage:
        errors.append(f"json questions do not cover layers: {sorted(missing_coverage)}")
    return errors


def validate_markdown_model() -> list[str]:
    errors: list[str] = []

    if not MODEL_PATH.is_file():
        errors.append("CHIP_DEPENDENCY_MAP_MODEL.md is missing")
        return errors

    content = MODEL_PATH.read_text(encoding="utf-8")
    lines = content.splitlines()

    if "Chip Dependency Map Model v1.0.0" not in content:
        errors.append("missing title version Chip Dependency Map Model v1.0.0")

    for layer in REQUIRED_ONTOLOGY_LAYERS:
        if layer not in content:
            errors.append(f"missing ontology layer: {layer}")

    for state in REQUIRED_DEPENDENCY_STATES:
        if state not in content:
            errors.append(f"missing dependency state: {state}")

    for phrase in REQUIRED_MODEL_PHRASES:
        if phrase not in content:
            errors.append(f"missing required phrase/section: {phrase}")

    if not README_PATH.is_file():
        errors.append("README.md is missing")
    elif "CHIP_DEPENDENCY_MAP_MODEL.md" not in README_PATH.read_text(encoding="utf-8"):
        errors.append("README.md does not reference CHIP_DEPENDENCY_MAP_MODEL.md")

    if not DECISION_LOG_PATH.is_file():
        errors.append("DECISION_LOG.md is missing")
    elif "ADR-015" not in DECISION_LOG_PATH.read_text(encoding="utf-8"):
        errors.append("DECISION_LOG.md does not include ADR-015")

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

    return errors


def main() -> None:
    errors: list[str] = []

    try:
        with JSON_PATH.open(encoding="utf-8") as handle:
            model = json.load(handle)
    except (OSError, json.JSONDecodeError) as exc:
        fail([f"could not load {JSON_PATH}: {exc}"])

    errors.extend(validate_json_model(model))
    errors.extend(validate_markdown_model())

    if errors:
        fail(errors)

    print(
        "PASS: Chip Dependency Map model is valid "
        f"({len(model['questions'])} questions, {len(model['layers'])} layers, "
        "5 dependency states, v1 document)."
    )


if __name__ == "__main__":
    main()
