# Stories: Profit Root-Cause Investigation

Team members: **TODO — add your team's names before submission.**

**Start with the [root-cause report](reports/root_cause/REPORT.md) and [executed EDA notebook](notebooks/02_root_cause_investigation.ipynb).** The focus is explaining recorded dollar differences, testing alternative explanations and identifying the evidence needed before changing the business.

The camera and offer planner are supporting prototypes. Their existence is not evidence of root cause or extra profit.

## Main findings

- **Harbour versus Garden:** of the observed $281.54/day gross-profit gap, a symmetric accounting decomposition allocates $145.58/day to transaction counts, $106.80/day to recorded unit costs and $33.59/day to prices, with small offsetting mix, basket-size and discount contributions. These are accounting contributions, not causal effects or recoverable savings.
- **Garden mechanism:** the same products have about 43% higher recorded unit costs and 5% lower prices than Harbour. Product mix does not explain that within-product difference. Cost allocation, actual landed cost and recipes/waste need reconciliation before claiming savings. At Garden's own volumes, the six-month cost-gap sensitivity is $15,923; 25% truly removable would be $3,981 before implementation cost, **conditional on verification**.
- **Tuesday:** the effect persists within weeks, across hours, with illustrative calendar controls and after excluding recorded 15% campaign dates. The adjusted ratio is approximately 1.66, with almost identical mean basket value. The measured mechanism is more transactions, not larger baskets. Payday, hidden promotions, events and data transformations remain competing behavioral explanations; none is proven.
- **Growth:** about 99.6% of the January–June revenue/day accounting increase comes from transaction counts. That does not distinguish footfall, conversion, acquisition or repeat purchases.
- **Tuesday outside the dataset:** real Stories shops in Lebanon show no Tuesday peak in Google Maps popular times (Tuesday index 0.74 to 1.10 across 10 branches, never the busiest day), and a public three-shop benchmark shows none either. This makes a data artifact more likely than a chain-wide driver, without proving it. See [Tuesday: external checks](#tuesday-external-checks).
- **Offers:** two bundles at 10% off are the strongest testable offer (about $6,000 to $20,000 a year at 10 to 20% take-up, a pilot can measure it). See [Offer pilots](#offer-pilots-notebooks-0608).

The source CSV is unchanged. The user's EDA is now in the repository as [notebooks/01_eda.ipynb](notebooks/01_eda.ipynb). Exact duplicates are retained in the primary analysis and checked as a sensitivity; their removal is not automatically justified. Customer first-observed dates and missing IDs are treated cautiously.

## Step 5 — Tuesday versus other working weekdays

Unique transactions are counted per branch/date. **Other weekdays = Monday, Wednesday, Thursday and Friday; weekends are excluded from these comparison values.** There are 78 Tuesday branch-days and 309 comparator branch-days.

| Statistic | Transactions per branch-day |
|---|---:|
| Tuesday mean | 94.846154 |
| Other weekdays mean | 61.796117 |
| Tuesday median | 92.500000 |
| Other weekdays median | 59.000000 |

![Daily transaction distributions by weekday](figures/activity/tuesday_weekday_boxplot.png)

The Tuesday mean is **1.535×** the comparator; its median is also higher. Each branch separately has higher Tuesday mean and median. The pooled boxplot mixes branch sizes and growth over time, so it does not alone establish persistence or causation. The previously reported 25-of-25 complete-week result provides separate persistence evidence. The earlier approximately 1.66 ratio used a different comparator including weekends (or the documented adjusted geometric contrast); do not interchange these ratios.

[Step 5 interpretation](reports/activity/step5_tuesday_distribution.md) · [Exact values and branch diagnostics](reports/activity/step5_tuesday_distribution.json) · [Branch-stratified boxplots](figures/activity/tuesday_weekday_boxplot_by_branch.png). **No model was trained for this step.**

## Step 6 — Daily transaction forecasting features (no training)

Created [02_demand_forecasting.ipynb](notebooks/02_demand_forecasting.ipynb) and local `daily_demand_features.csv`: **543 observations** (3 branches × 181 calendar dates), **0 missing branch-days**, and **0 missing targets**. Missing feature values: Branch, DayOfWeek, Month, DayOfMonth and Weekend **0 each**; Lag1 **3**; Lag7 **21**; RollingMean7 **21**. These initial history blanks remain in the CSV; 522 rows have all requested history available.

The one-day-ahead forecast is issued after the preceding day closes. Lags are calculated separately within branch on the dense calendar; the shifted rolling average excludes the target date and requires all seven prior dates. Unknown branch-days are not set to zero. Temporal-isolation and missing-day propagation checks passed. No model was trained or selected in this step.

[Full audit and first 15 rows](reports/demand_forecasting/REPORT.md) · [Feature summary](reports/demand_forecasting/feature_summary.json) · [Missing-date list](reports/demand_forecasting/missing_branch_days.csv). Reproduce with `python src/prepare_daily_demand.py --data /path/to/stories_transactions.csv`; regenerate the executed notebook with `STORIES_DATA=/path/to/stories_transactions.csv python src/build_demand_notebook.py`.

## Step 7 — First daily demand models

Executed [03_ml_demand_models.ipynb](notebooks/03_ml_demand_models.ipynb) with train Jan 8–Apr 30 (339 rows), May validation (93) and June test (90). Four fixed Random Forest settings and four fixed XGBoost settings were chosen using May MAE only. Each selected ML pipeline refit Jan 8–May 31 before the final rolling one-day June evaluation. Preprocessing is fitted only on the applicable training period; no June tuning occurs.

| Model | May MAE | June MAE | June RMSE | June WAPE |
|---|---:|---:|---:|---:|
| Seasonal naive | 8.9355 | 9.6000 | 11.6113 | 12.51% |
| Random Forest | 9.1987 | 10.0521 | 13.4934 | 13.10% |
| XGBoost | 8.2523 | 9.1015 | 12.2786 | 11.86% |

**XGBoost was selected on May and has 5.19% lower June MAE than seasonal naive**, but seasonal naive has the better June RMSE and wins Harbour MAE. XGBoost wins Garden and Uptown MAE. Random Forest loses to seasonal naive overall. The paired-date 95% interval for the selected model's MAE improvement is −0.7294 to 1.8134 transactions/day, including zero; the modest observed improvement is not established as reliably generalizable. No branch-specific hybrid is selected from June.

![Actual versus predicted daily transactions](figures/demand_forecasting/june_actual_vs_predicted.png)

[Full validation/test and branch results](reports/demand_forecasting/STEP7_REPORT.md) · [All eight validation trials](reports/demand_forecasting/validation_search.csv) · [Selection lock](reports/demand_forecasting/selection_lock.json) · [Model manifest](reports/demand_forecasting/best_model_manifest.json). The May-selected model bundle is `artifacts/daily_demand_models/best_model.joblib` (ignored, fit through May 31). Predictions and both ML pipelines are saved alongside it. Reproduce: `python src/train_daily_models.py --data daily_demand_features.csv`; build the executed notebook with `python src/build_ml_demand_notebook.py`. Verify with `python src/verify_daily_models.py`.

MAE/RMSE are transaction counts per branch-day; WAPE is aggregate absolute error divided by observed transactions, not accuracy. June was inspected in earlier project work; this is an internal chronological holdout. These results do not measure a dollar benefit or crisis resilience. Original data and source features are unchanged.

## Step 8 — Does the forecast improvement change the dollars?

Created and executed [04_forecast_business_value.ipynb](notebooks/04_forecast_business_value.ipynb), using frozen Step 7 June predictions and original recorded line gross profit. **No models were retrained; source, saved predictions, selection lock and model hashes are unchanged.**

Prepare nearest-integer transaction-equivalent capacity from each forecast. Nine explicitly hypothetical scenarios combine shortage penalties of 25%/50%/100% of Jan–May branch GP/transaction with excess penalties of 10%/25%/50% of Jan–May recorded input cost/transaction. The oracle has zero shortage/excess cost by construction. Every method uses the same 90 June branch-days; June economics are descriptive, never used to calibrate penalties.

**Seasonal naive has lower overall assumed decision cost in 8/9 scenarios.** XGBoost wins all nine at Garden and Uptown; naive wins all nine at Harbour. Harbour's shortage total increases from 193 to 294 transaction-equivalents under XGBoost, offsetting its reduction in excess preparation. Continuous-capacity sensitivity retains every winner.

| Shortage penalty / historical GP | Excess penalty / historical input cost | Naive total | XGBoost total | Lower assumed cost |
|---|---|---:|---:|---|
| 25% | 50% | $1,375.67 | $1,318.36 | XGBoost by $57.32 |
| 50% | 25% | $1,599.31 | $1,734.80 | Naive by $135.49 |
| 100% | 10% | $2,584.20 | $2,988.57 | Naive by $404.37 |

These are **total June hypothetical decision-cost comparisons, not actual savings** or operating profits. Transaction capacity is a proxy; stockouts, waste, salvage, SKU mix, labor and deployment cost are unobserved. June branch winners may motivate a prospectively validated branch policy, but do not validate selecting a hybrid from the test results.

[All nine scenarios, branch results and assumptions](reports/forecast_business_value/REPORT.md) · [Cost components](reports/forecast_business_value/decision_costs.csv) · [Paired differences](reports/forecast_business_value/model_comparison.csv) · [Historical transaction economics](reports/forecast_business_value/historical_economics.csv). Reproduce without training: `python3 src/forecast_business_value.py --data /path/to/stories_transactions.csv`; build the notebook with `python3 src/build_forecast_business_value_notebook.py`; verify with `python3 src/verify_forecast_business_value.py`.

## Step 9 — Exploratory hybrid forecasting policy

Created and executed [05_hybrid_forecasting_strategy.ipynb](notebooks/05_hybrid_forecasting_strategy.ipynb). Policy A uses seasonal naive everywhere; B uses XGBoost everywhere; C uses naive at Harbour and XGBoost at Garden/Uptown. All use the same saved Step 7 June predictions and nine Step 8 hypothetical cost scenarios. No models were retrained; the original dataset, saved forecasts/models and Step 8 evidence are unchanged.

**The hybrid has lower overall assumed cost in 9/9 scenarios**, improving on all-naive by **$44.65–$182.05**, on all-XGBoost by **$1.09–$572.67**, and on the stronger uniform policy in each scenario by **$1.09–$182.05** over June. Branch-level ties are explicit: hybrid equals naive at Harbour and XGBoost at Garden/Uptown.

**The hybrid was chosen after seeing June. This is a hindsight comparison, not independent validation or proven savings.** It mechanically combines previously observed branch winners. Nine scenarios reuse the same errors; implementation and monitoring costs could consume the modest advantage. The next step is to select/lock branch rules using earlier validation and contemporaneously available economics, then test on genuinely later dates or in a prospective shadow pilot. The report explains why a May selection must use Jan–Apr economics rather than leak Jan–May averages into validation.

[All costs, improvements and methodology](reports/hybrid_forecasting/REPORT.md) · [Comparison CSV](reports/hybrid_forecasting/model_comparison.csv) · [Cost components](reports/hybrid_forecasting/decision_costs.csv) · [Comparison chart](figures/hybrid_forecasting/policy_cost_comparison.png). Reproduce without training: `python3 src/hybrid_forecasting_strategy.py --data /path/to/stories_transactions.csv`; `python3 src/build_hybrid_forecasting_notebook.py`; `python3 src/verify_hybrid_forecasting.py`.

## Profit Lab — Ideas 9–15 implemented

[Open the private Profit Lab](https://stories-drink-lens-aya.sprycorgi128.chatgpt.site/profit-lab.html) · [Full evidence and assumptions](reports/profit_lab/REPORT.md) · [Executed notebook](notebooks/04_profit_lab.ipynb) · [Machine-readable results](reports/profit_lab/findings.json).

| Idea | Implementation | What the evidence supports |
|---|---|---|
| 9. Basket completion | Smoothed drink/branch product probabilities; margin-weighted recommendations | June retrieval test; conditional margin rule loses to the simpler popularity margin rule. No proven extra sales. |
| 10. One-dollar challenge | Minimum whole-cent uniform menu price step within each branch; demand-loss sensitivity | At unchanged volume, Harbour +1¢ yields $1.43/day; Garden +2¢ $1.96/day; Uptown +2¢ $1.12/day. Tiny volume losses can erase these gains. |
| 11. Menu alternatives | Same-category purchasing-profile similarity, margin and assumed ingredient filters | Candidate investigation tool; similarity does not establish customer substitution or safe ingredients. |
| 12. Profit at risk | Quantile gradient boosting, May lower-bound calibration, June evaluation | June pinball loss 14.86 versus baseline 20.69; 90% lower-bound coverage. 27 alerts contain only 3 actual low-profit days. |
| 13. Discount review | Recorded discount exposure and margin screening | $2,178.09 exposure, not guaranteed recoverable savings or evidence of ineffective promotions. |
| 14. Portfolio attention | Forecast units × historical realized unit GP versus popularity | Top-three selections capture $4,970.80 of existing June GP versus $4,720.01 for historical popularity; no incremental promotional impact measured. |
| 15. Crisis planning | Integer menu/stock optimization; six scenarios; two feasible baselines | Simulation with assumed budgets, capacities and ingredient proxies. The optimizer loses to the margin rule in the milk-unavailable scenario. No war validation. |

The interactive page includes all seven modules, branch controls, sensitivity/scenario selectors and an aggregate evidence download. July 1 examples are historical planning demonstrations. No live prices, offers, orders or inventory are changed. The root-cause investigation remains the submission's main argument; these tools support testable decisions after that investigation.

Reproduce after generating the existing daily features and product forecast artifacts:

```sh
python3 src/profit_lab.py --data /path/to/stories_transactions.csv --features daily_demand_features.csv
python3 src/build_profit_lab_report.py
python3 src/build_profit_lab_notebook.py
python3 src/verify_profit_lab.py
```

June was examined in earlier work, so these are exploratory internal holdouts. Basket metrics are retrieval measures; the profit-risk target uses pinball loss and coverage. None inherits the earlier category model's AUC.

## Tuesday: external checks

[Full report](reports/tuesday_external/REPORT.md) · [Google Maps readings](reports/tuesday_external/google_popular_times.csv) · [EDA notebook](notebooks/01_eda.ipynb)

Ten explanations were tested inside the dataset (promotions, product or category events, one-branch events, catering, a Tuesday customer segment, repeat visits, double posting, payday and calendar). None explains the spike; it behaves like a uniform multiplier on every branch, hour, product and customer. Two outside checks followed. Ratios below are a **weekday index** (a weekday's average divided by the branch's seven-day average), not the 1.535× weekday comparator in Step 5.

| | Mon | **Tue** | Wed | Thu | Fri | Sat | Sun |
|---|---|---|---|---|---|---|---|
| Stories dataset (3 branches) | 0.95 | **1.52** | 0.99 | 0.97 | 1.05 | 0.69 | 0.83 |
| Real Stories shops, Google Maps (mean of 10) | 0.93 | **0.95** | 1.00 | 1.02 | 1.11 | 1.01 | 0.97 |
| Maven Roasters benchmark (3 NYC shops) | 0.97 to 1.04 | **0.97 to 1.03** | 0.98 to 1.01 | 1.00 to 1.02 | 1.00 to 1.03 | 0.98 to 1.02 | 0.97 to 1.01 |

The evening peak matches real shops; the Tuesday spike and the weak Saturday do not. Popular times are relative phone-location busyness from recent months, not Jan to Jun 2026 sales, and the dataset's branches cannot be matched to real shops. **Cheapest next step:** compare raw POS totals for a few Tuesdays with this file and check the marketing calendar.

## Offer pilots (notebooks 06–08)

These notebooks remove the 132 exact duplicate rows (see [01_eda.ipynb](notebooks/01_eda.ipynb)); the primary analysis above keeps them. Money figures are **changes in gross profit**, estimated for a 4-week pilot (6 Jul to 2 Aug 2026) with a trend forecast tested on unseen months (9% WAPE vs 22% for a weekday average). Take-up is unknown in this data, because no bundle was ever sold and past discounts were not random, so every notebook ends in a pilot, not a rollout.

| Notebook | Offer | Measured | Estimated | Recommendation |
|---|---|---|---|---|
| [06_bundle_offers.ipynb](notebooks/06_bundle_offers.ipynb) | Bakery + matcha/tea, and cold drink + sandwich, 10% off | Pairs chosen Jan–Mar, confirmed Apr–Jun (lift 1.8 and 2.1). Break-even take-up 3–6% at Harbour/Uptown, 5–9% at Garden | −$578 (no take-up) to +$1,534 per 4 weeks; about $6,000–$20,000/yr at 10–20% take-up | 4-week pilot at all branches; detects ~4% take-up |
| [07_couple_offer.ipynb](notebooks/07_couple_offer.ipynb) | With 2+ drinks, a bakery item 20% off | Two-drink baskets have food 23% vs 47%, but mostly because baskets never exceed 3 lines. Group orders cannot be targeted by time | −$107 to +$236 per 4 weeks; about $800–$3,000/yr | Check real till data first; pilot only if real groups skip food |
| [08_slow_seller_addons.ipynb](notebooks/08_slow_seller_addons.ipynb) | Slow sellers as add-ons at 30% off (best: Quinoa Bowl with a cold drink) | Slow sellers are cheapest to discount: median break-even 1.5% vs 3.8%, because few customers already buy them | $133–$273 per 100 add-ons; waste savings (assumed) add 30–70% | 8-week A/B pilot against popular items; a low result flags the item for menu removal |

`08` corrects the "rejected: pushing slow sellers" point inside `06`, which judged slow sellers on margin percentage alone. The offers overlap on bakery, so their estimates must not be added and their pilots should run in separate weeks. Garden's higher recorded unit costs (see the root-cause findings above) roughly double the take-up its offers need to break even.

**Run them:** put the CSV at `data/stories_transactions.csv` (ignored by git) or set `STORIES_DATA=/path/to/stories_transactions.csv`, then open the notebooks from the repository root or `notebooks/`. Figures are written to `figures/eda/`, `figures/bundle_offers/`, `figures/couple_offer/` and `figures/slow_seller_addons/`.

## Reproduce the investigation

Tested with the package versions in `requirements.txt`. For notebook generation/verification, also install `requirements-notebooks.txt`.

```sh
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt -r requirements-notebooks.txt
export MPLCONFIGDIR=/tmp/stories-matplotlib
python src/root_cause.py --data /path/to/stories_transactions.csv
python src/tuesday_distribution.py --data /path/to/stories_transactions.csv
python src/build_root_cause_report.py
STORIES_DATA=/path/to/stories_transactions.csv python src/build_root_cause_notebook.py
python src/verify_root_cause.py --data /path/to/stories_transactions.csv
```

The notebook builder executes cells in-process through IPython, embeds real outputs, and requires no notebook server. Set `STORIES_DATA` when opening/rerunning it against a different input location. Raw input is never bundled. Source fingerprint, model specification and detailed evidence are in [findings.json](reports/root_cause/findings.json). Daily panels, matched-product ratios, branch decompositions and calendar robustness CSVs are alongside it.

## Supporting work

| Component | Evidence / setup | Role |
|---|---|---|
| Daily demand ML | [Original report](reports/REPORT.md), [metrics](reports/forecast_metrics.json) | Supporting operational forecast; 3.5% lower June MAE than the seasonal blend |
| Hourly revenue/demand ML and offers | [Offer Studio report](reports/BUNDLE_PLANNER.md), [metrics](reports/bundle_forecast_metrics.json) | Tested forecasts plus explicit pilot policies and accounting scenarios; no proven uplift |
| Drink recognition | [App setup](drink-lens/README.md), [verification](reports/DRINK_LENS.md) | Experimental discovery feature; vision accuracy unmeasured |
| Add-on prediction | [Metrics](reports/metrics.json) | Pooled 0.745 AUC but weak within-category signal; no causal recommendation benefit |

Additional reproducibility scripts are in `src/`; each model pipeline accepts `--data`. The original report's historical recommendations are superseded in priority by the root-cause investigation. June was already inspected in earlier project work, so additional tasks are exploratory internal holdouts and need prospective validation.

## Submission

Fill in team names and submit one public GitHub repository URL. This workspace contains source and aggregate evidence; no public GitHub submission has been created. Source CSVs, individual prediction records, serialized models and exports stay in ignored `data/` or `artifacts/` folders. Do not put the company CSV at the repository root. Review aggregate evidence for permitted release before publication. The private app deployment is separate from the public-repository submission.
