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

## ADR-016: Register in the Sovereign Asset System Portfolio as Tier 1

- **Date:** 2026-07-03
- **Status:** Accepted

### Decision

AIElectronicChips.com is registered as a **Tier 1 — Sovereign Build
Candidate** in the `Sohadot/sovereign-asset-system` portfolio, via
`portfolio/asset-dossiers/aielectronicchips.com/ASSET_INTELLIGENCE_FACTORY_PLAN.md`
in that repository. The dossier is a portfolio-level cross-reference and gap
tracker; it does not supersede this repository's own governance documents,
which remain the authoritative source for ontology, standard, model, and
claim decisions.

### Rationale

Eight sprints of governed foundation work (category thesis, ontology,
standard, dependency map model, source registry, claim boundary matrix,
public reference surface, and interface thesis) satisfy Layers 1–5, 7, 8, and
11 of `docs/INTELLIGENCE_FACTORY_DOCTRINE.md` in the sovereign asset system.
The remaining gap to full Category Intelligence Factory grade is explicit:
Layer 6 (Engine) is specified (`CHIP_DEPENDENCY_MAP_MODEL.md`,
`DEPENDENCY_RECORD_SCHEMA.md`) but not yet operational, and distribution
(GitHub Pages, DNS) is prepared (`CNAME`, `PUBLIC_LAUNCH_READINESS_CHECKLIST.md`)
but not yet switched on. Formal portfolio registration makes this gap
trackable at the portfolio level rather than only inside this repository.

### Consequences

- The portfolio dossier's Execution Sequence supersedes no existing
  document here; it orders the same remaining work already implied by the
  README roadmap (engine, launch, respectable income activation, interface
  governance review, adoption monitoring).
- Future sprints that build the Chip Dependency Map engine or activate
  distribution should reference ADR-016 and update the portfolio dossier's
  status alongside this log.
- No new public routes, scores, rankings, or content sprawl are authorized
  by this entry.

## ADR-017: Ship Chip Dependency Map Engine v1 and Authorize Local JavaScript on One Page

- **Date:** 2026-07-03
- **Status:** Accepted

### Decision

`/chip-dependency-map/` becomes a working engine, not a model preview. It
implements `CHIP_DEPENDENCY_MAP_ENGINE_SPEC.md` (AEC-CDM-ENGINE-001 v1.0.0):
a fully static, client-side, deterministic tool that takes a visitor's own
answers to the twelve governed diagnostic questions in
`data/chip-dependency-model.json` and returns touched layers, raised exposure
types, a capped confidence label (Medium is the ceiling; High is never
returned), and a candidate next governed artifact format. Nothing is
collected, transmitted, or stored. The tool never uses the five Dependency
States from `CHIP_DEPENDENCY_MAP_MODEL.md`, since those require attributed
evidence a self-service form cannot supply.

This requires local JavaScript (`assets/js/chip-dependency-map.js`), the
first script on this site. `scripts/validate_public_launch.py` previously
forbade `<script` tags on every page; it now permits local
`/assets/js/`-only script tags exclusively on `chip-dependency-map/index.html`
(`SCRIPT_ALLOWED_PAGES`), and continues to forbid external/CDN JavaScript
everywhere, unchanged. Every other public route remains script-free. The page
carries a `<noscript>` fallback; all reference content on the site remains
readable without JavaScript.

### Rationale

Per `docs/INTELLIGENCE_FACTORY_DOCTRINE.md` (sovereign-asset-system), Layer 6
(Engine) is what elevates a category artifact to a Category Intelligence
Factory: "a rules-based, fully static, client-side diagnostic... is a valid
engine." Sprint 8 correctly built the model before any tool; ADR-016 recorded
this as the asset's largest remaining gap to factory grade. Shipping it
requires evolving the zero-JavaScript launch gate precisely rather than
working around it silently — the gate is amended, not bypassed, and the
amendment is scoped to exactly one page and exactly one directory.

