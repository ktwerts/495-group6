# Peer Review — Employees Module

- Reviewer — Kaden (`ktwerts`)
- Author — Jason Davis (`jdavis80`)
- Review date — November 16, 2026
- PR — https://github.com/ktwerts/495-group6/pull/2
- Original review — https://github.com/ktwerts/495-group6/pull/2#issuecomment-6921685153
- Corrective commit — https://github.com/ktwerts/495-group6/commit/5ed6d0115e08e46b9f4a83d0cd2dda1eb4635de1
- Author's response — https://github.com/ktwerts/495-group6/pull/2#issuecomment-6936127310

## Review findings and corrections

| Area | Finding | Correction or follow-up |
|------|---------|-------------------------|
| Readability | Clear names and route-to-service separation; some scaffold comments were outdated. | Preserved the existing structure. Comment cleanup was identified for follow-up. |
| Security | Employee names and positions lacked length limits. | Added 100-character limits after trimming, browser restrictions, and regression tests. |
| Configuration | The employee seed-password setting was missing from the example environment file. | Added SHIFTWISE_EMPLOYEE_PASSWORD to .env.example. |
| Performance | Availability was loaded in one batch, avoiding N+1 queries, but included inactive employees' slots. | Filtering inactive employees' slots and pagination remained follow-up opportunities. |
| Integration | Exact duplicates were rejected, but overlapping availability was accepted. | Added overlap rejection for the same employee and weekday, retaining support for adjacent slots. |
| Testing | Documented 404 and 409 availability responses lacked tests. | Added tests for unknown employees, duplicates, and overlaps. |
| Usability | Managers could save slots without seeing them in the table. | Added an Availability column that updates after successful saves. |
| Documentation | API documentation needed to reflect validation changes. | Updated the specification with length limits and overlap behavior. |

## Verification and review status

The corrective commit contains the five required fixes. Jason reported
completing them in the linked response. Automated tests and browser checks
were performed during development.

The PR merged on November 17, 2026. The review was submitted as a PR
conversation comment. GitHub has no formal approval or follow-up reviewer
confirmation recorded for the corrective commit. Reviewer re-verification
remains an evidence gap.

## Technical debt

The original review identified the fixed 40-hour employee limit as TD-2.
Configurable creation and editing were subsequently implemented in PR #12.
That later improvement is separate from the original corrective commit.