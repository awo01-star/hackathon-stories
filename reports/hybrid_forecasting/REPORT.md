### Step 9 — Exploratory hybrid forecasting strategy

**The hybrid was specified after examining June. Its June advantage is a hindsight result, not independent out-of-sample validation or proven savings.** No model is retrained and no branch rule is selected by this analysis. It evaluates the requested rule exactly.

- **A — All-naive:** Seasonal naive for every branch.
- **B — All-XGBoost:** XGBoost for every branch.
- **C — Hybrid:** Seasonal naive for Harbour; XGBoost for Garden and Uptown.

All three policies use the same frozen Step 7 predictions and the same **90 June branch-days**, with rolling next-day information. Step 8 economics and cost assumptions are unchanged. Prepare `floor(forecast + 0.5)` transaction-equivalents. Shortage penalties are **25%, 50% or 100% of Jan–May recorded branch GP/transaction**; excess penalties are **10%, 25% or 50% of Jan–May recorded branch input cost/transaction**. Score all nine cross-products, with no safety buffers or June-tuned capacity adjustments.

`Decision cost = max(actual − prepared,0) × shortage penalty + max(prepared − actual,0) × excess penalty`.

These are **hypothetical shortage/excess costs**, not measured waste, actual expenses, operating profit or realized savings. The source transactions, saved predictions, model files, selection lock and Step 8 evidence are unchanged.

#### Overall June costs and paired dollar differences

Positive improvement means the hybrid has lower assumed cost. All amounts below are total June USD, not per-day figures. Differences use unrounded values. A scenario ID such as `S0.25_W0.1` means 25% of historical GP for shortages and 10% of historical input cost for excess.

| Scenario | AllNaiveCostUSD | AllXGBoostCostUSD | HybridCostUSD | HybridImprovementVsNaiveUSD | HybridImprovementVsXGBoostUSD | HybridImprovementVsBestUniformUSD |
|---|---|---|---|---|---|---|
| S0.25_W0.1 | $761.25 | $837.34 | $716.60 | $44.65 | $120.73 | $44.65 |
| S0.25_W0.25 | $991.66 | $1,017.72 | $941.85 | $49.81 | $75.87 | $49.81 |
| S0.25_W0.5 | $1,375.67 | $1,318.36 | $1,317.27 | $58.41 | $1.09 | $1.09 |
| S0.5_W0.1 | $1,368.90 | $1,554.42 | $1,283.04 | $85.87 | $271.38 | $85.87 |
| S0.5_W0.25 | $1,599.31 | $1,734.80 | $1,508.29 | $91.02 | $226.51 | $91.02 |
| S0.5_W0.5 | $1,983.32 | $2,035.44 | $1,883.70 | $99.62 | $151.73 | $99.62 |
| S1_W0.1 | $2,584.20 | $2,988.57 | $2,415.91 | $168.30 | $572.67 | $168.30 |
| S1_W0.25 | $2,814.61 | $3,168.96 | $2,641.16 | $173.45 | $527.80 | $173.45 |
| S1_W0.5 | $3,198.62 | $3,469.60 | $3,016.57 | $182.05 | $453.02 | $182.05 |

**Descriptive result:** the hybrid has the lowest assumed overall decision cost in **9/9** scenarios. It improves on all-naive by **$44.65–$182.05**, on all-XGBoost by **$1.09–$572.67**, and on the stronger uniform policy in each scenario by **$1.09–$182.05**.

The stronger uniform policy is all-naive in eight scenarios and all-XGBoost in one. Choosing the lower-cost uniform policy from June is itself a descriptive comparison benchmark, not a validated deployment rule. The hybrid's branch mapping stays fixed across all nine scenarios.

![Policy costs across nine assumptions](../../figures/hybrid_forecasting/policy_cost_comparison.png)

#### Branch results and ties

**Garden**

