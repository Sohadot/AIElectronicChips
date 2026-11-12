#!/usr/bin/env python3
"""Render the Industrial Evidence Request & Research Workbench catalog (IDE-010).

The catalog is generated from data/industrial-evidence-requests.json, the evidence releases, the source
registry and the conflict register, and written between two markers in research-workbench/index.html.
Every workflow, requirement and evidence trace is plain HTML and readable without JavaScript; the
local script only adds per-tab collection statuses, notes, export and print.

    python3 scripts/render_research_workbench.py          # rewrite the page section
    python3 scripts/render_research_workbench.py --check  # fail if the page is out of date
"""

from __future__ import annotations

import argparse
import html
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MODEL = ROOT / "data" / "industrial-evidence-requests.json"
PAGE = ROOT / "research-workbench" / "index.html"
PREFLIGHT = ROOT / "data" / "deployment-evidence-preflight.json"
RECORD_MODEL = ROOT / "data" / "research" / "institutional" / "rack-deployment-verification-dossier-014.json"
IDE006_DOSSIER = ROOT / "data" / "research" / "dossiers" / "gb200-nvl72-reference-demo.json"
START, END = "<!-- research-workbench:start -->", "<!-- research-workbench:end -->"

LAYER_NAME = {"design": "Design", "fabrication": "Fabrication", "packaging": "Packaging", "memory": "Memory",
              "interconnect": "Interconnect", "power_thermal": "Power / Thermal", "controls": "Controls", "deployment": "Deployment"}
CATEGORY_LABEL = {"specification": "Specification", "design_documentation": "Design documentation",
                  "qualification_record": "Qualification record", "production_record": "Production record",
                  "procurement_record": "Procurement record", "installation_record": "Installation record",
                  "commissioning_record": "Commissioning record", "test_record": "Test record",
                  "operational_record": "Operational record", "measurement": "Measurement",
                  "regulatory_determination": "Regulatory determination"}
AVAILABILITY = {"published": ("tag-s", "P", "Published"), "partially_published": ("tag-c", "Pp", "Partially published"),
                "not_published": ("tag-u", "N", "Not published")}
BASIS_LABEL = {"source_derived": "Source-derived", "analytical_recommendation": "Analytical recommendation"}
STAGE_LABEL = {"specified": "Specified", "procured": "Procured", "installed": "Installed", "commissioned": "Commissioned",
               "operationally_observed": "Operationally observed", "access": "Access and regulatory scope"}
ISSUE_STATE = {"open_conflict": "open conflict", "missing_primary_evidence": "missing primary evidence",
               "version_scope_difference": "version-scope difference", "source_access_blocked": "source access blocked",
               "requires_reassessment": "requires reassessment", "resolved_with_evidence": "resolved with evidence; public wording under review"}

e = html.escape


def load():
    model = json.loads(MODEL.read_text(encoding="utf-8"))
    registry = {s["id"]: s for s in json.loads((ROOT / "data" / "source-registry.json").read_text(encoding="utf-8"))["source_records"]}
    findings, unresolved = {}, {}
    for p in sorted((ROOT / "data" / "research").glob("*.json")):
        r = json.loads(p.read_text(encoding="utf-8"))
        for f in r["findings"]:
            findings[f["id"]] = r["release_id"]
        for u in r["unresolved"]:
            unresolved[u["id"]] = u
    conflicts = {i["id"]: i for i in json.loads((ROOT / "data" / "evidence-conflicts.json").read_text(encoding="utf-8"))["issues"]}
    preflight = {"config": json.loads(PREFLIGHT.read_text(encoding="utf-8")),
                 "model": json.loads(RECORD_MODEL.read_text(encoding="utf-8")),
                 "ide006": json.loads(IDE006_DOSSIER.read_text(encoding="utf-8"))}
    return model, registry, findings, unresolved, conflicts, preflight


# ---------------------------------------------------------------------------------------------------------------
# Documentary preflight for Workflow C (IDE-015). Everything below is read from the IDE-014 record model, the IDE-006
# dossier and data/deployment-evidence-preflight.json, and rendered as plain HTML. The local script only adds
# present / missing / unknown selections, the gap explanation, export and print; it never computes an evidence state.
# ---------------------------------------------------------------------------------------------------------------
STATES = ["product_specification_documented", "infrastructure_proposed", "capability_contracted", "equipment_procured",
          "equipment_installed", "subsystem_commissioned", "integrated_configuration_verified", "operational_performance_observed"]
