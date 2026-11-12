"""Regression tests for IDE-008: source inspections, the conflict register, the impact index and their public surfaces.

All tests run offline. The inspection command is exercised with a fake fetcher; CI never depends on third-party sites.
"""

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
import inspect_sources  # noqa: E402
import render_evidence_maintenance as render_sources  # noqa: E402
import render_reference_pathways as render_pathways  # noqa: E402
from validate_evidence_maintenance import (  # noqa: E402
    CONFLICT_STATES,
    INSPECTION_STATES,
    _content_checks,
    build_impact,
    check_all,
    check_conflicts,
    check_inspections,
    context,
    metadata_issues,
)

TODAY = date(2026, 11, 12)


def load(name):
    return json.loads((ROOT / "data" / name).read_text(encoding="utf-8"))


def ctx():
    registry, releases, pathways, dossiers = context()
    return registry, releases, pathways, dossiers, load("source-inspections.json"), load("evidence-conflicts.json")


def record(log, sid):
    return next(r for r in log["records"] if r["source_id"] == sid)


def issue(reg, iid):
    return next(c for c in reg["issues"] if c["id"] == iid)


class CommittedStateTests(unittest.TestCase):
    def test_everything_validates(self):
        self.assertEqual([], check_all(TODAY))

    def test_every_registry_record_is_accounted_for(self):
        registry, *_ = context()
        log = load("source-inspections.json")
        self.assertEqual(sorted(registry), sorted({r["source_id"] for r in log["records"]}))
        self.assertEqual(76, len(registry))

    def test_states_are_kept_distinct(self):
        log = load("source-inspections.json")
        self.assertEqual(INSPECTION_STATES, list(log["state_definitions"]))
        for r in log["records"]:
            self.assertFalse({"source_retrieved", "source_inaccessible"} <= set(r["states"]), r["source_id"])
            self.assertNotIn("verified", json.dumps(r).lower().replace("unverified", ""))

    def test_pending_sources_stay_pending_with_an_outcome(self):
        registry, *_ = context()
        log = load("source-inspections.json")
        for sid in ("asml-2024-annual-reports", "ucie-2-specification-release-2024"):
            self.assertEqual("pending_review", registry[sid]["status"])
            r = record(log, sid)
            self.assertIn("review_required", r["states"])
            self.assertTrue(r["next_action"].startswith("Keep pending_review"))

    def test_inspection_did_not_rewrite_access_dates(self):
        registry, *_ = context()
        # Retrieved in this run but not re-used for a claim: the registry access date stays the claim-work date.
        self.assertEqual("2026-11-09", registry["nvidia-rubin-platform-architecture-2026"]["accessed_at"])
        self.assertEqual("2026-11-09", registry["amd-cdna3-white-paper-2025"]["accessed_at"])
        self.assertEqual("2026-06-14", registry["ucie-2-specification-release-2024"]["accessed_at"])


