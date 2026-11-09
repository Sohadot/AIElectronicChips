# HBM4 Evidence Release 001

- **Release file:** [`data/research/hbm4-evidence-release-001.json`](data/research/hbm4-evidence-release-001.json)
- **Public reference:** [`/hbm-memory/`](hbm-memory/index.html)
- **Evidence as of:** 2026-11-09
- **Status:** `research_candidate`. Awaiting human evidence review. Nothing in this release is a published Atlas relationship.

## Purpose

This is the first production-grade evidence release for the memory layer. It covers HBM3E, HBM4 and HBM4E as a reference case for how the asset converts primary disclosures into classified, machine-readable findings without overstating them. It records:

- **42 findings**, each with registered sources, a quoted locator, a scope, a date and limitations, classified as:
  - `verified_fact` (A): established by a standard or other independent record within its scope. **None at present.** JEDEC's announcement has been read, but it is not the normative standard, so its five findings (`f-std-*`) remain attributed statements. A company filing such as Micron's 10-K is also kept attributed: it is the company's own statement. The validator rejects any `verified_fact` that rests only on announcements or cites a pending source.
  - `attributed_statement` (B): what a company disclosed. No independent verification is implied.
  - `bounded_analysis` (C): project derivations, with explicit `assumptions`.
- **11 unresolved questions** (D), each with the sources checked and the evidence that would resolve it.
- **6 candidate nodes and 5 candidate relationships** in the exact Atlas edge shape, with `reviewed_at: null` and `review_owner: unassigned`. Each of the original four carries an AI-assisted `research_recommendation` (see IDE-002 below).

## Method

1. Candidate sources were checked against `data/source-registry.json` first; no parallel database was created. Twenty-one records were added (registry v0.4.0), including two SEC filings and one 8-K exhibit.
2. Each source page was read and the relevant passages were extracted verbatim, with the page's own date. Locators in the release file quote those passages.
3. Every statement was classified by what its evidence can bear. Sample shipments, "mass production system readied", volume shipment and commercial shipment are recorded as distinct milestones. Forward-looking statements are labelled as such. Priority claims ("world's first", "industry-first") are permitted only inside attributed findings; the validator rejects them elsewhere.
4. Where sources conflict (NVIDIA's dated articles give "up to 22 TB/s" and later an unqualified 19.2 TB/s per Rubin GPU, and its current product pages still disagree) or are silent (SK hynix's production base die), the gap is recorded as unresolved, not filled. No NVIDIA page labels either bandwidth figure preliminary.
5. Quoted excerpts are capped at 20 words each and 40 per citation, enforced by the validator.

## Retrieval log: what could not be read

| Source | Result on 2026-11-09 | Consequence |
| --- | --- | --- |
| JEDEC JESD270-4 press release and JESD270-4A page (jedec.org) | HTTP 403 (bot challenge) | Not used directly |
| Same release via businesswire.com (ID 20250416843598) | HTTP 403, on two attempts | Not used directly |
| Same release via its MarketsFinancialContent (Wedbush) syndication | Read in full with curl on 2026-11-09 (page SHA-256 `1cc133aabfbc2a75…`); includes the "About JEDEC" text and the Business Wire source link. The host disclaims responsibility for accuracy. | Registry record now `active`, typed as an announcement. All four `f-std-*` findings confirmed against the text; `f-std-stacks` corrected from "TSV stacks" to "DRAM stack configurations"; voltage options added as `f-std-voltage`. The JESD270-4/4A documents themselves remain unreviewed |
| Micron FY2026 Form 10-K, Q3 FY2026 8-K exhibit; SK hynix 424B4 prospectus | Read in part (the first ~80,000 characters of each filing; the full 8-K exhibit) | Micron base logic die: in-house design and manufacture. SK hynix: no base-die manufacturer in the portion read |
| Samsung HBM4 release, 2026-02-12 | Read in full on the Samsung Semiconductor Newsroom (an earlier news.samsung.com attempt timed out) | Registry record now `active` |
| Samsung Q1 2026 results | Timed out | Not registered |
| NVIDIA HGX and Vera Rubin NVL72 product pages | Read, but undated; footnotes checked: no "preliminary" label on memory figures | Cited only to document the bandwidth conflict; not registered, because the registry requires a publication or effective date |

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

- [ ] Compare `f-std-*` against JEDEC's own copy of the announcement on jedec.org. The text used here came from a third-party syndication. Any normative statement needs the JESD270-4A document itself.
- [ ] Spot-check every locator against its source, at minimum the base-die findings (`f-skh-base-die`, `f-tsmc-base-die`, `f-ss-base-die`) and the commercialization ledger.
- [ ] For each candidate relationship you accept: move it to `data/dependency-atlas.json` with a named `review_owner` and `reviewed_at`, add its nodes, set Atlas `status` to `evidence_backed`, and delete it from this release. Both validators enforce the move.
- [ ] Note the exposure model. This repository is public, so this file is readable on GitHub regardless. The Actions deploy job now stages the site without `data/research/`, and the validator fails if that exclusion is removed. Branch-mode Pages would still serve the file, so switch Pages to GitHub Actions before merging.

## Industrial Dependency Evidence Release 002 (IDE-002, release version 1.1.0)

IDE-002 follows the HBM4 dependency chain: architecture, base-die sourcing, stack assembly, package integration and platform qualification. Its public form is the "Industrial dependency pathways" section of `/hbm-memory/`.

- **New sources:** SK hynix, 2026-07-08 (`skhynix-full-stack-memory-2026`) and 2026-04-23 (`skhynix-tsmc-symposium-2026`). SK hynix now *states* it applies TSMC advanced logic process technology to the base die starting with HBM4. That is still a company statement, and no node is named.
- **New findings:** `f-skh-base-die-2026`, `f-packaging-stages`, `f-nv-on-package`, `f-dram-core-process` and the bounded analysis `f-an-dependency-pathways`.
- **Could not be read:** TSMC's 2026 North America Technology Symposium release (pr.tsmc.com/english/news/3302) returned HTTP 503 to the fetch tool and 403 to direct retrieval. Nothing from it is used.

| Candidate | AI-assisted recommendation | Basis |
| --- | --- | --- |
| `rel-hbm4-requires-logic-base-die` | ACCEPT (revised) | All three suppliers describe core dies on a base die; narrowed to architecture only |
| `rel-hbm-base-die-requires-logic-foundry` | REJECT | Contradicted for Micron (in-house); the Atlas has no supplier-level node kind. Kept for audit |
| `rel-hbm-base-die-requires-logic-cmos-fabrication` | ACCEPT (new) | Sourcing-neutral replacement supported by each supplier's statement |
| `rel-hbm4-integrates-with-cowos` | DEFER | No product-level HBM4-on-CoWoS disclosure; NVIDIA names no packaging technology |
| `rel-rubin-gpu-requires-hbm4` | ACCEPT (revised) | Rests on NVIDIA's own statements; supplier "designed for" evidence removed |

These are recommendations from an AI-assisted source check (`assessment_method: ai_assisted_source_check`), not a human scientific review. Every candidate remains `awaiting_human_review` and unpublished; the Atlas has 0 relationships.

## Ownership

The classification scheme, findings structure, arithmetic, Figure 1 and the analysis are original work of AIElectronicChips.com (Sohadot). Quoted passages, product specifications and the JEDEC standard remain the property of their publishers. Citation implies no endorsement by JEDEC or any company.
