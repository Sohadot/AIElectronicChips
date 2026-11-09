#!/usr/bin/env python3
"""Fail-closed structural and registry cross-reference validation for the Atlas."""

from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ATLAS = ROOT / "data" / "dependency-atlas.json"
REGISTRY = ROOT / "data" / "source-registry.json"
LAYERS = {
    "design", "fabrication", "packaging", "memory",
    "interconnect", "power_thermal", "controls", "deployment",
}
NODE_KINDS = {"ontology_layer", "technology", "capability", "infrastructure", "policy"}
RELATION_TYPES = {"requires", "integrates_with", "constrained_by", "governed_by", "enables"}
CLAIM_CLASSES = {"verified_fact", "attributed_statement", "bounded_analysis"}
CONFIDENCE = {"high", "medium", "low"}
ID_PATTERN = re.compile(r"^[a-z][a-z0-9]*(?:-[a-z0-9]+)*$")
ATLAS_FIELDS = {
    "atlas_id", "version", "status", "as_of", "ontology_reference",
    "standard_reference", "source_registry_reference", "description",
    "nodes", "relationships",
}
NODE_FIELDS = {"id", "label", "kind", "layers", "description"}
EDGE_FIELDS = {
    "id", "from", "to", "relation_type", "statement", "claim_class",
    "evidence", "geographic_scope", "temporal_scope", "as_of",
    "reviewed_at", "review_owner", "confidence", "limitations",
}
EVIDENCE_FIELDS = {"source_id", "supported_claim_type"}
# A company's own announcement, earnings release or product page records what the
# company said; it cannot on its own establish a verified_fact. Such edges must be classified as
# attributed_statement (or bounded_analysis), or cite an additional record type.
SELF_REPORTED_SOURCE_TYPES = {"official_technical_disclosure", "company_announcement"}


def nonempty(value: object) -> bool:
    return isinstance(value, str) and bool(value.strip())


def string_list(value: object) -> bool:
    return isinstance(value, list) and bool(value) and all(nonempty(x) for x in value)


def parse_date(value: object, where: str, errors: list[str]) -> date | None:
    if not nonempty(value):
        errors.append(f"{where} must be an ISO date")
        return None
    try:
        result = date.fromisoformat(value)
    except ValueError:
        errors.append(f"{where} must be a valid ISO date: {value}")
        return None
    if result.isoformat() != value:
        errors.append(f"{where} must use YYYY-MM-DD")
        return None
    return result


