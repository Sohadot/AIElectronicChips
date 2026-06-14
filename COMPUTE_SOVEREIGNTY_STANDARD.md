# Compute Sovereignty Standard

## Status and Core Principle

- **Standard ID:** AEC-CS-001
- **Version:** 0.1.0
- **Status:** Foundation standard
- **Thesis:** AI chips are the physical substrate of compute sovereignty.

AEC-CS-001 is an internal project interpretation standard. It is not an
external accreditation, certification, or industry-wide standard.

> **Compute sovereignty is interpreted through layered dependency exposure, not
> reduced to a single score.**

## 1. Purpose

This standard defines how AIElectronicChips.com interprets compute sovereignty
through evidence-backed, layered dependency exposure. It governs how findings,
confidence, limitations, and artifacts are read without converting them into a
score or final sovereignty judgment.

## 2. Scope and Non-Scope

The standard governs dependency records, the eight sovereignty layers, the six
exposure types, evidence, confidence, bounded artifacts, unknowns, conflicts,
and changing conditions.

It does not assign sovereignty or non-sovereignty; create a score, ranking,
benchmark, or maturity grade; certify independence, resilience, compliance,
readiness, or performance; or provide investment, procurement, purchase,
deployment, or policy advice.

## 3. Normative Language and Unit of Interpretation

**MUST** and **MUST NOT** are required for conformance. **SHOULD** and **SHOULD
NOT** are expected unless a documented reason supports an exception. **MAY** is
permitted but not required.

The unit of interpretation is a bounded dependency record within a declared
scope. A record MUST identify layers, dependency, exposure types, finding,
evidence, confidence, limitations, review ownership, and an `as_of` date.

A diagnostic response is an input to investigation, not a finding. A collection
of findings is not a sovereignty verdict.

## 4. Sovereignty Stack Layers

Every finding MUST reference one or more valid layers:

| Layer | Interpretation focus |
| --- | --- |
| `design` | Architecture, rights, tools, verification, and specialist capability. |
| `fabrication` | Manufacturing access, process capability, capacity, equipment, and yield. |
| `packaging` | Integration, assembly, substrates, test, and deployable-system preparation. |
| `memory` | Required memory type, bandwidth, capacity, qualification, and access. |
| `interconnect` | Data movement within and between systems and deployments. |
| `power_thermal` | Power capacity, density, cooling, heat rejection, and operating constraints. |
| `controls` | Applicable rules, licenses, thresholds, exceptions, scope, and effective dates. |
| `deployment` | Installation, operation, maintenance, recovery, and geographic distribution. |

No layer may be interpreted as sovereign in isolation. Control or access at one
layer MUST NOT be used to infer control or access at another layer.

## 5. Exposure Types

| Exposure type | Meaning |
| --- | --- |
| `concentration_exposure` | Dependence on a narrow source, location, pathway, or substitute set. |
| `access_exposure` | Dependence on permission, licensing, allocation, contractual access, or another access condition. |
| `capacity_exposure` | A supported constraint in scale, lead time, throughput, power, cooling, or deployable capacity. |
| `technology_exposure` | Dependence on proprietary capability, tools, integration, expertise, or compatibility. |
| `operational_exposure` | A supported constraint affecting installation, operation, maintenance, continuity, or recovery. |
| `evidence_exposure` | Evidence is incomplete, stale, conflicting, unattributable, or insufficient for the intended finding. |

Exposure types may coexist. They MUST NOT be treated as mutually exclusive,
automatically negative, or equivalent to a sovereignty judgment.

## 6. Confidence Model

Confidence describes evidence quality and completeness. It does not describe
how certain an author feels and MUST NOT be used as rhetorical emphasis.

| Confidence | Standard interpretation |
| --- | --- |
| `high` | Strong, attributable, sufficiently current evidence directly supports the bounded finding; material conflicts and limitations are disclosed. |
| `medium` | Credible evidence supports the finding, but material limitations, indirect elements, or unresolved conflicts remain. |
| `low` | Limited or indirect evidence permits only a narrow, visibly qualified finding. |
| `insufficient` | Evidence does not support an operational finding; the output may document the evidence gap only. |

Confidence MUST NOT be calculated from diagnostic answers alone. It MUST be
assigned through governed review of evidence and scope.

## 7. Evidence Requirements

