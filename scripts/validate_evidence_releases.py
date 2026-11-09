#!/usr/bin/env python3
"""Fail-closed validation for research-candidate evidence releases.

Each file in data/research/*.json is an evidence release: classified findings,
explicit unknowns, and proposed Atlas relationships that are NOT published.
This validator checks structure and registry cross-references only. It does
not read the cited documents and cannot confirm that a passage says what a
finding states; that remains a human review responsibility.

A candidate relationship is also run through the Atlas validator in a
simulated, reviewed state. That proves it would satisfy the publication
contract once a named human reviewer signs it off, without publishing it.
"""

from __future__ import annotations

import argparse
import copy
import html
import json
import re
import sys
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from validate_dependency_atlas import (  # noqa: E402
    ID_PATTERN,
    SELF_REPORTED_SOURCE_TYPES,
    nonempty,
    parse_date,
    string_list,
    validate as validate_atlas,
)

ROOT = Path(__file__).resolve().parents[1]
RESEARCH_DIR = ROOT / "data" / "research"
WORKFLOW = ROOT / ".github" / "workflows" / "validate-and-deploy.yml"
# Each release names the public page that presents it ("reference_page"). Release 001
# predates the field and keeps its original page. A release is checked only against
# its own page, so unrelated reference pages are never compared with each other.
LEGACY_REFERENCE_PAGES = {"aec-hbm4-evidence-release-001": "hbm-memory/index.html"}
REFERENCE_PAGES = [ROOT / "hbm-memory" / "index.html"]
# Quoted excerpts are for citation only: keep each short.
MAX_QUOTE_WORDS = 20
MAX_LOCATOR_QUOTED_WORDS = 40
QUOTED = re.compile(r'"([^"]+)"')
ATLAS = ROOT / "data" / "dependency-atlas.json"
REGISTRY = ROOT / "data" / "source-registry.json"

RELEASE_FIELDS = {
    "release_id", "version", "status", "publication_eligible", "as_of", "title",
    "source_registry_reference", "atlas_reference", "description", "rights_note",
    "findings", "unresolved", "candidate_nodes", "candidate_relationships",
}
OPTIONAL_RELEASE_FIELDS = {"reference_page"}
FINDING_FIELDS = {"id", "claim_class", "topic", "statement", "evidence", "evidence_state", "scope", "as_of", "limitations"}
EVIDENCE_STATES = {"cited_sources_active", "includes_pending_source"}
FINDING_CLASSES = {"verified_fact", "attributed_statement", "bounded_analysis"}
TOPICS = {
    "standard", "architecture", "interface_bandwidth", "stack_configuration",
    "base_die", "stacking_process", "packaging_integration", "thermal_power",
    "commercialization", "accelerator_integration", "substitution",
    # Advanced packaging and chiplet integration (IDE-003)
    "interposer_bridge", "chiplet_interface", "assembly_test", "production_chain", "interoperability",
    # Interconnect and data movement (IDE-004)
    "host_interface", "scale_up_fabric", "scale_out_network", "measurement_scope",
}
# Bandwidth and rate figures must carry their measurement scope. In these topics every
# figure in a finding's statement needs a matching entry in its "quantities" list.
QUANTIFIED_TOPICS = {"host_interface", "scale_up_fabric", "scale_out_network", "measurement_scope"}
QUANTITY_FIELDS = {"value", "unit", "quantity", "direction", "scope", "peak_or_sustained", "basis", "source_id"}
QUANTITY_UNITS = {"TB/s", "GB/s", "Tb/s", "Gb/s", "Gbps", "GT/s"}
QUANTITY_DIRECTIONS = {"bidirectional", "per_direction", "not_stated", "not_applicable"}
QUANTITY_SCOPES = {"per_lane", "per_link", "per_port", "per_device", "per_stack", "per_switch", "per_system", "per_package", "not_stated"}
QUANTITY_PEAK = {"peak", "sustained", "not_stated"}
# "specified": stated by a published standard; "vendor_stated": by a company or consortium announcement.
QUANTITY_BASES = {"vendor_stated", "specified", "calculated", "measured"}
# A measured figure needs a measurement record, not a vendor or consortium statement.
MEASUREMENT_SOURCE_TYPES = {"peer_reviewed_research", "official_dataset"}
FIGURE = re.compile(r"(\d[\d,]*(?:\.\d+)?)\s?(TB/s|GB/s|Tb/s|Gb/s|Gbps|GT/s)")
UNRESOLVED_FIELDS = {"id", "topic", "question", "why_unresolved", "sources_checked", "next_evidence_needed"}
CANDIDATE_EXTRA_FIELDS = {"review_status", "research_recommendation"}
# An AI-assisted source check may recommend a decision for the human reviewer.
# It is never a review: it cannot change review_status, reviewed_at or review_owner.
RECOMMENDATION_FIELDS = {"decision", "rationale", "changes_in_release", "evidence_gaps", "assessed_at", "assessment_method"}
RECOMMENDATION_DECISIONS = {"ACCEPT", "REVISE", "REJECT", "DEFER"}
RECOMMENDATION_METHOD = "ai_assisted_source_check"
# Priority and superiority language may only be reported as what a company said.
ATTRIBUTION_ONLY = re.compile(
    r"\b(?:world'?s first|world’s first|industry'?s first|industry-first|industry-leading|"
    r"market leader|leadership|best-in-class|dominant|market share)\b",
    re.IGNORECASE,
)


