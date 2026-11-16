"""Metadata correction and separately recorded source-identity review (2026-11-16).

`asml-2024-annual-reports` now points to the report itself rather than its publication notice, and
`ucie-2-specification-release-2024` is typed as the announcement it is rather than as the normative standard.
The first run retains pending review; ADR-024's later identity decision is active, never a scientific claim approval.
"""

from __future__ import annotations

import copy
import hashlib
import json
import re
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import render_source_navigator as navigator  # noqa: E402
import validate_source_registry as registry_validator  # noqa: E402

ASML, UCIE = "asml-2024-annual-reports", "ucie-2-specification-release-2024"
ASML_PDF = "https://ourbrand.asml.com/m/79d325b168e0fd7e/original/2024-Annual-Report-based-on-US-GAAP.pdf"
UCIE_PDF = "https://www.uciexpress.org/_files/ugd/0c1418_c9fb71cbbd4644e3b73b123216fa2e52.pdf"
# The inspection log as it stood before this change: these runs and records must survive unchanged.
PRIOR_RUNS = "7c2e70d0146a980217bf7741753495ebb003201090544cb214911b165860c60a"
PRIOR_RECORDS = "95c563a81943a20aa1105f812295b3746e4b9637c06fa3dda90c118b24c55a3b"
PRIOR_COUNT = 120


def load(rel):
    return json.loads((ROOT / rel).read_text(encoding="utf-8"))


def record(sid):
    return next(r for r in load("data/source-registry.json")["source_records"] if r["id"] == sid)


def digest(obj):
    return hashlib.sha256(json.dumps(obj, sort_keys=True, ensure_ascii=False).encode()).hexdigest()


class CorrectedMetadataTests(unittest.TestCase):
    def test_asml_points_to_the_report(self):
        r = record(ASML)
        self.assertEqual((r["title"], r["canonical_url"], r["source_type"], r["publisher"], r["publication_date"], r["status"]),
                         ("2024 Annual Report based on US GAAP", ASML_PDF, "annual_report", "ASML Holding N.V.", "2025-03-05", "active"))
        joined = " ".join(r["use_limitations"])
        self.assertIn("statutory EU-IFRS report and Form 20-F were not cross-verified", joined)
        self.assertIn("not independently verified", joined)
        self.assertIn("current production capacity", joined)

    def test_ucie_typed_as_announcement(self):
        r = record(UCIE)
        self.assertEqual((r["source_type"], r["canonical_url"], r["publication_date"], r["status"]),
                         ("official_technical_disclosure", UCIE_PDF, "2024-08-06", "active"))
        self.assertEqual(r["geographic_scope"], "Industry consortium announcement; no country-specific deployment is established")
        self.assertIn("This two-page press release is not the normative UCIe 2.0 specification", r["use_limitations"])
        self.assertTrue(any("prohibit submission to AI systems" in v for v in r["use_limitations"]))

    def test_announcement_cannot_be_typed_as_a_standard(self):
        bad = copy.deepcopy(record(UCIE))
        bad["source_type"] = "technical_standard"
        self.assertIn("cannot be technical_standard", registry_validator.announcement_typed_as_standard(bad))
        self.assertIsNone(registry_validator.announcement_typed_as_standard(record(UCIE)))
        for r in load("data/source-registry.json")["source_records"]:
            self.assertIsNone(registry_validator.announcement_typed_as_standard(r), r["id"])
        self.assertEqual([r["id"] for r in load("data/source-registry.json")["source_records"] if r["source_type"] == "technical_standard"],
                         ["uec-specification-1-1-2026"])

    def test_both_identity_reviewed_without_hidden_pending_markers(self):
        self.assertEqual([r["id"] for r in load("data/source-registry.json")["source_records"] if r["status"] == "pending_review"], [])
        sources = (ROOT / "sources" / "index.html").read_text(encoding="utf-8")
        for sid in (ASML, UCIE):
            self.assertNotIn(f'<li class="pending">{sid}', sources)
            item = re.search(rf'<li class="nav-source" id="nav-{sid}".*?\n</li>', sources, re.S).group(0)
            self.assertIn('data-status="active"', item)
            self.assertNotIn("nav-pending", item)
        for route, sid in (("design-fabrication-packaging", UCIE), ("design-fabrication-packaging", ASML), ("interconnects", UCIE),
                           ("methodology", UCIE), ("export-control-layer", ASML)):
            text = re.sub(r"<[^>]+>", "", (ROOT / route / "index.html").read_text(encoding="utf-8"))
            self.assertIn(sid, text, route)
            self.assertNotRegex(text, rf"{sid}\s*[·,]\s*pending_review", route)


