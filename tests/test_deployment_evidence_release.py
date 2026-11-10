"""Regression tests for IDE-006 (AI compute infrastructure and deployment readiness evidence)."""

from __future__ import annotations

import copy
import html
import json
import re
import sys
import unittest
from collections import Counter
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from validate_evidence_releases import (  # noqa: E402
    DOSSIER_DOMAINS,
    EVIDENCE_STATES_ORDERED,
    SITE_EVIDENCE_STATES,
    check_dossier,
    check_inference_boundaries,
    check_pages_exclusion,
    check_public_references,
    check_release,
    check_review_representation,
    check_shared_candidate_nodes,
    inference_boundary_errors,
    reference_page,
)

RESEARCH = ROOT / "data" / "research"
RELEASE = RESEARCH / "deployment-evidence-release-006.json"
POWER_RELEASE = RESEARCH / "power-thermal-evidence-release-005.json"
DOSSIER = RESEARCH / "dossiers" / "gb200-nvl72-reference-demo.json"
PAGE = ROOT / "ai-chip-infrastructure" / "index.html"
WORKFLOW = ROOT / ".github" / "workflows" / "validate-and-deploy.yml"
TODAY = date(2026, 11, 10)


def read(path):
    return json.loads(path.read_text(encoding="utf-8"))


def registry():
    return read(ROOT / "data" / "source-registry.json")


def atlas():
    return read(ROOT / "data" / "dependency-atlas.json")


def releases():
    return {p.name: read(p) for p in sorted(RESEARCH.glob("*.json"))}


def dossier_errors(d, reg=None):
    return check_dossier(d, reg or registry(), releases(), "fixture")


def requirement(d, rid):
    return next(r for r in d["requirements"] if r["id"] == rid)


def site_record_registry():
    """A fixture registry with one hypothetical site record, to show the site-state rule is conditional."""
    reg = copy.deepcopy(registry())
    reg["source_records"].append({
        "id": "fixture-site-commissioning-record", "title": "Fixture commissioning record", "publisher": "Fixture operator",
        "source_type": "official_dataset", "canonical_url": "https://example.invalid/record", "publication_date": "2026-11-01",
        "accessed_at": "2026-11-10", "ontology_layers": ["deployment"], "supported_claim_types": ["site_record"],
        "geographic_scope": "fixture", "temporal_scope": "fixture", "confidence_use": "fixture", "use_limitations": ["fixture"],
        "status": "active"})
    return reg


class ReleaseTests(unittest.TestCase):
    def test_release_is_valid_and_mapped_to_its_page(self):
        release = read(RELEASE)
        self.assertEqual([], check_release(release, registry(), atlas(), TODAY, RELEASE.name))
        self.assertEqual("ai-chip-infrastructure/index.html", release["reference_page"])
        self.assertEqual(PAGE, reference_page(release))
        self.assertEqual("research_candidate", release["status"])
        self.assertIs(False, release["publication_eligible"])

    def test_page_passes_boundaries_references_and_review_representation(self):
        release = read(RELEASE)
        self.assertEqual([], check_inference_boundaries(release, PAGE))
        self.assertEqual([], check_public_references(PAGE, registry()))
        self.assertEqual([], check_review_representation(PAGE, {release["as_of"]}))
        self.assertIn("Evidence compiled: 2026-11-10 · Scientific review pending", PAGE.read_text(encoding="utf-8"))

    def test_finding_classes_cover_definitions_statements_analyses_and_insights(self):
        release = read(RELEASE)
        classes = Counter(f["claim_class"] for f in release["findings"])
        self.assertGreater(classes["attributed_statement"], 0)
        self.assertGreater(classes["bounded_analysis"], 0)
        ids = {f["id"] for f in release["findings"]}
        self.assertTrue(any(i.startswith("d-def-") for i in ids))
        self.assertTrue(any(i.startswith("d-int-") for i in ids))
        for f in release["findings"]:
            if f["id"].startswith(("d-def-", "d-int-", "d-an-")):
                self.assertEqual("bounded_analysis", f["claim_class"], f["id"])

    def test_earlier_findings_are_referenced_not_copied(self):
        release, earlier = read(RELEASE), read(POWER_RELEASE)
        earlier_ids = {f["id"] for f in earlier["findings"]} | {u["id"] for u in earlier["unresolved"]}
        own_ids = {f["id"] for f in release["findings"]} | {u["id"] for u in release["unresolved"]}
        self.assertEqual(set(), own_ids & earlier_ids)
        earlier_statements = {f["statement"] for f in earlier["findings"]}
        self.assertFalse(any(f["statement"] in earlier_statements for f in release["findings"]))

    def test_no_vera_rubin_figures_and_generations_kept_apart(self):
        release = read(RELEASE)
        text = json.dumps(release)
        self.assertNotIn("Rubin", text)
        self.assertIn("u-d-gb300-difference", {u["id"] for u in release["unresolved"]})


