# API Specification

_Owner: Interface Designer_

Every API route lives under `/api`, accepts and returns JSON, and uses session-cookie auth
(log in first with `POST /api/auth/login`). Update this file **in the same PR** as any
endpoint change, so teammates can code against it.

## Conventions

| Convention | Format |
|------------|--------|
| Dates | `YYYY-MM-DD` |
| Times | `HH:MM` (24-hour) |
| Days of week | `0` = Monday … `6` = Sunday |
| Errors | `{"error": "message"}`, plus `"violations": [...]` on 409 |

| Status | Meaning |
|--------|---------|
| 200 / 201 | Success / created |
| 400 | Invalid input |
| 401 | Not logged in |
| 403 | Logged in but wrong role |
| 404 | Record not found |
| 409 | Breaks a scheduling rule (see `violations`) |
| 501 | Endpoint exists but isn't implemented yet (scaffold stub) |

**Role key:** M = manager only, A = any logged-in user, P = public

## Auth (implemented: use this section as the format example)

| Method | Path | Role | Body | Returns |
|--------|------|------|------|---------|
| POST | `/api/auth/login` | P | `{username, password}` | `{id, username, role}` |
| POST | `/api/auth/logout` | P | — | `{message}` |
| GET | `/api/auth/me` | A | — | `{id, username, role, employee_id}` |
| POST | `/api/auth/users` | M | `{username, password (8+ chars), role, employee_id?}` | user |

## Employees (Interface Designer)

To create an employee, send `name` and `position` as nonblank strings.
Leading and trailing whitespace is trimmed. Each field must be at most 100 characters after trimming. A successful request returns
`201 Created` with `id`, `name`, `position`, `active` (integer `1`),
`max_weekly_hours` (number, defaults to `40`), and empty `qualifications`
and `availability` arrays. Invalid input returns `400`. A signed-out
caller receives `401`, and a signed-in employee receives `403`.

| Method | Path | Role | Body / query | Returns | Status |
|--------|------|------|--------------|---------|--------|
| GET | `/api/employees` | M | — | List of active employees (200) | Implemented |
| POST | `/api/employees` | M | JSON with `name` and `position` | Created employee (201) | Implemented |
| POST | `/api/employees/{employee_id}/availability` | M | JSON with `day_of_week`, `start_time`, and `end_time` | Recorded slot (201) | Implemented |

To record a weekly availability slot, send `day_of_week` as an integer
from `0` (Monday) to `6` (Sunday), with `start_time` and `end_time` in
24-hour `HH:MM` format. The end time must be later than the start time
on the same day. A successful request returns `201 Created` with the
recorded slot. Invalid input returns `400`, an unknown employee returns `404`, and a slot that overlaps an existing slot for the same employee and weekday returns `409`. Back-to-back slots are allowed.

**Response for `GET /api/employees`**

A successful request returns `200 OK` and a JSON array of active employees.
If there are no active employees, it returns `[]`. A caller who is signed out
receives `401`. A signed-in employee receives `403`.

| Field | Type | Meaning |
|-------|------|---------|
| `id` | Integer | Unique employee ID |
| `name` | String | Employee's display name |
| `position` | String | Employee's job title |
| `active` | Integer | `1` if the employee is active |
| `qualifications` | Array of strings | Qualifications used to match shift requirements |
| `max_weekly_hours` | Number | Maximum hours the employee can be scheduled per week |
| `availability` | Array of objects | Recurring weekly availability slots |

Each availability slot contains `day_of_week` (integer, 0 for Monday through
6 for Sunday), `start_time` (string, `HH:MM`), and `end_time` (string, `HH:MM`).

```json
[
  {
    "id": 1,
    "name": "Sam Rivera",
    "position": "Cook",
    "active": 1,
    "qualifications": ["food safety"],
    "max_weekly_hours": 32,
    "availability": [
      {
        "day_of_week": 0,
        "start_time": "09:00",
        "end_time": "17:00"
      }
    ]
  }
]
```

Proposed scheduling behavior: `availability: []` means the employee has no
recorded availability and is ineligible for automatic replacement recommendations.

For review with Scheduling: confirm the empty-availability rule and how
qualification strings are matched.

## Scheduling (Lead Architect)

| Method | Path | Role | Body / query | Returns | Status |
|--------|------|------|--------------|---------|--------|
| GET | `/api/shifts?start=YYYY-MM-DD&end=YYYY-MM-DD` | M | `start` and `end` optional, inclusive | List of shifts, ordered by date and start time | Implemented (200) |
| POST | `/api/shifts` | M | `{date, start_time, end_time, required_qualification?}` | Created open shift | Implemented (201) |
| POST | `/api/shifts/{shift_id}/assign` | M | `{employee_id}` | Assigned shift | Implemented (200) |
| POST | `/api/shifts/{shift_id}/unassign` | M | — | Reopened shift | Implemented (200) |
| POST | `/api/absences` | M | `{employee_id, date}` | Recorded absence (201) | Implemented |
| GET | `/api/shifts/{shift_id}/recommendations` | M | Optional `limit`, 1–50; default 3 | Eligible replacements (200) | Implemented |
| POST | `/api/shifts/{shift_id}/recommendations/approve` | M | `{employee_id}` | Assigned shift (200) | Implemented |

