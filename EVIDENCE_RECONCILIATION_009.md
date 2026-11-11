# IDE-009: Evidence Reconciliation and Reference Synchronization

- **Record:** [`data/evidence-reconciliations-009.json`](data/evidence-reconciliations-009.json), with one entry for each of the 11 register issues.
- **Validator:** `scripts/validate_evidence_reconciliations.py`, run by `validate_all.py`.
- **Tests:** `tests/test_evidence_reconciliation.py`.
- **Public view:** `/sources/#reconciliation`. The changed pathway steps and comparisons link to it.

Each entry keeps five states separate:

- evidence reviewed;
- interpretation changed;
- public pages synchronized;
- pathway model synchronized;
- conflict still open.

It lists the exact old and new public text and pathway values. The validator fails if a page still carries the old text or lacks the new text, or if a pathway value differs from the record.

## Outcomes

| Issue | Decision | Result |
| --- | --- | --- |
| MI300X Infinity Fabric | applied; reopened | AMD states 896 GB/s is bidirectional and gives seven 128 GB/s links per GPU. The 2023 platform data sheet labels the figure a ring-of-8 aggregate. The 2025 CDNA 4 edition (PID#2258402-C, 10/1/2025) is reported in editorial review to state it per GPU OAM module in endnote MI350-007. The 2026 edition served now omits that endnote, and no stable copy of the 2025 edition could be retrieved from here (archive.org unreachable), so the 2025 statement is recorded as *pending version verification*. None of these figures is measured throughput. The IDE-008 "resolved" state is reopened as `requires_reassessment`. |
| Rubin memory bandwidth | applied (references only) | `/hbm-memory/` already presented both figures correctly; only its reference note was corrected. The HGX page (22 TB/s) is registered. The conflict stays open. |
| NVLink 6 per GPU | applied | The current HGX (3.6 TB/s) and Vera Rubin NVL72 (3 TB/s) pages are added to `/interconnects/`. The conflict stays open. |
| HBM export controls | applied | Public text now cites the current eCFR 742.6 and 740.25 and states that other provisions were not reviewed. State: `missing_primary_evidence`. |
| Other seven issues | unnecessary or deferred | No new primary evidence; the public references already present the uncertainty. |

## Fail-closed validation

The reconciliation record is required:

- `validate_evidence_reconciliations.py` fails, and `validate_all.py` with it, when the record is missing.
- `render_evidence_maintenance.py` refuses to render `/sources/` without the record.

Tests cover all three.

## Registry

Three sources were added:

- `amd-instinct-mi300x-platform-data-sheet-2023`
- `amd-cdna4-white-paper-2025`
- `nvidia-hgx-platform-product-page-2026`

A second inspection run, `ide-009-2026-11-11`, covers the 13 sources cited by the four reconciliations. That run also checks register and reconciliation quotes, and the 2026-11-10 records are kept.

## Historical releases

Releases 001–006 are unchanged. Two earlier tests asserted the superseded wording; they now assert the reconciled boundary:

- `test_interconnect_evidence_release`, which still checks that the 896 GB/s scope is not promoted to a vendor-confirmed per-GPU figure;
- `test_evidence_maintenance`, which now expects the reopened state and the appended history.
