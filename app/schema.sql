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
CREATE TABLE users (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    username      TEXT    NOT NULL UNIQUE,
    password_hash TEXT    NOT NULL,
    role          TEXT    NOT NULL CHECK (role IN ('manager', 'employee')),
    employee_id   INTEGER  -- TODO: REFERENCES employees (id) once that table exists
);

-- TODO: tables the team still needs to design. Suggested starting points:
--   employees         (Interface Designer): name, position, qualifications, max weekly hours, active
--   availability      (Interface Designer): employee, day of week, start/end time
--   shifts            (Lead Architect):     date, start/end time, required qualification, employee, status
--   absences          (Lead Architect):     employee, date, reason
--   recommendations   (Lead Architect):     shift, suggested employee, score, pending/approved/rejected
--   staffing_history  (Integration Lead):   date, workload, staff needed (training data for the model)
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