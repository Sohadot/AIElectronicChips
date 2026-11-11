"""Regression tests for IDE-013: correcting cmp-scale-up-vs-scale-out in reference pathway B."""

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
import render_evidence_maintenance as maintenance  # noqa: E402
import render_reference_pathways as pathways_render  # noqa: E402
import validate_evidence_reconciliations as recon  # noqa: E402

CMP = "cmp-scale-up-vs-scale-out"
RC = "rc-013-scale-up-vs-scale-out"
PATHWAY_B = "pathway-memory-bandwidth-to-data-movement"
# Fingerprints of what IDE-013 must not change, taken from main before the correction.
UNCHANGED = {
    "pathway-hbm-to-advanced-packaging": "f81c4705b6d4db7eb43899395ccdae6c2d4610fda068dd6de461235960065b3f",
    "pathway-rack-to-deployable-compute": "cc45306f1a481950f5d3ccd675a75fe1b59afb53c4c54202407220be2eddbeb6",
}
B_WITHOUT_COMPARISONS = "9ed1091130f9c2947dab3bda809b54eaf04519cdadd23e085991fcb96a634045"
B_OTHER_COMPARISONS = "0af3ef74cf74a9ed977cb99a4916192a17e89b21a14af162899c91f7935e24aa"
IDE009_RECORD = "a26600fcf6b3ac7ce9a6f767788025cfef4dbd18c5b81c74c6ebb6b10c82383b"
OLD_REASON = ("Comparable only after converting bits to bytes; the ratio is about 9x or 18x depending on the unstated direction of the "
              "1.6 Tb/s figure, and it uses the 3.6 TB/s NVLink 6 figure, which NVIDIA also publishes as 3 TB/s.")
EXPECTED_VERDICTS = {"cmp-stack-vs-stack": "valid", "cmp-rubin-22-vs-19": "conditional", "cmp-mi300x-vs-rubin-memory": "conditional",
                     "cmp-mi300x-p2p-vs-nvlink6": "unsupported", "cmp-memory-vs-scale-up": "unsupported", "cmp-rack-vs-gpu": "unsupported",
                     CMP: "unsupported", "cmp-cxl-vs-pcie6": "conditional"}


