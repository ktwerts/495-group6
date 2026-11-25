# Unit 5 revision evidence

This record maps the professor's feedback to implementation and verification.
PRs #13 and #14 have been merged. Additional peer-review documentation
and individual refinement report updates were completed on November 24, 2026.
Final release verification must correspond to the final submitted commit.

## Feedback and corrective work

| Feedback | Corrective work | Evidence and status |
|----------|-----------------|---------------------|
| Complete absence management and replacement coverage | Full-day absence recording reopens assigned shifts. Recommendations apply active status, qualifications, availability, overlap, absence, and weekly-hour checks. Manager approval rechecks eligibility and updates assignments. | [PR #11](https://github.com/ktwerts/495-group6/pull/11), merged. Browser checks covered successful coverage and no eligible replacement. |
| Prove module integration | The seeded integration test records an absence, retrieves recommendations, approves coverage, and verifies Forecasting's scheduled count and gap before and after changes. | `tests/test_integration.py::test_approved_replacement_closes_forecast_gap`. Uses actual API calls and staffing counts. |
| Complete skipped workflow and performance tests | Implemented Scheduling workflow tests, the replacement integration test, and the 50-employee recommendation benchmark. | `tests/test_scheduling.py`, `tests/test_integration.py`, and `tests/test_performance.py`. One employee self-service test remains explicitly deferred. |
| Supply supported-version CI evidence | Main at commit `cd5d949` passed Ruff, formatting, Bandit, dependency audit, Python 3.11–3.13 tests, and build smoke checks. | [CI run #108](https://github.com/ktwerts/495-group6/actions/runs/45521937786). Per-version results under [GitHub Actions CI results](#github-actions-ci-results). |
| Preserve completed peer-review records | Four records link original reviews, required corrections, corrective commits, and verification limitations. Assignment table includes all three teammates. Diana completed retrospective verification on November 24 and posted a follow-up confirmation on PR #3. | [PR #14](https://github.com/ktwerts/495-group6/pull/14), merged. See [review assignments](peer-reviews/README.md) and [Diana's review record](peer-reviews/diana-reviews-staffing-history.md). Original pre-merge approvals remain absent where documented. |
| Mitigate TD-2 | Managers can configure and edit weekly limits. Scheduling enforces them. Edits below assigned hours in the current or future weeks return 409. | [PR #12](https://github.com/ktwerts/495-group6/pull/12), merged. API, Scheduling, boundary, permission, and browser checks completed. |
| Mitigate TD-1 | Added failed-login limits, JSON 429 responses, expiry recovery, and IP isolation tests. | [PR #13](https://github.com/ktwerts/495-group6/pull/13), merged; [successful PR run](https://github.com/ktwerts/495-group6/actions/runs/45319767027). In-memory counter limitations remain documented. |
| Evaluate TD-3 using representative data | Synthetic-data model evaluation and weekday-baseline comparison exist. Representative real/public staffing evaluation is outstanding. | [AI feature documentation](ai-feature.md) and [debt log](technical-debt.md). Synthetic performance does not establish workplace accuracy. |

## GitHub Actions CI results

[CI run #108](https://github.com/ktwerts/495-group6/actions/runs/45521937786)
ran on a push to `main` at commit `cd5d949` and succeeded in every job. The test
numbers come from each job's summary; the JUnit and coverage reports are attached to
the run as the `test-reports-py3.11`, `test-reports-py3.12` and `test-reports-py3.13`
artifacts.

| Job | Python | Tests | Passed | Failures | Errors | Skipped | Line coverage |
|-----|--------|------:|-------:|---------:|-------:|--------:|--------------:|
| Tests | 3.11 | 229 | 228 | 0 | 0 | 1 | 97.2% |
| Tests | 3.12 | 229 | 228 | 0 | 0 | 1 | 97.2% |
| Tests | 3.13 | 229 | 228 | 0 | 0 | 1 | 97.2% |

| Job | Result |
|-----|--------|
| Lint (ruff) | Passed: `ruff check` and `ruff format --check` |
| Security scan | Passed: Bandit (`-ll`) reported no issues; pip-audit found no known vulnerabilities in `requirements.txt` |
| Build check (app boots + seeds) | Passed: seeds the database, logs in, loads every page, trains and reads the forecast, then runs the absence → recommendation → approval workflow; log ends `Smoke test OK` |

CI fails the test jobs below 80% coverage (`--cov-fail-under=80`).
[CI run #106](https://github.com/ktwerts/495-group6/actions/runs/45520719030) on
`1f81cb1` (the merge of PR #16) shows the same results.
Subsequent commits include refinement reports and peer-review documentation updates.

**Skipped tests.** `tests/test_scheduling.py`, `tests/test_integration.py` and
`tests/test_performance.py` contain no skips. The single skip in the suite is
`test_employee_can_only_view_own_record` in `tests/test_employees.py`: the Alpha
provides manager-only employee management, and the employee self-service record
endpoint it would test is deferred. Its skip reason states that scope.

## Local verification history

These results were recorded during development on local Python 3.14. They are
separate from the supported-version GitHub CI jobs and describe specific stages.

| Stage | Passed | Skipped | Coverage |
|-------|-------:|--------:|---------:|
| Completed absence workflow | 190 | 1 | 96.86% |
| Workflow plus configurable weekly hours | 210 | 1 | 96.98% |
| Login protection integrated with workflow and weekly hours | 214 | 1 | 97.01% |

The remaining test is `test_employee_can_only_view_own_record` in
`tests/test_employees.py`. The Alpha provides manager-only employee management;
the employee self-service record endpoint is deferred. Its skip reason states
that scope explicitly. Coverage output also omits fully covered files; that
display setting does not represent additional skipped tests.

## Reproducible demo

Use [the Alpha demo script](alpha-checklist.md). For a fresh demo database,
the seed command recreates tables and prints generated account passwords.
Never seed a database whose contents need preserving.

1. Sign in as manager and open Schedule and Forecast for the same date.
2. Record an assigned employee's full-day absence. Confirm their shifts reopen
   and the scheduled headcount decreases.
3. Request replacements. Confirm requesting candidates alone leaves staffing
   unchanged. Demonstrate a shift with no eligible candidates staying open.
4. For reproducible successful coverage, create two available demo employees
   and a shift without a required qualification. Assign the first, report their
   absence, select the second, and approve replacement coverage.
5. Refresh Schedule and Forecast. Confirm the replacement persists and the
   scheduled count recovers. A previously absent employee remains ineligible.
6. Edit a weekly-hour limit. Demonstrate a successful edit and a rejected
   reduction below already assigned hours, with explanatory feedback.
7. Demonstrate five failed logins followed by a 429 response.
   Wait for expiry before attempting the correct credentials from that IP.

## Individual refinement reports

Diana's revised individual Refinement Report documents her scheduling
implementation, peer-review corrections, technical debt analysis, and
retrospective verification of the staffing-history module.

- [Diana Arango's Refinement Report](refinement-reports/diana-arango.md)
- [Jason Davis's Refinement Report](refinement-reports/jason-davis.md)

Kaden's refinement report was previously added to the repository.

Diana completed retrospective verification on November 24, 2026, through
code inspection and review of five regression tests associated with corrective
commit `4427225`. A follow-up confirmation was posted on
[PR #3](https://github.com/ktwerts/495-group6/pull/3).
This verification occurred after the original merge and did not involve
independent test execution.

## Submission completion checklist

- [x] PR #13 merged.
- [x] PR #14 merged.
- [ ] Final submitted main commit recorded here.
- [ ] Successful CI link for that exact commit recorded here.
- [x] Test counts, coverage, and skips recorded for each of Python 3.11, 3.12, and 3.13 from CI run #108.
- [x] Build and security results confirmed for CI run #108.
- [ ] Final demo completed against the submitted commit.
- [ ] Each individual's report verified at exactly 250 words and submitted through the LMS.
- [ ] All repository copies of individual reports confirmed.
- [x] Diana's retrospective peer-review verification documented and follow-up confirmation posted on PR #3.
- [ ] All remaining reviewer confirmations and verification limitations documented.
- [ ] Submission archive and repository reference point to the same final revision.

Previously verified commit: `cd5d949`.

Previously verified CI run: [CI run #108](https://github.com/ktwerts/495-group6/actions/runs/45521937786), succeeded.

The final submitted commit and corresponding CI run must be updated
after all remaining documentation changes are merged.
