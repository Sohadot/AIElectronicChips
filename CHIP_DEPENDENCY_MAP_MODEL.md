# Chip Dependency Map Model v1.0.0

- **Model ID:** AEC-CDM-001
- **Version:** 1.0.0
- **Status:** Active dependency mapping model
- **Thesis:** AI chips are the physical substrate of compute sovereignty.
- **Governing rule:** Map dependencies before scoring sovereignty.

## Purpose

This model defines how dependency relationships may be mapped across the eight
layers of the Compute Sovereignty Ontology under the Compute Sovereignty
Standard and the Claim Boundary Matrix.

**Ontology** answers: what are the layers?
**Standard** answers: how may those layers be discussed without overclaiming?
**Dependency Map Model** answers: how may dependency relationships be identified
and read across those layers without scoring sovereignty?

The dependency map does not score sovereignty. It identifies dependency
relationships across compute infrastructure layers using documented evidence and
bounded interpretation.

## What the Model Does

- maps dependency relationships across all eight ontology layers;
- uses five non-numeric dependency states to describe relationship posture;
- inherits evidence posture discipline from the Compute Sovereignty Standard;
- requires scope, attribution, `as_of` dating, and explicit unknowns;
- connects dependency records to governed sources through the source registry;
- preserves layered exposure without collapsing layers into a single label;
- constrains any future diagnostic tool, exposure map, audit, or brief output;
- governs how named entities may appear as bounded references, not as anchors.

## What the Model Does Not Do

The model does **not**:

- score sovereignty, independence, resilience, or national strength;
- produce rankings, benchmarks, maturity grades, league tables, or winners;
- assign sovereign or non-sovereign status to any company, country, product, or
  institution;
- certify readiness, compliance, performance, availability, or substitution;
- provide investment, legal, procurement, deployment, or policy advice;
- compare products, vendors, countries, or chips as superior or inferior;
- create company-led site structure, country assessments, or product comparisons;
- replace the ontology, standard, claim boundary matrix, or primary evidence review;
- publish market-news framing, case studies, or entity-specific dependency maps in
  Sprint 8.

## Relationship to the Compute Sovereignty Ontology

`COMPUTE_SOVEREIGNTY_ONTOLOGY.md` defines the eight dependency layers and
cross-layer surfaces. This model maps how dependency relationships are expressed
within and across those layers.

Every dependency record MUST:

- name one or more ontology layers: Design, Fabrication, Packaging, Memory,
  Interconnect, Power / Thermal, Export-Control, or Deployment;
- treat each layer as a distinct dependency surface;
- avoid inferring control at one layer from evidence at another;
- preserve cross-layer linkage without collapsing the stack into one verdict.

## Relationship to the Compute Sovereignty Standard

`COMPUTE_SOVEREIGNTY_STANDARD.md` governs responsible layer interpretation.
This model applies that discipline to dependency relationship mapping.

A conforming dependency map MUST:

- use the standard's evidence posture levels where layer discussion is required;
- respect responsible interpretation rules and prohibited uses from AEC-CS-001;
- treat `insufficient` or `Not Assessable` evidence as a boundary, not a weakness
  signal;
- avoid language that converts exposure description into sovereignty assignment.

## Relationship to the Claim Boundary Matrix

`CLAIM_BOUNDARY_MATRIX.md` governs what claims may be stated and how they must
be supported. This model governs how dependency relationships may be described
once claim classes are applied.

A conforming map MUST:

- respect permitted, source-required, and confidence-qualified claim categories;
- treat prohibited claims as non-publishable;
- attach limitations, conflicts, and unknowns to every supported dependency
  relationship;
- not use dependency state labels as substitutes for permitted claim language.

## Dependency Types

Dependency states describe relationship posture. They are **not** scores,
grades, rankings, or performance ratings. They are descriptive dependency states
used to map relationships responsibly.

Each dependency state applies across all eight ontology layers:

