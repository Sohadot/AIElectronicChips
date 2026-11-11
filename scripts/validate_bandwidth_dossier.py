#!/usr/bin/env python3
"""Validate the accelerator bandwidth comparability dossier (IDE-012).

The dossier classifies published bandwidth figures and the comparisons drawn between them. This
validator checks each judgment against the corpus and against fixed rules:

- every figure resolves to the record that already holds it (a release quantity, a conflict-register
  locator, a finding locator or a bounded-analysis statement), with the same source and value;
- units belong to a known dimension, and every normalization is recomputed, must satisfy its rule's
  preconditions, and must not hit a rejection condition; rejected normalizations really do break them;
- comparability classes follow the descriptors: 'comparable' needs matching level, scope, direction
  and peak status; 'conditional' needs stated conditions, including one naming any unstated
  direction; 'not comparable' needs a real difference; any figure with an unresolved scope or an
  unstated direction forces 'indeterminate' or 'not comparable' unless a condition names it;
- every reference pathway B comparison is classified consistently with its verdict;
- the three cases keep the IDE-009 reconciliations (MI300X direction stated, scope open; no figure
  selected) and do not use the unverified 2025 CDNA 4 edition;
- all thirteen workflow B requirements are mapped; review questions cite active sources;
- nothing is promoted and no review, approval, score or ranking is recorded;
- the rendered dossier and review brief match their inputs.

Structure and lineage only: it cannot confirm that a source says what a figure records.
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(Path(__file__).resolve().parent))
from validate_evidence_maintenance import _content_checks  # noqa: E402

DOSSIER = ROOT / "data" / "research" / "institutional" / "accelerator-bandwidth-comparability-dossier-012.json"
TOP = {"dossier_id", "schema_version", "release", "status", "review_status", "scientific_review", "review_owner", "assessment_method",
       "as_of", "interpretation_standard", "research_question", "scope", "boundary", "inputs", "method", "figures", "normalizations",
       "rejected_normalizations", "comparisons", "cases", "workflow_b_mapping", "review_questions", "applications", "public_reference_decision",
       "principal_findings"}
FIG_FIELDS = {"id", "ref", "source_id", "value", "unit", "product", "configuration", "hierarchy_level", "metric", "counting_convention",
              "direction", "direction_basis", "aggregation_scope", "topology", "status", "conditions", "evidence_class", "uncertainty", "restrictions"}
LEVELS = {"memory_stack": "memory", "device_memory": "memory", "system_memory_aggregate": "memory",
          "device_fabric_link": "network", "device_fabric_aggregate": "network", "superchip_fabric_aggregate": "network",
          "system_fabric_aggregate": "network", "host_link": "network", "scale_out_port": "network"}
DIRECTIONS = {"bidirectional", "per_direction", "not_stated", "not_applicable"}
DIRECTION_BASES = {"source_stated", "unknown", "not_applicable"}
AGGREGATIONS = {"per_stack", "per_link", "per_device", "per_superchip", "per_system", "unresolved"}
STATUSES = {"advertised_peak", "specified_peak", "calculated_peak", "measured", "not_stated"}
PEAKS = {"advertised_peak", "specified_peak", "calculated_peak"}
CLASSES = {"comparable_on_documented_terms", "conditionally_comparable", "not_comparable", "indeterminate"}
PATHWAY_MAP = {"valid": {"comparable_on_documented_terms"}, "conditional": {"conditionally_comparable"},
               "unsupported": {"not_comparable", "indeterminate"}}
# How much a class or verdict permits. A recorded divergence from a pathway verdict may only restrict, never loosen.
STRICTNESS = {"comparable_on_documented_terms": 0, "conditionally_comparable": 1, "not_comparable": 2, "indeterminate": 2,
              "valid": 0, "conditional": 1, "unsupported": 2}
DIVERGENCE_FIELDS = {"pathway_comparison_id", "pathway_verdict", "dossier_classification", "justification", "status"}
DIVERGENCE_STATUS = "pending_editorial_reconciliation"
# Once the public pathway is corrected through a later reconciliation, the divergence stays recorded as history.
RECONCILED_STATUS = "reconciled"
LATER_RECONCILIATIONS = ROOT / "data" / "evidence-reconciliations-013.json"
COVERAGE = {"addressed", "partially_addressed", "open", "not_available"}
BYTES = {"TB/s": 1e12, "GB/s": 1e9}
BITS = {"Tb/s": 1e12 / 8, "Gb/s": 1e9 / 8, "Gbps": 1e9 / 8}
UNVERIFIED_EDITION = re.compile(r"MI350-007|PID#2258402")
ROUTE = re.compile(r"^(quantity|register|finding|statement):([a-z0-9-]+):([a-z0-9-]+)(?::(\d+))?$")


def j(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def load_context():
    releases = {r["release_id"]: r for r in (j(p) for p in sorted((ROOT / "data" / "research").glob("*.json")))}
    return {"registry": {s["id"]: s for s in j(ROOT / "data" / "source-registry.json")["source_records"]}, "releases": releases,
            "issues": {i["id"]: i for i in j(ROOT / "data" / "evidence-conflicts.json")["issues"]},
            "reconciliations": {r["id"]: r for r in j(ROOT / "data" / "evidence-reconciliations-009.json")["reconciliations"]},
            "workbench": j(ROOT / "data" / "industrial-evidence-requests.json"), "pathways": j(ROOT / "data" / "reference-pathways.json"),
            "atlas": j(ROOT / "data" / "dependency-atlas.json"),
            "later_reconciliations": {r["id"]: r for r in (j(LATER_RECONCILIATIONS)["reconciliations"] if LATER_RECONCILIATIONS.is_file() else [])}}


def number(value: str) -> float:
    return float(value.replace(",", ""))


def bytes_per_s(value: str, unit: str) -> float | None:
    scale = BYTES.get(unit) or BITS.get(unit)
    return None if scale is None else number(value) * scale


def resolve(ref: str, ctx) -> tuple[str | None, str | None, list[str]]:
    """Return (source_id, text-or-value, unit) recorded at a reference, or (None, None, [error])."""
    m = ROUTE.fullmatch(ref)
    if not m:
        return None, None, [f"reference '{ref}' is not a governed route"]
    kind, a, b, idx = m.groups()
    if kind == "register":
        idx = b if idx is None and b.isdigit() else idx
        ev = ctx["issues"].get(a, {}).get("evidence", [])
        if idx is None or int(idx) >= len(ev):
            return None, None, [f"register reference '{ref}' does not resolve"]
        return ev[int(idx)]["source_id"], ev[int(idx)]["locator"], []
    release = ctx["releases"].get(a)
    finding = next((f for f in release["findings"] if f["id"] == b), None) if release else None
    if finding is None:
        return None, None, [f"finding reference '{ref}' does not resolve"]
    if kind == "statement":
        if finding["claim_class"] != "bounded_analysis":
            return None, None, [f"'{ref}': only a bounded-analysis statement can be cited as a figure's record"]
        return None, finding["statement"], []
    items = finding.get("quantities", []) if kind == "quantity" else finding["evidence"]
    if idx is None or int(idx) >= len(items):
        return None, None, [f"reference '{ref}' does not resolve"]
    item = items[int(idx)]
    if kind == "quantity":
        return item["source_id"], f"{item['value']} {item['unit']}", []
    return item["source_id"], item["locator"], []


def quantity_label(ref: str, ctx) -> str | None:
    """The quantity a release records for a figure, normalised for comparison; None if the figure is not a release quantity."""
    m = ROUTE.fullmatch(ref)
    if not m or m.group(1) != "quantity":
        return None
    release = ctx["releases"].get(m.group(2))
    finding = next((f for f in release["findings"] if f["id"] == m.group(3)), None) if release else None
    items = finding.get("quantities", []) if finding else []
    idx = int(m.group(4)) if m.group(4) is not None else len(items)
    return re.sub(r"\s+", " ", items[idx]["quantity"].lower()).strip() if idx < len(items) else None


def divergence_errors(w: str, div, pid: str, verdict: str, cls: str) -> list[str]:
    """A dossier class outside the pathway verdict's mapping needs one exact, restrictive, pending divergence record."""
    if not isinstance(div, dict):
        return [f"{w}: classification {cls} contradicts pathway verdict '{verdict}' for {pid} and no divergence is recorded"]
    errs = []
    if set(div) != DIVERGENCE_FIELDS:
        errs.append(f"{w}: pathway divergence must contain exactly {sorted(DIVERGENCE_FIELDS)}")
        return errs
    if (div["pathway_comparison_id"], div["pathway_verdict"], div["dossier_classification"]) != (pid, verdict, cls):
        errs.append(f"{w}: pathway divergence must name this comparison's pathway id, its current verdict ('{verdict}') and this classification")
    if STRICTNESS[cls] <= STRICTNESS[verdict]:
        errs.append(f"{w}: a pathway divergence may only restrict the pathway verdict, never loosen it")
    if div["status"] != DIVERGENCE_STATUS:
        errs.append(f"{w}: a pathway divergence stays '{DIVERGENCE_STATUS}' until the pathway itself is reconciled in a release")
    if not isinstance(div["justification"], str) or len(div["justification"].strip()) < 60:
        errs.append(f"{w}: a pathway divergence needs a technical justification")
    return errs


