# Compute Sovereignty Standard v1.0.0

- **Standard ID:** AEC-CS-001
- **Version:** 1.0.0
- **Status:** Active interpretation standard
- **Thesis:** AI chips are the physical substrate of compute sovereignty.

## Purpose

This standard defines how AIElectronicChips.com reads compute sovereignty
responsibly after ontology and claim boundaries are established.

**Ontology** answers: what are the layers?
**Standard** answers: how may those layers be discussed without overclaiming?

The standard does not assign sovereignty to any company, country, product, or
institution. It defines the conditions required to discuss compute sovereignty
responsibly.

## What the Standard Does

- governs how the eight ontology layers may be interpreted;
- defines evidence posture levels for responsible layer discussion;
- requires scope, attribution, confidence discipline, and `as_of` dating;
- preserves unknowns, conflicts, and insufficient evidence;
- applies to public reference pages, dependency records, briefs, audits, and
  dossiers;
- constrains any future tool, map, or diagnostic output.

## What the Standard Does Not Do

The standard does **not**:

- assign sovereignty or non-sovereignty to any entity;
- produce a score, ranking, benchmark, maturity grade, or league table;
- certify independence, resilience, compliance, readiness, or performance;
- provide investment, legal, procurement, deployment, or policy advice;
- compare products, vendors, countries, or chips as winners or losers;
- replace the source registry, claim boundary matrix, or primary evidence review.

## Relationship to the Compute Sovereignty Ontology

`COMPUTE_SOVEREIGNTY_ONTOLOGY.md` defines the eight dependency layers and
cross-layer surfaces. This standard defines how each layer may be read.

Every layer discussion MUST:

- name the relevant ontology layer or layers;
- remain bounded by declared scope and time horizon;
- avoid inferring control at one layer from evidence at another;
- treat the stack as interconnected exposure, not a single capability label.

## Relationship to the Claim Boundary Matrix

`CLAIM_BOUNDARY_MATRIX.md` governs what claims may be stated and how they must
be supported. This standard governs how layered dependency exposure is
interpreted once claim classes are applied.

A conforming interpretation MUST:

- respect permitted, source-required, and confidence-qualified claim categories;
- treat prohibited claims as non-publishable;
- use `insufficient` when evidence does not support an operational finding.

## Evidence Posture Levels

Evidence posture describes whether a layer can be discussed responsibly with
available public reference evidence. These levels are **not** scores and **not**
rankings.

| Level | Meaning |
| --- | --- |
| **Documented** | Sufficient official or primary sources exist to discuss the layer within declared scope. |
| **Partially Documented** | Sources exist, but they do not cover all elements required for a complete layer reading. |
| **Source-Constrained** | The layer is material, but publicly available governed sources are limited or narrow. |
| **Not Assessable** | Available evidence does not support a responsible layer reading without further scoped review. |

Evidence posture guides caution in language. It does not measure national
strength, vendor quality, or product superiority.

## The Eight Standard Dimensions

### 1. Design Layer

**Definition:** The rights, tools, talent, architecture, and verification
capability required to turn compute intent into a manufacturable design.

**Why it matters:** Design control shapes what can be built, licensed, verified,
and transferred before any fabrication step begins.

**Evidence required:** Attributed disclosures on architecture rights, design
capability, IP context, tools, or program scope from filings, official technical
material, or primary policy documents within scope.

**Claim boundary:** May support attributed design-capability framing. Must not
support sovereignty assignment, vendor ranking, or product superiority claims.

**Misinterpretation risk:** Treating a product announcement as full design
control across the stack.

**Related routes:** `/design-fabrication-packaging/`, `/compute-sovereignty/`,
`/sovereignty-stack/`

### 2. Fabrication Layer

**Definition:** Manufacturing access, process capability, equipment dependency,
materials, yield, and the conditions under which silicon can be produced.

**Why it matters:** A design without fabrication access remains a dependency,
not deployable compute substrate.

**Evidence required:** Government policy, regulation, filings, annual reports, or
official institutional material on manufacturing scope, reported risk, or
program context.

**Claim boundary:** May support attributed fabrication-access framing within
source scope. Must not support market-wide capacity conclusions, supplier
ranking, or operating guarantees.

**Misinterpretation risk:** Inferring current production conditions from strategy
documents or announcements alone.

**Related routes:** `/design-fabrication-packaging/`, `/export-control-layer/`,
`/sources/`

### 3. Packaging Layer

**Definition:** Die integration, substrates, assembly, test, thermal design, and
the capability required to turn manufactured dies into deployable systems.

**Why it matters:** Advanced AI compute often depends on packaging integration,
not isolated die performance.

**Evidence required:** Technical standards releases, official technical
disclosures, filings, or institutional reports on packaging, assembly, or
integration scope.

**Claim boundary:** May support attributed integration and packaging framing.
Must not support adoption, interoperability, or supplier-position conclusions
without scoped evidence.

**Misinterpretation risk:** Treating a standard release or product disclosure as
proof of deployable packaging access everywhere.

**Related routes:** `/design-fabrication-packaging/`, `/hbm-memory/`,
`/interconnects/`

### 4. Memory Layer

**Definition:** Required memory type, bandwidth, capacity, qualification,
integration, and access conditions for AI compute.

**Why it matters:** Memory bandwidth and integration can bound usable compute
even when processors are available.

**Evidence required:** Official technical disclosures, product specifications,
controls-related records, or filings within attributed scope.

**Claim boundary:** May support attributed memory-bandwidth and integration
framing. Must not support market-wide availability, allocation, supplier
ranking, or future-supply findings.