def validate(atlas: object, registry: object, today: date | None = None) -> list[str]:
    """Pure validation entry point: tests can mutate fixtures without touching disk."""
    errors: list[str] = []
    today = today or date.today()
    if not isinstance(atlas, dict):
        return ["atlas root must be an object"]
    if not isinstance(registry, dict):
        return ["source registry root must be an object"]

    missing = ATLAS_FIELDS - set(atlas)
    extra = set(atlas) - ATLAS_FIELDS
    if missing:
        errors.append(f"atlas missing fields: {sorted(missing)}")
    if extra:
        errors.append(f"atlas unknown fields: {sorted(extra)}")

    if atlas.get("atlas_id") != "aec-dependency-evidence-atlas":
        errors.append("invalid atlas_id")
    if atlas.get("version") != "0.1.0":
        errors.append("unsupported atlas schema version")
    if atlas.get("status") not in {"foundation", "evidence_backed"}:
        errors.append("invalid atlas status")
    if atlas.get("ontology_reference") != "COMPUTE_SOVEREIGNTY_ONTOLOGY.md":
        errors.append("ontology reference mismatch")
    if atlas.get("standard_reference") != "COMPUTE_SOVEREIGNTY_STANDARD.md":
        errors.append("standard reference mismatch")
    if atlas.get("source_registry_reference") != "data/source-registry.json":
        errors.append("source registry reference mismatch")
    if not nonempty(atlas.get("description")):
        errors.append("atlas description must be non-empty")
    atlas_date = parse_date(atlas.get("as_of"), "atlas.as_of", errors)
    if atlas_date and atlas_date > today:
        errors.append("atlas.as_of is in the future")

    registered = {}
    entries = registry.get("source_records")
    if not isinstance(entries, list):
        errors.append("registry source_records must be a list")
        entries = []
    for source in entries:
        if isinstance(source, dict) and nonempty(source.get("id")):
            if source["id"] in registered:
                errors.append(f"duplicate registry ID: {source['id']}")
            registered[source["id"]] = source

    nodes = atlas.get("nodes")
    if not isinstance(nodes, list):
        errors.append("nodes must be a list")
        nodes = []
    node_ids: set[str] = set()
    layer_nodes: set[str] = set()
    node_index: dict[str, dict] = {}
    for i, node in enumerate(nodes):
        where = f"nodes[{i}]"
        if not isinstance(node, dict):
            errors.append(f"{where} must be an object")
            continue
        if set(node) != NODE_FIELDS:
            errors.append(f"{where} fields mismatch: missing={sorted(NODE_FIELDS-set(node))}, extra={sorted(set(node)-NODE_FIELDS)}")
        nid = node.get("id")
        if not nonempty(nid) or not ID_PATTERN.fullmatch(nid):
            errors.append(f"{where} invalid id")
            continue
        if nid in node_ids:
            errors.append(f"{where} duplicate node ID: {nid}")
        node_ids.add(nid)
        node_index[nid] = node
        if not nonempty(node.get("label")) or not nonempty(node.get("description")):
            errors.append(f"{where} requires label and description")
        if node.get("kind") not in NODE_KINDS:
            errors.append(f"{where} invalid node kind")
        node_layers = node.get("layers")
        if not string_list(node_layers) or set(node_layers) - LAYERS or len(set(node_layers)) != len(node_layers):
            errors.append(f"{where} invalid ontology layers")
        if node.get("kind") == "ontology_layer":
            if not isinstance(node_layers, list) or len(node_layers) != 1:
                errors.append(f"{where} ontology layer node must map exactly one layer")
            else:
                layer = node_layers[0]
                if nid != "layer-" + layer.replace("_", "-"):
                    errors.append(f"{where} noncanonical ontology layer node ID")
                layer_nodes.add(layer)

    if layer_nodes != LAYERS:
        errors.append(f"missing or invalid canonical ontology layers: {sorted(LAYERS-layer_nodes)}")
    if len([n for n in nodes if isinstance(n, dict) and n.get("kind") == "ontology_layer"]) != 8:
        errors.append("atlas must contain exactly eight canonical ontology layer nodes")

    relationships = atlas.get("relationships")
    if not isinstance(relationships, list):
        errors.append("relationships must be a list")
        relationships = []
    if atlas.get("status") == "evidence_backed" and not relationships:
        errors.append("evidence_backed atlas requires at least one reviewed relationship")
    if atlas.get("status") == "foundation" and relationships:
        errors.append("foundation atlas cannot contain published relationships; change status after review")

    edge_ids: set[str] = set()
    edge_keys: set[tuple] = set()
    for i, edge in enumerate(relationships):
        where = f"relationships[{i}]"
        if not isinstance(edge, dict):
            errors.append(f"{where} must be an object")
            continue
        if set(edge) != EDGE_FIELDS:
            errors.append(f"{where} fields mismatch: missing={sorted(EDGE_FIELDS-set(edge))}, extra={sorted(set(edge)-EDGE_FIELDS)}")
        eid = edge.get("id")
        if not nonempty(eid) or not ID_PATTERN.fullmatch(eid):
            errors.append(f"{where} invalid id")
        elif eid in edge_ids:
            errors.append(f"{where} duplicate edge ID: {eid}")
        else:
            edge_ids.add(eid)
        a, b = edge.get("from"), edge.get("to")
        if not nonempty(a) or a not in node_ids or not nonempty(b) or b not in node_ids:
            errors.append(f"{where} references unknown endpoint(s)")
        elif a == b:
            errors.append(f"{where} has a self-loop")
        else:
            key = (a, b, edge.get("relation_type"))
            if key in edge_keys:
                errors.append(f"{where} duplicates an existing from/to/relation_type relationship")
            edge_keys.add(key)
        if edge.get("relation_type") not in RELATION_TYPES:
            errors.append(f"{where} invalid relation_type")
        if edge.get("claim_class") not in CLAIM_CLASSES:
            errors.append(f"{where} invalid claim_class")
        if edge.get("confidence") not in CONFIDENCE:
            errors.append(f"{where} invalid confidence")
        for field in ("statement", "geographic_scope", "temporal_scope", "review_owner"):
            if not nonempty(edge.get(field)) or str(edge.get(field)).strip().lower() in {"unassigned", "todo", "tbd"}:
                errors.append(f"{where}.{field} must be specific and non-empty")
        if not string_list(edge.get("limitations")):
            errors.append(f"{where}.limitations must be a non-empty list")

        as_of = parse_date(edge.get("as_of"), where + ".as_of", errors)
        reviewed = parse_date(edge.get("reviewed_at"), where + ".reviewed_at", errors)
        if as_of and reviewed and as_of > reviewed:
            errors.append(f"{where}.as_of exceeds reviewed_at")
        if reviewed and reviewed > today:
            errors.append(f"{where}.reviewed_at is in the future")
        if as_of and atlas_date and as_of > atlas_date:
            errors.append(f"{where}.as_of exceeds atlas.as_of")

        citations = edge.get("evidence")
        if not isinstance(citations, list) or not citations:
            errors.append(f"{where}.evidence must contain at least one registry citation")
            continue
        used_sources: set[str] = set()
        cited_types: list[object] = []
        for j, citation in enumerate(citations):
            cwhere = f"{where}.evidence[{j}]"
            if not isinstance(citation, dict) or set(citation) != EVIDENCE_FIELDS:
                errors.append(f"{cwhere} must contain exactly source_id and supported_claim_type")
                continue
            sid, claim = citation.get("source_id"), citation.get("supported_claim_type")
            if not nonempty(sid) or not nonempty(claim):
                errors.append(f"{cwhere} requires nonempty values")
                continue
            if sid in used_sources:
                errors.append(f"{cwhere} duplicate source ID: {sid}")
            used_sources.add(sid)
            source = registered.get(sid)
            if source is None:
                errors.append(f"{cwhere} unregistered source: {sid}")
                continue
            cited_types.append(source.get("source_type"))
            if source.get("status") != "active":
                errors.append(f"{cwhere} source is not active: {sid}")
            supported = source.get("supported_claim_types", [])
            if not isinstance(supported, list) or claim not in supported:
                errors.append(f"{cwhere} source does not support claim type: {claim}")
            if a in node_index and b in node_index:
                source_layers = source.get("ontology_layers", [])
                edge_layers = set(node_index[a].get("layers", [])) | set(node_index[b].get("layers", []))
                if not isinstance(source_layers, list) or not (set(source_layers) & edge_layers):
                    errors.append(f"{cwhere} source ontology layers do not overlap endpoints")
            accessed = parse_date(source.get("accessed_at"), f"registry[{sid}].accessed_at", errors)
            if reviewed and accessed and reviewed < accessed:
                errors.append(f"{cwhere} reviewer date predates recorded source access")
            published_field = "publication_date" if source.get("publication_date") else "effective_date"
            published = parse_date(source.get(published_field), f"registry[{sid}].{published_field}", errors)
            if published and as_of and published > as_of:
                errors.append(f"{cwhere} source {published_field} is later than the relationship as_of date")
        if (
            edge.get("claim_class") == "verified_fact"
            and cited_types
            and all(t in SELF_REPORTED_SOURCE_TYPES for t in cited_types)
        ):
            errors.append(
                f"{where} verified_fact cannot rest solely on self-reported company disclosures; "
                "classify as attributed_statement or cite an independent record"
            )
    return errors


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--atlas", type=Path, default=ATLAS, help="atlas JSON path (default: repository atlas)")
    parser.add_argument("--registry", type=Path, default=REGISTRY, help="source registry JSON path")
    args = parser.parse_args(argv)
    try:
        atlas = json.loads(args.atlas.read_text(encoding="utf-8"))
        registry = json.loads(args.registry.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        print(f"FAIL: dependency atlas or source registry unreadable: {exc}", file=sys.stderr)
        raise SystemExit(1)
    errors = validate(atlas, registry)
    if errors:
        for err in errors:
            print(f"FAIL: {err}", file=sys.stderr)
        raise SystemExit(1)
    print(f"PASS: Dependency Evidence Atlas valid ({len(atlas['nodes'])} nodes, {len(atlas['relationships'])} reviewed relationships; status={atlas['status']}).")


if __name__ == "__main__":
    main()
