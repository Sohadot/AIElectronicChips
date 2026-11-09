# AIElectronicChips

**AI chips are the physical substrate of compute sovereignty.**

AIElectronicChips.com is being developed as a governed reference and
intelligence asset for **AI Chip Sovereignty Intelligence**. It maps the
physical, commercial, infrastructural, and policy dependencies that determine
who can operate AI compute.

It is not a chip news site, GPU review publication, affiliate catalog, or
high-volume AI blog.

## Current Phase

**Sprint 9: Chip Dependency Map Engine v1 — Live at [aielectronicchips.com](https://aielectronicchips.com/)**

The repository now includes the governed, machine-readable foundation for the
future Chip Dependency Map. It defines the protocol, controlled vocabularies,
dependency record schema, diagnostic questions, and automated validation. It
does not implement a score, ranking, chatbot, API, or operational assessment.
The foundation has passed a coherence audit covering layer balance, exposure
types, confidence, diagnostic wording, artifact boundaries, and model safety.
Sprint 3 adds a formal interpretation standard for reading layered dependency
exposure without reducing it to a score, ranking, benchmark, or maturity grade.
Sprint 3A adds the first governed source registry and evidence seed. Registry
presence makes a source discoverable; it does not automatically create a
finding or approve every statement in the source.
Sprint 3B links selected public reference pages to relevant registry IDs while
preserving source scope, freshness, limitations, and the boundary between
registered evidence and findings.
Sprint 3C strengthens the HBM evidence layer with bounded official technical
disclosures while preserving the prohibition on availability, capacity,
supplier-position, and ranking conclusions.
Sprint 4 turns `strategic-availability/` into a serious commercial pathway for
premium briefs, scoped audits, reference dossiers, ontology licensing, and
strategic acquisition inquiry. It adds a governed offerings model and protocol
boundary without prices, checkout, scores, rankings, certifications, or
guarantees.
Sprint 4A adds the Strategic Availability Trust Gate, a commercial trust audit,
and `validate_all.py` to enforce validator and prohibited-language checks before
any commercial surface is accepted.
Sprint 5 prepares the public site for launch, crawling, and indexing with a
launch checklist, indexation audit, `CNAME`, and `validate_public_launch.py`.
Sprint 6 expands the source registry, publishes the Claim Boundary Matrix,
stabilizes Compute Sovereignty Ontology v1, and upgrades all thirteen public
routes into a reference-grade foundation without content sprawl.
Sprint 7 establishes Compute Sovereignty Standard v1 as the responsible
interpretation standard for the eight-layer ontology, with evidence posture
levels and a dedicated validator. No score, ranking, or route expansion is
introduced.
Sprint 8 establishes Chip Dependency Map Model v1 as a non-numeric dependency
mapping model across the eight ontology layers under the standard and claim
boundary matrix. Five descriptive dependency states replace any scoring impulse.
Named entities remain governed and non-anchoring. No company pages, country
assessments, product comparisons, monetization, pilot, or route expansion is
introduced.
Sprint 9 ships Chip Dependency Map Engine v1 (ADR-017): `/chip-dependency-map/`
becomes a working, fully static, client-side diagnostic instead of a model
preview. It reads a visitor's own answers to the twelve governed questions
and returns touched layers, raised exposure types, a confidence label capped
at Medium, and a candidate next governed artifact format — never a score,
ranking, or entity-specific finding. Nothing is collected, transmitted, or
stored. This is the first and only page on the site permitted to load local
JavaScript.

## Portfolio Registration

This asset is registered as a **Tier 1 — Sovereign Build Candidate** in the
[Sovereign Asset System](https://github.com/Sohadot/sovereign-asset-system)
portfolio. See
[`portfolio/asset-dossiers/aielectronicchips.com/ASSET_INTELLIGENCE_FACTORY_PLAN.md`](https://github.com/Sohadot/sovereign-asset-system/blob/main/portfolio/asset-dossiers/aielectronicchips.com/ASSET_INTELLIGENCE_FACTORY_PLAN.md)
for the portfolio-level factory plan, gap tracking, and execution sequence
(ADR-016).

## Foundation Documents

- [Category Thesis](CATEGORY_THESIS.md)
- [Compute Sovereignty Ontology v1](COMPUTE_SOVEREIGNTY_ONTOLOGY.md)
- [Claim Boundary Matrix](CLAIM_BOUNDARY_MATRIX.md)
- [Source Policy](SOURCE_POLICY.md)
- [Claim Policy](CLAIM_POLICY.md)
- [Interface Thesis](INTERFACE_THESIS.md)
- [Buyer Logic](BUYER_LOGIC.md)
- [Asset Intelligence Factory Plan](ASSET_INTELLIGENCE_FACTORY_PLAN.md)
- [Monetization Boundary](MONETIZATION_BOUNDARY.md)
- [Decision Log](DECISION_LOG.md)

## Chip Dependency Map Foundation

- [Governed model](data/chip-dependency-model.json)
- [Chip Dependency Map Protocol](CHIP_DEPENDENCY_MAP_PROTOCOL.md)
- [Dependency Record Schema](DEPENDENCY_RECORD_SCHEMA.md)
- [Model validation script](scripts/validate_chip_dependency_model.py)
- [Model Coherence Audit](MODEL_COHERENCE_AUDIT.md)
- [Compute Sovereignty Standard v1](COMPUTE_SOVEREIGNTY_STANDARD.md) — Defines responsible interpretation rules for the eight-layer compute sovereignty ontology.
- [Chip Dependency Map Model v1](CHIP_DEPENDENCY_MAP_MODEL.md) — Defines non-numeric dependency states and named-entity governance for mapping relationships across the eight ontology layers.
- [Chip Dependency Map Engine v1](CHIP_DEPENDENCY_MAP_ENGINE_SPEC.md) — Specifies the deterministic, client-side, self-service engine live at [`/chip-dependency-map/`](chip-dependency-map/index.html).

## Dependency Evidence Atlas (governed scaffold)

The [Dependency Evidence Atlas](DEPENDENCY_EVIDENCE_ATLAS.md) defines a source-linked, machine-readable structure separate from the self-reported diagnostic engine. The initial [Atlas JSON](data/dependency-atlas.json) contains the eight ontology-layer nodes and no reviewed operational relationships. Every future relationship must cite active entries in the existing [Source Registry](data/source-registry.json), declare scope, dates, review ownership and limitations, and pass [the dedicated validator](scripts/validate_dependency_atlas.py). Unreviewed relationships cannot be published through the governed gate.

All repository gates run in `scripts/validate_all.py`; the GitHub Actions workflow also checks the public site and negative-test suite. **GitHub Pages must be set to deploy from GitHub Actions rather than directly from the main branch**, and the validation status must be required before merging, for the gate to prevent publication.

## Evidence Releases

Research-candidate evidence lives in [`data/research/`](data/research/) and is validated by [`scripts/validate_evidence_releases.py`](scripts/validate_evidence_releases.py). Releases hold classified findings (verified fact, attributed statement, bounded analysis), explicit unresolved questions, and candidate Atlas relationships that are **not published** until a named human reviewer moves them into the Atlas.

- [HBM4 Evidence Release 001](HBM4_EVIDENCE_RELEASE_001.md): HBM3E/HBM4/HBM4E, base-die and packaging dependencies, and supplier-reported status, behind the [`/hbm-memory/`](hbm-memory/index.html) reference.

## Source Registry

- [Governed source registry](data/source-registry.json)
- [Source Registry Protocol](SOURCE_REGISTRY_PROTOCOL.md)
- [Source registry validation script](scripts/validate_source_registry.py)
- [Public source registry reference](sources/index.html)

Validate the registry with:

```powershell
py scripts/validate_source_registry.py
```

Validate the model with:

```powershell
python scripts/validate_chip_dependency_model.py
```

Validate the standard with:

```powershell
py scripts/validate_compute_sovereignty_standard.py
```

## Strategic Availability

- [Governed offerings model](data/strategic-offerings.json)
- [Strategic Availability Protocol](STRATEGIC_AVAILABILITY_PROTOCOL.md)
- [Premium Brief Boundary](PREMIUM_BRIEF_BOUNDARY.md)
- [Strategic Availability Trust Gate](STRATEGIC_AVAILABILITY_TRUST_GATE.md)
- [Commercial Trust Audit](COMMERCIAL_TRUST_AUDIT.md)
- [Strategic availability reference](strategic-availability/index.html)

Validate the offerings model with:

```powershell
py scripts/validate_strategic_offerings.py
```

Run all validators and the commercial trust-language scan with:

```powershell
py scripts/validate_all.py
```

## Public Launch Readiness

- [Public launch checklist](PUBLIC_LAUNCH_READINESS_CHECKLIST.md)
- [Indexation hardening audit](INDEXATION_HARDENING_AUDIT.md)
- [Sitemap](sitemap.xml)
- [Robots](robots.txt)
- [Custom domain CNAME](CNAME)

Validate launch readiness with:

```powershell
py scripts/validate_public_launch.py
```

## Development Roadmap

1. **Sprint 0 — Compute Sovereignty Foundation:** governance and category definition.
2. **Sprint 1 — Public Reference Surface:** a focused 10–12 page reference experience.
3. **Sprint 2 — Chip Dependency Map:** a governed, rule-based diagnostic tool.
4. **Sprint 3 — Compute Sovereignty Standard:** formalized methodology and protocol.
5. **Sprint 4 — Premium Brief / Strategic Availability Layer:** briefs, audits, licensing, and strategic pathways.

## Public Reference Surface

The planned first release covers:

- compute sovereignty;
- AI chip infrastructure;
- design, fabrication, and packaging;
- HBM memory and interconnects;
- power and thermal limits;
- the export-control layer;
- the Chip Dependency Map;
- methodology, sources, and strategic availability.

## Research Standard

Material claims must be sourced, dated, bounded, and labeled by confidence.
Primary evidence is preferred. Uncertainty is disclosed, and insufficient
evidence results in no finding.
