# HBM4 Evidence Release 001

- **Release file:** [`data/research/hbm4-evidence-release-001.json`](data/research/hbm4-evidence-release-001.json)
- **Public reference:** [`/hbm-memory/`](hbm-memory/index.html)
- **Evidence as of:** 2026-11-09
- **Status:** `research_candidate`. Awaiting human evidence review. Nothing in this release is a published Atlas relationship.

## Purpose

This is the first production-grade evidence release for the memory layer. It covers HBM3E, HBM4 and HBM4E as a reference case for how the asset converts primary disclosures into classified, machine-readable findings without overstating them. It records:

- **32 findings**, each with registered sources, a quoted locator, a scope, a date and limitations, classified as:
  - `verified_fact` (A): established by a standard or other independent record within its scope. These currently rest on the JEDEC record, which is `pending_review`, so all four carry `evidence_state: includes_pending_source`.
  - `attributed_statement` (B): what a company disclosed. No independent verification is implied.
  - `bounded_analysis` (C): project derivations, with explicit `assumptions`.
- **12 unresolved questions** (D), each with the sources checked and the evidence that would resolve it.
- **5 candidate nodes and 4 candidate relationships** in the exact Atlas edge shape, with `reviewed_at: null` and `review_owner: unassigned`.

## Method

1. Candidate sources were checked against `data/source-registry.json` first; no parallel database was created. Fourteen records were added (registry v0.4.0).
2. Each source page was read and the relevant passages were extracted verbatim, with the page's own date. Locators in the release file quote those passages.
3. Every statement was classified by what its evidence can bear. Sample shipments, "mass production system readied", volume shipment and commercial shipment are recorded as distinct milestones. Forward-looking statements are labelled as such. Priority claims ("world's first", "industry-first") are permitted only inside attributed findings; the validator rejects them elsewhere.
4. Where sources conflict (NVIDIA's 22 TB/s versus 19.2 TB/s per Rubin GPU) or are silent (Micron's base die), the gap is recorded as unresolved, not filled.

## Retrieval log: what could not be read

| Source | Result on 2026-11-09 | Consequence |
| --- | --- | --- |
| JEDEC JESD270-4 press release and JESD270-4A page (jedec.org) | HTTP 403 (bot challenge) | Registry record `pending_review`; standard parameters shown on the page as `S`, awaiting direct confirmation |
| Same release via Business Wire | HTTP 403 | As above |
| Samsung HBM4 release, 2026-02-12 | Timed out; mirror redirected to a generic landing page | Registry record `pending_review`; its per-stack bandwidth figure is not used |
| Samsung Q1 2026 results | Timed out | Not registered |
| NVIDIA Vera Rubin NVL72 product page | Read, but undated | Cited on the page only to document the bandwidth conflict; not registered, because the registry requires a publication or effective date |

An archive.org fallback for the JEDEC pages was attempted but blocked by this session's permission policy, so it was not used.

## Validation, and its limits

`scripts/validate_evidence_releases.py`, run by `scripts/validate_all.py`, enforces:

- the release can never declare itself published;
- source IDs resolve and are not retired;
- every citation carries a locator;
- `evidence_state` agrees with each cited source's registry status;
- `verified_fact` never rests only on company sources (`official_technical_disclosure` or `company_announcement`);
- `bounded_analysis` states its assumptions;
- source dates precede finding dates;
- IDs are unique.

Each candidate relationship is also run through the Atlas validator in a simulated reviewed state. This proves it would satisfy the publication contract, and it would fail if it cited a pending source.

None of this checks that a passage actually says what a finding states. **That is the human reviewer's job.**

## Reviewer checklist (owner and scientific review)

- [ ] Read the JEDEC JESD270-4 announcement directly and confirm or correct `f-std-*`; then set `jedec-jesd270-4-hbm4-standard-2025` to `active` with a review date.
- [ ] Read Samsung's 2026-02-12 HBM4 release; promote or revise `samsung-hbm4-commercial-shipment-2026`.
- [ ] Spot-check every locator against its source, at minimum the base-die findings (`f-skh-base-die`, `f-tsmc-base-die`, `f-ss-base-die`) and the commercialization ledger.
- [ ] Decide whether the interpretation in `f-ss-base-die` ("same combination of core and base die" as describing Samsung HBM4) is acceptable.
- [ ] For each candidate relationship you accept: move it to `data/dependency-atlas.json` with a named `review_owner` and `reviewed_at`, add its nodes, set Atlas `status` to `evidence_backed`, and delete it from this release. Both validators enforce the move.
- [ ] Decide whether `data/research/` should be excluded from the Pages artifact. The current workflow uploads the repository root, so once merged this file is publicly fetchable, although no page links to it.

## Ownership

The classification scheme, findings structure, arithmetic, Figure 1 and the analysis are original work of AIElectronicChips.com (Sohadot). Quoted passages, product specifications and the JEDEC standard remain the property of their publishers. Citation implies no endorsement by JEDEC or any company.
