# Decision Log

This log records decisions that govern the direction, credibility, and
commercial boundaries of AIElectronicChips.com.

## ADR-001: Establish AI Chip Sovereignty Intelligence as the Category

- **Date:** 2026-06-14
- **Status:** Accepted

### Decision

AIElectronicChips.com will be developed as a governed reference layer and
category intelligence factory for **AI Chip Sovereignty Intelligence**.

Its foundation is:

> AI chips are the physical substrate of compute sovereignty.

The asset will not operate as a chip news site, GPU review publication,
affiliate catalog, general AI blog, or high-volume content property.

### Rationale

The strategic value of AI chips cannot be understood through product
specifications alone. Practical AI compute depends on design, fabrication,
packaging, memory, interconnect, power and thermal capacity, controls, and
deployment. A governed category and ontology create a more durable and credible
asset than commodity publishing.

### Consequences

- Research and public claims must comply with the source and claim policies.
- The public interface must express the Silicon Sovereignty Stack.
- Products and monetization must extend the governed reference value.
- Unsupported rankings, sovereignty scores, and shallow comparisons are out of
  scope.

## ADR-002: Name the First Public Tool and Its Output

- **Date:** 2026-06-14
- **Status:** Accepted

### Decision

**Chip Dependency Map** is the public name of the first diagnostic tool.

**Compute Dependency Exposure Map** is the structured output produced by that
tool.

### Rationale

The tool name is direct and understandable. The output name accurately
describes a layered exposure assessment without implying a definitive
sovereignty score.

### Consequences

- Sprint 1 public language must use these names consistently.
- Sprint 2 must define the output schema, confidence labels, and limitations.
- The tool must present a preliminary governed diagnosis, not a final judgment.

## ADR-003: Accept Sprint 0 Foundation

- **Date:** 2026-06-14
- **Status:** Accepted

### Decision

Sprint 0, **Compute Sovereignty Foundation**, is accepted as the governing base
for Sprint 1, subject to continued compliance with its policies and boundaries.

### Consequences

Sprint 1 may begin the focused Public Reference Surface. It should contain only
the pages necessary to explain the category, sovereignty stack, methodology,
sources, first tool, and strategic availability.

## ADR-004: Establish the Chip Dependency Map Foundation

- **Date:** 2026-06-14
- **Status:** Accepted

### Decision

The Chip Dependency Map foundation is defined as a governed, machine-readable
diagnostic model. It contains eight dependency layers, six exposure types, four
confidence levels, four artifact outputs, and twelve bounded diagnostic
questions.

The model reveals layered dependency exposure. It does not aggregate findings
into a sovereignty score, rank entities, or create claims about specific
companies, countries, chips, or governments.

### Rationale

Governance must precede interaction. A controlled vocabulary, protocol,
dependency record schema, and validation process make future outputs
inspectable and prevent an interface from implying unsupported certainty.

### Consequences

- The canonical model is `data/chip-dependency-model.json`.
- Model vocabulary and references must pass
  `scripts/validate_chip_dependency_model.py`.
- A diagnostic response is an input to investigation, not an operational
  finding.
- `insufficient` confidence produces no operational finding.
- Any future interface must remain a model preview until evidence-backed
  assessment workflows are governed and implemented.

## ADR-005: Accept the Sprint 2A Model Coherence Audit

- **Date:** 2026-06-14
- **Status:** Accepted

### Decision

The Chip Dependency Map foundation passes the Sprint 2A Model Coherence Audit
after limited governance and wording improvements.

The governing principle is reaffirmed:

> The Chip Dependency Map reveals layered exposure. It does not assign
> sovereignty.

Diagnostic questions must request or test evidence rather than invite
unsupported self-assessment. Artifact output hints classify the appropriate
next governed analysis format; they are not purchase, investment, deployment,
or operational recommendations.

### Rationale

The model covers all eight layers proportionately, uses all six exposure types
coherently, preserves evidence-based confidence, and keeps every output bounded.
Machine-readable artifact boundaries reduce the risk that future interfaces
overstate what an output represents.

### Consequences

- The audit verdict and deferred risks are recorded in
  `MODEL_COHERENCE_AUDIT.md`.
- The canonical model must define complete boundaries for all artifact outputs.
- No automatic mapping from responses to findings, confidence, or judgments is
  authorized.
- Sprint 2A authorizes no score, ranking, operational assessment, or production
  interface.
