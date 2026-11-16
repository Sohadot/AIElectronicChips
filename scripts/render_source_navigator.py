#!/usr/bin/env python3
"""Render the Institutional Evidence Navigator on /sources/ (IDE-017).

Every registered source is written as plain HTML between two markers in sources/index.html, from
data/source-registry.json (identity, scope, limitations), data/evidence-impact-index.json (latest inspection and where
the source is used) and data/evidence-conflicts.json (register issues that name it). Nothing is added to the records:
no score, ranking or confidence is derived. Without JavaScript the full inventory is readable; the local script
assets/js/source-navigator.js only filters what is already on the page and exports the visible records.

    python3 scripts/render_source_navigator.py          # rewrite the navigator section
    python3 scripts/render_source_navigator.py --check  # fail if the page is out of date
"""

from __future__ import annotations

import argparse
import html
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from render_evidence_maintenance import ISSUE_TAG, STATE_LABEL  # noqa: E402
from render_research_workbench import LAYER_NAME  # noqa: E402

PAGE = ROOT / "sources" / "index.html"
REGISTRY = ROOT / "data" / "source-registry.json"
IMPACT = ROOT / "data" / "evidence-impact-index.json"
CONFLICTS = ROOT / "data" / "evidence-conflicts.json"
START, END = "<!-- source-navigator:start -->", "<!-- source-navigator:end -->"
LAYER_ORDER = ["design", "fabrication", "packaging", "memory", "interconnect", "power_thermal", "controls", "deployment"]
TYPE_LABEL = {"official_technical_disclosure": "Official technical disclosure", "company_announcement": "Company announcement",
              "company_filing": "Company filing", "annual_report": "Annual report", "institutional_report": "Institutional report",
              "technical_standard": "Technical standard", "regulation": "Regulation", "government_rule": "Government rule"}
STATUS_LABEL = {"active": "Active", "pending_review": "Pending review", "retired": "Retired"}
STATUS_MEANING = {"active": "identity and metadata reviewed", "pending_review": "further verification needed before detailed claim use",
                  "retired": "historical record; cannot support new findings"}
# Exported fields, in order: the registry record unchanged, then the page's own context.
RECORD_FIELDS = ["id", "title", "publisher", "source_type", "status", "publication_date", "effective_date", "accessed_at",
                 "canonical_url", "ontology_layers", "supported_claim_types", "geographic_scope", "temporal_scope",
                 "confidence_use", "use_limitations"]
BOUNDARY = ("The registry records source identity, metadata and review status. Registration does not "
            "verify any claim. Support "
            "for a statement is assessed finding by finding, only within the claim types and limitations listed. Publication "
            "and access dates show when a source was issued and read, not that its contents are still current. Statements "
            "are attributed to the publisher named, and conflicting evidence stays recorded in the conflict register.")

e = html.escape


def load():
    j = lambda p: json.loads(p.read_text(encoding="utf-8"))
    return j(REGISTRY), {s["source_id"]: s for s in j(IMPACT)["sources"]}, j(CONFLICTS)["issues"]


def words(s: str) -> str:
    return s.replace("_", " ")


def dated(r) -> tuple[str, str]:
    if r.get("publication_date"):
        return "Published", r["publication_date"]
    if r.get("effective_date"):
        return "Effective", r["effective_date"]
    return "Undated", ""


