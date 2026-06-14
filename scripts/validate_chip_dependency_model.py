#!/usr/bin/env python3
"""Validate the governed Chip Dependency Map foundation model."""

from __future__ import annotations

import json
import sys
from pathlib import Path


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
REQUIRED_SECTIONS = {
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


def fail(errors: list[str]) -> None:
    for error in errors:
        print(f"FAIL: {error}", file=sys.stderr)
    raise SystemExit(1)


def validate(model: dict) -> list[str]:
    errors: list[str] = []
    missing = REQUIRED_SECTIONS - model.keys()
    if missing:
        errors.append(f"missing required sections: {sorted(missing)}")

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
                f"{field} must exactly match the governed vocabulary; "
                f"missing={sorted(expected - actual)}, extra={sorted(actual - expected)}"
            )

    prohibited = set(model.get("prohibited_outputs", []))
    for required in {"sovereignty_score", "ranking"}:
        if required not in prohibited:
            errors.append(f"prohibited_outputs must include {required}")

    boundaries = model.get("artifact_boundaries", {})
    if not isinstance(boundaries, dict) or set(boundaries) != EXPECTED_ARTIFACTS:
        errors.append("artifact_boundaries must define exactly the four governed artifact outputs")
    else:
        for artifact, definition in boundaries.items():
            if not isinstance(definition, dict):
                errors.append(f"artifact boundary for {artifact} must be an object")
                continue
            for field in {"purpose", "boundary"}:
                if not isinstance(definition.get(field), str) or not definition[field].strip():
                    errors.append(f"artifact boundary for {artifact} requires non-empty {field}")

    questions = model.get("questions", [])
    if not isinstance(questions, list) or not 8 <= len(questions) <= 16:
        errors.append("questions must be a list containing 8 to 16 items")
        return errors

    ids: set[str] = set()
    covered_layers: set[str] = set()
    for index, question in enumerate(questions, start=1):
        label = f"question {index}"
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
        errors.append(f"questions do not cover layers: {sorted(missing_coverage)}")
    return errors


def main() -> None:
    default_path = Path(__file__).resolve().parents[1] / "data" / "chip-dependency-model.json"
    model_path = Path(sys.argv[1]) if len(sys.argv) > 1 else default_path
    try:
        with model_path.open(encoding="utf-8") as handle:
            model = json.load(handle)
    except (OSError, json.JSONDecodeError) as exc:
        fail([f"could not load {model_path}: {exc}"])

    errors = validate(model)
    if errors:
        fail(errors)
    print(
        "PASS: Chip Dependency Map model is valid "
        f"({len(model['questions'])} questions, {len(model['layers'])} layers)."
    )


if __name__ == "__main__":
    main()
