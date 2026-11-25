# ShiftWise AI: Intelligent Workforce Scheduling

ShiftWise AI helps managers anticipate staffing needs, avoid scheduling conflicts, and cover
unexpected absences. A scikit-learn model predicts how many staff each day needs. When someone
calls out, the system recommends replacements who meet availability and qualification rules,
and a manager approves the change before it takes effect.

**Stack:** Python 3.11+ · Flask · SQLite · scikit-learn · HTML/CSS/JavaScript · GitHub Actions

> **Status: Alpha revision.** Employee management, shift assignment, and AI
> forecasting work with seeded demo data. Managers can record full-day absences,
> find eligible replacements, and approve coverage. Integration tests verify that
> absences and replacement approvals update Forecasting's scheduled staffing counts.
## Team roles

| Role | Owner | Module | Docs |
|------|-------|--------|------|
| Lead Architect | Diana Arango | Scheduling (`app/scheduling/`) and database schema | [architecture.md](docs/architecture.md) |
| Interface Designer | Jason Davis | Employees (`app/employees/`) and UI pages | [api-spec.md](docs/api-spec.md) |
| Integration Lead | Kaden Werts | Forecasting / AI (`app/forecasting/`) | [ai-feature.md](docs/ai-feature.md) |

## Features

| Module | What works |
|--------|------------|
| **Auth** | Login, hashed passwords, manager and employee roles. Manager pages and APIs return 403 for employees |
| **Employees** | List and add employees, record weekly availability (overlapping slots are rejected) |
| **Scheduling** | Create, assign, and unassign shifts; record full-day absences; find eligible replacements; approve coverage. Assignment and approval enforce availability, qualifications, overlapping shifts, absences, active status, and weekly-hour limits. Rule violations return 409. |
| **Forecasting (AI)** | A scikit-learn random forest predicts staff needed per day, is scored against a weekday-average baseline, and compares each day with the staff actually scheduled. The Forecast page shows the gaps and can retrain the model |

How the modules connect: Scheduling asks Employees for availability before it assigns anyone,
and the forecast asks Scheduling how many people are assigned each day. Details are in
[architecture.md](docs/architecture.md) and [ai-feature.md](docs/ai-feature.md).

## Getting started

Requires Python 3.11 or newer.

```bash
git clone https://github.com/ktwerts/495-group6.git
cd 495-group6
python -m venv .venv
```

Activate the virtual environment, install dependencies and create your `.env`:

**Windows (PowerShell)**

```powershell
.venv\Scripts\Activate.ps1
pip install -r requirements-dev.txt
copy .env.example .env
```

**macOS / Linux**

```bash
source .venv/bin/activate
pip install -r requirements-dev.txt
cp .env.example .env
```

In `.env`, set `SHIFTWISE_SECRET_KEY` to a long random string so logins survive a restart
(`python -c "import secrets; print(secrets.token_hex(32))"` makes one). You can also set
`SHIFTWISE_ADMIN_PASSWORD` and `SHIFTWISE_EMPLOYEE_PASSWORD`; if you leave them blank,
seeding generates passwords and prints them.

Load the demo data and start the app:

```bash
flask --app run seed     # resets the database and loads demo data
python run.py            # http://127.0.0.1:5000
```

`flask --app run seed` wipes and reloads everything each time it runs. Stop the server with
Ctrl+C.

**After every `git pull`**, reinstall dependencies, because new packages (such as
Flask-Limiter) are added over time. If `app/schema.sql` changed, reseed too:

```bash
pip install -r requirements-dev.txt
flask --app run seed     # only when schema.sql changed; this wipes local data
```

## Using the app

The seed creates two logins, `manager` and `employee`, four employees, a week of shifts starting
today (some deliberately left open) and 180 days of staffing history for the model.

Log in as **manager**:

1. **Employees:** see Sam, Priya, Jordan and Casey with their availability. Add an employee or
   an availability slot.
2. **Schedule:** open shifts are red and assigned shifts green. Pick an employee and press
   **Assign**. Try assigning Casey Morgan to today's 17:00-21:00 shift (it works), then Sam
   Rivera to a shift on any day but Monday (blocked: he's only available Mondays).
3. **Forecast:** predicted staff needed vs. scheduled for each day, with understaffed days
   marked "Short by N" and the model's error next to the baseline's. After the Casey
   assignment, today's gap is one smaller. **Retrain model** refreshes the metrics.

Log in as **employee** to check that the manager pages are blocked.

The full demo script is in the [alpha checklist](docs/alpha-checklist.md#alpha-demo-script-fill-in-once-features-land),
and every endpoint is documented in the [API specification](docs/api-spec.md).

## Known limitations

These are tracked with impact and mitigation plans in the
[technical debt log](docs/technical-debt.md):

- The model trains on synthetic history, so its accuracy shows the pipeline works, not
  real-world accuracy (TD-3).
- Login rate limiting (per IP and per username, set in `app/config.py`) uses
  in-memory counters for the single-process Alpha. Shared storage is required for
  consistent limits across multiple workers, and restarting the server resets the
  counters (TD-1).
- The employee home page's "My shifts" list is still a placeholder.

## Running checks locally (the same checks CI runs)

```bash
ruff format .                                 # auto-format (CI checks this)
ruff check .                                  # lint
bandit -c pyproject.toml -r app -ll           # security scan
pytest --cov=app --cov-fail-under=80          # tests + coverage
```

Run these before every push. CI runs them on every branch and on each pull request to `main`.
The 80% coverage gate means new code needs tests in the same PR.

## CI/CD pipeline

[.github/workflows/ci.yml](.github/workflows/ci.yml) runs these jobs:

1. **Lint**: `ruff check` and `ruff format --check`
2. **Security**: `bandit` (code) and `pip-audit` (dependencies with known vulnerabilities)
3. **Test**: `pytest` on Python 3.11, 3.12 and 3.13, with an 80% coverage gate; uploads
   JUnit and coverage reports as artifacts
4. **Build check**: seeds a fresh database, then smoke-tests login and every page

Newer pushes to the same branch cancel older runs automatically.

## Workflow

See [CONTRIBUTING.md](CONTRIBUTING.md) for branch naming, commit messages, pull requests and
peer review.

## Project structure

```
app/
  __init__.py          application factory, registers all modules
  config.py            settings from environment variables
  db.py, schema.sql    SQLite connection + schema, `flask init-db` / `flask seed`
  seed.py              demo employees, shifts, logins and staffing history
  errors.py            ValidationError/NotFoundError/ConflictError -> JSON responses
  validation.py        shared input parsing
  auth/                login, roles
  employees/           employee records and availability
  scheduling/          shifts, assignments, constraints.py (scheduling rules)
  forecasting/         staffing history, features, random forest model, forecast API
  templates/, static/  pages, shared CSS and JS helpers
tests/                 unit, API, end-to-end and performance tests
docs/                  architecture, API spec, AI feature, tech debt, checklist, review templates
```

## Documentation

- **[Alpha release checklist](docs/alpha-checklist.md)**: tasks per person and the demo script
- [Architecture](docs/architecture.md) (Lead Architect)
- [API specification](docs/api-spec.md) (Interface Designer)
- [AI feature and integration](docs/ai-feature.md) (Integration Lead)
- [Technical debt log](docs/technical-debt.md)
- [Peer review template](docs/peer-review-template.md) and [completed reviews](docs/peer-reviews/)
- [Refinement report template](docs/refinement-report-template.md)
