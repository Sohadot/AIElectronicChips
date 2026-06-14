# Dependency Record Schema

## Purpose

A dependency record is the smallest governed unit used by a future Compute
Dependency Exposure Map. It records a bounded finding and the evidence needed
to interpret it. This document describes the schema; it does not contain
operational records.

## Required Fields

| Field | Type | Rule |
| --- | --- | --- |
| `record_id` | string | Stable identifier unique within the assessment. |
| `assessment_scope` | string | Declared subject, purpose, and boundary. |
| `as_of` | date | Date through which the record is supported. |
| `layers` | array | One or more valid model layers. |
| `dependency` | string | Specific capability, access condition, or operating requirement. |
| `exposure_types` | array | One or more valid model exposure types. |
| `finding` | string | Bounded statement supported by cited evidence. |
| `confidence` | string | `high`, `medium`, `low`, or `insufficient`. |
| `evidence` | array | Source records supporting the finding. |
| `limitations` | array | Known gaps, conflicts, and scope constraints. |
| `review_owner` | string | Person or governed process responsible for review. |

## Optional Fields

| Field | Type | Purpose |
| --- | --- | --- |
| `question_ids` | array | Diagnostic questions that led to investigation. |
| `substitutability` | string | `available`, `constrained`, `unavailable`, or `unknown`. |
| `criticality` | string | `low`, `moderate`, `high`, or `unknown` within the declared scope. |
| `suggested_artifact` | string | One valid artifact classification hint from the model; not a recommendation. |
| `next_review_date` | date | Scheduled review for changing conditions. |

## Evidence Record

Each item in `evidence` should contain:

- `title`;
- `publisher`;
- `canonical_url`;
- `publication_or_effective_date`;
- `accessed_date`;
- `source_type`;
- `supported_claim`;
- `scope`;
- optional `archive_url`.

## Confidence Rule

Confidence describes evidence quality and completeness, not rhetorical
certainty. An `insufficient` record may document an evidence gap but must not
support an operational finding.

## Example Shape

```json
{
  "record_id": "example-record",
  "assessment_scope": "Illustrative schema only",
  "as_of": "YYYY-MM-DD",
  "layers": ["memory"],
  "dependency": "Required memory access",
  "exposure_types": ["access_exposure", "evidence_exposure"],
  "finding": "No operational finding; evidence is insufficient.",
  "confidence": "insufficient",
  "evidence": [],
  "limitations": ["Illustrative record without entity evidence."],
  "review_owner": "Unassigned"
}
```