def reconciled_divergence_errors(w: str, div, pid: str, verdict: str, cls: str, ctx) -> list[str]:
    """Where the class agrees with the pathway, a divergence may stay only as the history of a completed reconciliation."""
    if not isinstance(div, dict) or div.get("status") != RECONCILED_STATUS:
        return [f"{w}: a pathway divergence is recorded where the classification agrees with the pathway"]
    if set(div) != DIVERGENCE_FIELDS | {"reconciled_by"}:
        return [f"{w}: a reconciled divergence must contain exactly {sorted(DIVERGENCE_FIELDS | {'reconciled_by'})}"]
    rc = ctx.get("later_reconciliations", {}).get(div["reconciled_by"])
    errs = []
    if rc is None:
        return [f"{w}: reconciled_by names no reconciliation that exists"]
    if (rc["comparison_id"], rc["previous_verdict"], rc["corrected_verdict"]) != (pid, div["pathway_verdict"], verdict):
        errs.append(f"{w}: the reconciliation must cover this pathway comparison, from the recorded verdict to the pathway's current one")
    if div["pathway_comparison_id"] != pid or div["dossier_classification"] != cls:
        errs.append(f"{w}: the reconciled divergence must keep this comparison's id and classification")
    if STRICTNESS[cls] <= STRICTNESS[div["pathway_verdict"]]:
        errs.append(f"{w}: a pathway divergence may only restrict the pathway verdict, never loosen it")
    if not isinstance(div["justification"], str) or len(div["justification"].strip()) < 60:
        errs.append(f"{w}: a pathway divergence needs a technical justification")
    return errs