def reference_page(release: dict) -> Path | None:
    """The public page that presents this release, or None if it is missing or invalid."""
    rel = release.get("reference_page", LEGACY_REFERENCE_PAGES.get(release.get("release_id")))
    if not nonempty(rel) or rel.startswith(("/", "data/", "scripts/", "tests/", ".")) or ".." in rel or not rel.endswith("index.html"):
        return None
    page = ROOT / rel
    return page if page.is_file() else None


def check_quantities(finding: dict, where: str, cited_ids: set[str], sources: dict) -> list[str]:
    """Each bandwidth or rate figure states its unit, direction, scope, peak/sustained status and basis."""
    errors: list[str] = []
    quantities = finding.get("quantities")
    statement = str(finding.get("statement", ""))
    figures = {(v.replace(",", ""), u) for v, u in FIGURE.findall(statement)}
    if quantities is None:
        if finding.get("topic") in QUANTIFIED_TOPICS and figures:
            errors.append(f"{where} states bandwidth or rate figures without a quantities list")
        return errors
    if not isinstance(quantities, list) or not quantities:
        return [f"{where}.quantities must be a non-empty list"]
    described = set()
    for k, q in enumerate(quantities):
        qwhere = f"{where}.quantities[{k}]"
        if not isinstance(q, dict) or set(q) != QUANTITY_FIELDS:
            errors.append(f"{qwhere} must contain exactly {sorted(QUANTITY_FIELDS)}")
            continue
        value, unit = str(q["value"]).replace(",", ""), q["unit"]
        described.add((value, unit))
        if unit not in QUANTITY_UNITS:
            errors.append(f"{qwhere} unit must be one of {sorted(QUANTITY_UNITS)}")
        if q["direction"] not in QUANTITY_DIRECTIONS:
            errors.append(f"{qwhere} direction must be one of {sorted(QUANTITY_DIRECTIONS)}")
        if q["scope"] not in QUANTITY_SCOPES:
            errors.append(f"{qwhere} scope must be one of {sorted(QUANTITY_SCOPES)}")
        if q["peak_or_sustained"] not in QUANTITY_PEAK:
            errors.append(f"{qwhere} peak_or_sustained must be one of {sorted(QUANTITY_PEAK)}")
        if q["basis"] not in QUANTITY_BASES:
            errors.append(f"{qwhere} basis must be one of {sorted(QUANTITY_BASES)}")
        if not nonempty(q["quantity"]):
            errors.append(f"{qwhere} must name the quantity measured")
        if unit == "GT/s" and (q["scope"] != "per_lane" or q["direction"] != "not_applicable"):
            errors.append(f"{qwhere} GT/s is a per-lane transfer rate, not payload bandwidth: use scope per_lane and direction not_applicable")
        if q["source_id"] not in cited_ids:
            errors.append(f"{qwhere} source_id must be one of the finding's cited sources")
        if q["basis"] == "calculated" and finding.get("claim_class") != "bounded_analysis":
            errors.append(f"{qwhere} a calculated figure belongs in a bounded_analysis finding")
        if q["basis"] == "specified" and sources.get(q["source_id"], {}).get("source_type") != "technical_standard":
            errors.append(f"{qwhere} a specified figure must come from a technical_standard source")
        if q["basis"] == "measured" and sources.get(q["source_id"], {}).get("source_type") not in MEASUREMENT_SOURCE_TYPES:
            errors.append(f"{qwhere} a measured figure needs a measurement source, not a vendor or consortium statement")
        if (value, unit) not in figures:
            errors.append(f"{qwhere} {q['value']} {unit} does not appear in the finding statement")
    for value, unit in sorted(figures - described):
        errors.append(f"{where} figure {value} {unit} has no quantities entry")
    return errors


