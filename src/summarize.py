"""Build the reviewer-facing report from computed artifacts."""
from pathlib import Path
import json
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
R=Path(__file__).resolve().parents[1]
a=json.loads((R/'reports/data_audit.json').read_text());m=json.loads((R/'reports/metrics.json').read_text());f=json.loads((R/'reports/forecast_metrics.json').read_text());c=json.loads((R/'reports/cost_audit.json').read_text())
w=f['selected_ml'];base=f['paired_day_bootstrap']['baseline'];d=pd.read_csv(R/'artifacts/demand_predictions.csv');d['date']=pd.to_datetime(d.date)
rows=[]
for branch,g in d.groupby('Branch'):
 for name in [base,w]:rows.append({'Branch':branch,'model':name,'mae':abs(g.units-g[name]).mean(),'wape':abs(g.units-g[name]).sum()/g.units.sum(),'bias':(g[name].sum()-g.units.sum())/g.units.sum()})
pd.DataFrame(rows).to_csv(R/'reports/forecast_by_branch.csv',index=False)
fig,ax=plt.subplots(figsize=(8,4));names=list(f['test']);ax.barh(names,[f['test'][n]['mae'] for n in names]);ax.set(xlabel='June mean absolute error (units per branch/product/day)',title='ML beats five simple demand baselines');fig.tight_layout();fig.savefig(R/'figures/demand_comparison.png',dpi=160);plt.close(fig)
fig,ax=plt.subplots(figsize=(8,4));daily=d.groupby('date')[['units',base,w]].sum();daily.plot(ax=ax);ax.set(ylabel='Units sold / forecast',title='June daily demand: rolling one-day forecasts');fig.tight_layout();fig.savefig(R/'figures/daily_forecast.png',dpi=160);plt.close(fig)
forecast_table='\n'.join(f"| {n} | {v['mae']:.3f} | {v['wape']:.2%} | {v['poisson_deviance']:.3f} | {v['bias_fraction']:+.2%} |" for n,v in f['test'].items())
attach_table='\n'.join(f"| {n} | {v['roc_auc']:.3f} | {v['pr_auc']:.3f} | {v['log_loss']:.4f} |" for n,v in m['test'].items())
category_table='\n'.join(f"| {k} | {v[m['selected_ml']]['roc_auc']:.3f} | {v[m['selected_ml']]['prevalence']:.2%} |" for k,v in m['per_category'].items())
rel=1-f['test'][w]['mae']/f['test'][base]['mae'];s=f['scenario_only_poisson_stocking'];gain=s[w]['simulated_gross_profit']-s[base]['simulated_gross_profit']
text=f'''# Stories ProfitPilot: forecast first, promote only after testing

## CEO recommendation
Pilot daily food replenishment forecasts, and ask finance to verify Garden's cost allocation before funding promotions. On June's 4,050 branch/product/day observations, a Poisson gradient boosted model lowers mean absolute forecasting error **{rel:.2%}** against the strongest validation-selected simple baseline ({base}). A food-only stocking simulation shows **${gain:,.2f}** more gross profit in June, but this is an assumption-dependent scenario, not measured savings. Garden's recorded unit cost is about **43% higher** than Harbour's for the same products; holding Garden's quantities fixed gives a **${c['garden_cost_gap_at_harbour_costs']:,.2f}** six-month accounting gap. Verify whether that represents procurement, recipes, or allocated overhead. A separate add-on model reaches **{m['test'][m['selected_ml']]['roc_auc']:.3f} AUC**, yet provides weak within-category discrimination; it does not justify deploying personalized promotions.

## Evidence and data quality

- {a['rows']:,} line items, {a['baskets']:,} baskets, 45 products, three branches, 181 dates ({a['dates'][0]}–{a['dates'][1]}).
- Revenue: ${a['total_revenue']:,.2f}; recorded gross profit: ${a['total_gross_profit']:,.2f}. Gross profit excludes unrecorded rent, payroll, inventory waste and implementation costs.
- {a['missing_customer_fraction']:.2%} of line items lack customer IDs. We exclude IDs entirely rather than inventing customers or using identifiers as predictive features.
- Repeated transaction IDs are multiple basket lines. Basket date, time, branch, order type and nonmissing customer values are consistent. Exact duplicate rows: {a['exact_duplicate_rows']}; they are reported rather than silently deleted.
- Revenue and gross-profit arithmetic agree to rounding; maximum absolute discrepancies are ${a['revenue_max_abs_rounding_error']:.4f} and ${a['gross_profit_max_abs_rounding_error']:.4f}. See [audit](data_audit.json).
- Branch/product unit prices and unit costs are each constant throughout the data. This limits price-response identification. The `SYN-` ID prefix alone does not establish how the data was generated.

## 1. Demand ML and replenishment decision

**Target:** next day's sold units per branch/product, including zero-sales days. Grid: 3 branches × 45 products × 181 days. The first 28 days warm up lagged features. A zero means no recorded sale, not proof of zero demand or an open/stocked store.

**Features available at decision time:** product, branch, weekday, elapsed date, yesterday's sales, last week's same-day sales, and shifted 7/28-day averages. All rolling features exclude the prediction day. No same-day revenue, profit, quantity or discount enters the forecast. Prices/costs enter the stocking scenario, not demand model features.

**Evaluation:** train after warm-up through April; choose depth 2 or 4 using May Poisson deviance; refit January–May (after warm-up), evaluate June. June forecasts are made one day at a time using preceding observed days, while model parameters remain fixed. This is not a June 1 forecast of the whole month. Seasonal controls were added as a robustness check after the initial June readout; model settings were unchanged. June is therefore an internal chronological holdout, not a pristine external benchmark. Confirm on July or a prospective pilot.

The seasonal4 control averages the preceding four matching weekdays; seasonal_blend averages seasonal4 and the shifted 28-day average. All five baselines appear below. A zero forecast is floored at .001 only for Poisson deviance, so the last-week baseline's deviance is sensitive to that floor. MAE is the primary operational comparison.

| Forecast | MAE ↓ | WAPE ↓ | Poisson deviance ↓ | Aggregate bias |
|---|---:|---:|---:|---:|
{forecast_table}

MAE improvement against {base}: {f['test'][base]['mae']-f['test'][w]['mae']:.4f} units per cell, with paired day-bootstrap 95% interval [{f['paired_day_bootstrap']['ci95'][0]:.4f}, {f['paired_day_bootstrap']['ci95'][1]:.4f}] (500 resamples, seed 490). Days, rather than individual rows, are sampled to preserve within-day dependence. Serial dependence and one-month scope remain limitations. **WAPE still exceeds 50%**: low-count product/day demand is noisy, and a good aggregate forecast does not guarantee accurate individual items. Branch breakdown: [CSV](forecast_by_branch.csv).

![Forecast comparison](../figures/demand_comparison.png)
![Daily forecasts](../figures/daily_forecast.png)

### Translate a forecast into an order quantity

For a perishable item with no salvage value, the scenario uses `stock = PoissonQuantile((price − cost) / price, predicted_units)`. This trades off an unsold item's cost against a missed sale's gross margin. The mean forecast is learned; the Poisson predictive distribution is an assumption, not an empirically calibrated uncertainty interval.

Food only (Bakery, Breakfast, Desserts, Meals, Sandwiches), using January–May branch/product prices and costs:

| June scenario | {base} | ML |
|---|---:|---:|
| Simulated gross profit | ${s[base]['simulated_gross_profit']:,.2f} | ${s[w]['simulated_gross_profit']:,.2f} |
| Unsold units | {s[base]['unsold_units']:,.0f} | {s[w]['unsold_units']:,.0f} |
| Unserved recorded units | {s[base]['unserved_observed_units']:,.0f} | {s[w]['unserved_observed_units']:,.0f} |

ML stocks more and misses fewer recorded sales, but **creates more unsold units**. Do not pitch it as proven waste reduction. Scenario uplift is ${gain:,.2f} before implementation costs. If pilot cost exceeds that amount for an equivalent month, this simulated advantage disappears even if all demand/cost assumptions hold. Historical sales may be censored by stockouts; actual inventory, spoilage, expiry, salvage, capacity, discount revenue, labor and substitution are missing. Discounts are deliberately excluded from scenario prices; observed June sales are treated as demand. Consequently these figures neither reconstruct historical realized profit nor estimate causal savings. The all-food spoilage assumption is intentionally visible and needs SKU-specific replacement.

## 2. Cost anomaly: a decision before a promotion

Across all 45 matched products, Garden/Harbour median recorded unit-cost ratio ranges from {c['ratio_range'][0]:.3f} to {c['ratio_range'][1]:.3f}; median {c['median_garden_harbour_unit_cost_ratio']:.3f}. Comparing identical products eliminates product mix as an explanation for this ratio. Constant costs within branch/product and the near-uniform multiplier suggest an accounting convention or systematic markup as plausible explanations, alongside real procurement/recipe differences. Transaction records cannot choose between them.

Holding Garden's actual quantities fixed and substituting Harbour's unit costs gives a six-month gap of ${c['garden_cost_gap_at_harbour_costs']:,.2f}. If finance confirms 10%, 25%, or 50% is removable, the corresponding **scenario** is ${c['recoverable_gap_scenarios']['0.1']:,.2f}, ${c['recoverable_gap_scenarios']['0.25']:,.2f}, or ${c['recoverable_gap_scenarios']['0.5']:,.2f}. No amount is claimed recoverable. Inspect [matched products](matched_product_costs.csv) and [gap by product](garden_cost_gap.csv). Reconcile supplier invoices, recipes, transfers and overhead allocation for five high-gap products first. If costs are only allocations, operational savings may be zero and a price increase would be unsupported.

## 3. Profit-aware add-ons: useful negative result

One row per beverage basket × five food categories. Label: whether that food category occurs in the completed basket. Select the alphabetically first beverage as an anchor, ignoring food labels. Inputs are anchor drink, branch, order type, hour, weekday, elapsed date and candidate category. All categories for a basket stay in the same chronological partition. Training Jan–Apr; May selects logistic versus depth 2/4 boosted models by log loss; selected model refits Jan–May; June has {m['test_baskets']:,} beverage baskets. Customer histories, final basket size, food items, revenue, cost, discount and profit are excluded from features.

There is no item sequence: the anchor comes from the completed basket, and {a['multiple_distinct_beverages_fraction']:.2%} of beverage baskets have multiple distinct drinks. This evaluates **masked same-basket category retrieval**, not real-time next-item behavior. A real interface must capture the initial drink before showing the recommendation and validate the resulting distribution.

| Model | Pooled ROC AUC ↑ | Average precision ↑ | Log loss ↓ |
|---|---:|---:|---:|
{attach_table}

The best simple baseline smooths food-category frequency by drink and branch with 30 prior observations. Pooled category-pair prevalence is {m['test'][m['selected_ml']]['prevalence']:.2%}; an always-negative classifier would appear {1-m['test'][m['selected_ml']]['prevalence']:.2%} accurate. Accuracy is misleading here. Pooled AUC also benefits from differences in category prevalence:

| Category | ML within-category AUC | June prevalence |
|---|---:|---:|
{category_table}

The paired day-bootstrap interval for baseline log loss minus ML log loss is [{m['paired_day_bootstrap']['ci95'][0]:.6f}, {m['paired_day_bootstrap']['ci95'][1]:.6f}]. This modest predictive gain does not establish an improvement in business decisions. Full margin-weighted retrieval policies, using January–May **branch/category** realized unit margins, are in [metrics.json](metrics.json). The proxy rewards selecting a category already present in the completed basket. It is not incremental profit, and category-average margins do not specify an actual SKU. Do not give retention discounts or claim recommendation uplift from these labels.

![Add-on calibration](../figures/calibration.png)

## Pilot, uncertainty and stop rules

1. **Finance check:** reconcile Garden costs before interpreting them as savings or using them for pricing. Record the result even if it invalidates the apparent opportunity.
2. **Shadow mode:** run daily forecasts for two weeks without changing orders. Record available inventory, opening hours, sell-outs, discarded units and unit costs. Check error and bias by branch/product and record deviations from model quantities.
3. **Controlled replenishment test:** randomize comparable branch/product groups to current process or forecast-assisted ordering, stratified by branch/category and historical volume. Keep assignments stable during the test, exclude or cluster substitutes, log stock transfers and pre-register analysis. Start with a small perishable menu with known shelf life. Primary endpoint: gross profit net of waste and incremental handling cost per assigned product/day; secondary: stockout frequency and waste. Use cluster-aware uncertainty; three branches alone are not enough independent clusters for confident branch-only inference. Stop if agreed stockout/waste service limits are breached; set limits with operations before launch.
4. **Scale gate:** widen only if the lower confidence bound for net benefit is above zero and service limits hold. The dataset cannot determine required sample size: collect pilot variance, serial correlation and a minimum worthwhile effect, then power the test. No invented significance threshold in dollars or guaranteed duration.
5. **Optional add-on experiment later:** randomly assign beverage baskets to no prompt, a simple branch/drink margin rule, or the ML margin rule. Same menu availability and no automatic discount. Log exposures, acceptance and total basket gross profit, including cannibalization and prompt cost. Customer-level stable assignment if repeat customers can be identified; otherwise record repeat-customer contamination as a limitation.

## Choices rejected

- Predicting line gross profit from price/cost/quantity: arithmetic leakage, not a useful ML contribution.
- Random row split: shares basket lines and time regimes across train/test.
- Discount optimization or uplift training: recommendation exposures, randomized promotions, stockouts and price variation are absent; 15% discounts occur only at Harbour, so treatment and branch are confounded. Recorded co-movement cannot identify price elasticity.
- Customer churn/CLV as the main pitch: 36.5% of lines lack customer ID and observation covers only six months.
- Vision or a chatbot-first website: no drink-image labels; neither improves evidence from this dataset.
- Claiming the largest AUC as the winner: policy utility and within-category discrimination tell a less flattering but more useful story.

## Inspection and reproducibility

Run commands in the root [README](../README.md). Machine-readable evidence: [forecast metrics](forecast_metrics.json), [classification metrics](metrics.json), [cost audit](cost_audit.json), [data audit](data_audit.json). Model hyperparameters and preprocessing live in `src/`. Figures and aggregate CSVs are generated from the source CSV; raw data, row-level predictions and serialized models are excluded from publication by default. Training has fixed random seed 490. The source-file SHA-256 is recorded to identify the input without publishing it. Team names must be filled in before submission. No public repository has been created or submission sent.
'''
(R/'reports/REPORT.md').write_text(text)
print('Wrote reports/REPORT.md')
# Predeclared scenario grid: no policy selection from these June outcomes.
from scipy.stats import poisson
food=d.Product.isin(pd.read_csv(R/'reports/product_economics.csv').query("Product in ['Butter Croissant','Chocolate Croissant','Almond Croissant','Cinnamon Roll','Blueberry Muffin','Banana Bread','Chocolate Cookie','Pistachio Cookie','Brownie','Cheesecake Slice','Tiramisu Cup','Frozen Yoghurt Cup','Egg Sandwich','Avocado Toast','Granola Yoghurt','Chicken Pesto Sandwich','Turkey & Cheese Sandwich','Tuna Sandwich','Halloumi Wrap','Chicken Salad Bowl','Quinoa Bowl','Soup of the Day']").Product.unique())
# Same 22 food products as the main scenario; identify independently from model features.
e=d[food].copy();rows=[]
for price_factor in [1.,.9]:
 for salvage_fraction in [0.,.25,.5]:
  price=e.price*price_factor;salvage=e.cost*salvage_fraction;q=((price-e.cost)/(price-salvage)).clip(0,1)
  values={}
  for name in [base,w]:
   stock=poisson.ppf(q,e[name].clip(lower=.001));sold=np.minimum(stock,e.units);left=np.maximum(stock-e.units,0);values[name]=float((sold*price+left*salvage-stock*e.cost).sum())
  rows.append({'price_factor':price_factor,'salvage_fraction_of_cost':salvage_fraction,'baseline_simulated_gp':values[base],'ml_simulated_gp':values[w],'ml_minus_baseline':values[w]-values[base]})
