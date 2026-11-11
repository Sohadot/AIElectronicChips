#!/usr/bin/env python3
"""Validate the industrial research workbench (IDE-010): its evidence-request model, page and script.

data/industrial-evidence-requests.json lists the documents a researcher would need for three workflows.
These checks keep it a request-preparation tool rather than an assessment:

* exactly the three prescribed workflows, each linked to its IDE-007 pathway;
* every requirement traceable: registered active sources that its own findings or conflict records cite,
  existing findings, unresolved questions and register issues, and a public section that resolves;
* availability and basis consistent: nothing is 'published' without reviewed sources;
* no readiness, qualification, compliance, approval or score language, and no unverified edition used as evidence;
* the rack workflow covers every deployment stage, each kept separate;
* the page shows every requirement without JavaScript and matches the model;
* the script never transmits or stores what a user records, and never interpolates it as HTML.

Fails closed: a missing model, page or script is an error.
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from validate_dependency_atlas import LAYERS  # noqa: E402
from validate_evidence_maintenance import _content_checks, page_ids  # noqa: E402

MODEL = ROOT / "data" / "industrial-evidence-requests.json"
PAGE = ROOT / "research-workbench" / "index.html"
SCRIPT = ROOT / "assets" / "js" / "research-workbench.js"
EXPECTED = ["workflow-hbm4-integration", "workflow-bandwidth-comparison", "workflow-rack-deployment"]
TOP = {"model_id", "schema_version", "release", "status", "compiled_at", "scientific_review", "boundary", "evidence_categories",
       "basis_definitions", "availability_definitions", "deployment_stages", "session_statuses", "workflows"}
WF_FIELDS = {"id", "letter", "title", "research_question", "objective", "pathway_id", "requirements"}
REQ_FIELDS = {"id", "workflow_id", "objective", "title", "document_requested", "why_it_matters", "ontology_layer", "evidence_category",
              "basis", "public_availability", "technical_scope", "source_ids", "finding_ids", "unresolved_ids", "conflict_ids", "reference",
              "acceptance_considerations", "limitations", "permits_after_review", "not_established_without_review"}
STAGES = ["specified", "procured", "installed", "commissioned", "operationally_observed", "access"]
STATUSES = {"not_requested", "requested", "received", "needs_expert_review"}
ID = re.compile(r"^r[abc]-\d{2}-[a-z0-9-]+$")
# Readiness and verdict words a requirement may use only when negated.
VERDICT = re.compile(r"\b(?:is|are|was|were|be|been)\s+(?:ready|qualified|certified|compliant|verified|validated|approved|interoperable|authentic)\b"
                     r"|\breadiness (?:score|level|verdict)\b|\bfaster than\b|\bbest\b|\boutperforms?\b", re.I)
NEGATION = re.compile(r"\b(?:not|no|never|none|nor|without|cannot)\b|n't\b", re.I)
UNVERIFIED_EDITION = re.compile(r"MI350-007|PID#?2258402", re.I)
# Client-side privacy and safety: no network, no persistence, no URL state, no HTML interpolation, no dynamic code.
JS_FORBIDDEN = re.compile(
    r"\bfetch\s*\(|XMLHttpRequest|sendBeacon|WebSocket|EventSource|localStorage|sessionStorage|indexedDB|document\.cookie|"
    r"\.innerHTML|\.outerHTML|insertAdjacentHTML|document\.write|\beval\s*\(|new\s+Function|\bimport\s*\(|"
    r"history\.(?:push|replace)State|location\.(?:search|hash|href)\s*=|location\.assign|location\.replace|postMessage|serviceWorker|navigator\.share")


OVERCLAIM = re.compile(r"not sent anywhere|never leaves? (?:your|the) (?:browser|device)|completely private|kept only in this tab", re.I)
PRESERVED_FIGURES = ("896 GB/s", "22 TB/s", "19.2 TB/s", "3.6 TB/s", "3 TB/s")
STATUS_VERDICT = re.compile(r"\b(?:verified|approved|qualified|compliant|readiness|score|percent(?:age)?|progress bar)\b", re.I)


def nonempty(v) -> bool:
    return isinstance(v, str) and bool(v.strip())


def string_list(v) -> bool:
    return isinstance(v, list) and bool(v) and all(nonempty(x) for x in v)


def load_context():
    def j(p):
        return json.loads(p.read_text(encoding="utf-8"))
    registry = {s["id"]: s for s in j(ROOT / "data" / "source-registry.json")["source_records"]}
    releases = {}
    for p in sorted((ROOT / "data" / "research").glob("*.json")):
        r = j(p)
        releases[r["release_id"]] = r
    return registry, releases, j(ROOT / "data" / "evidence-conflicts.json"), j(ROOT / "data" / "reference-pathways.json"), \
        j(ROOT / "data" / "dependency-atlas.json")


def check_model(model, registry, releases, register, pathways, atlas) -> list[str]:
    errors: list[str] = []
    if not isinstance(model, dict) or set(model) != TOP:
        return ["evidence-requests: top-level fields mismatch"]
    if model["status"] != "research_tool" or model["scientific_review"] != "pending":
        errors.append("evidence-requests: status must be 'research_tool' and scientific_review 'pending'")
    if "not an assessment" not in model["boundary"] or "never validation" not in model["boundary"]:
        errors.append("evidence-requests: boundary must say this is not an assessment and that user statuses are never validation")
    if model["deployment_stages"] != STAGES or set(model["session_statuses"]) != STATUSES:
        errors.append("evidence-requests: deployment stages and session statuses must be the governed lists")
    if set(model["basis_definitions"]) != {"source_derived", "analytical_recommendation"} or \
            set(model["availability_definitions"]) != {"published", "partially_published", "not_published"}:
        errors.append("evidence-requests: basis and availability definitions must be the governed lists")
    categories = set(model["evidence_categories"])
    findings = {f["id"]: f for r in releases.values() for f in r["findings"]}
    unresolved = {u["id"] for r in releases.values() for u in r["unresolved"]}
    issues = {c["id"]: c for c in register["issues"]}
    pathway_ids = {p["id"] for p in pathways["pathways"]}
    leaked = {e["id"] for r in releases.values() for e in r["candidate_relationships"]}
    leaked |= {n["id"] for r in releases.values() for n in r["candidate_nodes"]}
    leaked -= {n["id"] for n in atlas["nodes"]}
    workflows = model["workflows"]
    if [w.get("id") for w in workflows if isinstance(w, dict)] != EXPECTED:
        errors.append(f"evidence-requests: workflows must be exactly {EXPECTED}, in order")
    seen: set[str] = set()
    for w in workflows:
        if not isinstance(w, dict) or set(w) != WF_FIELDS:
            errors.append("evidence-requests: workflow fields mismatch")
            continue
        ww = f"evidence-requests[{w['id']}]"
        if not w["research_question"].rstrip().endswith("?"):
            errors.append(f"{ww}: research_question must be a question")
        if w["pathway_id"] not in pathway_ids:
            errors.append(f"{ww}: pathway_id {w['pathway_id']} does not exist")
        reqs = w["requirements"]
        if not isinstance(reqs, list) or len(reqs) < 10:
            errors.append(f"{ww}: a workflow needs at least ten requirements")
            reqs = reqs if isinstance(reqs, list) else []
        stages = []
        for r in reqs:
            extra = {"deployment_stage"} if w["id"] == "workflow-rack-deployment" else set()
            if not isinstance(r, dict) or not REQ_FIELDS <= set(r) or set(r) - REQ_FIELDS - extra:
                errors.append(f"{ww}: requirement {r.get('id') if isinstance(r, dict) else r} fields mismatch")
                continue
            rw = f"{ww}.{r['id']}"
            if not ID.fullmatch(r["id"]) or r["id"] in seen or r["id"][1] != "abc"[EXPECTED.index(w["id"])]:
                errors.append(f"{rw}: invalid or duplicate id")
            seen.add(r["id"])
            if r["workflow_id"] != w["id"] or r["objective"] != w["objective"]:
                errors.append(f"{rw}: workflow_id and objective must match the workflow")
            for field in ("title", "document_requested", "why_it_matters", "technical_scope", "permits_after_review", "not_established_without_review"):
                if not nonempty(r[field]) or len(r[field]) < 12:
                    errors.append(f"{rw}.{field} must be a meaningful description")
            for field in ("acceptance_considerations", "limitations"):
                if not string_list(r[field]):
                    errors.append(f"{rw}.{field} must be a non-empty list")
            if r["ontology_layer"] not in LAYERS:
                errors.append(f"{rw}: ontology_layer must be a governed layer")
            if r["evidence_category"] not in categories:
                errors.append(f"{rw}: evidence_category must be one of {sorted(categories)}")
            if r["basis"] not in model["basis_definitions"] or r["public_availability"] not in model["availability_definitions"]:
                errors.append(f"{rw}: basis or public_availability invalid")
            # Traceability.
            for fid in r["finding_ids"]:
                if fid not in findings:
                    errors.append(f"{rw}: finding {fid} does not exist")
            for uid in r["unresolved_ids"]:
                if uid not in unresolved:
                    errors.append(f"{rw}: unresolved question {uid} does not exist")
            for cid in r["conflict_ids"]:
                if cid not in issues:
                    errors.append(f"{rw}: register issue {cid} does not exist")
            cited = {e["source_id"] for fid in r["finding_ids"] if fid in findings for e in findings[fid]["evidence"]}
            cited |= {s for cid in r["conflict_ids"] if cid in issues for s in issues[cid]["source_ids"]}
            for sid in r["source_ids"]:
                if sid not in registry:
                    errors.append(f"{rw}: source {sid} is not registered")
                elif registry[sid]["status"] != "active":
                    errors.append(f"{rw}: source {sid} is {registry[sid]['status']}, not active evidence")
                elif sid not in cited:
                    errors.append(f"{rw}: source {sid} is not cited by the requirement's findings or register issues")
            route, _, anchor = r["reference"].partition("#")
            if not anchor or anchor not in page_ids(route):
                errors.append(f"{rw}: reference {r['reference']} does not resolve")
            # Basis and availability: nothing published without reviewed sources.
            if r["basis"] == "source_derived" and not (r["finding_ids"] or r["source_ids"] or r["unresolved_ids"]):
                errors.append(f"{rw}: a source-derived requirement must cite findings, sources or unresolved questions")
            if r["basis"] == "analytical_recommendation" and (r["source_ids"] or r["finding_ids"]):
                errors.append(f"{rw}: an analytical recommendation cannot cite sources or findings as its support")
            if r["public_availability"] in ("published", "partially_published") and not r["source_ids"]:
                errors.append(f"{rw}: '{r['public_availability']}' needs the reviewed sources that publish it")
            if r["public_availability"] == "published" and r["basis"] != "source_derived":
                errors.append(f"{rw}: only a source-derived requirement can be 'published'")
            # Language.
            for field in ("title", "document_requested", "why_it_matters", "permits_after_review", "technical_scope"):
                if VERDICT.search(r[field]) and not NEGATION.search(r[field]):
                    errors.append(f"{rw}.{field}: readiness or verdict language '{VERDICT.search(r[field]).group(0)}'")
            for field, value in r.items():
                text = json.dumps(value)
                if UNVERIFIED_EDITION.search(text) and not (field == "limitations" and "pending" in text):
                    errors.append(f"{rw}.{field}: the unverified 2025 CDNA 4 edition may appear only as a pending limitation")
            if w["id"] == "workflow-rack-deployment":
                if r.get("deployment_stage") not in STAGES:
                    errors.append(f"{rw}: deployment_stage must be one of {STAGES}")
                stages.append(r.get("deployment_stage"))
        if w["id"] == "workflow-rack-deployment" and set(STAGES) - set(stages):
            errors.append(f"{ww}: deployment stages {sorted(set(STAGES) - set(stages))} have no requirement")
    # Workflow B keeps every published figure side by side: none is selected, dropped or averaged.
    bandwidth = json.dumps(next((w for w in workflows if isinstance(w, dict) and w.get("id") == EXPECTED[1]), {}))
    for figure in PRESERVED_FIGURES:
        if figure not in bandwidth:
            errors.append(f"evidence-requests[{EXPECTED[1]}]: published figure '{figure}' must stay in the workflow")
    errors += _content_checks(model, "evidence-requests", leaked, prose_skip=(".boundary", ".reference"))
    return errors


def check_script(text: str) -> list[str]:
    errors = []
    for m in STATUS_VERDICT.finditer(text):
        errors.append(f"research-workbench.js: status vocabulary '{m.group(0)}' implies review or a result; statuses record collection only")
    for m in JS_FORBIDDEN.finditer(text):
        errors.append(f"research-workbench.js: forbidden API '{m.group(0).strip()}' (no transmission, storage, URL state or HTML interpolation)")
    if re.search(r"spellcheck[\"']?\s*(?:,|=)\s*[\"']?true", text):
        errors.append("research-workbench.js: notes must not enable browser spell-check (it can send typed text elsewhere)")
    for needed in ('setAttribute("spellcheck", "false")', 'setAttribute("autocorrect", "off")'):
        if needed not in text:
            errors.append(f"research-workbench.js: note field must set {needed} so browser spelling services stay off")
    if OVERCLAIM.search(text):
        errors.append("research-workbench.js: privacy copy must say what this site does, not promise browser-wide privacy")
    for needed in ("not been independently validated", "csvCell", "textContent"):
        if needed not in text:
            errors.append(f"research-workbench.js: missing required safeguard '{needed}'")
    return errors


def check_page(page: str, model: dict) -> list[str]:
    errors = []
    scripts = re.findall(r"<script\b[^>]*>", page)
    if [s for s in scripts if "ld+json" not in s] != ['<script src="/assets/js/research-workbench.js" defer>']:
        errors.append("research-workbench/index.html: must load exactly the local workbench script, deferred")
    if 'href="/data/industrial-evidence-requests.json"' not in page:
        errors.append("research-workbench/index.html: must link the machine-readable model")
    if OVERCLAIM.search(page):
        errors.append("research-workbench/index.html: privacy copy must say what this site does, not promise browser-wide privacy")
    if "browser, extension or operating-system input features follow your own settings" not in page:
        errors.append("research-workbench/index.html: privacy note must say browser and system input features follow the user's settings")
    if "<noscript>" not in page:
        errors.append("research-workbench/index.html: must explain what works without JavaScript")
    for w in model["workflows"]:
        if f'id="{w["id"]}"' not in page:
            errors.append(f"research-workbench/index.html: workflow {w['id']} not rendered")
        for r in w["requirements"]:
            if f'id="{r["id"]}"' not in page or f'href="{r["reference"]}"' not in page:
                errors.append(f"research-workbench/index.html: requirement {r['id']} or its reference is not rendered statically")
    return errors


def check_all() -> list[str]:
    for path in (MODEL, PAGE, SCRIPT):
        if not path.is_file():
            return [f"required workbench file missing: {path.relative_to(ROOT)}"]
    model = json.loads(MODEL.read_text(encoding="utf-8"))
    errors = check_model(model, *load_context())
    errors += check_script(SCRIPT.read_text(encoding="utf-8"))
    errors += check_page(PAGE.read_text(encoding="utf-8"), model)
    if not errors:
        import render_research_workbench as render
        if not render.in_sync():
            errors.append("research-workbench/index.html is out of date; run scripts/render_research_workbench.py")
    return errors


def main() -> None:
    errors = check_all()
    if errors:
        for e in errors:
            print(f"FAIL: {e}", file=sys.stderr)
        raise SystemExit(1)
    model = json.loads(MODEL.read_text(encoding="utf-8"))
    n = sum(len(w["requirements"]) for w in model["workflows"])
    print(f"PASS: Research workbench valid (3 workflows, {n} traceable evidence requirements; local-only script, no transmission or storage).")


if __name__ == "__main__":
    main()
