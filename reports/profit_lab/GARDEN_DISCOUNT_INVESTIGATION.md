# Garden discount investigation: the 153 low-margin lines

## Three actionable findings

1. **Use a product-defined review, not an invented narrow time window.** All **153 lines** have a recorded **10% discount**, covering **seven products, 162 units and 152 unique transactions across 101 dates**. Chicken Pesto Sandwich has the largest exposure, **$25.69 (21.1%)**. The top three products account for **$67.62 (55.6%)**, so no single product contains most of the exposure. Verify eligibility for these seven products before choosing a test; a one-product/hour test would have very little historical volume.
2. **The observed exposure is small and the volume-loss denominator matters.** These lines record **$1,097.57 revenue**, **$285.80 GP** and **$121.63 discount exposure**. At unchanged purchases and costs, the no-discount accounting sensitivity is **$407.43 GP**, an increase of **$121.63 over the entire six-month file**—about **$0.67/calendar day**. The break-even unit loss is **29.85%** if only affected discounted-item volume changes, but **1.93%** if volume falls proportionally across all sales of these seven products. This is a sensitivity, not a predicted customer response or actual saving.
3. **Reconcile Garden costing and review product margins before changing offers.** Sparkling Water's non-discounted recorded margin is already **29.82%**, below the 30% screen; removing its discount would not move it above that threshold. Turkey & Cheese Sandwich is only **30.05%** at full price. No flagged line is loss-making at the recorded GP level. Check the branch cost-allocation rule and promotion rationale, then consider a controlled eligibility/discount test with total basket GP and lost purchases measured.

## Scope and definitions

Source: original `stories_transactions.csv`, January 1–June 30, 2026. Reproduce the flag exactly: `Branch == Garden`, `Discount Rate > 0`, and `Line Gross Profit / Line Revenue < 0.30`. Thirty percent is a screening choice, not a measured optimal margin. This is a line-level selection: 153 lines belong to 152 baskets, not 153 customers.

Observed discount dollars are `Quantity × Unit Price − recorded Line Revenue` on those lines. Use recorded revenue and GP without recomputing them from an unrounded discount percentage. The unrounded rate formula gives **$121.9200**, versus **$121.63** recorded exposure; the small rounding difference is not extra leakage. Recorded input cost for the flagged lines is **$811.77**. All seven products have constant recorded list prices and unit costs at Garden throughout the period.

Keep all original recorded lines, consistent with the existing audit. **None of the flagged lines is an exact duplicate** under the source columns; other file-wide duplicate-origin concerns remain unresolved. No model was trained, application feature added, source row changed, or individual customer/transaction record published.

## Products and observed dollars

| Product | Lines | Units | RevenueUSD | GPUSD | DiscountUSD | ExposureShare |
|---|---|---|---|---|---|---|
| Chicken Pesto Sandwich | 23 | 24 | $232.31 | $54.95 | $25.69 | 21.12% |
| Avocado Toast | 20 | 23 | $195.53 | $57.99 | $21.82 | 17.94% |
| Cheesecake Slice | 29 | 30 | $182.39 | $50.39 | $20.11 | 16.53% |
| Brownie | 33 | 36 | $167.01 | $44.97 | $18.39 | 15.12% |
| Turkey & Cheese Sandwich | 17 | 18 | $156.25 | $34.75 | $17.45 | 14.35% |
| Chicken Salad Bowl | 10 | 10 | $112.00 | $31.20 | $12.50 | 10.28% |
| Sparkling Water | 21 | 21 | $52.08 | $11.55 | $5.67 | 4.66% |

Totals: **153 lines; 162 units; $1,097.57 revenue; $285.80 recorded GP; $121.63 discount exposure**. Aggregate recorded margin is **26.04%**. Each flagged line still has positive recorded GP. The observed discount exposure is part of Garden's existing $555.90 total and the network's $2,178.09 total; do not add the subset to those totals.

## Comparison with non-discounted Garden sales of the same products

Every discounted sale of these seven products is in the flagged set; there are no additional positive-discount sales of these products outside it. The comparison group contains **2,236 non-discounted lines, 2,348 units, $17,672.00 revenue and $5,885.20 GP**. The same seven products have **2,389 total lines and 2,510 units** at Garden. Discounted lines are **6.40%** of those lines.

Non-discounted observed sales and both per-unit comparisons:

