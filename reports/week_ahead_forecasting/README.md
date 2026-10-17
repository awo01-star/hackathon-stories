# Week-ahead planning: extension to notebooks 02–05

**Business use:** plan all seven daily branch totals before the week begins.
Notebook 03 addresses next-day updates; this study refits weekly and forecasts
seven days at once. It does not replace the team's profit/root-cause argument.

## Measured historical forecast performance

| method | WAPE (%) | 100-WAPE (%) | MAE | RMSE | Bias (%) |
|---|---|---|---|---|---|
| baseline | 9.044 | 90.956 | 6.940 | 8.859 | 0.415 |
| seasonal_naive_4_weeks | 9.894 | 90.106 | 7.592 | 9.989 | -4.435 |
| selected | 8.828 | 91.172 | 6.774 | 8.922 | -1.252 |

June contains 90 matched branch-days. Recipe selection uses March/April and May;
all fits exclude their target week. Previously completed June weeks may enter
later training. June was inspected before this extension: results are exploratory.
100%-WAPE is an error shorthand, not exact-match accuracy or a confidence level.

The descriptive 95% interval for WAPE reduction against the regression baseline is
-0.133 to
+0.593 percentage points;
approximate DM/HAC p=0.2076. The gain is not conclusive.
The selected model's RMSE is slightly worse than the regression baseline.

## Hypothetical business decision test

Reuse notebook 04's original Jan–May GP/input-cost accounting and shortage/excess
formulas without rewriting its reports or running its pipeline. All nine penalty
combinations are reported for every weekly model, with integer and continuous
capacity. There is no cost-based retuning or selection from June.

- integer capacity vs baseline: selected forecast has lower assumed cost in 1/9 scenarios; total June cost difference (benchmark minus selected) ranges from $-233.77 to $+51.88.
- integer capacity vs seasonal_naive_4_weeks: selected forecast has lower assumed cost in 9/9 scenarios; total June cost difference (benchmark minus selected) ranges from $+64.96 to $+742.08.
- continuous capacity vs baseline: selected forecast has lower assumed cost in 1/9 scenarios; total June cost difference (benchmark minus selected) ranges from $-238.87 to $+54.26.
- continuous capacity vs seasonal_naive_4_weeks: selected forecast has lower assumed cost in 9/9 scenarios; total June cost difference (benchmark minus selected) ranges from $+66.51 to $+770.36.

These are scenario-dependent penalties, **not measured savings or profit uplift**.
Do not deploy the lowest-WAPE recipe on that score alone. Retain the regression
baseline in the prospective pilot: under the current assumptions it can have
lower preparation penalties despite slightly higher absolute prediction error.
The nine scenarios reuse the same errors. Recorded costs may include allocation;
actual waste, lost sales, salvage, labour, service delays and implementation costs
are unknown. Transaction capacity is a proxy and cannot specify product orders.

## Relationship to the team's existing findings

- Notebook 03's next-day XGBoost and this weekly model have different information
  schedules and refitting rules. Their scores cannot establish a controlled winner.
- Notebook 05's branch hybrid was proposed after inspecting June; this is a global
  May-selected blend, not a retrospective selection of June branch winners.
- Notebook 10's shared weekday rhythm motivates pooling; it does not establish
  that today's real branches follow the same pattern. Check raw POS and promotions.
- Garden cost/price investigation, offers and long-term profit outlook remain
  separate. Forecast accuracy does not validate a promotion or recoverable cash.

**Pilot:** freeze the recipe, store weekly forecasts before sales arrive, compare
with normal planning on newly collected weeks, and measure paid hours, service
delays, availability and waste. Verify opening hours and operational penalties.

## Reproduce and inspect

Set `STORIES_DATA` to the supplied CSV or use `data/stories_transactions.csv`.
Run [notebook 12](../../notebooks/12_week_ahead_demand_forecasting.ipynb), then
[notebook 13](../../notebooks/13_week_ahead_validation.ipynb), each with a fresh
kernel and Run All. Source code is in `src/stories_coffee/` and
`src/week_ahead_integration.py`. Supplemental dependencies are in
`requirements-week-ahead.txt`; the team's original requirements are unchanged.

Published evidence contains aggregate metrics, selection/protocol, source hash,
runtime versions, calibration economics and decision costs. Detailed forecasts,
saved coefficients and the next forecast stay under ignored
`artifacts/week_ahead_forecasting/`. No raw CSV or individual transaction records
are added. Missing branch-days stop fitting rather than being imputed as zero.
The default next forecast starts 2026-07-01, after source
end 2026-06-30; it is a historical example, not today's forecast.

Audit status: **PASS** (20223 computation checks).
This verifies consistency rather than prospective accuracy. Run
`python src/verify_week_ahead.py` after both notebooks to check the integration.
