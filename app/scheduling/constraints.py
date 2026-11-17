
"""Scheduling rules for ShiftWise AI.

Owner: Lead Architect

These functions validate employee assignments without
accessing the database or Flask.
"""


def times_overlap(a_start: str, a_end: str,
                  b_start: str, b_end: str) -> bool:
    """Check whether two shifts overlap on the same day."""
    return a_start < b_end and b_start < a_end


def check_assignment(employee: dict, shift: dict, **context) -> list[str]:
    """Check whether an employee can work a shift.

    Context:
        availability: weekly availability slots
        other_shifts: existing employee shifts
        absences: reported employee absences

    Returns a list of violations, or [] if valid.
    """
    violations = []

    availability = context.get("availability", [])
    other_shifts = context.get("other_shifts", [])
    absences = context.get("absences", [])

    shift_date = shift["date"]
    start = shift["start_time"]
    end = shift["end_time"]

    # Check that shift times are valid.
    if start >= end:
        violations.append("Shift end time must be after start time.")
        return violations

    # Check employee status.
    if not employee.get("active", True):
        violations.append("Employee is inactive.")

    # Check qualifications.
    required = shift.get("required_qualification")
    qualifications = employee.get("qualifications", [])

    if isinstance(qualifications, str):
        qualifications = [
            q.strip() for q in qualifications.split(",")
        ]

    if required and required not in qualifications:
        violations.append(
            "Employee does not have the required qualification."
        )

    # Check employee availability.
    # Availability must be supplied by the employee module.
    if not availability:
        violations.append("Employee availability is not available.")
    else:
        from datetime import date

        weekday = date.fromisoformat(shift_date).weekday()

        available = any(
            slot.get("day_of_week") == weekday
            and slot["start_time"] <= start
            and slot["end_time"] >= end
            for slot in availability
        )

        if not available:
            violations.append(
                "Employee is not available for the entire shift."
            )

    # Check for overlapping shifts.
    for existing in other_shifts:
        if existing["date"] == shift_date:
            if times_overlap(
                start, end,
                existing["start_time"],
                existing["end_time"]
            ):
                violations.append(
                    "Employee already has an overlapping shift."
                )
                break

    # Check reported absences.
    if any(a["date"] == shift_date for a in absences):
        violations.append(
            "Employee has a reported absence on this date."
        )

    return violations
