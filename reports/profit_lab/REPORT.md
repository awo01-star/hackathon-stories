# Profit Lab — implemented Ideas 9–15

Seven runnable extensions accompany the root-cause investigation. They are not seven proven profit opportunities. Every module labels historical prediction, accounting sensitivity or assumed simulation. No offers, rewards, purchases, inventory transfers or menu changes are activated.

Planning examples are for **July 1, 2026**, from records through **June 30**. None is a current forecast or validated wartime model. The original transaction CSV is unchanged; the aggregate web payload contains no customer or transaction identifiers. June was inspected earlier in this project, so all new model tasks are exploratory internal holdouts, not untouched external tests.

## 9. Profit-aware basket completion

A smoothed empirical model estimates product presence given branch and an anchor drink, then ranks by probability or probability × branch/product realized unit GP. Twenty-two food candidates per beverage basket are evaluated. The alphabetically first drink is selected from the completed basket without reading food labels; the absence of item order prevents claiming real-time next-item prediction.

Fit Jan–Apr, choose smoothing from {20,100} by May pooled product-pair log loss, refit Jan–May, evaluate June. No customer history, final basket size, revenue, or purchased food labels enter prediction features. Category AUC from earlier work is not this product-level evaluation.

| Policy | June hit@1 | June hit@3 | Matched unit-GP proxy/basket | Log loss |
|---|---:|---:|---:|---:|
| branch_popularity_probability | 4.46% | 10.52% | $0.1079 | 0.09459 |
| branch_popularity_profit_weighted | 4.06% | 8.72% | $0.1118 | 0.09459 |
| drink_branch_smoothed_probability | 3.93% | 10.86% | $0.0992 | 0.09494 |
| drink_branch_smoothed_profit_weighted | 3.21% | 9.23% | $0.1011 | 0.09494 |

There are **4,734 June beverage baskets**. The conditional margin rule **loses to the branch-popularity margin rule** on hit@1 and matched GP. Profit weighting need not improve retrieval accuracy. The matched margin proxy rewards selecting an item already in the observed basket, one unit at historical GP; it is not incremental profit or observed acceptance of a recommendation.

To estimate impact: randomize no prompt, popularity prompt and margin prompt; keep eligibility and stock availability equivalent; log assignment, exposures and completed baskets; compare net total basket GP including prompt cost and purchases that would happen anyway. Do not present this model as a demonstrated improvement in sales.

## 10. The one-dollar challenge

Search a defined policy family: the smallest **whole-cent uniform price increase across a branch's menu** that adds at least $1/day at unchanged quantities, mix, unit costs and discount percentages. This is a constrained accounting search, not a universal optimum over all possible pricing/mix actions. Single-SKU candidates are also enumerated with at most a 5% list-price increase. Prices are USD as recorded; real price-step/rounding rules need verification.

| Branch | Whole-cent price step | Affected units/day | Affected transactions/day | Fixed-volume GP/day gain | Break-even uniform unit loss |
|---|---:|---:|---:|---:|---:|
| Garden | $0.02 | 98.52 | 61.67 | $1.96 | 0.752% |
| Harbour | $0.01 | 144.16 | 90.24 | $1.43 | 0.264% |
| Uptown | $0.02 | 56.14 | 35.30 | $1.12 | 0.576% |

For an assumed uniform unit loss L, daily GP change = `(1−L)×(current GP/day + fixed-volume price gain) − current GP/day`. Unit costs scale with units, with no change in product mix or fixed costs; this is not a price elasticity estimate. Tiny percentage volume losses can erase the gain. No additional purchases, discount-policy changes or real margin improvement are proven.

## 11. Menu alternatives under constraints

Generate same-category alternatives using cosine similarity of Jan–May hourly product-sales profiles. Show each alternative's recorded branch margin and the assumed resource groups. Filter candidates if a selected assumed resource is unavailable. Empty candidate sets remain empty; demand is never silently transferred.

