# IDE-007: Cross-Layer Reference Pathways

- **Model:** [`data/reference-pathways.json`](data/reference-pathways.json). It is public and is published with the site.
- **Explorer:** [`/sovereignty-stack/#research-pathways`](sovereignty-stack/index.html), sections 04–07.
- **Renderer:** [`scripts/render_reference_pathways.py`](scripts/render_reference_pathways.py). It generates the explorer section of the page from the model.
- **Validator:** [`scripts/validate_reference_pathways.py`](scripts/validate_reference_pathways.py). It runs in `validate_all.py`.
- **Tests:** `tests/test_reference_pathways.py`.
- **Status:** `reference_navigation`, with scientific review pending. A pathway is navigation, not a Dependency Evidence Atlas relationship. The Atlas still has 0 approved relationships.

## Editing a pathway

1. Edit `data/reference-pathways.json`.
2. Run `python3 scripts/render_reference_pathways.py` to regenerate the page section between the `reference-pathways` markers.
3. Run `python3 scripts/validate_all.py`. It fails if the page and the model disagree.

## Schema

**Model fields:**

- `model_id`, `schema_version`, `release`;
- `status`, which must be `reference_navigation`;
- `compiled_at`;
- `scientific_review`, which must be `pending`;
- `boundary`;
- `atlas_reference`, `source_registry_reference`;
- `workflow`: the eight question-to-evidence stages;
- `evidence_classes`, `comparison_verdicts`;
- `pathways`.

**Pathway fields:**

- `id`, `title`, `research_question`, `technical_purpose`;
- `ontology_layers`, `evidence_release_ids`;
- `scope`: technical, temporal and geographic;
- `assumptions`, `limitations`;
- `steps`, `statements`, `next_evidence`;
- optional `comparisons` and `evidence_ladder`.

**Step fields:**

- `id`, `title`, `route`, `anchor`, `ontology_layer`;
- `evidence_class`, `relevance`;
- `release_id`, `finding_ids`, `source_ids`;
- `scope`, `limitations`;
- `unresolved_ids`, `next_evidence`.

## What the validator enforces

- **Pathway set.** Exactly three pathways, in the prescribed order.
- **Routes and anchors.** Every route is in the sitemap, every anchor resolves on its page, and that page is the one that presents the step's release.
- **Findings and sources.**
  - Every finding belongs to the step's release.
  - Every source is registered and cited by one of the step's findings.
  - Every source is listed in the page's own references.
- **Evidence classes.** A step's class must match the class of one of its findings. A statement's class must match the class of its basis.
- **Comparisons.** Each figure must appear in the finding it cites.
- **Evidence ladder.** It uses the governed evidence states. A site-level state cannot be marked reviewed without a registered site record.
- **Excluded content.**
  - No unpublished candidate relationship or node ID appears in the model.
  - No approval, score, ranking, confidence or edge field appears.
  - No score or verdict language appears.
- **Boundary rules.** The deployment inference boundaries apply to all prose.

## Cross-release checks (`scripts/validate_evidence_releases.py`)

`check_cross_release_consistency` requires three things:

- finding, unresolved and candidate IDs are unique across releases;
- a candidate edge is proposed only once;
- each reference page's sitemap `lastmod` is no earlier than its release's `as_of`.

The last check caught four stale pages, corrected in this release:

| Page | Old `lastmod` | Release presented | New `lastmod` |
| --- | --- | --- | --- |
| `/design-fabrication-packaging/` | 2026-07-03 | IDE-003 | 2026-11-09 |
| `/interconnects/` | 2026-07-03 | IDE-004 | 2026-11-09 |
| `/power-and-thermal-limits/` | 2026-07-03 | IDE-005 | 2026-11-10 |
| `/ai-chip-infrastructure/` | 2026-07-03 | IDE-006 | 2026-11-10 |
