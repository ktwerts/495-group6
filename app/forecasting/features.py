"""Feature engineering: turn historical records into model inputs.

Owner: Integration Lead

Ideas from the proposal: historical attendance, workload patterns, scheduled shifts.
Start simple (for example day of week, month, weekend flag) and add features as you go.
"""

from datetime import date


def build_features(day: date, **inputs) -> list[float]:
    """Return the numeric feature vector for one day."""
    raise NotImplementedError("features.build_features")