class EvidenceStateTests(unittest.TestCase):
    def test_governed_states_are_exact(self):
        self.assertEqual(9, len(EVIDENCE_STATES_ORDERED))
        self.assertEqual("not_established", EVIDENCE_STATES_ORDERED[-1])
        self.assertEqual(set(EVIDENCE_STATES_ORDERED[2:8]), SITE_EVIDENCE_STATES)
        d = read(DOSSIER)
        self.assertEqual(EVIDENCE_STATES_ORDERED, d["evidence_states"])
        bad = copy.deepcopy(d)
        bad["evidence_states"] = list(reversed(d["evidence_states"]))
        self.assertTrue(any("governed states" in e for e in dossier_errors(bad)))

    def test_dossier_uses_only_documentation_states(self):
        states = {r["current_state"] for r in read(DOSSIER)["requirements"]}
        self.assertLessEqual(states, {"product_specification_documented", "infrastructure_proposed", "not_established"})

    def test_every_site_state_is_rejected_without_a_site_record(self):
        d = read(DOSSIER)
        for state in sorted(SITE_EVIDENCE_STATES):
            bad = copy.deepcopy(d)
            requirement(bad, "req-el-rack-power")["current_state"] = state
            errs = dossier_errors(bad)
            self.assertTrue(any("site record" in e for e in errs), state)

    def test_site_state_is_accepted_only_with_a_site_record(self):
        d = copy.deepcopy(read(DOSSIER))
        r = requirement(d, "req-el-site-capacity")
        r.update(current_state="subsystem_commissioned", evidence_classification="site_record",
                 evidence=[{"source_id": "fixture-site-commissioning-record", "locator": "Fixture section 1"}])
        self.assertEqual([], dossier_errors(d, site_record_registry()))

    def test_no_registered_source_is_a_site_record(self):
        self.assertFalse(any("site_record" in s.get("supported_claim_types", []) for s in registry()["source_records"]))

    def test_classification_must_match_state(self):
        d = read(DOSSIER)
        bad = copy.deepcopy(d)
        requirement(bad, "req-ch-rack-configuration")["evidence_classification"] = "none"
        self.assertTrue(any("does not match state" in e or "classified 'none'" in e for e in dossier_errors(bad)))

    def test_documented_states_need_evidence(self):
        bad = copy.deepcopy(read(DOSSIER))
        requirement(bad, "req-sw-management-stack")["evidence"] = []
        self.assertTrue(any("must cite evidence" in e for e in dossier_errors(bad)))


