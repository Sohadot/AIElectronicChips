#!/usr/bin/env python3
"""Render the cross-layer research-pathway explorer into /sovereignty-stack/ (IDE-007).

The explorer is generated from data/reference-pathways.json, the evidence releases and the
source registry, and written between two markers in sovereignty-stack/index.html. It is plain
HTML: every pathway, step and evidence trace is readable without JavaScript.

    python3 scripts/render_reference_pathways.py          # rewrite the page section
    python3 scripts/render_reference_pathways.py --check  # fail if the page is out of date
"""

from __future__ import annotations

import argparse
import html
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MODEL = ROOT / "data" / "reference-pathways.json"
PAGE = ROOT / "sovereignty-stack" / "index.html"
START, END = "<!-- reference-pathways:start -->", "<!-- reference-pathways:end -->"

LAYER_ORDER = [("design", "01", "Design"), ("fabrication", "02", "Fabrication"), ("packaging", "03", "Packaging"),
               ("memory", "04", "Memory"), ("interconnect", "05", "Interconnect"), ("power_thermal", "06", "Power / Thermal"),
               ("controls", "07", "Controls"), ("deployment", "08", "Deployment")]
LAYER_NAME = {k: n for k, _, n in LAYER_ORDER}
TAGS = {"verified_fact": ("tag-s", "S", "Definition or verified fact"), "attributed_statement": ("tag-a", "A", "Attributed"),
        "bounded_analysis": ("tag-c", "C", "Bounded analysis"), "unresolved": ("tag-u", "U", "Unresolved"),
        "not_supported": ("tag-u", "N", "Not supported")}
VERDICT_LABEL = {"valid": "Valid", "conditional": "Conditional", "unsupported": "Unsupported"}
STATE_LABEL = {"product_specification_documented": "Product specification documented", "infrastructure_proposed": "Infrastructure proposed",
               "capability_contracted": "Capability contracted", "equipment_procured": "Equipment procured",
               "equipment_installed": "Equipment installed", "subsystem_commissioned": "Subsystem commissioned",
               "integrated_configuration_verified": "Integrated configuration verified",
               "operational_performance_observed": "Operational performance observed", "not_established": "Not established"}
LETTERS = {"pathway-hbm-to-advanced-packaging": "A", "pathway-memory-bandwidth-to-data-movement": "B",
           "pathway-rack-to-deployable-compute": "C"}

SHORT = {"pathway-hbm-to-advanced-packaging": "HBM to packaging", "pathway-memory-bandwidth-to-data-movement": "Bandwidth to data",
         "pathway-rack-to-deployable-compute": "Rack to deployment"}

e = html.escape
MAINTENANCE: dict[str, list[dict]] = {}
ISSUE_STATE = {"open_conflict": "open conflict", "missing_primary_evidence": "missing primary evidence",
               "version_scope_difference": "version-scope difference", "source_access_blocked": "source access blocked",
               "requires_reassessment": "requires reassessment", "resolved_with_evidence": "resolved with evidence; public wording under review"}


def ranges(nums: list[int]) -> str:
    """Compress step numbers: [4, 5, 6, 8] -> '4–6, 8'."""
    out, start = [], None
    for i, n in enumerate(nums):
        if start is None:
            start = n
        if i + 1 == len(nums) or nums[i + 1] != n + 1:
            out.append(str(start) if start == n else f"{start}–{n}")
            start = None
    return ", ".join(out)


def load():
    model = json.loads(MODEL.read_text(encoding="utf-8"))
    registry = {s["id"]: s for s in json.loads((ROOT / "data" / "source-registry.json").read_text(encoding="utf-8"))["source_records"]}
    unresolved, releases = {}, {}
    for p in sorted((ROOT / "data" / "research").glob("*.json")):
        r = json.loads(p.read_text(encoding="utf-8"))
        releases[r["release_id"]] = r
        for u in r["unresolved"]:
            unresolved[u["id"]] = u
    MAINTENANCE.clear()
    conflicts_path = ROOT / "data" / "evidence-conflicts.json"
    if conflicts_path.is_file():  # IDE-008: steps affected by a register issue carry a maintenance note
        for issue in json.loads(conflicts_path.read_text(encoding="utf-8"))["issues"]:
            for sid in issue["affected_pathway_steps"]:
                MAINTENANCE.setdefault(sid, []).append(issue)
    return model, registry, unresolved, releases