def check_release(release: object, registry: dict, atlas: dict, today: date, label: str) -> list[str]:
    errors: list[str] = []
    if not isinstance(release, dict):
        return [f"{label}: release root must be an object"]

    missing, extra = RELEASE_FIELDS - set(release), set(release) - RELEASE_FIELDS - OPTIONAL_RELEASE_FIELDS
    if missing:
        errors.append(f"{label}: missing fields {sorted(missing)}")
    if extra:
        errors.append(f"{label}: unknown fields {sorted(extra)}")
    if release.get("status") != "research_candidate":
        errors.append(f"{label}: status must be research_candidate; publication happens only via the Atlas")
    if release.get("publication_eligible") is not False:
        errors.append(f"{label}: publication_eligible must be false")
    if release.get("source_registry_reference") != "data/source-registry.json":
        errors.append(f"{label}: source registry reference mismatch")
    if release.get("atlas_reference") != "data/dependency-atlas.json":
        errors.append(f"{label}: atlas reference mismatch")
    for field in ("release_id", "version", "title", "description", "rights_note"):
        if not nonempty(release.get(field)):
            errors.append(f"{label}: {field} must be non-empty")
    if reference_page(release) is None:
        errors.append(f"{label}: reference_page must name an existing public index.html outside data/, scripts/ and tests/")
    release_date = parse_date(release.get("as_of"), f"{label}.as_of", errors)
    if release_date and release_date > today:
        errors.append(f"{label}: as_of is in the future")

    sources = {
        s["id"]: s for s in registry.get("source_records", [])
        if isinstance(s, dict) and nonempty(s.get("id"))
    }

    def source_date(sid: str) -> date | None:
        record = sources[sid]
        value = record.get("publication_date") or record.get("effective_date")
        try:
            return date.fromisoformat(value) if isinstance(value, str) else None
        except ValueError:
            return None

    # --- findings -----------------------------------------------------------
    findings = release.get("findings")
    if not isinstance(findings, list) or not findings:
        errors.append(f"{label}: findings must be a non-empty list")
        findings = []
    seen: set[str] = set()
    for i, finding in enumerate(findings):
        where = f"{label}.findings[{i}]"
        if not isinstance(finding, dict):
            errors.append(f"{where} must be an object")
            continue
        cls = finding.get("claim_class")
        allowed = FINDING_FIELDS | {"quantities"} | ({"assumptions"} if cls == "bounded_analysis" else set())
        if set(finding) - allowed or FINDING_FIELDS - set(finding):
            errors.append(f"{where} fields mismatch: missing={sorted(FINDING_FIELDS - set(finding))}, extra={sorted(set(finding) - allowed)}")
        fid = finding.get("id")
        if not nonempty(fid) or not ID_PATTERN.fullmatch(fid):
            errors.append(f"{where} invalid id")
        elif fid in seen:
            errors.append(f"{where} duplicate id: {fid}")
        else:
            seen.add(fid)
        if cls not in FINDING_CLASSES:
            errors.append(f"{where} invalid claim_class: {cls}")
        if finding.get("topic") not in TOPICS:
            errors.append(f"{where} invalid topic")
        for field in ("statement", "scope"):
            if not nonempty(finding.get(field)):
                errors.append(f"{where}.{field} must be non-empty")
        if not string_list(finding.get("limitations")):
            errors.append(f"{where}.limitations must be a non-empty list")
        if cls == "bounded_analysis" and not string_list(finding.get("assumptions")):
            errors.append(f"{where} bounded_analysis requires stated assumptions")
        if cls != "attributed_statement" and ATTRIBUTION_ONLY.search(str(finding.get("statement", ""))):
            errors.append(f"{where} priority or superiority language may appear only in attributed_statement findings")
        f_date = parse_date(finding.get("as_of"), f"{where}.as_of", errors)
        if f_date and release_date and f_date > release_date:
            errors.append(f"{where}.as_of exceeds release as_of")

        evidence = finding.get("evidence")
        if not isinstance(evidence, list) or not evidence:
            errors.append(f"{where}.evidence must cite at least one registered source")
            continue
        cited_types = []
        cited_ids: set[str] = set()
        any_pending = False
        for j, item in enumerate(evidence):
            ewhere = f"{where}.evidence[{j}]"
            if not isinstance(item, dict) or set(item) != {"source_id", "locator"}:
                errors.append(f"{ewhere} must contain exactly source_id and locator")
                continue
            sid = item.get("source_id")
            locator = item.get("locator")
            if not nonempty(locator):
                errors.append(f"{ewhere} requires a locator (quoted passage or section)")
            else:
                quoted = [len(q.split()) for q in QUOTED.findall(locator)]
                if any(n > MAX_QUOTE_WORDS for n in quoted):
                    errors.append(f"{ewhere} quoted excerpt exceeds {MAX_QUOTE_WORDS} words")
                if sum(quoted) > MAX_LOCATOR_QUOTED_WORDS:
                    errors.append(f"{ewhere} quotes more than {MAX_LOCATOR_QUOTED_WORDS} words in one citation")
            if sid in cited_ids:
                errors.append(f"{ewhere} duplicate source: {sid}")
            cited_ids.add(sid)
            if sid not in sources:
                errors.append(f"{ewhere} unregistered source: {sid}")
                continue
            if sources[sid].get("status") == "retired":
                errors.append(f"{ewhere} cites retired source: {sid}")
            cited_types.append(sources[sid].get("source_type"))
            any_pending = any_pending or sources[sid].get("status") == "pending_review"
            published = source_date(sid)
            if published and f_date and published > f_date:
                errors.append(f"{ewhere} source {sid} postdates the finding as_of")
        expected_state = "includes_pending_source" if any_pending else "cited_sources_active"
        if finding.get("evidence_state") not in EVIDENCE_STATES:
            errors.append(f"{where} invalid evidence_state")
        elif cited_types and finding.get("evidence_state") != expected_state:
            errors.append(f"{where} evidence_state must be {expected_state} given the cited sources' registry status")
        if cls == "verified_fact" and any_pending:
            errors.append(f"{where} verified_fact cannot cite a pending_review source")
        if cls == "verified_fact" and cited_types and all(t in SELF_REPORTED_SOURCE_TYPES for t in cited_types):
            errors.append(f"{where} verified_fact cannot rest solely on self-reported company sources")
        errors.extend(check_quantities(finding, where, cited_ids, sources))

    # --- unresolved ---------------------------------------------------------
    unresolved = release.get("unresolved")
    if not isinstance(unresolved, list):
        errors.append(f"{label}: unresolved must be a list")
        unresolved = []
    for i, item in enumerate(unresolved):
        where = f"{label}.unresolved[{i}]"
        if not isinstance(item, dict) or set(item) != UNRESOLVED_FIELDS:
            errors.append(f"{where} must contain exactly {sorted(UNRESOLVED_FIELDS)}")
            continue
        uid = item["id"]
        if not nonempty(uid) or not ID_PATTERN.fullmatch(uid):
            errors.append(f"{where} invalid id")
        elif uid in seen:
            errors.append(f"{where} duplicate id: {uid}")
        else:
            seen.add(uid)
        if item["topic"] not in TOPICS:
            errors.append(f"{where} invalid topic")
        for field in ("question", "why_unresolved", "next_evidence_needed"):
            if not nonempty(item[field]):
                errors.append(f"{where}.{field} must be non-empty")
        checked = item["sources_checked"]
        if not isinstance(checked, list) or any(s not in sources for s in checked):
            errors.append(f"{where}.sources_checked must list registered source IDs")

    # --- candidate graph ----------------------------------------------------
    nodes = release.get("candidate_nodes")
    edges = release.get("candidate_relationships")
    if not isinstance(nodes, list) or not isinstance(edges, list):
        errors.append(f"{label}: candidate_nodes and candidate_relationships must be lists")
        return errors
    atlas_node_ids = {n.get("id") for n in atlas.get("nodes", []) if isinstance(n, dict)}
    atlas_edge_ids = {e.get("id") for e in atlas.get("relationships", []) if isinstance(e, dict)}
    for node in nodes:
        if isinstance(node, dict) and node.get("id") in atlas_node_ids:
            errors.append(f"{label}: candidate node already in published Atlas: {node.get('id')}")

    simulated_edges = []
    for i, edge in enumerate(edges):
        where = f"{label}.candidate_relationships[{i}]"
        if not isinstance(edge, dict):
            errors.append(f"{where} must be an object")
            continue
        if edge.get("id") in atlas_edge_ids:
            errors.append(f"{where} already published in Atlas; remove it from the candidate release")
        if edge.get("review_status") != "awaiting_human_review":
            errors.append(f"{where} review_status must be awaiting_human_review")
        if edge.get("reviewed_at") is not None:
            errors.append(f"{where} reviewed_at must be null until a human review is recorded in the Atlas")
        if edge.get("review_owner") != "unassigned":
            errors.append(f"{where} review_owner must be 'unassigned' in a candidate release")
        rec = edge.get("research_recommendation")
        if rec is not None:
            rwhere = f"{where}.research_recommendation"
            if not isinstance(rec, dict) or set(rec) != RECOMMENDATION_FIELDS:
                errors.append(f"{rwhere} must contain exactly {sorted(RECOMMENDATION_FIELDS)}")
            else:
                if rec["decision"] not in RECOMMENDATION_DECISIONS:
                    errors.append(f"{rwhere}.decision must be one of {sorted(RECOMMENDATION_DECISIONS)}")
                if rec["assessment_method"] != RECOMMENDATION_METHOD:
                    errors.append(f"{rwhere}.assessment_method must be '{RECOMMENDATION_METHOD}'; a recommendation is not a human review")
                for field in ("rationale", "changes_in_release"):
                    if not nonempty(rec[field]):
                        errors.append(f"{rwhere}.{field} must be non-empty")
                if not isinstance(rec["evidence_gaps"], list) or not all(nonempty(g) for g in rec["evidence_gaps"]):
                    errors.append(f"{rwhere}.evidence_gaps must be a list of non-empty strings")
                rdate = parse_date(rec["assessed_at"], f"{rwhere}.assessed_at", errors)
                if rdate and rdate > today:
                    errors.append(f"{rwhere}.assessed_at is in the future")
                if rec["decision"] == "DEFER" and not rec["evidence_gaps"]:
                    errors.append(f"{rwhere}: DEFER must name the evidence gaps that block a decision")
        simulated = {k: v for k, v in edge.items() if k not in CANDIDATE_EXTRA_FIELDS}
        simulated["reviewed_at"] = release.get("as_of")
        simulated["review_owner"] = "simulated reviewer (structural precheck only)"
        simulated_edges.append(simulated)

    if simulated_edges:
        candidate_atlas = copy.deepcopy(atlas)
        candidate_atlas["status"] = "evidence_backed"
        candidate_atlas["as_of"] = release.get("as_of")
        candidate_atlas["nodes"] = list(candidate_atlas.get("nodes", [])) + copy.deepcopy(nodes)
        candidate_atlas["relationships"] = list(candidate_atlas.get("relationships", [])) + simulated_edges
        for err in validate_atlas(candidate_atlas, registry, today=today):
            errors.append(f"{label}: candidate fails Atlas publication contract: {err}")
    return errors


