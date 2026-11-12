#!/usr/bin/env python3
"""Validate the IDE-009 reconciliation record against the register, the pathways and the public pages.

data/evidence-reconciliations-009.json records, for every register issue, whether new primary evidence was reviewed,
whether it changed the interpretation, and whether the public pages and the pathway model were brought into line.
These checks keep the layers in agreement:

* every register issue has exactly one reconciliation, and its 'still open' state matches the register;
* an applied correction's new public text is on the page and its old text is gone, including figure titles and labels;
* an applied pathway change is the model's current value, and the changed step or comparison names the reconciliation;
* new evidence comes from sources an inspection actually retrieved, no later than the reconciliation date;
* no record claims a human review, a score or an approval, and three semantic guards hold on the public text:
  the NVLink 6 3.6 / 3.0 TB/s difference is not called explained, two eCFR sections are not presented as a complete
  review of the rules, and AMD's 896 GB/s figure is not called scope-unknown once its direction is stated.
"""

from __future__ import annotations

import html
import json
import re
import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from validate_evidence_maintenance import _content_checks, iso, page_ids, source_date  # noqa: E402
from validate_evidence_releases import MAX_QUOTE_WORDS, NEGATION, QUOTED, sentences  # noqa: E402

RECORD = ROOT / "data" / "evidence-reconciliations-009.json"
# Later editorial corrections (IDE-013). Each names the value it replaces, so the IDE-009 record stays a historical record:
# a pathway value IDE-009 set may change only through a later entry that supersedes it and starts from exactly that value.
LATER_RECORDS = [ROOT / "data" / "evidence-reconciliations-013.json"]
LATER_TOP = {"record_id", "release", "schema_version", "status", "scientific_review", "as_of", "boundary", "reconciliations"}
LATER_FIELDS = {"id", "comparison_id", "previous_verdict", "corrected_verdict", "supersedes", "original_interpretation",
                "reconciled_interpretation", "why_previous_insufficient", "basis", "claim_classification", "scope",
                "uncertainty_remaining", "pathway_changes", "publication_changes", "dossier_divergence", "reconciled_at"}
TOP = {"record_id", "release", "schema_version", "status", "scientific_review", "as_of", "boundary", "state_definitions",
       "decision_definitions", "reconciliations"}
STATES = ["evidence_reviewed", "interpretation_changed", "public_reference_synchronized", "pathway_synchronized", "conflict_remains_open"]
DECISIONS = ["applied", "unnecessary", "deferred", "blocked"]
FIELDS = {"id", "conflict_id", "decision", "reason", "states", "original_interpretation", "original_locations", "new_evidence",
          "sources_examined_not_supporting", "pending_version_verification", "source_ids", "finding_ids", "unresolved_ids", "reconciled_interpretation",
          "claim_classification", "scope", "uncertainty_remaining", "affected_references", "affected_pathway_steps",
          "affected_comparisons", "publication_changes", "pathway_changes", "inspected_at", "validation_status"}
CLASSES = {"verified_fact", "attributed_statement", "bounded_analysis", "unresolved"}
# A document edition reported but not yet retrieved and checked here. It is never evidence until verified.
PENDING_FIELDS = {"document", "edition", "reported_by", "reported_content", "canonical_url_note", "retrieval_attempts", "status", "next_action"}
GUARDED_ROUTES = ["/interconnects/", "/hbm-memory/", "/ai-chip-infrastructure/", "/export-control-layer/", "/sovereignty-stack/", "/sources/"]
NVLINK_EXPLAINED = re.compile(r"\b(?:explains?|explained|reconciles|due to|because|accounted for)\b", re.I)
COMPLETE_REVIEW = re.compile(r"\b(?:complete|full|entire|all applicable|comprehensive(?:ly)?|fully)\b" r"(?:[^.]|\.(?=\d))*"
                             r"\b(?:rules?|regulations?|EAR|export[- ]controls?|current[- ]law|legal)\b", re.I)
