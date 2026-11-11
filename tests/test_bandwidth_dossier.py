"""Regression tests for IDE-012: the accelerator bandwidth comparability dossier and its review brief."""

from __future__ import annotations

import copy
import functools
import json
import os
import re
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import render_bandwidth_dossier as render  # noqa: E402
import validate_bandwidth_dossier as v  # noqa: E402


@functools.lru_cache(maxsize=1)
def _ctx():
    return v.load_context()


def ctx():
    return copy.deepcopy(_ctx())


def dossier():
    return json.loads(v.DOSSIER.read_text(encoding="utf-8"))


def item(d, key, iid):
    return next(x for x in d[key] if x["id"] == iid)


class DossierTests(unittest.TestCase):
    def test_validates_and_documents_in_sync(self):
        self.assertEqual(v.check_all(), [])
        self.assertEqual(render.out_of_sync(), [])

    def test_rendering_is_deterministic(self):
        for seed in ("1", "7", "42"):
            out = subprocess.run([sys.executable, str(ROOT / "scripts" / "render_bandwidth_dossier.py"), "--check"],
                                 capture_output=True, text=True, env={**os.environ, "PYTHONHASHSEED": seed, "PYTHONDONTWRITEBYTECODE": "1"})
            self.assertEqual(out.returncode, 0, out.stderr)

    def test_cases_and_pathway_coverage(self):
        d = dossier()
        self.assertEqual({c["id"] for c in d["cases"]}, {"case-a-mi300x", "case-b-rubin-memory", "case-c-nvlink6"})
        pathway = next(p for p in _ctx()["pathways"]["pathways"] if p["id"] == d["inputs"]["pathway_id"])
        mapped = {c["pathway_comparison_id"]: c for c in d["comparisons"] if c["pathway_comparison_id"]}
        self.assertEqual(set(mapped), {c["id"] for c in pathway["comparisons"]})
        for c in pathway["comparisons"]:
            ours = mapped[c["id"]]
            if ours["pathway_divergence"]:
                # The one documented divergence: stricter than the pathway, and pending reconciliation.
                self.assertEqual(c["id"], "cmp-scale-up-vs-scale-out")
                self.assertGreater(v.STRICTNESS[ours["classification"]], v.STRICTNESS[c["verdict"]])
                self.assertEqual(ours["pathway_divergence"]["status"], "pending_editorial_reconciliation")
            else:
                self.assertIn(ours["classification"], v.PATHWAY_MAP[c["verdict"]], c["id"])

    def test_ide009_reconciliation_preserved(self):
        d = dossier()
        amd = item(d, "figures", "fg-a-896-platform")
        self.assertEqual((amd["direction"], amd["direction_basis"], amd["aggregation_scope"]), ("bidirectional", "source_stated", "unresolved"))
        self.assertEqual(item(d, "comparisons", "cp-mi300x-896-vs-link-sum")["classification"], "indeterminate")
        for fid in ("fg-b-22-gpu", "fg-b-192-blog"):
            self.assertEqual(item(d, "figures", fid)["hierarchy_level"], "device_memory")
        self.assertEqual(item(d, "comparisons", "cp-nvlink-36-vs-3")["classification"], "indeterminate")
        for case in d["cases"]:
            for line in case["established"] + case["analysis"] + case["preserved"]:
                if re.search(r"MI350-007|PID#2258402", line):
                    self.assertIn("pending version verification", line)
                    self.assertIn("not used as evidence", line)

    def test_no_measured_figure_and_nothing_promoted(self):
        d = dossier()
        self.assertNotIn("measured", {f["status"] for f in d["figures"]})
        self.assertEqual((d["status"], d["review_status"], d["scientific_review"], d["review_owner"]),
                         ("research_candidate", "not_reviewed", "pending", "unassigned"))
        self.assertEqual(_ctx()["atlas"].get("relationships", []), [])
        self.assertFalse(d["public_reference_decision"]["change_made"])

    def test_workflow_b_all_thirteen(self):
        d = dossier()
        wf = next(w for w in _ctx()["workbench"]["workflows"] if w["id"] == "workflow-bandwidth-comparison")
        self.assertEqual(sorted(m["requirement_id"] for m in d["workflow_b_mapping"]), sorted(r["id"] for r in wf["requirements"]))

    def test_brief_terms(self):
        text = render.BRIEF.read_text(encoding="utf-8")
        for phrase in ("voluntary and unpaid", "review a single question", "only if you give explicit permission",
                       "never presented as independent human review", "public, non-confidential material"):
            self.assertIn(phrase, text)

    def test_document_has_required_sections(self):
        text = render.OUT.read_text(encoding="utf-8")
        for n, title in enumerate(["Research question", "Metric interpretation method", "Evidence matrix", "Case: AMD MI300X Infinity Fabric",
                                   "Case: NVIDIA Rubin HBM bandwidth", "Case: NVLink 6 bandwidth", "Conflicting disclosures and version history",
                                   "Permitted and prohibited comparisons", "Unresolved questions and missing evidence",
                                   "IDE-010 workflow B requirements", "Independent technical review",
                                   "Source lineage, dates and limitations", "Research applications"], start=1):
            self.assertRegex(text, rf"(?m)^## {n}\. {re.escape(title)}$")


