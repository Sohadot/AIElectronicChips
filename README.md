# AIElectronicChips

**AI chips are the physical substrate of compute sovereignty.**

AIElectronicChips.com is being developed as a governed reference and
intelligence asset for **AI Chip Sovereignty Intelligence**. It maps the
physical, commercial, infrastructural, and policy dependencies that determine
who can operate AI compute.

It is not a chip news site, GPU review publication, affiliate catalog, or
high-volume AI blog.

## Current Phase

**Sprint 7: Compute Sovereignty Standard v1**

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
