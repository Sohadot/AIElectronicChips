"""Regression tests for IDE-007: cross-layer reference pathways, the evidence explorer and cross-release consistency."""

from __future__ import annotations

import copy
import json
import re
import sys
import tempfile
import unittest
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import render_reference_pathways as render  # noqa: E402
from validate_evidence_releases import check_cross_release_consistency  # noqa: E402
from validate_reference_pathways import (  # noqa: E402
    EXPECTED_PATHWAYS,
    check_explorer_page,
    check_model,
    load_context,
)

MODEL = ROOT / "data" / "reference-pathways.json"
PAGE = ROOT / "sovereignty-stack" / "index.html"
TODAY = date(2026, 11, 10)


def model():
    return json.loads(MODEL.read_text(encoding="utf-8"))


def errors(m):
    registry, atlas, releases = load_context()
    return check_model(m, registry, atlas, releases, today=TODAY)


def pathway(m, pid):
    return next(p for p in m["pathways"] if p["id"] == pid)


def step(m, sid):
    return next(s for p in m["pathways"] for s in p["steps"] if s["id"] == sid)


A, B, C = EXPECTED_PATHWAYS


class ModelValidityTests(unittest.TestCase):
    def test_model_is_valid(self):
        self.assertEqual([], errors(model()))

    def test_exactly_the_three_prescribed_pathways(self):
        m = model()
        self.assertEqual(EXPECTED_PATHWAYS, [p["id"] for p in m["pathways"]])
        for mutate in (lambda m: m["pathways"].pop(), lambda m: m["pathways"].reverse(),
                       lambda m: m["pathways"].append(copy.deepcopy(m["pathways"][0]))):
            bad = model()
            mutate(bad)
            self.assertTrue(any("exactly the IDE-007 set" in e for e in errors(bad)))

    def test_research_questions_are_the_prescribed_ones(self):
        m = model()
        self.assertIn("high-bandwidth memory architecture and advanced packaging interact", pathway(m, A)["research_question"])
        self.assertIn("why are their published performance figures not automatically comparable", pathway(m, B)["research_question"])
        self.assertIn("installed, commissioned, and operational computing infrastructure", pathway(m, C)["research_question"])

    def test_every_step_is_complete(self):
        for p in model()["pathways"]:
            self.assertGreaterEqual(len(p["steps"]), 5)
            for s in p["steps"]:
                self.assertTrue(s["relevance"] and s["limitations"] and s["source_ids"] and s["finding_ids"], s["id"])


class TraceabilityTests(unittest.TestCase):
    def expect(self, mutate, fragment):
        bad = model()
        mutate(bad)
        errs = errors(bad)
        self.assertTrue(any(fragment in e for e in errs), (fragment, errs[:5]))

    def test_unknown_ontology_layer_rejected(self):
        self.expect(lambda m: pathway(m, A)["ontology_layers"].append("quantum"), "governed ontology layers")

    def test_step_layer_must_belong_to_pathway(self):
        self.expect(lambda m: step(m, "a1-interface-standard").update(ontology_layer="deployment"), "pathway's layers")

    def test_route_must_exist(self):
        self.expect(lambda m: step(m, "a1-interface-standard").update(route="/hbm4-memory/"), "not an existing public route")

    def test_anchor_must_resolve(self):
        self.expect(lambda m: step(m, "a1-interface-standard").update(anchor="no-such-section"), "does not resolve")

    def test_step_must_sit_on_its_release_page(self):
        self.expect(lambda m: step(m, "a1-interface-standard").update(route="/interconnects/", anchor="hierarchy"), "is presented on")

    def test_finding_must_belong_to_named_release(self):
        self.expect(lambda m: step(m, "a1-interface-standard")["finding_ids"].append("p-cowos-s"), "is not in release")

    def test_unregistered_source_rejected(self):
        self.expect(lambda m: step(m, "a1-interface-standard")["source_ids"].append("jedec-hbm5-2030"), "is not registered")

    def test_source_must_be_behind_the_findings(self):
        # Registered and cited on the HBM page, but not by the step's findings: a page may not be cited for what its findings do not rest on.
        self.expect(lambda m: step(m, "a1-interface-standard")["source_ids"].append("micron-fy2026-form-10-k"),
                    "not cited by any of the step's findings")

    def test_source_must_be_cited_on_the_page(self):
        def mutate(m):
            s = step(m, "a6-product-case")
            s["finding_ids"].append("p-cowos-s")
            s["source_ids"].append("jedec-jesd270-4-hbm4-standard-2025")
        self.expect(mutate, "not in the references of /design-fabrication-packaging/")

    def test_evidence_class_must_match_findings(self):
        self.expect(lambda m: step(m, "a1-interface-standard").update(evidence_class="verified_fact"), "not the class of any finding")

    def test_unresolved_reference_must_exist(self):
        self.expect(lambda m: step(m, "a1-interface-standard")["unresolved_ids"].append("u-invented"), "unresolved_ids must name")

    def test_limitations_required(self):
        self.expect(lambda m: step(m, "b1-stack-bandwidth").update(limitations=[]), "limitations must be a non-empty list")

    def test_open_questions_need_next_evidence(self):
        self.expect(lambda m: step(m, "c3-electrical").update(next_evidence=""), "must name the next evidence")

    def test_statement_class_must_match_basis(self):
        self.expect(lambda m: pathway(m, A)["statements"][0].update(classification="bounded_analysis"), "no basis finding has that class")

    def test_not_supported_must_be_a_negation(self):
        self.expect(lambda m: pathway(m, A)["statements"][-1].update(text="MI300X packaging evidence carries over to HBM4 products."),
                    "worded as a negation")


