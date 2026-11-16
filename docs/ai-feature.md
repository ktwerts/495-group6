# AI Feature: Staffing Demand Forecasting

_Owner: Integration Lead_

> Outline: answer each section as you build. Graders look for a working model, an honest
> evaluation, and a clear integration with the rest of the system.

## What it does

_TODO: one paragraph. From the proposal, it predicts staffing requirements from historical
attendance, workload patterns and scheduled shifts, and supports replacement recommendations
when absences occur._

## Data

_TODO:_

- What does each training row contain, and where does it come from (synthetic for alpha is fine)?
- Which table stores it?

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

_TODO:_

- Which scikit-learn model, and why?
- How is it evaluated? (Use held-out data. For time series, train on older days and test on
  newer ones.)
- What baseline do you compare against, and what are the error numbers?
- What happens with too little history?

## Integration with the rest of the system

_TODO: how forecasting uses `scheduling.count_scheduled_staff()`, how results reach the UI,
and how a manager stays in control._

## How to try it

_TODO: commands or clicks to demo it._

## Limitations and next steps

_TODO: also add these to [technical-debt.md](technical-debt.md)._