class InspectionValidationTests(unittest.TestCase):
    def expect(self, mutate, fragment, registry_mutate=None):
        registry, *_ = context()
        log = copy.deepcopy(load("source-inspections.json"))
        mutate(log)
        if registry_mutate:
            registry = copy.deepcopy(registry)
            registry_mutate(registry)
        errs = check_inspections(log, registry, TODAY)
        self.assertTrue(any(fragment in e for e in errs), (fragment, errs[:4]))

    def test_metadata_validated_must_match_recomputed_checks(self):
        self.expect(lambda log: None, "metadata_issues do not match",
                    registry_mutate=lambda r: r["jedec-jesd270-4-hbm4-standard-2025"].update(canonical_url="https://www.jedec.org/news/"))

    def test_listing_page_url_is_a_metadata_issue(self):
        self.assertIn("canonical_url points to a listing page, not the document",
                      metadata_issues({**load("source-registry.json")["source_records"][0], "canonical_url": "https://www.uciexpress.org/press-releases"}))

    def test_retrieved_needs_a_successful_retrieval(self):
        self.expect(lambda log: record(log, "asml-2024-annual-reports")["states"].insert(1, "source_retrieved"), "source_retrieved must be present")

    def test_compared_needs_a_passage_check(self):
        self.expect(lambda log: record(log, "jedec-jesd270-4-hbm4-standard-2025").update(passage_check=None), "needs a retrieval and a passage check")

    def test_missing_passages_require_review(self):
        def mutate(log):
            r = record(log, "jedec-jesd270-4-hbm4-standard-2025")
            r["passage_check"]["not_found"] = [{"finding_id": "f-std-interface", "passage": "x"}]
        self.expect(mutate, "passages not found require review_required")

    def test_changed_needs_documentation(self):
        self.expect(lambda log: record(log, "jedec-jesd270-4-hbm4-standard-2025")["states"].insert(3, "source_changed"), "source_changed needs")

    def test_inaccessible_cannot_have_succeeded(self):
        self.expect(lambda log: record(log, "jedec-jesd270-4-hbm4-standard-2025")["states"].append("source_inaccessible"), "source_inaccessible needs")

    def test_every_source_needs_a_record(self):
        def drop(log):
            sid = log["records"][-1]["source_id"]
            log["records"] = [r for r in log["records"] if r["source_id"] != sid]
        self.expect(drop, "has no record")

    def test_dates_and_chronology(self):
        self.expect(lambda log: record(log, "jedec-jesd270-4-hbm4-standard-2025").update(inspected_at="2027-01-01"), "inspected_at must be")
        self.expect(lambda log: log["runs"][0].update(inspected_at="2020-01-01"), "inspected_at must be the run's date")

    def test_no_review_or_score_fields(self):
        leaked: set[str] = set()
        for key in ("verified", "freshness_score", "reviewer", "risk_level", "approved"):
            with self.subTest(key):
                log = copy.deepcopy(load("source-inspections.json"))
                log["records"][0][key] = True
                self.assertTrue(any("is not allowed" in e for e in _content_checks(log, "x", leaked)))
        log = copy.deepcopy(load("source-inspections.json"))
        log["records"][0]["notes"] = ["The source was fully verified and scientifically reviewed."]
        self.assertTrue(any("review-completion language" in e for e in _content_checks(log, "x", leaked)))