class BoundaryTests(unittest.TestCase):
    def expect(self, mutate, fragment):
        bad = model()
        mutate(bad)
        self.assertTrue(any(fragment in e for e in errors(bad)), fragment)

    def test_unpublished_candidates_never_appear(self):
        registry, atlas, releases = load_context()
        text = MODEL.read_text(encoding="utf-8")
        for r in releases.values():
            for edge in r["candidate_relationships"]:
                self.assertNotIn(edge["id"], text)
            for node in r["candidate_nodes"]:
                self.assertNotIn(node["id"], text)
        self.expect(lambda m: step(m, "c6-software").update(
            relevance="See rel-gb200-nvl72-requires-rack-firmware-baseline for the dependency."), "unpublished research candidate")
        self.expect(lambda m: step(m, "c1-rack-architecture").update(title="tech-nvidia-gb200-nvl72"), "unpublished research candidate")

    def test_no_edges_approvals_or_scores(self):
        for key in ("relation_type", "from", "to", "approved_by", "approval", "score", "readiness", "ranking", "confidence",
                    "reviewed_at", "certified"):
            with self.subTest(key):
                self.expect(lambda m, k=key: step(m, "a1-interface-standard").update({k: "x"}), "is not allowed")

    def test_no_verdict_language(self):
        for text in ("The rack has a readiness score of 4.", "Pathway C is 80% complete.", "This is an approved dependency.",
                     "Ranked first among packaging routes."):
            with self.subTest(text):
                self.expect(lambda m, t=text: step(m, "c9-evidence-states").update(relevance=t), "verdict or score language")

    def test_deployment_boundaries_apply_to_pathway_text(self):
        self.expect(lambda m: step(m, "c9-evidence-states").update(
            relevance="The DGX SuperPOD reference architecture is deployed at the site."), "reference design")
        self.expect(lambda m: step(m, "c9-evidence-states").update(
            relevance="The completed checklist is an approval of the deployment."), "checklist or assessment")

    def test_review_and_status_cannot_be_promoted(self):
        self.expect(lambda m: m.update(scientific_review="complete"), "scientific_review must be 'pending'")
        self.expect(lambda m: m.update(status="approved"), "status must be 'reference_navigation'")
        self.expect(lambda m: m.update(boundary="Pathways are verified dependencies."), "not an Atlas relationship")

    def test_evidence_ladder_cannot_mark_site_states_reviewed(self):
        def mutate(m):
            row = next(r for r in pathway(m, C)["evidence_ladder"] if r["state"] == "subsystem_commissioned")
            row["reviewed"] = True
        self.expect(mutate, "cannot be marked reviewed")
        self.expect(lambda m: pathway(m, C)["evidence_ladder"].reverse(), "governed evidence states in order")

    def test_atlas_untouched(self):
        _, atlas, _ = load_context()
        self.assertEqual([], atlas["relationships"])
        self.assertEqual(8, len(atlas["nodes"]))


