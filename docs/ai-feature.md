# AI Feature: Staffing Demand Forecasting

_Owner: Integration Lead_

> Outline: answer each section as you build. Graders look for a working model, an honest
> evaluation, and a clear integration with the rest of the system.

## What it does

_TODO: one paragraph. From the proposal, it predicts staffing requirements from historical
attendance, workload patterns and scheduled shifts, and supports replacement recommendations
when absences occur._

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
average workload unless a value is passed in. Predictions are rounded **up** to a whole
person, with a minimum of 1, because being one person short is worse than having one extra.

**Too little history:**

| History | Behavior |
|---------|----------|
| None | `train()` raises `ValueError` (the API turns it into a 400) |
| Under 28 days | Falls back to the weekday average; `method` is `weekday_average` |
| 28 days or more | Random forest; `method` is `random_forest` |

## Integration with the rest of the system

_TODO: how forecasting uses `scheduling.count_scheduled_staff()`, how results reach the UI,
and how a manager stays in control._

## How to try it

_TODO: commands or clicks to demo it._

## Limitations and next steps

_TODO: also add these to [technical-debt.md](technical-debt.md)._