# Once AMD's direction is stated, no page may call it unknown; and the old "scope not established/unconfirmed" wording
# (scope treated as wholly unknown) must not return. "Per-GPU scope not stated" stays allowed: AMD does not state it.
AMD_DIRECTION_UNKNOWN = re.compile(r"896(?:[^.]|\.(?=\d))*\bdirection\b(?:[^.]|\.(?=\d))*\b(?:unconfirmed|not stated|unknown|not established)\b"
                                   r"|\bdirection\b(?:[^.]|\.(?=\d))*\b(?:unconfirmed|not stated|unknown|not established)\b(?:[^.]|\.(?=\d))*896", re.I)
AMD_SCOPE_UNKNOWN = re.compile(r"896(?:[^.]|\.(?=\d))*\bscope\b(?:[^.]|\.(?=\d))*\b(?:unconfirmed|unknown|not established)\b"
                               r"|\bscope\b(?:[^.]|\.(?=\d))*\b(?:unconfirmed|unknown|not established)\b(?:[^.]|\.(?=\d))*896", re.I)
# The change log on /sources/ quotes superseded text on purpose.
CHANGE_LOG_ROUTES = {"/sources/"}


def plain(text: str) -> str:
    text = re.sub(r"(?is)<(script|style)\b.*?</\1>", " ", text)
    text = re.sub(r"</?(?:td|th|li|p|h[1-6]|tr|caption|figcaption|div|title|desc|text|dt|dd)\b[^>]*>", "\n", text, flags=re.I)
    return html.unescape(re.sub(r"[ \t]+", " ", re.sub(r"<[^>]+>", " ", text)))