def check_public_references(page: Path, registry: dict) -> list[str]:
    """Each cited registry ID on a public page must exist and show its true review status."""
    try:
        html = page.read_text(encoding="utf-8")
    except OSError as exc:
        return [f"{page.name}: unreadable: {exc}"]
    status = {s.get("id"): s.get("status") for s in registry.get("source_records", []) if isinstance(s, dict)}
    rel = page.relative_to(ROOT)
    errors = []
    # Visible numbering of an <ol> follows position, so ids must run 1..n in order,
    # every [n] citation must resolve, and every reference must be cited.
    ids = [int(n) for n in re.findall(r'<li id="ref-(\d+)"', html)]
    if ids != list(range(1, len(ids) + 1)):
        errors.append(f"{rel}: reference list ids must run 1..n in order, found {ids}")
    cited = {int(n) for n in re.findall(r'href="#ref-(\d+)"', html)}
    for n in sorted(cited - set(ids)):
        errors.append(f"{rel}: citation [{n}] has no matching reference")
    for n in sorted(set(ids) - cited):
        errors.append(f"{rel}: reference [{n}] is never cited")
    for item in re.findall(r'<li id="ref-\d+">(.*?)</li>', html, re.DOTALL):
        for sid in re.findall(r"<code>([a-z0-9-]+)</code>", item):
            if sid not in status:
                errors.append(f"{rel}: cites unregistered source {sid}")
            elif (status[sid] == "pending_review") != ("pending_review" in item):
                errors.append(f"{rel}: reference to {sid} must show pending_review exactly when the registry does")
    return errors


