# Peer Review — Staffing History

- Reviewer — Diana Arango (`dianaarango03`)
- Author — Kaden (`ktwerts`)
- Review date — November 16, 2026, America/Chicago
- PR — https://github.com/ktwerts/495-group6/pull/3
- Submitted review — https://github.com/ktwerts/495-group6/pull/3#pullrequestreview-5931155743
- Corrective commit — https://github.com/ktwerts/495-group6/commit/4427225c7f39a2d15356c3a57e5631dac7ad3f1d

## Findings and corrections

| Area | Finding | Correction or assessment |
|------|---------|--------------------------|
| Readability | Sample-data generation was separated from database functions, making the code easier to maintain and test. | Retained this structure. |
| Security and integrity | Parameterized SQL and database constraints protected staffing values. Tests covered invalid inputs and duplicate dates. | Preserved validation while introducing repeat-seeding support. |
| Reliability and integration | Seeding could fail when staffing-history dates already existed. | Added skip_existing support so seeding preserves existing dates and inserts new ones. |
| Performance | The original review did not explicitly assess performance. | Record this as a limitation of the review's coverage. |
| Documentation | The original review did not explicitly assess documentation completeness. | Record this as a limitation of the review's coverage. |

## Verification and review status

The corrective commit `4427225` addresses repeat-seeding failures by implementing `skip_existing=True`, preserving existing records and inserting only new dates.

On November 24, 2026, Diana conducted a retrospective review of the corrective commit and the five additional regression tests. These tests cover duplicate prevention, invalid staffing values, repeated seeding, missing dates, and repeated execution of the Flask seed command.

Diana posted a follow-up confirmation on PR #3, acknowledging that the original concern was addressed through the corrective implementation and regression test coverage.

The original PR merged on November 17, 2026. The follow-up verification was completed after the merge and was based on code inspection and test coverage rather than independent test execution.

## Technical debt

The repeat-seeding issue and its mitigation are recorded as TD-4 in
docs/technical-debt.md. This fix improves demo-data reliability.
Evaluation on representative real staffing data remains separate
work under TD-3.