`POST /api/absences` records a full-day absence for an existing employee. The date must use `YYYY-MM-DD` format. Recording the absence reopens all of that employee's assigned shifts on that date and clears their employee assignments in the same transaction. Subsequent assignment attempts for that employee on that date return `409`.

A successful request returns `201` with `{id, employee_id, date}`.
Invalid input returns `400`, an unknown employee returns `404`, and
access requires a signed-in manager (`401` or `403` otherwise).

Replacement recommendations require an open shift. Candidates must be active,
qualified, available for the entire shift, free of overlapping assignments and
reported absences, and within their weekly-hour limit. Results contain
`employee_id`, `name`, and `scheduled_hours`, ordered by scheduled weekly hours
and then employee ID. If nobody qualifies, the endpoint returns `[]`.
Retrieving recommendations does not assign anyone.

Approval requires a manager's explicit request and rechecks the employee's
current eligibility. Successful approval assigns the employee and updates
scheduled staffing counts. Unknown shifts or employees return `404`; invalid
input returns `400`; ineligible assignments or a shift that is no longer open
return `409`. Both endpoints require manager access.

### Shift object

Example response:

```json
{
  "id": 1,
  "date": "2026-11-17",
  "start_time": "09:00",
  "end_time": "17:00",
  "required_qualification": "Cashier",
  "employee_id": null,
  "status": "open"
}
```

### Creating a shift

Managers can create a shift by sending a JSON object to
`POST /api/shifts`.

Required fields:
- `date`: Date in YYYY-MM-DD format.
- `start_time`: Start time in 24-hour format.
- `end_time`: End time in 24-hour format.

Optional:
- `required_qualification`: Qualification required for the shift. Leave it out (or blank)
  for a shift anyone available can work. Matching ignores case.

The API validates the required fields and ensures the end time
comes after the start time.

Successful creation returns HTTP 201 with the new shift.
New shifts are initially open and have no assigned employee. Sending `employee_id` here
returns 400; assign the shift with the endpoint below instead.

### Assigning a shift

`POST /api/shifts/{shift_id}/assign` with `{"employee_id": 1}` runs the scheduling
constraints below. If the employee can work the shift, it returns 200 with the shift,
`employee_id` set and `status: "assigned"`. Assigned shifts are what
`count_scheduled_staff()` counts for the forecast.

If any rule is broken, nothing changes and it returns 409:

```json
{
  "error": "Sam Rivera can't work this shift",
  "violations": ["Employee is not available for the entire shift."]
}
```

`POST /api/shifts/{shift_id}/unassign` removes the employee and sets the shift back to
`open`. Both return 404 for an unknown shift or employee, and 409 for a cancelled shift.

### Error responses

- 400: Missing fields, invalid dates or times, invalid JSON, a `start` filter after `end`,
  or a missing or invalid `employee_id`.
- 404: Unknown shift or employee.
- 409: The assignment breaks a scheduling rule (see `violations`).
- 401: User is not logged in.
- 403: User does not have manager permissions.

### Scheduling constraints

Assignment validation checks:
- Employee is active.
- Employee has the required qualification.
- Employee is available for the entire shift.
- Employee does not have an overlapping shift.
- Employee has no reported absence on the shift date.
- The shift doesn't take the employee past `max_weekly_hours` for that Monday-Sunday week
  (counting their other assigned shifts).

The assignment and replacement recommendation features
are not yet fully implemented.

## Forecasting (Integration Lead)

| Method | Path | Role | Body / query | Returns | Status |
|--------|------|------|--------------|---------|--------|
| GET | `/api/forecast?start=YYYY-MM-DD&days=7` | M | `days` 1–31 (default 7, max set by `FORECAST_MAX_DAYS`); `start` defaults to today | Forecast (200) | Implemented |
| POST | `/api/forecast/train` | M | — | Model metrics (200) | Implemented |

`GET /api/forecast` trains a model automatically the first time, and again whenever the
staffing history changes. Otherwise it reuses the saved model.

```json
{
  "method": "random_forest",
  "metrics": {
    "method": "random_forest", "history_days": 180, "test_days": 36, "test_from": "2026-10-11",
    "mae": 0.518, "baseline_mae": 0.664, "beats_baseline": true
  },
  "days": [
    {
      "date": "2026-12-07", "expected_workload": 58.4,
      "predicted_staff_needed": 4, "scheduled_staff": 2, "gap": 2
    }
  ]
}
```

| Field | Meaning |
|-------|---------|
| `method` | `random_forest`, or `weekday_average` with under 28 days of history (`SHIFTWISE_FORECAST_MIN_HISTORY`) |
| `metrics` | Same object `POST /api/forecast/train` returns. The fallback includes only `method` and `history_days` |
| `expected_workload` | Average historical workload for that weekday |
| `predicted_staff_needed` | Whole number of staff, minimum 1, rounded up |
| `scheduled_staff` | Distinct employees scheduled that day, from `count_scheduled_staff()`; `null` until scheduling can report counts |
| `gap` | `predicted_staff_needed - scheduled_staff`; positive means understaffed; `null` when `scheduled_staff` is |

Errors: `400` for no staffing history (run `flask seed`), invalid history data, or a bad
`days`/`start` value. Signed-out callers get `401`, and employees get `403`.

## Other

| Method | Path | Notes |
|--------|------|-------|
| GET | `/health` | `{"status": "ok"}`, used by the CI build check |
