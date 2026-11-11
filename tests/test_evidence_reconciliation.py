"""Regression tests for IDE-009: reconciling public references and pathways with newly retrieved primary evidence."""

from __future__ import annotations

import copy
import json
import re
import sys
import unittest
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import validate_evidence_reconciliations as recon  # noqa: E402
from validate_evidence_maintenance import check_inspections  # noqa: E402
from validate_source_registry import check_public_index  # noqa: E402

TODAY = date(2026, 11, 11)


def state():
    record, registry, register, pathways, inspections, releases = recon.load_all()
    return {"record": record, "registry": registry, "register": register, "pathways": pathways,
            "inspections": inspections, "releases": releases, "pages": recon.default_pages()}


def run(s):
    return recon.check(s["record"], s["registry"], s["register"], s["pathways"], s["inspections"], s["releases"], s["pages"], TODAY)


def rc(s, rid):
    return next(r for r in s["record"]["reconciliations"] if r["id"] == rid)


def issue(s, cid):
    return next(c for c in s["register"]["issues"] if c["id"] == cid)


AMD, RUBIN, NV, EXPORT = ("rc-009-mi300x-infinity-fabric", "rc-009-rubin-memory-bandwidth", "rc-009-nvlink6-per-gpu",
                          "rc-009-hbm-export-control-currency")


class CommittedStateTests(unittest.TestCase):
    def test_record_validates(self):
        self.assertEqual([], run(state()))

    def test_every_register_issue_is_reconciled_once(self):
        s = state()
        self.assertEqual(sorted(c["id"] for c in s["register"]["issues"]),
                         sorted(r["conflict_id"] for r in s["record"]["reconciliations"]))
        applied = {r["id"] for r in s["record"]["reconciliations"] if r["decision"] == "applied"}
        self.assertEqual({AMD, RUBIN, NV, EXPORT}, applied)

    def test_no_issue_is_called_resolved_while_uncertainty_remains(self):
        s = state()
        for r in s["record"]["reconciliations"]:
            self.assertTrue(r["states"]["conflict_remains_open"], r["id"])
            self.assertNotEqual("resolved_with_evidence", issue(s, r["conflict_id"])["state"])

    def test_history_is_appended_not_rewritten(self):
        c = issue(state(), "ec-mi300x-infinity-fabric-scope")
        events = [h["event"] for h in c["history"]]
        self.assertEqual(["registered", "evidence_added", "resolved", "evidence_added", "evidence_added", "reopened"], events)

    def test_historical_releases_untouched(self):
        rel = json.loads((ROOT / "data" / "research" / "interconnect-evidence-release-004.json").read_text(encoding="utf-8"))
        q = next(q for q in next(f for f in rel["findings"] if f["id"] == "i-an-memory-vs-fabric")["quantities"] if q["value"] == "896")
        self.assertEqual(("not_stated", "not_stated"), (q["direction"], q["scope"]))
        self.assertEqual("2026-11-09", rel["as_of"])


class ScientificOutcomeTests(unittest.TestCase):
    def test_amd_direction_stated_scope_not_promoted(self):
        page = (ROOT / "interconnects" / "index.html").read_text(encoding="utf-8")
        self.assertIn("peak aggregate bidirectional", page)
        self.assertIn("no reviewed AMD document states that 896 GB/s is a per-GPU figure", page)
        self.assertNotIn("AMD states that 896 GB/s is a per-GPU", page)
        verdict = next(c for p in state()["pathways"]["pathways"] for c in p.get("comparisons", []) if c["id"] == "cmp-mi300x-p2p-vs-nvlink6")
        self.assertEqual("unsupported", verdict["verdict"])

    def test_unverified_endnote_is_recorded_not_used(self):
        r = rc(state(), AMD)
        self.assertTrue(any("MI350-007" in x["observation"] for x in r["sources_examined_not_supporting"]))
        self.assertFalse(any("MI350-007" in e["locator"] for e in r["new_evidence"]))

    def test_rubin_and_nvlink_keep_both_figures(self):
        s = state()
        self.assertEqual("requires_reassessment", issue(s, "ec-rubin-memory-bandwidth")["state"])
        self.assertEqual("requires_reassessment", issue(s, "ec-nvlink6-per-gpu")["state"])
        self.assertFalse(rc(s, RUBIN)["states"]["interpretation_changed"])
        hbm = (ROOT / "hbm-memory" / "index.html").read_text(encoding="utf-8")
        self.assertIn("22 TB/s", hbm)
        self.assertIn("19.2 TB/s", hbm)

    def test_export_controls_scoped_to_two_sections(self):
        infra = recon.plain((ROOT / "ai-chip-infrastructure" / "index.html").read_text(encoding="utf-8"))
        self.assertIn("15 CFR 742.6", infra)
        self.assertIn("not the full set of rules that may apply", recon.norm(infra))
        self.assertIn("no transaction-level conclusion", recon.norm(infra))
        c8 = next(st for p in state()["pathways"]["pathways"] for st in p["steps"] if st["id"] == "c8-access")
        self.assertIn("only two current sections", c8["limitations"][0])