| Layer | Applicable states |
| --- | --- |
| Design | Direct, Layered, Constrained, Opaque, Not Assessable |
| Fabrication | Direct, Layered, Constrained, Opaque, Not Assessable |
| Packaging | Direct, Layered, Constrained, Opaque, Not Assessable |
| Memory | Direct, Layered, Constrained, Opaque, Not Assessable |
| Interconnect | Direct, Layered, Constrained, Opaque, Not Assessable |
| Power / Thermal | Direct, Layered, Constrained, Opaque, Not Assessable |
| Export-Control | Direct, Layered, Constrained, Opaque, Not Assessable |
| Deployment | Direct, Layered, Constrained, Opaque, Not Assessable |

### Direct Dependency

**Definition:** A dependency relationship is directly supported by attributed
evidence linking a declared scope to a specific layer, capability, access path,
or constraint within that layer.

**Layer coverage:** Design, Fabrication, Packaging, Memory, Interconnect, Power /
Thermal, Export-Control, Deployment.

**When to use:** Official disclosures, filings, primary technical material, or
governed registry sources explicitly describe the relationship within scope.

**Evidence required:** Source-backed attribution with scope, `as_of` date, and
stated limitations.

**Claim boundary:** May support attributed dependency framing. Must not support
sovereignty assignment, ranking, or substitution guarantees.

**Misinterpretation risk:** Treating a single disclosed relationship as full-layer
control or stack-wide independence.

### Layered Dependency

**Definition:** A dependency relationship is supported through multiple linked
layers, where evidence at one layer implies exposure or access conditions at
adjacent layers without proving control at every layer.

**Layer coverage:** Design, Fabrication, Packaging, Memory, Interconnect, Power /
Thermal, Export-Control, Deployment.

**When to use:** Evidence shows cross-layer linkage—such as design rights
constrained by fabrication access, memory qualification tied to packaging, or
deployment limits shaped by export-control scope.

**Evidence required:** Layer-specific attribution for each supported link;
unknown adjacent layers must remain visible.

**Claim boundary:** May describe linked exposure across named layers. Must not
collapse linked exposure into a sovereignty verdict or vendor ranking.

**Misinterpretation risk:** Inferring full-stack capability from a supported link
at only one or two layers.

### Constrained Dependency

**Definition:** A dependency relationship is material and partially documented,
but access, substitution, timing, jurisdiction, licensing, or operating
conditions limit how the relationship can be read.

**Layer coverage:** Design, Fabrication, Packaging, Memory, Interconnect, Power /
Thermal, Export-Control, Deployment.

**When to use:** Evidence exists, but scope, policy, capacity, qualification, or
operational conditions materially narrow interpretation.

**Evidence required:** Documented constraints with source attribution; explicit
statement of what remains unknown or time-bound.

**Claim boundary:** May describe bounded constraint within scope. Must not
support market-wide conclusions, performance claims, or readiness guarantees.

**Misinterpretation risk:** Treating a named constraint as proof of total
dependency failure or total external control.

### Opaque Dependency

**Definition:** A dependency relationship is material to the declared scope, but
public governed evidence is too limited, indirect, or fragmented to support a
more specific state.

**Layer coverage:** Design, Fabrication, Packaging, Memory, Interconnect, Power /
Thermal, Export-Control, Deployment.

**When to use:** The layer matters, but available sources do not support Direct,
Layered, or Constrained classification without overclaiming.

**Evidence required:** Statement of why opacity exists, what was searched, and
which source gaps remain.

**Claim boundary:** May state that dependency posture is opaque within scope.
Must not invent detail, infer secret conditions, or treat opacity as weakness
proof.

**Misinterpretation risk:** Filling opacity with assumption, rumor, or
market-narrative substitution.

### Not Assessable

**Definition:** Available evidence does not support a responsible dependency
relationship reading for the declared scope and layer within governed public
reference conditions.

**Layer coverage:** Design, Fabrication, Packaging, Memory, Interconnect, Power /
Thermal, Export-Control, Deployment.

**When to use:** Evidence is absent, out of scope, stale without update, or
conflicted beyond responsible resolution.

**Evidence required:** Explicit non-assessment statement with scope, review date,
and reassessment trigger where applicable.

**Claim boundary:** Must not produce an operational finding. May record that the
layer is not assessable under current evidence posture.

**Misinterpretation risk:** Treating not assessable as confirmation of hidden
dependency, hidden strength, or strategic vulnerability.