| Product | NonDiscountLines | NonDiscountUnits | NonDiscountRevenueUSD | NonDiscountGPUSD | DiscountedGPPerUnitUSD | NonDiscountGPPerUnitUSD |
|---|---|---|---|---|---|---|
| Chicken Pesto Sandwich | 316 | 330 | $3,547.50 | $1,108.80 | 2.2896 | 3.3600 |
| Avocado Toast | 263 | 282 | $2,664.90 | $978.54 | 2.5213 | 3.4700 |
| Cheesecake Slice | 415 | 435 | $2,936.25 | $1,022.25 | 1.6797 | 2.3500 |
| Brownie | 498 | 518 | $2,667.70 | $911.68 | 1.2492 | 1.7600 |
| Turkey & Cheese Sandwich | 280 | 299 | $2,885.35 | $867.10 | 1.9306 | 2.9000 |
| Chicken Salad Bowl | 163 | 169 | $2,104.05 | $738.53 | 3.1200 | 4.3700 |
| Sparkling Water | 301 | 315 | $866.25 | $258.30 | 0.5500 | 0.8200 |

Per-unit GP is **sum recorded line GP / sum Quantity**, not an average of line margins or a count of baskets. Four decimal places retain quantity/rounding effects; all amounts are USD. The product-matched comparison avoids simply contrasting different product mixes.

| Product | DiscountedMargin | NonDiscountMargin | TreatedUnitsBreakEvenLoss |
|---|---|---|---|
| Chicken Pesto Sandwich | 23.65% | 31.26% | 31.86% |
| Avocado Toast | 29.66% | 36.72% | 27.34% |
| Cheesecake Slice | 27.63% | 34.81% | 28.52% |
| Brownie | 26.93% | 34.17% | 29.02% |
| Turkey & Cheese Sandwich | 22.24% | 30.05% | 33.43% |
| Chicken Salad Bowl | 27.86% | 35.10% | 28.60% |
| Sparkling Water | 22.18% | 29.82% | 32.93% |

Pooled observed GP/unit is **$1.7642** for the discounted lines and **$2.5065** for non-discounted lines; these pooled groups also have different product weights. At the **discounted group's own product mix**, hypothetical full-price GP/unit is **$2.5150**. Prefer the product-matched rows to interpreting the pooled difference as a policy effect.

**This is an accounting comparison, not a causal estimate.** The groups are not randomized, and the flag itself selects low realized margins. Constant recorded price/cost and different recorded discounts reconcile the unit-GP differences arithmetically; they do not establish that offering or withdrawing a promotion changes overall profitability in the same way. Customer intent, eligibility, timing, basket composition and purchases that would not occur at full price are unobserved.

## Concentration by dates, weekdays and hours

There is exposure on **101 of 181 calendar dates**, in **all six months**, and across **all 17 recorded hours (07:00–23:59)**. Observed sales hours do not establish opening schedules. No single date or hour contains most of the dollars; this does not rule out an unrecorded eligibility rule or statistically meaningful pattern.

Denominators below are **all Garden lines of the same seven products in that period**, including discounted and non-discounted lines. `FlaggedLineRate` is a descriptive incidence among sold lines, not a customer discount probability, footfall conversion rate or causal effect. Date/hour scans are exploratory and unadjusted for product mix or multiple comparisons.

### Months

| Month | SameProductLines | Lines | DiscountUSD | FlaggedLineRate |
|---|---|---|---|---|
| 2026-01 | 315 | 25 | $19.09 | 7.94% |
| 2026-02 | 363 | 15 | $11.41 | 4.13% |
| 2026-03 | 387 | 26 | $18.84 | 6.72% |
| 2026-04 | 412 | 31 | $27.59 | 7.52% |
| 2026-05 | 426 | 25 | $19.45 | 5.87% |
| 2026-06 | 486 | 31 | $25.25 | 6.38% |

### Weekdays

| Weekday | SameProductLines | Lines | DiscountUSD | FlaggedLineRate |
|---|---|---|---|---|
| Monday | 344 | 27 | $22.11 | 7.85% |
| Tuesday | 507 | 32 | $26.48 | 6.31% |
| Wednesday | 339 | 7 | $8.33 | 2.06% |
| Thursday | 308 | 17 | $12.33 | 5.52% |
| Friday | 370 | 23 | $16.79 | 6.22% |
| Saturday | 232 | 21 | $16.35 | 9.05% |
| Sunday | 289 | 26 | $19.24 | 9.00% |

