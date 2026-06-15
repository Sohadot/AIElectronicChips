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

## ADR-009: Patch the HBM Evidence Gap with Official Technical Disclosures

- **Date:** 2026-06-14
- **Status:** Accepted

### Decision

The HBM evidence layer will add three attributable official technical
disclosures covering product-level HBM integration, bandwidth context,
stacking, and packaging.

`official_technical_disclosure` is added as an approved source type because
these primary company materials are neither filings nor technical standards.
They remain attributed and cannot establish market-wide conditions.

### Rationale

The initial HBM posture contained only a controls-related record. Technical
framing requires primary evidence about how HBM relates to memory bandwidth,
accelerator integration, and advanced packaging without inferring supply or
availability.

### Consequences

- HBM technical disclosures may support bounded and attributed technical
  framing.
- They must not support availability, allocation, production-capacity, future
  supply, supplier-position, ranking, or entity-level access findings.
- Product specifications and company announcements are not independent
  verification.
- The HBM page must continue to disclose evidence limits and freshness.

## ADR-010: Strategic Availability and Premium Brief Layer

- **Date:** 2026-06-14
- **Status:** Accepted

### Decision

Sprint 4 will define five governed strategic offerings in
`data/strategic-offerings.json` and publish the Strategic Availability Protocol
and Premium Brief Boundary.

The public `strategic-availability/` page will present serious pathways only:
briefs, audits, dossiers, licensing, and strategic acquisition inquiry. Inquiry
will use qualified contact, not checkout or public pricing.

### Rationale

The asset now has thesis, ontology, reference surface, dependency model,
standard, source registry, and evidence-linked pages. The next durable step is
a bounded commercial layer that can generate respectful revenue without
weakening trust, neutrality, or acquisition value.

### Consequences

- Five offering IDs are machine-readable and validator-governed.
- No prices, checkout flow, score, ranking, benchmark, certification, or
  guarantee may appear on the public strategic availability surface.
- Paid work follows the same source and claim standards as public reference
  material.
- Clients may define questions but may not purchase predetermined conclusions.
- Strategic acquisition interest must not alter public findings or source
  posture.

## ADR-011: Strategic Availability Trust Gate

- **Date:** 2026-06-14
- **Status:** Accepted

### Decision

Sprint 4A will add `STRATEGIC_AVAILABILITY_TRUST_GATE.md`,
`COMMERCIAL_TRUST_AUDIT.md`, and `scripts/validate_all.py`.

The commercial layer is accepted only when validators pass and risky commercial
or scoring language appears solely in prohibition or boundary contexts.

### Rationale

Sprint 4 introduced the first revenue pathway. Before quiet launch, the asset
requires an explicit trust gate to ensure the commercial surface does not weaken
neutrality, buyer logic, or strategic acquisition value.

### Consequences

- `validate_all.py` becomes the pre-release check for model, registry, offerings,
  and commercial trust language.
- The Sprint 4 implementation is audited as PASS in `COMMERCIAL_TRUST_AUDIT.md`.
- HTML and JSON offering copy must remain manually aligned until a later
  automation sprint.
- CI integration for `validate_all.py` remains deferred.

## ADR-012: Public Launch Readiness and Indexation Hardening

- **Date:** 2026-06-14
- **Status:** Accepted

### Decision

Sprint 5 will add `PUBLIC_LAUNCH_READINESS_CHECKLIST.md`,
`INDEXATION_HARDENING_AUDIT.md`, `scripts/validate_public_launch.py`, and
`CNAME` for custom-domain readiness.

The sprint hardens sitemap, robots, canonical, metadata, internal links,
accessibility basics, and dependency safety without adding new products or
content expansion.

### Rationale

After governance, reference surface, evidence linkage, and strategic availability
trust gating, the asset needs a launch-readiness layer before quiet public
discovery and indexing.

### Consequences

- `validate_public_launch.py` becomes the pre-launch structural gate.
- All 13 public routes must remain aligned across HTML files and `sitemap.xml`.
- GitHub Pages and DNS setup remain manual post-sprint steps.
- CI integration for launch validators remains deferred.

## ADR-013: Reference Authority Foundation

- **Date:** 2026-06-14
- **Status:** Accepted

### Decision

Sprint 6 will expand the source registry with primary and official sources,
publish `CLAIM_BOUNDARY_MATRIX.md`, stabilize `COMPUTE_SOVEREIGNTY_ONTOLOGY.md`
as v1, and upgrade all thirteen public routes with reference summaries,
ontology mapping, and clearer evidence boundaries.

No new public routes, scores, rankings, or content sprawl are authorized.

### Rationale

After public launch readiness, the asset must move from technical readiness to
reference authority. Sensitive claims require governed sources and explicit
claim boundaries before category-scale expansion.

### Consequences

- The source registry grows to twenty records with government, filing, and
  institutional coverage across ontology layers.
- Every public route gains a reference summary and clearer boundary language.
- Interconnect and deployment pages gain registry-linked evidence posture.
- Claim and ontology documents become first-class foundation references in
  `README.md`.

## ADR-014: Establish Compute Sovereignty Standard v1

- **Date:** 2026-06-14
- **Status:** Accepted

### Decision

Sprint 7 will publish `COMPUTE_SOVEREIGNTY_STANDARD.md` as version 1.0.0 after
ontology v1 and the Claim Boundary Matrix.

The standard defines responsible interpretation rules, four non-numeric evidence
posture levels, and eight standard dimensions. It does not assign sovereign
status to any entity.

### Rationale

No score before standard. No standard before ontology. No claim before boundary.
The asset requires an explicit reading standard to prevent rankings, opinions,
and overclaiming before any stronger tool or dependency map is built.

### Consequences

- `scripts/validate_compute_sovereignty_standard.py` is added and wired into
  `validate_all.py`.
- Public pages receive light standard references only; no new routes or content
  sprawl.
- No Chip Sovereignty Score, country ranking, company ranking, or product
  comparison is authorized.
- Any future tool or diagnostic output must conform to AEC-CS-001 v1.0.0.

## ADR-015: Establish Chip Dependency Map Model v1

- **Date:** 2026-06-14
- **Status:** Accepted

### Decision

Sprint 8 will publish `CHIP_DEPENDENCY_MAP_MODEL.md` as version 1.0.0 after
ontology v1, the Claim Boundary Matrix, and Compute Sovereignty Standard v1.

The model defines five non-numeric dependency states mapped across all eight
ontology layers, evidence posture inheritance, and named-entity governance. It
does not score sovereignty or assign sovereign status to any entity.

### Rationale

Map dependencies before scoring sovereignty. The asset requires an explicit
dependency mapping model before any stronger diagnostic tool, exposure map, or
score-like output is considered. Named entities may appear as bounded references
inside the framework; they must never define the framework.

### Consequences

- `scripts/validate_chip_dependency_model.py` validates both the JSON foundation
  and the v1 model document; it remains wired into `validate_all.py`.
- Public pages receive light dependency-map model references only; no new routes
  or content sprawl.
- No Chip Sovereignty Score, country ranking, company ranking, product comparison,
  company-led pages, or market-news framing is authorized.
- Any future tool, exposure map, audit, or brief output must conform to
  AEC-CDM-001 v1.0.0 and AEC-CS-001 v1.0.0.
