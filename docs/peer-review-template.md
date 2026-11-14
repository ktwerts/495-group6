# Peer Review

Submit this as a GitHub PR review: leave inline comments on specific lines and paste the
summary below into the review body. Approve only when the blocking items are fixed.

- **Reviewer:**
- **Author:**
- **Module / PR link:**
- **Date:**

## 1. Code quality and readability

- [ ] Names are clear; functions do one thing
- [ ] Follows the routes → service pattern; no direct cross-module table access
- [ ] No dead code, debug prints or commented-out blocks
- [ ] `ruff check .` passes

Findings:

## 2. Security

- [ ] All SQL is parameterized
- [ ] Manager-only routes use `@role_required("manager")`
- [ ] Input is validated (`app/validation.py`) before use
- [ ] No secrets or passwords in code; new settings added to `.env.example`
- [ ] User data is escaped in templates/JS (`esc()`)
- [ ] `bandit -r app -ll` passes

Findings:

## 3. Performance

- [ ] No queries inside loops that could be batched
- [ ] Model is not retrained on every request
- [ ] No unbounded results (limits or date ranges in place)

Findings:

## 4. Integration compatibility

- [ ] Request/response shapes match [api-spec.md](api-spec.md), or the spec was updated
- [ ] Uses the shared error types (`ValidationError`, `NotFoundError`, `ConflictError`)
- [ ] Doesn't break other modules (`pytest` passes, including the cross-module tests)

Findings:

## 5. Documentation

- [ ] Public functions have docstrings
- [ ] README or docs updated for new setup steps or endpoints
- [ ] Any shortcuts recorded in [technical-debt.md](technical-debt.md)

Findings:

## Summary

| # | Severity (blocking / should fix / nit) | File:line | Issue | Suggested fix |
|---|------|-----------|-------|---------------|
| 1 | | | | |

**Decision:** Approve / Request changes
