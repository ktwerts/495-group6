# Unit 5 revision evidence

This record maps the professor's feedback to implementation and verification.
PRs #13 and #14 remain open for teammate review. Final release verification is
pending their merge and any subsequent changes.

## Feedback and corrective work

| Feedback | Corrective work | Evidence and status |
|----------|-----------------|---------------------|
| Complete absence management and replacement coverage | Full-day absence recording reopens assigned shifts. Recommendations apply active status, qualifications, availability, overlap, absence, and weekly-hour checks. Manager approval rechecks eligibility and updates assignments. | [PR #11](https://github.com/ktwerts/495-group6/pull/11), merged. Browser checks covered successful coverage and no eligible replacement. |
| Prove module integration | The seeded integration test records an absence, retrieves recommendations, approves coverage, and verifies Forecasting's scheduled count and gap before and after changes. | `tests/test_integration.py::test_approved_replacement_closes_forecast_gap`. Uses actual API calls and staffing counts. |
| Complete skipped workflow and performance tests | Implemented Scheduling workflow tests, the replacement integration test, and the 50-employee recommendation benchmark. | `tests/test_scheduling.py`, `tests/test_integration.py`, and `tests/test_performance.py`. One employee self-service test remains explicitly deferred. |
| Supply supported-version CI evidence | Current main passed Ruff, formatting, Bandit, dependency audit, Python 3.11–3.13 tests, and build smoke checks. | [Main run](https://github.com/ktwerts/495-group6/actions/runs/45318239921), commit `e111d583a3cd98245ec0d630f10a3bf5c66a91b0`. Final post-merge run still required. |
| Preserve completed peer-review records | Four records link original reviews, required corrections, corrective commits, and verification limitations. Assignment table includes all three teammates. | [PR #14](https://github.com/ktwerts/495-group6/pull/14), open. See [review assignments](peer-reviews/README.md). Follow-up approvals are absent from the original reviewed PRs. |
| Mitigate TD-2 | Managers can configure and edit weekly limits. Scheduling enforces them. Edits below assigned hours in the current or future weeks return 409. | [PR #12](https://github.com/ktwerts/495-group6/pull/12), merged. API, Scheduling, boundary, permission, and browser checks completed. |
| Mitigate TD-1 | Added failed-login limits, JSON 429 responses, expiry recovery, and IP isolation tests. | [PR #13](https://github.com/ktwerts/495-group6/pull/13), open; [successful PR run](https://github.com/ktwerts/495-group6/actions/runs/45319767027). In-memory counter limitations remain documented. |
| Evaluate TD-3 using representative data | Synthetic-data model evaluation and weekday-baseline comparison exist. Representative real/public staffing evaluation is outstanding. | [AI feature documentation](ai-feature.md) and [debt log](technical-debt.md). Synthetic performance does not establish workplace accuracy. |

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
7. After PR #13 merges, demonstrate five failed logins followed by a 429 response.
   Wait for expiry before attempting the correct credentials from that IP.

## Submission completion checklist

- [ ] PR #13 merged after its checks and available review feedback are assessed.
- [ ] PR #14, including this evidence document, merged after its checks pass.
- [ ] Final submitted main commit recorded here.
- [ ] Successful CI link for that exact commit recorded here.
- [ ] Test counts, coverage, and skips recorded for each of Python 3.11, 3.12, and 3.13 from CI summaries.
- [ ] Build and security results confirmed for that run; reports downloaded or linked.
- [ ] Final demo completed against the submitted commit.
- [ ] Each individual's report verified at exactly 250 words and submitted through the LMS.
- [ ] Repository copies of available reports included; missing reports identified.
- [ ] Actual reviewer re-verification linked where supplied; absent approvals remain identified.
- [ ] Submission archive and repository reference point to the same final revision.

Final submitted commit: pending.

Final CI run: pending.
