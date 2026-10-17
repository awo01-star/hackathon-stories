### Step 6 — Daily branch transaction forecasting dataset

**No model trained.** Created [02_demand_forecasting.ipynb](../../notebooks/02_demand_forecasting.ipynb) and local [daily_demand_features.csv](../../daily_demand_features.csv). The panel has **543 observations** (3 branches × 181 dates, Jan 1–Jun 30, 2026), **0 missing branch-days**, and **0 missing target values**. Target is unique observed transactions per branch/date, not unconstrained demand.

| Requested feature | Missing values |
|---|---:|
| Branch | 0 |
| DayOfWeek | 0 |
| Month | 0 |
| DayOfMonth | 0 |
| Weekend | 0 |
| Lag1 | 3 |
| Lag7 | 21 |
| RollingMean7 | 21 |

Initial history blanks are expected: one lag-1 value per branch and seven lag-7/rolling values per branch. All rows remain in the CSV; 522 have complete requested features and target. No filling or dropping is performed. DayOfWeek is a name, Weekend is Saturday/Sunday = 1, and MissingBranchDay is an audit flag rather than a predictor. Date and all other exported calendar/audit columns have no missing values in this file.

All dates are explicitly reindexed within branch. Missing branch-days, if present, remain unknown. Lag1 and Lag7 refer to one/seven calendar days earlier; RollingMean7 uses a shift of one day and requires all seven preceding calendar dates. A missing observation propagates rather than silently becoming zero or an average over fewer days.

The forecast origin is **after the previous day closes**. These features are not a valid drop-in setup for forecasts issued a full week ahead. Calendar features are known in advance; observed branch-day presence does not prove full-day opening or absence of stockouts.

First 15 rows (sorted branch/date):

```text
Branch       Date DayOfWeek  Month  DayOfMonth  Weekend  Lag1  Lag7  RollingMean7  Transactions  MissingBranchDay
Garden 2026-01-01  Thursday      1           1        0  <NA>  <NA>           NaN            48             False
Garden 2026-01-02    Friday      1           2        0    48  <NA>           NaN            48             False
Garden 2026-01-03  Saturday      1           3        1    48  <NA>           NaN            36             False
Garden 2026-01-04    Sunday      1           4        1    36  <NA>           NaN            47             False
Garden 2026-01-05    Monday      1           5        0    47  <NA>           NaN            32             False
Garden 2026-01-06   Tuesday      1           6        0    32  <NA>           NaN            73             False
Garden 2026-01-07 Wednesday      1           7        0    73  <NA>           NaN            40             False
Garden 2026-01-08  Thursday      1           8        0    40    48     46.285714            37             False
Garden 2026-01-09    Friday      1           9        0    37    48     44.714286            50             False
Garden 2026-01-10  Saturday      1          10        1    50    36     45.000000            43             False
Garden 2026-01-11    Sunday      1          11        1    43    47     46.000000            36             False
Garden 2026-01-12    Monday      1          12        0    36    32     44.428571            48             False
Garden 2026-01-13   Tuesday      1          13        0    48    73     46.714286            80             False
Garden 2026-01-14 Wednesday      1          14        0    80    40     47.714286            62             False
Garden 2026-01-15  Thursday      1          15        0    62    37     50.857143            47             False
```

Temporal checks executed in the notebook: deleting June 1 and later records does not change June 1 or earlier predictors; deleting Garden January 20 leaves its target unknown and correctly propagates missing lags/rolling history; unique keys and the 33,887 source transactions reconcile; CSV missingness survives serialization. These checks modify copies only. The original transaction file is unchanged.

Reproduce: `python3 src/prepare_daily_demand.py --data /path/to/stories_transactions.csv`. To regenerate the executed notebook: `STORIES_DATA=/path/to/stories_transactions.csv python3 src/build_demand_notebook.py`. [Machine-readable audit](../demand_forecasting/feature_summary.json); [missing-date list](../demand_forecasting/missing_branch_days.csv). No baseline fitting, imputation, model training or model selection took place in Step 6.