### Consequences

- `scripts/validate_public_launch.py` and `scripts/validate_all.py` both
  gained `CHIP_DEPENDENCY_MAP_ENGINE_SPEC.md` as a recognized governance file
  for the risky-language scan.
- `PUBLIC_LAUNCH_READINESS_CHECKLIST.md`'s performance checklist is updated to
  describe local, page-scoped JavaScript instead of claiming zero JavaScript
  site-wide.
- No dependency record, score, ranking, or entity-specific output is
  authorized by this entry. Paid brief and audit production still requires
  the governed, evidence-reviewed pipeline in `ASSET_INTELLIGENCE_FACTORY_PLAN.md`.
- Future engine changes require a `DECISION_LOG.md` entry, matching
  governance for every other model change in this repository.

## ADR-018: Add the Qualified Inquiry Builder to Strategic Availability

- **Date:** 2026-07-03
- **Status:** Accepted

### Decision

`/strategic-availability/` gains a Qualified Inquiry Builder: a client-side
form that reads the five governed pathways from
`data/strategic-offerings.json`, collects the structured fields the page
already requires of a serious inquiry (pathway, entity or topic, decision
context, time horizon, sovereignty layers, geographic scope, constraints),
and composes a structured email that opens in the visitor's own mail client.
Nothing entered is transmitted, stored, or logged by this site; the only
same-origin request is fetching the public offerings file. The plain mailto
pathway remains as the no-JavaScript fallback.

`strategic-availability/index.html` is added to `SCRIPT_ALLOWED_PAGES` in
`scripts/validate_public_launch.py`, becoming the second and only other page
authorized to load local `/assets/js/` JavaScript under the rule established
in ADR-017. External and CDN scripts remain forbidden everywhere.

### Rationale

`MONETIZATION_BOUNDARY.md` permits paid briefs, audits, dossiers, and
licensing but forbids checkout, price lists, and predetermined conclusions.
The gap between a bare mailto button and a real commercial pathway is intake
quality: the inquiry page itself states that useful inquiries name seven
structured elements and that vague contacts may be declined. The builder
operationalizes that stated standard without adding a server, a price, or a
purchase flow, and it embeds the no-predetermined-conclusions acknowledgment
directly in the composed email.

### Consequences

- Respectable income intake (briefs, audits, dossiers, licensing,
  acquisition dialogue) now has a structured, self-qualifying entry channel
  consistent with the Strategic Availability Trust Gate.
- The composed email carries an explicit acknowledgment that no score,
  ranking, certification, guarantee, or predetermined conclusion can be
  purchased.
- No checkout, pricing, payment processing, analytics, or data collection is
  authorized by this entry.
- Changes to the builder's fields or composed-email wording follow the same
  decision-log discipline as other governed surfaces.


## ADR-019: Encode the Ontology as Structured Data and Establish the og:image Visual System

- **Date:** 2026-07-03
- **Status:** Accepted

### Decision

Every public page now carries exactly one JSON-LD `@graph` and a governed
og:image, and `sitemap.xml` carries `<lastmod>` dates. Three connected moves:

1. **The ontology becomes machine-readable vocabulary.** The Compute
   Sovereignty Ontology is published as a schema.org `DefinedTermSet`
   (`/sovereignty-stack/#ontology`) with eight `DefinedTerm` entries whose
   stable `@id`s anchor to their reference routes. Each layer page declares
   its own term(s); `/compute-sovereignty/` defines the category term. The
   Chip Dependency Map engine is declared as a free `WebApplication`, the
   Compute Sovereignty Standard as a versioned `CreativeWork`, and the source
   registry as a `Dataset` with a JSON distribution. The asset is thereby the
   definitional source of its category for machine readers, per the agent
   legibility requirement in the Intelligence Factory doctrine.