BASIS_CLASS = {"published": "follows NVIDIA's published procedure", "derived_from_published": "derived from published sources",
               "project_defined": "project-defined, pending engineering review"}


def state_label(s: str | None) -> str:
    return s.replace("_", " ").capitalize() if s else ""


def attr_label(a: str) -> str:
    return {"dated": "Date", "period": "Observation period"}.get(a, state_label(a))


def lower_first(s: str) -> str:
    return s[:1].lower() + s[1:]


def preflight_rows(pf):
    """Per Workflow C requirement: the IDE-014 matrix row with its record types, substitutes, category errors and dependencies."""
    from render_rack_deployment_dossier import DOMAIN_LABEL
    d, ide006 = pf["model"], pf["ide006"]
    types = {t["id"]: t for t in d["record_types"]}
    reqs = {q["id"]: q for q in ide006["requirements"]}
    domain_of = {rc: dm["id"] for dm in d["domains"] for rc in dm["workflow_c_ids"]}
    covers: dict[str, list[str]] = {}
    for m in d["matrix"]:
        for q in m["ide006_requirement_ids"]:
            covers.setdefault(q, []).append(m["requirement_id"])
    rank = {s: i for i, s in enumerate(STATES)}
    rows = []
    for m in d["matrix"]:
        listed = [types[x] for x in m["record_type_ids"]]
        target = m["target_state"]
        access = target == "access"
        substitutes = [] if access else [t for t in d["record_types"] if t["dimension"] == "technical" and not t["site_specific"]
                                         and t["id"] not in m["record_type_ids"] and rank[t["state_ceiling"]] < rank[target]]
        errors = [ce for c in d["chain"] if set(c["record_type_ids"]) & set(m["record_type_ids"]) for ce in c["category_errors"]]
        own = set(m["ide006_requirement_ids"])
        deps = []
        for edge in d["dependencies"]:
            if edge["dependent"] in own and edge["prerequisite"] not in own:
                other, direction = edge["prerequisite"], "upstream"
            elif edge["prerequisite"] in own and edge["dependent"] not in own:
                other, direction = edge["dependent"], "downstream"
            else:
                continue
            deps.append({"direction": direction, "edge": edge, "other": reqs[other], "rows": [r for r in covers.get(other, []) if r != m["requirement_id"]]})
        rows.append({"m": m, "records": listed, "access": access, "substitutes": substitutes, "errors": errors, "deps": deps,
                     "domain": DOMAIN_LABEL[domain_of[m["requirement_id"]]], "rank": rank})
    return rows