EXPECTED_CLASSES = {
    "cp-stack-vs-stack": "comparable_on_documented_terms", "cp-rubin-22-vs-19": "conditionally_comparable",
    "cp-mi300x-vs-rubin-memory": "conditionally_comparable", "cp-mi300x-p2p-vs-nvlink6": "indeterminate",
    "cp-memory-vs-scale-up": "not_comparable", "cp-rack-vs-gpu": "not_comparable", "cp-scale-up-vs-scale-out": "not_comparable",
    "cp-cxl-vs-pcie6": "conditionally_comparable", "cp-nvlink-36-vs-3": "indeterminate", "cp-nvl72-share-vs-column": "conditionally_comparable",
    "cp-nvl8-share-vs-row": "conditionally_comparable", "cp-nvl8-memory-share-vs-gpu": "conditionally_comparable",
    "cp-mi300x-896-vs-link-sum": "indeterminate", "cp-mi300x-896-vs-1024": "not_comparable"}
EXPECTED_NORMALIZATIONS = {"nm-a-7-links": "896", "nm-a-28-links": "3584", "nm-b-nvl8-share": "16.25", "nm-c-nvl72-share": "3",
                           "nm-c-nvl8-share": "3", "nm-c-36-halve": "1.8", "nm-x-scaleout-bytes": "200"}


