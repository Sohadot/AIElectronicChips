"""Regression tests for IDE-011: the HBM4 integration and qualification evidence dossier."""

from __future__ import annotations

import copy
import functools
import json
import re
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import render_hbm4_dossier as render  # noqa: E402
import validate_hbm4_dossier as v  # noqa: E402

RELEASE = ROOT / "data" / "research" / "hbm4-evidence-release-001.json"


@functools.lru_cache(maxsize=1)
def _ctx():
    return v.load_context()


def ctx():
    return copy.deepcopy(_ctx())


def dossier():
    return json.loads(v.DOSSIER.read_text(encoding="utf-8"))


def row(d, fid):
    return next(r for r in d["evidence_matrix"] if r["finding_id"] == fid)


def assessment(d, cid):
    return next(a for a in d["candidate_assessments"] if a["candidate_id"] == cid)


class DossierTests(unittest.TestCase):
    def test_validates_and_document_in_sync(self):
        self.assertEqual(v.check_all(), [])
        self.assertTrue(render.in_sync())

    def test_covers_every_finding_and_candidate_once(self):
        d, release = dossier(), json.loads(RELEASE.read_text(encoding="utf-8"))
        self.assertEqual(sorted(r["finding_id"] for r in d["evidence_matrix"]), sorted(f["id"] for f in release["findings"]))
        self.assertEqual(sorted(a["candidate_id"] for a in d["candidate_assessments"]),
                         sorted(c["id"] for c in release["candidate_relationships"]))

    def test_recommendations(self):
        d = dossier()
        got = {a["candidate_id"]: (a["release_recommendation"], a["dossier_recommendation"]) for a in d["candidate_assessments"]}
        self.assertEqual(got, {
            "rel-hbm4-requires-logic-base-die": ("ACCEPT", "ACCEPT"),
            "rel-hbm-base-die-requires-logic-foundry": ("REJECT", "REJECT"),
            "rel-hbm4-integrates-with-cowos": ("DEFER", "DEFER"),
            "rel-rubin-gpu-requires-hbm4": ("ACCEPT", "ACCEPT"),
            "rel-hbm-base-die-requires-logic-cmos-fabrication": ("ACCEPT", "REVISE")})

    def test_nothing_promoted_and_no_review_recorded(self):
        d = dossier()
        self.assertEqual((d["status"], d["review_status"], d["scientific_review"], d["review_owner"]),
                         ("research_candidate", "not_reviewed", "pending", "unassigned"))
        atlas = json.loads((ROOT / "data" / "dependency-atlas.json").read_text(encoding="utf-8"))
        self.assertEqual(atlas.get("relationships", []), [])
        release = json.loads(RELEASE.read_text(encoding="utf-8"))
        for c in release["candidate_relationships"]:
            self.assertEqual((c["review_status"], c["reviewed_at"], c["review_owner"]), ("awaiting_human_review", None, "unassigned"))

    def test_ide011_inspection_run_recorded(self):
        log = json.loads((ROOT / "data" / "source-inspections.json").read_text(encoding="utf-8"))
        run = [r for r in log["records"] if r["run_id"] == "ide-011-2026-11-11"]
        self.assertEqual(len(run), 24)
        blocked = sorted(r["source_id"] for r in run if "source_inaccessible" in r["states"])
        self.assertEqual(blocked, ["micron-fy2026-form-10-k", "micron-q3-fy2026-results-2026", "skhynix-424b4-prospectus-2026"])
        for r in run:
            if r["passage_check"]:
                self.assertEqual(r["passage_check"]["not_found"], [], r["source_id"])
        tsmc = next(r for r in run if r["source_id"] == "tsmc-2025-na-technology-symposium")
        self.assertIn("source_retrieved", tsmc["states"])
        self.assertTrue(any("refused" in n for n in tsmc["notes"]))

    def test_document_quotes_passages_and_states_limits(self):
        text = render.OUT.read_text(encoding="utf-8")
        self.assertIn('"N12 and N3 logic base die for HBM4"', text)
        self.assertIn("not retrievable on 2026-11-11; passage not rechecked", text)
        for heading in ("Research question and scope", "Dependency architecture", "Evidence matrix", "Provenance and freshness",
                        "Conflicting disclosures", "Candidate Atlas relationships", "Critical unknowns", "Documentary requirements",
                        "Limitations", "Prohibited inferences", "Review and acceptance requirements", "Lineage"):
            self.assertRegex(text, rf"(?m)^## \d+\. {re.escape(heading)}$")
        self.assertNotRegex(text, r"(?i)\b(?:score|ranking|certified|approved by)\b")