class ConflictValidationTests(unittest.TestCase):
    def expect(self, iid, mutate, fragment):
        registry, releases, pathways, _, log, reg = ctx()
        reg = copy.deepcopy(reg)
        mutate(issue(reg, iid))
        errs = check_conflicts(reg, registry, releases, pathways, log, TODAY)
        self.assertTrue(any(fragment in e for e in errs), (fragment, errs[:4]))

    def test_register_covers_the_priority_subjects(self):
        ids = {c["id"] for c in load("evidence-conflicts.json")["issues"]}
        self.assertEqual({"ec-rubin-memory-bandwidth", "ec-nvlink6-per-gpu", "ec-mi300x-infinity-fabric-scope", "ec-cowos-l-5p5-reticle",
                          "ec-hbm4-package-qualification", "ec-gb200-power-redundancy", "ec-gb200-busbar-rack-power", "ec-scalable-unit-power",
                          "ec-gb200-coolant-specification", "ec-mission-control-orchestration-versions", "ec-hbm-export-control-currency"}, ids)
        self.assertEqual(CONFLICT_STATES, list(load("evidence-conflicts.json")["state_definitions"]))

    def test_resolution_needs_evidence_history_and_review_targets(self):
        self.expect("ec-gb200-power-redundancy", lambda c: c.update(state="resolved_with_evidence"), "needs a 'resolved' history entry")
        self.expect("ec-cowos-l-5p5-reticle", lambda c: c.update(state="resolved_with_evidence"), "needs primary evidence")
        self.expect("ec-mi300x-infinity-fabric-scope", lambda c: c.update(state="resolved_with_evidence", downstream_review=[]),
                    "must name the public statements")

    def test_newer_finding_source_alone_cannot_resolve(self):
        def mutate(c):
            c["state"] = "resolved_with_evidence"
            c["history"].append({"date": "2026-11-11", "event": "resolved", "detail": "Newer article chosen."})
            c["downstream_review"] = ["x"]
            c["evidence"] = [e for e in c["evidence"] if e["source_id"] not in {"nvidia-vera-rubin-nvl72-product-page-2026",
                                                                                "nvidia-hgx-platform-product-page-2026"}]
        self.expect("ec-rubin-memory-bandwidth", mutate, "evidence beyond the findings")

    def test_unresolved_issues_state_what_is_unknown(self):
        self.expect("ec-gb200-power-redundancy", lambda c: c.update(unknown=[]), "must state what remains unknown")

    def test_open_conflict_needs_two_sources(self):
        def mutate(c):
            c["finding_ids"], c["evidence"] = ["pt-gb-power-shelves"], [c["evidence"][0]]
        self.expect("ec-gb200-power-redundancy", mutate, "at least two sources")

    def test_access_blocked_needs_an_inaccessible_source(self):
        self.expect("ec-cowos-l-5p5-reticle", lambda c: c.update(source_ids=["amd-cdna3-white-paper-2025"]), "recorded as inaccessible")

    def test_evidence_must_come_from_retrieved_sources(self):
        def mutate(c):
            c["source_ids"].append("tsmc-2025-annual-report")
            c["evidence"].append({"source_id": "tsmc-2025-annual-report", "locator": "x", "observation": "y"})
        self.expect("ec-gb200-power-redundancy", mutate, "source this inspection retrieved")

    def test_quotes_stay_short(self):
        self.expect("ec-gb200-power-redundancy", lambda c: c["evidence"][0].update(locator='"' + " ".join(["word"] * 21) + '"'), "exceeds 20 words")

    def test_references_must_resolve(self):
        self.expect("ec-gb200-power-redundancy", lambda c: c["affected_references"].append("/power-and-thermal-limits/#no-such"), "does not resolve")
        self.expect("ec-gb200-power-redundancy", lambda c: c["affected_pathway_steps"].append("c99-none"), "does not exist")
        self.expect("ec-gb200-power-redundancy", lambda c: c["finding_ids"].append("pt-invented"), "does not exist in any release")
        self.expect("ec-gb200-power-redundancy", lambda c: c["unresolved_ids"].append("u-invented"), "does not exist")

    def test_history_must_be_ordered(self):
        self.expect("ec-rubin-memory-bandwidth", lambda c: c["history"].reverse(), "must be valid, ordered")

    def test_missing_evidence_posture_is_negative(self):
        self.expect("ec-gb200-coolant-specification", lambda c: c.update(posture="The coolant is PG25 at 25 C."), "must say what is not established")

    def test_content_rules_apply_to_the_register(self):
        reg = copy.deepcopy(load("evidence-conflicts.json"))
        issue(reg, "ec-scalable-unit-power")["posture"] = "The DGX SuperPOD reference architecture is deployed at the site."
        self.assertTrue(any("reference design" in e for e in _content_checks(reg, "x", set())))
        reg = copy.deepcopy(load("evidence-conflicts.json"))
        issue(reg, "ec-scalable-unit-power")["posture"] = "See rel-gb200-nvl72-requires-rack-firmware-baseline."
        self.assertTrue(any("unpublished research candidate" in e
                            for e in _content_checks(reg, "x", {"rel-gb200-nvl72-requires-rack-firmware-baseline"})))

    def test_review_status_cannot_be_promoted(self):
        registry, releases, pathways, _, log, reg = ctx()
        reg = copy.deepcopy(reg)
        reg["scientific_review"] = "complete"
        self.assertTrue(any("scientific_review 'pending'" in e for e in check_conflicts(reg, registry, releases, pathways, log, TODAY)))


