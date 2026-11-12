"""Regression tests for IDE-014: the AI rack deployment evidence chain and operational verification dossier."""

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
import render_rack_deployment_dossier as render  # noqa: E402
import validate_rack_deployment_dossier as v  # noqa: E402


@functools.lru_cache(maxsize=1)
def _ctx():
    return v.load_context()


def ctx():
    return copy.deepcopy(_ctx())


def dossier():
    return json.loads(v.DOSSIER.read_text(encoding="utf-8"))


def item(d, key, iid, field="id"):
    return next(x for x in d[key] if x[field] == iid)


class DossierTests(unittest.TestCase):
    def test_validates_and_documents_in_sync(self):
        self.assertEqual(v.check_all(), [])
        self.assertEqual(render.out_of_sync(), [])

    def test_rendering_is_deterministic(self):
        for seed in ("1", "9"):
            out = subprocess.run([sys.executable, str(ROOT / "scripts" / "render_rack_deployment_dossier.py"), "--check"],
                                 capture_output=True, text=True, env={**os.environ, "PYTHONHASHSEED": seed, "PYTHONDONTWRITEBYTECODE": "1"})
            self.assertEqual(out.returncode, 0, out.stderr)

    def test_all_fifteen_workflow_c_requirements_once(self):
        d = dossier()
        wf = next(w for w in _ctx()["workbench"]["workflows"] if w["id"] == "workflow-rack-deployment")
        ids = sorted(r["id"] for r in wf["requirements"])
        self.assertEqual(sorted(r["requirement_id"] for r in d["matrix"]), ids)
        self.assertEqual(sorted(x for dm in d["domains"] for x in dm["workflow_c_ids"]), ids)

    def test_reuses_the_nine_states_and_seven_domains(self):
        d = dossier()
        self.assertEqual({dm["id"] for dm in d["domains"]}, v.DOSSIER_DOMAINS)
        self.assertTrue({t["state_ceiling"] for t in d["record_types"] if t["state_ceiling"]} <= set(v.STATES))
        self.assertNotRegex(json.dumps(d), r"(?i)readiness (?:score|percent)|maturity|\d+\s?%")

    def test_no_site_record_and_nothing_reviewed(self):
        d = dossier()
        self.assertEqual([s for s, r in _ctx()["registry"].items() if "site_record" in r["supported_claim_types"]], [])
        self.assertEqual({r["record_status"] for r in d["matrix"]}, {"not_obtained"})
        self.assertEqual((d["status"], d["review_status"], d["scientific_review"], d["review_owner"]),
                         ("research_candidate", "not_reviewed", "pending", "unassigned"))
        self.assertEqual(_ctx()["atlas"].get("relationships", []), [])
        self.assertFalse(d["public_reference_decision"]["change_made"])

    def test_ide006_consistency_flags_exactly_one_entry(self):
        self.assertEqual([x["requirement_id"] for x in dossier()["ide006_consistency"]], ["req-nw-north-south"])

    def test_document_sections_and_brief_terms(self):
        text = render.OUT.read_text(encoding="utf-8")
        for n, title in enumerate(["Research question and scope", "Evidence states and the records that can support them", "Deployment evidence chain",
                                   "Seven-domain verification matrix", "Cross-domain dependencies", "GB200 NVL72 documentary case",
                                   "Evidence needed for commissioning and acceptance", "Operational observation and measurement",
                                   "Workflow C coverage", "Unsupported and unresolved claims", "Documentary and technical review requirements",
                                   "Source lineage, limitations and dates", "Research and due-diligence applications"], start=1):
            self.assertRegex(text, rf"(?m)^## {n}\. {re.escape(title)}$")
        self.assertIn("0 registered sources support a site-record claim", text)
        brief = render.BRIEF.read_text(encoding="utf-8")
        for phrase in ("voluntary and unpaid", "review a single question", "only if you give explicit permission",
                       "never presented as independent human review", "do not share site records"):
            self.assertIn(phrase, brief)

    def test_inspection_run_recorded(self):
        run = [r for r in _ctx()["log"]["records"] if r["run_id"] == "ide-014-2026-11-12"]
        self.assertEqual(len(run), 10)
        self.assertTrue(all(r["passage_check"] and not r["passage_check"]["not_found"] for r in run))


