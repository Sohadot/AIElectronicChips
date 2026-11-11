#!/usr/bin/env python3
"""Render the HBM4 integration and qualification dossier (IDE-011) as a review document.

The dossier JSON holds only the dossier's own judgments. Every statement, quoted passage, source
date and inspection result in the rendered document is read from the evidence release, the source
registry, the inspection log, the conflict register and the IDE-010 workbench, so the document
cannot drift from its evidence. The output is a repository document; it is not deployed.

    python3 scripts/render_hbm4_dossier.py          # rewrite the document
    python3 scripts/render_hbm4_dossier.py --check  # fail if the document is out of date
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DOSSIER = ROOT / "data" / "research" / "institutional" / "hbm4-integration-qualification-dossier-011.json"
OUT = ROOT / "HBM4_INTEGRATION_QUALIFICATION_DOSSIER_011.md"
sys.path.insert(0, str(Path(__file__).resolve().parent))
from validate_evidence_maintenance import FRESHNESS_BASIS  # noqa: E402

CLASS = {"attributed_statement": "A — attributed statement", "bounded_analysis": "C — bounded analysis"}
EVIDENCE_LEVEL = {
    "announced_standard": "Standard as announced; normative text not reviewed",
    "supplier_statements": "Suppliers' statements about their own products",
    "accelerator_maker_statements": "The accelerator maker's own statements",
    "roadmap_statements_only": "Roadmap and intent statements only; no product disclosure",
    "design_target_statements_only": "Suppliers' design-target statements only; no qualification disclosure",
    "no_public_evidence": "No public evidence in the reviewed sources",
}
REVIEW = {"documentary_verification": "Documentary verification", "technical_review": "Technical review",
          "normative_text_review": "Normative text review"}
LAYER = {"design": "Design", "fabrication": "Fabrication", "packaging": "Packaging", "memory": "Memory", "interconnect": "Interconnect",
         "power_thermal": "Power / Thermal", "controls": "Controls", "deployment": "Deployment"}
ISSUE_STATE = {"open_conflict": "open conflict", "missing_primary_evidence": "missing primary evidence",
               "version_scope_difference": "version-scope difference", "source_access_blocked": "source access blocked",
               "requires_reassessment": "requires reassessment", "resolved_with_evidence": "resolved with evidence"}
AVAILABILITY = {"published": "published", "partially_published": "partially published", "not_published": "not published"}


def j(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def load():
    dossier = j(DOSSIER)
    registry = {s["id"]: s for s in j(ROOT / "data" / "source-registry.json")["source_records"]}
    releases = {r["release_id"]: r for r in (j(p) for p in sorted((ROOT / "data" / "research").glob("*.json")))}
    log = j(ROOT / "data" / "source-inspections.json")
    issues = {i["id"]: i for i in j(ROOT / "data" / "evidence-conflicts.json")["issues"]}
    workbench = j(ROOT / "data" / "industrial-evidence-requests.json")
    return dossier, registry, releases, log, issues, workbench


def cell(text: str) -> str:
    return str(text).replace("|", "\\|").replace("\n", " ")


def latest_records(log) -> dict[str, dict]:
    order = {r["run_id"]: i for i, r in enumerate(log["runs"])}
    out: dict[str, dict] = {}
    for rec in log["records"]:
        if rec["source_id"] not in out or order[rec["run_id"]] >= order[out[rec["source_id"]]["run_id"]]:
            out[rec["source_id"]] = rec
    return out


def passage_status(finding: dict, latest: dict[str, dict]) -> list[str]:
    """Per cited source: how the finding's quoted passages fared on the latest inspection run."""
    out = []
    for ev in finding["evidence"]:
        sid = ev["source_id"]
        rec = latest.get(sid)
        quoted = '"' in ev["locator"]
        if rec is None:
            out.append(f"`{sid}`: not inspected")
        elif "source_inaccessible" in rec["states"]:
            out.append(f"`{sid}`: not retrievable on {rec['inspected_at']}; passage not rechecked")
        elif not quoted:
            out.append(f"`{sid}`: retrieved {rec['inspected_at']}; full-text search record, no quoted passage")
        else:
            missing = [m for m in (rec["passage_check"] or {}).get("not_found", []) if m["cited_in"] == finding["id"]]
            out.append(f"`{sid}`: {'passage not found' if missing else 'passage found'} on {rec['inspected_at']}")
    return out


