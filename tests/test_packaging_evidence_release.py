"""Regression tests for IDE-003 (advanced packaging) and the per-release page mapping."""

from __future__ import annotations

import copy
import json
import sys
import tempfile
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
    cowos_evidence,
    inference_boundary_errors,
    reference_page,
    sentences,
)

PACKAGING = ROOT / "data" / "research" / "packaging-evidence-release-003.json"
HBM = ROOT / "data" / "research" / "hbm4-evidence-release-001.json"
PAGE = ROOT / "design-fabrication-packaging" / "index.html"
HBM_PAGE = ROOT / "hbm-memory" / "index.html"
TODAY = date(2026, 11, 9)


def load(path=PACKAGING):
    release = json.loads(path.read_text(encoding="utf-8"))
    registry = json.loads((ROOT / "data" / "source-registry.json").read_text(encoding="utf-8"))
    atlas = json.loads((ROOT / "data" / "dependency-atlas.json").read_text(encoding="utf-8"))
    return release, registry, atlas


def finding(release, fid):
    return next(f for f in release["findings"] if f["id"] == fid)


class PackagingReleaseTests(unittest.TestCase):
    def errors(self, release):
        _, registry, atlas = load()
        return check_release(release, registry, atlas, TODAY, "fixture")

    def test_repository_release_is_valid(self):
        release, _, _ = load()
        self.assertEqual([], self.errors(release))

    def test_release_is_an_unpublished_candidate(self):
        release, _, atlas = load()
        self.assertEqual("research_candidate", release["status"])
        self.assertIs(False, release["publication_eligible"])
        self.assertEqual([], atlas["relationships"])
        for edge in release["candidate_relationships"]:
            self.assertEqual("awaiting_human_review", edge["review_status"])
            self.assertIsNone(edge["reviewed_at"])
            self.assertEqual("unassigned", edge["review_owner"])
            self.assertEqual("ai_assisted_source_check", edge["research_recommendation"]["assessment_method"])

    def test_no_verified_facts_rest_on_company_or_consortium_statements(self):
        release, _, _ = load()
        self.assertNotIn("verified_fact", {f["claim_class"] for f in release["findings"]})

    def test_findings_citing_pending_ucie_release_declare_it(self):
        release, _, _ = load()
        for f in release["findings"]:
            if any(e["source_id"] == "ucie-2-specification-release-2024" for e in f["evidence"]):
                self.assertEqual("includes_pending_source", f["evidence_state"], f["id"])

    def test_pending_source_must_be_declared(self):
        release, _, _ = load()
        finding(release, "p-ucie-2-3d-dfx")["evidence_state"] = "cited_sources_active"
        self.assertTrue(any("evidence_state must be includes_pending_source" in e for e in self.errors(release)))

    def test_packaging_topics_accepted_and_unknown_topic_rejected(self):
        release, _, _ = load()
        self.assertIn("interposer_bridge", {f["topic"] for f in release["findings"]})
        release["findings"][0]["topic"] = "marketing"
        self.assertTrue(any("invalid topic" in e for e in self.errors(release)))

    def test_ucie_specifications_remain_unverified(self):
        release, _, _ = load()
        unresolved = {u["id"]: u for u in release["unresolved"]}
        self.assertIn("u-p-ucie-normative", unresolved)
        self.assertIn("u-p-ucie-implementation", unresolved)
        for f in release["findings"]:
            if f["topic"] == "chiplet_interface":
                self.assertEqual("attributed_statement", f["claim_class"], f["id"])

    def test_mi300x_unknowns_are_recorded_not_filled(self):
        release, _, _ = load()
        ids = {u["id"] for u in release["unresolved"]}
        self.assertTrue({"u-p-mi300x-stacking", "u-p-mi300x-cowos-variant"} <= ids)
        text = json.dumps(release["findings"])
        self.assertNotRegex(text, r"MI300X[^.\"]*(?:uses|via) SoIC")
        self.assertNotRegex(text, r"MI300X[^.\"]*CoWoS-[SRL]\b")


