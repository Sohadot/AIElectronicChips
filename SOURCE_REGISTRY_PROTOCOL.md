# Source Registry Protocol

## Purpose

The source registry records verified source metadata that may support future
reference pages, dependency records, briefs, and audits. Registration makes a
source discoverable; it does not turn the source into a finding or approve
every statement it contains.

## Source Hierarchy

Prefer sources in this order where practicable:

1. government rules, regulations, official notices, and official datasets;
2. company filings, audited statements, annual reports, and attributable
   official technical disclosures;
3. technical standards and peer-reviewed research;
4. official institutional reports with disclosed methodology.

Anonymous commentary, social posts, generated citations, unsourced
aggregations, and unattributable material are prohibited.

## Required Metadata

Every record must contain a stable ID, title, publisher, approved source type,
canonical URL, publication or effective date, access date, ontology layers,
supported claim types, geographic scope, temporal scope, confidence use,
limitations, and status.

## Status

- `active`: metadata and source identity have been reviewed; use remains
  claim-specific and governed.
- `pending_review`: useful official source whose detailed claim use, underlying
  document, or metadata requires further review.
- `retired`: retained for history but not eligible to support new findings.

Status does not describe whether the source's subject is favorable or reliable
in every context.

`official_technical_disclosure` records preserve attributable product,
architecture, integration, or engineering context that does not fit a filing
or technical-standard classification. They must remain attributed and cannot
establish market-wide availability, capacity, adoption, or supplier position.

## Freshness and Review

Every source must carry `accessed_at` and a temporal scope. Rules, policy,
capacity, ownership, access, and company disclosures must be reviewed before
reuse. A record should move to `pending_review` or `retired` when its canonical
source changes, its metadata becomes uncertain, or it is superseded.

## Supporting Dependency Records

A dependency record may cite a registered source only for a specific supported
claim within the source's geographic, temporal, and technical scope. The record
must still state its finding, confidence, limitations, and `as_of` date.

Multiple sources may be required. Registry presence never substitutes for claim
review under `CLAIM_POLICY.md` or interpretation under
`COMPUTE_SOVEREIGNTY_STANDARD.md`.

## Conflicts

Credible conflicts must be recorded and disclosed. Sources must not be averaged
away or selected solely because they support a preferred conclusion. An
unresolved material conflict may require `low` or `insufficient` confidence.

## Prohibited Uses

Registered sources must not be used to:

- create automatic findings, scores, rankings, or sovereignty assignments;
- imply current conditions from stale or historical evidence;
- infer entity-level exposure from general policy or industry material;
- present projections, announcements, plans, or recommendations as operating
  facts;
- create affiliate, product-review, or promotional conclusions;
- conceal source conflicts, limitations, or status.