# Three different events must not be conflated on a public page:
#   evidence compilation  -> "Evidence compiled: <release as_of>"
#   automated validation  -> CI only; never presented as review
#   human scientific review -> not yet recorded for any research_candidate release
REVIEW_PENDING_TEXT = "Scientific review pending"
REVIEW_COMPLETION_CLAIM = re.compile(
    r'"lastReviewed"|"reviewedBy"|\bReviewed:?\s+\d{4}-\d{2}-\d{2}|'
    r"\b(?:scientifically|peer|independently)[ -]reviewed\b|\breview(?:ed)? (?:completed|approved)\b|\bapproved by\b",
    re.IGNORECASE,
)


def check_review_representation(page: Path, compiled_dates: set[str]) -> list[str]:
    """A page backed by a research_candidate release may state when evidence was
    compiled, but must not claim a completed human scientific review."""
    try:
        html = page.read_text(encoding="utf-8")
    except OSError as exc:
        return [f"{page.name}: unreadable: {exc}"]
    rel = page.relative_to(ROOT) if page.is_relative_to(ROOT) else page.name
    errors = []
    match = REVIEW_COMPLETION_CLAIM.search(html)
    if match:
        errors.append(f"{rel}: claims a completed scientific review ({match.group(0)!r}) but no human review is recorded")
    if REVIEW_PENDING_TEXT not in html:
        errors.append(f"{rel}: must state '{REVIEW_PENDING_TEXT}' while its evidence release is a research candidate")
    stated = set(re.findall(r"Evidence compiled: (\d{4}-\d{2}-\d{2})", html))
    if not stated:
        errors.append(f"{rel}: must state 'Evidence compiled: YYYY-MM-DD'")
    elif not stated <= compiled_dates:
        errors.append(f"{rel}: evidence compilation date {sorted(stated)} does not match any release as_of {sorted(compiled_dates)}")
    return errors