class ScientificContentTests(unittest.TestCase):
    def test_comparison_figures_trace_to_findings(self):
        bad = model()
        pathway(bad, B)["comparisons"][0]["figures"][0] = {"value": "896 GB/s", "finding_id": "f-nv-rubin"}
        self.assertTrue(any("does not appear in finding" in e for e in errors(bad)))

    def test_amd_896_is_never_a_valid_comparison(self):
        for cmp in pathway(model(), B)["comparisons"]:
            if any(f["value"] == "896 GB/s" for f in cmp["figures"]):
                self.assertEqual("unsupported", cmp["verdict"])
                self.assertIn("per GPU or per platform", cmp["reason"])

    def test_cross_generation_and_cross_scope_comparisons_are_not_valid(self):
        verdicts = {c["id"]: c["verdict"] for c in pathway(model(), B)["comparisons"]}
        self.assertEqual("unsupported", verdicts["cmp-rack-vs-gpu"])
        self.assertEqual("conditional", verdicts["cmp-mi300x-vs-rubin-memory"])
        self.assertEqual("conditional", verdicts["cmp-rubin-22-vs-19"])
        self.assertIn("valid", verdicts.values())

    def test_pathway_a_keeps_generation_and_qualification_boundaries(self):
        p = pathway(model(), A)
        self.assertTrue(any("MI300X uses HBM3" in lim for lim in p["limitations"]))
        open_ids = {u for s in p["steps"] for u in s["unresolved_ids"]}
        self.assertLessEqual({"u-qualification", "u-interposer-substrate", "u-jedec-text", "u-p-mi300x-cowos-variant"}, open_ids)

    def test_pathway_c_preserves_ide005_and_ide006_boundaries(self):
        p = pathway(model(), C)
        open_ids = {u for s in p["steps"] for u in s["unresolved_ids"]}
        self.assertLessEqual({"u-pt-redundancy-conflict", "u-pt-bus-bar-paths", "u-pt-120kw-basis", "u-pt-scalable-unit-remainder",
                              "u-pt-coolant-specification", "u-d-firmware-guide", "u-d-software-versions", "u-d-acceptance-criteria",
                              "u-d-site-records"}, open_ids)
        sw = step(model(), "c6-software")
        self.assertTrue(any("Kubernetes through RunAI" in lim for lim in sw["limitations"]))
        reviewed = [r["state"] for r in p["evidence_ladder"] if r["reviewed"]]
        self.assertEqual(["product_specification_documented", "infrastructure_proposed", "not_established"], reviewed)
        self.assertNotIn("Rubin", json.dumps(p["steps"]))


class ExplorerPageTests(unittest.TestCase):
    def test_page_matches_the_model(self):
        current = PAGE.read_text(encoding="utf-8")
        self.assertEqual(current, render.apply(current, render.render(*render.load())))
        self.assertEqual([], check_explorer_page(model()))

    def test_explorer_check_catches_a_missing_step(self):
        m = model()
        step(m, "b5-scale-up")["anchor"] = "matrix"
        self.assertTrue(any("b5-scale-up" in e for e in check_explorer_page(m)))

    def test_content_needs_no_javascript(self):
        text = PAGE.read_text(encoding="utf-8")
        scripts = re.findall(r"<script\b[^>]*>", text)
        self.assertEqual(['<script type="application/ld+json">'], scripts)
        for p in model()["pathways"]:
            for s in p["steps"]:
                self.assertIn(f'id="step-{s["id"]}"', text)
        self.assertGreaterEqual(text.count('<details class="evidence-trace">'), 25)

    def test_structured_data_lists_the_pathways(self):
        text = PAGE.read_text(encoding="utf-8")
        data = json.loads(re.search(r'<script type="application/ld\+json">(.*?)</script>', text, re.S).group(1))
        items = next(n for n in data["@graph"] if n.get("@type") == "ItemList")["itemListElement"]
        self.assertEqual([f"https://aielectronicchips.com/sovereignty-stack/#{p}" for p in EXPECTED_PATHWAYS], [i["url"] for i in items])
        self.assertIn('<link rel="canonical" href="https://aielectronicchips.com/sovereignty-stack/">', text)
        ontology = next(n for n in data["@graph"] if n.get("@id", "").endswith("#ontology"))
        self.assertEqual(8, len(ontology["hasDefinedTerm"]))

    def test_diagnostic_engine_is_separate(self):
        self.assertNotIn("chip-dependency", MODEL.read_text(encoding="utf-8"))
        for path in (ROOT / "chip-dependency-map" / "index.html", ROOT / "assets" / "js" / "chip-dependency-map.js"):
            self.assertNotIn("reference-pathways", path.read_text(encoding="utf-8"))
        cdm = json.loads((ROOT / "data" / "chip-dependency-model.json").read_text(encoding="utf-8"))
        self.assertEqual(12, len(cdm["questions"]))


class CrossReleaseConsistencyTests(unittest.TestCase):
    def releases(self):
        _, _, releases = load_context()
        return releases

    def test_releases_are_consistent_now(self):
        self.assertEqual([], check_cross_release_consistency(self.releases()))

    def test_duplicate_ids_and_edges_across_releases_are_caught(self):
        rel = copy.deepcopy(self.releases())
        a, b = list(rel)[:2]
        rel[b]["findings"].append(copy.deepcopy(rel[a]["findings"][0]))
        rel[b]["candidate_relationships"].append(dict(copy.deepcopy(rel[a]["candidate_relationships"][0]), id="rel-copy"))
        errs = check_cross_release_consistency(rel)
        self.assertTrue(any("already used" in e for e in errs))
        self.assertTrue(any("duplicates one proposed" in e for e in errs))

    def test_stale_sitemap_lastmod_is_caught(self):
        stale = re.sub(r"(/interconnects/</loc><lastmod>)[0-9-]+", r"\g<1>2026-07-03", (ROOT / "sitemap.xml").read_text(encoding="utf-8"))
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "sitemap.xml"
            path.write_text(stale, encoding="utf-8")
            errs = check_cross_release_consistency(self.releases(), path)
        self.assertTrue(any("/interconnects/" in e and "predates" in e for e in errs))


if __name__ == "__main__":
    unittest.main()
