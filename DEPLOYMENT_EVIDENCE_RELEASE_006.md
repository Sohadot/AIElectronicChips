# Industrial Dependency Evidence Release 006: AI Compute Infrastructure and Deployment Readiness Evidence

- **Release file:** [`data/research/deployment-evidence-release-006.json`](data/research/deployment-evidence-release-006.json)
- **Demonstration dossier:** [`data/research/dossiers/gb200-nvl72-reference-demo.json`](data/research/dossiers/gb200-nvl72-reference-demo.json)
- **Public reference:** [`/ai-chip-infrastructure/`](ai-chip-infrastructure/index.html), sections 04–14
- **Evidence as of:** 2026-11-10
- **Status:** `research_candidate`, awaiting human evidence review. Nothing here is a published Atlas relationship; `data/dependency-atlas.json` still has 0 relationships.

## Scope

**The question.** What evidence separates a documented AI compute capability from one that has been deployed? The release answers it across seven domains:

- compute hardware;
- electrical;
- thermal;
- network and interconnect;
- software;
- facility operations;
- access and compliance.

**Software version boundary.** The 2025 GB200 administration guide states that Slurm is the only supported scheduler, while the newer Mission Control rack-setup guide version 2.5.0 explicitly includes Slurm and Kubernetes through RunAI. IDE-006 records both as dated vendor claims and does not assume a particular software stack has been deployed.

**Primary case.** GB200 NVL72 with the DGX SuperPOD reference architecture. Where a source covers GB200 and GB300 together, the release says so. Vera Rubin is out of scope.

**Evidence states.** Nine states classify the kind of record that exists for one requirement:

1. product specification documented
2. infrastructure proposed
3. capability contracted
4. equipment procured
5. equipment installed
6. subsystem commissioned
7. integrated configuration verified
8. operational performance observed
9. not established

The states are not a sequence a requirement must pass through, not a score and not an approval.

**What the release contains:**

- **22 findings:**
  - 12 `attributed_statement`;
  - 10 `bounded_analysis`: 2 definitions (`d-def-*`), 3 integration insights (`d-int-*`) and 5 analyses (`d-an-*`).
- **9 unresolved questions.**
- **3 unpublished candidate relationships.** Two are recommended for acceptance. The third, the firmware-baseline candidate, is recommended for deferral because the baseline itself is unpublished.

**Power and thermal evidence.** It is referenced from Release 005, not copied. `u-d-ide005-carryover` lists the open IDE-005 questions by ID.

## Demonstration dossier

The dossier has 18 requirements covering all seven domains:

| State | Requirements |
| --- | --- |
| Product specification documented | 8 |
| Infrastructure proposed | 3 |
| Not established | 7 |

- **Labels.** Its status is `demonstration`, its review status is `not_reviewed` and its assessment method is `ai_assisted_source_check`.
- **No site.** It represents no site, customer, contract or deployment.
- **Site-level states.** No registered source carries the `site_record` claim type, so the validator rejects any site-level state.

## Evidence conflicts and gaps recorded, not resolved

- **Tested scale.** The SuperPOD reference architecture says a fully tested system scales to two scalable units. A garbled adjacent line says one.
- **Checklist items.** NVIDIA's validation checklist includes "sufficient power capacity", cooling "adequate" and "Management approval received". It is a blank template with no thresholds, so it records nothing about any site.
- **Not reviewed:**
  - the standalone GB200/GB300 firmware update guide;
  - the customer SBOM;
  - the building-management interface specification.
- **Export controls.** Only BIS's 2024-12-02 announcement was reviewed, not the current rule text.
- **Carried from IDE-005:**
  - N+N versus N redundancy;
  - the 1,400 A bus bar versus the approximately 120 kW rack;
  - the basis of the 120 kW figure;
  - the unitemised 1.2 MW per scalable unit;
  - the missing coolant specification.

## Retrieval log

| Source | Result on 2026-11-10 | Consequence |
| --- | --- | --- |
| NVIDIA Mission Control rack setup guide 2.5.0, read in full: introduction, pre-deployment, bring-up, firmware, verification and validation checklists | Read | Registered |
| NVIDIA Mission Control GB200 administration guide (PDF) | Read | Registered |
| NVIDIA north-south network deployment guide 2.5.0 | Introduction read | Registered; the rest of the guide was not reviewed |
| NVIDIA DGX GB rack user guide; DGX SuperPOD GB200 reference architecture | Re-read | Claim types extended; `accessed_at` updated |
| BIS 2024-12-02 press release | Re-read | Claim type `access_control_context` added |
| NVIDIA DGX GB200/GB300 Firmware Update Guide | Not retrieved | Recorded as `u-d-firmware-guide` |

## Validator changes (`scripts/validate_evidence_releases.py`)

- **New topics:** `deployment_procedure`, `software_stack`, `operations`, `access_compliance`, `evidence_state`.
- **New boundary rules.** They reject un-negated claims that:
  - installation proves commissioning or operation;
  - software or driver compatibility proves performance;
  - availability proves delivery;
  - a facility conforms to a standard (unless attributed);
  - a planned facility is operational;
  - rated capacity is available capacity;
  - a checklist, dossier or assessment is an approval.

  These sit alongside the IDE-005 rules on reference designs, facility readiness and cooling compatibility.
- **Dossier validation (`data/research/dossiers/*.json`).** The validator checks:
  - exact fields and governed states;
  - all seven domains covered;
  - active cited sources and quote lengths;
  - site-level states only with a `site_record` source;
  - missing information for `not_established`;
  - contradiction IDs that exist in a release;
  - no approval, score, reviewer or certification keys;
  - the boundary rules applied to dossier text.
- **One test change outside IDE-006.** `tests/test_power_thermal_evidence_release.py` hard-coded exactly four release files. It now asserts at least four, so later releases do not break it. Its node-consistency check is unchanged.

The new tests are in `tests/test_deployment_evidence_release.py`.

## Reviewer checklist

- [ ] **Locators.** Spot-check them, at minimum:
  - `d-ra-tested-scope` (both lines);
  - `d-validation-checklist`;
  - `d-bringup-sequence`;
  - `d-sw-stack`.
- [ ] **Evidence-state model.** Confirm that the nine states and their reading rule suit editorial use.
- [ ] **Accepted candidates.** For each candidate you accept: move it to the Atlas with a named reviewer and date, add its nodes, and delete it from this release.

## Ownership

The evidence-state model, classification, Figure 1, the matrix, the dossier and the analysis are original work of AIElectronicChips.com (Sohadot). Quoted passages remain the property of their publishers. Citation implies no endorsement by any company or agency named.
