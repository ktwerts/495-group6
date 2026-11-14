# Contributing to ShiftWise AI

## Branching

- `main` is always releasable. **Never commit directly to `main`.** Every change goes through
  a pull request (PR).
- Create a branch from an up-to-date `main` for each piece of work:

```bash
git checkout main
git pull
git checkout -b feature/<module>-<short-description>
```

| Prefix | Use for | Example |
|--------|---------|---------|
| `feature/` | New functionality | `feature/forecasting-holiday-feature` |
| `fix/` | Bug fixes | `fix/scheduling-overlap-check` |
| `docs/` | Documentation only | `docs/api-spec-recommendations` |
| `test/` | Tests only | `test/employees-validation` |
| `refactor/` | Cleanup with no behavior change | `refactor/auth-service` |

Keep branches small and short-lived (a few days at most). If `main` moves ahead, update your
branch with `git pull origin main`.

## Commit messages

Use the [Conventional Commits](https://www.conventionalcommits.org/) format:

```
<type>(<module>): <what changed, imperative, under ~70 chars>

<optional body: why, and anything a reviewer should know>
```

Types: `feat`, `fix`, `docs`, `test`, `refactor`, `chore`, `ci`.

Good:

- `feat(forecasting): add holiday flag to model features`
- `fix(scheduling): reject shifts that end before they start`
- `test(employees): cover availability validation errors`

Bad: `update`, `fixed stuff`, `asdf`, `final version 2`.

Commit often, in small logical steps. Each commit should leave the tests passing.

## Pull requests

1. Run the local checks before you push:
   ```bash
   ruff check .
   bandit -c pyproject.toml -r app -ll
   pytest --cov=app --cov-fail-under=80
   ```
2. Push your branch and open a PR into `main`. Fill in the PR template.
3. CI must be green.
4. **At least one teammate must approve the PR** using the
   [peer review checklist](docs/peer-review-template.md).
5. The author merges with **Squash and merge** and deletes the branch.

### Recommended GitHub settings (repo owner)

Settings → Branches → Add branch protection rule for `main`:

- Require a pull request before merging (1 approval)
- Require status checks to pass: `Lint (ruff)`, `Security scan (bandit + pip-audit)`,
  `Tests (Python 3.12)`, `Build check (app boots + seeds)`
- Require branches to be up to date before merging

## Code standards

- Follow the existing module pattern: `routes.py` handles HTTP only, `service.py` holds logic,
  and other modules call each other's **service functions**, never their tables directly.
- Raise `ValidationError`, `NotFoundError` or `ConflictError` from `app/errors.py`. Don't
  build error responses by hand.
- Always use parameterized SQL (`?` placeholders). Never build SQL with f-strings or `+`.
- Escape user data in the front end with `esc()` before inserting it into HTML.
- Keep secrets out of the code. Add new settings to `app/config.py` and `.env.example`.
- Every new feature or bug fix comes with tests.
- Record any shortcut you knowingly take in [docs/technical-debt.md](docs/technical-debt.md).
