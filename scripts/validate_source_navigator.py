#!/usr/bin/env python3
"""Validate the Institutional Evidence Navigator on /sources/ (IDE-017).

The navigator must stay a faithful, non-certifying view of the source registry:

* the page section matches its generator, and lists every registry record exactly once, with its status, type, layers,
  statement types, scope, limitations and canonical URL as recorded;
* the boundary that registration is not verification, the dates-are-not-currency rule and publisher attribution are shown;
* no score, rating, ranking or confidence value is introduced by the navigator's own wording;
* the page loads only the local deferred navigator script, which never transmits, stores, writes to the URL, evaluates
  code or interpolates HTML, and which neutralises spreadsheet formulas in CSV export;
* the restrained commercial pointer names only the published offerings and carries no price or promise.

Fails closed: a missing page, script or input is an error.
"""

from __future__ import annotations

import html
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import render_source_navigator as render  # noqa: E402
from validate_evidence_requests import JS_FORBIDDEN, OVERCLAIM  # noqa: E402

SCRIPT = ROOT / "assets" / "js" / "source-navigator.js"
SCRIPT_TAG = '<script src="/assets/js/source-navigator.js" defer></script>'
# Wording the navigator itself may never use about a source (registry text quoted verbatim is checked by its own validator).
INVENTED = re.compile(r"\b(?:score[ds]?|scoring|rated|rating|ranked|top-ranked|trust(?:ed|worthy)? level|confidence (?:level|score|rating)|"
                      r"verified source|approved source|certified|recommended source)\b", re.I)
OFFERINGS = ("Compute Sovereignty Brief", "Chip Dependency Audit", "Premium Reference Dossier", "Ontology and Methodology Licensing")


def block(page: str) -> str:
    if render.START not in page or render.END not in page:
        return ""
    return page[page.index(render.START): page.index(render.END)]


def own_text(section: str) -> str:
    """The navigator's own wording: the section with every per-source record removed."""
    without = re.sub(r'<li class="nav-source".*?\n</li>', "", section, flags=re.S)
    return html.unescape(re.sub(r"<[^>]+>", " ", without))


def check_page(page: str, registry: dict) -> list[str]:
    errors = []
    section = block(page)
    if not section:
        return ["sources/index.html: navigator markers missing"]
    scripts = [s for s in re.findall(r"<script\b[^>]*>", page) if "ld+json" not in s]
    if scripts != [SCRIPT_TAG.replace("</script>", "")]:
        errors.append("sources/index.html: must load exactly the local deferred navigator script")
    records = registry["source_records"]
    ids = re.findall(r'<li class="nav-source" id="nav-([a-z0-9-]+)"', section)
    if sorted(ids) != sorted(r["id"] for r in records) or len(ids) != len(set(ids)):
        errors.append("navigator: must list every registry record exactly once")
    for r in records:
        m = re.search(rf'<li class="nav-source" id="nav-{re.escape(r["id"])}".*?\n</li>', section, re.S)
        if not m:
            continue
        item = m.group(0)
        w = f"navigator[{r['id']}]"
        if f'data-status="{r["status"]}"' not in item or f'data-type="{r["source_type"]}"' not in item:
            errors.append(f"{w}: status or source type differs from the registry")
        if f'href="{html.escape(r["canonical_url"])}"' not in item:
            errors.append(f"{w}: canonical URL differs from the registry")
        if re.findall(r'<ul class="nav-layers">(.*?)</ul>', item) != ["".join(
                f'<li data-value="{x}">{render.LAYER_NAME[x]}</li>' for x in r["ontology_layers"])]:
            errors.append(f"{w}: ontology layers differ from the registry")
        for field in ("title", "publisher", "geographic_scope", "temporal_scope", "confidence_use", *r["use_limitations"],
                      *r["supported_claim_types"]):
            value = r.get(field, field)
            if html.escape(value) not in item and html.escape(render.words(value)) not in item:
                errors.append(f"{w}: recorded text missing: {value[:50]!r}")
        if r["status"] != "active" and "nav-pending" not in item:
            errors.append(f"{w}: a non-active source must be marked visibly")
    text = re.sub(r"\s+", " ", own_text(section))
    for phrase in ("registration does not verify any claim", "not that its contents are still current", "attributed to the publisher",
                   "conflicting evidence stays recorded", "an empty result means only that no registered source carries this metadata"):
        if phrase not in text:
            errors.append(f"navigator: boundary wording missing: {phrase!r}")
    m = INVENTED.search(text)
    if m:
        errors.append(f"navigator: introduces evaluative wording {m.group(0)!r}; it must not score, rate or rank sources")
    if OVERCLAIM.search(text):
        errors.append("navigator: privacy copy must say what this site does, not promise browser-wide privacy")
    if 'href="/strategic-availability/"' not in section or not all(o in text for o in OFFERINGS):
        errors.append("navigator: the commercial pointer must link /strategic-availability/ and name the published offerings")
    if re.search(r"(?i)[$€£]\s?\d|\bper (?:month|year|seat)\b|\bsubscri|\bcheckout\b|\bbuy now\b", text):
        errors.append("navigator: no prices, subscriptions or checkout")
    if 'spellcheck="false"' not in section or 'autocorrect="off"' not in section:
        errors.append("navigator: the search field must turn off browser spelling services")
    return errors


def check_script(js: str) -> list[str]:
    errors = [f"source-navigator.js: forbidden API '{m.group(0).strip()}'" for m in JS_FORBIDDEN.finditer(js)]
    for needed in ("csvCell", "textContent", "/^[=+\\-@\\t\\r]/"):
        if needed not in js:
            errors.append(f"source-navigator.js: missing safeguard {needed!r}")
    if INVENTED.search(js):
        errors.append(f"source-navigator.js: evaluative wording {INVENTED.search(js).group(0)!r}")
    return errors


def check_all() -> list[str]:
    for path in (render.PAGE, SCRIPT, render.REGISTRY, render.IMPACT, render.CONFLICTS):
        if not path.is_file():
            return [f"required navigator file missing: {path.relative_to(ROOT)}"]
    registry = json.loads(render.REGISTRY.read_text(encoding="utf-8"))
    errors = check_page(render.PAGE.read_text(encoding="utf-8"), registry) + check_script(SCRIPT.read_text(encoding="utf-8"))
    if not errors and not render.in_sync():
        errors.append("sources/index.html navigator is out of date; run scripts/render_source_navigator.py")
    return errors


def main() -> None:
    errors = check_all()
    if errors:
        for err in errors:
            print(f"FAIL: {err}", file=sys.stderr)
        raise SystemExit(1)
    n = len(json.loads(render.REGISTRY.read_text(encoding="utf-8"))["source_records"])
    print(f"PASS: Evidence navigator valid ({n} registered sources listed as recorded; no score or verification implied; local-only script).")


if __name__ == "__main__":
    main()