class NegativeFixtureTests(unittest.TestCase):
    """Each fixture reintroduces a defect the reconciliation exists to prevent."""

    def expect(self, mutate, fragment):
        s = state()
        mutate(s)
        errs = run(s)
        self.assertTrue(any(fragment in e for e in errs), (fragment, errs[:4]))

    def test_1_page_still_claims_amd_scope_unknown(self):
        def mutate(s):
            s["pages"]["/interconnects/"] = s["pages"]["/interconnects/"].replace(
                "</main>", "<p>AMD gives 896 GB/s but its scope and direction are not stated.</p></main>")
        self.expect(mutate, "still treats the 896 GB/s scope or direction as unknown")

    def test_2_diagram_keeps_old_scope_label(self):
        def mutate(s):
            s["pages"]["/interconnects/"] = s["pages"]["/interconnects/"].replace("P2P RING (8 GPUs)", "7 GPU LINKS (TOTAL)")
        self.expect(mutate, "still carries the superseded text '7 GPU LINKS (TOTAL)'")

    def test_2b_svg_title_keeps_old_alternative_text(self):
        def mutate(s):
            s["pages"]["/interconnects/"] = s["pages"]["/interconnects/"].replace(
                "per-GPU or ring-level scope not stated)", "device-level scope and direction unconfirmed)")
        self.expect(mutate, "superseded text")

    def test_3_nvlink_difference_claimed_explained(self):
        def mutate(s):
            s["pages"]["/interconnects/"] = s["pages"]["/interconnects/"].replace(
                "</main>", "<p>The 3.6 TB/s and 3.0 TB/s figures differ because the later one counts one direction.</p></main>")
        self.expect(mutate, "difference is explained without source support")

    def test_4_regulatory_review_claimed_complete(self):
        def mutate(s):
            s["pages"]["/ai-chip-infrastructure/"] = s["pages"]["/ai-chip-infrastructure/"].replace(
                "</main>", "<p>With 15 CFR 742.6 reviewed, the page reflects a complete review of current export-control law.</p></main>")
        self.expect(mutate, "presents a limited rule-text review as complete")

    def test_5_new_source_missing_from_inspection_and_public_index(self):
        s = state()
        log = copy.deepcopy(s["inspections"])
        log["records"] = [r for r in log["records"] if r["source_id"] != "amd-instinct-mi300x-platform-data-sheet-2023"]
        self.assertTrue(any("has no record" in e for e in check_inspections(log, s["registry"], TODAY)))
        records = json.loads((ROOT / "data" / "source-registry.json").read_text(encoding="utf-8"))["source_records"]
        page = ROOT / "sources" / "index.html"
        fixture = ROOT / "build" / "sources-fixture.html"
        fixture.parent.mkdir(exist_ok=True)
        try:
            fixture.write_text(page.read_text(encoding="utf-8").replace("<li>amd-cdna4-white-paper-2025</li>", ""), encoding="utf-8")
            self.assertTrue(any("amd-cdna4-white-paper-2025" in e for e in check_public_index(fixture, records)))
        finally:
            fixture.unlink()
            fixture.parent.rmdir()

    def test_6_applied_reconciliation_without_page_change(self):
        def mutate(s):
            s["pages"]["/ai-chip-infrastructure/"] = s["pages"]["/ai-chip-infrastructure/"].replace(
                "Only the 2024 announcement and two current sections reviewed", "Only a 2024 announcement reviewed")
        self.expect(mutate, "does not carry the reconciled text")

    def test_pathway_value_must_match_record(self):
        def mutate(s):
            c = next(c for p in s["pathways"]["pathways"] for c in p.get("comparisons", []) if c["id"] == "cmp-mi300x-p2p-vs-nvlink6")
            c["reason"] = "Old reason."
        self.expect(mutate, "does not carry the reconciled value")

    def test_open_state_must_match_register(self):
        self.expect(lambda s: rc(s, AMD)["states"].update(conflict_remains_open=False), "disagrees with the register")

    def test_applied_needs_changes_and_evidence(self):
        self.expect(lambda s: rc(s, EXPORT).update(publication_changes=[], pathway_changes=[]), "must change the public pages")
        def no_evidence(s):
            r = rc(s, EXPORT)
            r.update(new_evidence=[], source_ids=[])
            r["states"]["evidence_reviewed"] = False
        self.expect(no_evidence, "must rest on reviewed evidence")

    def test_unretrieved_or_unregistered_evidence_rejected(self):
        def unretrieved(s):
            rc(s, AMD)["new_evidence"].append({"source_id": "tsmc-2025-annual-report", "locator": "x", "observation": "y"})
            rc(s, AMD)["source_ids"].append("tsmc-2025-annual-report")
        self.expect(unretrieved, "was not retrieved by an inspection")

        def unregistered(s):
            rc(s, AMD)["new_evidence"].append({"source_id": "amd-cdna4-endnote-snippet", "locator": "x", "observation": "y"})
            rc(s, AMD)["source_ids"].append("amd-cdna4-endnote-snippet")
        self.expect(unregistered, "is not registered")

    def test_unknown_conflict_and_missing_coverage(self):
        self.expect(lambda s: rc(s, AMD).update(conflict_id="ec-invented"), "is not in the register")
        self.expect(lambda s: s["record"]["reconciliations"].pop(), "has no reconciliation entry")

    def test_no_review_or_approval_claims(self):
        self.expect(lambda s: rc(s, AMD).update(reviewer="Editor"), "is not allowed")
        self.expect(lambda s: rc(s, AMD).update(reason="Scientifically reviewed and approved by the board."), "review-completion language")
        self.expect(lambda s: s["record"].update(scientific_review="complete"), "scientific_review 'pending'")

    def test_unnecessary_cannot_change_text(self):
        def mutate(s):
            r = next(r for r in s["record"]["reconciliations"] if r["decision"] == "unnecessary")
            r["publication_changes"] = [{"route": "/hbm-memory/", "old_text": None, "new_text": "x"}]
        self.expect(mutate, "only an applied reconciliation may change public text")


