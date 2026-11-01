# Dependency Evidence Atlas — v0.1.0

## Purpose

The Atlas is a machine-readable, source-linked structure for understanding dependencies across AI chips and compute systems. It complements the existing self-reported Chip Dependency Map Engine rather than treating visitor answers as verified evidence.

**Source of truth:** `data/dependency-atlas.json`. The Atlas initially contains the eight governed ontology-layer nodes and **zero evidence-backed relationships**. This is an honest scaffold, not a completed supply-chain map or operational assessment.

## Relationship contract

Each future entry in `relationships` MUST contain:

| Field | Requirement |
| --- | --- |
| `id`, `from`, `to` | Unique edge ID; both endpoints must be existing, distinct node IDs |
| `relation_type` | One of `requires`, `integrates_with`, `constrained_by`, `governed_by`, `enables` |
| `statement` | A narrow, independently reviewable explanation of the relationship |
| `claim_class` | `verified_fact`, `attributed_statement` or `bounded_analysis` |
| `evidence` | At least one `{ "source_id": "...", "supported_claim_type": "..." }`; every source must be `active` in the existing registry and must allow that claim type |
| `geographic_scope`, `temporal_scope` | Explicit limits; a company disclosure must not become a general industry finding |
| `as_of`, `reviewed_at`, `review_owner` | Valid dates and accountable human review |
| `confidence` | `high`, `medium` or `low`, assessed from the actual evidence rather than the publisher name |
| `limitations` | Non-empty list recording unknowns, limitations and material conflicts |

Nodes may be `ontology_layer`, `technology`, `capability`, `infrastructure` or `policy`. Every node declares one or more of the existing eight ontology layers. The existing eight layer nodes must remain present and correctly mapped.

`status: foundation` permits a structure with zero supported edges. `status: evidence_backed` requires at least one validated, reviewed edge. A new edge is **never** made valid simply by copying a source ID: review must verify that the exact passage substantiates the statement within the declared scope and date.

## Governance and separation

- `data/source-registry.json` remains the only registry of approved source metadata.
- `data/chip-dependency-model.json` and the existing client-side diagnostic remain unchanged.
- AEC-CS-001 remains the interpretation standard. The Atlas does not revise it or assign an overall status to a company or country.
- Registry metadata validation is necessary but does not independently verify the truth of an edge. Human claim-level review remains required.
- Unknown, outdated, unpublished, pending-review or retired evidence must never silently become a published relation.
- Do not populate speculative company, capacity, availability or supplier edges merely to fill out the graph.

## How to add a relationship

1. Read the primary source and verify its exact relevant claim, dates and scope.
2. Register or review the original source in `data/source-registry.json`.
3. Add missing nodes (stable IDs, type, ontology layers, non-promotional description).
4. Add the edge with an appropriate supported claim type, explicit reviewer, dates, evidence and limitations.
5. Run `python scripts/validate_all.py`, `python scripts/validate_public_launch.py` and `python -m unittest discover -s tests`.
6. Open a PR. Review the actual text of every claim against each primary source before approval.

## Fail-closed publishing

`.github/workflows/validate-and-deploy.yml` runs all repository validators and regression tests on PRs and on `main`. The deploy job is dependent on successful validation and is skipped for PRs.

**Critical one-time configuration:** GitHub Pages currently deploys from the `main` branch. Switch **Settings → Pages → Build and deployment → Source** to **GitHub Actions** before considering the workflow a true deployment gate. Configure a branch ruleset requiring the validation check and approved review before merges, and restrict direct pushes. Until that configuration is applied, the existing branch-based Pages publisher can still deploy an invalid push, despite a failing new workflow. This repository change alone cannot enforce that external setting.

The Atlas is released as machine-readable groundwork, not an implied endorsement, forecast, or verified supplier database.