sens=pd.DataFrame(rows);sens.to_csv(R/'reports/stocking_sensitivity.csv',index=False)
policy=m['retrieval_policies'];mlp=policy[m['selected_ml']+'_margin']['matched_margin_proxy'];bp=policy['drink_branch_margin']['matched_margin_proxy']
extra=f'''\n## Additional robustness and policy evidence\n\nThe ML margin policy's matched-margin proxy is ${mlp:.3f} per held-out beverage basket versus ${bp:.3f} for the simpler drink/branch margin rule. This is why the recommendation model's AUC improvement is not the main business claim. Neither proxy measures incremental profit.\n\nStocking sensitivity varies realized selling price (100% or 90% of the training list price) and salvage value (0%, 25%, 50% of cost), recomputing the same newsvendor rule for both frozen forecasts. This explores assumptions rather than selecting a best policy from June:\n\n| Selling price factor | Salvage / cost | ML minus baseline simulated gross profit |\n|---:|---:|---:|\n'''
extra+='\n'.join(f"| {r['price_factor']:.0%} | {r['salvage_fraction_of_cost']:.0%} | ${r['ml_minus_baseline']:,.2f} |" for r in rows)
extra+='\n\nThese scenarios hold recorded demand fixed even when price changes; they are accounting sensitivities, not demand-response predictions. Positive values do not remove the need to measure censored demand, waste and implementation cost in a pilot. Full figures: [CSV](stocking_sensitivity.csv).\n'
(R/'reports/REPORT.md').write_text((R/'reports/REPORT.md').read_text()+extra)