def appears(value: str, unit: str, text: str) -> bool:
    plain = text.replace(",", "")
    v = value.replace(",", "")
    pattern = rf"(?<![\d.]){re.escape(v)}(?:\.0)?\s*{re.escape(unit)}"
    return bool(re.search(pattern, plain)) or bool(re.search(rf"(?<![\d.]){re.escape(v)}(?:\.0)?(?![\d.])", plain) and unit in plain)


def check(d, ctx) -> list[str]:
    if not isinstance(d, dict) or set(d) != TOP:
        return ["bandwidth-dossier: top-level fields mismatch"]
    errors: list[str] = []
    if (d["status"], d["review_status"], d["scientific_review"], d["review_owner"]) != ("research_candidate", "not_reviewed", "pending", "unassigned"):
        errors.append("bandwidth-dossier: must stay a research candidate, not reviewed, scientific review pending, review owner unassigned")
    if d["assessment_method"] != "ai_assisted_source_check" or d["interpretation_standard"] != "AEC-CS-001":
        errors.append("bandwidth-dossier: assessment method and interpretation standard must be the governed values")
    for phrase in ("not an assessment of products", "never says which product is better", "records no human or scientific review", "does not promote"):
        if phrase not in d["boundary"]:
            errors.append(f"bandwidth-dossier: boundary must say '{phrase}'")
    if set(d["method"].get("comparability_classes", {})) != CLASSES:
        errors.append(f"bandwidth-dossier: comparability classes must be exactly {sorted(CLASSES)}")
    inputs = d["inputs"]
    for rid in inputs["release_ids"]:
        if rid not in ctx["releases"]:
            errors.append(f"bandwidth-dossier: release {rid} does not exist")
    for rid in inputs["reconciliation_ids"]:
        if rid not in ctx["reconciliations"]:
            errors.append(f"bandwidth-dossier: reconciliation {rid} does not exist")
    for cid in inputs["conflict_ids"]:
        if cid not in ctx["issues"]:
            errors.append(f"bandwidth-dossier: register issue {cid} does not exist")
    wf = next((w for w in ctx["workbench"]["workflows"] if w["id"] == inputs["workflow_id"]), None)
    pathway = next((p for p in ctx["pathways"]["pathways"] if p["id"] == inputs["pathway_id"]), None)
    if wf is None or pathway is None:
        return errors + ["bandwidth-dossier: workflow and pathway must exist"]

    # Figures.
    figs = {}
    for f in d["figures"]:
        if not isinstance(f, dict) or set(f) != FIG_FIELDS:
            errors.append(f"bandwidth-dossier: figure {f.get('id') if isinstance(f, dict) else f} fields mismatch")
            continue
        w = f"bandwidth-dossier.figure[{f['id']}]"
        if f["id"] in figs:
            errors.append(f"{w}: duplicate id")
        figs[f["id"]] = f
        if f["unit"] not in BYTES and f["unit"] not in BITS:
            errors.append(f"{w}: unit {f['unit']} is not a bandwidth unit")
        if f["hierarchy_level"] not in LEVELS or f["direction"] not in DIRECTIONS or f["direction_basis"] not in DIRECTION_BASES \
                or f["aggregation_scope"] not in AGGREGATIONS or f["status"] not in STATUSES:
            errors.append(f"{w}: descriptors must use the governed vocabularies")
        if f["direction"] in ("bidirectional", "per_direction") and f["direction_basis"] != "source_stated":
            errors.append(f"{w}: a direction may be recorded only when the source states it")
        if f["direction"] == "not_stated" and f["direction_basis"] != "unknown":
            errors.append(f"{w}: an unstated direction must have basis 'unknown'")
        if (f["direction"] == "not_applicable") != (f["direction_basis"] == "not_applicable"):
            errors.append(f"{w}: 'not_applicable' direction and basis go together")
        if LEVELS.get(f["hierarchy_level"]) == "memory" and f["direction"] != "not_applicable":
            errors.append(f"{w}: memory bandwidth carries no link direction")
        if f["status"] == "measured":
            errors.append(f"{w}: no reviewed source publishes a measured figure; 'measured' needs a measurement record")
        if f["source_id"] not in ctx["registry"] or ctx["registry"][f["source_id"]]["status"] != "active":
            errors.append(f"{w}: source {f['source_id']} must be an active registered source")
        for field in ("configuration", "topology", "counting_convention", "conditions", "product", "metric"):
            if not isinstance(f[field], str) or not f[field].strip():
                errors.append(f"{w}.{field}: state the value or 'unknown'")
        if not f["uncertainty"] or not f["restrictions"]:
            errors.append(f"{w}: uncertainty and restrictions must be stated")
        src, text, errs = resolve(f["ref"], ctx)
        errors += [f"{w}: {e}" for e in errs]
        if text is not None:
            if f["ref"].startswith("statement:"):
                if f["evidence_class"] != "bounded_analysis":
                    errors.append(f"{w}: a figure taken from a bounded-analysis statement is bounded analysis")
            elif src != f["source_id"]:
                errors.append(f"{w}: source {f['source_id']} does not match the record's source {src}")
            if not appears(f["value"], f["unit"], text):
                errors.append(f"{w}: value {f['value']} {f['unit']} does not appear in the record it cites")
    # Normalizations.
    rules = {r["id"]: r for r in d["method"].get("normalization_rules", [])}
    norms = {}

    def violations(fig: dict, rule: dict) -> list[str]:
        out = []
        for cond in rule["requires"]:
            if " in " in cond:
                key, allowed = cond.split(" in ", 1)
                ok = fig.get(key.strip()) in [a.strip() for a in allowed.split(",")]
            else:
                key, _, want = cond.partition("=")
                ok = fig.get(key) == want
            if not ok:
                out.append(f"requires {cond}")
        for cond in rule["rejects_when"]:
            key, _, bad = cond.partition("=")
            if fig.get(key) == bad:
                out.append(f"rejected when {cond}")
        if rule["from_units"] and fig.get("unit") not in rule["from_units"]:
            out.append(f"applies only to {rule['from_units']}")
        return out

    for n in d["normalizations"]:
        w = f"bandwidth-dossier.normalization[{n.get('id')}]"
        fig, rule = figs.get(n.get("figure_id")), rules.get(n.get("rule_id"))
        if fig is None or rule is None:
            errors.append(f"{w}: figure and rule must exist")
            continue
        norms[n["id"]] = n
        for v in violations(fig, rule):
            errors.append(f"{w}: unsupported normalization of {fig['id']} ({v})")
        if rule["factor"] is not None and n["factor"] != rule["factor"]:
            errors.append(f"{w}: rule {rule['id']} fixes the factor at {rule['factor']}")
        base, result = bytes_per_s(fig["value"], fig["unit"]), bytes_per_s(n["result_value"], n["result_unit"])
        if base is None or result is None:
            errors.append(f"{w}: units must be bandwidth units")
        else:
            # Units are compared in bytes per second, so a bits-to-bytes conversion leaves the value unchanged.
            expected = base if rule["id"] == "nr-bits-to-bytes" else base * n["factor"] if rule["operation"] == "multiply" else base / n["factor"]
            if abs(expected - result) > 1e-9 * max(expected, 1):
                errors.append(f"{w}: arithmetic does not hold ({fig['value']} {fig['unit']} {rule['operation']} {n['factor']} "
                              f"is not {n['result_value']} {n['result_unit']})")
        if rule["id"] == "nr-bits-to-bytes" and n["result_unit"] not in BYTES:
            errors.append(f"{w}: a bits-to-bytes conversion must give a byte unit")
        if n.get("result_level") not in LEVELS:
            errors.append(f"{w}: result level must be governed")
        for b in n["basis"]:
            if resolve(b, ctx)[2]:
                errors.append(f"{w}: basis {b} does not resolve")
        if "not a publisher statement" not in n["note"]:
            errors.append(f"{w}: the note must say the result is arithmetic, not a publisher statement")
    for r in d["rejected_normalizations"]:
        fig, rule = figs.get(r.get("figure_id")), rules.get(r.get("rule_id"))
        if fig is None or rule is None or not violations(fig, rule):
            errors.append(f"bandwidth-dossier.rejected[{r.get('id')}]: a rejected normalization must actually break its rule")
    # Comparisons.
    pathway_cmps = {c["id"]: c for c in pathway.get("comparisons", [])}
    mapped = set()
    for c in d["comparisons"]:
        w = f"bandwidth-dossier.comparison[{c.get('id')}]"
        pair = [figs.get(x) for x in c.get("figure_ids", [])]
        if len(pair) != 2 or None in pair:
            errors.append(f"{w}: must compare two existing figures")
            continue
        cls = c["classification"]
        if cls not in CLASSES:
            errors.append(f"{w}: classification must be one of {sorted(CLASSES)}")
            continue
        used = [norms.get(x) for x in c["normalization_ids"]]
        if None in used:
            errors.append(f"{w}: normalization ids must exist")
            continue
        # Effective descriptors after normalization.
        eff = []
        for f in pair:
            n = next((u for u in used if u["figure_id"] == f["id"]), None)
            eff.append({"level": n["result_level"] if n else f["hierarchy_level"],
                        "aggregation": "per_device" if n and rules[n["rule_id"]]["id"] == "nr-equal-share" else f["aggregation_scope"],
                        "unit": n["result_unit"] if n else f["unit"]})
        for u in used:
            if u["figure_id"] not in c["figure_ids"]:
                errors.append(f"{w}: normalization {u['id']} does not apply to a compared figure")
        cond_text = " ".join(c["conditions"]).lower()
        unknown_direction = any(f["direction"] == "not_stated" for f in pair)
        unresolved_scope = any(f["aggregation_scope"] == "unresolved" for f in pair)
        same_dimension = (eff[0]["unit"] in BYTES) == (eff[1]["unit"] in BYTES)
        if cls == "comparable_on_documented_terms":
            if eff[0]["level"] != eff[1]["level"] or eff[0]["aggregation"] != eff[1]["aggregation"] or not same_dimension \
                    or pair[0]["direction"] != pair[1]["direction"] or unknown_direction or unresolved_scope \
                    or not all(f["status"] in PEAKS for f in pair) or c["conditions"]:
                errors.append(f"{w}: 'comparable on documented terms' needs the same level, scope, direction and peak status, all stated, and no conditions")
        elif cls == "conditionally_comparable":
            if not c["conditions"]:
                errors.append(f"{w}: a conditional comparison must state its conditions")
            if eff[0]["level"] != eff[1]["level"] or eff[0]["aggregation"] != eff[1]["aggregation"] or not same_dimension:
                errors.append(f"{w}: a conditional comparison needs the same hierarchy level, aggregation scope and unit dimension "
                              "after normalization; a unit conversion does not make different metrics comparable")
            if unresolved_scope:
                errors.append(f"{w}: a figure with an unresolved scope cannot be compared; use 'indeterminate'")
            if unknown_direction and "direction" not in cond_text:
                errors.append(f"{w}: a figure states no direction; a condition must name it, or the class is 'indeterminate'")
            if any(f["status"] == "not_stated" for f in pair) and "peak" not in cond_text:
                errors.append(f"{w}: a figure does not state its peak status; a condition must name it")
        elif cls == "not_comparable":
            if eff[0]["level"] == eff[1]["level"] and eff[0]["aggregation"] == eff[1]["aggregation"]:
                # Same level and scope: the metric difference must come from the release's own quantity records,
                # not from the dossier's wording of the two figures.
                labels = [quantity_label(f["ref"], ctx) for f in pair]
                if None in labels or labels[0] == labels[1]:
                    errors.append(f"{w}: 'not comparable' at one level and scope needs release quantity records whose "
                                  "recorded quantities differ; a difference in the dossier's own wording is not enough")
        elif cls == "indeterminate":
            if not (unknown_direction or unresolved_scope):
                errors.append(f"{w}: 'indeterminate' needs a figure with an unstated direction or unresolved scope")
        if not c["reason"].strip():
            errors.append(f"{w}: a classification needs a reason")
        pid = c.get("pathway_comparison_id")
        div = c.get("pathway_divergence")
        if pid is not None:
            if pid not in pathway_cmps:
                errors.append(f"{w}: pathway comparison {pid} does not exist")
            else:
                verdict = pathway_cmps[pid]["verdict"]
                if cls not in PATHWAY_MAP[verdict]:
                    errors += divergence_errors(w, div, pid, verdict, cls)
                elif div is not None:
                    errors += reconciled_divergence_errors(w, div, pid, verdict, cls, ctx)
            mapped.add(pid)
        elif div is not None:
            errors.append(f"{w}: a pathway divergence needs a pathway comparison")
    if set(pathway_cmps) - mapped:
        errors.append(f"bandwidth-dossier: pathway comparisons not classified: {sorted(set(pathway_cmps) - mapped)}")
    # Cases: preserve the IDE-009 reconciliations.
    unresolved = {u["id"] for r in ctx["releases"].values() for u in r["unresolved"]}
    case_ids = {c["id"] for c in d["cases"]}
    if case_ids != {"case-a-mi300x", "case-b-rubin-memory", "case-c-nvlink6"}:
        errors.append("bandwidth-dossier: the three mandatory cases must be present")
    for case in d["cases"]:
        w = f"bandwidth-dossier.case[{case['id']}]"
        if case["conflict_id"] not in ctx["issues"] or case["reconciliation_id"] not in ctx["reconciliations"]:
            errors.append(f"{w}: conflict and reconciliation must exist")
        elif ctx["issues"][case["conflict_id"]]["state"] == "resolved_with_evidence":
            errors.append(f"{w}: the register shows the issue resolved; the case must follow the register")
        for x in case["figure_ids"]:
            if x not in figs:
                errors.append(f"{w}: figure {x} does not exist")
        for x in case["comparison_ids"]:
            if x not in {c["id"] for c in d["comparisons"]}:
                errors.append(f"{w}: comparison {x} does not exist")
        for u in case["unresolved_ids"]:
            if u not in unresolved:
                errors.append(f"{w}: open question {u} does not exist")
        for line in case["established"] + case["analysis"] + case["preserved"]:
            if UNVERIFIED_EDITION.search(line) and "pending version verification" not in line:
                errors.append(f"{w}: the unverified 2025 CDNA 4 edition may appear only as pending version verification: '{line[:60]}'")
    amd = figs.get("fg-a-896-platform")
    if not amd or amd["direction"] != "bidirectional" or amd["aggregation_scope"] != "unresolved":
        errors.append("bandwidth-dossier: the MI300X 896 GB/s figure must keep its AMD-stated direction and unresolved scope (IDE-009)")
    for fid in ("fg-b-22-gpu", "fg-b-192-blog", "fg-c-36-platform", "fg-c-3-blog"):
        if fid in figs and not any("select" in r.lower() or "not comparable with" in r.lower() or "cite" in r.lower() for r in figs[fid]["restrictions"]):
            errors.append(f"bandwidth-dossier.figure[{fid}]: a conflicting figure must carry a restriction against selecting it")
    # Principal findings rest on normalizations, comparisons or figures in this dossier.
    known = set(figs) | set(norms) | {c["id"] for c in d["comparisons"]} | {r["id"] for r in d["rejected_normalizations"]}
    for p in d["principal_findings"]:
        if not p.get("basis") or any(b not in known for b in p["basis"]):
            errors.append(f"bandwidth-dossier.principal_findings: '{p.get('text', '')[:40]}' needs a basis in this dossier's figures, normalizations or comparisons")
    # Workflow B coverage and review questions.
    reqs = {r["id"] for r in wf["requirements"]}
    got = [m["requirement_id"] for m in d["workflow_b_mapping"]]
    if sorted(got) != sorted(reqs):
        errors.append("bandwidth-dossier: every workflow B requirement must be mapped exactly once")
    for m in d["workflow_b_mapping"]:
        if m["coverage"] not in COVERAGE or any(x not in figs for x in m["figure_ids"]):
            errors.append(f"bandwidth-dossier.mapping[{m['requirement_id']}]: coverage and figures must be governed")
        if m["coverage"] == "addressed" and not m["figure_ids"]:
            errors.append(f"bandwidth-dossier.mapping[{m['requirement_id']}]: an addressed requirement names its figures")
    for q in d["review_questions"]:
        if not q["question"].rstrip().endswith("?") or any(s not in ctx["registry"] or ctx["registry"][s]["status"] != "active" for s in q["materials"]):
            errors.append(f"bandwidth-dossier.review[{q['id']}]: a question with public, active source materials")
        if q["case_id"] is not None and q["case_id"] not in case_ids:
            errors.append(f"bandwidth-dossier.review[{q['id']}]: case does not exist")
    if d["public_reference_decision"].get("change_made") is not False:
        errors.append("bandwidth-dossier: public reference changes must go through a release and its validators")
    if ctx["atlas"].get("relationships"):
        errors.append("bandwidth-dossier: the Atlas has relationships; this dossier must not be read as promoting any")
    errors += _content_checks(d, "bandwidth-dossier", set(), prose_skip=(".boundary",))
    return errors


def check_all() -> list[str]:
    if not DOSSIER.is_file():
        return [f"required dossier missing: {DOSSIER.relative_to(ROOT)}"]
    errors = check(j(DOSSIER), load_context())
    if not errors:
        import render_bandwidth_dossier as render
        for name in render.out_of_sync():
            errors.append(f"{name} is out of date; run scripts/render_bandwidth_dossier.py")
    return errors


def main() -> None:
    errors = check_all()
    if errors:
        for e in errors:
            print(f"FAIL: {e}", file=sys.stderr)
        raise SystemExit(1)
    d = j(DOSSIER)
    counts = {}
    for c in d["comparisons"]:
        counts[c["classification"]] = counts.get(c["classification"], 0) + 1
    print(f"PASS: Bandwidth dossier valid ({len(d['figures'])} figures traced, {len(d['normalizations'])} normalizations recomputed, "
          f"{len(d['rejected_normalizations'])} rejected; {len(d['comparisons'])} comparisons: "
          + ", ".join(f"{k} {v}" for k, v in sorted(counts.items())) + "; no review recorded).")


if __name__ == "__main__":
    main()
