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

| Method | Path | Role | Body / query | Returns | Status |
|--------|------|------|--------------|---------|--------|
| GET | `/api/employees` | M | — | list of employees | Stub (501) |
| _TODO_ | | | | | |

_TODO: define the employee object (fields and types) with an example._

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