# Inference boundaries: wording that turns supplier self-descriptions into
# platform facts, or company structure into capability claims.
NEGATION = re.compile(r"\b(?:not|no|none|nothing|never|neither|nor|unknown|unresolved|cannot|without)\b|n't\b", re.I)
MULTI_SOURCING = re.compile(r"multi-?sourc|interchangeab|dual[- ]sourc|second[- ]sourc|designed to accept", re.I)
QUALIFIED = re.compile(r"\b(?:qualified (?:by|for|on)|has qualified|have qualified|completed qualification)\b", re.I)
IN_HOUSE_OVERREACH = re.compile(r"in-house[^.]*\b(?:eliminat\w*|removes? the need|no longer (?:needs?|requires?|depends?)|independent of|no dependency|avoids? (?:the )?need)", re.I)
LOGIC_BASE_DIE = re.compile(r"base[- ]die[^.]*logic[- ]process|logic[- ]process[^.]*base[- ]die", re.I)
SUPPLIER_NAMED = re.compile(r"SK hynix|Samsung|Micron|TSMC|N12|N3|4nm", re.I)
# CoWoS is one packaging platform: no product-level or universal integration claim without evidence.
COWOS_PRODUCT_CLAIM = re.compile(r"CoWoS[^.]*\b(?:Rubin|Vera|Blackwell|MI\d{3}|GB\d{3}|every HBM4|all HBM4)|\b(?:Rubin|Vera|Blackwell|MI\d{3}|GB\d{3}|every HBM4|all HBM4)[^.]*CoWoS", re.I)
# Interoperability and compliance are test results; a standard's release or a product's
# announcement does not establish them, nor that a product implements a standard.
INTEROP_ASSERTION = re.compile(
    r"\b(?:(?:is|are|was|were|be|been)\s+(?:fully\s+)?interoperable|interoperates?\s+with|"
    r"demonstrated\s+interoperability\s+(?:between|with|across|among)|(?:is|are)\s+(?:fully\s+)?compliant\s+with|"
    r"passed\s+(?:the\s+)?compliance)", re.I)
STANDARD_IMPLEMENTATION = re.compile(r"\b(?:implements|supports|adopts)\s+(?:the\s+)?(?:UCIe|CXL|Ultra Ethernet|UEC)\b", re.I)
# "whether a product implements X" or "a claim that a product implements X" names no product.
GENERIC_SUBJECT = re.compile(r"(?:\b(?:a|any|a given|each|every)\s+(?:product|device|accelerator)\s*|\bwhether\b[^.]*)$", re.I)


# A product's support for a standard may be reported only as that vendor's statement.
ATTRIBUTED = re.compile(r"\b(?:states?|stated|lists?|listed|says?|said|describes?|described|according to|reports?|reported|claims?)\b", re.I)


def _names_a_product(sentence: str) -> bool:
    return any(not GENERIC_SUBJECT.search(sentence[:m.start()]) for m in STANDARD_IMPLEMENTATION.finditer(sentence))
COWOS_PRODUCT = re.compile(r"\b(?:Rubin|Vera|Blackwell|MI\d{3}[A-Z]?|GB\d{3})\b", re.I)
COWOS_UNIVERSAL = re.compile(r"\b(?:every|all) HBM4\b", re.I)
# Citation markers kept from a page so a sentence can be matched to the sources it cites.
CITE_TOKEN = re.compile(r"⟦(\d+)⟧")


def cowos_evidence(release: dict) -> dict[str, set[str]]:
    """Products that an attributed finding of this release ties to CoWoS, with the sources it cites.

    A product-level CoWoS statement is allowed elsewhere only for these products. An attributed
    finding is a company's own statement, recorded as such; whether its passage says what the
    finding states remains the human reviewer's check."""
    found: dict[str, set[str]] = {}
    for f in release.get("findings", []):
        if not isinstance(f, dict) or f.get("claim_class") != "attributed_statement":
            continue
        sources = {e.get("source_id") for e in f.get("evidence", []) if isinstance(e, dict)}
        for sent in sentences(str(f.get("statement", ""))):
            if COWOS_PRODUCT_CLAIM.search(sent) and not NEGATION.search(sent) and not COWOS_UNIVERSAL.search(sent):
                for product in COWOS_PRODUCT.findall(sent):
                    found.setdefault(product.upper(), set()).update(sources)
    return found


def _cowos_claim_supported(sentence: str, evidence: dict[str, set[str]] | None, cited: set[str] | None) -> bool:
    if not evidence or COWOS_UNIVERSAL.search(sentence):
        return False
    products = {p.upper() for p in COWOS_PRODUCT.findall(sentence)}
    if not products or not products <= set(evidence):
        return False
    # Where citations are known (a public page or a candidate edge), each product must be
    # cited to a source that its attributed finding rests on.
    return cited is None or all(evidence[p] & cited for p in products)