class NegativeTests(unittest.TestCase):
    def assertFlags(self, d, pattern, c=None):
        errs = v.check(d, c or ctx())
        self.assertTrue(any(re.search(pattern, e) for e in errs), f"expected /{pattern}/ in {errs}")

    def test_missing_files_fail_closed(self):
        original = v.DOSSIER
        try:
            v.DOSSIER = ROOT / "does-not-exist.json"
            self.assertIn("required file missing", v.check_all()[0])
        finally:
            v.DOSSIER = original

    def test_unknown_identifiers(self):
        d = dossier(); item(d, "record_types", "rt-installation-record")["basis_refs"].append("d-invented-finding")
        self.assertFlags(d, r"references must resolve")
        d = dossier(); d["dependencies"][0]["prerequisite"] = "req-invented"
        self.assertFlags(d, r"distinct IDE-006 requirements")
        d = dossier(); d["domains"][1]["unresolved_ids"].append("u-invented")
        self.assertFlags(d, r"open questions and register issues must exist")

    def test_vendor_specification_cannot_prove_installation(self):
        d = dossier(); t = item(d, "record_types", "rt-product-specification"); t["state_ceiling"] = "equipment_installed"
        self.assertFlags(d, r"not site-specific cannot support the site-level state equipment_installed")
        self.assertFlags(d, r"vendor document cannot support installation")

    def test_checklist_cannot_be_commissioning(self):
        d = dossier(); t = item(d, "record_types", "rt-checklist-template"); t["state_ceiling"] = "subsystem_commissioned"; t["site_specific"] = True
        t["required_attributes"] += ["named_site", "configuration_identity", "method", "criteria", "results"]
        self.assertFlags(d, r"vendor document cannot support installation, commissioning")

    def test_acceptance_procedure_cannot_be_signed_acceptance(self):
        d = dossier(); item(d, "record_types", "rt-acceptance-criteria")["state_ceiling"] = "integrated_configuration_verified"
        self.assertFlags(d, r"acceptance criteria \(a procedure to accept\) cannot support acceptance")
        d = dossier(); item(d, "record_types", "rt-acceptance-record")["required_attributes"].remove("signatory_authority")
        self.assertFlags(d, r"signed acceptance record needs signatory authority")

    def test_benchmark_specification_cannot_be_operational_measurement(self):
        d = dossier(); item(d, "record_types", "rt-performance-specification")["state_ceiling"] = "operational_performance_observed"
        self.assertFlags(d, r"cannot support the site-level state operational_performance_observed")
        d = dossier(); item(d, "record_types", "rt-workload-measurement")["required_attributes"].remove("period")
        self.assertFlags(d, r"needs an observation period")

    def test_commissioning_needs_method_criteria_results(self):
        d = dossier(); item(d, "record_types", "rt-commissioning-record")["required_attributes"].remove("criteria")
        self.assertFlags(d, r"needs criteria stated in advance")
        d = dossier(); item(d, "record_types", "rt-integrated-test-record")["required_attributes"].remove("results")
        self.assertFlags(d, r"stated method and recorded results")

    def test_requested_document_is_not_a_reviewed_record(self):
        d = dossier(); item(d, "matrix", "rc-09-installation", "requirement_id")["record_status"] = "reviewed"
        self.assertFlags(d, r"requested site record is treated as reviewed")

    def test_site_claim_needs_site_record_and_sufficient_type(self):
        d = dossier(); r = item(d, "matrix", "rc-09-installation", "requirement_id"); r["record_type_ids"] = ["rt-documented-procedure"]
        self.assertFlags(d, r"no listed record type can support equipment_installed")
        self.assertFlags(d, r"site-level claim needs a site record")
        d = dossier(); item(d, "matrix", "rc-12-acceptance", "requirement_id")["record_type_ids"] = ["rt-commissioning-record"]
        self.assertFlags(d, r"cannot support integrated_configuration_verified|no listed record type can support integrated_configuration_verified")

    def test_unsupported_state_transition_through_dependencies(self):
        c = ctx()
        next(q for q in c["ide006"]["requirements"] if q["id"] == "req-nw-nvlink-bring-up")["current_state"] = "subsystem_commissioned"
        self.assertFlags(dossier(), r"dependent holds subsystem_commissioned while its prerequisite holds", c)
        d = dossier(); d["dependencies"].append({"prerequisite": "req-sw-validation-results", "dependent": "req-sw-firmware-baseline",
                                                 "basis": ["d-bringup-sequence"], "basis_class": "project_defined"})
        self.assertFlags(d, r"dependency graph has a cycle")

    def test_access_is_separate_and_no_regulatory_conclusion(self):
        d = dossier(); item(d, "chain", "g-access")["states"] = ["equipment_installed"]
        self.assertFlags(d, r"access is a separate dimension")
        d = dossier(); item(d, "matrix", "rc-08-procurement-delivery", "requirement_id")["record_type_ids"] = ["rt-transaction-determination"]
        self.assertFlags(d, r"target state must be a governed technical state")
        d = dossier(); item(d, "record_types", "rt-rule-text")["state_ceiling"] = "capability_contracted"
        self.assertFlags(d, r"access record has no technical evidence state")

    def test_missing_workflow_c_requirement(self):
        d = dossier(); d["matrix"].pop()
        self.assertFlags(d, r"matrix must cover every Workflow C requirement")
        d = dossier(); d["domains"][0]["workflow_c_ids"].pop()
        self.assertFlags(d, r"exactly one domain")

    def test_consistency_list_cannot_hide_or_invent(self):
        d = dossier(); d["ide006_consistency"] = []
        self.assertFlags(d, r"must list exactly the IDE-006 entries above their evidence ceiling")
        d = dossier(); d["ide006_consistency"].append(dict(d["ide006_consistency"][0], requirement_id="req-ch-rack-configuration"))
        self.assertFlags(d, r"must list exactly")

    def test_no_fabricated_review_or_promotion(self):
        d = dossier(); d["review_owner"] = "A. Engineer"
        self.assertFlags(d, r"review owner unassigned")
        d = dossier(); d["matrix"][0]["certified_by"] = "someone"
        self.assertFlags(d, r"'certified_by' is not allowed")
        d = dossier(); d["findings"][0]["text"] = "The site is ready for production and fully verified."
        self.assertFlags(d, r"review-completion language|readiness")
        d = dossier(); d["public_reference_decision"]["change_made"] = True
        self.assertFlags(d, r"must go through a release")
        c = ctx(); c["atlas"]["relationships"] = [{"id": "rel-x"}]
        self.assertFlags(dossier(), r"must not be read as promoting", c)

    def test_document_out_of_sync(self):
        original = render.OUT
        tmp = ROOT / "build" / "rack-sync-test.md"
        try:
            tmp.parent.mkdir(exist_ok=True)
            tmp.write_text(original.read_text(encoding="utf-8").replace("not established", "established"), encoding="utf-8")
            render.OUT = tmp
            self.assertIn("rack-sync-test.md", render.out_of_sync())
        finally:
            render.OUT = original
            tmp.unlink(missing_ok=True)


if __name__ == "__main__":
    unittest.main()
