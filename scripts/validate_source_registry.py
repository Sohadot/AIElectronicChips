#!/usr/bin/env python3
"""Validate the governed source registry."""

from __future__ import annotations

import json
import sys
from pathlib import Path

LAYERS = {"design", "fabrication", "packaging", "memory", "interconnect", "power_thermal", "controls", "deployment"}
STATUSES = {"active", "pending_review", "retired"}
SOURCE_TYPES = {"government_rule", "regulation", "company_filing", "annual_report", "institutional_report", "technical_standard", "peer_reviewed_research", "official_dataset"}
TOP_LEVEL = {"registry_version", "updated_at", "source_policy_reference", "source_records"}
REQUIRED = {"id", "title", "publisher", "source_type", "canonical_url", "accessed_at", "ontology_layers", "supported_claim_types", "geographic_scope", "temporal_scope", "confidence_use", "use_limitations", "status"}


def main() -> None:
    path = Path(__file__).resolve().parents[1] / "data" / "source-registry.json"
    try:
        registry = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        print(f"FAIL: could not load registry: {exc}", file=sys.stderr)
        raise SystemExit(1)
    errors: list[str] = []
    missing = TOP_LEVEL - registry.keys()
    if missing:
        errors.append(f"missing top-level fields: {sorted(missing)}")
    records = registry.get("source_records", [])
    if not isinstance(records, list) or len(records) < 8:
        errors.append("source_records must contain at least 8 records")
        records = []
    ids: set[str] = set()
    for index, record in enumerate(records, 1):
        label = f"record {index}"
        if not isinstance(record, dict):
            errors.append(f"{label} must be an object")
            continue
        fields = REQUIRED - record.keys()
        if fields:
            errors.append(f"{label} missing fields: {sorted(fields)}")
        if not record.get("publication_date") and not record.get("effective_date"):
            errors.append(f"{label} requires publication_date or effective_date")
        if record.get("id") in ids:
            errors.append(f"duplicate id: {record.get('id')}")
        ids.add(record.get("id"))
        if record.get("source_type") not in SOURCE_TYPES:
            errors.append(f"{label} invalid source_type: {record.get('source_type')}")
        if record.get("status") not in STATUSES:
            errors.append(f"{label} invalid status: {record.get('status')}")
        layers = record.get("ontology_layers", [])
        if not isinstance(layers, list) or not layers or set(layers) - LAYERS:
            errors.append(f"{label} has invalid ontology_layers: {layers}")
        if not str(record.get("canonical_url", "")).startswith("https://"):
            errors.append(f"{label} canonical_url must use https")
    if errors:
        for error in errors:
            print(f"FAIL: {error}", file=sys.stderr)
        raise SystemExit(1)
    pending = sum(r["status"] == "pending_review" for r in records)
    print(f"PASS: Source registry is valid ({len(records)} records, {pending} pending_review).")


if __name__ == "__main__":
    main()