**Misinterpretation risk:** Using product-level HBM disclosures to infer general
market access or supply dominance.

**Related routes:** `/hbm-memory/`, `/design-fabrication-packaging/`

### 5. Interconnect Layer

**Definition:** Data movement within systems, across racks, facilities, and
regions, including fabrics, switching, topology, latency, and compatibility.

**Why it matters:** Interconnect fit determines whether compute, memory, and
hosts function as a usable system.

**Evidence required:** Technical standards, official technical disclosures,
filings, or institutional infrastructure context within scope.

**Claim boundary:** May support attributed interconnect and integration framing.
Must not support vendor comparison, deployment verdict, or performance ranking.

**Misinterpretation risk:** Treating disclosed topology or standard scope as proof
of deployment success.

**Related routes:** `/interconnects/`, `/ai-chip-infrastructure/`,
`/hbm-memory/`

### 6. Power / Thermal Layer

**Definition:** Power delivery, density, cooling, heat rejection, water use,
and operating constraints that bound deployable compute.

**Why it matters:** Power and thermal limits can make otherwise available chips
undeployable in practice.

**Evidence required:** Institutional reports, official recommendations, modeled
projections, or facility-context disclosures with stated scope and dates.

**Claim boundary:** May support attributed infrastructure and energy-context
framing. Must not support site-level readiness, operating guarantees, or
current availability conclusions.

**Misinterpretation risk:** Treating projections or recommendations as present
operating facts.

**Related routes:** `/power-and-thermal-limits/`, `/ai-chip-infrastructure/`

### 7. Export-Control Layer

**Definition:** Rules, licenses, thresholds, exceptions, sanctions, procurement
constraints, and effective dates that shape access and transfer.

**Why it matters:** Legal and administrative controls can constrain design,
equipment, memory, fabrication, and deployment paths.

**Evidence required:** Government rules, regulations, official notices, and
attributed company or institutional disclosures after primary-text review.

**Claim boundary:** May support attributed control-scope framing. Must not
support compliance verdicts, geopolitical conclusions, or entity-level access
findings without scoped evidence.

**Misinterpretation risk:** Treating announcements as implemented operating
conditions.

**Related routes:** `/export-control-layer/`, `/sources/`, `/methodology/`

### 8. Deployment Layer

**Definition:** Installation, facilities, operations, maintenance, recovery,
cloud or on-premises access, and geographic distribution of compute.

**Why it matters:** A chip becomes useful compute only inside an operating
infrastructure with continuing access.

**Evidence required:** Institutional infrastructure reports, filings, official
program material, and scoped operating-context disclosures.

**Claim boundary:** May support attributed deployment and infrastructure framing.
Must not support readiness certification, performance guarantees, or entity-level
deployment conclusions.

**Misinterpretation risk:** Inferring operational resilience from component-level
or policy-level evidence alone.

**Related routes:** `/ai-chip-infrastructure/`, `/power-and-thermal-limits/`,
`/chip-dependency-map/`

## Responsible Interpretation Rules

1. Read by layer and exposure type before cross-layer synthesis.
2. Preserve contradictions, unknowns, and differing confidence across findings.
3. Treat missing evidence as `insufficient`, not proof of weakness.
4. Distinguish verified fact, attributed statement, estimate, analysis, and unknown.
5. Carry an `as_of` date on material findings and review before reuse.
6. Use exposure types as contextual framing, not verdicts:
   concentration, access, capacity, technology, operational, and evidence exposure.
7. Use finding confidence (`high`, `medium`, `low`, `insufficient`) only after
   governed evidence review; confidence is not a score.
8. Treat diagnostic responses and artifact hints as investigation inputs, not
   recommendations.
9. Disclose material conflicts rather than averaging them away.
10. Any future tool or map MUST conform to this standard before public scoring is
    even considered.

## Prohibited Uses

The following are non-conforming under AEC-CS-001 v1.0.0:

- assigning sovereignty or non-sovereignty to any company, country, product, or
  institution;
- public or private rankings, league tables, benchmarks, or maturity grades;
- Chip Sovereignty Score or any numeric sovereignty index;
- country, company, or product comparison presented as winner/loser framing;
- best-chip, best-HBM, or superiority marketing language in reference findings;
- investment, legal, procurement, or national-security advice;
- certification, guarantee, or readiness verdicts;
- treating evidence posture levels as performance scores;
- using ontology layer control at one layer to imply full-stack sovereignty;
- publishing news-cycle commentary as foundational evidence.

## Versioning Notes

- **0.1.0** established the foundation interpretation standard before public
  reference authority work was complete.
- **1.0.0** formalizes responsible reading rules after ontology v1 and the
  Claim Boundary Matrix, with eight standard dimensions and non-numeric evidence
  posture levels.

No score, ranking, sovereignty assignment, or automated operational judgment may
be introduced without a separately governed standard revision, documented
methodology, validation evidence, and explicit approval. This version does not
imply that such approval will ever be appropriate.

Future revisions MAY add conformance checklists, artifact templates, and tool
binding rules. They MUST NOT silently introduce scoring or ranking products.

## Related Documents

- [Compute Sovereignty Ontology v1](COMPUTE_SOVEREIGNTY_ONTOLOGY.md)
- [Claim Boundary Matrix](CLAIM_BOUNDARY_MATRIX.md)
- [Claim Policy](CLAIM_POLICY.md)
- [Source Registry Protocol](SOURCE_REGISTRY_PROTOCOL.md)
