#!/usr/bin/env python3
"""Atlas validation regression checks; no external network or packages required."""

from __future__ import annotations

import copy
import json
import subprocess
import sys
import tempfile
import unittest
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from validate_dependency_atlas import LAYERS, validate  # noqa: E402

VALIDATOR = ROOT / "scripts" / "validate_dependency_atlas.py"

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
        "source_type": "official_technical_disclosure", "publication_date": "2025-04-16",
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

    # --- Additional rejection paths (Sprint 10 hardening) -------------------

    def test_invalid_claim_class(self):
        atlas, registry = fixture()
        atlas["relationships"][0]["claim_class"] = "confirmed"
        self.assert_fails(atlas, registry, "invalid claim_class")

    def test_invalid_relation_type(self):
        atlas, registry = fixture()
        atlas["relationships"][0]["relation_type"] = "supplies"
        self.assert_fails(atlas, registry, "invalid relation_type")

    def test_malformed_date(self):
        atlas, registry = fixture()
        atlas["relationships"][0]["as_of"] = "2026-13-40"
        self.assert_fails(atlas, registry, "valid ISO date")

    def test_non_canonical_date_format(self):
        atlas, registry = fixture()
        atlas["relationships"][0]["reviewed_at"] = "20260614"
        self.assert_fails(atlas, registry, "reviewed_at")

    def test_as_of_after_review(self):
        atlas, registry = fixture()
        atlas["relationships"][0]["as_of"] = "2026-06-20"
        self.assert_fails(atlas, registry, "as_of exceeds reviewed_at")

    def test_missing_geographic_scope(self):
        atlas, registry = fixture()
        atlas["relationships"][0]["geographic_scope"] = "  "
        self.assert_fails(atlas, registry, "geographic_scope must be specific")

    def test_missing_temporal_scope(self):
        atlas, registry = fixture()
        del atlas["relationships"][0]["temporal_scope"]
        self.assert_fails(atlas, registry, "temporal_scope must be specific")

    def test_placeholder_reviewer(self):
        atlas, registry = fixture()
        atlas["relationships"][0]["review_owner"] = "TBD"
        self.assert_fails(atlas, registry, "review_owner must be specific")

    def test_missing_evidence(self):
        atlas, registry = fixture()
        atlas["relationships"][0]["evidence"] = []
        self.assert_fails(atlas, registry, "evidence must contain at least one")

    def test_duplicate_edge_id(self):
        atlas, registry = fixture()
        twin = copy.deepcopy(atlas["relationships"][0])
        twin["relation_type"] = "requires"
        atlas["relationships"].append(twin)
        self.assert_fails(atlas, registry, "duplicate edge ID")

    def test_semantic_duplicate_edge(self):
        atlas, registry = fixture()
        twin = copy.deepcopy(atlas["relationships"][0])
        twin["id"] = "rel-hbm-packaging-copy"
        atlas["relationships"].append(twin)
        self.assert_fails(atlas, registry, "duplicates an existing from/to/relation_type")

    def test_duplicate_registry_id(self):
        atlas, registry = fixture()
        registry["source_records"].append(copy.deepcopy(registry["source_records"][0]))
        self.assert_fails(atlas, registry, "duplicate registry ID")

    def test_self_loop(self):
        atlas, registry = fixture()
        atlas["relationships"][0]["to"] = "tech-hbm"
        self.assert_fails(atlas, registry, "self-loop")

    def test_invalid_confidence(self):
        atlas, registry = fixture()
        atlas["relationships"][0]["confidence"] = "certain"
        self.assert_fails(atlas, registry, "invalid confidence")

    def test_verified_fact_on_company_disclosure_only(self):
        atlas, registry = fixture()
        atlas["relationships"][0]["claim_class"] = "verified_fact"
        self.assert_fails(atlas, registry, "verified_fact cannot rest solely")

    def test_verified_fact_with_independent_record_passes(self):
        atlas, registry = fixture()
        atlas["relationships"][0]["claim_class"] = "verified_fact"
        registry["source_records"].append({
            "id": "standard-test-source", "status": "active", "accessed_at": "2026-06-14",
            "source_type": "technical_standard", "publication_date": "2025-04-16",
            "supported_claim_types": ["technical_specification"],
            "ontology_layers": ["memory"],
        })
        atlas["relationships"][0]["evidence"].append(
            {"source_id": "standard-test-source", "supported_claim_type": "technical_specification"})
        self.assertEqual([], validate(atlas, registry, today=TODAY))

    def test_source_published_after_relationship_date(self):
        atlas, registry = fixture()
        registry["source_records"][0]["publication_date"] = "2026-07-01"
        self.assert_fails(atlas, registry, "later than the relationship as_of")

    def test_retired_source(self):
        atlas, registry = fixture()
        registry["source_records"][0]["status"] = "retired"
        self.assert_fails(atlas, registry, "not active")


class AtlasCliExitCodeTests(unittest.TestCase):
    """Prove the gate is fail-closed at the process level, which is what CI consumes."""

    def run_cli(self, atlas, registry):
        with tempfile.TemporaryDirectory() as tmp:
            atlas_path = Path(tmp) / "atlas.json"
            registry_path = Path(tmp) / "registry.json"
            atlas_path.write_text(json.dumps(atlas), encoding="utf-8")
            registry_path.write_text(json.dumps(registry), encoding="utf-8")
            return subprocess.run(
                [sys.executable, str(VALIDATOR), "--atlas", str(atlas_path), "--registry", str(registry_path)],
                capture_output=True, text=True, check=False,
            )

    def test_repository_files_exit_zero(self):
        result = subprocess.run([sys.executable, str(VALIDATOR)], capture_output=True, text=True, check=False)
        self.assertEqual(0, result.returncode, result.stderr)

    def test_malformed_relationship_exits_nonzero(self):
        atlas, registry = fixture()
        atlas["relationships"][0]["evidence"][0]["source_id"] = "fictional-source"
        result = self.run_cli(atlas, registry)
        self.assertNotEqual(0, result.returncode)
        self.assertIn("unregistered source", result.stderr)

    def test_unparseable_json_exits_nonzero(self):
        with tempfile.TemporaryDirectory() as tmp:
            bad = Path(tmp) / "atlas.json"
            bad.write_text("{not json", encoding="utf-8")
            result = subprocess.run(
                [sys.executable, str(VALIDATOR), "--atlas", str(bad)],
                capture_output=True, text=True, check=False,
            )
        self.assertNotEqual(0, result.returncode)
        self.assertIn("unreadable", result.stderr)


if __name__ == "__main__":
    unittest.main()
