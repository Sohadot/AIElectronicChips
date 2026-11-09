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
from validate_evidence_releases import (  # noqa: E402
    check_inference_boundaries,
    check_pages_exclusion,
    inference_boundary_errors,
    check_review_representation,
    check_public_references,
    check_release,
)

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
        finding = next(f for f in release["findings"] if f["id"] == "f-std-interface")
        sid = finding["evidence"][0]["source_id"]
        next(s for s in registry["source_records"] if s["id"] == sid)["status"] = "pending_review"
        self.assertEqual("cited_sources_active", finding["evidence_state"])
        self.assert_fails(release, registry, atlas, "evidence_state must be includes_pending_source")

    def test_announcement_cannot_be_promoted_to_verified_fact(self):
        """JEDEC's announcement is not the normative standard: it cannot alone establish a verified fact."""
        release, registry, atlas = load()
        next(f for f in release["findings"] if f["id"] == "f-std-interface")["claim_class"] = "verified_fact"
        self.assert_fails(release, registry, atlas, "cannot rest solely on self-reported")

    def test_jedec_findings_remain_attributed(self):
        release, _, _ = load()
        jedec = [f for f in release["findings"] if f["id"].startswith("f-std-")]
        self.assertGreaterEqual(len(jedec), 5)
        self.assertTrue(all(f["claim_class"] == "attributed_statement" for f in jedec))
        self.assertTrue(all(any("normative" in l for l in f["limitations"]) for f in jedec))

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
            {"source_id": "ucie-2-specification-release-2024", "supported_claim_type": "standard_release"})
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

    def test_pending_source_cannot_be_verified_fact(self):
        release, registry, atlas = load()
        finding = next(f for f in release["findings"] if f["id"] == "f-std-interface")
        sid = finding["evidence"][0]["source_id"]
        next(s for s in registry["source_records"] if s["id"] == sid)["status"] = "pending_review"
        finding["evidence_state"] = "includes_pending_source"
        finding["claim_class"] = "verified_fact"
        self.assert_fails(release, registry, atlas, "verified_fact cannot cite a pending_review source")

    def test_long_quote_rejected(self):
        release, registry, atlas = load()
        release["findings"][0]["evidence"][0]["locator"] = '"' + " ".join(["word"] * 21) + '"'
        self.assert_fails(release, registry, atlas, "quoted excerpt exceeds 20 words")

    def test_quote_total_per_citation_capped(self):
        release, registry, atlas = load()
        chunk = '"' + " ".join(["word"] * 15) + '"'
        release["findings"][0]["evidence"][0]["locator"] = "; ".join([chunk] * 3)
        self.assert_fails(release, registry, atlas, "quotes more than 40 words")


class PublicExposureTests(unittest.TestCase):
    def test_page_references_match_registry(self):
        _, registry, _ = load()
        self.assertEqual([], check_public_references(ROOT / "hbm-memory" / "index.html", registry))

    def test_pending_status_must_be_visible(self):
        _, registry, _ = load()
        sid = "samsung-hbm4-commercial-shipment-2026"
        next(s for s in registry["source_records"] if s["id"] == sid)["status"] = "pending_review"
        errors = check_public_references(ROOT / "hbm-memory" / "index.html", registry)
        self.assertTrue(any(sid in e for e in errors), errors)

    def check_modified_page(self, registry, old, new):
        html = (ROOT / "hbm-memory" / "index.html").read_text(encoding="utf-8")
        self.assertIn(old, html)
        with tempfile.TemporaryDirectory(dir=ROOT) as tmp:
            page = Path(tmp) / "index.html"
            page.write_text(html.replace(old, new, 1), encoding="utf-8")
            return check_public_references(page, registry)

    def test_active_source_cannot_be_labelled_pending(self):
        _, registry, _ = load()
        sid = "jedec-jesd270-4-hbm4-standard-2025"
        errors = self.check_modified_page(registry, f"<code>{sid}</code>.", f"<code>{sid}</code> · <strong>pending_review</strong>.")
        self.assertTrue(any(sid in e for e in errors), errors)

    def test_reference_numbering_must_follow_list_order(self):
        _, registry, _ = load()
        errors = self.check_modified_page(registry, '<li id="ref-2">', '<li id="ref-99">')
        self.assertTrue(any("must run 1..n in order" in e for e in errors), errors)

    def test_dangling_citation_rejected(self):
        _, registry, _ = load()
        errors = self.check_modified_page(registry, 'href="#ref-1">[1]</a>', 'href="#ref-42">[42]</a>')
        self.assertTrue(any("has no matching reference" in e for e in errors), errors)

    def test_workflow_excludes_research(self):
        self.assertEqual([], check_pages_exclusion(ROOT / ".github" / "workflows" / "validate-and-deploy.yml", ROOT / "data" / "research"))

    def test_workflow_without_exclusion_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            wf = Path(tmp) / "wf.yml"
            wf.write_text("        with:\n          path: .\n", encoding="utf-8")
            errors = check_pages_exclusion(wf, ROOT / "data" / "research")
        self.assertTrue(errors)


