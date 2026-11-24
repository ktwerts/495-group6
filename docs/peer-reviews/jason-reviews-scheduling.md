# Peer Review — Scheduling Module

- Reviewer — Jason Davis (`jdavis80`)
- Author — Diana Arango (`dianaarango03`)
- Review date — November 16, 2026, America/Chicago
- PR — https://github.com/ktwerts/495-group6/pull/6
- Submitted review — https://github.com/ktwerts/495-group6/pull/6#pullrequestreview-5932212591
- Primary corrective commit — https://github.com/ktwerts/495-group6/commit/e8a805d39e314355ee22b79ec6de59da17503f48
- Additional tests and route corrections — https://github.com/ktwerts/495-group6/commit/fcf0cfbf7ea0ade29d44d336a9a2b7e2395fce6f

## Findings and corrections

| Area | Finding | Correction or assessment |
|------|---------|--------------------------|
| Readability | Routes, database services, and pure constraint functions had clear responsibilities. Time handling needed consistency. | Preserved the structure and introduced parsed-time comparisons. |
| Security | Manager-only routes and parameterized SQL were present. Route-level permission tests were requested. | Added route tests and reused shared JSON validation. |
| Performance | Distinct staff counting was performed in SQLite. The route did not pass optional date filters to the service. | Retained database aggregation and connected date filters to the route with tests. |
| Integration | The staff-count query filtered on scheduled, although the schema stored assigned. Assigned employees were therefore counted as zero. | Changed the filter to assigned and added a regression test for distinct employees and excluded statuses. |
| Integration | Single-digit hours could cause a database constraint failure or missed overlap detection. | Normalized stored times to HH:MM and compared parsed times. Added regression tests. |
| Documentation | GET shifts was still marked as a stub, and POST shifts was undocumented. | Documented implemented endpoints, shift responses, validation, and error codes. |

## Verification and review status

The primary corrective commit changes the staff-count filter, normalizes
stored times, updates constraint comparisons, and adds regression tests.
The additional commit adds route tests and date-filter handling.

Jason submitted the review with GitHub state COMMENTED. No subsequent
review approval or explicit reviewer confirmation is recorded. The PR
merged on November 17, 2026, America/Chicago. Corrective commits provide
implementation evidence; follow-up reviewer verification remains an
evidence gap.

## Subsequent Alpha work

This review covered the initial Scheduling implementation. Absence
recording, replacement selection, manager approval, and their end-to-end
Forecasting test were subsequently implemented in PR #11. Weekly-hour
configuration followed in PR #12.