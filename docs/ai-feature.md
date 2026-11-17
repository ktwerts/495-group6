# AI Feature: Staffing Demand Forecasting

_Owner: Integration Lead_

## What it does

The forecast predicts how many staff each upcoming day needs, using past workload and
staffing, and compares that with how many people are actually scheduled. A manager opens the
Forecast page, sees which days are short and by how many, and can fix the schedule before the
day arrives instead of reacting to a callout. The prediction comes from a scikit-learn random
forest trained on daily history, and every training run is scored against a simple
weekday-average baseline so the team can tell whether the model is actually adding value.

## Data

Training data lives in the `staffing_history` table, with one row per past day:

| Column | Meaning |
|--------|---------|
| `record_date` | The day (`YYYY-MM-DD`, unique) |
| `workload_units` | How busy the day was (e.g. orders or customer visits) |
| `staff_needed` | How many staff that workload actually required (**what the model predicts**) |
| `absences` | Unplanned absences that day (the proposal's "historical attendance") |

For the alpha, `flask seed` fills the table with 180 days of **synthetic** history from
`generate_sample_history()` in `app/forecasting/history.py`. The generator builds in patterns
the model should learn:

- Fridays are somewhat busier, and Saturdays and Sundays are much busier.
- There's a mild yearly seasonal swing.
- Staff needed follows workload, with random variation, so the model can't simply memorize a
  formula.

A fixed random seed makes the data identical on every run, so tests and demos are repeatable.
Using synthetic data is a known limitation; see TD-3 in [technical-debt.md](technical-debt.md).

## Features

`build_features()` in `app/forecasting/features.py` turns one day into 7 numbers. Each one
targets a pattern in staffing demand:

| Feature | Pattern it captures |
|---------|---------------------|
| `day_of_week` (0 = Mon) | Weekly rhythm |
| `is_friday` | Friday rush |
| `is_weekend` | Saturday and Sunday peaks |
| `month` | Month-level changes |
| `season_sin`, `season_cos` | Time of year as a point on a circle, so Dec 31 and Jan 1 sit next to each other instead of 365 apart |
| `workload_units` | How busy the day is, the strongest single signal for staff needed |

`history_to_xy()` converts `staffing_history` rows into the feature matrix `X` and the target
`y` (`staff_needed`) that scikit-learn expects.

## Model and evaluation (proposal risk 1: prediction accuracy)

`StaffingForecaster` in `app/forecasting/model.py` wraps a scikit-learn
`RandomForestRegressor` (100 trees, `min_samples_leaf=2`, fixed `random_state`).

**Why a random forest:** staffing demand mixes a weekly cycle, seasonal effects and workload.
A random forest picks up those non-linear interactions without feature scaling, handles a
small dataset well, and gives the same result on every run with a fixed seed.

**Evaluation:**

- History is sorted by date. The oldest 80% trains the model and the newest 20% tests it, so
  the model never learns from days that come after the ones it's scored on.
- The error metric is mean absolute error (MAE), in staff per day.
- The baseline is the average staff needed for that weekday, computed from the training days
  only. `beats_baseline` reports whether the model is adding value.
- After evaluation, the model is refit on all history for real predictions.

Results on the 180-day seed data, at three different end dates:

| History ends | Model MAE | Baseline MAE | Beats baseline |
|--------------|-----------|--------------|----------------|
| 2026-05-01 | 0.44 | 0.64 | Yes |
| 2026-11-15 | 0.52 | 0.66 | Yes |
| 2027-02-01 | 0.37 | 0.72 | Yes |

These numbers come from synthetic data (TD-3), so they show the pipeline works, not that it
would be this accurate on a real workplace.

**Predictions:** for a future day, workload isn't known yet, so the model uses that weekday's
average workload unless a value is passed in. A passed-in workload must be a finite number
>= 0. The weekday-average fallback has no workload input, so there it's checked and then
ignored. Predictions are rounded **up** to a whole person, with a minimum of 1, because being
one person short is worse than having one extra.

**Input validation:** `train()` validates every history row before using it, on both the
random forest and fallback paths, so a bad row raises `ValueError` naming its date instead of
causing a crash at prediction time.

**Too little history:**

| History | Behavior |
|---------|----------|
| None | `train()` raises `ValueError` (the API turns it into a 400) |
| Under 28 days | Falls back to the weekday average; `method` is `weekday_average` |
| 28 days or more | Random forest; `method` is `random_forest` |

## Integration with the rest of the system

`app/forecasting/service.py` connects the model to the rest of the app:

1. **History → model:** `train_model()` loads `staffing_history`, trains a
   `StaffingForecaster`, and saves it to `instance/staffing_model.joblib` along with the
   history's row count and latest date.
2. **Reuse vs. retrain:** `get_forecaster()` keeps the model in memory and reloads it from disk
   after a restart. It retrains only when the history has changed or the saved file can't be
   read.
3. **Model → schedule:** `forecast()` gets scheduled counts for the whole range in one call to
   `scheduling.count_scheduled_staff_between()`, compares each day with the prediction, and
   reports the gap. This is the integration point with the Scheduling module. Until the range
   function exists it calls `count_scheduled_staff()` once per day, and until neither exists,
   `scheduled_staff` and `gap` are `null` instead of the whole forecast failing.
4. **Manager in control:** the forecast only reports gaps. Nothing changes the schedule
   automatically, and both endpoints are manager-only.

5. **Forecast page:** `/forecast` (manager-only) calls `GET /api/forecast` and shows the
   model's error next to the baseline's, then one row per day with predicted vs. scheduled
   staff. Understaffed days are marked "Short by N". **Retrain model** calls
   `POST /api/forecast/train` and refreshes the table.

## How to try it

```bash
flask --app run seed
python run.py
```

Log in as `manager` and open **Forecast**. Pick a start date and 7, 14 or 31 days, or press
**Retrain model** to see fresh metrics. The raw JSON is at
`http://127.0.0.1:5000/api/forecast?days=7`.

## Limitations and next steps

| Limitation | Effect | Next step | Debt |
|------------|--------|-----------|------|
| Training data is synthetic | Accuracy numbers show the pipeline works, not real-world accuracy | Import real attendance and workload data | TD-3 |
| One headcount per day | Doesn't say which shift or position is short | Add shift and position to the history and predict per shift | TD-8 |
| Future workload is a weekday average | A known busy day (holiday, event) is predicted like any other | Let managers enter expected workload for specific days | — |
| Model saved with pickle | A tampered file could run code | Sign the file or store only model parameters | TD-6 |
| Retrain check uses row count and latest date | Editing an old row doesn't trigger a retrain | Track when history was last updated | TD-7 |
| Duplicate dates passed directly to `train()` count twice | Skews averages for callers outside the database | Reject duplicates in `train()` | TD-5 |
| Scheduling gaps are reported, not filled | A manager still has to find cover themselves | Link a short day to Scheduling's replacement recommendations | — |

The end-to-end tests in `tests/test_integration.py` start from `flask seed` and cover training,
the forecast, access control, and the calls into Scheduling (one range call, or one per day as a
fallback). A separate test trains on history with a fixed end date and checks that the model
beats the baseline, so an accuracy regression fails CI.
