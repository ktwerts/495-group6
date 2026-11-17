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
| GET | `/api/shifts` | M | — | list of shifts | Stub (501) |
| _TODO_ | | | | | |

_TODO: define the shift object, and list the constraint violation messages the API can return._

## Forecasting (Integration Lead)

| Method | Path | Role | Body / query | Returns | Status |
|--------|------|------|--------------|---------|--------|
| GET | `/api/forecast?start=YYYY-MM-DD&days=7` | M | `days` 1–31; `start` defaults to today | forecast | Stub (501) |
| _TODO_ | | | | | |

_TODO: define the forecast response (per-day predicted vs. scheduled, model metrics)._

## Other

| Method | Path | Notes |
|--------|------|-------|
| GET | `/health` | `{"status": "ok"}`, used by the CI build check |
