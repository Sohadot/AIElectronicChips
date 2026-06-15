# Compute Sovereignty Ontology v1

## Status

- **Version:** 1.0.0
- **Status:** Reference authority foundation
- **Thesis:** AI chips are the physical substrate of compute sovereignty.

## Purpose

This ontology is the core reference model for AIElectronicChips.com. It provides
a common language for mapping the dependencies that make AI compute possible. It
describes exposure; it does not assign a universal sovereignty score.

Every public reference page must map to one or more of these layers or to a
governed cross-layer surface such as methodology, sources, or the dependency map.

## Eight Layers

| ID | Layer | Governing question | Public reference route |
| --- | --- | --- | --- |
| 01 | **Design Layer** | Who controls the architecture and design rights? | `/design-fabrication-packaging/` |
| 02 | **Fabrication Layer** | Who can manufacture the required silicon? | `/design-fabrication-packaging/` |
| 03 | **Packaging Layer** | Who can integrate dies into deployable systems? | `/design-fabrication-packaging/` |
| 04 | **Memory Layer** | Who can provide memory at the required bandwidth and scale? | `/hbm-memory/` |
| 05 | **Interconnect Layer** | How does data move within and between compute systems? | `/interconnects/` |
| 06 | **Power / Thermal Layer** | Can the infrastructure energize and cool deployment? | `/power-and-thermal-limits/` |
| 07 | **Export-Control Layer** | What rules shape access and transfer? | `/export-control-layer/` |
| 08 | **Deployment Layer** | Can compute be installed, operated, and maintained? | `/ai-chip-infrastructure/` |

### Layer signals

| Layer | Example dependency signals |
| --- | --- |
| Design | IP ownership, EDA access, design talent, architecture rights |
| Fabrication | foundry access, process node, equipment, yield, manufacturing geography |
| Packaging | advanced packaging capacity, substrates, assembly, test, thermal integration |
| Memory | HBM access, bandwidth, qualification, supplier concentration |
| Interconnect | network fabrics, optical links, switching capacity, topology fit |
| Power / Thermal | grid access, power density, cooling, heat rejection, water constraints |
| Export-Control | export controls, licenses, sanctions, procurement rules, effective dates |
| Deployment | data centers, cloud access, operations, maintenance, geographic diversity |

## Cross-Layer Surfaces

These routes serve the ontology without replacing a layer definition:

| Surface | Role |
| --- | --- |
| `/` | Thesis and entry to the reference system |
| `/compute-sovereignty/` | Category definition for compute sovereignty |
| `/sovereignty-stack/` | Ontology navigation across all eight layers |
| `/chip-dependency-map/` | Governed diagnostic model across all layers |
| `/methodology/` | Evidence, claim, and confidence governance |
| `/sources/` | Governed source registry and evidence posture |
| `/strategic-availability/` | Bounded commercial pathways; not a layer |

## Dependency Record

Every mapped dependency should identify:

- `entity`: the organization, jurisdiction, facility, or system being assessed;
- `layer`: one or more ontology layers;
- `dependency`: the capability, supplier, jurisdiction, or permission required;
- `criticality`: low, moderate, high, or unknown;
- `substitutability`: available, constrained, unavailable, or unknown;
- `evidence`: source references supporting the record;
- `confidence`: high, medium, low, or insufficient;
- `as_of`: the date through which the record is supported.

## Exposure Types

- **Concentration exposure:** dependence on a narrow supplier or location.
- **Access exposure:** dependence on permission, licensing, or allocation.
- **Capacity exposure:** insufficient scale, lead time, power, or cooling.
- **Technology exposure:** dependence on proprietary technology or expertise.
- **Operational exposure:** inability to deploy, maintain, or recover systems.
- **Evidence exposure:** insufficient reliable information to make a claim.

## Interpretation Rule

No layer is sovereign in isolation. An entity that controls chip design but
depends on external fabrication, memory, or power remains exposed at those
layers. Findings must preserve this layered character rather than collapse it
into a simplistic label.

Claims about any layer require governed evidence under `CLAIM_BOUNDARY_MATRIX.md`
and the source registry.

## Related Documents

- [Claim Boundary Matrix](CLAIM_BOUNDARY_MATRIX.md)
- [Compute Sovereignty Standard](COMPUTE_SOVEREIGNTY_STANDARD.md)
- [Silicon Sovereignty Stack reference](/sovereignty-stack/)