class NegativeTests(unittest.TestCase):
    def assertFlags(self, d, pattern, c=None):
        errs = v.check(d, c or ctx())
        self.assertTrue(any(re.search(pattern, e) for e in errs), f"expected /{pattern}/ in {errs}")

    def test_missing_dossier_fails_closed(self):
        original = v.DOSSIER
        try:
            v.DOSSIER = ROOT / "does-not-exist.json"
            self.assertIn("required dossier missing", v.check_all()[0])
        finally:
            v.DOSSIER = original

    def test_dropped_or_duplicated_finding(self):
        d = dossier(); d["evidence_matrix"].pop()
        self.assertFlags(d, r"cover every finding once")
        d = dossier(); d["evidence_matrix"].append(copy.deepcopy(d["evidence_matrix"][0]))
        self.assertFlags(d, r"duplicated \['f-std-interface'\]")

    def test_unknown_basis(self):
        d = dossier(); assessment(d, "rel-hbm4-integrates-with-cowos")["reasons"][0]["basis"].append("f-invented-finding")
        self.assertFlags(d, r"basis f-invented-finding does not resolve")
        d = dossier(); assessment(d, "rel-rubin-gpu-requires-hbm4")["reasons"][0]["basis"].append("inspection:ide-099-2026-11-11:nvidia-rubin-ces-2026")
        self.assertFlags(d, r"does not resolve")

    def test_review_requirement_follows_evidence(self):
        d = dossier(); row(d, "f-an-bandwidth")["review_requirement"] = "documentary_verification"
        self.assertFlags(d, r"bounded analysis needs technical review")
        d = dossier(); row(d, "f-std-interface")["review_requirement"] = "documentary_verification"
        self.assertFlags(d, r"normative-text review")

    def test_unretrieved_source_must_be_disclosed(self):
        d = dossier(); row(d, "f-mu-base-die")["interpretation"] = "Micron states its base die is made in-house with advanced CMOS."
        self.assertFlags(d, r"could not retrieve; the interpretation must say so")

    def test_release_recommendation_quoted_exactly(self):
        d = dossier(); assessment(d, "rel-hbm4-integrates-with-cowos")["release_recommendation"] = "ACCEPT"
        self.assertFlags(d, r"must quote the release's decision \(DEFER\)")

    def test_revision_rules(self):
        d = dossier(); assessment(d, "rel-hbm-base-die-requires-logic-cmos-fabrication")["proposed_revision"] = None
        self.assertFlags(d, r"proposed revision is given exactly when")
        d = dossier(); a = assessment(d, "rel-hbm4-integrates-with-cowos"); a["dossier_recommendation"] = "PROMOTE"
        self.assertFlags(d, r"recommendation must be one of")

    def test_accept_on_unretrieved_source_needs_precondition(self):
        d = dossier(); assessment(d, "rel-hbm4-requires-logic-base-die")["preconditions_for_review"] = []
        self.assertFlags(d, r"unretrieved source must state what the reviewer has to read first")

    def test_no_fabricated_review(self):
        d = dossier(); d["review_owner"] = "Dr. Example Reviewer"
        self.assertFlags(d, r"review owner unassigned")
        d = dossier(); d["scientific_review"] = "complete"
        self.assertFlags(d, r"scientific review pending")
        d = dossier(); assessment(d, "rel-rubin-gpu-requires-hbm4")["reviewed_at"] = "2026-11-11"
        self.assertFlags(d, r"fields mismatch")
        d = dossier(); d["candidate_assessments"][0]["reasons"][0]["approved_by"] = "someone"
        self.assertFlags(d, r"'approved_by' is not allowed")

    def test_verdict_language(self):
        d = dossier(); row(d, "f-nv-rubin")["interpretation"] = "NVIDIA's figures are certified and the integration is fully verified by this dossier."
        self.assertFlags(d, r"review-completion language")

    def test_promotion_blocked(self):
        c = ctx(); c["atlas"]["relationships"] = [{"id": "rel-rubin-gpu-requires-hbm4"}]
        self.assertFlags(dossier(), r"must not promote candidates", c)

    def test_stage_rules(self):
        d = dossier(); next(s for s in d["dependency_architecture"] if s["id"] == "st-known-good-stack")["evidence_level"] = "supplier_statements"
        self.assertFlags(d, r"'no_public_evidence' must be used exactly when")
        d = dossier()
        for s in d["dependency_architecture"]:
            s["documentary_requirement_ids"] = [r for r in s["documentary_requirement_ids"] if r != "ra-08-known-good-stack"] or ["ra-01-interface-revision"]
        self.assertFlags(d, r"not mapped to a stage: \['ra-08-known-good-stack'\]")
        d = dossier(); d["dependency_architecture"][2]["candidate_ids"].pop()
        self.assertFlags(d, r"placed in exactly one stage")

    def test_document_out_of_sync(self):
        original = render.OUT
        try:
            tmp = ROOT / "build" / "dossier-sync-test.md"
            tmp.parent.mkdir(exist_ok=True)
            tmp.write_text(original.read_text(encoding="utf-8").replace("REVISE", "ACCEPT"), encoding="utf-8")
            render.OUT = tmp
            self.assertFalse(render.in_sync())
            self.assertTrue(any("out of date" in e for e in v.check_all()))
        finally:
            render.OUT = original
            tmp.unlink(missing_ok=True)


if __name__ == "__main__":
    unittest.main()