class ReferencePageMappingTests(unittest.TestCase):
    def test_each_release_maps_to_its_own_page(self):
        packaging, _, _ = load()
        hbm, _, _ = load(HBM)
        self.assertEqual(PAGE, reference_page(packaging))
        self.assertEqual(HBM_PAGE, reference_page(hbm))

    def test_new_release_must_name_a_page(self):
        release, registry, atlas = load()
        del release["reference_page"]
        errs = check_release(release, registry, atlas, TODAY, "fixture")
        self.assertTrue(any("reference_page" in e for e in errs), errs)

    def test_reference_page_cannot_point_at_research_data(self):
        release, registry, atlas = load()
        for bad in ("data/research/index.html", "../hbm-memory/index.html", "missing-page/index.html", "/hbm-memory/index.html"):
            release["reference_page"] = bad
            errs = check_release(release, registry, atlas, TODAY, "fixture")
            self.assertTrue(any("reference_page" in e for e in errs), bad)

    def test_unknown_release_field_still_rejected(self):
        release, registry, atlas = load()
        release["published_at"] = "2026-11-09"
        errs = check_release(release, registry, atlas, TODAY, "fixture")
        self.assertTrue(any("unknown fields" in e for e in errs), errs)

    def test_repository_pages_pass_against_their_own_release(self):
        packaging, registry, _ = load()
        self.assertEqual([], check_inference_boundaries(packaging, PAGE))
        self.assertEqual([], check_public_references(PAGE, registry))
        self.assertEqual([], check_review_representation(PAGE, {packaging["as_of"]}))

    def test_packaging_page_date_must_match_its_release(self):
        errs = check_review_representation(PAGE, {"2026-12-01"})
        self.assertTrue(any("does not match" in e for e in errs), errs)

    def test_hbm_release_evidence_does_not_license_packaging_page(self):
        # The HBM release has no attributed MI300X/CoWoS finding, so it cannot vouch for the packaging page.
        hbm, _, _ = load(HBM)
        errs = check_inference_boundaries(hbm, PAGE)
        self.assertTrue(any("ties CoWoS to a product" in e for e in errs), errs)

    def test_ucie_pending_marker_is_visible(self):
        html = PAGE.read_text(encoding="utf-8")
        self.assertRegex(html, r"<code>ucie-2-specification-release-2024</code>, pending_review")


