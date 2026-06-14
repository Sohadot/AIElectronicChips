# Model Coherence Audit

## Audit Scope

Sprint 2A reviews the Chip Dependency Map foundation for conceptual coherence,
governance alignment, model safety, and consistency with the principle:

> The Chip Dependency Map reveals layered exposure. It does not assign
> sovereignty.

The audit does not add an assessment feature, score, ranking, dashboard,
chatbot, API, external dependency, entity example, or operational claim.

## Files Reviewed

- `data/chip-dependency-model.json`
- `CHIP_DEPENDENCY_MAP_PROTOCOL.md`
- `DEPENDENCY_RECORD_SCHEMA.md`
- `chip-dependency-map/index.html`
- `README.md`
- `DECISION_LOG.md`
- `COMPUTE_SOVEREIGNTY_ONTOLOGY.md`
- `CLAIM_POLICY.md`
- `SOURCE_POLICY.md`
- `ASSET_INTELLIGENCE_FACTORY_PLAN.md`
- `scripts/validate_chip_dependency_model.py`

## Layer Coverage Assessment

All eight governed layers are represented by at least one layer-specific
question and by two cross-layer questions.

| Layer | Question references | Assessment |
| --- | ---: | --- |
| Design | 4 | Clear; two specific questions plus cross-layer review. |
| Fabrication | 3 | Clear and proportionate. |
| Packaging | 3 | Clear and proportionate. |
| Memory | 3 | Clear and proportionate. |
| Interconnect | 3 | Clear and proportionate. |
| Power / Thermal | 4 | Clear; separate power and thermal questions are justified. |
| Controls | 3 | Clear and deliberately evidence-led. |
| Deployment | 3 | Clear and proportionate. |

Design and power / thermal appear one additional time because each is split
into two materially different questions. No layer is absent or
disproportionately dominant.

## Exposure Type Assessment

All six exposure types are valid against the ontology and used across the
question set.

| Exposure type | Question references | Assessment |
| --- | ---: | --- |
| Concentration exposure | 4 | Adequate; focused on substitution and supply concentration. |
| Access exposure | 6 | Adequate; expected prominence for controlled or allocated capability. |
| Capacity exposure | 7 | Adequate; expected prominence for infrastructure and production constraints. |
| Technology exposure | 6 | Adequate; correctly attached to capability and integration questions. |
| Operational exposure | 5 | Adequate; correctly attached to continuity and deployment questions. |
| Evidence exposure | 5 | Adequate; preserves unknowns and prevents unsupported findings. |

The distribution is coherent. Access and capacity exposure are most frequent,
but neither is used as a proxy for sovereignty or as a default negative
finding.

## Confidence Model Assessment

The four confidence levels remain `high`, `medium`, `low`, and `insufficient`.
Across the protocol, schema, public preview, and Claim Policy, confidence
describes evidence quality and completeness rather than rhetorical certainty.

`insufficient` confidence explicitly produces no operational finding. The model
does not calculate confidence or convert answers into confidence labels.

## Diagnostic Question Assessment

All twelve questions reference valid layers, exposure types, and artifact
outputs. No question asks whether an entity is sovereign or implies a
definitive sovereignty judgment.

| Question | Coherence assessment |
| --- | --- |
| `design_control` | Correctly maps design access, technology, and evidence exposure. Reworded to ask what evidence establishes the condition. |
| `design_tooling_continuity` | Correctly separates continuity from design control. Reworded to be evidence-led. |
| `fabrication_access` | Correctly combines access, capacity, and concentration within scope and time horizon. Reworded to be evidence-led. |
| `packaging_capacity` | Correctly covers packaging, assembly, and test capability. Reworded to avoid an unsupported availability judgment. |
| `memory_access` | Correctly covers access, capacity, concentration, and qualification. Reworded to be evidence-led. |
| `interconnect_fit` | Correctly maps technology, capacity, and operational exposure. Reworded to require support for deployment fit. |
| `power_capacity` | Correctly maps capacity and operations while preserving evidence gaps. Reworded to require support. |
| `thermal_capacity` | Correctly separates thermal capability from power capacity. Reworded to require support. |
| `control_applicability` | Correctly focuses on scope, exceptions, and effective dates. Reworded to require evidence rather than assumed understanding. |
| `deployment_readiness` | Correctly covers installation, operations, maintenance, and recovery. Reworded to avoid implying certification. |
| `substitution_path` | Correctly provides a cross-layer concentration and access review. Reworded to ask what evidence supports credible paths. |
| `evidence_completeness` | Correctly provides a cross-layer governance gate. Reworded to test evidence requirements rather than certainty. |

The question count remains twelve, within the governed range of eight to
sixteen.

## Output Artifact Assessment

The four artifact outputs are retained and now have machine-readable purpose
and boundary definitions:

- **Compute Sovereignty Brief:** bounded synthesis; no sovereignty assignment,
  ranking, or operational verdict.
- **Chip Dependency Audit:** scoped dependency-record review; no certification
  of independence, resilience, compliance, or readiness.
- **Infrastructure Readiness Brief:** bounded operating-condition assessment; no
  guarantee of capacity, availability, performance, or deployment.
- **Premium Reference Dossier:** deep governed reference; no ranking, purchase
  recommendation, or investment advice.

Question-level `suggested_artifacts` are classification hints for the next
analysis format. They do not behave as purchase, investment, deployment, or
operational recommendations.

## Prohibited-Risk Review

| Risk | Verdict |
| --- | --- |
| Sovereignty score or assignment | Prohibited and absent. |
| Ranking or comparative league table | Prohibited and absent. |
| Definitive judgment from question responses | Prevented by evidence-led wording and protocol. |
| Missing evidence treated as weakness | Prohibited; evidence exposure and `insufficient` preserve uncertainty. |
| Artifact hint treated as advice | Boundary language added to model, protocol, schema, and public preview. |
| Specific entity claims or examples | Absent. |
| Fake interactive or automated assessment | Absent; public page remains a model preview. |

## Changes Made

- Reworded all twelve questions to request evidence or test evidence
  sufficiency instead of inviting unsupported self-assessment.
- Added machine-readable `artifact_boundaries` for the four artifact outputs.
- Strengthened protocol language so artifact hints are classifications, not
  recommendations.
- Clarified the optional `suggested_artifact` schema field.
- Updated the public model preview to reflect the bounded classification
  language.
- Extended model validation to require complete artifact boundaries.

## Deferred Risks

- The model does not define an automated mapping from answer options to
  exposure findings or confidence. This is intentionally deferred because such
  mapping could imply unsupported certainty.
- Artifact hint frequency is uneven: audits and dossiers appear more often than
  readiness briefs. This is coherent with the current questions but should be
  re-audited if the question set changes.
- Criticality and substitutability remain optional dependency-record fields.
  Their interpretation should be standardized before any operational use.
- No real assessment records exist. The model's practical reliability cannot be
  evaluated until a separately governed evidence-backed pilot is authorized.

## Final Audit Verdict

**PASS**

The Chip Dependency Map foundation is conceptually coherent, aligned with
Sprint 0 governance, and safe to retain as a model preview. It reveals layered
dependency exposure and does not assign sovereignty. Sprint 2A adds no
assessment feature and authorizes no operational use.