2. **A governed og:image system.** Thirteen 1200×630 images generated by
   `scripts/generate-og-images.mjs` from the Interface Thesis visual
   language (black substrate, micro-grid, copper wafer cross-section,
   reserved blue rule, monospace layer identifiers). Layer pages carry their
   ontology position (01–08). Regeneration goes through the script; images
   are never hand-edited.
3. **Validator upgrade, not bypass.** `scripts/validate_public_launch.py`
   now requires exactly one parsing JSON-LD graph per page, requires
   og:image to exist locally under `/assets/og/` with declared 1200×630
   dimensions, and continues to forbid executable scripts outside
   `SCRIPT_ALLOWED_PAGES` (`application/ld+json` blocks are data, not
   executable script). The external-JavaScript pattern was corrected to stop
   false-matching `.json` URLs.

### Rationale

The doctrine states that when agents answer category questions, the governed
source wins because agents weight consistency, structure, and provenance
mechanically. Publishing the ontology as `DefinedTermSet` is the strongest
available structural claim to category-language ownership: any machine
reader that resolves the category resolves this asset's URLs and this
asset's definitions. The og:image system extends the interface thesis to
the asset's off-site surface — link previews are the first impression a
strategic buyer gets in email, chat, and social contexts.

### Consequences

- Structured data is now a validated launch requirement, not an optional
  enhancement; a page without a valid JSON-LD graph fails the launch gate.
- Ontology changes must be reflected in three places together: the ontology
  document, the sovereignty-stack page markup, and the JSON-LD terms —
  the validator enforces presence, and the decision log governs meaning.
- Home and sovereignty-stack meta descriptions were lengthened to carry the
  thesis and the eight-layer enumeration respectively.
- No tracking, analytics, external requests, or executable script scope is
  added by this entry.
  
## ADR-020: HBM4 Evidence Release 001 and Research-Candidate Evidence Releases

- **Date:** 2026-11-09
- **Status:** Proposed (awaiting owner and scientific review)

### Decision

1. **`/hbm-memory/` becomes the evidence-classified HBM reference.** It is not split into a separate HBM4 route. HBM4 is the substance of the memory layer, and a second page would duplicate it. Every material statement is tagged as Standard (S), Attributed (A), Bounded analysis (C) or Unresolved (U) and carries a numbered citation to a registry record.
2. **Evidence releases are a new, non-published data class.** Files in `data/research/*.json` hold classified findings, explicit unknowns and candidate Atlas relationships. They are validated by `scripts/validate_evidence_releases.py`, can never declare themselves published, and are kept out of `data/dependency-atlas.json` until a named human reviewer moves each relationship across.
3. **`company_announcement` source type.** Earnings and status press releases are neither filings nor technical disclosures. The registry accepts this narrow, backward-compatible type, and the Atlas gate treats it as self-reported, so it can never alone establish a `verified_fact`.
4. **The registry and its public index stay in lockstep.** `validate_source_registry.py` now fails if `/sources/` omits a registry ID, lists an unregistered one, or mismarks pending status.
5. **Undated pages are not registered.** NVIDIA's Vera Rubin NVL72 page is cited only to document a bandwidth conflict.

### Rationale

The asset's value is the separation of what a standard establishes, what a company says, what can be derived, and what is unknown. HBM4 is a good proving case because supplier disclosures move fast and compete. The base-die shift to logic processes is also a genuine dependency change that a generic summary would miss.

### Consequences

- The Atlas remains `foundation` with zero published relationships. Four candidates await review.
- JEDEC's JESD270-4 announcement is registered as an announcement, not a standard, and stays `pending_review` because its text could not be retrieved. Figures from it are marked as announcement content. The normative standard has not been reviewed.
- Unpublished research candidates are excluded from the Pages artifact, and the validator enforces the exclusion. The public repository still exposes them as labelled research files.
- AEC-CS-001 is unchanged. No supplier capacity, availability or position conclusion is introduced.