| Scenario | AllNaiveCostUSD | AllXGBoostCostUSD | HybridCostUSD | HybridImprovementVsNaiveUSD | HybridImprovementVsXGBoostUSD | HybridImprovementVsBestUniformUSD | BestPolicy |
|---|---|---|---|---|---|---|---|
| S0.25_W0.1 | $232.26 | $197.16 | $197.16 | $35.11 | $0.00 | $0.00 | B_AllXGBoost + C_Hybrid |
| S0.25_W0.25 | $343.15 | $315.16 | $315.16 | $28.00 | $0.00 | $0.00 | B_AllXGBoost + C_Hybrid |
| S0.25_W0.5 | $527.97 | $511.82 | $511.82 | $16.15 | $0.00 | $0.00 | B_AllXGBoost + C_Hybrid |
| S0.5_W0.1 | $390.60 | $315.65 | $315.65 | $74.95 | $0.00 | $0.00 | B_AllXGBoost + C_Hybrid |
| S0.5_W0.25 | $501.49 | $433.64 | $433.64 | $67.84 | $0.00 | $0.00 | B_AllXGBoost + C_Hybrid |
| S0.5_W0.5 | $686.31 | $630.31 | $630.31 | $56.00 | $0.00 | $0.00 | B_AllXGBoost + C_Hybrid |
| S1_W0.1 | $707.27 | $552.62 | $552.62 | $154.65 | $0.00 | $0.00 | B_AllXGBoost + C_Hybrid |
| S1_W0.25 | $818.16 | $670.62 | $670.62 | $147.54 | $0.00 | $0.00 | B_AllXGBoost + C_Hybrid |
| S1_W0.5 | $1,002.98 | $867.29 | $867.29 | $135.69 | $0.00 | $0.00 | B_AllXGBoost + C_Hybrid |

**Harbour**

| Scenario | AllNaiveCostUSD | AllXGBoostCostUSD | HybridCostUSD | HybridImprovementVsNaiveUSD | HybridImprovementVsXGBoostUSD | HybridImprovementVsBestUniformUSD | BestPolicy |
|---|---|---|---|---|---|---|---|
| S0.25_W0.1 | $334.18 | $454.91 | $334.18 | $0.00 | $120.73 | $0.00 | A_AllNaive + C_Hybrid |
| S0.25_W0.25 | $403.65 | $479.52 | $403.65 | $0.00 | $75.87 | $0.00 | A_AllNaive + C_Hybrid |
| S0.25_W0.5 | $519.43 | $520.52 | $519.43 | $0.00 | $1.09 | $0.00 | A_AllNaive + C_Hybrid |
| S0.5_W0.1 | $622.05 | $893.42 | $622.05 | $0.00 | $271.38 | $0.00 | A_AllNaive + C_Hybrid |
| S0.5_W0.25 | $691.52 | $918.03 | $691.52 | $0.00 | $226.51 | $0.00 | A_AllNaive + C_Hybrid |
| S0.5_W0.5 | $807.30 | $959.03 | $807.30 | $0.00 | $151.73 | $0.00 | A_AllNaive + C_Hybrid |
| S1_W0.1 | $1,197.78 | $1,770.44 | $1,197.78 | $0.00 | $572.67 | $0.00 | A_AllNaive + C_Hybrid |
| S1_W0.25 | $1,267.25 | $1,795.05 | $1,267.25 | $0.00 | $527.80 | $0.00 | A_AllNaive + C_Hybrid |
| S1_W0.5 | $1,383.03 | $1,836.06 | $1,383.03 | $0.00 | $453.02 | $0.00 | A_AllNaive + C_Hybrid |

**Uptown**