This is a candidate-finding tool, **not a validated substitution model**. Similar hourly profiles can reflect a common calendar rather than customer switching preferences. Actual out-of-stock events, exposed alternatives, choices and recipes are needed to estimate substitution. Resource membership (coffee, milk, matcha, bakery) is an illustrative serving-equivalent proxy; it is not verified recipe or allergen information. Manual review is required before using it operationally.

## 12. Profit-at-risk forecasting

Target: recorded daily branch GP. Inputs: the eight Step 6 date/lagged-transaction features, without same-day sales or GP. A fixed gradient boosting 10th-quantile model fits Jan 8–Apr 30; May supplies a conservative one-sided calibration correction. The Jan–Apr model stays fixed for June, so calibration is not reused after a model refit. The baseline is each branch's Jan–Apr GP 10th percentile.

| June method | Pinball loss ↓ | Lower-forecast coverage | Mean lower forecast |
|---|---:|---:|---:|
| branch_train_quantile | 20.686 | 98.9% | $204.83 |
| quantile_model | 14.858 | 90.0% | $274.38 |

Lower pinball loss improves quantile forecasting relative to the conservative unconditional baseline; higher coverage alone is not the objective. The learned lower forecast has **90.0% empirical coverage** over 90 June branch-days. It is not a guaranteed financial floor. May calibration uses 93 correlated branch-days; temporal dependence, shared branches and distribution shift prevent asserting a simple distribution-free coverage guarantee.

An alert means the lower forecast crosses the branch's Jan–Apr 20th-percentile GP threshold, not a probability that intervention will help. June has **27 flags, 3 actual low days, 11.1% precision and 100.0% recall**. Many false positives and only three events make automatic interventions inappropriate. War-specific calibration or predictive performance has not been measured.

## 13. Discount review, not proven leakage

Recorded discount dollars (list value minus recorded revenue on discounted lines) total **$2,178.09**. The unrounded rate×list-value formula gives **$2,179.36**; the **$1.27** difference is line-revenue rounding reconciliation, not an additional loss. This explains small differences from earlier rate-formula summaries.

There are **153 discounted lines below a 30% recorded gross-margin rate**, with **$121.63** discount exposure. There are **0 negative-GP discounted lines**. Review tables rank branch/category/time groups by exposure. Tuesday or 19:00–22:59 defines a review period, not a causal treatment group or evidence discounts are wasted.

Exposure is a fixed-volume accounting maximum; ending promotions may change demand. Larger baskets have more chances to contain a discounted line, so their higher observed ticket does not establish discount effectiveness. Review reason codes, eligibility, campaign cost and exposure logs, then randomize a narrow policy change with a net-GP endpoint.

## 14. Product attention portfolio

Rank July 1 products using the existing product-demand forecast × Jan–May branch/product realized unit margin. Compare three top-three policies on June existing-sales GP: historical popularity, forecast popularity and forecast×margin. Each day's candidate ranking uses the previously evaluated product forecasting pipeline and prior-period economics; June is already an internal benchmark. No customer response to promotional placement is modeled.

| Top-three policy per branch/day | Captured existing June GP | Share of total June GP |
|---|---:|---:|
| forecast_margin | $4,970.80 | 13.52% |
| forecast_popularity | $4,572.47 | 12.43% |
| historical_popularity | $4,720.01 | 12.83% |

The margin ranking captures a larger share of **profit already present in historical sales**. This does not establish extra profit from moving menu items, adding promotions or replacing products. Top-k attention limits are management constraints; the UI slider changes the July 1 candidate list, while June evaluation stays fixed at three. A controlled placement test is the next evidence step.

## 15. Crisis menu/stock optimizer

For each branch/product, choose integer stock x and binary active-menu z. Across 16 assumed Poisson demand draws, maximize average `price×min(stock,demand) − scenario unit cost×all stock`. Enforce a shared procurement budget, branch unit capacities, at most 12 stocked menu products per open branch, and assumed ingredient-serving-equivalent caps. Stock must be positive for an active menu item, and unavailable/closed items cannot be stocked. All units purchased are charged, including unsold units; terminal salvage is assumed zero even for potentially storable items.

