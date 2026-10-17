### Step 8 — Do better demand forecasts improve financial decisions?

Uses the **saved Step 7 June predictions**, with no retraining, prediction regeneration or cost-based model selection. Each model scores the same 90 branch-days (June 1–30, three branches). These remain rolling next-day forecasts after yesterday closes, not a single month-ahead forecast. June was already examined elsewhere in the project: these are exploratory internal comparisons.

#### Historical economics, separated from assumed costs

First sum recorded line gross profit within each unique transaction ID, verifying branch/date consistency, then divide total transaction GP by transaction count per branch. Recorded input cost is Quantity × recorded unit cost, also aggregated per transaction. All recorded rows are retained; identical-line origin is unresolved. No claim that these costs are avoidable cash costs is implied.

Jan–May values below price every June decision. Full six-month and June-only descriptive values are saved separately; June realized margins are not used to set penalty rates.

| Branch | Transactions | RecordedGPUSD | GPPerTransactionUSD | InputCostPerTransactionUSD |
|---|---|---|---|---|
| Garden | 8912 | $37,379.76 | $4.19 | $4.74 |
| Harbour | 12948 | $77,249.43 | $5.97 | $3.22 |
| Uptown | 5121 | $28,026.31 | $5.47 | $3.27 |

#### Hypothetical operational policy and nine scenarios

Prepared capacity is **floor(max(forecast,0) + 0.5)** transaction-equivalents, the same nearest-integer policy for both models. This is an illustrative aggregate capacity proxy, not SKU inventory or staffing. A continuous-capacity sensitivity is also saved. No safety buffer or economically optimal quantile is selected from June.

- Shortage penalty: **25%, 50% or 100% of Jan–May branch GP/transaction** per unserved transaction-equivalent. This assumes that fraction of recorded gross margin is at risk; actual balking, queues, recapture and lifetime value are unobserved.
- Over-preparation penalty: **10%, 25% or 50% of Jan–May recorded branch input cost/transaction** per excess transaction-equivalent. This assumes that fraction is prepared, unsalvageable and avoidable; recipes, waste and salvage are unobserved. It is not measured waste.
- Evaluate all nine cross-products without choosing a preferred rate from the result. Shortage/excess quantities are identical across scenarios for a model; only their prices change.

`Shortage = max(actual − capacity, 0)`; `Excess = max(capacity − actual, 0)`.

`Decision cost = shortage × assumed shortage penalty + excess × assumed over-preparation penalty`.

The **oracle** sets capacity equal to observed demand, so both penalties equal zero by construction. It is an unattainable information benchmark, not a competing deployable model. Costs represent regret-like penalties, not total operating expenditure, accounting profit or actual savings. Do not subtract them from recorded GP and call the result measured profit.

#### Overall June results (USD)

Positive **NaiveMinusXGBoostUSD** means a lower assumed cost for XGBoost; negative means seasonal naive wins. Differences are computed before rounding.

| Scenario | Seasonal naive | XGBoost | Oracle | NaiveMinusXGBoostUSD | Winner |
|---|---|---|---|---|---|
| S0.25_W0.1 | $761.25 | $837.34 | $0.00 | $-76.08 | Seasonal naive |
| S0.25_W0.25 | $991.66 | $1,017.72 | $0.00 | $-26.06 | Seasonal naive |
| S0.25_W0.5 | $1,375.67 | $1,318.36 | $0.00 | $57.32 | XGBoost |
| S0.5_W0.1 | $1,368.90 | $1,554.42 | $0.00 | $-185.51 | Seasonal naive |
| S0.5_W0.25 | $1,599.31 | $1,734.80 | $0.00 | $-135.49 | Seasonal naive |
| S0.5_W0.5 | $1,983.32 | $2,035.44 | $0.00 | $-52.11 | Seasonal naive |
| S1_W0.1 | $2,584.20 | $2,988.57 | $0.00 | $-404.37 | Seasonal naive |
| S1_W0.25 | $2,814.61 | $3,168.96 | $0.00 | $-354.35 | Seasonal naive |
| S1_W0.5 | $3,198.62 | $3,469.60 | $0.00 | $-270.98 | Seasonal naive |

**Observed outcome:** seasonal naive wins 8 of 9 overall scenarios; XGBoost wins 1. This does not establish a universal financial improvement from the MAE winner.

Garden: {'XGBoost': 9}. Harbour: {'Seasonal naive': 9}. Uptown: {'XGBoost': 9}. 

With integer capacity, Harbour's shortage totals are 193 transaction-equivalents under naive and 294 under XGBoost; excess totals are 144 and 51, respectively. Shortage-heavy assumptions price that tradeoff against XGBoost. Overall naive-minus-XGBoost differences range from $-404.37 to $57.32. These are total June differences, before implementation costs, not per-day savings.

Continuous-capacity sensitivity changes the winner in 0 of 36 branch/overall scenario comparisons.

![Hypothetical cost differences](../../figures/forecast_business_value/decision_cost_difference.png)

#### Winners by branch across the nine assumptions

| Branch | Seasonal naive | XGBoost |
|---|---|---|
| ALL | 8 | 1 |
| Garden | 0 | 9 |
| Harbour | 9 | 0 |
| Uptown | 0 | 9 |

These scenario rows reuse the same errors and are not independent confirmations. Branch winners are descriptive: do not create and claim an out-of-sample branch-specific hybrid using June. Instead predefine a branch policy using earlier validation and verified operational costs, then compare prospectively on later dates.

#### Directional errors explain the cost differences

| Branch | Model | ShortageTransactions | ExcessTransactions |
|---|---|---|---|
| Garden | Oracle | 0.0 | 0.0 |
| Garden | Seasonal naive | 151.0 | 156.0 |
| Garden | XGBoost | 113.0 | 166.0 |
| Harbour | Oracle | 0.0 | 0.0 |
| Harbour | Seasonal naive | 193.0 | 144.0 |
| Harbour | XGBoost | 294.0 | 51.0 |
| Uptown | Oracle | 0.0 | 0.0 |
| Uptown | Seasonal naive | 118.0 | 102.0 |
| Uptown | XGBoost | 117.0 | 77.0 |

A lower pooled MAE can coexist with higher shortage or excess at one branch. Different penalties and branch GP/input costs reweight those directional errors. The saved branch comparison reports both cost components, not just a single score.

Transaction sales are used as a demand proxy; lost sales and actual capacity are unobserved. If historical sales were already constrained, even the oracle's observed-demand benchmark understates true demand. Product mix, transaction size, batch constraints, perishability, labor, fixed costs, model maintenance and service effects are omitted. A small assumed advantage could be outweighed by these costs. None of this validates wartime behavior or promotion effects.

**Business action:** inspect where under/over-forecasting occurs, verify shortage and salvage costs with operations, and run a shadow pilot using prospectively fixed capacity rules. Measure actual stockouts, waste, queues, service costs and GP. Retain a baseline where it wins; neither lower MAE nor simulated dollar differences justify universal deployment.

Files: `notebooks/04_forecast_business_value.ipynb`; `reports/forecast_business_value/historical_economics.csv`; `decision_costs.csv`; `model_comparison.csv`; `continuous_model_comparison.csv`; `scenario_unit_costs.csv`; `findings.json`; and `figures/forecast_business_value/decision_cost_difference.png`. Row-level hypothetical decisions stay in ignored `artifacts/forecast_business_value/`.

Reproduce without training: `python3 src/forecast_business_value.py --data /path/to/stories_transactions.csv`; `python3 src/build_forecast_business_value_notebook.py`. Original data, predictions and saved models are unchanged.