def source_item(r, impact, issues) -> list[str]:
    sid = r["id"]
    kind, date = dated(r)
    layers = [x for x in LAYER_ORDER if x in r["ontology_layers"]]
    mine = [i for i in issues if sid in i["source_ids"]]
    imp = impact.get(sid, {})
    search = " ".join([sid, r["title"], r["publisher"], TYPE_LABEL[r["source_type"]], r["geographic_scope"], r["temporal_scope"],
                       r["confidence_use"], *map(words, r["supported_claim_types"]), *r["use_limitations"],
                       *(LAYER_NAME[x] for x in layers)]).lower()
    out = [f'<li class="nav-source" id="nav-{sid}" data-id="{sid}" data-layers="{" ".join(layers)}" data-type="{r["source_type"]}" '
           f'data-status="{r["status"]}" data-year="{date[:4]}" data-issues="{" ".join(i["id"] for i in mine)}" '
           f'data-search="{e(search)}">']
    out.append(f'<h3 class="nav-title"><a class="nav-url" href="{e(r["canonical_url"])}">{e(r["title"])}</a></h3>')
    pending = ' nav-pending' if r["status"] != "active" else ""
    out.append(f'<p class="nav-meta"><span class="nav-publisher">{e(r["publisher"])}</span> · '
               f'<span class="nav-type" data-value="{r["source_type"]}">{TYPE_LABEL[r["source_type"]]}</span> · '
               f'{kind} <span class="nav-date" data-kind="{kind.lower()}">{e(date)}</span> · '
               f'Accessed <span class="nav-accessed">{e(r["accessed_at"])}</span> · '
               f'<span class="nav-status{pending}" data-value="{r["status"]}">{STATUS_LABEL[r["status"]]}</span>'
               f'<span class="visually-hidden">: {STATUS_MEANING[r["status"]]}</span></p>')
    out.append('<dl class="nav-fields">')
    out.append(f'<dt>Registry ID</dt><dd><code class="nav-id">{sid}</code></dd>')
    out.append('<dt>Ontology layers</dt><dd><ul class="nav-layers">' + "".join(
        f'<li data-value="{x}">{LAYER_NAME[x]}</li>' for x in r["ontology_layers"]) + "</ul></dd>")
    out.append('<dt>Statement types it may support</dt><dd><ul class="nav-claims">' + "".join(
        f'<li data-value="{e(c)}">{e(words(c))}</li>' for c in r["supported_claim_types"]) + "</ul></dd>")
    out.append(f'<dt>Recorded use</dt><dd class="nav-use">{e(r["confidence_use"])}</dd>')
    out.append(f'<dt>Geographic scope</dt><dd class="nav-geo">{e(r["geographic_scope"])}</dd>')
    out.append(f'<dt>Temporal scope</dt><dd class="nav-temporal">{e(r["temporal_scope"])}</dd>')
    out.append('<dt>Limitations</dt><dd><ul class="nav-limits">')
    out += [f"<li>{e(x)}</li>" for x in r["use_limitations"]]  # one per line: each keeps its own negation
    out.append("</ul></dd>")
    insp = imp.get("latest_inspection")
    if insp:
        out.append(f'<dt>Latest inspection</dt><dd class="nav-inspection" data-date="{insp["inspected_at"]}">{insp["inspected_at"]}: '
                   f'{", ".join(STATE_LABEL[s] for s in insp["states"])}. Retrieval and passage checks, not a check of any claim.</dd>')
    else:
        out.append('<dt>Latest inspection</dt><dd class="nav-inspection" data-date="">None recorded.</dd>')
    direct = imp.get("direct", {})
    pages = direct.get("reference_pages", [])
    used = [f'{len(direct.get("findings", []))} release findings']
    used.append("reference pages: " + (", ".join(f'<a href="{p}">{p}</a>' for p in pages) if pages else "none"))
    out.append(f'<dt>Used in</dt><dd class="nav-used">{"; ".join(used)}. Counts are review targets, not importance.</dd>')
    if mine:
        out.append('<dt>Register issues</dt><dd><ul class="nav-issues">' + "".join(
            f'<li data-value="{i["id"]}"><a href="#{i["id"]}">{e(i["title"])}</a> ({ISSUE_TAG[i["state"]][1].lower()})</li>'
            for i in mine) + "</ul></dd>")
    out.append("</dl>")
    out.append(f'<p class="nav-links"><a href="#source-{sid}">Inspection and impact record</a> · '
               f'Statements from this source are attributed to {e(r["publisher"].rstrip("."))}.</p>')
    out.append("</li>")
    return out