A conforming finding MUST cite attributable evidence appropriate to its risk;
prefer primary, dated, official sources where practicable; identify publication
or effective date and date accessed; state relevant scope; include an `as_of`
date; distinguish fact, attributed statement, estimate, analysis, and unknown;
disclose credible conflicts; and state material limitations.

Evidence MUST NOT be invented, inferred from absence, or represented as current
after its supported time horizon.

## 8. Interpretation Rules

1. Findings MUST remain bounded by declared scope, time horizon, and evidence.
2. Findings MUST be read by layer and exposure type before cross-layer synthesis.
3. Synthesis MUST preserve contradictions, unknowns, and differing confidence.
4. Missing evidence MUST be treated as evidence exposure, not proof of weakness.
5. Substitutability and criticality MUST be scoped and supported.
6. A change in one layer MUST NOT be generalized to the full stack.
7. Artifact hints identify a next analysis format; they are not recommendations.
8. Every artifact MUST disclose limitations and an `as_of` date.

## 9. Prohibited Interpretations

The following are non-conforming:

- declaring an entity sovereign or non-sovereign;
- aggregating findings into a score, rank, benchmark, or maturity grade;
- treating high confidence as proof of favorable capability;
- treating low or insufficient confidence as proof of weakness;
- treating exposure as failure or dependence as misconduct;
- assigning intent without evidence;
- converting artifact hints into commercial or investment recommendations;
- presenting announced policy or planned capacity as an operating condition;
- comparing entities without equivalent scope, evidence, time horizon, and
  methodology.

## 10. Artifact Rules

### Compute Sovereignty Brief

May be issued when supported findings across one or more layers answer a
declared decision question. It MUST preserve layer-level exposure, confidence,
unknowns, and limitations. It MUST NOT assign sovereignty or provide an
operational verdict.

### Chip Dependency Audit

May be issued when a scoped set of dependency records has sufficient evidence
for structured review. It MUST identify assessed and unassessed layers. It MUST
NOT certify independence, resilience, compliance, or readiness.

### Infrastructure Readiness Brief

May be issued when deployment, interconnect, power, thermal, and operating
conditions are sufficiently evidenced. It MUST distinguish planned, accessible,
and operating conditions. It MUST NOT guarantee capacity, availability,
performance, or successful deployment.

### Premium Reference Dossier

May be issued when a defined layer, dependency, or evidence question can be
documented deeply and consistently. It MUST separate reference material from
analysis. It MUST NOT provide a ranking, purchase recommendation, or investment
advice.

## 11. When Findings Must Be Insufficient

A finding MUST be labeled `insufficient` when evidence is absent,
unattributable, unverifiable, materially incomplete, stale, or disproportionate
to claim risk; credible conflicts cannot be resolved; applicable scope,
thresholds, exceptions, or effective dates are unclear; unsupported inference
is required; or material layers remain unassessed.

`insufficient` MUST result in no operational finding. It MAY identify evidence
needed for future review.

## 12. Changing Conditions

Policy, capacity, ownership, access, and operating conditions can change. Every
affected finding MUST carry an `as_of` date and SHOULD define a review date or
trigger.

A finding MUST be reviewed before reuse when a relevant rule, license,
threshold, exception, capacity condition, ownership condition, access
condition, source, deployment scope, or decision context materially changes.
Historical evidence MUST NOT silently represent current conditions.

## 13. Why No Sovereignty Score Is Permitted

A score is not permitted because layers contain different kinds of capability
and access; exposure types are contextual and not naturally commensurable;
confidence varies by finding; aggregation hides unknowns and conflicts; weights
would introduce unsupported normative judgments; and a number could be misread
as a political, commercial, or operational verdict.

No score may be introduced without a separately governed standard revision,
documented methodology, validation evidence, and explicit approval. This
standard does not imply that such approval will be appropriate.

## 14. Future Upgrade Path

Future revisions MAY formalize review workflows, conformance checklists,
criticality and substitutability terminology, evidence freshness rules,
artifact templates, correction and versioning procedures, and a separately
governed evidence-backed pilot.

No upgrade may silently introduce a score, ranking, sovereignty assignment, or
automated operational judgment.

## 15. Conformance

An artifact conforms to AEC-CS-001 only when it follows this standard and
`SOURCE_POLICY.md` and `CLAIM_POLICY.md`; preserves unknowns; applies
`insufficient` where required; respects artifact boundaries; discloses scope,
`as_of` date, confidence, evidence, and limitations; and avoids every
prohibited interpretation.

Conformance means the artifact follows this interpretation standard. It does
not certify the subject of the artifact.