class ProgressionBoundaryTests(unittest.TestCase):
    """Evidence at one level must not be promoted to another."""

    CASES = {
        "reference design as operation": ("The DGX SuperPOD reference architecture is deployed at the site.",
                                          "The reference architecture is not deployed at any reviewed site."),
        "installation as commissioning": ("Installation of the racks proves they are commissioned.",
                                          "Installation of the racks does not prove they are commissioned."),
        "driver compatibility as performance": ("Driver compatibility ensures cluster performance.",
                                                "Driver compatibility does not ensure cluster performance."),
        "rated as available": ("The rated capacity is available to the racks.",
                               "The rated capacity is not available capacity."),
        "liquid-cooling support as site compatibility": ("The facility water loop is compatible with liquid-cooled GB200 racks.",
                                                         "No reviewed source shows a facility water loop compatible with liquid-cooled racks."),
        "availability as delivery": ("General availability means the racks were delivered.",
                                     "Availability does not mean the racks were delivered."),
        "standard as conformance": ("The facility meets Tier III.",
                                    "No reviewed record shows the facility meets Tier III."),
        "planned as operational": ("The planned facility is now operational.",
                                   "The planned facility is not shown to be operational."),
        "checklist as approval": ("The completed checklist is an approval of the deployment.",
                                  "The checklist is not an approval."),
        "dossier as approval": ("This dossier serves as an engineering sign-off.",
                                "This dossier is not a sign-off."),
        "facility readiness": ("The site is ready for GB200 NVL72.",
                               "No site is shown to be ready for GB200 NVL72."),
    }

    def test_unsupported_progressions_are_rejected_and_negations_pass(self):
        for name, (claim, negated) in self.CASES.items():
            with self.subTest(name):
                self.assertTrue(inference_boundary_errors(claim, "fixture"), claim)
                self.assertEqual([], inference_boundary_errors(negated, "fixture"), negated)

    def test_open_questions_assert_nothing(self):
        self.assertEqual([], inference_boundary_errors("Is the site ready for GB200 NVL72?", "fixture"))

    def test_dossier_text_is_held_to_the_same_boundaries(self):
        bad = copy.deepcopy(read(DOSSIER))
        requirement(bad, "req-fo-handover")["next_verification_action"] = "Installation of the system proves it is operational."
        self.assertTrue(any("installation" in e for e in dossier_errors(bad)))

    def test_release_rejects_an_unsupported_commissioning_claim(self):
        release = copy.deepcopy(read(RELEASE))
        f = next(f for f in release["findings"] if f["id"] == "d-bringup-sequence")
        f["statement"] += " Installation of the switch trays establishes that the rack is commissioned."
        page_errors = check_inference_boundaries(release, PAGE)
        self.assertTrue(any("d-bringup-sequence" in e and "commission" in e for e in page_errors))


class DossierIntegrityTests(unittest.TestCase):
    def test_dossier_is_valid_and_demonstration_only(self):
        d = read(DOSSIER)
        self.assertEqual([], dossier_errors(d))
        self.assertEqual("demonstration", d["status"])
        self.assertEqual("not_reviewed", d["review_status"])
        self.assertEqual("ai_assisted_source_check", d["assessment_method"])
        self.assertEqual(read(RELEASE)["release_id"], d["evidence_release"])
        self.assertIn("None", d["subject"]["site"])

    def test_all_seven_domains_are_covered(self):
        d = read(DOSSIER)
        self.assertEqual(DOSSIER_DOMAINS, {r["domain"] for r in d["requirements"]})
        bad = copy.deepcopy(d)
        bad["requirements"] = [r for r in d["requirements"] if r["domain"] != "access_compliance"]
        self.assertTrue(any("seven domains" in e for e in dossier_errors(bad)))

    def test_approvals_scores_and_reviewers_are_forbidden(self):
        for key in ("approved_by", "approval", "readiness_score", "readiness_percent", "score", "reviewer", "reviewed_at", "sign_off",
                    "certified"):
            with self.subTest(key):
                bad = copy.deepcopy(read(DOSSIER))
                bad["requirements"][0][key] = "x"
                self.assertTrue(any("cannot carry approvals" in e for e in dossier_errors(bad)))

    def test_review_status_and_method_cannot_be_promoted(self):
        for field, value in (("review_status", "reviewed"), ("assessment_method", "human_review"), ("status", "approved")):
            with self.subTest(field):
                bad = copy.deepcopy(read(DOSSIER))
                bad[field] = value
                self.assertTrue(dossier_errors(bad))

    def test_unknown_release_and_duplicate_ids_rejected(self):
        bad = copy.deepcopy(read(DOSSIER))
        bad["evidence_release"] = "aec-ide-999"
        bad["requirements"].append(copy.deepcopy(bad["requirements"][0]))
        errs = dossier_errors(bad)
        self.assertTrue(any("existing evidence release" in e for e in errs))
        self.assertTrue(any("duplicate id" in e for e in errs))

    def test_traceability_to_registry_and_releases(self):
        d, reg = read(DOSSIER), {s["id"]: s for s in registry()["source_records"]}
        unresolved = {u["id"] for r in releases().values() for u in r["unresolved"]}
        for r in d["requirements"]:
            for e in r["evidence"]:
                self.assertEqual("active", reg[e["source_id"]]["status"], r["id"])
                self.assertTrue(e["locator"].strip())
            self.assertLessEqual(set(r["contradictions"]), unresolved, r["id"])
        for sid in d["assessment_scope"]["sources_reviewed"]:
            self.assertIn(sid, reg)

    def test_missing_facility_evidence_is_explicit(self):
        d = read(DOSSIER)
        for rid in ("req-el-site-capacity", "req-th-validated-under-load", "req-sw-validation-results", "req-fo-handover"):
            r = requirement(d, rid)
            self.assertEqual("not_established", r["current_state"], rid)
            self.assertEqual("none", r["evidence_classification"], rid)
            self.assertTrue(r["missing_information"], rid)
        bad = copy.deepcopy(d)
        requirement(bad, "req-fo-handover")["missing_information"] = []
        self.assertTrue(any("must say what information is missing" in e for e in dossier_errors(bad)))
        bad = copy.deepcopy(d)
        requirement(bad, "req-fo-handover")["contradictions"] = ["u-invented"]
        self.assertTrue(any("contradictions" in e for e in dossier_errors(bad)))


