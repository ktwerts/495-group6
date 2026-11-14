"""Integration layer: database + model + scheduling.

Owner: Integration Lead

This is where the AI feature meets the rest of the system. For each requested day,
predict staff needed (model.py) and compare it with scheduling.count_scheduled_staff()
to show managers where they're understaffed.

Delete each `raise NotImplementedError` as you implement the function.
"""

from datetime import date


def train_model() -> dict:
    """Load staffing history from the database, train, save the model, return metrics."""
    raise NotImplementedError("forecasting.train_model")


def forecast(start: date, days: int) -> dict:
    """Return predicted vs. scheduled staff for each day in the range."""
    raise NotImplementedError("forecasting.forecast")
