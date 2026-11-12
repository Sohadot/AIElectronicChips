#!/usr/bin/env python3
"""Validate the Workflow C documentary preflight (IDE-015) on the research workbench.

The preflight turns the IDE-014 record model into a document-review preparation aid. These checks keep it one:

* its definitions (data/deployment-evidence-preflight.json) name the IDE-014 model and Release 006 states it reuses,
  carry exactly the four user selections, one guidance entry per IDE-014 attribute, and the ten evidence-state
  boundaries, each resolving to an IDE-014 category error or record type;
* no selection, label or statement reads as a review, verification, approval, certification, pass, score or readiness
  result, unless the sentence negates it;
* the page renders, for every Workflow C requirement and in matrix order, exactly the IDE-014 record types, their
  required attributes and their ceilings, with access kept apart from deployment states, and all 18 record types
  reachable; the static preflight has no form controls (the script adds them) and is labelled as a research candidate
  pending scientific review;
* the script holds no evidence-state identifier or label, so it cannot compute or raise one: every ceiling it reports
  is read from the page, and its packet always reports that no evidence state is established;
* the Atlas has no relationships.

Fails closed: a missing definitions file, record model, page or script is an error.
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from validate_evidence_releases import EVIDENCE_STATES_ORDERED, REVIEW_COMPLETION_CLAIM  # noqa: E402

CONFIG = ROOT / "data" / "deployment-evidence-preflight.json"
MODEL = ROOT / "data" / "research" / "institutional" / "rack-deployment-verification-dossier-014.json"
PAGE = ROOT / "research-workbench" / "index.html"
SCRIPT = ROOT / "assets" / "js" / "research-workbench.js"
TOP = {"preflight_id", "schema_version", "release", "status", "scientific_review", "compiled_at", "workflow_id", "record_model",
       "evidence_states_release", "boundary", "packet", "document_statuses", "attribute_statuses", "status_definitions",
       "attribute_guidance", "boundaries"}
PACKET = {"format", "format_version", "label", "disclaimer", "research_status", "no_state_statement", "completeness_boundary",
          "dependency_rule", "access_rule"}
LABEL = "Documentary Preflight — Not an Evidence Verification or Readiness Assessment"
STATUSES = ["not_marked", "present", "missing", "unknown"]
BOUNDARIES = ["pb-specification-not-procurement", "pb-order-not-delivery", "pb-delivery-not-installation",
              "pb-installation-not-commissioning", "pb-procedure-not-execution", "pb-subsystem-not-integrated", "pb-test-not-acceptance",
              "pb-peak-not-operation", "pb-monitoring-description-not-operation", "pb-rule-not-determination"]
# Words that would turn a user's report into a result. Allowed only in a sentence that negates it.
RESULT_WORDS = re.compile(r"\b(?:approved?|certif\w*|deployment[- ]ready|passed|validated|verified|scor(?:e|es|ing)|percent\w*|"
                          r"grade[sd]?|rank(?:ing|ed)?|readiness|maturity|confidence (?:level|score)|risk (?:level|score|rating))\b", re.I)
NEGATION = re.compile(r"\b(?:not|no|never|none|nothing|without|cannot)\b|n't\b", re.I)
CONTROLS = re.compile(r"<(?:input|select|textarea|button)\b", re.I)


def j(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def strings(obj, path=""):
    if isinstance(obj, str):
        yield path, obj
    elif isinstance(obj, dict):
        for k, v in obj.items():
            yield from strings(v, f"{path}.{k}")
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            yield from strings(v, f"{path}[{i}]")


def result_language(text: str, where: str) -> list[str]:
    errors = []
    for sentence in re.split(r"(?<=[.;:])\s+|\s+—\s+", text):
        m = RESULT_WORDS.search(sentence)
        if m and not NEGATION.search(sentence):
            errors.append(f"{where}: '{m.group(0)}' reads as a review result for user-reported evidence")
    return errors


def check_config(cfg, model, releases: set[str]) -> list[str]:
    if not isinstance(cfg, dict) or set(cfg) != TOP:
        return ["preflight: top-level fields mismatch"]
    errors = []
    if (cfg["status"], cfg["scientific_review"], cfg["release"]) != ("research_tool", "pending", "IDE-015"):
        errors.append("preflight: status 'research_tool', scientific_review 'pending' and release 'IDE-015' are required")
    if cfg["workflow_id"] != "workflow-rack-deployment":
        errors.append("preflight: the preflight covers Workflow C only")
    rm = cfg["record_model"]
    if rm.get("dossier_id") != model["dossier_id"] or rm.get("compiled_at") != model["as_of"] or rm.get("status") != model["status"] \
            or not (ROOT / rm.get("file", "")).is_file() or (ROOT / rm["file"]).resolve() != MODEL.resolve() \
            or not (ROOT / rm.get("document", "")).is_file():
        errors.append("preflight.record_model must name the IDE-014 dossier, its file, document, date and status exactly")
    if model["status"] != "research_candidate" or model["scientific_review"] != "pending":
        errors.append("preflight: the IDE-014 model must still be an unreviewed research candidate for this labelling to hold")
    if cfg["evidence_states_release"] not in releases:
        errors.append("preflight: evidence_states_release must be an existing release")
    p = cfg["packet"]
    if not isinstance(p, dict) or set(p) != PACKET:
        errors.append("preflight.packet fields mismatch")
    else:
        if p["label"] != LABEL:
            errors.append(f"preflight.packet.label must be exactly '{LABEL}'")
        if not re.fullmatch(r"\d+\.\d+\.\d+", p["format_version"]) or p["format"] != "aec-deployment-evidence-preflight":
            errors.append("preflight.packet: format and semantic format_version required")
        for key, phrase in (("disclaimer", "has not seen"), ("disclaimer", "establishes no evidence state"),
                            ("research_status", "Scientific review pending"), ("no_state_statement", "No evidence state is established"),
                            ("completeness_boundary", "ready only for substantive examination by a qualified human reviewer"),
                            ("dependency_rule", "does not advance"), ("access_rule", "never advances a deployment state")):
            if phrase not in p[key]:
                errors.append(f"preflight.packet.{key} must say '{phrase}'")
    for key in ("document_statuses", "attribute_statuses", "status_definitions"):
        if list(cfg[key]) != STATUSES:
            errors.append(f"preflight.{key} must be exactly {STATUSES}, starting from not_marked")
    if "has not seen" not in cfg["status_definitions"].get("present", ""):
        errors.append("preflight.status_definitions.present must say this site has not seen the document")
    if list(cfg["attribute_guidance"]) != list(model["attributes"]):
        errors.append("preflight.attribute_guidance must cover exactly the IDE-014 attributes, in order")
    for a, g in cfg["attribute_guidance"].items():
        if not isinstance(g, dict) or set(g) != {"significance", "request"} or not all(isinstance(v, str) and len(v) > 20 for v in g.values()):
            errors.append(f"preflight.attribute_guidance.{a} needs a significance and a request")
    refs = {t["id"] for t in model["record_types"]} | {ce["id"] for c in model["chain"] for ce in c["category_errors"]}
    if [b.get("id") for b in cfg["boundaries"]] != BOUNDARIES:
        errors.append(f"preflight.boundaries must be exactly {BOUNDARIES}")
    for b in cfg["boundaries"]:
        if not b.get("refs") or any(r not in refs for r in b["refs"]) or not NEGATION.search(b.get("statement", "")):
            errors.append(f"preflight.boundaries[{b.get('id')}]: a negative statement with references resolving to IDE-014")
    for where, text in strings(cfg, "preflight"):
        if not re.fullmatch(r"[a-z0-9_./-]+", text):  # identifiers such as the Release 006 id are names, not statements
            errors += result_language(text, where)
    return errors


def section(page: str, sid: str) -> str:
    start = page.find(f'<section class="pf-req" id="{sid}"')
    return page[start:page.index("</section>", start)] if start >= 0 else ""


def check_page(page: str, cfg, model, workbench) -> list[str]:
    errors = []
    start = page.find('<section class="wb-preflight" id="workflow-rack-deployment-preflight"')
    if start < 0:
        return ["research-workbench: the Workflow C preflight is not rendered"]
    wf = page.find('id="workflow-rack-deployment"')
    nxt = page.find("</article>", wf)
    if not (wf < start < nxt):
        errors.append("research-workbench: the preflight must sit inside Workflow C")
    panel = page[start:nxt]
    if CONTROLS.search(panel):
        errors.append("research-workbench: the static preflight must not contain form controls; the local script adds them")
    for needed in (cfg["packet"]["label"], "Scientific review pending", f"Record model compiled: {model['as_of']}",
                   'href="/data/deployment-evidence-preflight.json"'):
        if needed not in panel:
            errors.append(f"research-workbench: preflight must show '{needed}'")
    m = REVIEW_COMPLETION_CLAIM.search(panel)
    if m:
        errors.append(f"research-workbench: preflight claims a completed review ({m.group(0)!r})")
    rc_ids = [r["id"] for w in workbench["workflows"] if w["id"] == cfg["workflow_id"] for r in w["requirements"]]
    rendered = re.findall(r'<section class="pf-req" id="pf-([a-z0-9-]+)"', panel)
    if rendered != [x["requirement_id"] for x in model["matrix"]] or sorted(rendered) != sorted(rc_ids):
        errors.append("research-workbench: the preflight must cover every Workflow C requirement exactly once, in matrix order")
    types = {t["id"]: t for t in model["record_types"]}
    seen_types = set(re.findall(r'data-record="(rt-[a-z0-9-]+)"', panel))
    if seen_types != set(types):
        errors.append(f"research-workbench: record types not reachable from the preflight: {sorted(set(types) - seen_types)}")
    for row in model["matrix"]:
        s = section(panel, f"pf-{row['requirement_id']}")
        w = f"research-workbench#pf-{row['requirement_id']}"
        if f'data-target-state="{row["target_state"]}"' not in s:
            errors.append(f"{w}: target state must be {row['target_state']}")
        records = re.findall(r'<div class="pf-record" data-record="([a-z0-9-]+)" data-ceiling="([a-z_]*)">(.*?)</ul></div>', s, re.S)
        if [r[0] for r in records] != row["record_type_ids"]:
            errors.append(f"{w}: record types must be exactly {row['record_type_ids']}")
            continue
        for rid, ceiling, body in records:
            t = types[rid]
            if ceiling != (t["state_ceiling"] or ""):
                errors.append(f"{w}.{rid}: ceiling must be {t['state_ceiling']}")
            if re.findall(r'<li class="pf-attr" data-attr="([a-z_]+)"', body) != t["required_attributes"]:
                errors.append(f"{w}.{rid}: attributes must be exactly {t['required_attributes']}")
            if t["dimension"] == "access" and ceiling:
                errors.append(f"{w}.{rid}: an access record supports no deployment state")
        if row["target_state"] == "access" and "never advances a deployment state" not in s:
            errors.append(f"{w}: the access requirement must say access never advances a deployment state")
        if "pf-prohibited" not in s or "pf-errors" not in s or cfg["packet"]["dependency_rule"] not in s.replace("&#x27;", "'"):
            errors.append(f"{w}: prohibited inference, category errors and the dependency rule must be shown")
    return errors


def check_script(text: str) -> list[str]:
    errors = []
    for s in (x for x in EVIDENCE_STATES_ORDERED if x != "not_established"):  # the eight states a record could support
        for form in (s, s.replace("_", " ")):
            if re.search(re.escape(form), text, re.I):
                errors.append(f"research-workbench.js: names the evidence state '{form}'; ceilings must be read from the page, never computed")
    for needed in ("initPreflight", "evidence_state_established: null", 'getAttribute("data-ceiling")', "textContent"):
        if needed not in text:
            errors.append(f"research-workbench.js: preflight safeguard '{needed}' missing")
    return errors


def check_all() -> list[str]:
    for path in (CONFIG, MODEL, PAGE, SCRIPT):
        if not path.is_file():
            return [f"required preflight file missing: {path.relative_to(ROOT)}"]
    cfg, model = j(CONFIG), j(MODEL)
    releases = {j(p)["release_id"] for p in sorted((ROOT / "data" / "research").glob("*.json"))}
    workbench = j(ROOT / "data" / "industrial-evidence-requests.json")
    errors = check_config(cfg, model, releases)
    if errors:
        return errors
    errors += check_page(PAGE.read_text(encoding="utf-8"), cfg, model, workbench)
    errors += check_script(SCRIPT.read_text(encoding="utf-8"))
    if j(ROOT / "data" / "dependency-atlas.json").get("relationships"):
        errors.append("preflight: the Atlas has relationships; nothing here may be read as promoting one")
    return errors


def main() -> None:
    errors = check_all()
    if errors:
        for e in errors:
            print(f"FAIL: {e}", file=sys.stderr)
        raise SystemExit(1)
    model = j(MODEL)
    print(f"PASS: Deployment evidence preflight valid ({len(model['matrix'])} Workflow C requirements, {len(model['record_types'])} record types "
          f"reachable, {len(model['attributes'])} attributes; no evidence state computed, no review recorded).")


if __name__ == "__main__":
    main()
