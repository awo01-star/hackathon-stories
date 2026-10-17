from pathlib import Path
import json
import pandas as pd
R=Path(__file__).resolve().parents[1];O=R/'reports/root_cause';f=json.loads((O/'findings.json').read_text());t=f['tuesdayControlled'];g=f['gardenDecision'];growth=f['growthAccounting'];parts=pd.DataFrame(f['branchDecomposition']['effects']);garden=parts[parts.comparison=='Garden to Harbour'];delta=f['branchDecomposition']['dailyGP']['Harbour']-f['branchDecomposition']['dailyGP']['Garden']
table='\n'.join(f"| {r.factor} | ${r.dailyGrossProfitDifference:,.2f} | {r.dailyGrossProfitDifference/delta:.1%} |"for r in garden.itertuples())
cal='\n'.join(f"| {k} | {v['ratio']:.3f} | {v['ci95'][0]:.3f}–{v['ci95'][1]:.3f} |"for k,v in t['calendarProxyRatios'].items())
text=f'''# Root-cause investigation: explain the dollars before designing offers

## What changes in the project

Lead with a reproducible investigation of recorded profit and transaction differences. Keep forecasting as supporting validation and operational infrastructure. The camera, loyalty concepts and bundle planner are prototypes; they do not establish a root cause or a measured financial benefit. We should not use technical complexity as evidence of originality. The user-supplied `01_eda.ipynb` is a useful starting analysis, not a set of instructions or proof that its assumptions are true. It remains untouched.

## 1. Why does Harbour record more gross profit than Garden?

Observed GP per calendar day: Harbour **${f['branchDecomposition']['dailyGP']['Harbour']:,.2f}**, Garden **${f['branchDecomposition']['dailyGP']['Garden']:,.2f}**. Gap: **${delta:,.2f}/day**. An exact accounting decomposition separates six factors in the identity:

`GP/day = transactions/day × units/transaction × Σ product unit share × [price × (1 − effective discount) − unit cost]`.

All 720 possible orders of changing the six factors from Garden to Harbour are averaged (Shapley decomposition). This allocates interaction terms symmetrically rather than choosing a convenient order. Rounding is included in the effective discount so the identity reproduces the recorded money exactly.

| Accounting factor | Contribution to observed GP/day gap | Share of net gap |
|---|---:|---:|
{table}

Negative entries offset the positive contributions; positive shares can sum above 100%. These are contributions to an **observed accounting gap**, not causal effects or savings. In particular, the transaction-count contribution does not show whether Harbour has better location, marketing, footfall or conversion. We need storefront visitor counts and campaign exposure to distinguish them.

![Profit decomposition](../../figures/root_cause/branch_profit_decomposition.png)

### Rule out the obvious alternative: product mix

For all 45 matched products, Garden's price/Harbour price is {f['gardenRatios']['priceGardenHarbour']['median']:.3f} at the median, with a narrow {f['gardenRatios']['priceGardenHarbour']['min']:.3f}–{f['gardenRatios']['priceGardenHarbour']['max']:.3f} range. Its cost ratio is {f['gardenRatios']['costGardenHarbour']['median']:.3f}, range {f['gardenRatios']['costGardenHarbour']['min']:.3f}–{f['gardenRatios']['costGardenHarbour']['max']:.3f}. The price and cost differences exist **within the same products**, not just because Garden sells different items. Matching products and the small Shapley mix contribution weaken product mix as an explanation for the profit gap.

Every branch/product price and unit cost is constant over the observation window. A near-uniform branch cost multiplier across coffee, food and packaged drinks is compatible with a standard-cost allocation rule as well as a real branch-wide procurement or recipe difference. It cannot identify which. The smaller Uptown branch has lower recorded unit costs than Harbour, so a simple 'small branch ⇒ higher cost' narrative does not fit the ordering; this does not rule out other scale effects.

### Investigate the mechanism, then size a decision

| Competing explanation | What this file tests | Evidence needed to distinguish it | Action if confirmed |
|---|---|---|---|
| Different overhead allocation | Near-uniform multiplier is compatible; not proof | Finance cost formula, chart of accounts and allocations for identical SKUs | Normalize reporting; do not call accounting reclassification cash savings |
| Supplier/transfer-price difference | Same-product gap exists; invoices absent | Landed-cost invoices and transfer prices for matched products on matched dates | Negotiate or standardize sourcing only after measuring total landed cost |
| Recipe/portion/waste difference | Standard recorded costs are fixed; actual usage absent | Recipe grams, yields, inventory movements, waste and sampled portions | Change the operational process responsible; include quality/service tradeoffs |
| Local pricing strategy | Garden price is consistently lower; elasticity unobserved | Local demand context and a controlled pricing test | Adjust only if net GP and customer response justify it |

At **Garden's own observed quantities**, replacing only recorded costs with Harbour's gives a six-month accounting sensitivity of **${g['sixMonthRecordedCostGapAtHarbourCosts']:,.2f}**. This differs from the Shapley cost contribution because the latter averages interactions with both branches' volumes and other factors. Do not add the two figures.

If 10%, 25% or 50% of that fixed-volume gap is genuinely removable cash cost, the corresponding six-month scenarios are **${g['costRecoveryScenarios']['0.1']:,.2f}**, **${g['costRecoveryScenarios']['0.25']:,.2f}** or **${g['costRecoveryScenarios']['0.5']:,.2f}**, before implementation costs. If the whole gap is only allocation, avoidable cost may be zero. No annual extrapolation is used as the headline.

Aligning Garden prices with Harbour at unchanged volumes and discount percentages adds **${g['sameVolumePriceDifferenceAtHarbourPrices']:,.2f}** in six-month revenue and GP. Under a **uniform volume-loss, unchanged-mix and unchanged-unit-cost assumption**, a loss of about **{g['uniformVolumeLossBreakEvenForPriceAlignment']:.1%}** of units would erase that GP improvement. This is a break-even boundary, not an elasticity estimate or a recommendation to raise prices now.

## 2. Why does Tuesday outperform?

We can identify the measured mechanism—**more transactions rather than higher spending per basket**—and test competing explanations. The ultimate behavioral reason remains unidentified.

- Tuesday is the highest network transaction day in **{f['weeklyTuesday']['tuesdayWins']} of {f['weeklyTuesday']['fullWeeks']} complete weeks**. Comparing each Tuesday to the mean of the other days in the same week gives ratios from **{f['weeklyTuesday']['ratioRange'][0]:.2f} to {f['weeklyTuesday']['ratioRange'][1]:.2f}**, median **{f['weeklyTuesday']['medianRatio']:.2f}**. This avoids treating late-period growth as a weekday effect.
- Tuesday mean basket revenue is **${f['tuesdayBasketComparisons']['Tuesday']['ticket']:.4f}** versus **${f['tuesdayBasketComparisons']['OtherDays']['ticket']:.4f}** on other days. Average basket sizes are **{f['tuesdayBasketComparisons']['Tuesday']['unitsPerBasket']:.3f}** versus **{f['tuesdayBasketComparisons']['OtherDays']['unitsPerBasket']:.3f}** units.
- Tuesday category unit shares have total-variation distance **{f['tuesdayCategoryTotalVariation']:.2%}** from other days. This is descriptive closeness, not a formal equivalence test or evidence that the same people visit.
- Across all 17 recorded hours, Tuesday/other-day average transaction ratios remain above 1, ranging **{f['tuesdayHourRatioRange'][0]:.2f}–{f['tuesdayHourRatioRange'][1]:.2f}**. The pattern is broader than one evening slot. Per-branch/week results are in [CSV](tuesday_by_branch_week.csv).

![Within-week Tuesday test](../../figures/root_cause/tuesday_within_week.png)

### Is 'people got paid' supported?

We tested **illustrative** calendar proxies: days 1–3, 14–16 and 25–month end. These are not actual local salary dates: the dataset supplies no country, payroll schedule or verified calendar. We fit log daily transactions with branch×week fixed effects, weekday indicators and those calendar proxies, using 525 branch-day observations in 25 complete weeks. Standard errors cluster by week to account for common variation across branches and days. Intervals are exploratory; model choice and multiple hypotheses were not pre-registered, only six months exist, and cross-week dependence may remain.

The adjusted Tuesday ratio versus the **geometric mean** of other weekday counts is **{t['tuesdayRatioVsGeometricMeanOtherDays']:.3f}**, 95% interval **{t['ci95'][0]:.3f}–{t['ci95'][1]:.3f}**. This is a conditional association in log counts, not an estimate of what changing a date would cause.

| Hypothetical calendar window | Adjusted count ratio | Exploratory 95% interval |
|---|---:|---:|
{cal}

None of these monthly-date proxy intervals excludes 1. The calendar controls do not explain away the Tuesday association. **This does not disprove payday effects**: a weekly payday that always lands on Tuesday is observationally confounded with weekday, and different salary schedules were not observed. Do not invent a country, payday or local explanation to complete the story.

### Is the recorded 15% campaign the explanation?

Removing **all {f['excludedCampaignDates']} dates** on which any branch has a 15% line discount—including observations at other branches on those dates—still gives a Tuesday ratio of **{f['tuesdayExcluding15PercentDates']['tuesdayRatioVsGeometricMeanOtherDays']:.3f}**, interval **{f['tuesdayExcluding15PercentDates']['ci95'][0]:.3f}–{f['tuesdayExcluding15PercentDates']['ci95'][1]:.3f}**. That weakens the explanation that these recorded campaign dates alone create the recurring Tuesday pattern. It does not identify discount effectiveness or exclude unrecorded recurring offers.

| Behavioral hypothesis | Current status | Discriminating next evidence |
|---|---|---|
| Month-end/midmonth salary timing | Tested proxies do not explain the recurring Tuesday effect | Actual local pay calendar; customer/source-of-visit evidence; more months |
| Weekly payday, recurring event or hidden Tuesday promotion | Still plausible and indistinguishable here | Promotion/event calendar including off-POS channels and associated campaign costs |
| Bigger baskets or category shift | Not the main arithmetic mechanism in this data | Controlled customer/occasion study if a behavioral claim is needed |
| A particular branch or isolated hour | Pattern is broad across branches/hours; inspect CSV heterogeneity | Local footfall and operating schedules by site |
| Construction or anonymization artifact | Possible; `SYN-` prefix or regular patterns alone do not prove it | Data provenance, replacement-ID procedure and whether a date multiplier was applied |

The next useful step is to reconcile the Tuesday calendar with Stories' promotion and operations records. If a hidden promotion exists, assess **total contribution net of campaign cost**, rather than copy the pattern into a new discount. If the pattern reflects provenance transformations, do not base a real staffing or pricing intervention on it. Without labor, inventory and lost-sale records, we cannot price the value of extra staffing or preparation.

## 3. What is driving growth—and what is not?

Network revenue per calendar day rises from **${growth['revenuePerDayJanuary']:,.2f} in January** to **${growth['revenuePerDayJune']:,.2f} in June**. A three-factor Shapley identity decomposes the change into:

- Transactions/day: **+${growth['effectsRevenuePerDay']['transactionsPerDay']:,.2f}/day**.
- Units/basket: **+${growth['effectsRevenuePerDay']['unitsPerBasket']:,.2f}/day**.
- Realized revenue/unit: **${growth['effectsRevenuePerDay']['netRevenuePerUnit']:+,.2f}/day**.

Approximately {growth['effectsRevenuePerDay']['transactionsPerDay']/(growth['revenuePerDayJune']-growth['revenuePerDayJanuary']):.1%} of the accounting increase comes from transaction counts. That does not establish customer acquisition: one person can make multiple purchases and footfall is unobserved.

A useful countercheck to the supplied notebook's growth narrative: the **January first-observed customer cohort** contributes {f['identifiedGrowth']['2026-01']['januaryObservedCohortTransactions']:,} transactions in January versus {f['identifiedGrowth']['2026-06']['januaryObservedCohortTransactions']:,} in June, and revenue **${f['identifiedGrowth']['2026-01']['januaryObservedCohortRevenue']:,.2f}** versus **${f['identifiedGrowth']['2026-06']['januaryObservedCohortRevenue']:,.2f}**. Overall identified transactions nevertheless rise from {f['identifiedGrowth']['2026-01']['identifiedTransactions']:,} to {f['identifiedGrowth']['2026-06']['identifiedTransactions']:,}. Later first-observed cohorts contribute to that composition change. This neither proves acquisition nor a retention failure: first-observed dates are censored by the file start, January cohort selection guarantees January activity, and customer-ID capture/provenance is uncertain. See [cohort CSV](observed_first_cohort_growth.csv).

## 4. Resolve notebook assumptions rather than silently inheriting them

The supplied notebook drops 132 exact duplicate rows, interpreting them as POS/export duplication. Repeated identical lines can also be genuine two-item entries. Both representations must be checked until POS logs resolve the issue. Excluding them changes revenue by **${f['duplicateSensitivity']['revenueDifference']:,.2f}** and the Garden cost sensitivity from **${g['sixMonthRecordedCostGapAtHarbourCosts']:,.2f}** to **${f['duplicateSensitivity']['gardenCostGapDeduplicated']:,.2f}**. The main economic issue is robust, but the duplicate mechanism is not established.

Other distinctions matter: recorded sales hours do not prove opening hours; missing customer ID does not prove nonmembership; first-observed customers do not prove new customers; a branch-choice simulation matching the observed distribution does not prove IDs are randomized. Customer-level conclusions require corroboration rather than automatic rejection or acceptance.

## Decision priority and evidence request

1. **Finance/operations cost reconciliation first.** Compare the five Garden products with the largest dollar cost gaps against Harbour invoices, standard-cost formulas, recipes and waste. Determine which components are avoidable cash cost. Quantified opportunity is a bounded scenario, not a promise.
2. **Investigate the common Tuesday mechanism.** Join a verified promotion/event calendar and data-provenance description to the date/branch panel. If neither explains it, collect customer occasion and footfall evidence. Record disconfirming evidence as well as a preferred story.
3. **Validate the growth mechanism.** Join footfall/conversion and stable customer identity before choosing acquisition, retention or basket expansion as the intervention.
4. **Use the forecasts and offer planner downstream.** They can support a tested intervention once the business mechanism is understood. No additional cashback, camera or bundle feature is needed to establish these findings.

## Reproduce and inspect

`python3 src/root_cause.py --data /path/to/stories_transactions.csv` generates the [machine-readable findings](findings.json), detailed CSVs and figures. The executed notebook is `notebooks/02_root_cause_investigation.ipynb`. Raw input and the user's notebook are unchanged. Source SHA-256: `{f['sourceSHA256']}`. All dollar comparisons refer to the observed six-month file or explicitly identified daily amounts; none is an observed treatment benefit.
'''
step5 = R/'reports/activity/step5_tuesday_distribution.md'
if step5.exists():
    anchor = "### Is 'people got paid' supported?"
    text = text.replace(anchor, step5.read_text() + '\n\n' + anchor, 1)
step6 = R/'reports/demand_forecasting/REPORT.md'
if step6.exists():
    text = text.replace('## Reproduce and inspect', step6.read_text() + '\n\n## Reproduce and inspect', 1)
step7 = R/'reports/demand_forecasting/STEP7_REPORT.md'
if step7.exists():
    text = text.replace('## Reproduce and inspect', step7.read_text() + '\n\n## Reproduce and inspect', 1)
step8 = R/'reports/forecast_business_value/REPORT.md'
if step8.exists():
    text = text.replace('## Reproduce and inspect', step8.read_text() + '\n\n## Reproduce and inspect', 1)
step9 = R/'reports/hybrid_forecasting/REPORT.md'
if step9.exists():
    text = text.replace('## Reproduce and inspect', step9.read_text() + '\n\n## Reproduce and inspect', 1)
extension = R/'reports/profit_lab/ROOT_CAUSE_EXTENSION.md'
if extension.exists():
    text = text.replace('## Reproduce and inspect', extension.read_text() + '\n\n## Reproduce and inspect', 1)
(O/'REPORT.md').write_text(text);print('Wrote',O/'REPORT.md')
