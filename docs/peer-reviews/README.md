# Peer Reviews

Each team member reviews one teammate's module. The review itself happens on GitHub as a
PR review with inline comments. A copy goes here so it's part of the submitted repository.

## Process

1. The author opens a PR for their module (or a "review" PR covering the module's current code).
2. The reviewer copies [../peer-review-template.md](../peer-review-template.md) to this folder as
   `<reviewer>-reviews-<module>.md`, for example `alex-reviews-forecasting.md`.
3. The reviewer leaves inline comments on the PR, fills in the checklist and summary table here,
   and links the PR.
4. The author addresses each finding in commits that reference it, for example
   `fix(forecasting): validate days param (review #3)`.
5. The reviewer re-checks the fixes, marks findings resolved, and approves the PR.
6. New technical debt found during review goes into [../technical-debt.md](../technical-debt.md).

## Assignments

| Reviewer | Reviews module | Author | PR | Status |
|----------|----------------|--------|----|--------|
| Kaden | Employees | Jason | [#2](https://github.com/ktwerts/495-group6/pull/2) | Review and corrections documented; follow-up approval absent |
| Jason | Forecast features | Kaden | [#4](https://github.com/ktwerts/495-group6/pull/4) | Review and corrections documented; follow-up approval absent |
| Jason | Scheduling | Diana | [#6](https://github.com/ktwerts/495-group6/pull/6) | Review and corrections documented; follow-up approval absent |
| Diana | Staffing history | Kaden | [#3](https://github.com/ktwerts/495-group6/pull/3) | Review and corrections documented; follow-up approval absent |