class ProvenanceTests(unittest.TestCase):
    def test_earlier_inspections_are_unchanged(self):
        log = load("data/source-inspections.json")
        self.assertEqual(digest(log["records"][:PRIOR_COUNT]), PRIOR_RECORDS)
        self.assertEqual(digest(log["runs"][:-2]), PRIOR_RUNS)
        asml_old = next(r for r in log["records"] if r["source_id"] == ASML and r["run_id"] == "ide-008-2026-11-10")
        self.assertEqual(asml_old["retrievals"][0]["http_status"], 403)
        self.assertIn("source_inaccessible", asml_old["states"])

    def test_new_run_records_what_was_retrieved(self):
        log = load("data/source-inspections.json")
        run = log["runs"][-2]
        self.assertEqual((run["run_id"], run["inspected_at"], run["tool"]), ("pending-sources-2026-11-16", "2026-11-16", "scripts/inspect_sources.py"))
        new = {r["source_id"]: r for r in log["records"] if r["run_id"] == run["run_id"]}
        self.assertEqual(set(new), {ASML, UCIE})
        a, u = new[ASML], new[UCIE]
        self.assertEqual(a["retrievals"][0]["url"], ASML_PDF)
        self.assertEqual((a["retrievals"][0]["http_status"], a["retrievals"][0]["bytes"]), (200, 32408363))
        self.assertEqual(a["retrievals"][0]["sha256"], "24570fe735f00c8c8b3305568c1b343be9051626ca04a465e8f505d2b97726a8")
        self.assertEqual(u["retrievals"][0]["sha256"], "dacaaa4158b6942ab61cea26691e6dd8fe8b3c39dce42428ce0adbc8f4d99a31")
        self.assertEqual((u["passage_check"]["found"], u["passage_check"]["quoted_passages"]), (6, 6))
        for r in (a, u):
            self.assertIn("review_required", r["states"])  # this historical run preceded the separate decision
            self.assertIn("Keep pending_review", r["next_action"])
        later = log["runs"][-1]
        self.assertEqual(later["run_id"], "ide-018-2026-11-16")
        reviewed = [r for r in log["records"] if r["run_id"] == later["run_id"]]
        self.assertEqual({r["source_id"] for r in reviewed}, {ASML, UCIE})
        self.assertTrue(all("review_required" not in r["states"] for r in reviewed))


class PublicRepresentationTests(unittest.TestCase):
    def test_navigator_and_impact_index_follow_the_registry(self):
        self.assertTrue(navigator.in_sync())
        page = (ROOT / "sources" / "index.html").read_text(encoding="utf-8")
        asml = re.search(rf'<li class="nav-source" id="nav-{ASML}".*?\n</li>', page, re.S).group(0)
        self.assertIn(f'href="{ASML_PDF}">2024 Annual Report based on US GAAP</a>', asml)
        self.assertNotIn("asml-publishes-2024-annual-reports", asml)
        ucie = re.search(rf'<li class="nav-source" id="nav-{UCIE}".*?\n</li>', page, re.S).group(0)
        self.assertIn('data-type="official_technical_disclosure"', ucie)
        impact = {s["source_id"]: s for s in load("data/evidence-impact-index.json")["sources"]}
        self.assertTrue(impact[UCIE]["freshness_basis"].startswith("Product or technical disclosure"))
        self.assertEqual(impact[ASML]["latest_inspection"]["inspected_at"], "2026-11-16")

    def test_no_new_public_file(self):
        allow = [l for l in (ROOT / ".github" / "pages-allowlist.txt").read_text(encoding="utf-8").splitlines() if l and not l.startswith("#")]
        self.assertEqual(len(allow), 50)
        self.assertFalse([a for a in allow if a.startswith(("data/research", "scripts/", "tests/")) or a.endswith(".md")])


if __name__ == "__main__":
    unittest.main()
