#!/usr/bin/env python3
"""Validate the governed strategic offerings model."""

from __future__ import annotations

import json
import sys
from pathlib import Path

REQUIRED_IDS = {
    "compute_sovereignty_brief",
    "chip_dependency_audit",
    "premium_reference_dossier",
    "ontology_methodology_licensing",
    "strategic_acquisition_inquiry",
}
TOP_LEVEL = {
    "offerings_version",
    "updated_at",
    "protocol_reference",
    "premium_boundary_reference",
    "strategic_offerings",
}
REQUIRED_FIELDS = {
    "id",
    "label",
    "purpose",
    "suitable_when",
    "not_suitable_when",
    "required_inputs",
    "deliverable_boundary",
    "evidence_basis",
    "prohibited_outputs",
    "trust_constraints",
    "inquiry_type",
}


def main() -> None:
    path = Path(__file__).resolve().parents[1] / "data" / "strategic-offerings.json"
    try:
        model = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        print(f"FAIL: could not load strategic offerings: {exc}", file=sys.stderr)
        raise SystemExit(1)

    errors: list[str] = []
    missing = TOP_LEVEL - model.keys()
    if missing:
        errors.append(f"missing top-level fields: {sorted(missing)}")

    offerings = model.get("strategic_offerings", [])
    if not isinstance(offerings, list):
        errors.append("strategic_offerings must be a list")
        offerings = []

    ids: set[str] = set()
    for index, offering in enumerate(offerings, 1):
        label = f"offering {index}"
        if not isinstance(offering, dict):
            errors.append(f"{label} must be an object")
            continue

        fields = REQUIRED_FIELDS - offering.keys()
        if fields:
            errors.append(f"{label} missing fields: {sorted(fields)}")

        offering_id = offering.get("id")
        if offering_id in ids:
            errors.append(f"duplicate id: {offering_id}")
        ids.add(offering_id)

        for list_field in ("suitable_when", "not_suitable_when", "required_inputs", "prohibited_outputs", "trust_constraints"):
            value = offering.get(list_field)
            if not isinstance(value, list) or not value:
                errors.append(f"{label} {list_field} must be a non-empty list")

        for text_field in ("purpose", "deliverable_boundary", "evidence_basis", "inquiry_type", "label"):
            if not str(offering.get(text_field, "")).strip():
                errors.append(f"{label} {text_field} must be non-empty")

    if ids != REQUIRED_IDS:
        missing_ids = sorted(REQUIRED_IDS - ids)
        extra_ids = sorted(ids - REQUIRED_IDS)
        if missing_ids:
            errors.append(f"missing required offering ids: {missing_ids}")
        if extra_ids:
            errors.append(f"unexpected offering ids: {extra_ids}")

    if errors:
        for error in errors:
            print(f"FAIL: {error}", file=sys.stderr)
        raise SystemExit(1)

    print(f"PASS: Strategic offerings model is valid ({len(offerings)} offerings).")


if __name__ == "__main__":
    main()
