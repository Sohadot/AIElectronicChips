# Industrial Dependency Evidence Release 004: Interconnect and Data Movement

- **Release file:** [`data/research/interconnect-evidence-release-004.json`](data/research/interconnect-evidence-release-004.json)
- **Public reference:** [`/interconnects/`](interconnects/index.html), sections 04–14
- **Evidence as of:** 2026-11-09
- **Status:** `research_candidate`, awaiting human evidence review. Nothing in this release is a published Atlas relationship; `data/dependency-atlas.json` still has 0 relationships.

## Scope

The release covers how data moves in AI systems:

- on-package fabric;
- memory bandwidth versus device-interconnect bandwidth;
- PCIe, CXL and coherent CPU-GPU links;
- direct and switched accelerator fabrics;
- scale-out networking.

**Primary case.** The AMD MI300X 8-GPU platform. One AMD document with footnotes discloses its memory figures, link counts, topology and host link together.

**Bounded contrast.** NVIDIA Vera Rubin NVL72, a switched fabric, drawn from NVIDIA sources already in the registry.

**Not repeated here.** HBM4 (Release 001/IDE-002) and packaging and UCIe (Release 003) are cross-linked rather than duplicated.

**What the release contains:**

- **23 findings:** 2 `verified_fact`, 15 `attributed_statement` and 6 `bounded_analysis`.
  - Both verified facts rest only on the Ultra Ethernet Specification v1.1 text.
  - Every bandwidth or rate figure carries a structured `quantities` entry giving unit, direction, scope, peak or sustained, and whether it is vendor-stated, specified, calculated or measured.
- **10 unresolved questions.**
- **3 unpublished candidate relationships**, each with an AI-assisted recommendation.

## Evidence conflicts recorded, not reconciled

- **NVLink 6 per Rubin GPU.** NVIDIA gives 3.6 TB/s bidirectional (2026-01-05) and 3,600 GB/s (2026-07-21). On 2026-11-05 it gives 3.0 TB/s with no direction, and the live page still said so on 2026-11-09.
- **AMD L2 bandwidth.** The white paper's text gives 34.4 TB/s of aggregate read bandwidth; a legend in the same paper gives 51.6 TB/s for L2-to-XCD.
- **Rubin memory bandwidth.** 22 TB/s versus 19.2 TB/s. This conflict stays recorded in the HBM reference and is unchanged here.

## Retrieval log

| Source | Result on 2026-11-09 | Consequence |
| --- | --- | --- |
| AMD CDNA 3 white paper | Read in full (already registered) | Primary case; record gains `interconnect_specification` and `memory_bandwidth_context` claim types |
| NVIDIA Rubin posts of 2026-01-05, 2026-07-21 and 2026-11-05 | Read (already registered); the 2026-11-05 page was re-fetched live | Records gain the `interconnect` layer and the `interconnect_specification` claim type |
| CXL 3.0 release, CXL 3.0 white paper, CXL 4.0 release | Read in full | Three records registered |
| CXL specification text | The 4.0 text sits behind a click-through evaluation agreement, which was not accepted; only the cover of the public 3.0 PDF was opened | The normative content stays unverified |
| UEC 1.0 announcement | Read in full | Registered |
| UE Specification v1.1 (764 pages) | Introductory and informative sections (pages 20–80) and the contents read | Registered as `technical_standard`; the rest of the document was not read |
| PCI-SIG (pcisig.com) | HTTP 403, and blocked for search | Not used. PCIe figures come only from the CXL Consortium and the GPU vendors |

## Validator changes (`scripts/validate_evidence_releases.py`)

- **New topics:** `host_interface`, `scale_up_fabric`, `scale_out_network`, `measurement_scope`.
- **Optional `quantities` on findings.** It is required for every bandwidth or rate figure in the four topics above.
  - Each figure must be described, and each entry must appear in the finding's statement and cite one of the finding's own sources.
  - GT/s must be scoped per lane, with no direction.
  - `calculated` figures may appear only in bounded analyses; `specified` figures need a `technical_standard`; `measured` figures need a measurement source.
  - Earlier releases are unaffected.
- **New boundary rules:**
  - Un-negated interoperability or compliance assertions are rejected.
  - An un-negated claim that a named product implements, supports or adopts UCIe, CXL or Ultra Ethernet is allowed only when attributed. Generic "whether a product…" phrasing is not treated as a claim.
- **Negation words:** "none" and "nothing" are added.

The new tests are in `tests/test_interconnect_evidence_release.py`. Earlier tests are unchanged.

## Reviewer checklist

- [ ] **Locators.** Spot-check them against the sources, at minimum:
  - `i-amd-mi300x-topology` and `i-an-mi300x-link-arithmetic` (AMD's 896 and 1024 GB/s table figures);
  - `i-nvidia-nvlink6-figures` (the 3.6 versus 3.0 TB/s conflict);
  - `i-uec-network-types`.
- [ ] **Verified facts.** Decide whether the two `verified_fact` findings drawn from the UE Specification v1.1 should stay classed as standard text, given that they come from informative sections.
- [ ] **Accepted candidates.** For each candidate you accept: move it to the Atlas with a named reviewer and date, add its nodes, and delete it from this release.

## Ownership

The classification, unit normalisation, arithmetic, Figure 1 and analysis are original work of AIElectronicChips.com (Sohadot). Quoted passages remain the property of their publishers. Citation implies no endorsement by AMD, NVIDIA, the CXL Consortium or the Ultra Ethernet Consortium.
