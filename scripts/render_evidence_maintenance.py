#!/usr/bin/env python3
"""Render the evidence-maintenance sections of /sources/ (IDE-008) from the committed maintenance files.

Sources: data/source-inspections.json, data/evidence-conflicts.json, data/evidence-impact-index.json and the
registry. Output is plain HTML between two markers in sources/index.html; it needs no JavaScript.

    python3 scripts/render_evidence_maintenance.py          # rewrite the section
    python3 scripts/render_evidence_maintenance.py --check  # fail if out of date
"""

from __future__ import annotations

import argparse
import html
import json
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PAGE = ROOT / "sources" / "index.html"
START, END = "<!-- evidence-maintenance:start -->", "<!-- evidence-maintenance:end -->"
e = html.escape

STATE_LABEL = {"metadata_validated": "Metadata validated", "source_retrieved": "Retrieved", "source_content_compared": "Passages compared",
               "source_changed": "Changed", "source_inaccessible": "Inaccessible", "review_required": "Review required", "not_checked": "Not checked"}
ISSUE_TAG = {"open_conflict": ("tag-u", "Open conflict"), "missing_primary_evidence": ("tag-u", "Missing primary evidence"),
             "version_scope_difference": ("tag-c", "Version-scope difference"), "source_access_blocked": ("tag-u", "Source access blocked"),
             "requires_reassessment": ("tag-c", "Requires reassessment"), "resolved_with_evidence": ("tag-s", "Resolved with evidence")}


def load(name):
    return json.loads((ROOT / "data" / name).read_text(encoding="utf-8"))


def ref_link(ref: str) -> str:
    route, _, anchor = ref.partition("#")
    page = (ROOT / route.strip("/") / "index.html").read_text(encoding="utf-8")
    import re
    title = html.unescape(re.search(r"<h1[^>]*>(.*?)</h1>", page, re.S).group(1)).strip()
    m = re.search(r'id="%s"[^>]*>.*?<h2[^>]*>(.*?)</h2>' % re.escape(anchor), page, re.S)
    section = re.sub(r"\s+[SACU]$", "", html.unescape(re.sub(r"<[^>]+>", "", m.group(1))).strip()) if m else anchor
    return f'<a href="{e(ref)}">{e(title)}: {e(section)}</a>'