class SynchronizationTests(unittest.TestCase):
    def test_generated_pages_in_sync(self):
        sys.path.insert(0, str(ROOT / "scripts"))
        import render_evidence_maintenance as rs
        import render_reference_pathways as rp
        self.assertTrue(rs.in_sync())
        current = (ROOT / "sovereignty-stack" / "index.html").read_text(encoding="utf-8")
        self.assertEqual(current, rp.apply(current, rp.render(*rp.load())))
        sources = (ROOT / "sources" / "index.html").read_text(encoding="utf-8")
        for rid in (AMD, RUBIN, NV, EXPORT):
            self.assertIn(f'id="{rid}"', sources)
            self.assertIn(f'href="/sources/#{rid}"', current)

    def test_impact_index_lists_reconciliations(self):
        idx = json.loads((ROOT / "data" / "evidence-impact-index.json").read_text(encoding="utf-8"))
        e = next(x for x in idx["sources"] if x["source_id"] == "amd-instinct-mi300x-platform-data-sheet-2023")
        self.assertEqual([AMD], e["reconciliations"])
        self.assertIn("ec-mi300x-infinity-fabric-scope", e["conflicts"])

    def test_figure_alt_text_matches_corrected_label(self):
        page = (ROOT / "interconnects" / "index.html").read_text(encoding="utf-8")
        svg = re.search(r"<svg.*?</svg>", page, re.S).group(0)
        self.assertNotIn("calculated", svg)
        self.assertNotIn("unconfirmed", svg)
        self.assertIn("P2P RING (8 GPUs)", svg)


if __name__ == "__main__":
    unittest.main()