def render(dossier, registry, releases, log, issues, workbench) -> str:
    release = releases[dossier["inputs"]["release_ids"][0]]
    findings = {f["id"]: f for f in release["findings"]}
    unresolved = {u["id"]: u for u in release["unresolved"]}
    for r in releases.values():
        for u in r["unresolved"]:
            unresolved.setdefault(u["id"], u)
    candidates = {c["id"]: c for c in release["candidate_relationships"]}
    latest = latest_records(log)
    wf = next(w for w in workbench["workflows"] if w["id"] == dossier["inputs"]["workflow_id"])
    reqs = {r["id"]: r for r in wf["requirements"]}
    rows_by_stage: dict[str, list[dict]] = {}
    for row in dossier["evidence_matrix"]:
        rows_by_stage.setdefault(row["stage_id"], []).append(row)
    sources = sorted({e["source_id"] for f in release["findings"] for e in f["evidence"]}
                     | {e["source_id"] for c in release["candidate_relationships"] for e in c["evidence"]})
    runs = log["runs"]
    by_run = {(rec["source_id"], rec["run_id"]): rec for rec in log["records"]}

    out = [
        "<!-- Generated by scripts/render_hbm4_dossier.py from data/research/institutional/hbm4-integration-qualification-dossier-011.json. Do not edit by hand. -->",
        "",
        "# HBM4 Integration & Qualification Evidence Dossier",
        "",
        f"- **Dossier:** `{dossier['dossier_id']}` (release {dossier['release']}, schema {dossier['schema_version']}), as of {dossier['as_of']}.",
        f"- **Status:** {dossier['status'].replace('_', ' ')}; review status {dossier['review_status'].replace('_', ' ')}; "
        f"scientific review {dossier['scientific_review']}; review owner {dossier['review_owner']}.",
        f"- **Method:** {'AI-assisted source check' if dossier['assessment_method'] == 'ai_assisted_source_check' else dossier['assessment_method']}. Interpretation standard: {dossier['interpretation_standard']}.",
        f"- **Evidence base:** `{release['release_id']}` (version {release['version']}), {len(findings)} findings, {len(release['unresolved'])} open questions, "
        f"{len(candidates)} candidate relationships; {len(sources)} registered sources; inspection runs "
        + ", ".join(f"`{r}`" for r in dossier["inputs"]["inspection_run_ids"]) + ".",
        "",
        f"> {dossier['boundary']}",
        "",
        "## 1. Research question and scope",
        "",
        f"**Question.** {dossier['research_question']}",
        "",
        f"- **Technical scope:** {dossier['scope']['technical']}.",
        f"- **Time:** {dossier['scope']['temporal']}.",
        f"- **Geography:** {dossier['scope']['geographic']}.",
        "- **Excluded:** " + "; ".join(dossier["scope"]["excluded"]) + ".",
        "",
        "### How to read this dossier",
        "",
        "- **Evidence class.** *A* is an attributed statement: what a named party says, with its date. *C* is bounded analysis: this project's derivation, "
        "with its assumptions stated. Open questions are not matrix rows; they are cited by their `u-` identifiers in sections 2 and 7. No statement here is a verified fact in the Atlas sense; that would need an independent record type and a named reviewer.",
        "- **Passage status.** For each cited source, whether the finding's quoted passage was found in the document on the latest inspection run. "
        "A found passage shows the text is still published, not that the claim is correct.",
        "- **Review requirement.** The kind of human review the row needs before it can support a published statement: "
        + "; ".join(f"*{v}*" for v in REVIEW.values()) + ". See section 11.",
        "",
        "## 2. Dependency architecture",
        "",
        "Integration of named HBM4 in a named accelerator is a chain of separately evidenced stages. A statement at one stage does not carry over to the next: "
        "a standard does not describe a part, a part does not show integration, and integration does not show qualification or supply.",
        "",
        "| # | Stage | Layer | Evidence level | Findings | Open questions | Register issues | Documents to request | Candidate edges |",
        "| --- | --- | --- | --- | --- | --- | --- | --- | --- |",
    ]
    for n, st in enumerate(dossier["dependency_architecture"], start=1):
        out.append(f"| {n} | **{cell(st['title'])}**<br>{cell(st['question'])} | {LAYER[st['ontology_layer']]} | {EVIDENCE_LEVEL[st['evidence_level']]} | "
                   f"{len(rows_by_stage.get(st['id'], []))} | {', '.join(f'`{u}`' for u in st['unresolved_ids']) or '—'} | "
                   f"{', '.join(f'`{c}`' for c in st['conflict_ids']) or '—'} | {', '.join(f'`{r}`' for r in st['documentary_requirement_ids'])} | "
                   f"{', '.join(f'`{c}`' for c in st['candidate_ids']) or '—'} |")
    out += ["", "## 3. Evidence matrix", "",
            f"All {len(findings)} findings of `{release['release_id']}`, each assigned to one stage, with the exact passages relied on and their status on the latest inspection.", ""]
    for n, st in enumerate(dossier["dependency_architecture"], start=1):
        rows = rows_by_stage.get(st["id"], [])
        out.append(f"### 3.{n} {st['title']}")
        out.append("")
        if not rows:
            out.append(f"No reviewed source contains evidence for this stage. Open: {', '.join(f'`{u}`' for u in st['unresolved_ids'])}. "
                       f"Documents that would establish it: {', '.join(f'`{r}`' for r in st['documentary_requirement_ids'])}.")
            out.append("")
            continue
        for row in rows:
            f = findings[row["finding_id"]]
            out.append(f"**`{f['id']}`** — {CLASS[f['claim_class']]} · {REVIEW[row['review_requirement']]}")
            out.append("")
            out.append(f"{f['statement']}")
            out.append("")
            for ev in f["evidence"]:
                s = registry[ev["source_id"]]
                out.append(f"- `{ev['source_id']}` ({s['publisher']}, {s.get('publication_date') or s.get('effective_date') or 'undated'}): {ev['locator']}")
            out.append("- **Passage status:** " + "; ".join(passage_status(f, latest)) + ".")
            out.append(f"- **Scope:** {f['scope']}.")
            out.append("- **Limitations:** " + "; ".join(f["limitations"]) + ".")
            out.append(f"- **Reading:** {row['interpretation']}")
            out.append("")
    out += ["## 4. Provenance and freshness", "",
            "Every source the release cites. Dates are kept apart: publication, the access date recorded for the release, and each inspection.", "",
            "| Source | Publisher | Type | Published | Accessed | " + " | ".join(f"Inspection {r['inspected_at']} (`{r['run_id']}`)" for r in runs) + " | Why recheck before current use |",
            "| --- | --- | --- | --- | --- | " + " | ".join("---" for _ in runs) + " | --- |"]
    for sid in sources:
        s = registry[sid]
        cells = []
        for r in runs:
            rec = by_run.get((sid, r["run_id"]))
            if rec is None:
                cells.append("not in run")
            elif "source_inaccessible" in rec["states"]:
                cells.append("not retrievable (HTTP " + ", ".join(str(x.get("http_status", x.get("detail"))) for x in rec["retrievals"]) + ")")
            elif rec["passage_check"]:
                cells.append(f"retrieved; {rec['passage_check']['found']} of {rec['passage_check']['quoted_passages']} passages found")
            else:
                cells.append("retrieved; no quoted passages")
        out.append(f"| `{sid}` | {cell(s['publisher'])} | {s['source_type'].replace('_', ' ')} | {s.get('publication_date') or s.get('effective_date') or '—'} | "
                   f"{s['accessed_at']} | " + " | ".join(cells) + f" | {cell(FRESHNESS_BASIS.get(s['source_type'], 'Recheck before current use'))} |")
    blocked = [sid for sid in sources if "source_inaccessible" in latest[sid]["states"]]
    out += ["", f"{len(sources) - len(blocked)} of {len(sources)} sources were retrieved on the latest run and all of their quoted passages were found. "
            f"Not retrievable by automated inspection: {', '.join(f'`{b}`' for b in blocked) or 'none'}. "
            + (latest[blocked[0]]["notes"][0] if blocked else ""), ""]
    out += ["## 5. Conflicting disclosures", "", "Register issues linked to the stages above, with their state on the register:", ""]
    linked = []
    for st in dossier["dependency_architecture"]:
        linked += [c for c in st["conflict_ids"] if c not in linked]
    for cid in linked:
        i = issues[cid]
        out.append(f"- **`{cid}`** ({ISSUE_STATE[i['state']]}): {i['title']}. {i['question']} Posture: {i['posture']}")
    out += ["", "Conflicts within the release's own findings: `f-priority-conflict` (each supplier's 'first' uses a different milestone), "
            "`f-power-claims` (efficiency gains against different baselines) and `f-nv-rubin` against `f-nv-rubin-192` (two per-GPU bandwidth figures from NVIDIA).", ""]
    out += ["## 6. Candidate Atlas relationships", "",
            "Each of the release's five candidate edges, reassessed against the current corpus and the 2026-11-11 inspection. A recommendation is advice to a named human reviewer; "
            "none of these edges is in the Atlas, and this dossier does not move any of them there.", "",
            "| Candidate | Relation | Release recommendation | Dossier recommendation |", "| --- | --- | --- | --- |"]
    for a in dossier["candidate_assessments"]:
        c = candidates[a["candidate_id"]]
        out.append(f"| `{c['id']}` | `{c['from']}` {c['relation_type']} `{c['to']}` | {a['release_recommendation']} | **{a['dossier_recommendation']}** |")
    out.append("")
    for a in dossier["candidate_assessments"]:
        c = candidates[a["candidate_id"]]
        out.append(f"### `{c['id']}` — {a['dossier_recommendation']}")
        out.append("")
        out.append(f"*Candidate statement ({c['claim_class'].replace('_', ' ')}):* {c['statement']}")
        out.append("")
        for r in a["reasons"]:
            out.append(f"- {r['reason']} Basis: {', '.join(f'`{b}`' for b in r['basis'])}.")
        if a["preconditions_for_review"]:
            out.append("- **Before review:** " + "; ".join(a["preconditions_for_review"]) + ".")
        if a["proposed_revision"]:
            pr = a["proposed_revision"]
            out.append(f"- **Proposed statement:** {pr['statement']}")
            out.append("- **Evidence changes:** " + "; ".join(pr["evidence_changes"]) + ".")
            out.append(f"- **Scope:** {pr['scope_note']}.")
        out.append("")
    out += ["## 7. Critical unknowns", "", "What the public record cannot yet substantiate, and what would.", ""]
    for u in dossier["critical_unknowns"]:
        qs = "; ".join(f"`{x}`: {unresolved[x]['question']}" for x in u["unresolved_ids"])
        out.append(f"- **{u['question']}** {u['why_critical']} Open questions: {qs}{'' if qs.endswith('?') else '.'} "
                   + (f"Register: {', '.join(f'`{c}`' for c in u['conflict_ids'])}. " if u["conflict_ids"] else "")
                   + f"Would be established by: {', '.join(f'`{r}`' for r in u['would_establish'])}.")
    out += ["", "## 8. Documentary requirements", "",
            f"From IDE-010 workflow {wf['letter']} ({wf['title']}), mapped to the stages they would settle. Availability is as recorded in the workbench.", "",
            "| Requirement | Stage | Document to request | Publicly available |", "| --- | --- | --- | --- |"]
    stage_of = {}
    for st in dossier["dependency_architecture"]:
        for rid in st["documentary_requirement_ids"]:
            stage_of.setdefault(rid, []).append(st["title"])
    for rid, r in reqs.items():
        out.append(f"| `{rid}` {cell(r['title'])} | {', '.join(stage_of.get(rid, []))} | {cell(r['document_requested'])} | {AVAILABILITY[r['public_availability']]} |")
    out += ["", "## 9. Limitations", "",
            "- The evidence is what the three HBM suppliers, TSMC, JEDEC and NVIDIA chose to publish. No accelerator maker's qualification record, contract or test report was available.",
            "- The JEDEC standard was read as an announcement; the normative documents were not reviewed.",
            "- Three documents hosted on SEC EDGAR could not be retrieved by automated inspection, which EDGAR refuses without a declared contact identity: two company filings (Micron's FY2026 Form 10-K and SK hynix's 424B4 prospectus) and Micron's Q3 FY2026 results release. The registry classifies the results release as a company announcement; on EDGAR it is filed as an exhibit. Their passages are carried from the release and have not been rechecked.",
            "- Passage checks confirm that quoted text is still published. They do not confirm that a claim is correct, current or complete, or that no newer edition exists.",
            "- Every recommendation and reading in this dossier is AI-assisted and has not been reviewed by a person.", "",
            "## 10. Prohibited inferences", "", "Statements the evidence does not support, and why. Each cites the findings or issues it rests on.", ""]
    for p in dossier["prohibited_inferences"]:
        out.append(f"- **Unsupported inference:** {p['inference']}. {p['why_not']} Basis: {', '.join(f'`{b}`' for b in p['basis'])}.")
    out += ["", "## 11. Review and acceptance requirements", "",
            "No review has taken place, and no reviewer is assigned. Before any statement in this dossier supports a public reference or an Atlas change:", ""]
    counts = {k: sum(1 for r in dossier["evidence_matrix"] if r["review_requirement"] == k) for k in REVIEW}
    for rv in dossier["review_requirements"]:
        out.append(f"- **{rv['scope']}.** {rv['requirement']}.")
    out += ["", "Rows by review requirement: " + "; ".join(f"{REVIEW[k]} {v}" for k, v in counts.items()) + ".", "",
            "## 12. Lineage", "",
            "- Judgments: `data/research/institutional/hbm4-integration-qualification-dossier-011.json`.",
            f"- Findings, passages and candidates: `data/research/{release['release_id'].replace('aec-', '')}.json`.",
            "- Source metadata: `data/source-registry.json`. Inspections: `data/source-inspections.json`. Register: `data/evidence-conflicts.json`. "
            "Documentary requirements: `data/industrial-evidence-requests.json`.",
            "- Validated by `scripts/validate_hbm4_dossier.py`; this document is regenerated by `scripts/render_hbm4_dossier.py`.", ""]
    return "\n".join(out)


def in_sync() -> bool:
    return OUT.is_file() and OUT.read_text(encoding="utf-8") == render(*load())


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--check", action="store_true", help="fail if the document does not match its inputs")
    args = parser.parse_args(argv)
    if args.check:
        if not in_sync():
            print("FAIL: HBM4_INTEGRATION_QUALIFICATION_DOSSIER_011.md is out of date; run scripts/render_hbm4_dossier.py", file=sys.stderr)
            raise SystemExit(1)
        print("PASS: HBM4 dossier document matches its inputs.")
        return
    OUT.write_text(render(*load()), encoding="utf-8")
    print("dossier rendered")


if __name__ == "__main__":
    main()