def inference_boundary_errors(sentence: str, where: str, evidence: dict[str, set[str]] | None = None,
                              cited: set[str] | None = None) -> list[str]:
    errors = []
    if sentence.rstrip().endswith("?"):
        return errors  # an open question asserts nothing
    negated = bool(NEGATION.search(sentence))
    if MULTI_SOURCING.search(sentence) and not negated:
        errors.append(f"{where}: asserts multi-sourcing or interchangeability without platform evidence: {sentence[:120]!r}")
    if QUALIFIED.search(sentence) and not negated:
        errors.append(f"{where}: asserts completed qualification without evidence: {sentence[:120]!r}")
    if IN_HOUSE_OVERREACH.search(sentence):
        errors.append(f"{where}: treats in-house manufacture as removing a manufacturing dependency: {sentence[:120]!r}")
    if COWOS_PRODUCT_CLAIM.search(sentence) and not negated and not _cowos_claim_supported(sentence, evidence, cited):
        errors.append(f"{where}: ties CoWoS to a product or to all HBM4 without a product-level disclosure: {sentence[:120]!r}")
    if INTEROP_ASSERTION.search(sentence) and not negated:
        errors.append(f"{where}: asserts interoperability or compliance without a published test result: {sentence[:120]!r}")
    if STANDARD_IMPLEMENTATION.search(sentence) and not negated and _names_a_product(sentence) and not ATTRIBUTED.search(sentence):
        errors.append(f"{where}: asserts, unattributed, that a product implements a standard: {sentence[:120]!r}")
    if LOGIC_BASE_DIE.search(sentence) and not SUPPLIER_NAMED.search(sentence) and not negated:
        errors.append(f"{where}: generalizes a logic-process base die beyond the suppliers that disclose it: {sentence[:120]!r}")
    return errors


def sentences(text: str) -> list[str]:
    """Split on sentence punctuation and on line breaks (block boundaries).

    Citation markers that open a fragment belong to the sentence before them,
    because pages place [n] after the full stop."""
    out: list[str] = []
    for block in re.split(r"\n+", text):
        for part in re.split(r"(?<=[.!?])\s+", re.sub(r"[ \t\r\f\v]+", " ", block)):
            part = part.strip()
            lead = re.match(r"^((?:⟦\d+⟧\s*)+)(.*)$", part)
            if lead and out:
                out[-1] = f"{out[-1]} {lead.group(1).strip()}"
                part = lead.group(2).strip()
            if part:
                out.append(part)
    return out


CELL = re.compile(r"(<t[hd]\b[^>]*>)(.*?)(</t[hd]>)", re.S)


def _negation_columns(match: re.Match) -> str:
    table = match.group(0)
    head = re.search(r"<thead>(.*?)</thead>", table, re.S)
    if not head:
        return table
    headers = [re.sub(r"<[^>]+>", "", c[1]).strip().lower() for c in CELL.findall(head.group(1))]
    columns = {i for i, h in enumerate(headers) if h.startswith("does not establish")}
    if not columns:
        return table

    def row(r: re.Match) -> str:
        n = [-1]

        def cell(c: re.Match) -> str:
            n[0] += 1
            return c.group(1) + ("Does not establish: " if n[0] in columns else "") + c.group(2) + c.group(3)
        return CELL.sub(cell, r.group(0))
    body = re.search(r"<tbody>.*?</tbody>", table, re.S)
    if not body:
        return table
    return table[:body.start()] + re.sub(r"<tr>.*?</tr>", row, body.group(0), flags=re.S) + table[body.end():]