class ReviewRepresentationTests(unittest.TestCase):
    """Evidence compilation, automated validation and human review are different events."""

    PAGE = ROOT / "hbm-memory" / "index.html"

    def check(self, html, dates=frozenset({"2026-11-09"})):
        with tempfile.TemporaryDirectory() as tmp:
            page = Path(tmp) / "index.html"
            page.write_text(html, encoding="utf-8")
            return check_review_representation(page, set(dates))

    def test_repository_page_states_compilation_and_pending_review(self):
        self.assertEqual([], check_review_representation(self.PAGE, {"2026-11-09"}))

    def test_page_matches_release_compilation_date(self):
        release, _, _ = load()
        self.assertEqual([], check_review_representation(self.PAGE, {release["as_of"]}))

    def test_last_reviewed_jsonld_rejected(self):
        html = self.PAGE.read_text(encoding="utf-8").replace('"dateModified": "2026-11-09",', '"dateModified": "2026-11-09", "lastReviewed": "2026-11-09",')
        self.assertTrue(any("completed scientific review" in e for e in self.check(html)))

    def test_dated_reviewed_claim_rejected(self):
        html = self.PAGE.read_text(encoding="utf-8") + "<p>Reviewed 2026-11-09</p>"
        self.assertTrue(any("completed scientific review" in e for e in self.check(html)))

    def test_peer_review_claim_rejected(self):
        html = self.PAGE.read_text(encoding="utf-8") + "<p>This page was peer-reviewed.</p>"
        self.assertTrue(any("completed scientific review" in e for e in self.check(html)))

    def test_pending_statement_required(self):
        html = self.PAGE.read_text(encoding="utf-8").replace("Scientific review pending", "")
        self.assertTrue(any("Scientific review pending" in e for e in self.check(html)))

    def test_compilation_date_must_match_release(self):
        errors = check_review_representation(self.PAGE, {"2026-12-01"})
        self.assertTrue(any("does not match any release as_of" in e for e in errors), errors)

    def test_validation_wording_alone_is_not_review(self):
        html = self.PAGE.read_text(encoding="utf-8") + "<p>Automated validation passed 2026-11-09.</p>"
        self.assertEqual([], self.check(html))


class InferenceBoundaryTests(unittest.TestCase):
    """Supplier self-descriptions are not platform facts; in-house is not capability-free."""

    def errs(self, sentence):
        return inference_boundary_errors(sentence, "fixture")

    def test_repository_release_and_page_pass(self):
        release, _, _ = load()
        self.assertEqual([], check_inference_boundaries(release, ROOT / "hbm-memory" / "index.html"))

    def test_multi_sourcing_assertion_rejected(self):
        self.assertTrue(self.errs("Rubin is therefore multi-sourced across two HBM4 suppliers."))
        self.assertTrue(self.errs("The platform is therefore designed to accept HBM4 from more than one supplier."))
        self.assertTrue(self.errs("That establishes technical multi-sourcing intent only."))
        self.assertTrue(self.errs("The two suppliers' parts are interchangeable."))

    def test_negated_multi_sourcing_allowed(self):
        self.assertEqual([], self.errs("The statements do not establish that Rubin is actually multi-sourced."))

    def test_qualification_assertion_rejected(self):
        self.assertTrue(self.errs("NVIDIA has qualified Samsung HBM4 for Vera Rubin."))
        self.assertEqual([], self.errs("Which suppliers' parts are qualified for which platforms?"))

    def test_in_house_cannot_remove_manufacturing_dependency(self):
        self.assertTrue(self.errs("Micron's in-house base die eliminates its dependency on advanced manufacturing."))
        self.assertTrue(self.errs("Because it is made in-house, the base die is independent of advanced process capacity."))
        self.assertEqual([], self.errs("In-house manufacture still depends on Micron's own advanced process capability."))

    def test_unscoped_logic_process_base_die_rejected(self):
        self.assertTrue(self.errs("HBM4 moves the base die onto a logic process."))
        self.assertEqual([], self.errs("Samsung states a 4nm logic process for its HBM4 base die."))

    def test_finding_and_candidate_statements_are_checked(self):
        release, _, _ = load()
        release["findings"][0]["statement"] = "HBM4 is multi-sourced on every platform."
        release["candidate_relationships"][0]["statement"] = "NVIDIA has qualified both suppliers."
        errors = check_inference_boundaries(release, ROOT / "hbm-memory" / "index.html")
        self.assertTrue(any("finding" in e for e in errors), errors)
        self.assertTrue(any("candidate" in e for e in errors), errors)

    def test_substitution_finding_is_not_an_inference(self):
        release, _, _ = load()
        f = next(x for x in release["findings"] if x["id"] == "f-an-substitution")
        self.assertEqual("attributed_statement", f["claim_class"])
        self.assertIn("do not establish", f["statement"])


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
