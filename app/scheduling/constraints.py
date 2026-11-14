"""Scheduling rules (proposal risk 3: scheduling conflicts).

Owner: Lead Architect

Keep these functions *pure*: no database or Flask calls. Pass in the data they need,
so they're easy to unit test in tests/test_scheduling.py.

Rules from the proposal to enforce:
- the employee is available for the whole shift
- the employee has the required qualification
- no overlapping shifts for the same person
- (your choice) maximum weekly hours, absences, and so on
"""


def times_overlap(a_start: str, a_end: str, b_start: str, b_end: str) -> bool:
    """True if two 'HH:MM' time ranges on the same day overlap."""
    raise NotImplementedError("constraints.times_overlap")


def check_assignment(employee: dict, shift: dict, **context) -> list[str]:
    """Return a list of human-readable rule violations; an empty list means OK.

    Decide what goes in `context` (availability, other shifts, absences, ...)
    and document it here.
    """
    raise NotImplementedError("constraints.check_assignment")
