# ShiftWise AI: Intelligent Workforce Scheduling

ShiftWise AI helps managers anticipate staffing needs, avoid scheduling conflicts, and cover
unexpected absences. A scikit-learn model predicts how many staff each day needs. When someone
calls out, the system recommends replacements who meet availability and qualification rules,
and a manager approves the change before it takes effect.

**Stack:** Python 3.11+ · Flask · SQLite · scikit-learn · HTML/CSS/JavaScript · GitHub Actions

> **Status: scaffold.** The shared foundation (app structure, config, database, error handling,
> login and roles, CI) works. The three feature modules are stubs with TODOs for the team to
> build. See the [alpha checklist](docs/alpha-checklist.md) for who owns what.

## Team roles

| Role | Owner | Module | Docs |
|------|-------|--------|------|
| Lead Architect | _name_ | Scheduling (`app/scheduling/`) and database schema | [architecture.md](docs/architecture.md) |
| Interface Designer | _name_ | Employees (`app/employees/`) and UI pages | [api-spec.md](docs/api-spec.md) |
| Integration Lead | _name_ | Forecasting / AI (`app/forecasting/`) | [ai-feature.md](docs/ai-feature.md) |

## What's in the scaffold

| Area | Status |
|------|--------|
| App factory, blueprints, environment config (`app/__init__.py`, `app/config.py`) | Working |
| SQLite connection, `flask init-db` and `flask seed` (`app/db.py`, `app/seed.py`) | Working; schema has only `users` so far |
| Shared errors → JSON (400/404/409/501) and input validation (`app/errors.py`, `app/validation.py`) | Working |
| Login, password hashing, manager/employee roles (`app/auth/`) | Working |
| Base layout, CSS, JS helpers (`app/templates/base.html`, `app/static/`) | Working |
| Employees, Scheduling, Forecasting modules | **Stubs**: routes are wired, and service functions raise `NotImplementedError`, so the API returns 501 until they're built |
| Tests | Foundation tests pass; feature tests are skipped templates |
| CI pipeline | Working (lint, format, security, tests on 3 Python versions, startup check) |

## Getting started

```bash
git clone https://github.com/ktwerts/495-group6.git
cd 495-group6
python -m venv .venv
```

Activate the virtual environment:

- Windows (PowerShell): `.venv\Scripts\Activate.ps1`
- macOS/Linux: `source .venv/bin/activate`

```bash
pip install -r requirements-dev.txt
cp .env.example .env          # then fill in SHIFTWISE_SECRET_KEY
flask --app run seed          # resets the database and prints the manager password
python run.py                 # http://127.0.0.1:5000
```

Log in as `manager` with the password `flask seed` printed, or the one you set in
`SHIFTWISE_ADMIN_PASSWORD`. Feature pages show a "Not implemented yet" message until their
module is built.

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
  errors.py            ValidationError/NotFoundError/ConflictError -> JSON responses
  validation.py        shared input parsing
  auth/                login, roles (working)
  employees/           TODO: employee records + availability
  scheduling/          TODO: shifts, absences, constraints.py, recommendations
  forecasting/         staffing history, features, random forest model, forecast API
  templates/, static/  base layout + placeholder pages
tests/                 foundation tests + skipped templates per module
docs/                  checklist, outlines for each role, templates
```

## Documentation

- **[Alpha release checklist](docs/alpha-checklist.md)**: tasks per person, mapped to the rubric
- [Architecture](docs/architecture.md) (Lead Architect)
- [API specification](docs/api-spec.md) (Interface Designer)
- [AI feature and integration](docs/ai-feature.md) (Integration Lead)
- [Technical debt log](docs/technical-debt.md)
- [Peer review template](docs/peer-review-template.md) and [completed reviews](docs/peer-reviews/)
- [Refinement report template](docs/refinement-report-template.md)