def j(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def fingerprint(obj) -> str:
    return hashlib.sha256(json.dumps(obj, sort_keys=True, ensure_ascii=False).encode()).hexdigest()


def model():
    return j(ROOT / "data" / "reference-pathways.json")


def pathway_b(m):
    return next(p for p in m["pathways"] if p["id"] == PATHWAY_B)


def comparison(m):
    return next(c for c in pathway_b(m)["comparisons"] if c["id"] == CMP)


def later():
    return j(ROOT / "data" / "evidence-reconciliations-013.json")


def dossier():
    return j(ROOT / "data" / "research" / "institutional" / "accelerator-bandwidth-comparability-dossier-012.json")


class PublicCorrectionTests(unittest.TestCase):
    def test_verdict_uses_existing_vocabulary_and_is_no_longer_conditional(self):
        m = model()
        self.assertEqual(set(m["comparison_verdicts"]), {"valid", "conditional", "unsupported"})
        c = comparison(m)
        self.assertEqual(c["verdict"], "unsupported")
        self.assertNotEqual(c["reason"], OLD_REASON)
        self.assertNotIn("Comparable only after converting bits to bytes", c["reason"])
        self.assertEqual(c["reconciliations"], ["rc-009-nvlink6-per-gpu", RC])

    def test_reason_separates_unit_conversion_from_metric_equivalence(self):
        reason = comparison(model())["reason"]
        for phrase in ("Not comparable as one metric", "does not make them the same quantity", "As arithmetic on advertised figures only",
                       "says nothing about delivered throughput", "stated bidirectional", "no stated direction",
                       "NVIDIA also publishes NVLink 6 as 3 TB/s per GPU"):
            self.assertIn(phrase, reason)
        self.assertIsNone(re.search(r"(?i)\b(?:explain(?:s|ed)?|due to|because)\b", reason), "the 3.6 / 3 TB/s difference stays unexplained")

    def test_generated_pages_match_and_carry_no_old_wording(self):
        self.assertTrue(pathways_render.PAGE.read_text(encoding="utf-8")
                        == pathways_render.apply(pathways_render.PAGE.read_text(encoding="utf-8"), pathways_render.render(*pathways_render.load())))
        self.assertTrue(maintenance.in_sync())
        stack = (ROOT / "sovereignty-stack" / "index.html").read_text(encoding="utf-8")
        row = re.search(rf'<tr id="{CMP}">.*?</tr>', stack, re.S).group(0)
        self.assertIn("Unsupported", row)
        self.assertNotIn("Comparable only after converting", row)
        self.assertIn(f'href="/sources/#{RC}"', row)
        self.assertIn(f'id="{RC}"', (ROOT / "sources" / "index.html").read_text(encoding="utf-8"))

    def test_interconnects_passages_corrected(self):
        page = recon.norm(recon.plain((ROOT / "interconnects" / "index.html").read_text(encoding="utf-8")))
        for pc in later()["reconciliations"][0]["publication_changes"]:
            self.assertIn(recon.norm(pc["new_text"]), page)
            self.assertNotIn(recon.norm(pc["old_text"]), page)
        self.assertNotIn("a ninth to an eighteenth of per-GPU scale-up bandwidth", page)

    def test_all_eight_pathway_b_comparisons_and_other_pathways_unchanged(self):
        m = model()
        b = pathway_b(m)
        self.assertEqual({c["id"]: c["verdict"] for c in b["comparisons"]}, EXPECTED_VERDICTS)
        self.assertEqual(fingerprint([c for c in b["comparisons"] if c["id"] != CMP]), B_OTHER_COMPARISONS)
        self.assertEqual(fingerprint({k: v for k, v in b.items() if k != "comparisons"}), B_WITHOUT_COMPARISONS)
        for p in m["pathways"]:
            if p["id"] in UNCHANGED:
                self.assertEqual(fingerprint(p), UNCHANGED[p["id"]], p["id"])


class HistoryTests(unittest.TestCase):
    def test_ide009_record_byte_identical_and_still_names_its_change(self):
        raw = (ROOT / "data" / "evidence-reconciliations-009.json").read_bytes()
        self.assertEqual(hashlib.sha256(raw).hexdigest(), IDE009_RECORD)
        rc = next(r for r in json.loads(raw)["reconciliations"] if r["id"] == "rc-009-nvlink6-per-gpu")
        change = next(p for p in rc["pathway_changes"] if p["target"] == CMP)
        self.assertEqual(change["new"], OLD_REASON)

    def test_ide013_record_preserves_provenance(self):
        rc = later()["reconciliations"][0]
        self.assertEqual((rc["id"], rc["comparison_id"], rc["previous_verdict"], rc["corrected_verdict"]), (RC, CMP, "conditional", "unsupported"))
        self.assertEqual(rc["supersedes"], ["rc-009-nvlink6-per-gpu"])
        reason = next(p for p in rc["pathway_changes"] if p["field"] == "reason")
        self.assertEqual(reason["old"], OLD_REASON)
        self.assertEqual(reason["new"], comparison(model())["reason"])
        self.assertTrue(rc["why_previous_insufficient"] and rc["original_interpretation"] and rc["reconciled_interpretation"])
        self.assertEqual(rc["basis"]["dossier_comparison_id"], "cp-scale-up-vs-scale-out")
        self.assertEqual(rc["reconciled_at"], "2026-11-11")
        self.assertIn("ADR-021", (ROOT / "DECISION_LOG.md").read_text(encoding="utf-8"))

    def test_ide012_divergence_traceable_and_reconciled(self):
        c = next(x for x in dossier()["comparisons"] if x["id"] == "cp-scale-up-vs-scale-out")
        self.assertEqual(c["classification"], "not_comparable")
        self.assertEqual((c["pathway_divergence"]["status"], c["pathway_divergence"]["reconciled_by"], c["pathway_divergence"]["pathway_verdict"]),
                         ("reconciled", RC, "conditional"))

    def test_nothing_promoted_or_reviewed(self):
        self.assertEqual(later()["scientific_review"], "pending")
        self.assertEqual(j(ROOT / "data" / "dependency-atlas.json").get("relationships", []), [])
        d = dossier()
        self.assertEqual((d["status"], d["review_status"], d["scientific_review"]), ("research_candidate", "not_reviewed", "pending"))


class ChainOfCustodyTests(unittest.TestCase):
    """The IDE-009 pin may change only through an exact, recorded chain."""

    def setUp(self):
        self.args = recon.load_all()

    def run_check(self, later_records, pathways=None):
        record, registry, register, pw, inspections, releases = self.args
        return recon.check(record, registry, register, pathways or pw, inspections, releases, later=later_records)

    def test_current_state_valid(self):
        self.assertEqual(self.run_check([later()]), [])
        record, registry, _, pw, _, releases = self.args
        self.assertEqual(recon.check_later(later(), record, registry, pw, releases, recon.default_pages(), dossier()), [])

    def test_without_the_later_record_the_ide009_pin_fails(self):
        errs = self.run_check([])
        self.assertTrue(any("does not carry the reconciled value for cmp-scale-up-vs-scale-out.reason" in e for e in errs), errs)
        self.assertTrue(any(f"names unknown reconciliation {RC}" in e for e in errs), errs)

    def test_chain_must_start_from_the_ide009_value(self):
        rec = later(); next(p for p in rec["reconciliations"][0]["pathway_changes"] if p["field"] == "reason")["old"] = "Some other text."
        self.assertTrue(any("does not start from the value this reconciliation set" in e for e in self.run_check([rec])))
        record, registry, _, pw, _, releases = self.args
        self.assertTrue(any("old value must be the one the superseded reconciliation set" in e
                            for e in recon.check_later(rec, record, registry, pw, releases, recon.default_pages(), dossier())))

    def test_model_must_carry_the_later_value(self):
        pw = copy.deepcopy(self.args[3]); comparison(pw)["reason"] = OLD_REASON
        self.assertTrue(any("does not carry the reconciled value" in e for e in self.run_check([later()], pw)))

    def test_later_record_rules(self):
        record, registry, _, pw, _, releases = self.args
        pages = recon.default_pages()

        def errs(rec, p=pw, d=None):
            return recon.check_later(rec, record, registry, p, releases, pages, d or dossier())
        rec = later(); rec["scientific_review"] = "complete"
        self.assertTrue(any("scientific_review 'pending'" in e for e in errs(rec)))
        rec = later(); rec["reconciliations"][0]["corrected_verdict"] = "valid"
        self.assertTrue(any("must carry the corrected verdict" in e for e in errs(rec)))
        rec = later(); rec["reconciliations"][0]["publication_changes"][1]["new_text"] = "Text that is not on the page"
        self.assertTrue(any("must carry the new text" in e for e in errs(rec)))
        rec = later(); rec["reconciliations"][0]["supersedes"] = ["rc-009-invented"]
        self.assertTrue(any("superseded reconciliation rc-009-invented does not exist" in e for e in errs(rec)))
        p2 = copy.deepcopy(pw); comparison(p2)["reconciliations"] = [RC]
        self.assertTrue(any("must keep naming the superseded rc-009-nvlink6-per-gpu" in e for e in errs(later(), p2)))
        d = dossier(); next(x for x in d["comparisons"] if x["id"] == "cp-scale-up-vs-scale-out")["classification"] = "conditionally_comparable"
        self.assertTrue(any("must agree with the IDE-012 classification" in e for e in errs(later(), pw, d)))
        d = dossier(); next(x for x in d["comparisons"] if x["id"] == "cp-scale-up-vs-scale-out")["pathway_divergence"] = None
        self.assertTrue(any("divergence must stay recorded" in e for e in errs(later(), pw, d)))
        rec = later(); rec["reconciliations"][0]["approved_by"] = "someone"
        self.assertTrue(any("fields mismatch" in e for e in errs(rec)))


if __name__ == "__main__":
    unittest.main()
