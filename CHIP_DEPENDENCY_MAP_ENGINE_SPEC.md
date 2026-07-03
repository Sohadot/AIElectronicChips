# Chip Dependency Map Engine v1.0.0

- **Engine ID:** AEC-CDM-ENGINE-001
- **Version:** 1.0.0
- **Status:** Active
- **Conforms to:** `CHIP_DEPENDENCY_MAP_MODEL.md` (AEC-CDM-001 v1.0.0),
  `COMPUTE_SOVEREIGNTY_STANDARD.md` (AEC-CS-001 v1.0.0),
  `CLAIM_BOUNDARY_MATRIX.md`

## Purpose

This document specifies the first operational Chip Dependency Map tool: a
fully static, client-side, rules-based instrument at `/chip-dependency-map/`
that takes a visitor's own structured answers to the twelve governed
diagnostic questions in `data/chip-dependency-model.json` and returns a
bounded, deterministic preview — never a score, ranking, or entity finding.

## Why This Is Not a Dependency Record

`DEPENDENCY_RECORD_SCHEMA.md` governs dependency records: evidence-backed
statements about a real, declared entity, produced by an analyst following
`SOURCE_POLICY.md`. This engine does not produce dependency records. A
visitor's self-selected answer is not attributed evidence — it is exactly
the "diagnostic question response" that `CHIP_DEPENDENCY_MAP_MODEL.md`'s Map
Interpretation Rule 4 already names: "a diagnostic response or state label is
not itself a finding without attributed evidence."

For the same reason, this engine's output must **not** use the five
Dependency States (Direct, Layered, Constrained, Opaque, Not Assessable).
Those states require source-backed attribution per layer
(`CHIP_DEPENDENCY_MAP_MODEL.md`, "Evidence required" for each state) that a
self-service form cannot supply. Using them here would misrepresent
unverified self-report as governed classification — exactly what the Standard
and Model prohibit.

## What the Engine Does

- collects a visitor's own answers to the twelve governed diagnostic
  questions, each answered with one of the model's five `answer_options`
  (`controlled`, `accessible`, `constrained`, `unknown`, `not_applicable`);
- runs entirely in the browser; no data is transmitted, stored, or logged
  anywhere;
- deterministically maps the answer set to: touched ontology layers, raised
  exposure types, one bounded confidence label, and candidate next governed
  artifact formats — the exact four output fields already authorized in
  `ASSET_INTELLIGENCE_FACTORY_PLAN.md`'s First Tool Boundary;
- links every output field to its governing reference page;
- displays a persistent notice that the output is a self-reported,
  unverified preview, not a dependency record, finding, score, or ranking.

## What the Engine Does Not Do

- it does not collect, transmit, save, or analyze any personal or entity
  data — there is no server, no storage, no analytics on this page;
- it does not assign a Dependency State, sovereignty status, or numeric
  score;
- it does not name, infer, or imply anything about a specific company,
  country, or product;
- it does not present its output as a recommendation to buy, invest,
  deploy, or act;
- it does not report `high` confidence under any input combination — high
  confidence requires attributed, reviewed evidence that only the governed
  brief/audit production pipeline (`ASSET_INTELLIGENCE_FACTORY_PLAN.md`
  Production Pipeline) can supply.

## Input

The visitor answers as many of the twelve questions
(`data/chip-dependency-model.json` → `questions`) as apply, each with one of:
`controlled`, `accessible`, `constrained`, `unknown`, `not_applicable`.
Unanswered questions are treated as `not_applicable`. No free-text, name, or
identifying field is collected.

## Deterministic Processing Rules

Let `answered` be the questions with an answer other than `not_applicable`.

### 1. Layers touched

The union of `layers` across all `answered` questions.

### 2. Exposure types raised

For each `answered` question with answer `constrained` or `unknown`, add its
`exposure_types` to the raised set. Questions answered `controlled` or
`accessible` raise no exposure type — a self-reported absence of a
constraint is not itself evidence of exposure and must not be flagged as
one.

### 3. Confidence label

Let `n = |answered|`, `u = count(answer == unknown)`,
`c = count(answer == constrained)`.

- `n == 0` → **Insufficient**
- `u / n >= 0.5` → **Insufficient**
- `u > 0` or `c / n >= 0.5` → **Low**
- otherwise (majority `controlled`/`accessible`, some or no `constrained`) → **Medium**

**Medium is the ceiling.** No input combination may produce **High** — that
label is reserved for evidence-reviewed governed output, never for
unattributed self-report.

### 4. Candidate next governed artifact formats

Tally `suggested_artifacts` across all `answered` questions with answer
`constrained` or `unknown` (the same set used for exposure types). Return the
one or two most frequent artifact IDs, resolved to their names and
boundaries in `data/chip-dependency-model.json` → `artifact_boundaries`. If
no question was answered `constrained` or `unknown`, return no artifact
suggestion — direct the visitor to the reference layer instead of a
commercial pathway, since the model must never manufacture a reason to
upsell.

## Output Contract

The rendered result must show, per Map Interpretation Rules 3 and 5:

- the confidence label with its plain-language meaning;
- touched layers, each linking to its ontology reference route;
- raised exposure types, grouped by layer, each with a one-line definition;
- unanswered/`not_applicable` layers shown explicitly as not assessed by this
  preview, never silently omitted;
- candidate artifact format(s), if any, linking to `/strategic-availability/`,
  worded as a classification hint, not a recommendation;
- a persistent boundary notice (see below).

## Mandatory Boundary Notice

Every result view must display, unconditionally:

> This is a self-reported, unverified preview of your own answers. It creates
> no dependency record and is not saved, transmitted, or stored. It is not a
> score, ranking, sovereignty assignment, or governed finding, and it says
> nothing about any specific company, country, or product.

## Reference Linkage

| Output field | Links to |
| --- | --- |
| Each touched layer | Its route from `COMPUTE_SOVEREIGNTY_ONTOLOGY.md` (e.g. `/hbm-memory/`) |
| Confidence label | `/methodology/` |
| Candidate artifact format | `/strategic-availability/` |
| Full model | `CHIP_DEPENDENCY_MAP_MODEL.md` reference on `/chip-dependency-map/` itself |

## Versioning Notes

- **v1.0.0** implements the First Tool Boundary already authorized in
  `ASSET_INTELLIGENCE_FACTORY_PLAN.md` without modifying
  `data/chip-dependency-model.json`'s controlled vocabularies. It consumes
  that file's `questions`, `layers`, `exposure_types`, `confidence_levels`,
  and `artifact_boundaries` as-is.
- Changes to the deterministic rules in this document require a
  `DECISION_LOG.md` entry, matching governance for every other model change
  in this repository.
- Entity-specific assessment, Dependency State assignment, and paid brief
  production remain out of scope for this engine and require the governed,
  evidence-reviewed pipeline in `ASSET_INTELLIGENCE_FACTORY_PLAN.md`.
