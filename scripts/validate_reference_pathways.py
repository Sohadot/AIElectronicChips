#!/usr/bin/env python3
"""Validate the cross-layer reference-pathway model (data/reference-pathways.json, IDE-007).

A pathway is reference navigation: it links public reference sections, the release findings
they present and the registered sources behind those findings. It is not an Atlas relationship.
These checks keep that boundary and make every step traceable:

* each step names a public route and an anchor that exist, on the page that presents the
  release it draws on;
* every finding and unresolved question it names exists in that release set;
* every source it names is registered, not retired, cited by one of its findings and listed
  in that page's references, so a page is never cited for something its findings do not rest on;
* its evidence class matches the classes of the findings it rests on;
* no unpublished candidate relationship or candidate node appears anywhere in the model;
* no score, ranking, approval or readiness verdict appears, and the deployment inference
  boundaries apply to all text.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from validate_dependency_atlas import LAYERS  # noqa: E402
from validate_evidence_releases import (  # noqa: E402
    EVIDENCE_STATES_ORDERED,
    LEGACY_REFERENCE_PAGES,
    NEGATION,
    SITE_EVIDENCE_STATES,
    SITE_RECORD_CLAIM,
    inference_boundary_errors,
    sentences,
)

MODEL = ROOT / "data" / "reference-pathways.json"
REGISTRY = ROOT / "data" / "source-registry.json"
ATLAS = ROOT / "data" / "dependency-atlas.json"
RESEARCH_DIR = ROOT / "data" / "research"
SITEMAP = ROOT / "sitemap.xml"
EXPLORER_PAGE = ROOT / "sovereignty-stack" / "index.html"
DOMAIN = "https://aielectronicchips.com"

# IDE-007 prescribes exactly these three pathways, in this order.
EXPECTED_PATHWAYS = ["pathway-hbm-to-advanced-packaging", "pathway-memory-bandwidth-to-data-movement",
                     "pathway-rack-to-deployable-compute"]
MODEL_FIELDS = {"model_id", "schema_version", "release", "status", "compiled_at", "scientific_review", "boundary",
                "atlas_reference", "source_registry_reference", "workflow", "evidence_classes", "comparison_verdicts", "pathways"}
PATHWAY_FIELDS = {"id", "title", "research_question", "technical_purpose", "ontology_layers", "evidence_release_ids", "scope",
                  "assumptions", "limitations", "steps", "statements", "next_evidence"}
OPTIONAL_PATHWAY_FIELDS = {"comparisons", "evidence_ladder"}
# IDE-009: a step or comparison changed by a post-release reconciliation names it; its sources stay the original ones.
OPTIONAL_STEP_FIELDS = {"reconciliations"}
STEP_FIELDS = {"id", "title", "route", "anchor", "ontology_layer", "evidence_class", "relevance", "release_id", "finding_ids",
               "source_ids", "scope", "limitations", "unresolved_ids", "next_evidence"}
SCOPE_FIELDS = {"technical", "temporal", "geographic"}
STEP_CLASSES = {"verified_fact", "attributed_statement", "bounded_analysis", "unresolved"}
STATEMENT_CLASSES = STEP_CLASSES | {"not_supported"}
VERDICTS = {"valid", "conditional", "unsupported"}
WORKFLOW = ["research_question", "ontology_layers", "ordered_steps", "sources", "statements", "limitations", "unresolved", "next_evidence"]
ID_PATTERN = re.compile(r"^[a-z][a-z0-9]*(?:-[a-z0-9]+)*$")
FORBIDDEN_KEYS = re.compile(
    r"(?i)^(?:reviewer|reviewed_by|reviewed_at|approved\w*|approval\w*|sign_?off\w*|score\w*|rank\w*|grade|maturity\w*|"
    r"readiness\w*|certif\w*|relation_type|from|to|confidence)$")
# Outside the boundary statement, text may not score, rank, approve or grade anything.
VERDICT_LANGUAGE = re.compile(
    r"(?i)\b(?:score[sd]?|scoring|rank(?:ed|ing|s)?|maturity (?:level|grade)|readiness (?:score|verdict|level)|"
    r"approved (?:dependency|relationship|edge)|certified|\d+(?:\.\d+)?\s?%)")


def nonempty(value) -> bool:
    return isinstance(value, str) and bool(value.strip())


def string_list(value) -> bool:
    return isinstance(value, list) and bool(value) and all(nonempty(v) for v in value)


def page_for_route(route: str) -> Path | None:
    if not isinstance(route, str) or not route.startswith("/") or not route.endswith("/") or ".." in route:
        return None
    page = ROOT / route.strip("/") / "index.html" if route != "/" else ROOT / "index.html"
    return page if page.is_file() else None


def sitemap_routes() -> set[str]:
    return set(re.findall(r"<loc>https://aielectronicchips\.com(/[^<]*)</loc>", SITEMAP.read_text(encoding="utf-8")))


def page_ids(page: Path) -> set[str]:
    return set(re.findall(r'\bid="([^"]+)"', page.read_text(encoding="utf-8")))


def page_reference_sources(page: Path) -> set[str]:
    text = page.read_text(encoding="utf-8")
    return set(re.findall(r'<li id="ref-\d+">.*?<code>([a-z0-9-]+)</code>', text, re.S))


def release_page(release: dict) -> str | None:
    rel = release.get("reference_page", LEGACY_REFERENCE_PAGES.get(release.get("release_id")))
    return "/" + rel[: -len("index.html")] if isinstance(rel, str) else None


def _walk(obj, path=""):
    """Yield (key, path, value) for every dict entry, and (None, path, value) for strings."""
    if isinstance(obj, dict):
        for k, v in obj.items():
            yield k, f"{path}.{k}", v
            yield from _walk(v, f"{path}.{k}")
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            yield from _walk(v, f"{path}[{i}]")
    elif isinstance(obj, str):
        yield None, path, obj


def load_context():
    registry = json.loads(REGISTRY.read_text(encoding="utf-8"))
    atlas = json.loads(ATLAS.read_text(encoding="utf-8"))
    releases = {}
    for p in sorted(RESEARCH_DIR.glob("*.json")):
        r = json.loads(p.read_text(encoding="utf-8"))
        releases[r["release_id"]] = r
    return registry, atlas, releases


def check_model(model: object, registry: dict, atlas: dict, releases: dict[str, dict], today: date | None = None,
                routes: set[str] | None = None) -> list[str]:
    today = today or date.today()
    routes = sitemap_routes() if routes is None else routes
    errors: list[str] = []
    if not isinstance(model, dict):
        return ["model root must be an object"]
    if set(model) != MODEL_FIELDS:
        errors.append(f"model fields mismatch: missing={sorted(MODEL_FIELDS - set(model))}, extra={sorted(set(model) - MODEL_FIELDS)}")
    if model.get("status") != "reference_navigation":
        errors.append("status must be 'reference_navigation'; pathways are navigation, not Atlas relationships")
    if model.get("scientific_review") != "pending":
        errors.append("scientific_review must be 'pending'; no human review of the pathways is recorded")
    if model.get("atlas_reference") != "data/dependency-atlas.json" or model.get("source_registry_reference") != "data/source-registry.json":
        errors.append("atlas_reference and source_registry_reference must name the governed files")
    if model.get("workflow") != WORKFLOW:
        errors.append(f"workflow must list the question-to-evidence stages exactly: {WORKFLOW}")
    boundary = str(model.get("boundary", ""))
    if "not an Atlas relationship" not in boundary:
        errors.append("boundary must state that a pathway step is not an Atlas relationship")
    try:
        if date.fromisoformat(str(model.get("compiled_at"))) > today:
            errors.append("compiled_at is in the future")
    except ValueError:
        errors.append("compiled_at must be an ISO date")
    if not isinstance(model.get("evidence_classes"), dict) or set(model["evidence_classes"]) != STATEMENT_CLASSES:
        errors.append(f"evidence_classes must define exactly {sorted(STATEMENT_CLASSES)}")
    if not isinstance(model.get("comparison_verdicts"), dict) or set(model["comparison_verdicts"]) != VERDICTS:
        errors.append(f"comparison_verdicts must define exactly {sorted(VERDICTS)}")

    # --- forbidden content anywhere in the model -----------------------------------------------
    candidate_ids = {e.get("id") for r in releases.values() for e in r.get("candidate_relationships", [])}
    candidate_nodes = {n.get("id") for r in releases.values() for n in r.get("candidate_nodes", [])}
    atlas_nodes = {n.get("id") for n in atlas.get("nodes", [])}
    leaked = (candidate_ids | candidate_nodes) - atlas_nodes - {None}
    for key, where, value in _walk(model):
        if key is not None and FORBIDDEN_KEYS.match(str(key)):
            errors.append(f"model{where}: field '{key}' is not allowed; pathways carry no approvals, scores, rankings or edges")
        if key is None:
            for token in leaked:
                if token in value:
                    errors.append(f"model{where}: names unpublished research candidate '{token}'")
            # Identifiers are checked for traceability below; only prose is read for claims.
            if not where.endswith(".boundary") and not ID_PATTERN.fullmatch(value):
                m = VERDICT_LANGUAGE.search(value)
                if m:
                    errors.append(f"model{where}: verdict or score language '{m.group(0)}' is not allowed")
                for sent in sentences(value):
                    errors.extend(inference_boundary_errors(sent, f"model{where}"))

    # --- context ----------------------------------------------------------------------------------
    sources = {s.get("id"): s for s in registry.get("source_records", []) if isinstance(s, dict)}
    findings = {f["id"]: (rid, f) for rid, r in releases.items() for f in r.get("findings", [])}
    unresolved = {u["id"]: rid for rid, r in releases.items() for u in r.get("unresolved", [])}

    pathways = model.get("pathways")
    if not isinstance(pathways, list):
        return errors + ["pathways must be a list"]
    if [p.get("id") for p in pathways if isinstance(p, dict)] != EXPECTED_PATHWAYS:
        errors.append(f"pathways must be exactly the IDE-007 set, in order: {EXPECTED_PATHWAYS}")
    seen_steps: set[str] = set()
    for i, pw in enumerate(pathways):
        where = f"pathways[{i}]"
        if not isinstance(pw, dict):
            errors.append(f"{where} must be an object")
            continue
        extra, missing = set(pw) - PATHWAY_FIELDS - OPTIONAL_PATHWAY_FIELDS, PATHWAY_FIELDS - set(pw)
        if extra or missing:
            errors.append(f"{where} fields mismatch: missing={sorted(missing)}, extra={sorted(extra)}")
            continue
        where = pw["id"]
        for field in ("title", "research_question", "technical_purpose"):
            if not nonempty(pw[field]):
                errors.append(f"{where}.{field} must be non-empty")
        if not pw["research_question"].rstrip().endswith("?"):
            errors.append(f"{where}.research_question must be a question")
        for field in ("assumptions", "limitations", "next_evidence"):
            if not string_list(pw[field]):
                errors.append(f"{where}.{field} must be a non-empty list of strings")
        if not isinstance(pw["scope"], dict) or set(pw["scope"]) != SCOPE_FIELDS or not all(nonempty(v) for v in pw["scope"].values()):
            errors.append(f"{where}.scope must give technical, temporal and geographic scope")
        layers = pw["ontology_layers"]
        if not string_list(layers) or set(layers) - LAYERS or len(set(layers)) != len(layers):
            errors.append(f"{where}.ontology_layers must be distinct governed ontology layers")
            layers = []
        rels = pw["evidence_release_ids"]
        if not string_list(rels) or any(r not in releases for r in rels):
            errors.append(f"{where}.evidence_release_ids must name existing evidence releases")
            rels = []
        steps = pw["steps"]
        if not isinstance(steps, list) or len(steps) < 5:
            errors.append(f"{where}: a complete pathway needs at least five ordered steps")
            steps = steps if isinstance(steps, list) else []
        used_layers, used_releases = set(), set()
        for j, st in enumerate(steps):
            swhere = f"{where}.steps[{j}]"
            if not isinstance(st, dict) or not STEP_FIELDS <= set(st) or set(st) - STEP_FIELDS - OPTIONAL_STEP_FIELDS:
                errors.append(f"{swhere} must contain exactly {sorted(STEP_FIELDS)}")
                continue
            swhere = f"{where}.{st['id']}"
            if not ID_PATTERN.fullmatch(str(st["id"])) or st["id"] in seen_steps:
                errors.append(f"{swhere}: invalid or duplicate step id")
            seen_steps.add(st["id"])
            for field in ("title", "relevance"):
                if not nonempty(st[field]):
                    errors.append(f"{swhere}.{field} must say why the referenced material is relevant")
            if not string_list(st["limitations"]):
                errors.append(f"{swhere}.limitations must be a non-empty list")
            if not isinstance(st["scope"], dict) or set(st["scope"]) != SCOPE_FIELDS or not all(nonempty(v) for v in st["scope"].values()):
                errors.append(f"{swhere}.scope must give technical, temporal and geographic scope")
            if st["ontology_layer"] not in layers:
                errors.append(f"{swhere}.ontology_layer must be one of the pathway's layers")
            used_layers.add(st["ontology_layer"])
            # Route and anchor resolve, and the page is the one presenting the release.
            page = page_for_route(st["route"])
            if page is None or st["route"] not in routes:
                errors.append(f"{swhere}.route {st['route']!r} is not an existing public route in the sitemap")
                continue
            if st["anchor"] not in page_ids(page):
                errors.append(f"{swhere}.anchor #{st['anchor']} does not resolve on {st['route']}")
            rid = st["release_id"]
            if rid not in rels:
                errors.append(f"{swhere}.release_id must be one of the pathway's evidence releases")
                continue
            used_releases.add(rid)
            if release_page(releases[rid]) != st["route"]:
                errors.append(f"{swhere}: release {rid} is presented on {release_page(releases[rid])}, not {st['route']}")
            # Findings exist in that release and set the evidence class.
            fids = st["finding_ids"]
            if not string_list(fids):
                errors.append(f"{swhere}.finding_ids must name the findings the step rests on")
                fids = []
            classes, finding_sources = set(), set()
            for fid in fids:
                if fid not in findings or findings[fid][0] != rid:
                    errors.append(f"{swhere}: finding {fid} is not in release {rid}")
                    continue
                classes.add(findings[fid][1]["claim_class"])
                finding_sources |= {e["source_id"] for e in findings[fid][1]["evidence"]}
            if st["evidence_class"] not in STEP_CLASSES:
                errors.append(f"{swhere}.evidence_class must be one of {sorted(STEP_CLASSES)}")
            elif st["evidence_class"] != "unresolved" and classes and st["evidence_class"] not in classes:
                errors.append(f"{swhere}.evidence_class {st['evidence_class']} is not the class of any finding it rests on")
            elif st["evidence_class"] == "unresolved" and not st["unresolved_ids"]:
                errors.append(f"{swhere}: an unresolved step must link unresolved questions")
            # Sources: registered, not retired, behind the findings, and cited on the page.
            sids = st["source_ids"]
            if not string_list(sids):
                errors.append(f"{swhere}.source_ids must name registered sources")
                sids = []
            page_sources = page_reference_sources(page)
            for sid in sids:
                if sid not in sources:
                    errors.append(f"{swhere}: source {sid} is not registered")
                    continue
                if sources[sid].get("status") == "retired":
                    errors.append(f"{swhere}: source {sid} is retired")
                if sid not in finding_sources:
                    errors.append(f"{swhere}: source {sid} is not cited by any of the step's findings")
                if sid not in page_sources:
                    errors.append(f"{swhere}: source {sid} is not in the references of {st['route']}")
            if not isinstance(st["unresolved_ids"], list) or any(u not in unresolved for u in st["unresolved_ids"]):
                errors.append(f"{swhere}.unresolved_ids must name unresolved questions in an evidence release")
            if st["unresolved_ids"] and not nonempty(st["next_evidence"]):
                errors.append(f"{swhere}: a step with open questions must name the next evidence required")
        if set(layers) - used_layers:
            errors.append(f"{where}: layers {sorted(set(layers) - used_layers)} are declared but no step reaches them")
        if set(rels) - used_releases:
            errors.append(f"{where}: releases {sorted(set(rels) - used_releases)} are declared but no step draws on them")
        # Statements: classified and traceable.
        statements = pw["statements"]
        if not isinstance(statements, list) or not statements:
            errors.append(f"{where}.statements must be a non-empty list")
            statements = []
        present = set()
        for k, sm in enumerate(statements):
            mwhere = f"{where}.statements[{k}]"
            if not isinstance(sm, dict) or set(sm) != {"text", "classification", "basis"} or not nonempty(sm.get("text")):
                errors.append(f"{mwhere} must contain text, classification and basis")
                continue
            cls, basis = sm["classification"], sm["basis"]
            present.add(cls)
            if cls not in STATEMENT_CLASSES:
                errors.append(f"{mwhere}.classification must be one of {sorted(STATEMENT_CLASSES)}")
                continue
            if not string_list(basis) or any(b not in findings and b not in unresolved for b in basis):
                errors.append(f"{mwhere}.basis must name existing findings or unresolved questions")
                continue
            basis_classes = {findings[b][1]["claim_class"] for b in basis if b in findings}
            if cls in {"verified_fact", "attributed_statement", "bounded_analysis"} and cls not in basis_classes:
                errors.append(f"{mwhere}: classified {cls} but no basis finding has that class")
            if cls == "unresolved" and not any(b in unresolved for b in basis):
                errors.append(f"{mwhere}: an unresolved statement must rest on an unresolved question")
            if cls == "not_supported" and not NEGATION.search(sm["text"]):
                errors.append(f"{mwhere}: a not_supported statement must be worded as a negation")
        if not {"unresolved", "not_supported"} & present:
            errors.append(f"{where}: statements must record at least one unresolved or unsupported point")
        # Comparisons: each figure appears in the finding it cites.
        for k, cmp in enumerate(pw.get("comparisons", [])):
            cwhere = f"{where}.comparisons[{k}]"
            if not isinstance(cmp, dict) or not {"id", "verdict", "figures", "reason"} <= set(cmp) or set(cmp) - {"id", "verdict", "figures", "reason", "reconciliations"}:
                errors.append(f"{cwhere} must contain id, verdict, figures and reason")
                continue
            if cmp["verdict"] not in VERDICTS or not nonempty(cmp["reason"]):
                errors.append(f"{cwhere}: verdict must be one of {sorted(VERDICTS)} with a reason")
            figs = cmp["figures"]
            if not isinstance(figs, list) or len(figs) != 2:
                errors.append(f"{cwhere}: a comparison sets exactly two figures side by side")
                continue
            for fig in figs:
                fid = fig.get("finding_id") if isinstance(fig, dict) else None
                if fid not in findings:
                    errors.append(f"{cwhere}: figure must cite an existing finding")
                elif str(fig.get("value")) not in findings[fid][1]["statement"]:
                    errors.append(f"{cwhere}: figure {fig.get('value')!r} does not appear in finding {fid}")
        # Evidence ladder: the governed states; site states cannot be marked reviewed without a site record.
        ladder = pw.get("evidence_ladder")
        if ladder is not None:
            if not isinstance(ladder, list) or [r.get("state") for r in ladder if isinstance(r, dict)] != EVIDENCE_STATES_ORDERED:
                errors.append(f"{where}.evidence_ladder must list the governed evidence states in order")
            else:
                has_site_record = any(SITE_RECORD_CLAIM in s.get("supported_claim_types", []) for s in sources.values())
                for row in ladder:
                    if set(row) != {"state", "supported_statement", "record_required", "reviewed"} or not isinstance(row["reviewed"], bool):
                        errors.append(f"{where}.evidence_ladder: row {row.get('state')} fields mismatch")
                    elif row["state"] in SITE_EVIDENCE_STATES and row["reviewed"] and not has_site_record:
                        errors.append(f"{where}.evidence_ladder: {row['state']} cannot be marked reviewed without a registered site record")
    return errors


def check_explorer_page(model: dict, page: Path = EXPLORER_PAGE) -> list[str]:
    """The public explorer must present every pathway and step as static HTML."""
    errors = []
    text = page.read_text(encoding="utf-8")
    rel = page.relative_to(ROOT) if page.is_relative_to(ROOT) else page.name
    if 'href="/data/reference-pathways.json"' not in text:
        errors.append(f"{rel}: must link the machine-readable pathway model")
    for pw in model.get("pathways", []):
        if f'id="{pw["id"]}"' not in text:
            errors.append(f"{rel}: pathway {pw['id']} is not rendered")
        if pw["research_question"] not in text.replace("&amp;", "&"):
            errors.append(f"{rel}: research question of {pw['id']} is not rendered")
        for st in pw["steps"]:
            if f'href="{st["route"]}#{st["anchor"]}"' not in text:
                errors.append(f"{rel}: step {st['id']} does not link {st['route']}#{st['anchor']}")
    return errors


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("model", nargs="?", type=Path, default=MODEL)
    args = parser.parse_args(argv)
    try:
        model = json.loads(args.model.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        print(f"FAIL: reference pathways unreadable: {exc}", file=sys.stderr)
        raise SystemExit(1)
    registry, atlas, releases = load_context()
    errors = check_model(model, registry, atlas, releases)
    if not errors:
        errors = check_explorer_page(model)
    if not errors:
        import render_reference_pathways as render  # the page section is generated from the model
        current = EXPLORER_PAGE.read_text(encoding="utf-8")
        if render.apply(current, render.render(*render.load())) != current:
            errors.append("sovereignty-stack/index.html is out of date with the pathway model; run scripts/render_reference_pathways.py")
    if errors:
        for err in errors:
            print(f"FAIL: {err}", file=sys.stderr)
        raise SystemExit(1)
    steps = sum(len(p["steps"]) for p in model["pathways"])
    print(f"PASS: Reference pathways valid ({len(model['pathways'])} pathways, {steps} traceable steps; navigation only, no Atlas edges).")


if __name__ == "__main__":
    main()
