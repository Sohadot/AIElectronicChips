#!/usr/bin/env python3
"""Validate the AI rack deployment verification dossier (IDE-014).

The dossier adds a typed record model to the nine evidence states of Evidence Release 006: which record can
support which state, what it must carry, which inferences are category errors, and which requirements are
preconditions of others. This validator checks the model against the corpus and against fixed rules:

- vendor documents (specifications, reference architectures, procedures, checklist templates, performance
  descriptions) can never support a site-level state; an acceptance-criteria document cannot support acceptance;
- a site-level record type must name the site, the configuration and the date; commissioning and later
  states need method, criteria and results; operational states need an observation period; acceptance
  needs signatory authority;
- a requested document is never treated as a reviewed record: a site-level row can be 'reviewed' only if a
  registered source supports a site-record claim, and none does;
- every chain boundary can be reached by a record type; every Workflow C requirement is mapped exactly
  once; every IDE-006 requirement, finding, open question, conflict and source cited resolves;
- the requirement dependency graph is acyclic, and no dependent may hold a site-level state above its
  prerequisite's;
- no review, approval, score or certification is recorded, nothing is promoted to the Atlas, no public page
  is changed, and the generated dossier and brief match their inputs.

It checks structure, lineage and the record rules. It cannot confirm that a source says what a finding states.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(Path(__file__).resolve().parent))
from validate_evidence_maintenance import _content_checks  # noqa: E402
from validate_evidence_releases import DOSSIER_DOMAINS, EVIDENCE_STATES_ORDERED, SITE_EVIDENCE_STATES  # noqa: E402

DOSSIER = ROOT / "data" / "research" / "institutional" / "rack-deployment-verification-dossier-014.json"
IDE006_DOSSIER = ROOT / "data" / "research" / "dossiers" / "gb200-nvl72-reference-demo.json"
TOP = {"dossier_id", "schema_version", "release", "status", "review_status", "scientific_review", "review_owner", "assessment_method",
       "as_of", "interpretation_standard", "research_question", "scope", "boundary", "inputs", "attributes", "record_types", "chain",
       "domains", "dependencies", "ide006_consistency", "matrix", "findings", "review_questions", "applications", "public_reference_decision"}
STATES = [s for s in EVIDENCE_STATES_ORDERED if s != "not_established"]
RANK = {s: i for i, s in enumerate(STATES)}
# Vendor documents: they describe products and procedures, never an act at a site.
VENDOR_DOCUMENTS = {"rt-product-specification", "rt-reference-architecture", "rt-documented-procedure", "rt-checklist-template",
                    "rt-performance-specification"}
CHAIN_IDS = ["a-specification-design", "b-procurement-delivery", "c-installation", "d-commissioning", "e-acceptance", "f-operation", "g-access"]
BASES = {"published", "derived_from_published", "project_defined"}
RECORD_STATUSES = {"not_obtained", "reviewed"}
SITE_CLAIM = "site_record"
# IDE-006 evidence classifications and the record type each corresponds to in this model.
CLASSIFICATION_TYPES = {"product_specification": "rt-product-specification", "reference_design": "rt-reference-architecture",
                        "documented_procedure": "rt-documented-procedure", "regulatory_announcement": "rt-rule-text"}


def j(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def load_context():
    releases = {r["release_id"]: r for r in (j(p) for p in sorted((ROOT / "data" / "research").glob("*.json")))}
    return {"registry": {s["id"]: s for s in j(ROOT / "data" / "source-registry.json")["source_records"]}, "releases": releases,
            "issues": {i["id"]: i for i in j(ROOT / "data" / "evidence-conflicts.json")["issues"]},
            "ide006": j(IDE006_DOSSIER), "workbench": j(ROOT / "data" / "industrial-evidence-requests.json"),
            "pathways": j(ROOT / "data" / "reference-pathways.json"), "log": j(ROOT / "data" / "source-inspections.json"),
            "atlas": j(ROOT / "data" / "dependency-atlas.json")}


def nonempty(v) -> bool:
    return isinstance(v, str) and bool(v.strip())


def rank(state) -> int:
    return RANK.get(state, -1)


RESOLUTION_FIELDS = {"status", "resolved_by", "resolved_at", "previous_state", "corrected_state", "decision", "evidence_checked",
                     "uncertainty_remaining", "publication_change"}


def check_resolution(x, types, ctx) -> list[str]:
    """A flagged IDE-006 entry may be resolved only by an exact, recorded correction: the entry still names the state it
    flagged, the IDE-006 dossier now carries the corrected state within the ceiling, the evidence rechecked is the entry's own
    cited passage and was found by the named inspection run, and the public page carries the new text and not the old."""
    w = f"rack-dossier.ide006_consistency[{x.get('requirement_id')}].resolution"
    res = x["resolution"]
    if not isinstance(res, dict) or set(res) != RESOLUTION_FIELDS:
        return [f"{w} must contain exactly {sorted(RESOLUTION_FIELDS)}"]
    errors = []
    req = next((q for q in ctx["ide006"]["requirements"] if q["id"] == x.get("requirement_id")), None)
    t = types.get(x.get("record_type_id"))
    if req is None or t is None:
        return [f"{w}: requirement or record type does not exist"]
    if res["status"] != "corrected" or not str(res["resolved_by"]).startswith("IDE-") or not nonempty(res["resolved_at"]):
        errors.append(f"{w}: status 'corrected', the release that made it and a date are required")
    if res["previous_state"] != x["current_state"] or rank(x["current_state"]) <= rank(x["state_ceiling"]):
        errors.append(f"{w}: previous_state must be the flagged state the entry records, which exceeded the ceiling")
    if req["current_state"] != res["corrected_state"]:
        errors.append(f"{w}: the IDE-006 dossier must carry the corrected state {res['corrected_state']}")
    if res["corrected_state"] not in RANK or rank(res["corrected_state"]) > rank(t["state_ceiling"]):
        errors.append(f"{w}: the corrected state must be within the ceiling {t['state_ceiling']}")
    if req["evidence_classification"] != x["evidence_classification"]:
        errors.append(f"{w}: the evidence classification is not part of this correction and must be unchanged")
    ev = res["evidence_checked"]
    if not isinstance(ev, dict) or {"source_id": ev.get("source_id"), "locator": ev.get("locator")} not in req["evidence"]:
        errors.append(f"{w}: evidence_checked must be the entry's own cited source and locator")
    else:
        rec = next((r for r in ctx["log"]["records"] if r["source_id"] == ev["source_id"] and r["run_id"] == ev.get("inspection_run_id")), None)
        if rec is None or rec["passage_check"]["not_found"] or not rec["passage_check"]["found"]:
            errors.append(f"{w}: inspection run {ev.get('inspection_run_id')} must have found the cited passage")
    for field in ("decision", "uncertainty_remaining"):
        if not nonempty(res[field]):
            errors.append(f"{w}.{field} must be stated")
    pc = res["publication_change"]
    if not isinstance(pc, dict) or set(pc) != {"route", "anchor", "old_text", "new_text"}:
        errors.append(f"{w}.publication_change must name route, anchor, old_text and new_text")
    else:
        from validate_evidence_reconciliations import norm, plain, route_file
        path = route_file(pc["route"])
        page = path.read_text(encoding="utf-8") if path.is_file() else ""
        text = norm(plain(page))
        if norm(pc["new_text"]) not in text or norm(pc["old_text"]) in text:
            errors.append(f"{w}: {pc['route']} must carry the new text and not the old")
        if f'id="{pc["anchor"]}"' not in page or "Correction, " + res["resolved_at"] not in norm(plain(page)):
            errors.append(f"{w}: {pc['route']} must show a dated correction note at #{pc['anchor']}")
    return errors


def check(d, ctx) -> list[str]:
    if not isinstance(d, dict) or set(d) != TOP:
        return ["rack-dossier: top-level fields mismatch"]
    errors: list[str] = []
    if (d["status"], d["review_status"], d["scientific_review"], d["review_owner"]) != ("research_candidate", "not_reviewed", "pending", "unassigned"):
        errors.append("rack-dossier: must stay a research candidate, not reviewed, scientific review pending, review owner unassigned")
    if d["assessment_method"] != "ai_assisted_source_check" or d["interpretation_standard"] != "AEC-CS-001":
        errors.append("rack-dossier: assessment method and interpretation standard must be the governed values")
    for phrase in ("not an assessment of any site", "records no human or scientific review", "no engineering or legal determination", "does not promote"):
        if phrase not in d["boundary"]:
            errors.append(f"rack-dossier: boundary must say '{phrase}'")
    if not d["scope"].get("site", "").startswith("None"):
        errors.append("rack-dossier: the scope must represent no site")
    inputs = d["inputs"]
    release = ctx["releases"].get(inputs["release_id"])
    if release is None or ctx["ide006"]["dossier_id"] != inputs["dossier_id"]:
        return errors + ["rack-dossier: the release and IDE-006 dossier it builds on must exist"]
    wf = next((w for w in ctx["workbench"]["workflows"] if w["id"] == inputs["workflow_id"]), None)
    if wf is None or inputs["pathway_id"] not in {p["id"] for p in ctx["pathways"]["pathways"]}:
        return errors + ["rack-dossier: workflow and pathway must exist"]
    if inputs["inspection_run_id"] not in {r["run_id"] for r in ctx["log"]["runs"]}:
        errors.append(f"rack-dossier: inspection run {inputs['inspection_run_id']} does not exist")
    findings = {f["id"] for r in ctx["releases"].values() for f in r["findings"]}
    unresolved = {u["id"] for r in ctx["releases"].values() for u in r["unresolved"]}
    refs = findings | unresolved | set(ctx["issues"])
    reqs = {q["id"]: q for q in ctx["ide006"]["requirements"]}
    site_sources = [s for s, rec in ctx["registry"].items() if SITE_CLAIM in rec.get("supported_claim_types", []) and rec.get("status") == "active"]

    # Record types.
    attrs = d["attributes"]
    types = {}
    for t in d["record_types"]:
        w = f"rack-dossier.record_type[{t.get('id')}]"
        if t["id"] in types:
            errors.append(f"{w}: duplicate id")
        types[t["id"]] = t
        ceiling, site = t["state_ceiling"], t["site_specific"]
        if t["dimension"] == "access":
            if ceiling is not None:
                errors.append(f"{w}: an access record has no technical evidence state")
        elif t["dimension"] != "technical" or ceiling not in STATES:
            errors.append(f"{w}: a technical record needs one of the governed states as its ceiling")
            continue
        if not set(t["required_attributes"]) <= set(attrs):
            errors.append(f"{w}: unknown attributes {sorted(set(t['required_attributes']) - set(attrs))}")
        if ceiling in SITE_EVIDENCE_STATES and not site:
            errors.append(f"{w}: a record that is not site-specific cannot support the site-level state {ceiling}")
        if site and not {"named_site", "configuration_identity", "dated"} <= set(t["required_attributes"]):
            errors.append(f"{w}: a site record must name the site, the configuration and the date")
        if t["id"] in VENDOR_DOCUMENTS and (site or rank(ceiling) > rank("infrastructure_proposed")):
            errors.append(f"{w}: a vendor document cannot support installation, commissioning, acceptance or operation")
        if rank(ceiling) >= rank("subsystem_commissioned") and not {"method", "results"} <= set(t["required_attributes"]):
            errors.append(f"{w}: commissioning and later states need a stated method and recorded results")
        if ceiling in ("subsystem_commissioned", "integrated_configuration_verified") and "criteria" not in t["required_attributes"]:
            errors.append(f"{w}: a commissioning or integrated test record needs criteria stated in advance")
        if ceiling == "operational_performance_observed" and "period" not in t["required_attributes"]:
            errors.append(f"{w}: operational observation needs an observation period")
        if t["basis"] not in BASES or not t["basis_refs"] or any(r not in refs for r in t["basis_refs"]):
            errors.append(f"{w}: basis must be governed and its references must resolve")
        if not nonempty(t["does_not_establish"]):
            errors.append(f"{w}: state what the record does not establish")
    acc = types.get("rt-acceptance-record")
    if acc is None or not {"signatory_authority", "criteria", "results"} <= set(acc["required_attributes"]):
        errors.append("rack-dossier: a signed acceptance record needs signatory authority, criteria and results")
    crit = types.get("rt-acceptance-criteria")
    if crit is None or rank(crit["state_ceiling"]) >= rank("integrated_configuration_verified"):
        errors.append("rack-dossier: acceptance criteria (a procedure to accept) cannot support acceptance itself")

    # Chain.
    if [c.get("id") for c in d["chain"]] != CHAIN_IDS:
        errors.append(f"rack-dossier: the evidence chain must be exactly {CHAIN_IDS}")
    for c in d["chain"]:
        w = f"rack-dossier.chain[{c.get('id')}]"
        listed = [types.get(x) for x in c["record_type_ids"]]
        if None in listed:
            errors.append(f"{w}: record types must exist")
            continue
        for s in c["states"]:
            if s not in STATES or not any(t["state_ceiling"] == s for t in listed):
                errors.append(f"{w}: state {s} is not reachable by any record type listed")
        if c["id"] == "g-access" and (c["states"] or any(t["dimension"] != "access" for t in listed)):
            errors.append(f"{w}: access is a separate dimension, not a technical state")
        if not c["category_errors"]:
            errors.append(f"{w}: name the category errors this boundary guards against")
        for e in c["category_errors"]:
            if not e.get("basis") or any(b not in refs for b in e["basis"]) or not nonempty(e.get("why_not")):
                errors.append(f"{w}.{e.get('id')}: a category error needs a reason and resolvable basis")

    # Domains and Workflow C coverage.
    if {x.get("id") for x in d["domains"]} != DOSSIER_DOMAINS or len(d["domains"]) != len(DOSSIER_DOMAINS):
        errors.append(f"rack-dossier: domains must be exactly {sorted(DOSSIER_DOMAINS)}")
    rc_ids = {r["id"]: r for r in wf["requirements"]}
    covered = [x for dm in d["domains"] for x in dm["workflow_c_ids"]]
    if sorted(covered) != sorted(rc_ids):
        errors.append("rack-dossier: every Workflow C requirement must belong to exactly one domain")
    for dm in d["domains"]:
        w = f"rack-dossier.domain[{dm['id']}]"
        if any(x not in DOSSIER_DOMAINS for x in dm["depends_on"]) or any(x not in CHAIN_IDS for x in dm["chain_ids"]):
            errors.append(f"{w}: dependencies and chain boundaries must exist")
        if any(u not in unresolved for u in dm["unresolved_ids"]) or any(c not in ctx["issues"] for c in dm["conflict_ids"]):
            errors.append(f"{w}: open questions and register issues must exist")
        if not isinstance(dm["engineering_review"], bool) or not nonempty(dm["review_reason"]):
            errors.append(f"{w}: say whether engineering review is needed, and why")

    # Dependencies between IDE-006 requirements.
    graph: dict[str, set[str]] = {}
    for e in d["dependencies"]:
        w = f"rack-dossier.dependency[{e.get('prerequisite')}->{e.get('dependent')}]"
        a, b = reqs.get(e["prerequisite"]), reqs.get(e["dependent"])
        if a is None or b is None or a is b:
            errors.append(f"{w}: both ends must be distinct IDE-006 requirements")
            continue
        if e["basis_class"] not in BASES or not e["basis"] or any(x not in refs for x in e["basis"]):
            errors.append(f"{w}: basis must be governed and resolve")
        graph.setdefault(e["prerequisite"], set()).add(e["dependent"])
        if b["current_state"] in SITE_EVIDENCE_STATES and rank(b["current_state"]) > rank(a["current_state"]):
            errors.append(f"{w}: the dependent holds {b['current_state']} while its prerequisite holds {a['current_state']}")
    visiting, done = set(), set()

    def cyclic(n) -> bool:
        if n in visiting:
            return True
        if n in done:
            return False
        visiting.add(n)
        hit = any(cyclic(m) for m in graph.get(n, ()))
        visiting.discard(n)
        done.add(n)
        return hit
    if any(cyclic(n) for n in list(graph)):
        errors.append("rack-dossier: the dependency graph has a cycle")

    # The model applied to the IDE-006 dossier: every entry whose recorded state exceeds its evidence's ceiling is listed, exactly.
    # An entry keeps the state it recorded when flagged; a later correction is added beside it as a 'resolution', never by rewriting it.
    expected = []
    for q in ctx["ide006"]["requirements"]:
        t = types.get(CLASSIFICATION_TYPES.get(q["evidence_classification"], ""))
        if t and t["state_ceiling"] and q["current_state"] in RANK and rank(q["current_state"]) > rank(t["state_ceiling"]):
            expected.append((q["id"], q["evidence_classification"], q["current_state"], t["id"], t["state_ceiling"]))
    open_entries = [x for x in d["ide006_consistency"] if x.get("resolution") is None]
    got = [(x.get("requirement_id"), x.get("evidence_classification"), x.get("current_state"), x.get("record_type_id"), x.get("state_ceiling"))
           for x in open_entries]
    if sorted(got) != sorted(expected):
        errors.append(f"rack-dossier.ide006_consistency must list exactly the IDE-006 entries above their evidence ceiling: {sorted(expected)}")
    if any(not nonempty(x.get("note")) for x in d["ide006_consistency"]):
        errors.append("rack-dossier.ide006_consistency: each entry needs a note for editorial review")
    for x in d["ide006_consistency"]:
        if x.get("resolution") is not None:
            errors += check_resolution(x, types, ctx)

    # Claim-to-evidence matrix.
    rows = [r.get("requirement_id") for r in d["matrix"]]
    if sorted(rows) != sorted(rc_ids):
        errors.append("rack-dossier: the matrix must cover every Workflow C requirement exactly once")
    for r in d["matrix"]:
        w = f"rack-dossier.matrix[{r.get('requirement_id')}]"
        listed = [types.get(x) for x in r["record_type_ids"]]
        if None in listed or not listed or any(x not in reqs for x in r["ide006_requirement_ids"]) or not r["ide006_requirement_ids"]:
            errors.append(f"{w}: record types and IDE-006 requirements must exist")
            continue
        target = r["target_state"]
        if target == "access":
            if any(t["dimension"] != "access" for t in listed) or r["requirement_id"] != "rc-15-access-regulatory":
                errors.append(f"{w}: only the access requirement uses access records")
        else:
            if target not in STATES or any(t["dimension"] != "technical" for t in listed):
                errors.append(f"{w}: target state must be a governed technical state")
                continue
            if max(rank(t["state_ceiling"]) for t in listed) < rank(target):
                errors.append(f"{w}: no listed record type can support {target}")
            if target in SITE_EVIDENCE_STATES and not any(t["site_specific"] for t in listed):
                errors.append(f"{w}: a site-level claim needs a site record")
        if r["record_status"] not in RECORD_STATUSES:
            errors.append(f"{w}: record_status must be one of {sorted(RECORD_STATUSES)}")
        elif r["record_status"] == "reviewed" and any(t["site_specific"] for t in listed) and not site_sources:
            errors.append(f"{w}: a requested site record is treated as reviewed, but no registered source supports a site-record claim")
        for field in ("claim", "holder", "supported_inference", "prohibited_inference", "gap"):
            if not nonempty(r[field]):
                errors.append(f"{w}.{field} must be stated")
        if r["basis_class"] not in BASES or not r["verification_conditions"]:
            errors.append(f"{w}: basis class and verification conditions must be stated")
        if r["stage_note"] is not None and not nonempty(r["stage_note"]):
            errors.append(f"{w}: a stage note, when present, must say something")

    # Findings, review questions, governance.
    for f in d["findings"]:
        if not f.get("basis") or any(b not in refs for b in f["basis"]):
            errors.append(f"rack-dossier.findings: '{f.get('text', '')[:40]}' needs a resolvable basis")
    for q in d["review_questions"]:
        if not q["question"].rstrip().endswith("?") or q["domain_id"] not in DOSSIER_DOMAINS \
                or any(ctx["registry"].get(s, {}).get("status") != "active" for s in q["materials"]):
            errors.append(f"rack-dossier.review[{q['id']}]: a bounded question on one domain, with active public materials")
    if d["public_reference_decision"].get("change_made") is not False:
        errors.append("rack-dossier: public reference changes must go through a release and its validators")
    if ctx["atlas"].get("relationships"):
        errors.append("rack-dossier: the Atlas has relationships; this dossier must not be read as promoting any")
    errors += _content_checks(d, "rack-dossier", set(), prose_skip=(".boundary",))
    return errors


def check_all() -> list[str]:
    for path in (DOSSIER, IDE006_DOSSIER):
        if not path.is_file():
            return [f"required file missing: {path.relative_to(ROOT)}"]
    errors = check(j(DOSSIER), load_context())
    if not errors:
        import render_rack_deployment_dossier as render
        for name in render.out_of_sync():
            errors.append(f"{name} is out of date; run scripts/render_rack_deployment_dossier.py")
    return errors


def main() -> None:
    errors = check_all()
    if errors:
        for e in errors:
            print(f"FAIL: {e}", file=sys.stderr)
        raise SystemExit(1)
    d = j(DOSSIER)
    site = sum(1 for t in d["record_types"] if t["site_specific"])
    print(f"PASS: Rack deployment dossier valid ({len(d['record_types'])} record types, {site} site-specific; "
          f"{len(d['matrix'])} Workflow C requirements mapped; {len(d['dependencies'])} dependencies, acyclic; "
          "no site record reviewed, no review recorded).")


if __name__ == "__main__":
    main()
