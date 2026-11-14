"""Staffing demand model (the AI feature).

Owner: Integration Lead

Suggested approach (scikit-learn is already in requirements.txt):
1. Train a regressor (e.g. RandomForestRegressor or LinearRegression) to predict
   staff needed per day from the features in features.py.
2. Evaluate it on held-out data (proposal risk 1: prediction accuracy). Compare it
   against a simple baseline such as "average for that weekday" and report the error.
3. Decide what happens when there isn't enough history (fallback behavior).
4. Save and load the trained model (e.g. with joblib) so it isn't retrained per request.
"""


class StaffingForecaster:
    def train(self, rows: list) -> dict:
        """Fit the model on historical rows and return evaluation metrics."""
        raise NotImplementedError("StaffingForecaster.train")

    def predict(self, day, **inputs) -> int:
        """Predict the number of staff needed on `day`."""
        raise NotImplementedError("StaffingForecaster.predict")