def preflight_block(model, pf) -> list[str]:
    cfg, d = pf["config"], pf["model"]
    packet = cfg["packet"]
    attrs = d["attributes"]
    titles = {r["id"]: r["title"] for w in model["workflows"] for r in w["requirements"]}
    p = "workflow-rack-deployment-preflight"
    out = [f'<section class="wb-preflight" id="{p}" aria-labelledby="{p}-title" data-format="{e(packet["format"])}" '
           f'data-format-version="{e(packet["format_version"])}" data-record-model="{e(cfg["record_model"]["dossier_id"])}" '
           f'data-record-model-file="{e(cfg["record_model"]["file"])}" data-record-model-compiled="{e(cfg["record_model"]["compiled_at"])}" '
           f'data-states-release="{e(cfg["evidence_states_release"])}">']
    out.append(f'<h3 id="{p}-title">Documentary preflight for a Workflow C requirement</h3>')
    out.append(f'<div class="framing-note pf-label"><strong class="pf-packet-label">{e(packet["label"])}</strong>'
               f'<span><span class="pf-disclaimer">{e(packet["disclaimer"])}</span> <span class="pf-research-status">{e(packet["research_status"])}</span> '
               f'Record model compiled: {e(cfg["record_model"]["compiled_at"])} (IDE-014).</span></div>')
    out.append('<p class="detail">Choose one requirement. The preflight names the record that should exist and who holds it, the attributes '
               'that record must carry, and the highest evidence state that kind of record could support. Mark the record and each attribute as '
               'you find it in the document you hold. The preflight then lists what is missing, why it matters, what to request next, and what '
               'even a complete record would not establish. Definitions: <a href="/data/deployment-evidence-preflight.json">'
               'deployment-evidence-preflight.json</a>.</p>')
    out.append(f'<p class="detail pf-boundary">{e(cfg["boundary"])}</p>')
    out.append('<dl class="wb-definitions pf-status-defs" aria-label="Preflight selections">')
    for k, label in cfg["attribute_statuses"].items():
        out.append(f'<dt data-status="{k}" data-document-label="{e(cfg["document_statuses"][k])}">{e(label)}</dt>'
                   f'<dd>{e(cfg["status_definitions"][k])}</dd>')
    out.append("</dl>")
    out.append('<div class="pf-statements" hidden>' + "".join(
        f'<p data-key="{k}">{e(packet[k])}</p>' for k in ("no_state_statement", "completeness_boundary", "dependency_rule", "access_rule")) + "</div>")
    out.append('<details class="evidence-trace pf-guide"><summary>Why each attribute matters</summary><dl>')
    for a, desc in attrs.items():
        g = cfg["attribute_guidance"][a]
        out.append(f'<dt data-attr="{a}">{e(attr_label(a))}</dt><dd data-attr="{a}"><span class="pf-desc">{e(desc)}.</span> '
                   f'<span class="pf-sig">{e(g["significance"])}</span> <span class="pf-ask" hidden>{e(g["request"])}</span></dd>')
    out.append("</dl></details>")
    out.append('<details class="evidence-trace pf-boundaries"><summary>Evidence-state boundaries that always apply</summary><ul>')
    for b in cfg["boundaries"]:
        out.append(f'<li data-boundary="{b["id"]}">{e(b["statement"])} <span class="muted">({", ".join(f"<code>{r}</code>" for r in b["refs"])})</span></li>')
    out.append("</ul></details>")
    out.append('<div class="pf-picker" hidden></div>')
    out.append('<div class="pf-toolbar" role="group" aria-label="Documentary preflight actions" hidden></div>')
    for row in preflight_rows(pf):
        m = row["m"]
        rid = m["requirement_id"]
        sid = f"pf-{rid}"
        out.append(f'<section class="pf-req" id="{sid}" data-requirement="{rid}" data-target-state="{m["target_state"]}" aria-labelledby="{sid}-title">')
        out.append(f'<h4 id="{sid}-title"><code>{rid[:5]}</code> <span class="pf-title">{e(titles[rid])}</span></h4>')
        out.append('<dl class="pf-summary">')
        out.append(f'<dt>Claim under examination</dt><dd class="pf-claim">{e(m["claim"])}</dd>')
        out.append(f'<dt>Domain</dt><dd class="pf-domain">{e(row["domain"])}</dd>')
        if row["access"]:
            out.append(f'<dt>Claim\'s target</dt><dd class="pf-target">Access, which is not a deployment state. {e(packet["access_rule"])}</dd>')
        else:
            out.append(f'<dt>Claim\'s target state</dt><dd class="pf-target">{e(state_label(m["target_state"]))}</dd>')
        if m["stage_note"]:
            out.append(f'<dt>Stage note</dt><dd class="pf-stage-note">{e(m["stage_note"])}</dd>')
        out.append(f'<dt>Record holder</dt><dd class="pf-holder">{e(m["holder"])}</dd>')
        out.append('<dt>Verification conditions</dt><dd><ul class="pf-conditions">' + "".join(f"<li>{e(c)}</li>" for c in m["verification_conditions"]) + "</ul></dd>")
        out.append(f'<dt>Potential supported claim</dt><dd class="pf-supported">What a qualified reviewer could investigate, given an authentic, '
                   f'sufficient record: {e(lower_first(m["supported_inference"]))}.</dd>')
        out.append(f'<dt>Prohibited inference</dt><dd class="pf-prohibited">{e(m["prohibited_inference"])}.</dd>')
        out.append(f'<dt>Public record</dt><dd class="pf-gap">{e(m["gap"])}. Record status in the IDE-014 model: not obtained.</dd>')
        out.append("</dl>")
        for t in row["records"]:
            if row["access"]:
                ceiling = 'None: an access record supports no deployment state'
                note = ""
                bound = ""
            else:
                ceiling = state_label(t["state_ceiling"])
                bound = " (an upper bound, not a state reached)"
                note = ("" if row["rank"][t["state_ceiling"]] >= row["rank"][m["target_state"]] else
                        f' On its own this record type cannot support the claim\'s target state ({e(state_label(m["target_state"]))}).')
            out.append(f'<div class="pf-record" data-record="{t["id"]}" data-ceiling="{t["state_ceiling"] or ""}">')
            out.append(f'<h5>Required record: <span class="pf-record-label">{e(t["label"])}</span></h5>')
            out.append(f'<p class="pf-record-meta">Holder: <span class="pf-record-holder">{e(t["holder"])}</span> · Site-specific: '
                       f'{"yes" if t["site_specific"] else "no"} · Highest state this kind of record could support after human review: '
                       f'<strong class="pf-ceiling">{ceiling}</strong>{bound}.{note}</p>')
            out.append(f'<p class="pf-dne"><strong>Even complete, it does not establish:</strong> <span>{e(t["does_not_establish"])}.</span></p>')
            out.append('<div class="pf-doc-controls"></div>')
            out.append(f'<ul class="pf-attrs" aria-label="Attributes this record must carry">')
            for a in t["required_attributes"]:
                out.append(f'<li class="pf-attr" data-attr="{a}"><span class="pf-attr-label">{e(attr_label(a))}</span>: '
                           f'<span class="pf-attr-desc">{e(attrs[a])}</span><div class="pf-attr-controls"></div></li>')
            out.append("</ul></div>")
        if row["substitutes"]:
            out.append('<div class="pf-substitutes"><h5>Documents that cannot substitute for it</h5><ul>' + "".join(
                f'<li data-record="{t["id"]}"><span class="pf-sub-label">{e(t["label"])}</span>: ceiling {e(state_label(t["state_ceiling"]))}; '
                f'does not establish <span class="pf-sub-dne">{e(t["does_not_establish"][0].lower() + t["does_not_establish"][1:])}</span>.</li>'
                for t in row["substitutes"]) + "</ul></div>")
        out.append('<div class="pf-errors"><h5>Category errors to avoid</h5><ul>' + "".join(
            f'<li data-error="{ce["id"]}"><span class="pf-error-inference">{e(ce["inference"])}</span>: <span class="pf-error-why">{e(ce["why_not"])}</span>.</li>'
            for ce in row["errors"]) + "</ul></div>")
        out.append('<div class="pf-deps"><h5>Documentary dependencies</h5>')
        if row["deps"]:
            out.append("<ul>")
            for dep in row["deps"]:
                o, edge = dep["other"], dep["edge"]
                where = (", requested under " + ", ".join(f"<code>{r}</code>" for r in dep["rows"])) if dep["rows"] else ", which no Workflow C requirement requests"
                lead = "Presupposes records for" if dep["direction"] == "upstream" else "Is presupposed by"
                out.append(f'<li data-direction="{dep["direction"]}" data-ide006="{o["id"]}">{lead} <code>{o["id"]}</code> '
                           f'({e(o["required_capability"])}){where}. Basis: {BASIS_CLASS[edge["basis_class"]]}.</li>')
            out.append("</ul>")
        else:
            out.append("<p>None recorded in the IDE-014 model.</p>")
        out.append(f'<p class="pf-dep-rule">{e(packet["dependency_rule"])}</p></div>')
        out.append('<div class="pf-result" hidden></div>')
        out.append("</section>")
    out.append("</section>")
    return out