def render() -> str:
    log, register, impact = load("source-inspections.json"), load("evidence-conflicts.json"), load("evidence-impact-index.json")
    registry = {s["id"]: s for s in load("source-registry.json")["source_records"]}
    run = log["runs"][-1]
    records = log["records"]
    counts = Counter(s for r in records for s in r["states"])
    passages = sum(r["passage_check"]["quoted_passages"] for r in records if r["passage_check"])
    found = sum(r["passage_check"]["found"] for r in records if r["passage_check"])
    out = [START]
    out.append('<section class="reference-sections" id="evidence-maintenance" aria-labelledby="maintenance-title">')
    # 08: method and states
    out.append('<article class="reference-block"><div class="block-index">08</div><div>')
    out.append('<h2 id="maintenance-title">Evidence maintenance</h2>')
    out.append(f'<div class="framing-note"><strong>Inspected: {e(run["inspected_at"])}</strong><span>An inspection checks a source record and '
               'whether its quoted passages are still published. It is not a review of the claims those passages support, and no human '
               'scientific review is recorded for any source. Access dates in the registry are not changed by an inspection.</span></div>')
    out.append(f'<p class="detail">{e(run["method"])}</p>')
    out.append('<p class="detail">Dates are kept apart. A source has a publication or effective date, the date it was accessed for the '
               'claims it supports, and the date of each inspection. A claim is assessed in its own release, and scientific review would '
               'be a further date that no record yet carries. An old publication date does not make a historical claim wrong. A recent one '
               'does not make a figure suitable for a current comparison.</p>')
    out.append('<div class="table-scroll" tabindex="0" role="region" aria-label="Inspection states (scrollable table)"><table class="data-table">'
               f'<caption>Inspection states recorded on {e(run["inspected_at"])} for the {len(records)} registry records. A record can carry several states.</caption>'
               '<thead><tr><th scope="col">State</th><th scope="col">Meaning</th><th scope="col">Records</th></tr></thead><tbody>')
    for key, meaning in log["state_definitions"].items():
        out.append(f'<tr><th scope="row">{STATE_LABEL[key]}</th><td>{e(meaning)}</td><td>{counts.get(key, 0)}</td></tr>')
    out.append("</tbody></table></div>")
    out.append(f'<p class="detail">Of {passages} passages that release findings quote from retrieved sources, {found} were found in the '
               'documents as published on the inspection date. That shows the passages are still there. It does not show the claims are '
               'still correct, or that no newer edition exists. Machine-readable files: '
               '<a href="/data/source-inspections.json">source-inspections.json</a>, '
               '<a href="/data/evidence-conflicts.json">evidence-conflicts.json</a> and '
               '<a href="/data/evidence-impact-index.json">evidence-impact-index.json</a>.</p>')
    out.append("</div></article>")
    # 09: conflict register
    out.append('<article class="reference-block" id="conflict-register"><div class="block-index">09</div><div>')
    out.append("<h2>Conflict register</h2>")
    out.append(f'<p class="detail">Material contradictions and open evidence questions, as of {e(register["as_of"])}. A newer source does '
               'not settle a conflict by being newer; an issue is resolved only where retrieved primary evidence justifies a narrower conclusion. '
               'Earlier releases stay unchanged as historical records, and the public statements to revise are listed for editorial review.</p>')
    out.append('<ul class="class-legend" aria-label="Register states">'
               + "".join(f'<li><span class="tag {c}">{l.split()[0][0]}</span>{e(l)}</li>' for c, l in ISSUE_TAG.values()) + "</ul>")
    out.append('<ol class="conflict-list">')
    for c in register["issues"]:
        css, label = ISSUE_TAG[c["state"]]
        out.append(f'<li id="{c["id"]}" class="conflict-item"><div class="step-head"><h3>{e(c["title"])}</h3>'
                   f'<span class="tag {css}">{e(label)}</span></div>')
        out.append(f'<p class="pathway-question"><strong>Question.</strong> {e(c["question"])}</p>')
        out.append(f'<p>{e(c["posture"])}</p>')
        out.append('<details class="evidence-trace"><summary>Evidence, scope and what is affected</summary><dl>')
        out.append(f'<dt>Scope</dt><dd>{e(c["scope"]["product"])}. {e(c["scope"]["temporal"])}.</dd>')
        if c["evidence"]:
            items = "".join(
                f'<li><code>{ev["source_id"]}</code>: {e(ev["locator"])}. {e(ev["observation"])} '
                f'<a href="{e(registry[ev["source_id"]]["canonical_url"])}">Original source</a></li>' for ev in c["evidence"])
            out.append(f"<dt>Evidence inspected</dt><dd><ul>{items}</ul></dd>")
        out.append(f'<dt>Registered sources</dt><dd>{", ".join(f"<code>{s}</code>" for s in c["source_ids"])}</dd>')
        out.append(f'<dt>Release findings</dt><dd>{", ".join(f"<code>{f}</code>" for f in c["finding_ids"])}</dd>')
        out.append(f'<dt>Unresolved questions</dt><dd>{", ".join(f"<code>{u}</code>" for u in c["unresolved_ids"])}</dd>')
        out.append(f'<dt>Reference sections</dt><dd><ul>{"".join(f"<li>{ref_link(r)}</li>" for r in c["affected_references"])}</ul></dd>')
        if c["affected_pathway_steps"]:
            links = ", ".join(f'<a href="/sovereignty-stack/#step-{s}">{e(s)}</a>' for s in c["affected_pathway_steps"])
            out.append(f"<dt>Pathway steps</dt><dd>{links}</dd>")
        if c["affected_comparisons"]:
            out.append(f'<dt>Comparisons</dt><dd>{", ".join(f"<code>{x}</code>" for x in c["affected_comparisons"])}</dd>')
        if c["unknown"]:
            out.append(f'<dt>Still unknown</dt><dd><ul>{"".join(f"<li>{e(u)}</li>" for u in c["unknown"])}</ul></dd>')
        out.append(f'<dt>Next evidence</dt><dd>{e(c["next_evidence"])}</dd>')
        if c["downstream_review"]:
            out.append(f'<dt>To revise after editorial review</dt><dd><ul>{"".join(f"<li>{e(d)}</li>" for d in c["downstream_review"])}</ul></dd>')
        hist = "".join(f'<li>{e(h["date"])}, {e(h["event"].replace("_", " "))}: {e(h["detail"])}</li>' for h in c["history"])
        out.append(f"<dt>History</dt><dd><ul>{hist}</ul></dd>")
        out.append("</dl></details></li>")
    out.append("</ol></div></article>")
    # 10: per-source inspection and impact
    out.append('<article class="reference-block" id="source-impact"><div class="block-index">10</div><div>')
    out.append("<h2>Inspection and impact by source</h2>")
    out.append('<p class="detail">For each registered source: what this inspection observed, and what would need re-examination if the '
               'source changed. Impact counts are review targets, not a measure of importance: a source cited often is not more likely to be '
               'right.</p>')
    out.append('<div class="table-scroll" tabindex="0" role="region" aria-label="Inspection and impact by source (scrollable table)">'
               '<table class="data-table"><caption>Inspection outcome and reference impact for every registered source.</caption>'
               '<thead><tr><th scope="col">Source</th><th scope="col">Inspection</th><th scope="col">Passages</th>'
               '<th scope="col">Findings</th><th scope="col">Reference pages</th><th scope="col">Pathway steps</th>'
               '<th scope="col">Register issues</th><th scope="col">Next action</th></tr></thead><tbody>')
    log_by = {r["source_id"]: r for r in records}
    for entry in impact["sources"]:
        sid = entry["source_id"]
        rec = log_by[sid]
        states = ", ".join(STATE_LABEL[s] for s in rec["states"])
        pc = rec["passage_check"]
        passages_cell = f'{pc["found"]} of {pc["quoted_passages"]} found' if pc else "Not compared"
        pages = ", ".join(f'<a href="{e(p)}">{e(p.strip("/") or "home")}</a>' for p in entry["direct"]["reference_pages"]) or "None"
        issues = ", ".join(f'<a href="#{i}">{e(i)}</a>' for i in entry["conflicts"]) or "None"
        pending = " (pending review)" if entry["status"] == "pending_review" else ""
        out.append(f'<tr id="source-{sid}"><th scope="row"><code>{sid}</code>{pending}</th><td>{e(states)}</td><td>{passages_cell}</td>'
                   f'<td>{len(entry["direct"]["findings"])}</td><td>{pages}</td><td>{len(entry["direct"]["pathway_steps"])}</td>'
                   f'<td>{issues}</td><td>{e(rec["next_action"])}</td></tr>')
    out.append("</tbody></table></div></div></article>")
    out.append("</section>")
    out.append(END)
    return "\n".join(out)


def apply(text: str, block: str) -> str:
    if START not in text or END not in text:
        raise SystemExit("evidence-maintenance markers not found in sources/index.html")
    return text[: text.index(START)] + block + text[text.index(END) + len(END):]


def in_sync() -> bool:
    current = PAGE.read_text(encoding="utf-8")
    return apply(current, render()) == current


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args(argv)
    if args.check:
        if not in_sync():
            print("FAIL: sources/index.html maintenance section is out of date", file=sys.stderr)
            raise SystemExit(1)
        print("PASS: /sources/ maintenance section matches the maintenance files.")
        return
    PAGE.write_text(apply(PAGE.read_text(encoding="utf-8"), render()), encoding="utf-8")
    print("maintenance section rendered")


if __name__ == "__main__":
    main()
