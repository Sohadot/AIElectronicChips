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
    return model, registry, findings, unresolved, conflicts


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


def render(model, registry, findings, unresolved, conflicts) -> str:
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
        out.append("</ol></div></article></section>")
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