class CorrectionTests(unittest.TestCase):
    """The minimum blocking correction to PR #22: scale-up versus scale-out, and the recorded pathway divergence."""

    def test_scale_up_vs_scale_out_not_comparable_with_pending_divergence(self):
        c = item(dossier(), "comparisons", "cp-scale-up-vs-scale-out")
        self.assertEqual(c["classification"], "not_comparable")
        self.assertEqual(c["pathway_divergence"], {
            "pathway_comparison_id": "cmp-scale-up-vs-scale-out", "pathway_verdict": "conditional",
            "dossier_classification": "not_comparable", "justification": c["pathway_divergence"]["justification"],
            "status": "pending_editorial_reconciliation"})
        self.assertIn("does not make them the same physical metric", c["reason"])
        self.assertIn("neither ratio describes relative delivered throughput", c["reason"])
        pathway = next(p for p in _ctx()["pathways"]["pathways"] if p["id"] == "pathway-memory-bandwidth-to-data-movement")
        self.assertEqual(next(x for x in pathway["comparisons"] if x["id"] == "cmp-scale-up-vs-scale-out")["verdict"], "conditional")

    def test_only_one_divergence_and_other_classes_unchanged(self):
        d = dossier()
        self.assertEqual({c["id"]: c["classification"] for c in d["comparisons"]}, EXPECTED_CLASSES)
        self.assertEqual([c["id"] for c in d["comparisons"] if c["pathway_divergence"]], ["cp-scale-up-vs-scale-out"])
        counts = {k: list(EXPECTED_CLASSES.values()).count(k) for k in v.CLASSES}
        self.assertEqual(counts, {"comparable_on_documented_terms": 1, "conditionally_comparable": 6, "not_comparable": 4, "indeterminate": 3})

    def test_normalizations_unchanged(self):
        d = dossier()
        self.assertEqual({n["id"]: n["result_value"] for n in d["normalizations"]}, EXPECTED_NORMALIZATIONS)
        self.assertEqual(sorted(r["id"] for r in d["rejected_normalizations"]), ["rj-a-896-share", "rj-c-3-halve", "rj-c-3600-halve"])
        self.assertEqual(len(d["figures"]), 26)

    def test_conditional_across_levels_fails(self):
        d = dossier(); c = item(d, "comparisons", "cp-scale-up-vs-scale-out")
        c["classification"] = "conditionally_comparable"; c["pathway_divergence"] = None
        c["conditions"] = ["Convert bits to bytes", "Neither states a peak or a direction"]
        self.assertFlags(d, r"same hierarchy level, aggregation scope and unit dimension after normalization")

    def test_unexplained_pathway_discrepancy_fails(self):
        d = dossier(); item(d, "comparisons", "cp-scale-up-vs-scale-out")["pathway_divergence"] = None
        self.assertFlags(d, r"contradicts pathway verdict 'conditional' for cmp-scale-up-vs-scale-out and no divergence is recorded")

    def test_divergence_cannot_bypass_rules(self):
        # A divergence cannot loosen a pathway verdict.
        d = dossier(); c = item(d, "comparisons", "cp-mi300x-p2p-vs-nvlink6"); c["classification"] = "conditionally_comparable"
        c["conditions"] = ["direction stated", "peak"]
        c["pathway_divergence"] = {"pathway_comparison_id": "cmp-mi300x-p2p-vs-nvlink6", "pathway_verdict": "unsupported",
                                   "dossier_classification": "conditionally_comparable", "status": "pending_editorial_reconciliation",
                                   "justification": "An arbitrary declaration written to bypass the classification rules for this pair of figures."}
        self.assertFlags(d, r"may only restrict the pathway verdict")
        self.assertFlags(d, r"unresolved scope cannot be compared")
        # A divergence cannot be attached where the class already agrees with the pathway.
        d = dossier(); item(d, "comparisons", "cp-stack-vs-stack")["pathway_divergence"] = copy.deepcopy(item(dossier(), "comparisons", "cp-scale-up-vs-scale-out")["pathway_divergence"])
        self.assertFlags(d, r"divergence is recorded where the classification agrees")
        # A divergence must match the comparison exactly.
        d = dossier(); item(d, "comparisons", "cp-scale-up-vs-scale-out")["pathway_divergence"]["pathway_verdict"] = "unsupported"
        self.assertFlags(d, r"must name this comparison's pathway id, its current verdict")
        d = dossier(); item(d, "comparisons", "cp-scale-up-vs-scale-out")["pathway_divergence"]["justification"] = "Because."
        self.assertFlags(d, r"needs a technical justification")
        # A divergence is never a completed reconciliation.
        d = dossier(); item(d, "comparisons", "cp-scale-up-vs-scale-out")["pathway_divergence"]["status"] = "reconciled"
        self.assertFlags(d, r"stays 'pending_editorial_reconciliation'")
        d = dossier(); item(d, "comparisons", "cp-scale-up-vs-scale-out")["pathway_divergence"]["approved"] = True
        self.assertFlags(d, r"must contain exactly")

    def test_not_comparable_needs_recorded_metric_difference(self):
        d = dossier(); c = item(d, "comparisons", "cp-nvl72-share-vs-column"); c["classification"] = "not_comparable"
        item(d, "figures", "fg-c-3-nvl72")["metric"] = "A differently worded metric"
        self.assertFlags(d, r"a difference in the dossier's own wording is not enough")

    def test_capacity_wording(self):
        text = render.OUT.read_text(encoding="utf-8")
        self.assertNotIn("so the row is not a simple multiple", text)
        self.assertIn("do not explain whether rounding, a different configuration or another counting convention", text)
        self.assertNotIn("250 GB", text)

    def assertFlags(self, d, pattern):
        errs = v.check(d, ctx())
        self.assertTrue(any(re.search(pattern, e) for e in errs), f"expected /{pattern}/ in {errs}")


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

    def test_figure_must_match_its_record(self):
        d = dossier(); item(d, "figures", "fg-a-896-platform")["value"] = "900"
        self.assertFlags(d, r"value 900 GB/s does not appear")
        d = dossier(); item(d, "figures", "fg-c-3-blog")["source_id"] = "nvidia-rubin-platform-architecture-2026"
        self.assertFlags(d, r"does not match the record's source")
        d = dossier(); item(d, "figures", "fg-b-22-gpu")["ref"] = "register:ec-rubin-memory-bandwidth:99"
        self.assertFlags(d, r"does not resolve")
        d = dossier(); item(d, "figures", "fg-b-22-gpu")["unit"] = "TB"
        self.assertFlags(d, r"is not a bandwidth unit")

    def test_direction_cannot_be_inferred(self):
        d = dossier(); f = item(d, "figures", "fg-c-3-blog"); f["direction"] = "bidirectional"
        self.assertFlags(d, r"only when the source states it")
        d = dossier(); item(d, "figures", "fg-b-22-gpu")["direction"] = "bidirectional"; item(d, "figures", "fg-b-22-gpu")["direction_basis"] = "source_stated"
        self.assertFlags(d, r"memory bandwidth carries no link direction")

    def test_no_invented_measurement(self):
        d = dossier(); item(d, "figures", "fg-c-216-nvl72")["status"] = "measured"
        self.assertFlags(d, r"needs a measurement record")

    def test_normalization_arithmetic_and_rules(self):
        d = dossier(); item(d, "normalizations", "nm-c-nvl72-share")["result_value"] = "3.6"
        self.assertFlags(d, r"arithmetic does not hold")
        d = dossier(); d["normalizations"].append({"id": "nm-bad-halve", "figure_id": "fg-c-3-blog", "rule_id": "nr-halve-bidirectional", "factor": 2,
                                                   "result_value": "1.5", "result_unit": "TB/s", "result_level": "device_fabric_aggregate",
                                                   "basis": ["quantity:aec-ide-004-interconnect:i-nvidia-nvlink6-figures:2"], "note": "Arithmetic; not a publisher statement."})
        self.assertFlags(d, r"unsupported normalization of fg-c-3-blog \(requires direction=bidirectional\)")
        d = dossier(); d["normalizations"].append({"id": "nm-bad-share", "figure_id": "fg-a-896-platform", "rule_id": "nr-equal-share", "factor": 8,
                                                   "result_value": "112", "result_unit": "GB/s", "result_level": "device_fabric_link",
                                                   "basis": ["register:ec-mi300x-infinity-fabric-scope:3"], "note": "Arithmetic; not a publisher statement."})
        self.assertFlags(d, r"unsupported normalization of fg-a-896-platform")
        d = dossier(); item(d, "normalizations", "nm-x-scaleout-bytes")["result_unit"] = "Gb/s"; item(d, "normalizations", "nm-x-scaleout-bytes")["result_value"] = "1600"
        self.assertFlags(d, r"must give a byte unit")

    def test_rejected_normalization_must_break_its_rule(self):
        d = dossier(); d["rejected_normalizations"].append({"id": "rj-fake", "figure_id": "fg-c-36-platform", "rule_id": "nr-halve-bidirectional", "why": "x"})
        self.assertFlags(d, r"must actually break its rule")

    def test_comparability_rules(self):
        d = dossier(); item(d, "comparisons", "cp-nvlink-36-vs-3")["classification"] = "comparable_on_documented_terms"
        self.assertFlags(d, r"needs the same level, scope, direction and peak status")
        d = dossier(); c = item(d, "comparisons", "cp-memory-vs-scale-up"); c["classification"] = "conditionally_comparable"; c["conditions"] = ["state both"]
        self.assertFlags(d, r"same hierarchy level, aggregation scope and unit dimension")
        d = dossier(); item(d, "comparisons", "cp-rack-vs-gpu")["classification"] = "conditionally_comparable"
        self.assertFlags(d, r"must state its conditions")
        d = dossier(); item(d, "comparisons", "cp-cxl-vs-pcie6")["conditions"] = ["State that NVIDIA's counting basis is not published"]
        self.assertFlags(d, r"a condition must name it, or the class is 'indeterminate'")
        d = dossier(); c = item(d, "comparisons", "cp-mi300x-896-vs-link-sum"); c["classification"] = "conditionally_comparable"; c["conditions"] = ["Arithmetic only"]
        self.assertFlags(d, r"unresolved scope cannot be compared")
        d = dossier(); item(d, "comparisons", "cp-stack-vs-stack")["classification"] = "not_comparable"
        self.assertFlags(d, r"recorded quantities differ")
        d = dossier(); item(d, "comparisons", "cp-stack-vs-stack")["classification"] = "indeterminate"
        self.assertFlags(d, r"'indeterminate' needs a figure")

    def test_pathway_verdict_consistency(self):
        d = dossier(); c = item(d, "comparisons", "cp-mi300x-p2p-vs-nvlink6")
        c["figure_ids"] = ["fg-c-36-platform", "fg-c-36-platform"]; c["classification"] = "comparable_on_documented_terms"
        self.assertFlags(d, r"contradicts pathway verdict 'unsupported'")
        d = dossier(); d["comparisons"] = [c for c in d["comparisons"] if c["id"] != "cp-cxl-vs-pcie6"]
        self.assertFlags(d, r"pathway comparisons not classified: \['cmp-cxl-vs-pcie6'\]")

    def test_reconciliation_cannot_be_reversed(self):
        d = dossier(); f = item(d, "figures", "fg-a-896-platform"); f["direction"] = "not_stated"; f["direction_basis"] = "unknown"
        self.assertFlags(d, r"must keep its AMD-stated direction and unresolved scope")
        d = dossier(); item(d, "figures", "fg-a-896-platform")["aggregation_scope"] = "per_device"
        self.assertFlags(d, r"must keep its AMD-stated direction and unresolved scope")
        d = dossier(); item(d, "cases", "case-a-mi300x")["analysis"].append("Endnote MI350-007 states it per GPU.")
        self.assertFlags(d, r"unverified 2025 CDNA 4 edition")
        d = dossier(); item(d, "figures", "fg-b-192-blog")["restrictions"] = ["None"]
        self.assertFlags(d, r"must carry a restriction against selecting it")

    def test_coverage_and_materials(self):
        d = dossier(); d["workflow_b_mapping"].pop()
        self.assertFlags(d, r"every workflow B requirement must be mapped")
        d = dossier(); d["review_questions"][0]["materials"].append("unregistered-source-2026")
        self.assertFlags(d, r"public, active source materials")
        d = dossier(); d["principal_findings"][0]["basis"] = ["nm-does-not-exist"]
        self.assertFlags(d, r"needs a basis")

    def test_governance(self):
        d = dossier(); d["review_owner"] = "A. Specialist"
        self.assertFlags(d, r"review owner unassigned")
        d = dossier(); d["public_reference_decision"]["change_made"] = True
        self.assertFlags(d, r"must go through a release")
        d = dossier(); d["comparisons"][0]["approved_by"] = "someone"
        self.assertFlags(d, r"'approved_by' is not allowed")
        d = dossier(); item(d, "comparisons", "cp-rack-vs-gpu")["reason"] = "Rubin is ranked first for fabric bandwidth."
        self.assertFlags(d, r"score, approval or review-completion language")
        c = ctx(); c["atlas"]["relationships"] = [{"id": "rel-x"}]
        self.assertFlags(dossier(), r"must not be read as promoting", c)

    def test_brief_out_of_sync(self):
        original = render.BRIEF
        tmp = ROOT / "build" / "brief-sync-test.md"
        try:
            tmp.parent.mkdir(exist_ok=True)
            tmp.write_text(original.read_text(encoding="utf-8").replace("voluntary and unpaid", "paid"), encoding="utf-8")
            render.BRIEF = tmp
            self.assertIn("brief-sync-test.md", render.out_of_sync())
        finally:
            render.BRIEF = original
            tmp.unlink(missing_ok=True)


if __name__ == "__main__":
    unittest.main()