def render(registry, impact, issues) -> str:
    records = sorted(registry["source_records"], key=lambda r: r["id"])
    n = len(records)
    years = sorted({dated(r)[1][:4] for r in records if dated(r)[1]}, reverse=True)
    types = sorted({r["source_type"] for r in records}, key=lambda t: TYPE_LABEL[t])
    out = [START, '<section class="reference-sections" id="source-navigator" aria-labelledby="navigator-title">',
           '<article class="reference-block"><div class="block-index">08</div><div>',
           '<h2 id="navigator-title">Evidence navigator</h2>',
           f'<p class="detail">All {n} registered sources with their recorded identity, ontology layers, the statement types each may '
           'support, scope, limitations, latest inspection and the register issues that name them. With JavaScript you can filter '
           'by layer, source type, status, date and register issue, search the recorded text, and export the sources shown as JSON '
           'or CSV. Registry snapshot: version ' f'{e(registry["registry_version"])}, updated {e(registry["updated_at"])}. '
           'Machine-readable registry: <a href="/data/source-registry.json">source-registry.json</a>.</p>',
           f'<div class="framing-note"><strong>Boundary</strong><span class="nav-boundary">{e(BOUNDARY)}</span></div>',
           '<p class="intro nav-privacy">Filtering, search and export run in this page only: this website does not submit, save or '
           'add to the address anything you select or type, and reloading clears it. Other browser, extension or operating-system '
           'features follow your own settings.</p>',
           '<noscript><p class="detail">Without JavaScript the full inventory below is readable and printable; filtering and export '
           'need JavaScript. The registry is available as <a href="/data/source-registry.json">source-registry.json</a>.</p></noscript>',
           f'<div class="nav-controls" hidden data-registry-version="{e(registry["registry_version"])}" '
           f'data-registry-updated="{e(registry["updated_at"])}">',
           '<div class="nav-filter-groups">']
    out.append('<fieldset class="nav-group" data-group="layers"><legend>Ontology layers</legend>' + "".join(
        f'<label class="wb-option"><input type="checkbox" name="nav-layer" value="{x}"> {LAYER_NAME[x]} '
        f'<span class="muted">({sum(x in r["ontology_layers"] for r in records)})</span></label>' for x in LAYER_ORDER) +
        '<div class="nav-mode"><label class="wb-option"><input type="radio" name="nav-layer-mode" value="any" checked> Any selected layer</label>'
        '<label class="wb-option"><input type="radio" name="nav-layer-mode" value="all"> Every selected layer</label></div></fieldset>')
    out.append('<fieldset class="nav-group" data-group="types"><legend>Source type</legend>' + "".join(
        f'<label class="wb-option"><input type="checkbox" name="nav-type" value="{t}"> {TYPE_LABEL[t]} '
        f'<span class="muted">({sum(r["source_type"] == t for r in records)})</span></label>' for t in types) + "</fieldset>")
    statuses = [s for s in STATUS_LABEL if any(r["status"] == s for r in records)]
    out.append('<fieldset class="nav-group" data-group="other"><legend>Status, date and issues</legend>' + "".join(
        f'<label class="wb-option"><input type="checkbox" name="nav-status" value="{s}"> {STATUS_LABEL[s]} '
        f'<span class="muted">({sum(r["status"] == s for r in records)})</span></label>' for s in statuses) +
        '<label class="nav-field" for="nav-year">Publication or effective year</label><select id="nav-year" name="nav-year">'
        '<option value="">Any year</option>' + "".join(f'<option value="{y}">{y}</option>' for y in years) +
        '<option value="undated">Undated</option></select>'
        '<label class="wb-option"><input type="checkbox" name="nav-issues" value="1"> Named in a conflict-register issue</label></fieldset>')
    out.append('</div><label class="nav-field" for="nav-search">Search recorded text (title, publisher, ID, scope, limitations, statement types)</label>'
               '<input type="search" id="nav-search" name="nav-search" autocomplete="off" spellcheck="false" autocorrect="off" autocapitalize="off" maxlength="120">'
               '<div class="nav-toolbar" role="group" aria-label="Navigator actions"></div></div>')
    out.append(f'<p class="nav-count" role="status" aria-live="polite">Showing all {n} registered sources.</p>')
    out.append('<p class="nav-empty" hidden>No registered source matches these filters. Remove a filter or use Reset; an empty result '
               'means only that no registered source carries this metadata, not that no evidence exists.</p>')
    out.append(f'<ol class="nav-list" aria-label="Registered sources">')
    for r in records:
        out += source_item(r, impact, issues)
    out.append("</ol>")
    out.append('<h3>Scoped work beyond the public inventory</h3>'
               '<p class="detail nav-commercial">The navigator lists public sources and their recorded limits. It does not synthesise '
               'them or assess any organisation. An institution that needs that work can describe a scoped request on '
               '<a href="/strategic-availability/">Strategic Availability</a>: a Compute Sovereignty Brief, a Chip Dependency Audit, '
               'a Premium Reference Dossier, or a discussion of Ontology and Methodology Licensing. Each request is scoped case by case '
               'under the published independence rules; this page does not commit to availability or to any result.</p>')
    out.append("</div></article></section>")
    out.append(END)
    return "\n".join(out)


def apply(page_text: str, block: str) -> str:
    if START not in page_text or END not in page_text:
        raise SystemExit("source navigator markers not found in sources/index.html")
    return page_text[: page_text.index(START)] + block + page_text[page_text.index(END) + len(END):]


def in_sync() -> bool:
    current = PAGE.read_text(encoding="utf-8")
    return apply(current, render(*load())) == current


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--check", action="store_true", help="fail if the page does not match its inputs")
    args = parser.parse_args(argv)
    if args.check:
        if not in_sync():
            print("FAIL: sources/index.html navigator is out of date; run scripts/render_source_navigator.py", file=sys.stderr)
            raise SystemExit(1)
        print("PASS: source navigator matches the registry, impact index and conflict register.")
        return
    PAGE.write_text(apply(PAGE.read_text(encoding="utf-8"), render(*load())), encoding="utf-8")
    print("source navigator rendered")


if __name__ == "__main__":
    main()
