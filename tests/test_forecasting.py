"""Forecasting (AI) module tests. Owner: Integration Lead.

These are templates: remove the skip marker as you implement each feature.
Test the model on small synthetic data so tests stay fast and deterministic
(set random_state).
"""

import pytest

TODO = pytest.mark.skip(reason="TODO: implement forecasting module")


@TODO
def test_build_features_shape():
    """build_features() returns the same number of values for every day."""


@TODO
def test_model_trains_and_reports_metrics():
    """train() on synthetic history returns an error metric (e.g. MAE) and a baseline to compare."""


@TODO
def test_predictions_are_positive_integers():
    """predict() never returns 0 or negative staff."""


@TODO
def test_not_enough_history_is_handled():
    """With little or no history, the service falls back or returns a clear 400, not a crash."""


@TODO
def test_forecast_endpoint_shows_gap(manager):
    """Integration: /api/forecast compares predictions with scheduling.count_scheduled_staff()."""
