-- ShiftWise AI database schema (SQLite)
-- Owner: Lead Architect (coordinate table changes with the module owners)
--
-- Conventions: dates are ISO text (YYYY-MM-DD) and times are 24h text (HH:MM).
-- `flask init-db` or `flask seed` drops and recreates everything below.
-- When you add a table, add a matching DROP TABLE IF EXISTS line at the top,
-- children before parents.

DROP TABLE IF EXISTS users;
DROP TABLE IF EXISTS recommendations;
DROP TABLE IF EXISTS absences;
DROP TABLE IF EXISTS shifts;
DROP TABLE IF EXISTS availability;
DROP TABLE IF EXISTS employees;

CREATE TABLE users (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    username      TEXT    NOT NULL UNIQUE,
    password_hash TEXT    NOT NULL,
    role          TEXT    NOT NULL CHECK (role IN ('manager', 'employee')),
    employee_id   INTEGER  -- TODO: REFERENCES employees (id) once that table exists
);

CREATE TABLE employees (
    id       INTEGER PRIMARY KEY,
    name     TEXT    NOT NULL,
    position TEXT    NOT NULL,
    qualifications   TEXT NOT NULL DEFAULT '[]',
    max_weekly_hours REAL NOT NULL CHECK (max_weekly_hours > 0),
    active   INTEGER NOT NULL DEFAULT 1 CHECK (active IN (0, 1))
);

CREATE TABLE availability (
    employee_id INTEGER NOT NULL REFERENCES employees (id),
    day_of_week INTEGER NOT NULL CHECK (day_of_week BETWEEN 0 AND 6),
    start_time  TEXT    NOT NULL,
    end_time    TEXT    NOT NULL CHECK (end_time > start_time),
    PRIMARY KEY (employee_id, day_of_week, start_time, end_time)
);

-- TODO: tables the team still needs to design. Suggested starting points:
--   employees         (Interface Designer): name, position, qualifications, max weekly hours, active
--   availability      (Interface Designer): employee, day of week, start/end time
--   shifts            (Lead Architect):     date, start/end time, required qualification, employee, status
--   absences          (Lead Architect):     employee, date, reason
--   recommendations   (Lead Architect):     shift, suggested employee, score, pending/approved/rejected
-- Scheduling module: Lead Architect

CREATE TABLE shifts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    date TEXT NOT NULL,
    start_time TEXT NOT NULL,
    end_time TEXT NOT NULL,
    required_qualification TEXT,
    employee_id INTEGER,
    status TEXT NOT NULL DEFAULT 'open'
        CHECK (status IN ('open', 'assigned', 'cancelled')),
    CHECK (start_time < end_time)
);

CREATE TABLE absences (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    employee_id INTEGER NOT NULL,
    date TEXT NOT NULL,
    reason TEXT,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- One full-day absence per employee per date.
CREATE UNIQUE INDEX absences_employee_date ON absences (employee_id, date);

CREATE TABLE recommendations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    shift_id INTEGER NOT NULL,
    employee_id INTEGER NOT NULL,
    score REAL NOT NULL DEFAULT 0,
    status TEXT NOT NULL DEFAULT 'pending'
        CHECK (status IN ('pending', 'approved', 'rejected')),
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (shift_id) REFERENCES shifts(id)
);

-- Forecast training data, one row per day.
DROP TABLE IF EXISTS staffing_history;

CREATE TABLE staffing_history (
    record_date    TEXT    PRIMARY KEY,
    workload_units REAL    NOT NULL CHECK (workload_units >= 0),
    staff_needed   INTEGER NOT NULL CHECK (staff_needed >= 1),
    absences       INTEGER NOT NULL DEFAULT 0 CHECK (absences >= 0)
);
