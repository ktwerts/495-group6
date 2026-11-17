# Unit 5 Alpha Release Checklist

Who builds what, mapped to the rubric. Fill in names, tick items off as PRs merge, and keep
this file current.

## Already provided by the scaffold

- [x] App structure, environment config, SQLite connection, `flask seed`
- [x] Shared error handling (JSON 400/404/409/501) and input validation helpers
- [x] Login, password hashing, manager/employee roles (`@role_required`)
- [x] Base layout, CSS, JS helpers (`api`, `esc`, `formData`, `showMessage`, `showError`)
- [x] CI: lint and format, security scan, tests on 3 Python versions, startup smoke test
- [x] Contributing guide, PR template, peer review and refinement report templates

## Interface Designer: _name_

Module: **Employees** (`app/employees/`) + UI pages

- [ ] Design the `employees` and `availability` tables in `app/schema.sql`
- [ ] Implement `app/employees/service.py` (list, get, create, update/deactivate, availability)
- [ ] Add the employee endpoints in `routes.py`
- [ ] Build `templates/employees.html` (table plus add/edit form)
- [ ] Add sample employees and an employee-role login to `app/seed.py`
- [ ] Un-skip and complete `tests/test_employees.py`
- [ ] Write up all endpoints in `docs/api-spec.md`

## Lead Architect: _name_

Module: **Scheduling** (`app/scheduling/`) + system design

- [ ] Design the `shifts`, `absences` and `recommendations` tables in `app/schema.sql`
- [ ] Implement `constraints.py` (availability, qualification, overlap, and any rules you add)
- [ ] Implement `service.py` (shifts, absences, `count_scheduled_staff`, recommendations, manager approval)
- [ ] Add the scheduling endpoints, and build `templates/schedule.html`
- [ ] Show an employee their own shifts on the home page
- [ ] Add a week of sample shifts to `app/seed.py`
- [ ] Un-skip and complete `tests/test_scheduling.py`, plus the recommendations benchmark in `tests/test_performance.py`
- [ ] Keep `docs/architecture.md` (diagrams, module table, data model) current

## Integration Lead: _name_

Module: **Forecasting / AI** (`app/forecasting/`) + integration

- [x] Design the `staffing_history` table; generate sample history in `app/seed.py`
- [x] Implement `features.py` and `model.py` (train, evaluate against a baseline, predict, save/load)
- [x] Implement `service.py`: compare predictions with `scheduling.count_scheduled_staff()`
- [x] Add a retrain endpoint, and build `templates/forecast.html`
- [x] Un-skip and complete `tests/test_forecasting.py`, plus the forecast benchmark in `tests/test_performance.py`
- [x] Write `docs/ai-feature.md`
- [x] Extend the CI smoke test in `.github/workflows/ci.yml` to check the forecast endpoint

## Everyone

**Integration (Multi-Module Integration, 40 pts)**

- [ ] Agree on the service functions each module exposes, and record them in `architecture.md`
- [ ] Write at least one end-to-end test across modules (absence → recommend → approve → forecast)

**CI/CD (35 pts)**

- [ ] Turn on branch protection for `main` (see [CONTRIBUTING.md](../CONTRIBUTING.md))
- [ ] Every PR includes tests and has CI green before merge; keep coverage at 80% or above
- [ ] Screenshot a green CI run for the submission

**Peer review (35 pts)**

- [ ] Assign review pairs: each person reviews one teammate's module (A→B, B→C, C→A)
- [ ] Review as a GitHub PR review with inline comments, using the [checklist](peer-review-template.md)
- [ ] Save a copy in [peer-reviews/](peer-reviews/README.md); fix findings in commits that reference them

**Technical debt (30 pts)**

- [ ] Each person logs at least 2 debt items from their own module in [technical-debt.md](technical-debt.md)
- [ ] Each person resolves at least 1 and documents how (material for the report)
- [ ] Each person writes the 250-word [refinement report](refinement-report-template.md)

**Version control**

- [ ] Work only on feature branches merged by PR; no direct pushes to `main`
- [ ] Use Conventional Commit messages (`feat(scheduling): ...`)
- [ ] Every member has several merged PRs in the history

## Alpha demo script (fill in once features land)

1. Run `python -m flask --app run seed` against a fresh demo database, then
   `python run.py`. Sign in as `manager`. Use the generated manager password
   from the seed output or the value set in `SHIFTWISE_ADMIN_PASSWORD`.
2. Forecast page: point out the model's error next to the baseline's, then the days marked
   "Short by N". Press **Retrain model** and show the metrics refresh.
3. Schedule page: report an absence, find cover, approve: _TODO_
4. Show a blocked conflicting assignment (409): _TODO_
5. Sign out, then sign in as `employee`. Use the generated employee password
   from the seed output or the value set in `SHIFTWISE_EMPLOYEE_PASSWORD`.
   Verify that the home page shows **My Shifts** and the **employee** role.
6. GitHub Actions: all jobs green, plus the test report artifact
