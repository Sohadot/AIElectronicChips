# Compute Sovereignty Ontology

## Purpose

This ontology provides a common language for mapping the dependencies that make
AI compute possible. It describes exposure; it does not assign a universal
sovereignty score.

## Sovereignty Stack

| Layer | Governing question | Example dependency signals |
| --- | --- | --- |
| Design | Who controls the architecture and design rights? | IP ownership, EDA access, design talent |
| Fabrication | Who can manufacture the required silicon? | foundry access, process node, equipment, yield |
| Packaging | Who can integrate dies into deployable systems? | advanced packaging capacity, substrates, test |
| Memory | Who can provide memory at the required bandwidth and scale? | HBM access, supplier concentration, qualification |
| Interconnect | How does data move within and between compute systems? | network fabrics, optical links, switching capacity |
| Power and Thermal | Can the infrastructure energize and cool deployment? | grid access, power density, cooling, water constraints |
| Controls | What rules shape access and transfer? | export controls, licenses, sanctions, procurement rules |
| Deployment | Can compute be installed, operated, and maintained? | data centers, cloud access, operations, geographic diversity |

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