def items(values) -> str:
    return "".join(f"<li>{e(v)}</li>" for v in values)


def requirement(r, n, letter, registry, findings, unresolved, conflicts) -> list[str]:
    css, short, label = AVAILABILITY[r["public_availability"]]
    stage = r.get("deployment_stage")
    out = [f'<li class="wb-req" id="{r["id"]}" data-category="{r["evidence_category"]}" data-basis="{r["basis"]}" '
           f'data-availability="{r["public_availability"]}" data-reference="{e(r["reference"])}">']
    out.append(f'<div class="step-head"><span class="step-no">{letter}{n}</span><h4 class="wb-req-title">{e(r["title"])}</h4>'
               f'<span class="tag {css}" title="{label}">{short}</span><span class="visually-hidden">Public availability: </span>'
               f'<span class="wb-avail">{label}</span></div>')
    meta = [CATEGORY_LABEL[r["evidence_category"]], LAYER_NAME[r["ontology_layer"]], BASIS_LABEL[r["basis"]]]
    if stage:
        meta.insert(0, f"Stage: {STAGE_LABEL[stage]}")
    out.append(f'<p class="wb-meta">{" · ".join(e(m) for m in meta)}</p>')
    out.append(f'<p class="wb-doc"><strong>Document to request.</strong> {e(r["document_requested"])}</p>')
    out.append(f'<p class="wb-why"><strong>Why it matters.</strong> {e(r["why_it_matters"])}</p>')
    out.append(f'<p class="step-link"><a href="{e(r["reference"])}">Reference section →</a></p>')
    out.append('<details class="evidence-trace"><summary>Evidence trace and limits</summary><dl>')
    out.append(f'<dt>Technical scope</dt><dd>{e(r["technical_scope"])}</dd>')
    if r["finding_ids"]:
        out.append("<dt>Release findings</dt><dd>" + ", ".join(
            f'<code>{f}</code> <span class="muted">(<code>{findings[f]}</code>)</span>' for f in r["finding_ids"]) + "</dd>")
    if r["source_ids"]:
        src = []
        for sid in r["source_ids"]:
            s = registry[sid]
            src.append(f'<li><code>{sid}</code>: {e(s["publisher"])}, “{e(s["title"])}”, '
                       f'{e(s.get("publication_date") or s.get("effective_date") or "undated")}. '
                       f'<a href="{e(s["canonical_url"])}">Original source</a></li>')
        out.append(f'<dt>Registered sources</dt><dd><ul class="wb-sources">{"".join(src)}</ul></dd>')
    else:
        out.append('<dt>Registered sources</dt><dd>None. No reviewed source publishes this; the requirement is this project\'s '
                   'recommendation.</dd>')
    if r["unresolved_ids"]:
        qs = "".join(f'<li><code>{u}</code>: {e(unresolved[u]["question"])}</li>' for u in r["unresolved_ids"])
        out.append(f'<dt>Open questions</dt><dd><ul class="wb-unresolved">{qs}</ul></dd>')
    if r["conflict_ids"]:
        cs = "".join(f'<li><code>{c}</code>: <a href="/sources/#{c}">{e(conflicts[c]["title"])}</a> '
                     f'({ISSUE_STATE[conflicts[c]["state"]]})</li>' for c in r["conflict_ids"])
        out.append(f'<dt>Conflict register</dt><dd><ul class="wb-conflicts">{cs}</ul></dd>')
    out.append(f'<dt>Consider on receipt</dt><dd><ul>{items(r["acceptance_considerations"])}</ul></dd>')
    out.append(f'<dt>Limitations</dt><dd><ul class="wb-limitations">{items(r["limitations"])}</ul></dd>')
    out.append(f'<dt>After expert review</dt><dd>Could support a bounded statement about: {e(r["permits_after_review"])}</dd>')
    out.append(f'<dt>Not established without review</dt><dd class="wb-not-established">{e(r["not_established_without_review"])}</dd>')
    out.append("</dl></details>")
    out.append('<div class="wb-controls"></div>')
    out.append("</li>")
    return out