## Evidence Posture Inheritance

Dependency mapping inherits the four non-numeric evidence posture levels from the
Compute Sovereignty Standard:

| Posture | Effect on dependency mapping |
| --- | --- |
| **Documented** | One or more layers may support Direct or Layered states when scope and attribution are clear. |
| **Partially Documented** | Constrained or Layered states are likely; unknown sub-elements must remain explicit. |
| **Source-Constrained** | Opaque Dependency is likely for material layers until stronger scoped evidence is added. |
| **Not Assessable** | Not Assessable dependency state is required; no operational finding may be stated. |

Evidence posture guides caution in dependency language. It does not measure
national strength, vendor quality, product superiority, or sovereignty.

## Named Entity Governance

Companies, countries, institutions, and regions may be referenced only as
documented entities inside the model, source registry, or bounded examples.
They must not become the conceptual anchor of the asset.

**AIElectronicChips.com may reference players, but it must not orbit them.**

Named entities may appear inside the framework. They must never define the
framework.

### Allowed named-entity use

- as a source-backed example within declared scope;
- as a regulatory, infrastructure, supply-chain, or deployment reference;
- as a documented entity connected to a specific ontology layer;
- as a source-registry record or evidence reference;
- as a bounded example with no ranking or sovereignty assignment.

### Prohibited named-entity use

- no company-led site structure;
- no country ranking;
- no company ranking;
- no product comparison;
- no "best AI chip" framing;
- no "most sovereign company" or "most sovereign country" framing;
- no SEO pages built around company names;
- no market-news framing;
- no investment recommendations;
- no winner/loser language;
- no dependency map for a specific company or country in Sprint 8.

Sprint 8 may mention named entities only if required for governance, source
posture, or bounded reference. It does not create company pages, country pages,
market pages, or case studies.

## Map Interpretation Rules

1. **Scope first:** every map reading requires declared subject type, purpose,
   geography where relevant, and time horizon.
2. **Layer explicit:** every dependency record names at least one ontology
   layer and uses governed layer vocabulary.
3. **State not score:** dependency states describe relationship posture; they do
   not rank entities or measure sovereignty.
4. **Evidence before finding:** a diagnostic response or state label is not
   itself a finding without attributed evidence.
5. **Unknowns visible:** unassessed layers, opaque relationships, and conflicts
   remain in the output.
6. **No cross-layer collapse:** control or exposure at one layer does not imply
   control at another.
7. **Posture inheritance:** evidence posture from the standard constrains how
   strongly a dependency state may be stated.
8. **Registry discipline:** material claims trace to governed sources with
   limitations and `as_of` dating.
9. **Artifact classification only:** suggested brief, audit, dossier, or
   readiness outputs classify the next governed format; they are not action
   recommendations.
10. **Reassessment required:** changing policy, capacity, licensing, or
    operating conditions trigger review; maps are time-bounded readings.

## Prohibited Uses

The Chip Dependency Map Model must not be used to:

- produce a Chip Sovereignty Score or any numeric sovereignty metric;
- generate public or private rankings of countries, companies, products, or
  technologies;
- publish company profiles, country assessments, or product comparison pages;
- frame market news, winner/loser narratives, or investment recommendations;
- treat dependency states as performance ratings or competitive grades;
- infer undisclosed conditions from opacity or non-assessment;
- anchor site structure, SEO strategy, or editorial calendar around named
  entities;
- bypass the Claim Boundary Matrix, Compute Sovereignty Standard, or source
  registry review.

## Versioning Notes

- **v1.0.0** establishes five non-numeric dependency states mapped across all
  eight ontology layers under AEC-CS-001 and the Claim Boundary Matrix.
- The machine-readable foundation in `data/chip-dependency-model.json` and the
  operational protocol in `CHIP_DEPENDENCY_MAP_PROTOCOL.md` remain companion
  artifacts; changes to controlled vocabularies or prohibited outputs require
  validation and a recorded decision.
- Future tool implementations must conform to AEC-CDM-001 before any quantitative
  sovereignty output or entity-led expansion is considered.
- Named entity governance in this version is structural: players may appear as
  references, never as the organizing principle of the asset.