def check_inference_boundaries(release: dict, page: Path) -> list[str]:
    errors = []
    evidence = cowos_evidence(release)
    for f in release.get("findings", []):
        for sent in sentences(str(f.get("statement", ""))):
            errors.extend(inference_boundary_errors(sent, f"finding {f.get('id')}", evidence))
    for e in release.get("candidate_relationships", []):
        cited = {c.get("source_id") for c in e.get("evidence", []) if isinstance(c, dict)}
        for sent in sentences(str(e.get("statement", ""))):
            errors.extend(inference_boundary_errors(sent, f"candidate {e.get('id')}", evidence, cited))
    for n in release.get("candidate_nodes", []):
        for sent in sentences(str(n.get("description", ""))):
            errors.extend(inference_boundary_errors(sent, f"node {n.get('id')}", evidence))
    try:
        html_text = page.read_text(encoding="utf-8")
    except OSError as exc:
        return errors + [f"{page.name}: unreadable: {exc}"]
    # Reference number -> registry IDs, so page sentences can be matched to their sources.
    ref_sources = {
        n: set(re.findall(r"<code>([a-z0-9-]+)</code>", body))
        for n, body in re.findall(r'<li id="ref-(\d+)">(.*?)</li>', html_text, re.S)
    }
    main = html_text.split("<main", 1)[-1]
    main = re.sub(r'<a class="cite" href="#ref-(\d+)">\[\d+\]</a>', r" ⟦\1⟧ ", main)
    # The table of contents only repeats section headings, which are checked in place.
    main = re.sub(r'<nav class="ref-toc".*?</nav>', " ", main, flags=re.S)
    # Cells under a "Does not establish" column are read with that header as their context.
    main = re.sub(r"<table\b.*?</table>", _negation_columns, main, flags=re.S)
    # Table cells, list items, paragraphs and headings are separate statements.
    main = re.sub(r"</?(?:td|th|li|p|h[1-6]|tr|caption|figcaption|div|ul|ol|table)\b[^>]*>", "\n", main, flags=re.I)
    text = html.unescape(re.sub(r"<[^>]+>", " ", main))
    rel = page.relative_to(ROOT) if page.is_relative_to(ROOT) else page.name
    for sent in sentences(text):
        cited = set().union(*(ref_sources.get(n, set()) for n in CITE_TOKEN.findall(sent)))
        plain = re.sub(r"\s*⟦\d+⟧", "", sent).strip()
        if plain:
            errors.extend(inference_boundary_errors(plain, str(rel), evidence, cited))
    return errors


def check_shared_candidate_nodes(releases: dict[str, dict]) -> list[str]:
    """A candidate node proposed by more than one release must be defined identically,
    so that two releases cannot propose diverging versions of one Atlas node."""
    seen: dict[str, tuple[str, dict]] = {}
    errors = []
    for label, release in releases.items():
        for node in release.get("candidate_nodes", []):
            if not isinstance(node, dict) or not nonempty(node.get("id")):
                continue
            first = seen.setdefault(node["id"], (label, node))
            if first[1] != node:
                errors.append(f"{label}: candidate node {node['id']} differs from its definition in {first[0]}")
    return errors


def check_pages_exclusion(workflow: Path, research_dir: Path) -> list[str]:
    """Unpublished research candidates must not ship in the Pages artifact."""
    if not any(research_dir.glob("*.json")):
        return []
    try:
        text = workflow.read_text(encoding="utf-8")
    except OSError:
        return ["Pages workflow not found; cannot confirm data/research is excluded from the site artifact"]
    if "--exclude='data/research'" not in text or "path: .\n" in text:
        return ["Pages workflow must stage the site with data/research/ excluded before upload"]
    return []


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("releases", nargs="*", type=Path, help="release files (default: data/research/*.json)")
    parser.add_argument("--atlas", type=Path, default=ATLAS)
    parser.add_argument("--registry", type=Path, default=REGISTRY)
    args = parser.parse_args(argv)
    paths = args.releases or sorted(RESEARCH_DIR.glob("*.json"))
    try:
        atlas = json.loads(args.atlas.read_text(encoding="utf-8"))
        registry = json.loads(args.registry.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        print(f"FAIL: atlas or registry unreadable: {exc}", file=sys.stderr)
        raise SystemExit(1)
    errors: list[str] = []
    summary = []
    # Each page is checked against the releases that name it, never against another page's release.
    compiled_dates: dict[Path, set[str]] = {page: set() for page in REFERENCE_PAGES}
    loaded: dict[str, dict] = {}
    for path in paths:
        try:
            release = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            errors.append(f"{path.name}: unreadable: {exc}")
            continue
        errors.extend(check_release(release, registry, atlas, date.today(), path.name))
        if not isinstance(release, dict):
            continue
        loaded[path.name] = release
        page = reference_page(release)
        if page is not None:
            errors.extend(check_inference_boundaries(release, page))
            dates = compiled_dates.setdefault(page, set())
            if release.get("status") == "research_candidate" and isinstance(release.get("as_of"), str):
                dates.add(release["as_of"])
        summary.append(
            f"{path.name}: {len(release.get('findings', []))} findings, "
            f"{len(release.get('unresolved', []))} unresolved, "
            f"{len(release.get('candidate_relationships', []))} unpublished candidates"
        )
    errors.extend(check_shared_candidate_nodes(loaded))
    for page, dates in compiled_dates.items():
        errors.extend(check_public_references(page, registry))
        if dates:
            errors.extend(check_review_representation(page, dates))
    errors.extend(check_pages_exclusion(WORKFLOW, RESEARCH_DIR))
    if errors:
        for err in errors:
            print(f"FAIL: {err}", file=sys.stderr)
        raise SystemExit(1)
    print("PASS: Evidence releases valid (" + ("; ".join(summary) or "none present") + ").")


if __name__ == "__main__":
    main()
