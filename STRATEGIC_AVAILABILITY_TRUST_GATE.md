# Strategic Availability Trust Gate

## Purpose

This trust gate defines the acceptance rules for any commercial or strategic
availability surface on AIElectronicChips.com. The commercial layer is accepted
only when it preserves trust, neutrality, methodological restraint, and
strategic acquisition value.

No strategic availability change may ship without passing this gate and the
automated checks in `scripts/validate_all.py`.

## Acceptance Principle

The public site must remain a governed reference asset first. Strategic
availability extends that asset into serious institutional pathways. It must
not present the asset as a small service business, a domain sale page, or a
conclusion-for-hire product.

## Prohibited on Any Commercial or Strategic Availability Surface

The following are prohibited in public copy, offering definitions, inquiry
flows, and deliverable promises:

- prices, quotes, or public pricing tables;
- checkout flows or self-serve purchase;
- outcome guarantees or implied certainty;
- certification claims or readiness certification;
- benchmark claims or league-table framing;
- sovereignty scores or maturity grades;
- public rankings or vendor league tables;
- vendor recommendations or purchase recommendations;
- investment advice;
- legal advice;
- procurement advice;
- national-security advice;
- sponsored conclusions or paid ranking influence;
- affiliate framing or product-review framing;
- predetermined findings or purchasable verdicts;
- claims that any company, country, chip, vendor, or government is sovereign or
  non-sovereign.

These prohibitions apply equally to public pages, offering metadata, inquiry
copy, and commissioned deliverables.

## Permitted Strategic Availability Surface

The following are permitted when bounded by evidence, scope, confidence, and
written governance:

- scoped **Compute Sovereignty Briefs**;
- governed **Chip Dependency Audits**;
- **Premium Reference Dossiers** for institutional use;
- **ontology or methodology licensing** under written terms;
- **strategic acquisition inquiry** for institutions evaluating the asset;
- serious institutional inquiry through **agent@sohadot.com**.

Permitted pathways must remain visibly distinct from excluded commercial models.
They must not be presented as fast, cheap, or conclusion-ready services.

## Required Trust Properties

Any accepted commercial surface must:

- preserve the same source and claim standards as public reference material;
- disclose material commercial relationships where relevant;
- state evidence, confidence, limitations, and as-of requirements;
- allow clients to define questions without buying predetermined conclusions;
- keep acquisition inquiry framed as strategic fit, not distressed sale;
- avoid language that makes the asset appear needy, promotional, or desperate
  for revenue.

## Inquiry Standard

Qualified inquiry is the only permitted public conversion path.

The inquiry channel must:

- use a serious subject line such as `AIElectronicChips.com — Strategic Inquiry`;
- direct to `agent@sohadot.com`;
- request pathway, scope, entity or topic, time horizon, layers, and intended use;
- avoid checkout, pricing, or instant-purchase language.

Vague, promotional, affiliate-seeking, or conclusion-seeking contacts may be
declined.

## Release Gate

A strategic availability change passes this gate only if:

1. `scripts/validate_all.py` passes;
2. `COMMERCIAL_TRUST_AUDIT.md` records no unresolved high-risk finding;
3. the five offering IDs remain unchanged unless explicitly authorized;
4. `strategic-availability/index.html` remains aligned with
   `data/strategic-offerings.json`;
5. no new JavaScript or external dependencies are introduced.

## Related Documents

- [Commercial Trust Audit](COMMERCIAL_TRUST_AUDIT.md)
- [Strategic Availability Protocol](STRATEGIC_AVAILABILITY_PROTOCOL.md)
- [Premium Brief Boundary](PREMIUM_BRIEF_BOUNDARY.md)
- [Buyer Logic](BUYER_LOGIC.md)
- [Monetization Boundary](MONETIZATION_BOUNDARY.md)