class ContradictionTests(unittest.TestCase):
    IDE005 = ["u-pt-redundancy-conflict", "u-pt-bus-bar-paths", "u-pt-120kw-basis", "u-pt-scalable-unit-remainder",
              "u-pt-coolant-specification"]

    def test_ide005_conflicts_remain_open_and_are_carried_forward(self):
        earlier = {u["id"] for u in read(POWER_RELEASE)["unresolved"]}
        self.assertLessEqual(set(self.IDE005), earlier)
        carry = next(u for u in read(RELEASE)["unresolved"] if u["id"] == "u-d-ide005-carryover")
        for uid in self.IDE005:
            self.assertIn(uid, carry["why_unresolved"])
        linked = {c for r in read(DOSSIER)["requirements"] for c in r["contradictions"]}
        self.assertLessEqual(set(self.IDE005), linked)

    def test_tested_scale_conflict_preserves_both_lines(self):
        f = next(f for f in read(RELEASE)["findings"] if f["id"] == "d-ra-tested-scope")
        locator = f["evidence"][0]["locator"]
        self.assertIn("two SUs", locator)
        self.assertIn("single SU", locator)
        self.assertIn("u-d-tested-scale", requirement(read(DOSSIER), "req-nw-tested-scale")["contradictions"])

    def test_checklist_items_are_templates_not_records(self):
        f = next(f for f in read(RELEASE)["findings"] if f["id"] == "d-validation-checklist")
        self.assertTrue(any("blank template" in lim for lim in f["limitations"]))