| Scenario | AllNaiveCostUSD | AllXGBoostCostUSD | HybridCostUSD | HybridImprovementVsNaiveUSD | HybridImprovementVsXGBoostUSD | HybridImprovementVsBestUniformUSD | BestPolicy |
|---|---|---|---|---|---|---|---|
| S0.25_W0.1 | $194.81 | $185.27 | $185.27 | $9.55 | $0.00 | $0.00 | B_AllXGBoost + C_Hybrid |
| S0.25_W0.25 | $244.86 | $223.05 | $223.05 | $21.81 | $0.00 | $0.00 | B_AllXGBoost + C_Hybrid |
| S0.25_W0.5 | $328.26 | $286.01 | $286.01 | $42.25 | $0.00 | $0.00 | B_AllXGBoost + C_Hybrid |
| S0.5_W0.1 | $356.26 | $345.35 | $345.35 | $10.91 | $0.00 | $0.00 | B_AllXGBoost + C_Hybrid |
| S0.5_W0.25 | $406.30 | $383.13 | $383.13 | $23.18 | $0.00 | $0.00 | B_AllXGBoost + C_Hybrid |
| S0.5_W0.5 | $489.71 | $446.09 | $446.09 | $43.62 | $0.00 | $0.00 | B_AllXGBoost + C_Hybrid |
| S1_W0.1 | $679.16 | $665.51 | $665.51 | $13.65 | $0.00 | $0.00 | B_AllXGBoost + C_Hybrid |
| S1_W0.25 | $729.20 | $703.29 | $703.29 | $25.92 | $0.00 | $0.00 | B_AllXGBoost + C_Hybrid |
| S1_W0.5 | $812.61 | $766.25 | $766.25 | $46.36 | $0.00 | $0.00 | B_AllXGBoost + C_Hybrid |

At Harbour, hybrid and all-naive use exactly the same predictions and tie. At Garden and Uptown, hybrid and all-XGBoost tie. The hybrid combines the previously observed June branch winners. Because every branch's chosen model already won all nine Step 8 assumptions, its overall dominance here follows from adding those selected branch costs; it is not a new independent confirmation. The nine rows reuse the same forecast errors and are not nine independent experiments.

Cost components (shortage, excess and total) are saved for every policy/branch/scenario in `decision_costs.csv`. No oracle is added as a fourth evaluated policy; Step 8's perfect-information benchmark remains zero regret by construction and is not deployable.

#### How to choose the branch rule in a future experiment

1. **Before opening the next test period**, fix the capacity/rounding rule, eligible forecasting methods, branch-selection rule and actual shortage/excess cost accounting with operations. If several cost scenarios remain plausible, predeclare how they are combined (for example, fixed weights or worst-case regret); do not retrospectively choose the most favorable scenario.
2. Generate or use saved rolling validation forecasts from models fitted only on preceding data. For the original timeline, May could select branch policies using Jan–Apr economics and the existing May forecasts, with a predeclared fallback to naive when evidence is weak or tied. **Do not use Jan–May monetary averages to claim a prospective May selection.** This notebook does not perform that new selection or substitute it for the requested hybrid.
3. Lock each branch's model and every cost/policy choice using validation only. Refit permitted base models only through the validation cutoff in that future experiment, or keep them fixed if the protocol requires it. Then evaluate on genuinely later, unopened dates. Because June has already been inspected, selecting on May now cannot restore independent validation for this project; obtain later observations or run a prospective shadow pilot.
4. Compare the locked hybrid against all-naive and all-XGBoost on identical later branch-days. Report paired costs, branch results, uncertainty with temporal/branch dependence respected, stockouts, waste, service effects and model/operational overhead. If further retuning occurs, reserve another future period.

For live use, historical sales may censor true demand; transaction-equivalent capacity is not SKU inventory, recipe yield or staffing capacity. Recapture, perishability, salvage, labor and implementation costs are unobserved. Any incremental model/selection/monitoring cost can consume the small apparent benefit. Neither the branch mapping nor the hypothetical cost savings is proven stable over time or under disruption.

**Business implication:** this is a concrete hypothesis for a prospective branch-policy test, not a deployment recommendation. Retain simple models where they perform well, validate the economic penalties, and require net measured value before adding operational complexity. These ordinary-operation results cannot establish how a branch should respond during war; the existing crisis optimizer remains a separately labelled scenario tool.

Files: `notebooks/05_hybrid_forecasting_strategy.ipynb`; `reports/hybrid_forecasting/decision_costs.csv`; `model_comparison.csv`; `findings.json`; the comparison figure; and local row-level decisions in ignored `artifacts/hybrid_forecasting/`. Source input is never overwritten.

Reproduce without training: `python3 src/hybrid_forecasting_strategy.py --data /path/to/stories_transactions.csv`; `python3 src/build_hybrid_forecasting_notebook.py`; verify with `python3 src/verify_hybrid_forecasting.py`.
