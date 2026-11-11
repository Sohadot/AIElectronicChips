"""Regression tests for IDE-004 (interconnect and data movement)."""

from __future__ import annotations

import copy
import json
import sys
import unittest
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from validate_evidence_releases import (  # noqa: E402
    check_inference_boundaries,
    check_public_references,
    check_release,
    check_review_representation,
    check_shared_candidate_nodes,
    inference_boundary_errors,
    reference_page,
)

RESEARCH = ROOT / "data" / "research"
INTERCONNECT = RESEARCH / "interconnect-evidence-release-004.json"
PAGE = ROOT / "interconnects" / "index.html"
TODAY = date(2026, 11, 9)


def load(path=INTERCONNECT):
    release = json.loads(path.read_text(encoding="utf-8"))
    registry = json.loads((ROOT / "data" / "source-registry.json").read_text(encoding="utf-8"))
    atlas = json.loads((ROOT / "data" / "dependency-atlas.json").read_text(encoding="utf-8"))
    return release, registry, atlas


def finding(release, fid):
    return next(f for f in release["findings"] if f["id"] == fid)


class InterconnectReleaseTests(unittest.TestCase):
    def errors(self, release):
        _, registry, atlas = load()
        return check_release(release, registry, atlas, TODAY, "fixture")

    def assert_fails(self, release, fragment):
        errs = self.errors(release)
        self.assertTrue(any(fragment in e for e in errs), errs)

    def test_repository_release_is_valid(self):
        release, _, _ = load()
        self.assertEqual([], self.errors(release))

    def test_release_maps_to_interconnect_page(self):
        release, _, _ = load()
        self.assertEqual(PAGE, reference_page(release))

    def test_page_passes_against_its_own_release(self):
        release, registry, _ = load()
        self.assertEqual([], check_inference_boundaries(release, PAGE))
        self.assertEqual([], check_public_references(PAGE, registry))
        self.assertEqual([], check_review_representation(PAGE, {release["as_of"]}))

    def test_candidates_remain_unpublished_and_unreviewed(self):
        release, _, atlas = load()
        self.assertEqual([], atlas["relationships"])
        self.assertEqual("foundation", atlas["status"])
        for edge in release["candidate_relationships"]:
            self.assertEqual("awaiting_human_review", edge["review_status"])
            self.assertIsNone(edge["reviewed_at"])
            self.assertEqual("unassigned", edge["review_owner"])
            self.assertEqual("ai_assisted_source_check", edge["research_recommendation"]["assessment_method"])

    def test_earlier_releases_and_candidates_untouched(self):
        hbm = json.loads((RESEARCH / "hbm4-evidence-release-001.json").read_text(encoding="utf-8"))
        packaging = json.loads((RESEARCH / "packaging-evidence-release-003.json").read_text(encoding="utf-8"))
        self.assertEqual(5, len(hbm["candidate_relationships"]))
        self.assertEqual(3, len(packaging["candidate_relationships"]))
        self.assertEqual("1.1.1", hbm["version"])
        self.assertEqual("1.0.0", packaging["version"])

    def test_shared_mi300x_node_is_identical_across_releases(self):
        releases = {p.name: json.loads(p.read_text(encoding="utf-8")) for p in sorted(RESEARCH.glob("*.json"))}
        self.assertEqual([], check_shared_candidate_nodes(releases))

    def test_verified_facts_rest_only_on_the_standard(self):
        release, registry, _ = load()
        types = {s["id"]: s["source_type"] for s in registry["source_records"]}
        for f in release["findings"]:
            if f["claim_class"] == "verified_fact":
                self.assertTrue(all(types[e["source_id"]] == "technical_standard" for e in f["evidence"]), f["id"])

    def test_verified_fact_on_announcement_rejected(self):
        release, _, _ = load()
        finding(release, "i-uec-launch-claims")["claim_class"] = "verified_fact"
        self.assert_fails(release, "verified_fact cannot rest solely")

    def test_nvlink_conflict_is_recorded_not_reconciled(self):
        release, _, _ = load()
        values = {(q["value"], q["unit"]) for q in finding(release, "i-nvidia-nvlink6-figures")["quantities"]}
        self.assertTrue({("3.6", "TB/s"), ("3.0", "TB/s")} <= values)
        self.assertIn("u-i-nvlink6-figure", {u["id"] for u in release["unresolved"]})

    def test_ucie_2_stays_pending(self):
        _, registry, _ = load()
        record = next(s for s in registry["source_records"] if s["id"] == "ucie-2-specification-release-2024")
        self.assertEqual("pending_review", record["status"])


