#!/usr/bin/env python3
"""Atlas validation regression checks; no external network or packages required."""

from __future__ import annotations

import copy
import sys
import unittest
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from validate_dependency_atlas import LAYERS, validate  # noqa: E402

TODAY = date(2026, 11, 1)


def fixture():
    nodes = [
        {"id": "layer-" + layer.replace("_", "-"), "label": layer,
         "kind": "ontology_layer", "layers": [layer], "description": "Reference layer."}
        for layer in sorted(LAYERS)
    ]
    nodes += [
        {"id": "tech-hbm", "label": "HBM", "kind": "technology",
         "layers": ["memory"], "description": "High-bandwidth memory technology."},
        {"id": "tech-packaging", "label": "Advanced Packaging", "kind": "technology",
         "layers": ["packaging"], "description": "Integration technology."},
    ]
    edge = {
        "id": "rel-hbm-packaging",
        "from": "tech-hbm",
        "to": "tech-packaging",
        "relation_type": "integrates_with",
        "statement": "Attributed disclosure links a memory architecture and its packaging integration.",
        "claim_class": "attributed_statement",
        "evidence": [{"source_id": "official-test-source", "supported_claim_type": "technical_specification"}],
        "geographic_scope": "Disclosed component only",
        "temporal_scope": "2025 product disclosure only",
        "as_of": "2026-06-14",
        "reviewed_at": "2026-06-14",
        "review_owner": "Research reviewer",
        "confidence": "medium",
        "limitations": ["No market capacity or availability inference."],
    }
    atlas = {
        "atlas_id": "aec-dependency-evidence-atlas",
        "version": "0.1.0",
        "status": "evidence_backed",
        "as_of": "2026-11-01",
        "ontology_reference": "COMPUTE_SOVEREIGNTY_ONTOLOGY.md",
        "standard_reference": "COMPUTE_SOVEREIGNTY_STANDARD.md",
        "source_registry_reference": "data/source-registry.json",
        "description": "Fixture for structural validation only, not a published claim.",
        "nodes": nodes,
        "relationships": [edge],
    }
    registry = {"source_records": [{
        "id": "official-test-source", "status": "active", "accessed_at": "2026-06-14",
        "supported_claim_types": ["technical_specification"],
        "ontology_layers": ["memory", "packaging"],
    }]}
    return atlas, registry


class AtlasGateTests(unittest.TestCase):
    def assert_fails(self, atlas, registry, fragment):
        errors = validate(atlas, registry, today=TODAY)
        self.assertTrue(any(fragment in e for e in errors), errors)

    def test_valid_reviewed_edge(self):
        atlas, registry = fixture()
        self.assertEqual([], validate(atlas, registry, today=TODAY))

    def test_valid_empty_foundation(self):
        atlas, registry = fixture()
        atlas["status"] = "foundation"
        atlas["relationships"] = []
        self.assertEqual([], validate(atlas, registry, today=TODAY))

    def test_foundation_cannot_publish_edges(self):
        atlas, registry = fixture()
        atlas["status"] = "foundation"
        self.assert_fails(atlas, registry, "foundation atlas cannot contain")

    def test_published_requires_edge(self):
        atlas, registry = fixture()
        atlas["relationships"] = []
        self.assert_fails(atlas, registry, "requires at least one")

    def test_missing_node(self):
        atlas, registry = fixture()
        atlas["relationships"][0]["to"] = "missing-technology"
        self.assert_fails(atlas, registry, "unknown endpoint")

    def test_duplicate_node(self):
        atlas, registry = fixture()
        atlas["nodes"].append(copy.deepcopy(atlas["nodes"][0]))
        self.assert_fails(atlas, registry, "duplicate node ID")

    def test_missing_layer(self):
        atlas, registry = fixture()
        atlas["nodes"] = [node for node in atlas["nodes"] if node["id"] != "layer-design"]
        self.assert_fails(atlas, registry, "missing or invalid canonical")

    def test_unregistered_source(self):
        atlas, registry = fixture()
        atlas["relationships"][0]["evidence"][0]["source_id"] = "fictional-source"
        self.assert_fails(atlas, registry, "unregistered source")

    def test_pending_source(self):
        atlas, registry = fixture()
        registry["source_records"][0]["status"] = "pending_review"
        self.assert_fails(atlas, registry, "not active")

    def test_unsupported_claim_type(self):
        atlas, registry = fixture()
        atlas["relationships"][0]["evidence"][0]["supported_claim_type"] = "production_capacity"
        self.assert_fails(atlas, registry, "does not support claim type")

    def test_source_layer_mismatch(self):
        atlas, registry = fixture()
        registry["source_records"][0]["ontology_layers"] = ["controls"]
        self.assert_fails(atlas, registry, "do not overlap")

    def test_future_review(self):
        atlas, registry = fixture()
        atlas["relationships"][0]["reviewed_at"] = "2030-01-01"
        self.assert_fails(atlas, registry, "future")

    def test_missing_limitations(self):
        atlas, registry = fixture()
        atlas["relationships"][0]["limitations"] = []
        self.assert_fails(atlas, registry, "limitations")

    def test_source_access_newer_than_review(self):
        atlas, registry = fixture()
        registry["source_records"][0]["accessed_at"] = "2026-07-01"
        self.assert_fails(atlas, registry, "predates recorded source access")

    def test_unknown_schema_field(self):
        atlas, registry = fixture()
        atlas["relationships"][0]["unreviewed_opinion"] = "yes"
        self.assert_fails(atlas, registry, "fields mismatch")


if __name__ == "__main__":
    unittest.main()