Tuesday has **$26.48** of exposure, but its flagged-line incidence is **6.31%**, close to the pooled **6.40%**. A higher raw Tuesday count is not evidence that the discount is targeted disproportionately to Tuesday.

### Hours

| Hour | SameProductLines | Lines | DiscountUSD | FlaggedLineRate |
|---|---|---|---|---|
| 7 | 41 | 3 | $1.73 | 7.32% |
| 8 | 57 | 1 | $0.97 | 1.75% |
| 9 | 75 | 5 | $3.65 | 6.67% |
| 10 | 94 | 6 | $8.66 | 6.38% |
| 11 | 120 | 6 | $3.90 | 5.00% |
| 12 | 101 | 7 | $5.63 | 6.93% |
| 13 | 133 | 5 | $4.41 | 3.76% |
| 14 | 120 | 9 | $8.37 | 7.50% |
| 15 | 127 | 7 | $5.93 | 5.51% |
| 16 | 131 | 10 | $7.08 | 7.63% |
| 17 | 132 | 15 | $11.35 | 11.36% |
| 18 | 154 | 13 | $10.25 | 8.44% |
| 19 | 196 | 13 | $9.07 | 6.63% |
| 20 | 225 | 12 | $8.76 | 5.33% |
| 21 | 343 | 21 | $16.67 | 6.12% |
| 22 | 223 | 10 | $7.06 | 4.48% |
| 23 | 117 | 10 | $8.14 | 8.55% |

The largest raw-dollar hour is **21:00–21:59**, with **$16.67 (13.7%)**, **21 flagged lines among 343 same-product lines**, and a **6.12%** flagged-line rate. That does not exceed the pooled rate. The 17:00 hour has a higher descriptive incidence (**15/132 = 11.36%**) but only **$11.35** exposure and no causal or confirmatory significance claim.

The 19:00–22:59 window contains **$41.56 (34.2%)** of exposure and **56 flagged lines among 987 same-product lines**. Narrowing a test to peak periods is not justified solely by raw traffic or exposure.

### Five dates with largest exposure

| Date | SameProductLines | Lines | DiscountUSD | ExposureShare |
|---|---|---|---|---|
| 2026-04-14 | 26 | 5 | $4.19 | 3.44% |
| 2026-05-12 | 26 | 4 | $3.98 | 3.27% |
| 2026-01-01 | 12 | 3 | $2.99 | 2.46% |
| 2026-04-06 | 14 | 3 | $2.89 | 2.38% |
| 2026-06-14 | 20 | 4 | $2.80 | 2.30% |

The largest date contributes **3.44%**; the top five dates together contribute **13.85%**. Full day-level aggregates, including zero-flag days, are in [garden_discount_dates.csv](garden_discount_dates.csv). A few exceptional dates do not account for most of the $121.63.

## Hypothetical no-discount exposure and break-even purchasing loss

**Observed:** flagged-line GP is $285.80; recorded discount exposure is $121.63. **Hypothetical:** if the exact same 162 units were bought at recorded list prices with unchanged recorded unit costs, GP would be **$407.43**, an increase of **$121.63**. This is the maximum direct accounting uplift from removing only these discounts at those fixed quantities, not a prediction of attainable profit or a bound on every possible longer-run policy outcome. No extrapolation to future demand or annual savings is made.

For a defined affected scope with current GP `G_scope` and exposure `D = $121.63`, assume a proportional unit-volume decline `L`, stable product mix, unchanged prices and unit costs, no replacement purchases, and that recorded unit costs scale with retained units:

`GP_after(L) = (1 − L) × (G_scope + D)`.

`Incremental GP(L) = (1 − L) × (G_scope + D) − G_scope`.

`Break-even unit-volume loss = D / (G_scope + D)`.

At equality the policies tie on this accounting model; losses above the boundary make discount removal worse. This is **not** `discount / revenue`, a sales elasticity estimate, a customer-loss probability or a guarantee about avoidable cash cost.

| Scope | BaselineGPUSD | NoDiscountSameVolumeGPUSD | UniformUnitLossBreakEven |
|---|---|---|---|
| Discounted units only; unchanged affected-product mix | $285.80 | $407.43 | 29.85% |
| All seven products; uniform volume/mix change | $6,171.00 | $6,292.63 | 1.93% |
| Whole Garden branch; uniform volume/mix change | $46,794.49 | $46,916.12 | 0.26% |