class QuantityScopeTests(unittest.TestCase):
    """Bandwidth figures must state unit, direction, scope, peak status and basis."""

    def errors(self, release):
        _, registry, atlas = load()
        return check_release(release, registry, atlas, TODAY, "fixture")

    def assert_fails(self, release, fragment):
        errs = self.errors(release)
        self.assertTrue(any(fragment in e for e in errs), errs)

    def test_figure_without_quantities_rejected_in_interconnect_topics(self):
        release, _, _ = load()
        del finding(release, "i-amd-mi300x-topology")["quantities"]
        self.assert_fails(release, "without a quantities list")

    def test_undescribed_figure_rejected(self):
        release, _, _ = load()
        f = finding(release, "i-amd-mi300x-topology")
        f["quantities"] = [q for q in f["quantities"] if q["value"] != "1024"]
        self.assert_fails(release, "figure 1024 GB/s has no quantities entry")

    def test_quantity_must_appear_in_statement(self):
        release, _, _ = load()
        finding(release, "i-amd-mi300x-topology")["quantities"][0]["value"] = "900"
        self.assert_fails(release, "does not appear in the finding statement")

    def test_bits_and_bytes_are_distinct_units(self):
        release, _, _ = load()
        q = finding(release, "i-nvidia-scale-out")["quantities"][0]
        q["unit"] = "TB/s"  # 1.6 Tb/s is bits; relabelling it as bytes must fail
        self.assert_fails(release, "does not appear in the finding statement")

    def test_invalid_direction_rejected(self):
        release, _, _ = load()
        finding(release, "i-amd-mi300x-topology")["quantities"][0]["direction"] = "both"
        self.assert_fails(release, "direction must be one of")

    def test_gt_per_second_is_not_payload_bandwidth(self):
        release, _, _ = load()
        q = next(q for q in finding(release, "i-cxl-3-rate")["quantities"] if q["unit"] == "GT/s")
        q["scope"] = "per_link"
        self.assert_fails(release, "GT/s is a per-lane transfer rate")

    def test_calculated_figure_requires_bounded_analysis(self):
        release, _, _ = load()
        finding(release, "i-amd-mi300x-topology")["quantities"][0]["basis"] = "calculated"
        self.assert_fails(release, "a calculated figure belongs in a bounded_analysis finding")

    def test_vendor_figure_cannot_be_presented_as_measured(self):
        release, _, _ = load()
        finding(release, "i-nvidia-gb200-aggregate")["quantities"][0]["basis"] = "measured"
        self.assert_fails(release, "a measured figure needs a measurement source")

    def test_specified_figure_needs_a_standard(self):
        release, _, _ = load()
        finding(release, "i-cxl-4-release")["quantities"][0]["basis"] = "specified"
        self.assert_fails(release, "a specified figure must come from a technical_standard source")

    def test_quantity_source_must_be_cited(self):
        release, _, _ = load()
        finding(release, "i-amd-mi300x-topology")["quantities"][0]["source_id"] = "nvidia-rubin-platform-architecture-2026"
        self.assert_fails(release, "source_id must be one of the finding's cited sources")

    def test_aggregate_system_figure_keeps_system_scope(self):
        release, _, _ = load()
        q = finding(release, "i-nvidia-gb200-aggregate")["quantities"][0]
        self.assertEqual("per_system", q["scope"])

    def test_hbm_release_is_unaffected_by_quantity_rules(self):
        hbm, registry, atlas = load(RESEARCH / "hbm4-evidence-release-001.json")
        self.assertEqual([], check_release(hbm, registry, atlas, TODAY, "hbm"))


class StandardsAndInteropBoundaryTests(unittest.TestCase):
    def test_interoperability_assertion_rejected(self):
        self.assertTrue(inference_boundary_errors("Spectrum-X is interoperable with every UEC NIC.", "p"))
        self.assertTrue(inference_boundary_errors("The NIC passed compliance testing.", "p"))
        self.assertTrue(inference_boundary_errors("CXL 3.0 devices interoperate with each other.", "p"))

    def test_negated_interoperability_allowed(self):
        self.assertEqual([], inference_boundary_errors("No reviewed source shows that it is interoperable with other NICs.", "p"))

    def test_unattributed_implementation_claim_rejected(self):
        self.assertTrue(inference_boundary_errors("MI300X supports CXL memory sharing.", "p"))
        self.assertTrue(inference_boundary_errors("Spectrum-X implements Ultra Ethernet.", "p"))

    def test_attributed_or_negated_implementation_allowed(self):
        self.assertEqual([], inference_boundary_errors("NVIDIA states that the Vera CPU supports CXL 3.1.", "p"))
        self.assertEqual([], inference_boundary_errors("No reviewed source states that MI300X supports CXL.", "p"))
        self.assertEqual([], inference_boundary_errors("A release says nothing about whether a product implements UCIe.", "p"))

    def test_specification_release_is_not_adoption(self):
        release, _, _ = load()
        statement = finding(release, "i-uec-launch-claims")["statement"]
        self.assertIn("compliance", statement)
        limitations = " ".join(finding(release, "i-uec-launch-claims")["limitations"])
        self.assertIn("not compliance or interoperability results", limitations)

    def test_page_rejects_unattributed_standard_claim(self):
        release, _, _ = load()
        html = PAGE.read_text(encoding="utf-8").replace(
            "No reviewed source states that Spectrum-X follows the Ultra Ethernet specification.",
            "Spectrum-X implements Ultra Ethernet.")
        import tempfile
        with tempfile.TemporaryDirectory() as tmp:
            page = Path(tmp) / "index.html"
            page.write_text(html, encoding="utf-8")
            errs = check_inference_boundaries(release, page)
        self.assertTrue(any("implements a standard" in e for e in errs), errs)



class BandwidthScopeIntegrityTests(unittest.TestCase):
    def test_amd_896_scope_is_not_promoted_to_vendor_confirmed_per_gpu(self):
        release, _, _ = load()
        finding = next(f for f in release["findings"] if f["id"] == "i-an-memory-vs-fabric")
        quantity = next(q for q in finding["quantities"] if q["value"] == "896")
        self.assertEqual("not_stated", quantity["direction"])
        self.assertEqual("not_stated", quantity["scope"])
        page = PAGE.read_text(encoding="utf-8")
        # IDE-009 reconciliation: AMD now states the direction, but per-GPU scope is still not vendor-stated.
        self.assertIn("AMD does not state that it is a per-GPU figure", page)
        self.assertIn("no reviewed AMD document states that 896 GB/s is a per-GPU figure", page)
        self.assertIn("not memory access speed", page)

if __name__ == "__main__":
    unittest.main()
