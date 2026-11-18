# Technical Debt Log

Record every shortcut you take on purpose to hit a deadline. Each person's Refinement Report
must cite specific entries here and explain how they were or will be mitigated.

**Severity** is the cost if the item is left alone: **High** means a reliability or security risk
before real use; **Medium** limits features or scale; **Low** is a cleanup.

## Open

| ID | Area | Shortcut taken (where) | Interest (future cost) | Mitigation plan | Severity |
|----|------|------------------------|------------------------|-----------------|----------|
| TD-1 | auth | No login rate limiting or account lockout (`/api/auth/login` in `app/auth/routes.py`) | Passwords can be brute-forced | Add Flask-Limiter (e.g. 5 attempts per minute per IP and username) | High |
| TD-2 | employees | `create_employee` assigns a fixed 40-hour weekly limit so the Alpha form only needs name and position. | The saved limit can overstate availability for part-time staff. If Scheduling uses it to enforce weekly limits, it could recommend assignments beyond the employee's actual cap. | Let managers enter and edit a validated weekly limit, and test that Scheduling respects the stored value. | Medium |
| TD-3 | forecasting | Training data is **synthetic**: `generate_sample_history()` in `app/forecasting/history.py` invents workload and staffing from fixed rules plus noise | The model can only learn patterns we wrote into the generator, so its accuracy scores won't reflect a real workplace and could give false confidence in forecasts | Add a CSV import for real (or public) attendance and workload data; keep the weekday-average baseline comparison so the team can tell whether the model helps on real data | High |
| TD-5 | forecasting | `StaffingForecaster.train()` accepts history with duplicate dates and counts them twice (`app/forecasting/model.py`) | A repeated day skews weekday averages and can land in both the training and test split, making accuracy look better than it is | Reject duplicate `record_date` values in `train()`; the `staffing_history` table already enforces one row per date, so this only affects callers passing rows directly | Low |
| TD-6 | forecasting | The trained model is saved with joblib, which uses pickle (`app/forecasting/service.py`) | Loading a tampered model file could run arbitrary code | Mitigated for Alpha: only the app's own file in `instance/` (gitignored, never served) is loaded, and its contents are type-checked. For production, sign the file with a hash or store only model parameters | Medium |
| TD-7 | forecasting | The saved model counts as current while the history's row count and latest date are unchanged (`_history_version()` in `app/forecasting/service.py`) | Editing an existing history row in place won't trigger retraining, so forecasts could use stale data until someone presses retrain | Track a `last_updated` timestamp on `staffing_history`, or retrain whenever history is written | Low |
| TD-8 | forecasting | The model predicts one total headcount per day (`staff_needed` in `staffing_history`), with no shift or position | A manager sees that a day is short but not whether it's the morning shift or a missing cook, so the forecast can't feed replacement recommendations directly | Record shift and position in the history, predict per shift, and compare with Scheduling's per-shift counts | Medium |
| TD-9 | scheduling | Absences, replacement recommendations and manager approval aren't built; `recommend_replacements()` is a stub and the `absences` table can only be filled directly (`app/scheduling/service.py`) | When someone calls out, the manager has to unassign and reassign the shift by hand, and the absence → recommend → approve flow from the proposal can't be demoed or tested end to end | Add `POST /api/absences` that reopens the employee's shifts, rank replacements with `check_assignment()`, and add approve/reject endpoints; then un-skip the integration test in `tests/test_integration.py` | High |
| TD-10 | scheduling | Qualifications are free text matched by name, ignoring case only (`check_assignment()` in `app/scheduling/constraints.py`) | A typo or variant ("Food Safety Cert" vs "food safety") makes a qualified employee look unqualified, blocking valid assignments | Keep a shared list of qualifications and pick from it on both the Employees and Schedule forms | Medium |
| TD-11 | scheduling | `shifts.employee_id` and `absences.employee_id` have no foreign key to `employees` (`app/schema.sql`) | Nothing stops a shift pointing at a deleted employee id; the app only checks when assigning | Add `REFERENCES employees (id)` and turn on `PRAGMA foreign_keys` in `get_db()` | Low |
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
