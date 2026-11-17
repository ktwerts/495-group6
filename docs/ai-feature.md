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

_TODO: list each feature in `app/forecasting/features.py` and why it should help (pattern
recognition)._

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