The budget is 80% of ordinary forecast procurement cost; branch capacities and shared serving-equivalent availability are 80% of ordinary forecast units. These are **invented stress-test constraints**, not observed inventory, purchasing budgets, recipes, staffing capacity or physical stock-transfer limits. Allocations are a hypothetical shared-procurement decision. No actual transfer operation is scheduled.

Six scenarios: ordinary constrained operation; demand −20%; all unit costs +15%; Harbour closure with zero customer migration; assumed milk resources unavailable; and a +20-percentage-point takeaway share that changes product mix using historical order-type profiles while preserving total expected units. None is an estimated effect of war. A closure removes Harbour's demand from the active scenario, so reported unmet units do not include the removed branch's counterfactual demand.

Popularity and margin-weighted greedy baselines obey the same scenario constraints. The MILP requests a 2% optimality gap and a 12-second limit; its status and final gap are saved. It optimizes its 16 planning draws, then all policies are evaluated on **512 separate simulated draws**, not real held-out crisis data. A feasible fallback is declared if no solver incumbent exists. No policy is guaranteed to beat a baseline on fresh samples.

| Assumed scenario | Popularity mean GP | Margin-rule mean GP | Optimized-plan mean GP | Solver gap |
|---|---:|---:|---:|---:|
| Ordinary forecast · constrained resources | $328.00 | $327.91 | $337.96 | 0.0 |
| Demand falls 20% | $252.36 | $253.16 | $254.21 | 0.0 |
| Unit costs rise 15% | $283.96 | $288.06 | $291.28 | 0.0 |
| Harbour closed · no customer migration | $123.93 | $133.82 | $134.84 | 0.0 |
| Milk serving-equivalents unavailable | $218.06 | $241.96 | $240.04 | 0.0 |
| Takeaway mix rises 20 percentage points | $323.29 | $326.82 | $333.27 | 0.0 |

**The optimized plan loses to the margin rule in the milk-unavailable scenario on fresh draws.** This result is retained. The models assume independent Poisson product demand and ignore cross-product substitution, correlated demand, traffic migration, real shelf lives, labor, rent, service/variety requirements and logistics. Narrow menus can sacrifice service; a real policy needs explicit coverage constraints. Simulated GP and its 10th percentile are conditional on this artificial world, not validated crisis savings or survival guarantees.

## Files, reproduction and checks

- `src/profit_lab.py`: Ideas 9–14, historical evaluation and scenario orchestration.
- `src/crisis_optimizer.py`: constrained menu/stock MILP and feasible baselines.
- `reports/profit_lab/findings.json`: full machine-readable evidence and assumptions.
- `drink-lens/dist/profit-lab.html`: seven interactive modules, controls, model comparisons and downloadable evidence.
- `notebooks/04_profit_lab.ipynb`: executed inspection notebook.
- `artifacts/profit_lab/`: local risk model and row-level evaluation records, ignored for publication.

```sh
python3 src/profit_lab.py --data /path/to/stories_transactions.csv --features daily_demand_features.csv
python3 src/build_profit_lab_report.py
python3 src/build_profit_lab_notebook.py
python3 src/verify_profit_lab.py --data /path/to/stories_transactions.csv
cd drink-lens
npm test
node tests/profit-lab-browser.mjs
```

The product-level modules require the existing `artifacts/demand_predictions.csv` and `artifacts/next_day_forecast.csv`; regenerate them with `src/forecast.py` and `src/predict.py` if absent. Browser tests use a temporary local server and do not send offers, modify inventory or execute payments. Source and aggregate assets are published privately; the raw CSV and row-level records remain local.

The main submission should still lead with the root-cause investigation. Breadth is not evidence of business value; negative results and missing information are part of the submission.
