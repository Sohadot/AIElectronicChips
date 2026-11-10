# Industrial Dependency Evidence Release 005: Power Delivery and Thermal Infrastructure

- **Release file:** [`data/research/power-thermal-evidence-release-005.json`](data/research/power-thermal-evidence-release-005.json)
- **Public reference:** [`/power-and-thermal-limits/`](power-and-thermal-limits/index.html), sections 04–14
- **Calculations:** [`scripts/engineering_calcs.py`](scripts/engineering_calcs.py). A test checks every worked result on the page against these formulas.
- **Evidence as of:** 2026-11-10
- **Status:** `research_candidate`, awaiting human evidence review. Nothing here is a published Atlas relationship; `data/dependency-atlas.json` still has 0 relationships.

## Scope

**The two chains.** The release traces the electrical chain from utility to package, and the thermal chain from junction to heat rejection.

**Primary case.** The GB200 NVL72 rack, using NVIDIA's DGX GB rack user guide (2026-09-17), its DGX GB200 SuperPOD reference architecture (2025-09-03) and its 2024 OCP contribution. The user guide covers GB200 and GB300 racks together. Vera Rubin NVL72 figures are not used.

**What the release contains:**

- **26 findings:** 2 `verified_fact` (The Green Grid's PUE and WUE definitions), 16 `attributed_statement` and 8 `bounded_analysis`. Every power, energy, current, voltage, temperature and flow figure carries a structured `quantities` entry.
- **11 unresolved questions.**
- **3 unpublished candidate relationships.**

## Evidence conflicts and gaps recorded, not resolved

- **Power-shelf redundancy.** The user guide says "N+N redundancy"; the reference architecture says "configured as N redundancy".
- **Bus-bar rating versus rack load.** A 1,400 A bus bar at a nominal 50 V carries 70 kW, against an approximately 120 kW rack. No reviewed source states the number of bus-bar paths.
- **Undefined figures.**
  - "Approximately 120kW" is not defined as rated, typical or measured, and is not separated between GB200 and GB300.
  - There are no per-GPU or per-superchip power figures.
- **Missing cooling specifications.**
  - No coolant type, flow, supply temperature, pressure or ASHRAE class is stated for GB200 NVL72.
  - The split of rack heat between liquid and air is not stated.

## Retrieval log

| Source | Result on 2026-11-10 | Consequence |
| --- | --- | --- |
| NVIDIA DGX GB rack user guide (PDF, 74 pages) | Read | Registered |
| NVIDIA DGX GB200 SuperPOD reference architecture (PDF, 33 pages) | Read | Registered |
| NVIDIA OCP contribution blog (2024-10-15) | Read | Registered; the OCP specification files themselves were not reviewed |
| NVIDIA water-efficiency blog (2025-04-22) | Read | Registered as `company_announcement`; its efficiency multiples have no stated method |
| Vertiv GB200 NVL72 reference architecture release (2024-10-17) | Read | Registered as `company_announcement` |
| OCP liquid-to-liquid CDU test methodology, Revision 1.0 | Read | Registered; reproduces the ASHRAE TC 9.9 classes |
| The Green Grid WP#49 (PUE) and WP#35 (WUE) | Read | Registered. The PUE paper states no publication day, so its PDF date is recorded |
| DOE 2024 energy report announcement; SEAB recommendations | Re-read (already registered) | `accessed_at` updated |
| LBNL 2024 data-center energy report | Empty HTTP 202 response | Not used |
| IEA Energy and AI | HTTP 403 | Not used; the existing record is listed as not re-reviewed |
| ASHRAE TC 9.9 guidelines | Sold or subscription-only | Not reviewed; classes cited only as reproduced by OCP |

## Validator changes (`scripts/validate_evidence_releases.py`)

- **New topics:** `power_delivery`, `thermal_transport`, `facility_infrastructure`, `efficiency_metric`.
- **Structured `quantities` extended** to power (W to GW), energy (kWh to TWh), A, V, °C, K, L/min, kg/s and L/kWh.
  - These figures take no direction.
  - An energy figure cannot be a rating or peak.
  - Projected figures must be `modelled`.
  - Temperatures must name their loop or component.
  - `assumed` inputs belong only in bounded analyses.
  - The figure parser does not read class labels such as "W17" as watts.
- **New boundary rules** reject un-negated claims that:
  - apply PUE or WUE to a product;
  - treat TDP as consumption;
  - present a reference design as operating infrastructure;
  - assert facility readiness;
  - assert cooling compatibility without attribution;
  - equate heat load with a rated capacity.

  These rules read past decimal points such as "1.2 MW".
- **Unchanged:** the earlier rules, including the IDE-004 unit and direction rules.

The new tests are in `tests/test_power_thermal_evidence_release.py`.

## Reviewer checklist

- [ ] **Locators.** Spot-check them, at minimum:
  - `pt-gb-power-shelves` and `pt-ra-power-shelves` (the redundancy conflict);
  - `pt-ocp-bus-bar`;
  - `pt-ashrae-classes-via-ocp`.
- [x] **PUE paper date.** The Green Grid's official WP#49 listing dates original publication to 2012-10-02. The accessible LBNL-hosted v6 PDF was created 2013-02-04; a PDF creation timestamp is not the paper's publication date. The registry now uses the publisher date and separately discloses the edition provenance. The stable legacy source ID is retained to avoid unnecessary reference churn.
- [ ] **Accepted candidates.** For each candidate you accept: move it to the Atlas with a named reviewer and date, add its nodes, and delete it from this release.

## Ownership

The classification, calculations, Figure 1, the dependency matrix and the analysis are original work of AIElectronicChips.com (Sohadot). Quoted passages remain the property of their publishers. Citation implies no endorsement by any company or organisation named.
