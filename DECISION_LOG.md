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

## ADR-006: Establish the Compute Sovereignty Standard

- **Date:** 2026-06-14
- **Status:** Accepted

### Decision

AEC-CS-001 is established as the foundation Compute Sovereignty Standard.

> Compute sovereignty is interpreted through layered dependency exposure, not
> reduced to a single score.

The standard governs how dependency records, exposure types, evidence,
confidence, changing conditions, and bounded artifacts are interpreted. It does
not assign sovereignty or non-sovereignty and does not create a score, ranking,
benchmark, or maturity grade.

### Rationale

The ontology and diagnostic model define what is mapped. A separate
interpretation standard defines how supported findings may be read,
synthesized, issued, limited, and reviewed without overstating the evidence.

### Consequences

- Conforming artifacts must follow `COMPUTE_SOVEREIGNTY_STANDARD.md`.
- Confidence reflects evidence quality and completeness, not rhetorical
  certainty or favorable capability.
- `insufficient` evidence produces no operational finding.
- Changing policy, capacity, ownership, access, and operating conditions
  require dated findings and review before reuse.
- No sovereignty score, assignment, ranking, benchmark, or maturity grade is
  authorized.

## ADR-007: Establish the Governed Source Registry

- **Date:** 2026-06-14
- **Status:** Accepted

### Decision

The project will maintain a governed source registry containing attributable,
dated, scoped, and limited source metadata for future reference pages,
dependency records, briefs, and audits.

Registration does not create a finding, approve every statement in a source,
or authorize an interpretation. Source use remains claim-specific and governed
by `SOURCE_POLICY.md`, `CLAIM_POLICY.md`, and
`COMPUTE_SOVEREIGNTY_STANDARD.md`.

### Rationale

The ontology, dependency model, and interpretation standard require a
traceable evidence layer. A controlled registry allows source identity,
freshness, scope, limitations, and review status to be inspected before a
source is used.

### Consequences

- The canonical registry is `data/source-registry.json`.
- Registry structure and controlled values must pass
  `scripts/validate_source_registry.py`.
- Sources use `active`, `pending_review`, or `retired` status.
- Confidence belongs to a supported finding after review; it is not inherited
  from publisher identity or registry status.
- No registered source automatically creates a finding, score, ranking,
  recommendation, or sovereignty assignment.

## ADR-008: Link Public Reference Pages to Registry Evidence Posture

- **Date:** 2026-06-14
- **Status:** Accepted

### Decision

Selected public reference pages will disclose a compact evidence posture using
related source registry IDs, supported uses, prohibited inferences, freshness,
and confidence boundaries.

A registry link identifies potentially relevant evidence for governed review.
It is not a citation-backed finding and does not inherit confidence from source
status or publisher identity.

### Rationale

Visible evidence posture makes the public reference surface inspectable without
overloading it with unsupported claims or turning the source registry into a
conclusions database.

### Consequences

- Evidence posture sections must use only existing registry IDs.
- `pending_review` status must remain visible where linked.
- Reference pages must state what linked records can and cannot support.
- Every page-level source posture must link to `/sources/`.
- Source links do not authorize findings, rankings, recommendations, or
  sovereignty assignments.