def page_title(route: str) -> str:
    text = (ROOT / route.strip("/") / "index.html").read_text(encoding="utf-8")
    return html.unescape(re.search(r"<h1[^>]*>(.*?)</h1>", text, re.S).group(1)).strip()


def section_title(route: str, anchor: str) -> str:
    text = (ROOT / route.strip("/") / "index.html").read_text(encoding="utf-8")
    m = re.search(r'id="%s"[^>]*>.*?<h2[^>]*>(.*?)</h2>' % re.escape(anchor), text, re.S)
    title = re.sub(r"<[^>]+>", "", m.group(1)) if m else anchor
    return re.sub(r"\s+[SACU]$", "", html.unescape(title).strip())


def tag(cls: str) -> str:
    css, letter, label = TAGS[cls]
    return f'<span class="tag {css}" title="{label}">{letter}</span><span class="visually-hidden">{label}: </span>'


def figure(model) -> str:
    x0, w, y0, h = 150, 88, 70, 58
    rows = []
    for i, pw in enumerate(model["pathways"]):
        letter = LETTERS[pw["id"]]
        y = y0 + i * h
        rows.append(f'<text class="f-lbl" x="20" y="{y + 26}">PATHWAY {letter}</text>')
        rows.append(f'<text class="f-note" x="20" y="{y + 42}">{e(SHORT[pw["id"]])}</text>')
        for j, (layer, _, _) in enumerate(LAYER_ORDER):
            nums = [k + 1 for k, st in enumerate(pw["steps"]) if st["ontology_layer"] == layer]
            x = x0 + j * w
            cls = "f-base" if nums else "f-rdl"
            rows.append(f'<rect class="{cls}" x="{x}" y="{y}" width="{w - 6}" height="{h - 10}" rx="2"/>')
            if nums:
                rows.append(f'<text class="f-val" x="{x + (w - 6) / 2:.0f}" y="{y + 30}" text-anchor="middle">{letter}{ranges(nums)}</text>')
    heads = []
    for j, (_, code, name) in enumerate(LAYER_ORDER):
        cx = x0 + j * w + (w - 6) / 2
        heads.append(f'<text class="f-axis" x="{cx:.0f}" y="40" text-anchor="middle">{code}</text>')
        heads.append(f'<text class="f-note" x="{cx:.0f}" y="56" text-anchor="middle">{e(name)}</text>')
    desc = " ".join(
        f"Pathway {LETTERS[pw['id']]}, {pw['title']}: " + "; ".join(
            f"{LAYER_NAME[layer]} at step{'s' if len(n) > 1 else ''} {', '.join(n)}"
            for layer, _, _ in LAYER_ORDER
            for n in [[str(k + 1) for k, st in enumerate(pw["steps"]) if st["ontology_layer"] == layer]] if n) + "."
        for pw in model["pathways"])
    yl = y0 + len(model["pathways"]) * h + 18
    return "\n".join([
        '<svg viewBox="0 0 870 300" role="img" aria-labelledby="pathway-fig-title pathway-fig-desc">',
        '<title id="pathway-fig-title">Which ontology layers each research pathway crosses, and at which steps</title>',
        f'<desc id="pathway-fig-desc">A grid of three pathways by the eight ontology layers. Filled cells show the step numbers at which a pathway reaches a layer; empty cells are layers it does not use. {e(desc)}</desc>',
        '<text class="f-panel" x="20" y="22">Ontology layers crossed, by step</text>',
        *heads, *rows,
        f'<text class="f-note" x="20" y="{yl}">A cell shows where a pathway reads evidence, not a dependency between layers. Steps run in order within each pathway.</text>',
        "</svg>"])


