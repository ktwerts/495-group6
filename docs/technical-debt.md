# Technical Debt Log

Record every shortcut you take on purpose to hit a deadline. Each person's Refinement Report
must cite specific entries here and explain how they were or will be mitigated.

**Severity** is the cost if the item is left alone: **High** means a reliability or security risk
before real use; **Medium** limits features or scale; **Low** is a cleanup.

## Open

| ID | Area | Shortcut taken (where) | Interest (future cost) | Mitigation plan | Severity |
|----|------|------------------------|------------------------|-----------------|----------|
| TD-1 | auth | No login rate limiting or account lockout (`/api/auth/login` in `app/auth/routes.py`) | Passwords can be brute-forced | Add Flask-Limiter (e.g. 5 attempts per minute per IP and username) | High |
| TD-3 | forecasting | Training data is **synthetic**: `generate_sample_history()` in `app/forecasting/history.py` invents workload and staffing from fixed rules plus noise | The model can only learn patterns we wrote into the generator, so its accuracy scores won't reflect a real workplace and could give false confidence in forecasts | Add a CSV import for real (or public) attendance and workload data; keep the weekday-average baseline comparison so the team can tell whether the model helps on real data | High |
| | | | | | |

TD-1 is a real gap in the scaffold and a worked example of the format. Add your own entries
below it as you build. Typical sources: hardcoded values, missing validation, slow queries,
untested paths, simplified data models, and synthetic training data.

## Resolved

| ID | Area | Original shortcut | Interest that was accruing | How it was mitigated | PR |
|----|------|-------------------|----------------------------|----------------------|----|
| TD-4 | forecasting | `seed_staffing_history()` assumed an empty table; a date already stored made the whole insert fail (found in peer review) | Re-seeding, or adding demo history to a database that already had some, would crash instead of filling the gaps | `save_history(skip_existing=True)` skips dates already stored and still rejects invalid values; seeding is now safe to run repeatedly. Covered by 5 new tests | staffing-history-table |
| | | | | | |

## How to add an entry

1. Give it the next ID (TD-2, TD-3, ...).
2. Be specific: name the file or function and the actual shortcut.
3. Describe the real "interest": what gets harder, slower or riskier over time.
4. Propose a concrete fix and a severity.
5. When it's fixed, move it to **Resolved**, say how, and link the PR.