- **Discounted-only boundary:** 29.85% refers only to the 162 previously discounted units, at their same mix, with every other purchase unchanged. It does **not** mean Garden can lose 29.85% of customers or all sales. Product-specific discounted-only boundaries are in the comparison table above (approximately 27.34%–33.43%). Which products are lost matters.
- **Seven-product boundary:** 1.93% assumes proportional loss across all 2,510 units of these products, including full-price units, while other products are unaffected.
- **Whole-branch boundary:** 0.259% assumes proportional loss across all 17,833 Garden units and their existing mix. This illustrates exposure to broader basket/retention effects; it is not evidence that such a loss will occur.

These are alternative loss scopes, not interchangeable estimates. If particular baskets disappear, their own GP must be used; transaction count alone is insufficient. The 152 baskets containing flagged lines record **$1,777.12 revenue and $610.49 total basket GP**, including other purchases. This observed context is not proof that any of those baskets depend on the discount, and it must not be added to the discount exposure.

Discounted-only volume sensitivity:

| TreatedUnitLoss | HypotheticalGPUSD | ChangeVsObservedGPUSD |
|---|---|---|
| 0.00% | $407.43 | $121.63 |
| 10.00% | $366.69 | $80.89 |
| 20.00% | $325.94 | $40.14 |
| 29.85% | $285.80 | $0.00 |
| 30.00% | $285.20 | -$0.60 |
| 40.00% | $244.46 | -$41.34 |

The calculation ignores fixed overhead, labor changes, ingredient shelf life, disposal of prepared items, marketing/monitoring cost, substitution and long-run retention. It also treats recorded unit cost as scaling with units, although Garden's uniform branch cost multiplier may include allocations. Confirm avoidable costs before translating accounting GP into cash benefit.

## Practical controlled experiment

First ask finance to reconcile Garden's cost rule and operations to identify the promotion eligibility/reason codes for the seven products. The 30% outcome screen is for this audit; do not use realized low margin after purchase to assign treatment.

If the small available exposure justifies the implementation/measurement cost, predefine a product/eligibility population **before purchase** and randomize eligible offer opportunities between the existing 10% policy and a no-discount policy. Keep stock availability, placement and service comparable; record assignments, offers, nonpurchases/abandonment where feasible, quantities and complete baskets. Avoid selecting dates/hours from this retrospective scan simply because they look unusual. Consider repeat-customer exposure and contamination when choosing the randomization unit.

Use **total recorded GP per assigned eligible opportunity**, with verified cost accounting and implementation cost, as the primary endpoint. Track product units, total basket GP, substitution, customer response and service. Including nonbuyers avoids falsely concluding that higher GP per completed sale necessarily means a better policy. Predefine the sample plan, net-value decision rule and stopping conditions; the historical 153 discounted lines over six months warn that a very narrow test could be slow or underpowered. No sample size or causal effect is established by this audit.

## Evidence and reproduction

- [Product totals](garden_discount_products.csv), [same-product comparison](garden_discount_same_product_comparison.csv), [hours](garden_discount_hours.csv), [dates](garden_discount_dates.csv), [months](garden_discount_months.csv), [weekdays](garden_discount_weekdays.csv), [break-even scopes](garden_discount_break_even_scopes.csv), [volume sensitivities](garden_discount_volume_sensitivity.csv). These are aggregates without customer or transaction identifiers.
- [Financial ranking being investigated](FINANCIAL_EVIDENCE_RANKING.md), [saved Profit Lab totals](findings.json), [root-cause costing investigation](../root_cause/REPORT.md).
- Reproduce: `python3 src/investigate_garden_discounts.py --data /path/to/stories_transactions.csv`. The script contains no model imports, fitting or application-feature changes. It checks the 153-line/$121.63 reconciliation, unit-cost/GP identities, fixed price/cost comparisons and break-even equality before writing this report.

Source SHA-256: `f1672e728c28295b2b802d878fd38a158ba039827b429355e8438ee0463237a1`. Original data remain unchanged. All dollar values are recorded accounting amounts unless explicitly labelled hypothetical; none is a measured saving or a causal estimate of removing discounts.