def render(model, registry, unresolved, releases) -> str:
    out = [START]
    pws = model["pathways"]
    # Introduction, chooser, figure and workflow.
    out.append('<section class="reference-sections" id="research-pathways" aria-labelledby="pathways-title">')
    out.append('<article class="reference-block"><div class="block-index">04</div><div>')
    out.append('<h2 id="pathways-title">Cross-layer research pathways</h2>')
    out.append('<p class="detail">The layer references each go deep on one part of the stack. The pathways below read across them. Each '
               'starts from one technical question, follows ordered steps through the reference sections that bear on it, and shows for every '
               'step which release findings and registered sources it rests on, what they do not establish, and what evidence would settle '
               'the open points.</p>')
    out.append('<div class="framing-note pathway-boundary"><strong>Navigation, not approval</strong><span>A pathway links public evidence. '
               'It is not a relationship in the Dependency Evidence Atlas, which has no approved relationships yet, and it carries no score or '
               f'verdict. Compiled {e(model["compiled_at"])}; scientific review pending. Machine-readable model: '
               '<a href="/data/reference-pathways.json">reference-pathways.json</a>.</span></div>')
    out.append('<nav class="pathway-chooser" aria-label="Choose a research pathway"><ol>')
    for pw in pws:
        out.append(f'<li><a href="#{pw["id"]}"><span class="layer-id">{LETTERS[pw["id"]]}</span><span><strong>{e(pw["title"])}</strong>'
                   f'<small>{e(pw["research_question"])}</small></span></a></li>')
    out.append("</ol></nav>")
    out.append('<figure class="ref-figure"><div class="figure-frame" tabindex="0" role="region" aria-label="Figure 1 drawing; scrolls horizontally on narrow screens">')
    out.append(figure(model))
    out.append('</div><figcaption>Figure 1. Original analysis: the ontology layers each pathway reads, by step number. Generated from '
               'the pathway model.</figcaption></figure>')
    out.append('<h3>How to read a pathway</h3><ol class="detail pathway-workflow">'
               '<li><strong>Question.</strong> Start from the stated research question and its scope.</li>'
               '<li><strong>Layers.</strong> Note which ontology layers the question crosses.</li>'
               '<li><strong>Steps.</strong> Follow the steps in order; each says why its reference section is relevant.</li>'
               '<li><strong>Sources.</strong> Open the evidence trace to see the release findings and registered sources behind a step.</li>'
               '<li><strong>Statements.</strong> Read what the pathway supports, separated into attributed, bounded, unresolved and unsupported.</li>'
               '<li><strong>Limitations.</strong> Check what each step and the pathway as a whole do not establish.</li>'
               '<li><strong>Unresolved.</strong> Note the open questions the pathway inherits from the releases.</li>'
               '<li><strong>Next evidence.</strong> Use the stated next evidence to direct further research.</li></ol>')
    out.append('<ul class="class-legend" aria-label="Evidence classes used in the pathways">'
               + "".join(f'<li><span class="tag {c}">{l}</span>{lab}</li>' for c, l, lab in TAGS.values()) + "</ul>")
    out.append("</div></article>")
    # One block per pathway.
    for n, pw in enumerate(pws, start=5):
        letter = LETTERS[pw["id"]]
        out.append(f'<article class="reference-block pathway" id="{pw["id"]}"><div class="block-index">{n:02d}</div><div>')
        out.append(f'<h2>Pathway {letter}: {e(pw["title"])}</h2>')
        out.append(f'<p class="pathway-question"><strong>Research question.</strong> {e(pw["research_question"])}</p>')
        out.append(f'<p class="detail">{e(pw["technical_purpose"])}</p>')
        layers = ", ".join(LAYER_NAME[l] for l in pw["ontology_layers"])
        rel_ids = ", ".join(f"<code>{r}</code>" for r in pw["evidence_release_ids"])
        out.append('<dl class="pathway-scope">'
                   f'<dt>Layers</dt><dd>{e(layers)}</dd>'
                   f'<dt>Technical scope</dt><dd>{e(pw["scope"]["technical"])}</dd>'
                   f'<dt>Time</dt><dd>{e(pw["scope"]["temporal"])}</dd>'
                   f'<dt>Releases</dt><dd>{rel_ids}</dd>'
                   f'<dt>Assumptions</dt><dd>{"; ".join(e(a) for a in pw["assumptions"])}</dd></dl>')
        out.append(f'<h3>Steps</h3><ol class="pathway-steps">')
        for k, st in enumerate(pw["steps"], start=1):
            href = f'{st["route"]}#{st["anchor"]}'
            target = f'{page_title(st["route"])}: {section_title(st["route"], st["anchor"])}'
            out.append(f'<li id="step-{st["id"]}"><div class="step-head"><span class="step-no">{letter}{k}</span>'
                       f'<h4>{e(st["title"])}</h4>{tag(st["evidence_class"])}</div>')
            out.append(f'<p>{e(st["relevance"])}</p>')
            out.append(f'<p class="step-link"><a href="{href}">{e(target)} →</a></p>')
            out.append('<details class="evidence-trace"><summary>Evidence trace</summary><dl>')
            out.append(f'<dt>Release findings</dt><dd>{", ".join(f"<code>{f}</code>" for f in st["finding_ids"])} '
                       f'<span class="muted">in <code>{st["release_id"]}</code></span></dd>')
            src_items = []
            for sid in st["source_ids"]:
                s = registry[sid]
                pending = " (pending review)" if s.get("status") == "pending_review" else ""
                src_items.append(f'<li><code>{sid}</code>: {e(s["publisher"])}, “{e(s["title"])}”, '
                                 f'{e(s.get("publication_date") or s.get("effective_date") or "undated")}{pending}. '
                                 f'<a href="{e(s["canonical_url"])}">Original source</a></li>')
            out.append(f'<dt>Registered sources</dt><dd><ul>{"".join(src_items)}</ul></dd>')
            out.append(f'<dt>Scope</dt><dd>{e(st["scope"]["technical"])}. {e(st["scope"]["temporal"])}. {e(st["scope"]["geographic"])}.</dd>')
            out.append(f'<dt>Does not establish</dt><dd><ul>{"".join(f"<li>{e(x)}</li>" for x in st["limitations"])}</ul></dd>')
            if st["unresolved_ids"]:
                qs = "".join(f'<li><code>{u}</code>: {e(unresolved[u]["question"])}</li>' for u in st["unresolved_ids"])
                out.append(f"<dt>Open questions</dt><dd><ul>{qs}</ul></dd>")
            if st["next_evidence"]:
                out.append(f'<dt>Next evidence</dt><dd>{e(st["next_evidence"])}</dd>')
            if MAINTENANCE.get(st["id"]):
                notes = "".join(f'<li><a href="/sources/#{i["id"]}">{e(i["title"])}</a>: {ISSUE_STATE[i["state"]]}</li>'
                                for i in MAINTENANCE[st["id"]])
                out.append(f"<dt>Evidence maintenance</dt><dd><ul>{notes}</ul></dd>")
            out.append("</dl></details></li>")
        out.append("</ol>")
        if pw.get("comparisons"):
            out.append('<h3>Which comparisons hold</h3><div class="table-scroll" tabindex="0" role="region" '
                       'aria-label="Bandwidth comparisons and their validity (scrollable table)"><table class="data-table">'
                       '<caption>Pairs of published figures, and whether comparing them is valid, conditional or unsupported.</caption>'
                       '<thead><tr><th scope="col">Figures compared</th><th scope="col">Verdict</th><th scope="col">Why</th>'
                       '<th scope="col">Findings</th></tr></thead><tbody>')
            for cmp in pw["comparisons"]:
                figs = " vs ".join(e(f["value"]) for f in cmp["figures"])
                fids = ", ".join(sorted({f"<code>{f['finding_id']}</code>" for f in cmp["figures"]}))
                css = {"valid": "tag-s", "conditional": "tag-c", "unsupported": "tag-u"}[cmp["verdict"]]
                out.append(f'<tr><th scope="row">{figs}</th><td><span class="tag {css}">{VERDICT_LABEL[cmp["verdict"]]}</span></td>'
                           f'<td>{e(cmp["reason"])}</td><td>{fids}</td></tr>')
            out.append("</tbody></table></div>")
        if pw.get("evidence_ladder"):
            out.append('<h3>What each stronger statement would need</h3><div class="table-scroll" tabindex="0" role="region" '
                       'aria-label="Evidence ladder (scrollable table)"><table class="data-table">'
                       '<caption>Evidence states, the statement each would support, the record it needs, and whether such a record was '
                       'reviewed for GB200 NVL72. The states are not a required sequence.</caption>'
                       '<thead><tr><th scope="col">Evidence state</th><th scope="col">Statement it would support</th>'
                       '<th scope="col">Record required</th><th scope="col">Reviewed for GB200 NVL72</th></tr></thead><tbody>')
            for row in pw["evidence_ladder"]:
                rv = "Yes" if row["reviewed"] else "No record reviewed"
                out.append(f'<tr><th scope="row">{STATE_LABEL[row["state"]]}</th><td>{e(row["supported_statement"])}</td>'
                           f'<td>{e(row["record_required"])}</td><td>{rv}</td></tr>')
            out.append("</tbody></table></div>")
        out.append('<h3>What the pathway supports</h3><div class="table-scroll" tabindex="0" role="region" '
                   f'aria-label="Pathway {letter} statements (scrollable table)"><table class="data-table">'
                   '<caption>Statements the pathway supports, by evidence class, with the findings or questions they rest on.</caption>'
                   '<thead><tr><th scope="col">Statement</th><th scope="col">Class</th><th scope="col">Basis</th></tr></thead><tbody>')
        for sm in pw["statements"]:
            basis = ", ".join(f"<code>{b}</code>" for b in sm["basis"])
            out.append(f'<tr><th scope="row">{e(sm["text"])}</th><td><span class="tag {TAGS[sm["classification"]][0]}">{TAGS[sm["classification"]][1]}</span>{TAGS[sm["classification"]][2]}</td><td>{basis}</td></tr>')
        out.append("</tbody></table></div>")
        out.append('<div class="posture-grid">')
        out.append(f'<article><h3>Limitations</h3><ul>{"".join(f"<li>{e(x)}</li>" for x in pw["limitations"])}</ul></article>')
        out.append(f'<article><h3>Next evidence to seek</h3><ul>{"".join(f"<li>{e(x)}</li>" for x in pw["next_evidence"])}</ul></article>')
        out.append("</div></div></article>")
    out.append("</section>")
    out.append(END)
    return "\n".join(out)


def apply(page_text: str, block: str) -> str:
    if START not in page_text or END not in page_text:
        raise SystemExit("explorer markers not found in sovereignty-stack/index.html")
    return page_text[: page_text.index(START)] + block + page_text[page_text.index(END) + len(END):]


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--check", action="store_true", help="fail if the page does not match the model")
    args = parser.parse_args(argv)
    block = render(*load())
    current = PAGE.read_text(encoding="utf-8")
    updated = apply(current, block)
    if args.check:
        if updated != current:
            print("FAIL: sovereignty-stack/index.html is out of date; run scripts/render_reference_pathways.py", file=sys.stderr)
            raise SystemExit(1)
        print("PASS: research-pathway explorer matches data/reference-pathways.json.")
        return
    PAGE.write_text(updated, encoding="utf-8")
    print("explorer rendered")


if __name__ == "__main__":
    main()