class ScientificContentTests(unittest.TestCase):
    def test_rubin_figures_are_not_resolved_by_recency(self):
        c = issue(load("evidence-conflicts.json"), "ec-rubin-memory-bandwidth")
        self.assertEqual("requires_reassessment", c["state"])
        self.assertTrue({"nvidia-rubin-platform-architecture-2026", "nvidia-co-design-memory-2026",
                         "nvidia-vera-rubin-nvl72-product-page-2026"} <= set(c["source_ids"]))
        self.assertIn("22 TB/s", c["posture"])
        self.assertIn("19.2 TB/s", c["posture"])

    def test_mi300x_resolution_preserves_history(self):
        c = issue(load("evidence-conflicts.json"), "ec-mi300x-infinity-fabric-scope")
        # IDE-008 resolved it from arithmetic; IDE-009 reopened it because AMD never states the per-GPU scope.
        self.assertEqual("requires_reassessment", c["state"])
        events = [h["event"] for h in c["history"]]
        self.assertIn("resolved", events)
        self.assertIn("reopened", events)
        self.assertGreater(events.index("reopened"), events.index("resolved"))
        self.assertIn("amd-instinct-mi300x-data-sheet-2025", {e["source_id"] for e in c["evidence"]})
        self.assertTrue(c["unknown"], "remaining uncertainty must stay visible")
        rel = json.loads((ROOT / "data" / "research" / "interconnect-evidence-release-004.json").read_text(encoding="utf-8"))
        self.assertIn("u-i-amd-link-scope", {u["id"] for u in rel["unresolved"]})
        topo = next(f for f in rel["findings"] if f["id"] == "i-amd-mi300x-topology")
        self.assertIn("does not state the direction", topo["limitations"][0])

    def test_gb200_issues_stay_open_on_current_documents(self):
        reg = load("evidence-conflicts.json")
        self.assertEqual("open_conflict", issue(reg, "ec-gb200-power-redundancy")["state"])
        for iid in ("ec-gb200-busbar-rack-power", "ec-scalable-unit-power", "ec-gb200-coolant-specification"):
            self.assertEqual("missing_primary_evidence", issue(reg, iid)["state"])

    def test_software_versions_are_scope_not_contradiction(self):
        c = issue(load("evidence-conflicts.json"), "ec-mission-control-orchestration-versions")
        self.assertEqual("version_scope_difference", c["state"])
        self.assertIn("not a scientific contradiction", c["posture"])

    def test_regulatory_issue_gives_no_legal_conclusion(self):
        c = issue(load("evidence-conflicts.json"), "ec-hbm-export-control-currency")
        self.assertIn("no legal", c["posture"])
        self.assertTrue({"ecfr-15-cfr-742-6-2026", "ecfr-15-cfr-740-25-2024"} <= {e["source_id"] for e in c["evidence"]})

    def test_atlas_and_pathways_untouched(self):
        self.assertEqual([], load("dependency-atlas.json")["relationships"])
        pw = load("reference-pathways.json")
        self.assertEqual(25, sum(len(p["steps"]) for p in pw["pathways"]))
        cmp = next(c for p in pw["pathways"] for c in p.get("comparisons", []) if c["id"] == "cmp-mi300x-p2p-vs-nvlink6")
        self.assertEqual("unsupported", cmp["verdict"], "verdicts change only after editorial review, not automatically")


class ImpactIndexTests(unittest.TestCase):
    def test_index_is_generated_and_complete(self):
        registry, releases, pathways, dossiers, log, reg = ctx()
        self.assertEqual(load("evidence-impact-index.json"), build_impact(registry, releases, pathways, dossiers, log, reg))
        self.assertEqual(sorted(registry), [e["source_id"] for e in load("evidence-impact-index.json")["sources"]])

    def test_traces_source_to_finding_page_and_pathway(self):
        e = next(x for x in load("evidence-impact-index.json")["sources"] if x["source_id"] == "nvidia-dgx-gb-rack-user-guide-2026")
        self.assertIn("pt-gb-power-shelves", e["direct"]["findings"])
        self.assertIn("/power-and-thermal-limits/", e["direct"]["reference_pages"])
        self.assertIn("c3-electrical", e["direct"]["pathway_steps"])
        self.assertIn("ec-gb200-power-redundancy", e["conflicts"])
        self.assertIn("u-pt-redundancy-conflict", e["contextual"]["unresolved_checked"])

    def test_change_detection_follows_the_data(self):
        registry, releases, pathways, dossiers, log, reg = ctx()
        pathways = copy.deepcopy(pathways)
        pathways["pathways"][0]["steps"][0]["source_ids"].append("tsmc-2025-annual-report")
        e = next(x for x in build_impact(registry, releases, pathways, dossiers, log, reg)["sources"] if x["source_id"] == "tsmc-2025-annual-report")
        self.assertIn("a1-interface-standard", e["direct"]["pathway_steps"])

    def test_no_candidates_or_scores_in_the_index(self):
        text = (ROOT / "data" / "evidence-impact-index.json").read_text(encoding="utf-8")
        for r in (ROOT / "data" / "research").glob("*.json"):
            for edge in json.loads(r.read_text(encoding="utf-8"))["candidate_relationships"]:
                self.assertNotIn(edge["id"], text)
        self.assertNotRegex(text, r'"(?:score|risk|urgency|probability)\w*"')