class AtlasBoundaryTests(unittest.TestCase):
    def test_atlas_unchanged_and_candidates_unreviewed(self):
        self.assertEqual([], atlas()["relationships"])
        release = read(RELEASE)
        atlas_nodes = {n["id"] for n in atlas()["nodes"]}
        for node in release["candidate_nodes"]:
            self.assertNotIn(node["id"], atlas_nodes)
        for edge in release["candidate_relationships"]:
            self.assertEqual("awaiting_human_review", edge["review_status"])
            self.assertIsNone(edge["reviewed_at"])
            self.assertEqual("unassigned", edge["review_owner"])
            self.assertEqual("ai_assisted_source_check", edge["research_recommendation"]["assessment_method"])

    def test_shared_node_matches_ide005_exactly(self):
        self.assertEqual([], check_shared_candidate_nodes(releases()))
        mine = next(n for n in read(RELEASE)["candidate_nodes"] if n["id"] == "tech-nvidia-gb200-nvl72")
        theirs = next(n for n in read(POWER_RELEASE)["candidate_nodes"] if n["id"] == "tech-nvidia-gb200-nvl72")
        self.assertEqual(theirs, mine)

    def test_research_material_is_excluded_from_the_site(self):
        self.assertEqual([], check_pages_exclusion(WORKFLOW, RESEARCH))
        self.assertIn("--exclude='data/research'", WORKFLOW.read_text(encoding="utf-8"))
        self.assertTrue(DOSSIER.is_relative_to(RESEARCH))


class PageTests(unittest.TestCase):
    def test_figure_counts_match_the_dossier(self):
        page = PAGE.read_text(encoding="utf-8")
        svg = re.search(r'<svg viewBox="0 0 900 430".*?</svg>', page, re.S).group(0)
        values = [int(v) for v in re.findall(r'class="f-val"[^>]*>(\d+)<', svg)]
        self.assertEqual(len(read(DOSSIER)["requirements"]), sum(values))

    def test_every_dossier_requirement_appears_on_the_page(self):
        page = PAGE.read_text(encoding="utf-8")
        for r in read(DOSSIER)["requirements"]:
            self.assertIn(f"<code>{r['id']}</code>", page)

    def test_matrix_has_every_required_column(self):
        text = html.unescape(PAGE.read_text(encoding="utf-8"))
        for col in ("Required capability", "Dependency", "Evidence type", "Existing primary evidence", "What it establishes",
                    "Does not establish", "Missing evidence", "Contradictions or gaps recorded", "Verification method", "Next action"):
            self.assertIn(f'<th scope="col">{col}</th>', text, col)

    def test_canonical_url_and_ontology_ids_preserved(self):
        page = PAGE.read_text(encoding="utf-8")
        self.assertIn('<link rel="canonical" href="https://aielectronicchips.com/ai-chip-infrastructure/">', page)
        data = json.loads(re.search(r'<script type="application/ld\+json">(.*?)</script>', page, re.S).group(1))
        ids = {n["@id"] for n in data["@graph"]}
        self.assertEqual({"https://aielectronicchips.com/ai-chip-infrastructure/#webpage",
                          "https://aielectronicchips.com/ai-chip-infrastructure/#deployment"}, ids)
        term = next(n for n in data["@graph"] if n["@type"] == "DefinedTerm")
        self.assertEqual("08", term["termCode"])

    def test_workload_orchestration_claim_is_version_scoped(self):
        release = read(RELEASE)
        finding = next(f for f in release["findings"] if f["id"] == "d-sw-stack")
        self.assertIn("2025", finding["statement"])
        self.assertIn("Kubernetes (K8s) through RunAI", finding["statement"])
        self.assertIn("nvidia-mission-control-rack-setup-guide-2026",
                      {e["source_id"] for e in finding["evidence"]})
        candidate = next(c for c in release["candidate_relationships"]
                         if c["id"] == "rel-dgx-superpod-gb200-requires-cluster-management")
        self.assertIn("version", candidate["statement"])
        dossier_req = requirement(read(DOSSIER), "req-sw-management-stack")
        self.assertIn("Kubernetes", dossier_req["required_capability"])
        page = PAGE.read_text(encoding="utf-8")
        self.assertIn("newer rack-setup guide", page)
        self.assertIn("RunAI", page)
        self.assertNotIn("DGX SuperPOD only supports Slurm", page)

    def test_no_scores_percentages_or_approvals_on_the_page(self):
        text = re.sub(r"<[^>]+>", " ", PAGE.read_text(encoding="utf-8").split("<main", 1)[1])
        self.assertNotRegex(text, r"\d+\s?%")
        self.assertNotRegex(text, r"(?i)readiness score|approved by|certified")


if __name__ == "__main__":
    unittest.main()
