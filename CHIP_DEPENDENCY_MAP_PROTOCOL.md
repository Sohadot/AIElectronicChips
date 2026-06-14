# Chip Dependency Map Protocol

## Purpose

The Chip Dependency Map is a governed diagnostic model for revealing layered
dependency exposure. Its structured output is a **Compute Dependency Exposure
Map**. It does not produce a sovereignty score, ranking, or operational verdict.

## Protocol Boundary

The model may:

- define an assessment scope, entity type, decision context, and time horizon;
- ask bounded questions across the eight sovereignty layers;
- identify relevant exposure types and evidence gaps;
- attach confidence and limitations to findings;
- suggest an appropriate governed artifact.

The model must not:

- infer facts about a specific entity without evidence;
- treat missing information as proof of weakness;
- combine exposures into a universal score;
- rank entities, technologies, jurisdictions, or suppliers;
- present a model preview as a completed assessment.

## Assessment Sequence

1. **Declare scope:** identify the assessment subject, purpose, time horizon,
   relevant geography, and review owner.
2. **Collect evidence:** follow `SOURCE_POLICY.md`; record source metadata and an
   `as_of` date.
3. **Answer diagnostic questions:** use the model answer options and preserve
   unknown or not-applicable responses.
4. **Create dependency records:** map each supported finding to layers,
   exposure types, evidence, confidence, and limitations.
5. **Review claims:** apply `CLAIM_POLICY.md`, especially for access controls,
   strategic vulnerability, and changing capacity.
6. **Produce bounded output:** present exposure by layer, unknowns, confidence,
   and a suggested artifact. Do not aggregate into a score.
7. **Schedule review:** define when changing conditions require reassessment.

## Interpretation Rules

- A question response is an input, not a finding.
- A finding requires evidence appropriate to its consequence and risk.
- `insufficient` confidence results in no operational finding.
- Exposure types may coexist and must not be treated as mutually exclusive.
- Control of one layer does not imply control of adjacent layers.
- Suggested artifacts identify the appropriate next analysis format; they are
  not recommendations to purchase.

## Output Contract

A Compute Dependency Exposure Map should contain:

- declared scope and `as_of` date;
- assessed and unassessed layers;
- dependency records grouped by layer;
- applicable exposure types;
- confidence and evidence references;
- known limitations, conflicts, and unknowns;
- suggested governed artifact type;
- review ownership and next review date where applicable.

## Governance

The canonical machine-readable foundation is
`data/chip-dependency-model.json`. Changes to its controlled vocabularies,
question boundaries, or prohibited outputs require validation and a recorded
decision.