def render(model, registry, findings, unresolved, conflicts, preflight) -> str:
    wfs = model["workflows"]
    total = sum(len(w["requirements"]) for w in wfs)
    out = [START]
    out.append('<section class="reference-sections" id="workbench-guide" aria-labelledby="guide-title">')
    out.append('<article class="reference-block"><div class="block-index">01</div><div>')
    out.append('<h2 id="guide-title">How to use the workbench</h2>')
    out.append(f'<p class="detail">Each workflow starts from one research question and lists the documents a researcher would need to answer '
               f'it, {total} requirements in all. For every requirement the catalog says whether reviewed public sources already publish '
               'the information, which release findings and registered sources it rests on, which entries in the conflict register affect '
               'it, and what a received document would still not establish without expert review.</p>')
    out.append(f'<div class="framing-note"><strong>Boundary</strong><span>{e(model["boundary"])} Compiled {e(model["compiled_at"])}; '
               'scientific review pending. Machine-readable model: '
               '<a href="/data/industrial-evidence-requests.json">industrial-evidence-requests.json</a>.</span></div>')
    out.append('<h3>Collection statuses</h3><p class="detail">With JavaScript on, each requirement has a status you set yourself. '
               'The statuses record your own collection progress, not a property of the evidence. Nothing is summed or scored.</p>')
    out.append('<dl class="wb-definitions">' + "".join(f"<dt>{e(v)}</dt><dd><code>{k}</code></dd>"
                                                      for k, v in model["session_statuses"].items()) + "</dl>")
    out.append('<h3>Public availability</h3><ul class="class-legend" aria-label="Public availability labels">'
               + "".join(f'<li><span class="tag {c}">{s}</span>{lab}: {e(model["availability_definitions"][k])}</li>'
                         for k, (c, s, lab) in AVAILABILITY.items()) + "</ul>")
    out.append('<h3>Basis</h3><dl class="wb-definitions">' + "".join(f"<dt>{BASIS_LABEL[k]}</dt><dd>{e(v)}</dd>"
                                                                   for k, v in model["basis_definitions"].items()) + "</dl>")
    out.append('<nav class="pathway-chooser" aria-label="Choose a workflow"><ol>')
    for w in wfs:
        out.append(f'<li><a href="#{w["id"]}"><span class="layer-id">{w["letter"]}</span><span><strong>{e(w["title"])}</strong>'
                   f'<small>{e(w["research_question"])}</small></span></a></li>')
    out.append("</ol></nav></div></article></section>")
    for n, w in enumerate(wfs, start=2):
        letter = w["letter"]
        out.append(f'<section class="reference-sections" aria-labelledby="{w["id"]}-title">')
        out.append(f'<article class="reference-block wb-workflow" id="{w["id"]}"><div class="block-index">{n:02d}</div><div>')
        out.append(f'<h2 id="{w["id"]}-title">Workflow {letter}: {e(w["title"])}</h2>')
        out.append(f'<p class="pathway-question wb-question"><strong>Research question.</strong> {e(w["research_question"])}</p>')
        out.append(f'<p class="detail"><strong>Objective.</strong> {e(w["objective"])} Related pathway: '
                   f'<a href="/sovereignty-stack/#{w["pathway_id"]}">Pathway {letter} on the Sovereignty Stack</a>.</p>')
        stages = [r.get("deployment_stage") for r in w["requirements"] if r.get("deployment_stage")]
        if stages:
            order = [s for s in model["deployment_stages"] if s in stages]
            out.append('<p class="detail">Stages are kept apart: a record for one stage says nothing about the next.</p>')
            out.append('<ol class="wb-stages" aria-label="Deployment stages">' + "".join(
                f"<li>{e(STAGE_LABEL[s])} <span class=\"muted\">({stages.count(s)})</span></li>" for s in order) + "</ol>")
        out.append(f'<div class="wb-toolbar" role="group" aria-label="Workflow {letter} checklist actions" hidden></div>')
        out.append(f'<ol class="pathway-steps wb-requirements" aria-label="Workflow {letter} evidence requirements">')
        for k, r in enumerate(w["requirements"], start=1):
            out += requirement(r, k, letter, registry, findings, unresolved, conflicts)
        out.append("</ol>")
        if w["id"] == preflight["config"]["workflow_id"]:
            out += preflight_block(model, preflight)
        out.append("</div></article></section>")
    out.append(END)
    return "\n".join(out)


def apply(page_text: str, block: str) -> str:
    if START not in page_text or END not in page_text:
        raise SystemExit("workbench markers not found in research-workbench/index.html")
    return page_text[: page_text.index(START)] + block + page_text[page_text.index(END) + len(END):]


def in_sync() -> bool:
    current = PAGE.read_text(encoding="utf-8")
    return apply(current, render(*load())) == current


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--check", action="store_true", help="fail if the page does not match the model")
    args = parser.parse_args(argv)
    if args.check:
        if not in_sync():
            print("FAIL: research-workbench/index.html is out of date; run scripts/render_research_workbench.py", file=sys.stderr)
            raise SystemExit(1)
        print("PASS: research workbench matches data/industrial-evidence-requests.json.")
        return
    PAGE.write_text(apply(PAGE.read_text(encoding="utf-8"), render(*load())), encoding="utf-8")
    print("workbench rendered")


if __name__ == "__main__":
    main()
