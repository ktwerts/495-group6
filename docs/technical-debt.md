# Technical Debt Log

Record every shortcut you take on purpose to hit a deadline. Each person's Refinement Report
must cite specific entries here and explain how they were or will be mitigated.

**Severity** is the cost if the item is left alone: **High** means a reliability or security risk
before real use; **Medium** limits features or scale; **Low** is a cleanup.

## Open

| ID | Area | Shortcut taken (where) | Interest (future cost) | Mitigation plan | Severity |
|----|------|------------------------|------------------------|-----------------|----------|
| TD-1 | auth | No login rate limiting or account lockout (`/api/auth/login` in `app/auth/routes.py`) | Passwords can be brute-forced | Add Flask-Limiter (e.g. 5 attempts per minute per IP and username) | High |
| | | | | | |

TD-1 is a real gap in the scaffold and a worked example of the format. Add your own entries
below it as you build. Typical sources: hardcoded values, missing validation, slow queries,
untested paths, simplified data models, and synthetic training data.

## Resolved

| ID | Area | Original shortcut | Interest that was accruing | How it was mitigated | PR |
|----|------|-------------------|----------------------------|----------------------|----|
| | | | | | |

## How to add an entry

1. Give it the next ID (TD-2, TD-3, ...).
2. Be specific: name the file or function and the actual shortcut.
3. Describe the real "interest": what gets harder, slower or riskier over time.
4. Propose a concrete fix and a severity.
5. When it's fixed, move it to **Resolved**, say how, and link the PR.