class InspectorTests(unittest.TestCase):
    """The inspection command, offline: a fake fetcher stands in for the network."""

    def source(self, sid="jedec-jesd270-4-hbm4-standard-2025"):
        registry, *_ = context()
        return registry[sid]

    def test_found_passages_are_compared_not_approved(self):
        passages = [p["passage"] for p in inspect_sources.quoted_passages("jedec-jesd270-4-hbm4-standard-2025")]
        body = ("<html><body>" + " ".join(passages) + "</body></html>").encode()
        r = inspect_sources.inspect(self.source(), "2026-11-10", lambda url: (200, url, "text/html", body))
        self.assertEqual(["metadata_validated", "source_retrieved", "source_content_compared"], r["states"])
        self.assertEqual(len(passages), r["passage_check"]["found"])

    def test_missing_passage_means_review_not_change(self):
        r = inspect_sources.inspect(self.source(), "2026-11-10", lambda url: (200, url, "text/html", b"<html>revised page</html>"))
        self.assertIn("review_required", r["states"])
        self.assertNotIn("source_changed", r["states"])

    def test_refusal_is_recorded_as_inaccessible(self):
        r = inspect_sources.inspect(self.source(), "2026-11-10", lambda url: (403, url, "text/html", b""))
        self.assertIn("source_inaccessible", r["states"])
        self.assertIsNone(r["passage_check"])

    def test_network_failure_is_an_observation(self):
        def boom(url):
            raise OSError("unreachable")
        r = inspect_sources.inspect(self.source(), "2026-11-10", boom)
        self.assertEqual("failed", r["retrievals"][0]["outcome"])

    def test_typographic_fallback_is_counted_separately(self):
        passages = [p["passage"] for p in inspect_sources.quoted_passages("jedec-jesd270-4-hbm4-standard-2025")]
        body = " ".join(p.replace(" ", " ® ") for p in passages).encode()
        r = inspect_sources.inspect(self.source(), "2026-11-10", lambda url: (200, url, "text/html", body))
        self.assertEqual(len(passages), r["passage_check"]["found_after_character_fallback"])

    def test_inspector_never_writes_the_registry(self):
        before = (ROOT / "data" / "source-registry.json").read_bytes()
        inspect_sources.inspect(self.source(), "2026-11-10", lambda url: (200, url, "text/html", b"x"))
        self.assertEqual(before, (ROOT / "data" / "source-registry.json").read_bytes())


class PublicSurfaceTests(unittest.TestCase):
    def test_sources_page_matches_the_files(self):
        self.assertTrue(render_sources.in_sync())
        text = (ROOT / "sources" / "index.html").read_text(encoding="utf-8")
        for c in load("evidence-conflicts.json")["issues"]:
            self.assertIn(f'id="{c["id"]}"', text)
        for f in ("source-inspections.json", "evidence-conflicts.json", "evidence-impact-index.json"):
            self.assertIn(f'href="/data/{f}"', text)
        self.assertEqual(['<script type="application/ld+json">'], re.findall(r"<script\b[^>]*>", text))
        self.assertIn('"@id": "https://aielectronicchips.com/sources/#registry"', text)
        self.assertIn('<link rel="canonical" href="https://aielectronicchips.com/sources/">', text)

    def test_sources_page_has_no_universal_freshness_score(self):
        text = (ROOT / "sources" / "index.html").read_text(encoding="utf-8").lower()
        self.assertNotRegex(text, r"freshness score|readiness score|\b\d+\s?% (?:fresh|verified)")

    def test_pathway_steps_link_to_the_register(self):
        current = (ROOT / "sovereignty-stack" / "index.html").read_text(encoding="utf-8")
        self.assertEqual(current, render_pathways.apply(current, render_pathways.render(*render_pathways.load())))
        for c in load("evidence-conflicts.json")["issues"]:
            if c["affected_pathway_steps"]:
                self.assertIn(f'href="/sources/#{c["id"]}"', current)


if __name__ == "__main__":
    unittest.main()
