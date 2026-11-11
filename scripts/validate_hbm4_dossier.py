#!/usr/bin/env python3
"""Validate the HBM4 integration and qualification dossier (IDE-011).

The dossier records judgments about an evidence release; this validator checks every judgment
against facts it derives from the corpus itself:

- the dossier exists and is complete: every finding of the release appears in the evidence matrix
  exactly once, every candidate relationship is assessed exactly once, and every documentary
  requirement of IDE-010 workflow A is mapped to a stage;
- every identifier it cites resolves (findings, open questions, register issues, sources,
  inspection records, workbench requirements, pathway);
- review requirements follow the evidence: bounded analysis needs technical review and the JEDEC
  announcement needs normative-text review;
- a candidate recommendation that rests on a source automated inspection could not retrieve
  carries a precondition or a revision, and the release's own recommendation is quoted exactly;
- nothing is promoted: no candidate is in the Atlas, the Atlas keeps its reviewed relationships
  unchanged, and the dossier records no reviewer, review date, approval or score;
- the rendered review document matches its inputs.

It checks structure and lineage. It does not read the documents and cannot confirm that a source
says what a finding states; that is the human review the dossier asks for.
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(Path(__file__).resolve().parent))
from validate_dependency_atlas import LAYERS  # noqa: E402
from validate_evidence_maintenance import _content_checks  # noqa: E402

DOSSIER = ROOT / "data" / "research" / "institutional" / "hbm4-integration-qualification-dossier-011.json"
TOP = {"dossier_id", "schema_version", "release", "status", "review_status", "scientific_review", "review_owner", "assessment_method",
       "as_of", "interpretation_standard", "research_question", "scope", "boundary", "inputs", "dependency_architecture",
       "evidence_matrix", "candidate_assessments", "critical_unknowns", "prohibited_inferences", "review_requirements"}
STAGE_FIELDS = {"id", "title", "ontology_layer", "question", "evidence_level", "unresolved_ids", "conflict_ids",
                "documentary_requirement_ids", "candidate_ids"}
EVIDENCE_LEVELS = {"announced_standard", "supplier_statements", "accelerator_maker_statements", "roadmap_statements_only",
                   "design_target_statements_only", "no_public_evidence"}
REVIEW_REQUIREMENTS = {"documentary_verification", "technical_review", "normative_text_review"}
DECISIONS = {"ACCEPT", "REVISE", "DEFER", "REJECT"}
STANDARD_SOURCES = {"jedec-jesd270-4-hbm4-standard-2025"}
INSPECTION_REF = re.compile(r"^inspection:([a-z0-9-]+):([a-z0-9-]+)$")
ATLAS_REFS = {"atlas:node_types"}


def j(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def load_context():
    registry = {s["id"]: s for s in j(ROOT / "data" / "source-registry.json")["source_records"]}
    releases = {r["release_id"]: r for r in (j(p) for p in sorted((ROOT / "data" / "research").glob("*.json")))}
    return {"registry": registry, "releases": releases, "log": j(ROOT / "data" / "source-inspections.json"),
            "issues": {i["id"]: i for i in j(ROOT / "data" / "evidence-conflicts.json")["issues"]},
            "workbench": j(ROOT / "data" / "industrial-evidence-requests.json"), "pathways": j(ROOT / "data" / "reference-pathways.json"),
            "atlas": j(ROOT / "data" / "dependency-atlas.json")}


def nonempty(v) -> bool:
    return isinstance(v, str) and bool(v.strip())


def check(d, ctx) -> list[str]:
    if not isinstance(d, dict) or set(d) != TOP:
        return ["hbm4-dossier: top-level fields mismatch"]
    errors: list[str] = []
    # Governance: a research candidate that records no review.
    if (d["status"], d["review_status"], d["scientific_review"], d["review_owner"]) != ("research_candidate", "not_reviewed", "pending", "unassigned"):
        errors.append("hbm4-dossier: must stay a research candidate, not reviewed, scientific review pending, review owner unassigned")
    if d["assessment_method"] != "ai_assisted_source_check" or d["interpretation_standard"] != "AEC-CS-001":
        errors.append("hbm4-dossier: assessment method and interpretation standard must be the governed values")
    if "not an assessment" not in d["boundary"] or "does not promote" not in d["boundary"] or "records no human or scientific review" not in d["boundary"]:
        errors.append("hbm4-dossier: boundary must say it is not an assessment, promotes nothing and records no review")
    if not d["research_question"].rstrip().endswith("?"):
        errors.append("hbm4-dossier: research_question must be a question")
    # Inputs.
    inputs = d["inputs"]
    rel_ids = inputs.get("release_ids", [])
    if len(rel_ids) != 1 or rel_ids[0] not in ctx["releases"]:
        return errors + ["hbm4-dossier: inputs.release_ids must name exactly one existing release"]
    release = ctx["releases"][rel_ids[0]]
    run_ids = [r["run_id"] for r in ctx["log"]["runs"]]
    for rid in inputs.get("inspection_run_ids", []):
        if rid not in run_ids:
            errors.append(f"hbm4-dossier: inspection run {rid} does not exist")
    wf = next((w for w in ctx["workbench"]["workflows"] if w["id"] == inputs.get("workflow_id")), None)
    if wf is None:
        return errors + ["hbm4-dossier: inputs.workflow_id must name an IDE-010 workflow"]
    if inputs.get("pathway_id") not in {p["id"] for p in ctx["pathways"]["pathways"]}:
        errors.append("hbm4-dossier: inputs.pathway_id must name a reference pathway")
    findings = {f["id"]: f for f in release["findings"]}
    unresolved = {u["id"] for r in ctx["releases"].values() for u in r["unresolved"]}
    candidates = {c["id"]: c for c in release["candidate_relationships"]}
    reqs = {r["id"] for r in wf["requirements"]}
    issues = ctx["issues"]
    order = {r: i for i, r in enumerate(run_ids)}
    latest: dict[str, dict] = {}
    records = {(rec["source_id"], rec["run_id"]): rec for rec in ctx["log"]["records"]}
    for rec in ctx["log"]["records"]:
        if rec["source_id"] not in latest or order[rec["run_id"]] >= order[latest[rec["source_id"]]["run_id"]]:
            latest[rec["source_id"]] = rec
    inaccessible = {sid for sid, rec in latest.items() if "source_inaccessible" in rec["states"]}

    def resolves(ref: str) -> bool:
        m = INSPECTION_REF.fullmatch(ref)
        if m:
            return (m.group(2), m.group(1)) in records
        return ref in findings or ref in unresolved or ref in issues or ref in ctx["registry"] or ref in ATLAS_REFS

    # Dependency architecture.
    stages = d["dependency_architecture"]
    stage_ids = [s.get("id") for s in stages if isinstance(s, dict)]
    if len(set(stage_ids)) != len(stages) or len(stages) < 6:
        errors.append("hbm4-dossier: dependency architecture needs at least six uniquely identified stages")
    rows_by_stage = {}
    for row in d["evidence_matrix"]:
        rows_by_stage.setdefault(row.get("stage_id"), []).append(row)
    staged_candidates, staged_reqs = [], set()
    for st in stages:
        if not isinstance(st, dict) or set(st) != STAGE_FIELDS:
            errors.append("hbm4-dossier: stage fields mismatch")
            continue
        w = f"hbm4-dossier[{st['id']}]"
        if st["ontology_layer"] not in LAYERS or st["evidence_level"] not in EVIDENCE_LEVELS:
            errors.append(f"{w}: ontology_layer and evidence_level must be governed values")
        if not st["question"].rstrip().endswith("?"):
            errors.append(f"{w}: question must be a question")
        for u in st["unresolved_ids"]:
            if u not in unresolved:
                errors.append(f"{w}: open question {u} does not exist")
        for c in st["conflict_ids"]:
            if c not in issues:
                errors.append(f"{w}: register issue {c} does not exist")
        if not st["documentary_requirement_ids"]:
            errors.append(f"{w}: every stage names the documents that would establish it")
        for r in st["documentary_requirement_ids"]:
            if r not in reqs:
                errors.append(f"{w}: documentary requirement {r} is not in workflow {wf['id']}")
            staged_reqs.add(r)
        for c in st["candidate_ids"]:
            if c not in candidates:
                errors.append(f"{w}: candidate {c} is not in the release")
            staged_candidates.append(c)
        has_rows = bool(rows_by_stage.get(st["id"]))
        if (st["evidence_level"] == "no_public_evidence") == has_rows:
            errors.append(f"{w}: 'no_public_evidence' must be used exactly when no finding is assigned to the stage")
        if st["evidence_level"] == "no_public_evidence" and not st["unresolved_ids"]:
            errors.append(f"{w}: a stage without public evidence must name its open questions")
    if sorted(staged_candidates) != sorted(candidates):
        errors.append("hbm4-dossier: every candidate relationship must be placed in exactly one stage")
    if reqs - staged_reqs:
        errors.append(f"hbm4-dossier: workflow requirements not mapped to a stage: {sorted(reqs - staged_reqs)}")
    # Evidence matrix: complete, exact coverage of the release.
    seen = [r.get("finding_id") for r in d["evidence_matrix"]]
    if sorted(seen) != sorted(findings):
        missing, extra = sorted(set(findings) - set(seen)), sorted(set(seen) - set(findings))
        dup = sorted({x for x in seen if seen.count(x) > 1})
        errors.append(f"hbm4-dossier: evidence matrix must cover every finding once (missing {missing}, unknown {extra}, duplicated {dup})")
    for row in d["evidence_matrix"]:
        if set(row) != {"finding_id", "stage_id", "review_requirement", "interpretation"}:
            errors.append(f"hbm4-dossier: matrix row {row.get('finding_id')} fields mismatch")
            continue
        f = findings.get(row["finding_id"])
        w = f"hbm4-dossier.matrix[{row['finding_id']}]"
        if row["stage_id"] not in stage_ids:
            errors.append(f"{w}: stage {row['stage_id']} does not exist")
        if row["review_requirement"] not in REVIEW_REQUIREMENTS:
            errors.append(f"{w}: review_requirement must be one of {sorted(REVIEW_REQUIREMENTS)}")
        if not nonempty(row["interpretation"]) or len(row["interpretation"]) < 30:
            errors.append(f"{w}: interpretation must say what the finding does and does not show")
        if f is None:
            continue
        srcs = {e["source_id"] for e in f["evidence"]}
        if f["claim_class"] == "bounded_analysis" and row["review_requirement"] != "technical_review":
            errors.append(f"{w}: bounded analysis needs technical review")
        if srcs <= STANDARD_SOURCES and row["review_requirement"] != "normative_text_review":
            errors.append(f"{w}: a finding resting only on the standard's announcement needs normative-text review")
        if srcs & inaccessible and "retriev" not in row["interpretation"]:
            errors.append(f"{w}: cites a source automated inspection could not retrieve; the interpretation must say so")
    # Candidate assessments.
    assessed = [a.get("candidate_id") for a in d["candidate_assessments"]]
    if sorted(assessed) != sorted(candidates):
        errors.append("hbm4-dossier: every candidate relationship must be assessed exactly once")
    for a in d["candidate_assessments"]:
        c = candidates.get(a.get("candidate_id"))
        w = f"hbm4-dossier.assessment[{a.get('candidate_id')}]"
        if c is None or set(a) != {"candidate_id", "release_recommendation", "dossier_recommendation", "reasons", "preconditions_for_review", "proposed_revision"}:
            errors.append(f"{w}: unknown candidate or fields mismatch")
            continue
        if a["release_recommendation"] != c["research_recommendation"]["decision"]:
            errors.append(f"{w}: release_recommendation must quote the release's decision ({c['research_recommendation']['decision']})")
        if a["dossier_recommendation"] not in DECISIONS:
            errors.append(f"{w}: recommendation must be one of {sorted(DECISIONS)}")
        if not a["reasons"]:
            errors.append(f"{w}: a recommendation needs traceable reasons")
        cited_inaccessible = False
        for r in a["reasons"]:
            if not nonempty(r.get("reason")) or not r.get("basis"):
                errors.append(f"{w}: each reason needs text and at least one basis")
                continue
            for b in r["basis"]:
                if not resolves(b):
                    errors.append(f"{w}: basis {b} does not resolve")
                m = INSPECTION_REF.fullmatch(b)
                if (m and "source_inaccessible" in records.get((m.group(2), m.group(1)), {}).get("states", [])) or \
                        (b in findings and {e["source_id"] for e in findings[b]["evidence"]} & inaccessible):
                    cited_inaccessible = True
        revise = a["dossier_recommendation"] == "REVISE"
        pr = a["proposed_revision"]
        if revise != isinstance(pr, dict):
            errors.append(f"{w}: a proposed revision is given exactly when the recommendation is REVISE")
        if isinstance(pr, dict) and not (nonempty(pr.get("statement")) and pr.get("evidence_changes") and nonempty(pr.get("scope_note"))):
            errors.append(f"{w}: a revision needs a statement, evidence changes and a scope note")
        if cited_inaccessible and a["dossier_recommendation"] == "ACCEPT" and not a["preconditions_for_review"]:
            errors.append(f"{w}: an ACCEPT that rests on an unretrieved source must state what the reviewer has to read first")
    # Unknowns, prohibited inferences, review requirements.
    for u in d["critical_unknowns"]:
        w = f"hbm4-dossier.unknown[{u.get('id')}]"
        if not u.get("unresolved_ids") or any(x not in unresolved for x in u["unresolved_ids"]):
            errors.append(f"{w}: must cite existing open questions")
        if any(c not in issues for c in u.get("conflict_ids", [])) or not u.get("would_establish") or any(r not in reqs for r in u["would_establish"]):
            errors.append(f"{w}: register issues and documentary requirements must resolve")
    for p in d["prohibited_inferences"]:
        if not p.get("basis") or any(not resolves(b) for b in p["basis"]) or not nonempty(p.get("why_not")):
            errors.append(f"hbm4-dossier.prohibited[{p.get('id')}]: needs a reason and resolvable basis")
    if {"rv-documentary", "rv-technical", "rv-normative", "rv-unretrieved", "rv-candidates"} - {r.get("id") for r in d["review_requirements"]}:
        errors.append("hbm4-dossier: review requirements must cover documentary, technical, normative, unretrieved-source and candidate review")
    # Nothing promoted.
    atlas_ids = {r["id"] for r in ctx["atlas"].get("relationships", [])}
    for cid in candidates:
        if cid in atlas_ids:
            errors.append(f"hbm4-dossier: candidate {cid} is in the Atlas; the dossier must not promote candidates")
    errors += _content_checks(d, "hbm4-dossier", set(), prose_skip=(".boundary",))
    return errors


def check_all() -> list[str]:
    if not DOSSIER.is_file():
        return [f"required dossier missing: {DOSSIER.relative_to(ROOT)}"]
    errors = check(j(DOSSIER), load_context())
    if not errors:
        import render_hbm4_dossier as render
        if not render.in_sync():
            errors.append("HBM4_INTEGRATION_QUALIFICATION_DOSSIER_011.md is out of date; run scripts/render_hbm4_dossier.py")
    return errors


def main() -> None:
    errors = check_all()
    if errors:
        for e in errors:
            print(f"FAIL: {e}", file=sys.stderr)
        raise SystemExit(1)
    d = j(DOSSIER)
    rec = {}
    for a in d["candidate_assessments"]:
        rec[a["dossier_recommendation"]] = rec.get(a["dossier_recommendation"], 0) + 1
    print(f"PASS: HBM4 dossier valid ({len(d['dependency_architecture'])} stages, {len(d['evidence_matrix'])} findings traced, "
          f"{len(d['candidate_assessments'])} candidates assessed: " + ", ".join(f"{k} {v}" for k, v in sorted(rec.items()))
          + "; nothing promoted, no review recorded).")


if __name__ == "__main__":
    main()