def norm(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def route_file(route: str) -> Path:
    return ROOT / route.strip("/") / "index.html" if route.strip("/") else ROOT / "index.html"


def default_pages() -> dict[str, str]:
    out = {}
    for route in set(GUARDED_ROUTES):
        f = route_file(route)
        if f.is_file():
            out[route] = f.read_text(encoding="utf-8")
    return out


def model_strings(obj, path=""):
    if isinstance(obj, dict):
        for k, v in obj.items():
            yield from model_strings(v, f"{path}.{k}")
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            yield from model_strings(v, f"{path}[{i}]")
    elif isinstance(obj, str):
        yield path, obj


def semantic_guards(texts: dict[str, str], nvlink_open: bool, amd_applied: bool) -> list[str]:
    """texts: label -> plain text. Returns errors for the three guarded misstatements."""
    errors = []
    for label, text in texts.items():
        for sent in sentences(text):
            s = norm(sent)
            if s.endswith("?"):
                continue
            negated = bool(NEGATION.search(s))
            if nvlink_open and "3.6 TB/s" in s and re.search(r"\b3(?:\.0)? TB/s\b", s) and NVLINK_EXPLAINED.search(s) and not negated:
                errors.append(f"{label}: claims the NVLink 6 3.6 / 3.0 TB/s difference is explained without source support: {s[:140]!r}")
            if (re.search(r"\b(?:742\.6|740\.25|eCFR|Export Administration Regulations|rule text)\b", s) and COMPLETE_REVIEW.search(s)
                    and not negated):
                errors.append(f"{label}: presents a limited rule-text review as complete: {s[:140]!r}")
            if amd_applied and label not in CHANGE_LOG_ROUTES and (AMD_DIRECTION_UNKNOWN.search(s) or AMD_SCOPE_UNKNOWN.search(s)):
                errors.append(f"{label}: still treats the 896 GB/s scope or direction as unknown after reconciliation: {s[:140]!r}")
    return errors


def later_changes(later: list[dict]) -> dict[tuple[str, str, str], dict]:
    """(superseded reconciliation id, target, field) -> the later pathway change that replaces that value."""
    out = {}
    for rec in later:
        for rc in rec.get("reconciliations", []):
            for pc in rc.get("pathway_changes", []):
                for sid in rc.get("supersedes", []):
                    out[(sid, pc.get("target"), str(pc.get("field")))] = {**pc, "by": rc.get("id")}
    return out


def check(record: object, registry: dict, register: dict, pathways: dict, inspections: dict, releases: dict,
          pages: dict[str, str] | None = None, today: date | None = None, later: list[dict] | None = None) -> list[str]:
    today = today or date.today()
    pages = default_pages() if pages is None else pages
    later = load_later() if later is None else later
    superseded = later_changes(later)
    errors: list[str] = []
    if not isinstance(record, dict) or set(record) != TOP:
        return ["reconciliations: top-level fields mismatch"]
    if record["status"] != "maintenance_record" or record["scientific_review"] != "pending":
        errors.append("reconciliations: status must be 'maintenance_record' and scientific_review 'pending'")
    if list(record["state_definitions"]) != STATES or list(record["decision_definitions"]) != DECISIONS:
        errors.append("reconciliations: state and decision definitions must be the governed lists")
    if "not an Atlas" not in record["boundary"] or "not a scientific review" not in record["boundary"]:
        errors.append("reconciliations: boundary must say the record is not an Atlas and not a scientific review")
    as_of = iso(record["as_of"])
    if as_of is None or as_of > today:
        errors.append("reconciliations: as_of invalid or in the future")
    issues = {c["id"]: c for c in register["issues"]}
    findings = {f["id"] for r in releases.values() for f in r["findings"]}
    unresolved = {u["id"] for r in releases.values() for u in r["unresolved"]}
    steps = {s["id"]: s for p in pathways["pathways"] for s in p["steps"]}
    comps = {c["id"]: c for p in pathways["pathways"] for c in p.get("comparisons", [])}
    stmts = {f"{p['id']}.statements": p["statements"] for p in pathways["pathways"]}
    retrievals: dict[str, list[date]] = {}
    for r in inspections.get("records", []):
        if "source_retrieved" in r.get("states", []) and iso(r.get("inspected_at")):
            retrievals.setdefault(r["source_id"], []).append(iso(r["inspected_at"]))
    seen_ids, covered = set(), []
    rc_by_conflict = {}
    for i, rc in enumerate(record["reconciliations"]):
        if not isinstance(rc, dict) or set(rc) != FIELDS:
            errors.append(f"reconciliations[{i}] must contain exactly {sorted(FIELDS)}")
            continue
        w = f"reconciliations[{rc['id']}]"
        if rc["id"] in seen_ids or not re.fullmatch(r"rc-009-[a-z0-9-]+", str(rc["id"])):
            errors.append(f"{w}: invalid or duplicate id")
        seen_ids.add(rc["id"])
        cid = rc["conflict_id"]
        if cid not in issues:
            errors.append(f"{w}: conflict {cid} is not in the register")
            continue
        covered.append(cid)
        rc_by_conflict[cid] = rc
        st = rc["states"]
        if not isinstance(st, dict) or list(st) != STATES:
            errors.append(f"{w}: states must be exactly {STATES}")
            continue
        for k in ("evidence_reviewed", "interpretation_changed", "conflict_remains_open"):
            if not isinstance(st[k], bool):
                errors.append(f"{w}: {k} must be true or false")
        for k in ("public_reference_synchronized", "pathway_synchronized"):
            if st[k] not in (True, False, "not_required"):
                errors.append(f"{w}: {k} must be true, false or 'not_required'")
        dec = rc["decision"]
        if dec not in DECISIONS or not str(rc["reason"]).strip():
            errors.append(f"{w}: decision must be one of {DECISIONS}, with a reason")
        if rc["claim_classification"] not in CLASSES:
            errors.append(f"{w}: claim_classification must be one of {sorted(CLASSES)}")
        d = iso(rc["inspected_at"])
        if d is None or d > today:
            errors.append(f"{w}: inspected_at invalid or in the future")
        # Register agreement.
        reg_open = issues[cid]["state"] != "resolved_with_evidence"
        if st["conflict_remains_open"] is not reg_open:
            errors.append(f"{w}: conflict_remains_open disagrees with the register state '{issues[cid]['state']}'")
        if dec == "applied" and not any(h.get("date") == rc["inspected_at"] for h in issues[cid]["history"]):
            errors.append(f"{w}: the register history has no entry for this reconciliation's date")
        # References.
        for fid in rc["finding_ids"]:
            if fid not in findings:
                errors.append(f"{w}: finding {fid} does not exist")
        for uid in rc["unresolved_ids"]:
            if uid not in unresolved:
                errors.append(f"{w}: unresolved question {uid} does not exist")
        for ref in rc["affected_references"] + rc["original_locations"]:
            route, _, anchor = ref.partition("#")
            if not route_file(route).is_file() or (anchor and anchor not in page_ids(route)):
                errors.append(f"{w}: reference {ref} does not resolve")
        for sid in rc["affected_pathway_steps"]:
            if sid not in steps:
                errors.append(f"{w}: pathway step {sid} does not exist")
        for cmp in rc["affected_comparisons"]:
            if cmp not in comps:
                errors.append(f"{w}: comparison {cmp} does not exist")
        # Evidence.
        if set(rc["source_ids"]) != {e.get("source_id") for e in rc["new_evidence"]}:
            errors.append(f"{w}: source_ids must be exactly the sources of new_evidence")
        for j, ev in enumerate(rc["new_evidence"]):
            sid = ev.get("source_id")
            if sid not in registry:
                errors.append(f"{w}.new_evidence[{j}]: source {sid} is not registered")
                continue
            if not retrievals.get(sid) or (d and min(retrievals[sid]) > d):
                errors.append(f"{w}.new_evidence[{j}]: source {sid} was not retrieved by an inspection on or before {rc['inspected_at']}")
            if d and source_date(registry[sid]) and source_date(registry[sid]) > d:
                errors.append(f"{w}.new_evidence[{j}]: source postdates the reconciliation")
            if any(len(q.split()) > MAX_QUOTE_WORDS for q in QUOTED.findall(ev.get("locator", ""))):
                errors.append(f"{w}.new_evidence[{j}]: quoted excerpt exceeds {MAX_QUOTE_WORDS} words")
        for k, pv in enumerate(rc["pending_version_verification"] if isinstance(rc["pending_version_verification"], list) else [None]):
            pw = f"{w}.pending_version_verification[{k}]"
            if not isinstance(pv, dict) or set(pv) != PENDING_FIELDS:
                errors.append(f"{pw} must contain exactly {sorted(PENDING_FIELDS)}")
                continue
            if pv["status"] != "pending_version_verification":
                errors.append(f"{pw}: status must stay 'pending_version_verification' until an archived copy is retrieved and checked")
            if not isinstance(pv["retrieval_attempts"], list) or not pv["retrieval_attempts"] or not all(
                    isinstance(a, dict) and set(a) == {"url", "attempted_at", "outcome"} and iso(a.get("attempted_at")) for a in pv["retrieval_attempts"]):
                errors.append(f"{pw}: retrieval_attempts must record each attempt's url, date and outcome")
            if "source_id" in pv or any(pv["document"] in str(ev.get("locator", "")) for ev in rc["new_evidence"]):
                errors.append(f"{pw}: an unverified edition cannot be used as evidence")
        if st["evidence_reviewed"] != bool(rc["new_evidence"]):
            errors.append(f"{w}: evidence_reviewed must be true exactly when new evidence is listed")
        # Decisions and states.
        pubs, paths = rc["publication_changes"], rc["pathway_changes"]
        if dec == "applied":
            if not (pubs or paths):
                errors.append(f"{w}: an applied reconciliation must change the public pages or the pathway model")
            if not st["evidence_reviewed"]:
                errors.append(f"{w}: an applied reconciliation must rest on reviewed evidence")
        elif pubs or paths:
            errors.append(f"{w}: only an applied reconciliation may change public text")
        if (st["public_reference_synchronized"] is True) != bool(pubs) or (not pubs and st["public_reference_synchronized"] is False and dec == "applied"):
            errors.append(f"{w}: public_reference_synchronized must be true exactly when public text changed")
        if (st["pathway_synchronized"] is True) != bool(paths):
            errors.append(f"{w}: pathway_synchronized must be true exactly when the pathway model changed")
        if st["interpretation_changed"] and norm(rc["reconciled_interpretation"]) in ("", "Unchanged.", norm(rc["original_interpretation"])):
            errors.append(f"{w}: a changed interpretation must be stated")
        if st["conflict_remains_open"] and not rc["uncertainty_remaining"]:
            errors.append(f"{w}: an open issue must state the remaining uncertainty")
        # Public text agrees with the record: new text present, old text gone.
        for k, pc in enumerate(pubs):
            route = pc.get("route")
            if route not in pages:
                errors.append(f"{w}.publication_changes[{k}]: page {route} is not available")
                continue
            text = norm(plain(pages[route]))
            if not pc.get("new_text") or norm(pc["new_text"]) not in text:
                errors.append(f"{w}.publication_changes[{k}]: {route} does not carry the reconciled text {pc.get('new_text', '')[:70]!r}")
            if pc.get("old_text") and norm(pc["old_text"]) in text:
                errors.append(f"{w}.publication_changes[{k}]: {route} still carries the superseded text {pc['old_text'][:70]!r}")
        # Pathway model agrees with the record.
        for k, pc in enumerate(paths):
            target, field = pc.get("target"), str(pc.get("field"))
            m = re.fullmatch(r"(\w+)(?:\[(\d+)\])?", field)
            obj = steps.get(target) or comps.get(target)
            if target in stmts:
                current = next((s["text"] for s in stmts[target] if s["text"] == pc.get("new")), None)
                ok = current is not None and not any(s["text"] == pc.get("old") for s in stmts[target])
            elif obj is None or not m or m.group(1) not in obj:
                errors.append(f"{w}.pathway_changes[{k}]: target {target}.{field} does not exist")
                continue
            else:
                value = obj[m.group(1)]
                current = value[int(m.group(2))] if m.group(2) is not None and isinstance(value, list) and int(m.group(2)) < len(value) else value
                ok = current == pc.get("new")
                nxt = superseded.get((rc["id"], target, field))
                if nxt is not None:
                    # Chain of custody: the later correction must start from exactly the value this record set.
                    if nxt.get("old") != pc.get("new"):
                        errors.append(f"{w}.pathway_changes[{k}]: {nxt['by']} does not start from the value this reconciliation set")
                    ok = current == nxt.get("new")
                if rc["id"] not in obj.get("reconciliations", []):
                    errors.append(f"{w}.pathway_changes[{k}]: {target} does not name this reconciliation")
            if not ok:
                errors.append(f"{w}.pathway_changes[{k}]: the pathway model does not carry the reconciled value for {target}.{field}")
            if pc.get("old") == pc.get("new"):
                errors.append(f"{w}.pathway_changes[{k}]: old and new values are identical")
    for cid in sorted(set(issues) - set(covered)):
        errors.append(f"reconciliations: register issue {cid} has no reconciliation entry")
    for cid in sorted({c for c in covered if covered.count(c) > 1}):
        errors.append(f"reconciliations: register issue {cid} has more than one reconciliation")
    # Every reconciliation named by the pathway model exists.
    later_ids = {rc.get("id") for rec in later for rc in rec.get("reconciliations", [])}
    for obj in list(steps.values()) + list(comps.values()):
        for rid in obj.get("reconciliations", []):
            if rid not in seen_ids and rid not in later_ids:
                errors.append(f"pathways: {obj['id']} names unknown reconciliation {rid}")
    # Content and semantic guards.
    errors += _content_checks(record, "reconciliations", set(), prose_skip=(".boundary", ".old_text", ".old", ".original_interpretation", ".url"))
    nv = rc_by_conflict.get("ec-nvlink6-per-gpu")
    amd = rc_by_conflict.get("ec-mi300x-infinity-fabric-scope")
    texts = {route: plain(t) for route, t in pages.items()}
    texts["reference-pathways.json"] = "\n".join(v for _, v in model_strings(pathways))
    errors += semantic_guards(texts, nvlink_open=bool(nv and nv["states"]["conflict_remains_open"]),
                              amd_applied=bool(amd and amd["decision"] == "applied"))
    return errors


def load_later() -> list[dict]:
    return [json.loads(p.read_text(encoding="utf-8")) for p in LATER_RECORDS if p.is_file()]


def check_later(rec: object, base: dict, registry: dict, pathways: dict, releases: dict, pages: dict[str, str],
                dossier: dict | None, today: date | None = None) -> list[str]:
    """Validate a later correction record (IDE-013) against the IDE-009 record, the pathways, the pages and IDE-012."""
    today = today or date.today()
    if not isinstance(rec, dict) or set(rec) != LATER_TOP:
        return ["reconciliations-013: top-level fields mismatch"]
    errors: list[str] = []
    if rec["status"] != "maintenance_record" or rec["scientific_review"] != "pending":
        errors.append("reconciliations-013: status must be 'maintenance_record' and scientific_review 'pending'")
    if "not an Atlas" not in rec["boundary"] or "not a scientific review" not in rec["boundary"] or "kept unchanged" not in rec["boundary"]:
        errors.append("reconciliations-013: boundary must say it is not an Atlas or a scientific review and keeps earlier records unchanged")
    base_rcs = {r["id"]: r for r in base["reconciliations"]}
    comps = {c["id"]: (c, p) for p in pathways["pathways"] for c in p.get("comparisons", [])}
    findings = {f["id"] for r in releases.values() for f in r["findings"]}
    verdict_map = {"valid": {"comparable_on_documented_terms"}, "conditional": {"conditionally_comparable"},
                   "unsupported": {"not_comparable", "indeterminate"}}
    for rc in rec["reconciliations"]:
        if not isinstance(rc, dict) or set(rc) != LATER_FIELDS:
            errors.append(f"reconciliations-013: entry {rc.get('id') if isinstance(rc, dict) else rc} fields mismatch")
            continue
        w = f"reconciliations-013[{rc['id']}]"
        if not re.fullmatch(r"rc-013-[a-z0-9-]+", rc["id"]):
            errors.append(f"{w}: invalid id")
        d = iso(rc["reconciled_at"])
        if d is None or d > today or d < iso(base["as_of"]):
            errors.append(f"{w}: reconciled_at must be a valid date, no earlier than the IDE-009 record and not in the future")
        if rc["comparison_id"] not in comps:
            errors.append(f"{w}: comparison {rc['comparison_id']} does not exist")
            continue
        cmp_, _ = comps[rc["comparison_id"]]
        if cmp_["verdict"] != rc["corrected_verdict"] or rc["previous_verdict"] == rc["corrected_verdict"]:
            errors.append(f"{w}: the pathway must carry the corrected verdict, and it must differ from the previous one")
        if rc["id"] not in cmp_.get("reconciliations", []):
            errors.append(f"{w}: {rc['comparison_id']} does not name this reconciliation")
        for sid in rc["supersedes"]:
            if sid not in base_rcs:
                errors.append(f"{w}: superseded reconciliation {sid} does not exist")
            elif sid not in cmp_.get("reconciliations", []):
                errors.append(f"{w}: {rc['comparison_id']} must keep naming the superseded {sid} (history is kept)")
        fields_changed = set()
        for k, pc in enumerate(rc["pathway_changes"]):
            pw = f"{w}.pathway_changes[{k}]"
            if pc.get("target") != rc["comparison_id"] or pc.get("field") not in cmp_ or pc.get("old") == pc.get("new"):
                errors.append(f"{pw}: must change a field of {rc['comparison_id']} to a different value")
                continue
            fields_changed.add(pc["field"])
            if cmp_[pc["field"]] != pc["new"]:
                errors.append(f"{pw}: the pathway model does not carry the corrected value for {pc['field']}")
            earlier = [x for sid in rc["supersedes"] for x in base_rcs.get(sid, {}).get("pathway_changes", [])
                       if x.get("target") == pc["target"] and x.get("field") == pc["field"]]
            if earlier and earlier[-1]["new"] != pc["old"]:
                errors.append(f"{pw}: old value must be the one the superseded reconciliation set")
            if pc["field"] == "verdict" and (pc["old"], pc["new"]) != (rc["previous_verdict"], rc["corrected_verdict"]):
                errors.append(f"{pw}: verdict change must match previous_verdict and corrected_verdict")
        if not {"verdict", "reason"} <= fields_changed:
            errors.append(f"{w}: a verdict correction changes both the verdict and its reason")
        for k, pc in enumerate(rc["publication_changes"]):
            route = pc.get("route")
            text = norm(plain(pages.get(route, "")))
            if route not in pages or norm(pc.get("new_text", "")) not in text or norm(pc.get("old_text", "")) in text or not pc.get("old_text"):
                errors.append(f"{w}.publication_changes[{k}]: {route} must carry the new text and no longer carry the old text")
        ev = rc["basis"]
        for fid in ev.get("finding_ids", []):
            if fid not in findings:
                errors.append(f"{w}: finding {fid} does not exist")
        for sid in ev.get("source_ids", []):
            if registry.get(sid, {}).get("status") != "active":
                errors.append(f"{w}: source {sid} must be an active registered source")
        # The correction rests on, and agrees with, the IDE-012 classification.
        dc = next((c for c in (dossier or {}).get("comparisons", []) if c["id"] == ev.get("dossier_comparison_id")), None)
        if dc is None or (dossier or {}).get("dossier_id") != ev.get("dossier_id"):
            errors.append(f"{w}: the IDE-012 dossier comparison it rests on must exist")
        elif dc["classification"] not in verdict_map[rc["corrected_verdict"]] or dc.get("pathway_comparison_id") != rc["comparison_id"]:
            errors.append(f"{w}: the corrected verdict must agree with the IDE-012 classification of the same pathway comparison")
        elif not dc.get("pathway_divergence") or dc["pathway_divergence"].get("status") != rc["dossier_divergence"]["status_after"] \
                or dc["pathway_divergence"].get("reconciled_by") != rc["id"]:
            errors.append(f"{w}: the IDE-012 divergence must stay recorded and be marked reconciled by this entry")
        if not rc["uncertainty_remaining"] or not rc["why_previous_insufficient"].strip():
            errors.append(f"{w}: state why the earlier interpretation was insufficient and what remains uncertain")
    errors += _content_checks(rec, "reconciliations-013", set(), prose_skip=(".boundary", ".old_text", ".old", ".original_interpretation"))
    return errors


def load_all():
    def j(p):
        return json.loads(p.read_text(encoding="utf-8"))
    registry = {s["id"]: s for s in j(ROOT / "data" / "source-registry.json")["source_records"]}
    releases = {}
    for p in sorted((ROOT / "data" / "research").glob("*.json")):
        r = j(p)
        releases[r["release_id"]] = r
    return (j(RECORD), registry, j(ROOT / "data" / "evidence-conflicts.json"), j(ROOT / "data" / "reference-pathways.json"),
            j(ROOT / "data" / "source-inspections.json"), releases)


def main() -> None:
    # IDE-009 made the reconciliation record part of the evidence layer: its absence is a failure, never a pass.
    if not RECORD.is_file():
        print(f"FAIL: required reconciliation record missing: {RECORD.relative_to(ROOT)}", file=sys.stderr)
        raise SystemExit(1)
    errors = check(*load_all())
    for p in LATER_RECORDS:  # a correction the pathway model names is part of the evidence layer: missing means failure
        if not p.is_file():
            errors.append(f"required reconciliation record missing: {p.relative_to(ROOT)}")
    if not errors:
        record, registry, _, pathways, _, releases = load_all()
        dossier_path = ROOT / "data" / "research" / "institutional" / "accelerator-bandwidth-comparability-dossier-012.json"
        dossier = json.loads(dossier_path.read_text(encoding="utf-8")) if dossier_path.is_file() else None
        for later in load_later():
            errors += check_later(later, record, registry, pathways, releases, default_pages(), dossier)
    if errors:
        for e in errors:
            print(f"FAIL: {e}", file=sys.stderr)
        raise SystemExit(1)
    rec = json.loads(RECORD.read_text(encoding="utf-8"))["reconciliations"]
    applied = sum(r["decision"] == "applied" for r in rec)
    print(f"PASS: Evidence reconciliations valid ({len(rec)} issues covered, {applied} applied; public pages and pathways agree).")


if __name__ == "__main__":
    main()
