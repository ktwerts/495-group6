-- ShiftWise AI database schema (SQLite)
-- Owner: Lead Architect (coordinate table changes with the module owners)
--
-- Conventions: dates are ISO text (YYYY-MM-DD) and times are 24h text (HH:MM).
-- `flask init-db` or `flask seed` drops and recreates everything below.
-- When you add a table, add a matching DROP TABLE IF EXISTS line at the top,
-- children before parents.

DROP TABLE IF EXISTS users;

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