class EvidenceGatedCowosTests(unittest.TestCase):
    def setUp(self):
        self.release, _, _ = load()
        self.evidence = cowos_evidence(self.release)

    def test_evidence_comes_only_from_attributed_findings(self):
        self.assertEqual({"MI300X"}, set(self.evidence))
        self.assertIn("amd-synopsys-chiplet-packaging-2024", self.evidence["MI300X"])

    def test_page_sentence_needs_a_matching_citation(self):
        sentence = "AMD states that MI300X is integrated using TSMC CoWoS."
        self.assertEqual([], inference_boundary_errors(sentence, "p", self.evidence, {"amd-synopsys-chiplet-packaging-2024"}))
        self.assertTrue(inference_boundary_errors(sentence, "p", self.evidence, {"tsmc-2025-annual-report"}))
        self.assertTrue(inference_boundary_errors(sentence, "p", self.evidence, set()))

    def test_unevidenced_products_still_rejected(self):
        cited = {"amd-synopsys-chiplet-packaging-2024"}
        self.assertTrue(inference_boundary_errors("MI300A is built on CoWoS.", "p", self.evidence, cited))
        self.assertTrue(inference_boundary_errors("Rubin integrates its HBM4 on CoWoS.", "p", self.evidence, cited))
        self.assertTrue(inference_boundary_errors("MI300X and Rubin both use CoWoS.", "p", self.evidence, cited))

    def test_universal_claims_never_licensed(self):
        self.assertTrue(inference_boundary_errors("Like MI300X, all HBM4 uses CoWoS.", "p", self.evidence,
                                                  {"amd-synopsys-chiplet-packaging-2024"}))

    def test_claims_need_an_attributed_finding(self):
        # Without AMD's attributed statement, the candidate edge and the page sentence both fail.
        release = copy.deepcopy(self.release)
        release["findings"] = [f for f in release["findings"] if f["id"] != "p-amd-mi300x-cowos"]
        errs = check_inference_boundaries(release, PAGE)
        self.assertTrue(any("candidate rel-mi300x-integrates-with-cowos" in e for e in errs), errs)
        self.assertTrue(any(e.startswith("design-fabrication-packaging/index.html") for e in errs), errs)

    def test_bounded_analysis_cannot_create_evidence(self):
        release = copy.deepcopy(self.release)
        release["findings"].append({**copy.deepcopy(finding(release, "p-an-cowos-comparison")),
                                    "id": "p-an-fixture", "statement": "Blackwell is packaged with CoWoS-L."})
        self.assertNotIn("BLACKWELL", cowos_evidence(release))
        errs = check_inference_boundaries(release, PAGE)
        self.assertTrue(any("p-an-fixture" in e for e in errs), errs)

    def test_candidate_must_cite_the_finding_sources(self):
        release = copy.deepcopy(self.release)
        edge = next(e for e in release["candidate_relationships"] if e["id"] == "rel-mi300x-integrates-with-cowos")
        edge["evidence"] = [{"source_id": "tsmc-2025-annual-report", "supported_claim_type": "packaging_route_context"}]
        errs = check_inference_boundaries(release, PAGE)
        self.assertTrue(any("rel-mi300x-integrates-with-cowos" in e for e in errs), errs)

    def test_page_with_wrong_citation_fails(self):
        html = PAGE.read_text(encoding="utf-8").replace(
            "packaging technology\". <a class=\"cite\" href=\"#ref-9\">[9]</a>",
            "packaging technology\". <a class=\"cite\" href=\"#ref-1\">[1]</a>")
        with tempfile.TemporaryDirectory() as tmp:
            page = Path(tmp) / "index.html"
            page.write_text(html, encoding="utf-8")
            errs = check_inference_boundaries(self.release, page)
        self.assertTrue(any("ties CoWoS to a product" in e for e in errs), errs)


class CitationParsingTests(unittest.TestCase):
    def test_trailing_citations_attach_to_previous_sentence(self):
        self.assertEqual(["A claim. ⟦3⟧ ⟦4⟧", "Next claim."], sentences("A claim. ⟦3⟧ ⟦4⟧ Next claim."))

    def test_citation_only_fragment_is_not_a_sentence(self):
        self.assertEqual(["A claim. ⟦3⟧"], sentences("A claim. ⟦3⟧"))


class SharedCandidateNodeTests(unittest.TestCase):
    def test_repository_releases_share_identical_nodes(self):
        packaging, _, _ = load()
        hbm, _, _ = load(HBM)
        shared = {n["id"] for n in packaging["candidate_nodes"]} & {n["id"] for n in hbm["candidate_nodes"]}
        self.assertEqual({"tech-cowos"}, shared)
        self.assertEqual([], check_shared_candidate_nodes({"hbm": hbm, "packaging": packaging}))

    def test_diverging_node_definitions_rejected(self):
        packaging, _, _ = load()
        hbm, _, _ = load(HBM)
        node = next(n for n in packaging["candidate_nodes"] if n["id"] == "tech-cowos")
        node["description"] = "A different definition."
        errs = check_shared_candidate_nodes({"hbm": hbm, "packaging": packaging})
        self.assertTrue(any("tech-cowos" in e for e in errs), errs)


if __name__ == "__main__":
    unittest.main()
