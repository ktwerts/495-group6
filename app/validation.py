"""Input parsing helpers shared by every module."""

from datetime import date, datetime

from app.errors import ValidationError


def require_json(payload) -> dict:
    if not isinstance(payload, dict):
        raise ValidationError("Request body must be a JSON object")
    return payload


def require_fields(data: dict, *fields: str) -> None:
    missing = [f for f in fields if data.get(f) in (None, "")]
    if missing:
        raise ValidationError(f"Missing required field(s): {', '.join(missing)}")


def parse_date(value, field: str = "date") -> date:
    try:
        return date.fromisoformat(str(value))
    except (TypeError, ValueError) as exc:
        raise ValidationError(f"{field} must be a date in YYYY-MM-DD format") from exc


def parse_time(value, field: str = "time") -> str:
    """Return a normalized 'HH:MM' string."""
    try:
        return datetime.strptime(str(value), "%H:%M").strftime("%H:%M")
    except (TypeError, ValueError) as exc:
        raise ValidationError(f"{field} must be a time in HH:MM (24h) format") from exc


def parse_positive_number(value, field: str, maximum: float | None = None) -> float:
    try:
        number = float(value)
    except (TypeError, ValueError) as exc:
        raise ValidationError(f"{field} must be a number") from exc
    if number <= 0 or (maximum is not None and number > maximum):
        limit = f" and at most {maximum}" if maximum is not None else ""
        raise ValidationError(f"{field} must be greater than 0{limit}")
    return number


def parse_int(value, field: str, minimum: int | None = None, maximum: int | None = None) -> int:
    try:
        number = int(value)
    except (TypeError, ValueError) as exc:
        raise ValidationError(f"{field} must be a whole number") from exc
    if minimum is not None and number < minimum:
        raise ValidationError(f"{field} must be at least {minimum}")
    if maximum is not None and number > maximum:
        raise ValidationError(f"{field} must be at most {maximum}")
    return number


def parse_qualifications(value) -> list[str]:
    """Accept a list or comma-separated string; return sorted, lowercase, de-duplicated."""
    if value in (None, ""):
        return []
    if isinstance(value, str):
        items = value.split(",")
    elif isinstance(value, list):
        items = [str(v) for v in value]
    else:
        raise ValidationError("qualifications must be a list or comma-separated string")
    return sorted({item.strip().lower() for item in items if item.strip()})
