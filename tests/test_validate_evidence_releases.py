#!/usr/bin/env python3
"""Regression checks for research-candidate evidence releases (no network)."""

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
from validate_evidence_releases import check_release  # noqa: E402

VALIDATOR = ROOT / "scripts" / "validate_evidence_releases.py"
RELEASE = ROOT / "data" / "research" / "hbm4-evidence-release-001.json"
TODAY = date(2026, 11, 9)


def load():
    release = json.loads(RELEASE.read_text(encoding="utf-8"))
    registry = json.loads((ROOT / "data" / "source-registry.json").read_text(encoding="utf-8"))
    atlas = json.loads((ROOT / "data" / "dependency-atlas.json").read_text(encoding="utf-8"))
    return release, registry, atlas


def first(release, cls):
    return next(f for f in release["findings"] if f["claim_class"] == cls)


class EvidenceReleaseTests(unittest.TestCase):
    def errors(self, release, registry, atlas):
        return check_release(release, registry, atlas, TODAY, "fixture")

    def assert_fails(self, release, registry, atlas, fragment):
        errs = self.errors(release, registry, atlas)
        self.assertTrue(any(fragment in e for e in errs), errs)

    def test_repository_release_is_valid(self):
        self.assertEqual([], self.errors(*load()))

    def test_release_cannot_claim_publication(self):
        release, registry, atlas = load()
        release["publication_eligible"] = True
        self.assert_fails(release, registry, atlas, "publication_eligible must be false")

    def test_release_status_locked(self):
        release, registry, atlas = load()
        release["status"] = "published"
        self.assert_fails(release, registry, atlas, "research_candidate")

    def test_unregistered_source(self):
        release, registry, atlas = load()
        release["findings"][0]["evidence"][0]["source_id"] = "invented-source"
        self.assert_fails(release, registry, atlas, "unregistered source")

    def test_missing_locator(self):
        release, registry, atlas = load()
        release["findings"][0]["evidence"][0]["locator"] = ""
        self.assert_fails(release, registry, atlas, "requires a locator")

    def test_invalid_class(self):
        release, registry, atlas = load()
        release["findings"][0]["claim_class"] = "confirmed"
        self.assert_fails(release, registry, atlas, "invalid claim_class")

    def test_verified_fact_on_press_release_only(self):
        release, registry, atlas = load()
        finding = first(release, "attributed_statement")
        finding["claim_class"] = "verified_fact"
        self.assert_fails(release, registry, atlas, "cannot rest solely on self-reported")

    def test_analysis_requires_assumptions(self):
        release, registry, atlas = load()
        del first(release, "bounded_analysis")["assumptions"]
        self.assert_fails(release, registry, atlas, "requires stated assumptions")

    def test_priority_language_outside_attribution(self):
        release, registry, atlas = load()
        first(release, "bounded_analysis")["statement"] += " It is the industry's first."
        self.assert_fails(release, registry, atlas, "priority or superiority language")

    def test_pending_source_must_be_disclosed(self):
        release, registry, atlas = load()
        pending = next(f for f in release["findings"] if f["evidence_state"] == "includes_pending_source")
        pending["evidence_state"] = "cited_sources_active"
        self.assert_fails(release, registry, atlas, "evidence_state must be includes_pending_source")

    def test_retired_source(self):
        release, registry, atlas = load()
        sid = release["findings"][4]["evidence"][0]["source_id"]
        next(s for s in registry["source_records"] if s["id"] == sid)["status"] = "retired"
        self.assert_fails(release, registry, atlas, "retired source")

    def test_source_postdates_finding(self):
        release, registry, atlas = load()
        release["findings"][4]["as_of"] = "2024-01-01"
        self.assert_fails(release, registry, atlas, "postdates the finding")

    def test_duplicate_ids(self):
        release, registry, atlas = load()
        release["findings"].append(copy.deepcopy(release["findings"][0]))
        self.assert_fails(release, registry, atlas, "duplicate id")

    def test_unresolved_requires_next_evidence(self):
        release, registry, atlas = load()
        release["unresolved"][0]["next_evidence_needed"] = " "
        self.assert_fails(release, registry, atlas, "next_evidence_needed must be non-empty")

    def test_candidate_cannot_carry_review(self):
        release, registry, atlas = load()
        release["candidate_relationships"][0]["reviewed_at"] = "2026-11-09"
        self.assert_fails(release, registry, atlas, "reviewed_at must be null")

    def test_candidate_cannot_name_reviewer(self):
        release, registry, atlas = load()
        release["candidate_relationships"][0]["review_owner"] = "Research reviewer"
        self.assert_fails(release, registry, atlas, "review_owner must be 'unassigned'")

    def test_candidate_must_meet_atlas_contract(self):
        release, registry, atlas = load()
        release["candidate_relationships"][0]["evidence"][0]["supported_claim_type"] = "production_capacity"
        self.assert_fails(release, registry, atlas, "fails Atlas publication contract")

    def test_candidate_citing_pending_source_is_blocked(self):
        release, registry, atlas = load()
        release["candidate_relationships"][0]["evidence"].append(
            {"source_id": "jedec-jesd270-4-hbm4-standard-2025", "supported_claim_type": "technical_specification"})
        self.assert_fails(release, registry, atlas, "source is not active")

    def test_candidate_already_published(self):
        release, registry, atlas = load()
        atlas["relationships"] = [copy.deepcopy(release["candidate_relationships"][0])]
        self.assert_fails(release, registry, atlas, "already published in Atlas")

    def test_diagnostic_answers_are_not_evidence(self):
        """Chip Dependency Map answers are not registry sources and cannot back a finding."""
        release, registry, atlas = load()
        release["findings"][0]["evidence"] = [{"source_id": "chip-dependency-map-response", "locator": "q1"}]
        self.assert_fails(release, registry, atlas, "unregistered source")


class EvidenceReleaseCliTests(unittest.TestCase):
    def test_repository_exit_zero(self):
        result = subprocess.run([sys.executable, str(VALIDATOR)], capture_output=True, text=True, check=False)
        self.assertEqual(0, result.returncode, result.stderr)

    def test_malformed_release_exits_nonzero(self):
        release, _, _ = load()
        release["candidate_relationships"][0]["review_status"] = "approved"
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "bad.json"
            path.write_text(json.dumps(release), encoding="utf-8")
            result = subprocess.run([sys.executable, str(VALIDATOR), str(path)], capture_output=True, text=True, check=False)
        self.assertNotEqual(0, result.returncode)
        self.assertIn("awaiting_human_review", result.stderr)


if __name__ == "__main__":
    unittest.main()
