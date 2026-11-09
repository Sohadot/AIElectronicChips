# Industrial Dependency Evidence Release 003: Advanced Packaging and Chiplet Integration

- **Release file:** [`data/research/packaging-evidence-release-003.json`](data/research/packaging-evidence-release-003.json)
- **Public reference:** [`/design-fabrication-packaging/`](design-fabrication-packaging/index.html), sections 04–11
- **Evidence as of:** 2026-11-09
- **Status:** `research_candidate`. Awaiting human evidence review. Nothing in this release is a published Atlas relationship; `data/dependency-atlas.json` still has 0 relationships.

## Scope

How fabricated dies become a deployable AI accelerator:

- TSMC's CoWoS-S, CoWoS-R and CoWoS-L;
- SoIC 3D stacking and SoW;
- the UCIe die-to-die interface;
- an eight-stage production pathway;
- AMD Instinct MI300X as a case traced to AMD's own publications.

HBM is covered by Release 001/IDE-002 and is cross-linked, not repeated.

**The release records:**

- **22 findings**: 18 `attributed_statement` (A) and 4 `bounded_analysis` (C, with `assumptions`). There is no `verified_fact`: every source is a company or consortium statement.
- **9 unresolved questions** (U), each with the sources checked and the evidence that would resolve it.
- **5 candidate nodes and 3 candidate relationships**, each with an AI-assisted `research_recommendation`. All have `reviewed_at: null` and `review_owner: unassigned`.

## Route decision

The release extends `/design-fabrication-packaging/`, which already owns ontology layer 03 (Packaging). It adds no new route. Sections 01–03 and the `#design`, `#fabrication` and `#packaging` JSON-LD terms are kept, because other pages reference them.

## Retrieval log

| Source | Result on 2026-11-09 | Consequence |
| --- | --- | --- |
| TSMC 2025 Annual Report, ch. 5 (PDF) | HTTP 403 to curl; retrieved with the fetch tool; text extracted locally with pdftotext (SHA-256 `7ef33d9677401902…`) | Registered as `tsmc-2025-annual-report`. Its date, 2026-04-16, comes from the PDF metadata |
| TSMC 2024 Annual Report, ch. 5 (PDF) | Same route (SHA-256 `9453911b2e8b6ae5…`) | Existing record `tsmc-2024-annual-report`: `accessed_at` updated; `packaging_technology_status` claim type added |
| TSMC 3DFabric CoWoS and SoIC pages; pr.tsmc.com | HTTP 403 | Not used. The SoIC bonding method stays unresolved |
| AMD CDNA 3 white paper (PDF, revision 2025-04-07) | Read in full (SHA-256 `a0811d04f101f912…`) | Names no CoWoS, SoIC, hybrid bonding or interposer for MI300 |
| AMD blogs, 2024-12-10 (Synopsys; 30x25) | Read in full | These are the only reviewed sources that tie MI300X to CoWoS |
| AMD MI300 launch release, 2023-12-06 | Read in full | Availability date |
| AMD CDNA architecture page | Read; undated (no publication date in page or metadata) | Not registered and not used, per the registry's date rule. Its MI400 statements (hybrid-bonded dies, CoWoS-L) are therefore not in this release |
| UCIe 1.0, 2.0 and 3.0 announcements (PDF); 3.0 blog; 2025 review | Read in full | 1.0, 3.0, the blog and the review registered. The 2.0 record stays `pending_review`, and findings citing it are marked `includes_pending_source` |
| UCIe 2.0 and 3.0 specifications | Not requested (available by request only) | Normative content explicitly unverified |

## Validator changes (`scripts/validate_evidence_releases.py`)

- **Page mapping.** A release names its public page in an optional `reference_page` field, and is checked only against that page. Release 001 keeps `hbm-memory/index.html` through a legacy mapping. `reference_page` must point to an existing `index.html` outside `data/`, `scripts/` and `tests/`.
- **Review statement per page.** The "Evidence compiled" and "Scientific review pending" checks now run per page, against that page's own releases.
- **Packaging topics added:** `interposer_bridge`, `chiplet_interface`, `assembly_test`, `production_chain`, `interoperability`.
- **CoWoS product claims.** These are still rejected unless negated, with one exception. A product named in an attributed finding of the same release, together with CoWoS, may appear elsewhere in that release:
  - a candidate edge must cite one of that finding's sources;
  - a page sentence must cite a reference that resolves to one of them.
  - Universal claims ("all HBM4") are never allowed. Release 001 has no such finding, so its behaviour is unchanged.
- **Citations follow their sentence.** Page citations placed after a full stop are attached to the sentence before them.
- **Shared candidate nodes.** A candidate node proposed by two releases (`tech-cowos`) must be defined identically in both.

The new tests are in `tests/test_packaging_evidence_release.py`. All earlier tests are unchanged.

## Reviewer checklist

- [ ] **Locators.** Spot-check locators against the sources, at minimum:
  - `p-amd-mi300x-cowos` (AMD blogs);
  - `p-cowos-l-large-reticle` (two differing TSMC statements);
  - `p-soic-status`.
- [ ] **TSMC 2025 date.** Confirm the report's publication date. It is taken from the PDF metadata; TSMC's Form 20-F for 2025 was filed the same day.
- [ ] **UCIe 2.0 record.** Decide whether to activate `ucie-2-specification-release-2024`. The announcement has now been read in full, as was done for the JEDEC announcement. Activating it changes pending markers on `/sources/`, `/methodology/`, `/interconnects/` and this page, and one test fixture that uses it as the pending example.
- [ ] **Accepted candidates.** For each candidate you accept: move it to the Atlas with a named reviewer and date, add its nodes, and delete it from this release.

## Ownership

The classification, comparison, Figure 1, the arithmetic and the analysis are original work of AIElectronicChips.com (Sohadot). Quoted passages remain the property of their publishers. Citation implies no endorsement by TSMC, AMD or the UCIe Consortium.
