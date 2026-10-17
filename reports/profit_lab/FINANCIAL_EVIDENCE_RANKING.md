# Profit Lab: comparative financial evidence and decision ranking

## Decision for the presentation

**None of the seven components establishes incremental profit, realized savings, or a validated response to war.** The strongest financial evidence is a small, auditable discount exposure—not a proven loss. Lead with that distinction, then propose a narrow test with a net-gross-profit endpoint. Do not present seven implementations as seven profitable interventions.

**Primary finding — discount review (Idea 13).** Across January–June 2026, recorded discounts total **$2,178.09**. Within that total, **153 discounted lines, all at Garden, have recorded gross-margin rates below 30% and contain $121.63 of discount exposure**. None of the discounted lines records negative GP. This identifies a specific population for finance and promotion review; it does not show that the discounts were unnecessary. Garden's systematic recorded cost multiplier is a competing explanation for its low margins and must be reconciled first. Management can inspect these lines, validate costing and eligibility, and test a narrow policy change rather than cancel promotions wholesale.

Use **at most two supporting findings**:

1. **One-dollar challenge (Idea 10):** branch-wide increases of 1–2 cents imply **$4.50/day across the network** at historical volumes, before implementation costs. Losses of less than 1% of branch units can erase the modeled gain. This is a transparent pricing sensitivity and candidate for testing, not an elasticity estimate.
2. **Product portfolio (Idea 14):** the forecast/margin top-three ranking selects products accounting for **$250.79 more existing June GP** than historical popularity. This is evidence about ranking existing profit, not evidence that promoting those products generates $250.79 more profit. Test placement before claiming an opportunity value.

These are the strongest choices **within the seven Profit Lab components**. This ranking does not supersede the separate root-cause investigation or establish that this modest discount exposure should become the entire hackathon story. If the presentation requires a verified “we can earn $X more” claim, the current evidence does not support one.

## Scope and ranking method

Reviewed the saved aggregate results, implementation and existing evaluation outputs, with read-only reconciliation of discount totals and the low-margin subset against the original transaction data. No features were built, models fitted, or predictions regenerated for this review.

- Historical window: January 1–June 30, 2026; 181 days. Predictive comparisons use the previously saved June evaluations. July 1 examples are historical planning demonstrations.
- **Observed:** recorded transactions, recorded accounting amounts, or a retrospective metric computed from those observations. An observed retrospective metric does not establish an intervention effect.
- **Estimated:** model-based quantities such as future demand or a lower GP forecast; not realized outcomes.
- **Hypothetical:** an accounting or operational counterfactual conditional on specified assumptions, such as unchanged volume after a price increase.
- **Simulated:** an outcome produced in an assumed demand/resource world. Separate simulation draws are not real crisis observations.

Ranking is a qualitative management judgment, not a fitted score or statistically established ordering. Prioritize evidence for the stated claim, then a clearly bounded and actionable financial scope and feasibility. Originality breaks close comparisons; model sophistication earns no credit. Unknown financial impact is recorded as **unknown**, rather than assigned an invented value. A large historical total, a simulated GP level and an incremental profit opportunity are different quantities and are not ranked by numerical size alone.

| Rank | Component | Evidence for its narrow claim | Financial scope / upside status | Originality | Practical feasibility now |
|---|---|---|---|---|---|
| 1 | 13. Discount review | Strong accounting evidence; no causal effectiveness evidence | $2,178.09 six-month exposure; $121.63 targeted subset; recovery unknown | Modest; targeted Garden/costing interpretation is more useful than a discount dashboard | High for audit; medium for a controlled policy test |
| 2 | 10. One-dollar challenge | Strong arithmetic; demand response untested | $4.50/day hypothetical network gain; fragile to volume loss | Modest, but explicit break-even analysis answers a concrete dollar question | High for calculation; medium for real pricing/rounding and a test |
| 3 | 14. Product portfolio | Moderate retrospective ranking evidence | +$250.79 existing June GP captured; incremental upside unknown | Moderate: margin versus popularity is a useful decision comparison | Medium–high for a limited placement test |
| 4 | 12. Profit at risk | Moderate quantile evidence; weak alert precision | No defensible dollars recoverable from alerts | Moderate: lower-tail GP and alert burden are more useful than mean demand alone | Medium for shadow monitoring; low for automatic intervention |
| 5 | 9. Basket completion | Moderate evidence of failure to beat a simple margin baseline | Negative matched-GP proxy difference; incremental upside unknown | Modest: standard basket retrieval, honestly benchmarked | Medium for testing; poor case for deploying the conditional model |
| 6 | 15. Crisis optimizer | Simulation evidence only for business value | Small simulated deltas, including a loss; real crisis benefit unknown | Moderate: common constraints and baseline comparisons, not the solver itself | Low until budgets, recipes, capacity and demand assumptions are verified |
| 7 | 11. Menu alternatives | Descriptive similarity; substitution unvalidated | No quantified financial opportunity | Modest: hourly-profile similarity is not switching behavior | Low for automatic substitution; medium as a manually checked shortlist |

Ranks 2–5 are not a claim of statistically different project quality. Pricing ranks above the predictive tools because its financial assumptions and testable action are explicit, not because its causal evidence is stronger. The crisis tool's potential importance during a real disruption is substantial but cannot be valued from this file.

## 1. Discount review — Idea 13

1. **Business problem:** identify where a limited discount budget and low recorded margins deserve review, without assuming all discount spend is waste.
2. **Historical finding:** **$2,178.09** of list-value-minus-recorded-revenue exposure on discounted lines. Branch totals: Harbour **$1,300.04**, Garden **$555.90**, Uptown **$322.15**. The **153 lines below 30% recorded margin are all at Garden**, with **$121.63** exposure. There are **zero negative-GP discounted lines**. The 30% threshold is a management screening assumption, not a discovered optimum.
3. **Financial opportunity:** recoverable profit is **not identified**. At unchanged purchases, prices and costs, removing every recorded discount would mechanically add at most the $2,178.09 exposure over the same observed six months; restricting that exercise to the low-margin subset gives $121.63. These are conditional accounting ceilings on removing those discounts, not expected gains or bounds on the total value of redesigning promotions. Demand loss or implementation cost could make net benefit negative. The subset is already inside the total and must not be added to it.
4. **Dollar classification:** exposure is **observed accounting**. Recovery is **hypothetical**. The rate-times-list-value calculation is **$2,179.36** before line rounding; the **$1.27** reconciliation difference is not extra leakage.
5. **Simplest baseline:** reconcile the current policy against the same-quantity list-price accounting benchmark. No randomized no-discount control exists, so superiority to the current promotion policy has **not** been demonstrated. A simple margin threshold suffices for this review; no ML detector is needed.
6. **Limitations:** discount assignment, eligibility, campaign spend and counterfactual demand are missing. Busy-period discounts need not be ineffective. Garden's approximately uniform cost uplift may reflect allocation rather than avoidable cash cost. Recorded margin is not profit after labor, rent or other overhead.
7. **Specific action:** finance should reconcile Garden's recorded costs and review the 153 flagged lines against promotion rules. If eligibility or economics justify a change, randomize a narrow eligible promotion policy against the existing policy, keeping exposure logs and comparing **total GP per assigned customer/basket after campaign and implementation cost**, including nonbuyers where measurable. Stop if net GP falls; do not automatically withdraw discounts.

Sources: [saved results](findings.json), [review groups](discount_review.csv), [cost interpretation](../root_cause/REPORT.md). The Garden membership of the low-margin subset was reconciled directly from the source; it is a review finding, not a new model.

## 2. One-dollar challenge — Idea 10

1. **Business problem:** find a minimal, understandable pricing change within a defined policy family that could improve gross profit at historical volume.
2. **Historical finding:** recorded volume and discount rates imply the following price sensitivities. These quantities measure the observed operating scale; customers' responses to changed prices were not observed.

   | Branch | Uniform menu price increase | Units affected/day | Transactions affected/day | Hypothetical GP/day increase | Uniform unit-loss break-even |
   |---|---:|---:|---:|---:|---:|
   | Garden | $0.02 | 98.52 | 61.67 | $1.96 | 0.752% |
   | Harbour | $0.01 | 144.16 | 90.24 | $1.43 | 0.264% |
   | Uptown | $0.02 | 56.14 | 35.30 | $1.12 | 0.576% |

3. **Financial opportunity:** **$4.50/day network total**, calculated from unrounded branch figures. This is small, conditional gross profit before menu/POS update and monitoring cost. It is not a forecast of attainable uplift. The saved single-SKU alternatives are separate policy choices and cannot be added to this total without evaluating overlaps.
4. **Dollar classification:** **hypothetical fixed-volume accounting**, derived from observed quantities. No measured elasticity, realized incremental revenue or realized GP improvement.
5. **Simplest baseline:** unchanged prices yield zero price-driven accounting gain. Among whole-cent uniform menu changes, one cent less than each selected branch step fails the $1/day target. This establishes minimality only in that enumerated policy family, not global superiority to discount, mix or single-SKU actions.
6. **Limitations:** unchanged units, product mix, unit costs and discount percentages; no line-rounding interaction or fixed-cost changes. The break-even calculation assumes proportional volume loss across products and no overhead change. Actual pricing increments and POS/display rounding may make 1–2-cent changes impractical. Fractions below 1% are sensitivity boundaries, not predicted customer losses.
7. **Specific action:** verify price-step feasibility and administrative cost first. If management wants to test pricing, choose one feasible predeclared price policy using these sensitivities, then compare net GP, units and customer response against a control. Reject changes whose implementation cost or demand loss consumes the small upside. Do not interpret the tiny cent steps as a ready-to-deploy recommendation.

Sources: [saved policies and assumptions](findings.json), [implementation of the defined search](../../src/profit_lab.py).

## 3. Product attention portfolio — Idea 14

1. **Business problem:** use scarce menu/placement attention on products with more expected GP, rather than automatically highlighting the most popular products.
2. **Historical finding:** selecting three products per branch-day with forecast units × Jan–May realized unit GP captures **$4,970.80** of GP already recorded in June, versus **$4,720.01** for Jan–May historical popularity and **$4,572.47** for forecast-unit popularity. Capture shares are **13.52%, 12.83% and 12.43%**, respectively.
3. **Financial opportunity:** incremental promotion value is **not quantified**. The **$250.79** improvement over historical popularity and **$398.33** over forecast popularity are differences in **existing GP represented by the selections**, not new profit, available savings or forecasts of placement response. Do not add these alternatives together.
4. **Dollar classification:** **observed retrospective GP attribution** under a model-based ranking. Future ranking scores are **estimates**, not actual sales. No causal dollar uplift is measured.
5. **Simplest baseline:** historical branch popularity is the primary baseline; the margin ranking beats it on this proxy by **5.31% relative**, or approximately **0.68 percentage points** of all June GP. Forecast popularity is an additional comparator. Ranking quality and a sales intervention are different tasks.
6. **Limitations:** three slots are an assumed attention constraint; no exposure, availability or customer response is modeled. June is an already-inspected internal benchmark. Recorded sales may be constrained demand, and a product-level forecast does not establish that promoting it changes its sales. Forecast/margin confounding and cannibalization remain possible. No uncertainty interval for the capture advantage was established.
7. **Specific action:** test margin-based versus historical-popularity placement with equivalent slot count, eligibility, availability and visibility. Keep discounts constant initially. Compare **total basket/branch GP after placement cost**, not only GP of featured products, to capture cannibalization. Keep the popularity rule if the tested net benefit is absent.

Sources: [portfolio metrics](findings.json), [existing evaluation protocol](REPORT.md), local June policy records in `artifacts/profit_lab/portfolio_june.csv`.

## 4. Profit-at-risk predictor — Idea 12

1. **Business problem:** identify branch-days with low expected gross-profit downside so managers can review operations before committing resources.
2. **Historical finding:** on 90 June branch-days, the calibrated 10th-quantile model has pinball loss **14.858**, versus **20.686** for the branch's training-period 10th-percentile baseline—a **28.2%** lower loss on this metric. Empirical lower-forecast coverage is **90.0%**, versus the baseline's **98.9%**. Of **27 alerts**, **3** are actually below the training-defined low-GP threshold: **11.1% precision**, **100% recall**, and **24 false positives**.
3. **Financial opportunity:** **not quantifiable** from these results. The model's mean lower forecast of **$274.38 per branch-day**, versus **$204.83** for the baseline, is neither an opportunity value nor a $69.55 profit improvement. No action-specific recovery rate or intervention cost is available.
4. **Dollar classification:** daily GP targets are **observed accounting**; lower forecasts are **estimates**. Pinball loss has USD scale but is a quantile forecast score, not dollars spent or saved.
5. **Simplest baseline:** the unconditional branch training quantile. The model improves pinball loss and produces a less conservative lower forecast; high baseline coverage alone does not make it better. No positive net-value alert/intervention policy has been established against do-nothing monitoring.
6. **Limitations:** only three low-GP events; alert usefulness is weakly assessed. May calibration and June observations are temporally and cross-branch dependent; coverage is not a guaranteed future floor. GP already incorporates recorded costs, including Garden's costing rule. A low forecast does not identify the cause or show that intervention can help. No disruption-specific validation.
7. **Specific action:** run a shadow dashboard with manual review only. Log time spent and reasons for alerts, confirm whether any operational issue was avoidable, and prospectively compare to simple monitoring before authorizing discounts, inventory changes or paid interventions. Do not act automatically on 27 flags to capture three events.

Sources: [risk metrics](findings.json), local saved evaluation `artifacts/profit_lab/profit_risk_june.csv`.

## 5. Profit-aware basket completion — Idea 9

1. **Business problem:** offer an appropriate additional food item with an existing drink while balancing purchase probability and unit GP.
2. **Historical finding:** in **4,734 June beverage baskets** with 22 food candidates, the conditional drink/branch margin rule has **3.21% hit@1** and **$0.1011 matched unit-GP proxy per basket**. The simpler branch-popularity margin rule has **4.06% hit@1** and **$0.1118**. Conditional hit@3 is **9.23%**, versus **8.72%** for that margin baseline; the tradeoff does not rescue the primary top-one proxy. Pure popularity by probability also beats the conditional probability model on hit@1 and pooled log loss.
3. **Financial opportunity:** incremental profit is **not identified**. The conditional rule is approximately **$0.0106 per basket worse** on the matched-GP proxy than the margin baseline. This is a negative ranking result, not a measured financial loss from displaying recommendations. Multiplying it by customers and calling the result lost or recoverable revenue would be unjustified.
4. **Dollar classification:** **historical matched-margin proxy**, computed using pre-June realized unit GP and whether the selected item was already in the completed basket. It is not a recommendation acceptance rate or incremental margin.
5. **Simplest baseline:** branch food popularity weighted by unit GP. The conditional model loses on hit@1 and the primary GP proxy. The earlier category classifier's AUC is unrelated and cannot be attached to this product model.
6. **Limitations:** no ordered item sequence; the alphabetically first drink is the anchor. This is masked completed-basket retrieval, not a demonstrated next-item purchase model. Prior co-purchase can reflect common popularity, not compatibility. No recommendation exposures, stock availability, response or counterfactual baskets. June was already inspected.
7. **Specific action:** avoid deploying the conditional model on the strength of these results. If testing prompts is worthwhile, compare no prompt and the simple popularity/margin prompt, optionally retaining the conditional policy as a research arm. Measure net total GP per assigned eligible basket after prompt cost and displacement of other purchases.

Sources: [all four basket policies](findings.json), [protocol](REPORT.md).

## 6. Crisis survival optimizer — Idea 15

1. **Business problem:** allocate a constrained procurement budget, menu slots and preparation capacity when demand, supply or operating branches change.
2. **Historical finding:** historical product forecasts and recorded prices/costs supply inputs. The dataset itself does **not** establish customer response to war, closures, shortages or menu restrictions. The financial comparisons below are entirely scenario results.
3. **Financial opportunity:** **not established in real USD outcomes**. For one assumed network planning day, results are:

   | Assumed scenario | Optimized mean GP | Difference vs popularity | Difference vs margin rule |
   |---|---:|---:|---:|
   | Ordinary constrained resources | $337.96 | +$9.96 | +$10.05 |
   | Demand −20% | $254.21 | +$1.85 | +$1.05 |
   | Unit cost +15% | $291.28 | +$7.32 | +$3.21 |
   | Harbour closed; no migration | $134.84 | +$10.91 | +$1.02 |
   | Assumed milk resources unavailable | $240.04 | +$21.98 | **−$1.92** |
   | Takeaway share +20 percentage points | $333.27 | +$9.98 | +$6.45 |

4. **Dollar classification:** **simulated GP levels and simulated differences**, not observed revenue or savings. Scenario rows are mutually alternative worlds; do not sum them, annualize them, or add them to pricing/discount opportunities. The computed deltas use unrounded saved values, so subtraction of displayed levels may differ by a cent.
5. **Simplest baseline:** feasible popularity and margin-weighted greedy plans under the same constraints. The optimizer beats popularity in all six simulated cases, but **loses to the margin rule when milk is unavailable**. Report both baselines rather than highlighting only the easier one. Baselines include the same inventory economics; they are not just popularity lists.
6. **Limitations:** 16 planning draws and 512 separate evaluation draws from assumed independent Poisson demand; no real held-out crisis outcomes or uncertainty assessment for mean differences. Budgets/capacities/serving-equivalent limits are invented at 80% of ordinary levels, and menu caps are 12 products per open branch. Ingredient membership is not a verified recipe. All unsold stock has zero salvage; no labor, rent, transport, menu-service requirement or demand substitution. Closure removes Harbour demand without migration; a takeaway switch preserves total expected units. A zero solver gap solves the planning formulation, not the real business problem. Small simulated deltas can disappear under operational costs or misspecified demand.
7. **Specific action:** use the tool for a tabletop exercise only. Obtain actual recipes, shelf lives, salvage values, purchasing limits, labor capacity and service constraints; have operations compare the proposed plan with a simple margin plan. Do not authorize stock transfers or menu cuts from simulated GP alone. If verified inputs and prospective evidence are unavailable, retain this as an appendix rather than the primary business claim.

Sources: [scenario results and solver status](findings.json), [optimizer assumptions](../../src/crisis_optimizer.py).

## 7. Menu substitution during disruption — Idea 11

1. **Business problem:** shortlist possible alternatives when an item or resource becomes unavailable, while considering recorded product margins.
2. **Historical finding:** Jan–May hourly sales profiles can be compared with cosine similarity within product category; recorded prices/costs establish accounting margins. These are similarities and margins, not observed switching behavior. Common schedules can create similarity even when products are not substitutes.
3. **Financial opportunity:** **not quantifiable**. A price-minus-recorded-cost value for an alternative is not recovered profit: neither the number of customers who switch nor the displaced purchases is known. No lost-sales recovery total should be reported.
4. **Dollar classification:** displayed unit margins are **historical accounting amounts at list price**, before the actual purchase's discount and other operating costs. A recovery scenario would be hypothetical, but no validated substitution rate is available to price one.
5. **Simplest baseline:** a staff-reviewed list of available products in the same category. The implemented similarity ranking has **no held-out substitution benchmark** and has not shown better acceptance, service or GP than this manual rule. Mark that comparison unavailable, not a model win.
6. **Limitations:** no recorded stockouts, exposed alternatives, rejected offers or customer choices. Ingredient groups are illustrative and cannot establish ingredient availability or allergen safety. Margin can be distorted by branch cost allocation. No automatic demand transfer is justified.
7. **Specific action:** keep it as a manually verified candidate list. Staff should check actual recipes, stock and customer suitability, then record offered alternatives and acceptance during genuine availability events. Only compare recovery and GP after those data exist; do not infer them from profile similarity.

Sources: [saved candidate lists and interpretation](findings.json), [implemented similarity and ingredient proxies](../../src/profit_lab.py).

## Cross-check: better forecasts do not automatically mean more money

The separate [Step 8 financial sensitivity](../forecast_business_value/REPORT.md) reinforces the distinction: the saved daily XGBoost forecast has better pooled June MAE, but seasonal naive has lower assumed cost in **8 of 9** shortage/waste settings. XGBoost wins Garden and Uptown while naive wins Harbour in all nine settings. Those are hypothetical capacity costs, not actual savings, and they cannot be transferred to the different product-ranking or risk models. They do argue against a universal “ML improves profit” claim. No branch-specific hybrid was prospectively validated.

## CEO-ready conclusion and next evidence

“We reconciled **$2,178.09 of six-month recorded discount exposure** and found that **$121.63 sits on 153 low-margin discounted lines at Garden**. This is a targeted review population, not proven waste. Reconcile Garden's costing and promotion eligibility, then test a narrow policy change against the current policy using net total GP. Supporting analyses show a fragile **$4.50/day fixed-volume pricing sensitivity** and a **$250.79 advantage in selecting existing June GP**; neither is demonstrated extra profit. We retained negative baseline comparisons and will not deploy complexity without a measured net benefit.”

Do not add the three dollar figures: one is a six-month exposure/subset, one a hypothetical daily change, and one a retrospective June selection metric. There is no combined opportunity total. Predeclare the intervention and cost accounting, track implementation cost and customer response, and validate on later dates. If that work shows no net benefit, the correct financial recommendation is to keep the simpler policy.

Evidence reviewed: [machine-readable Profit Lab results](findings.json), [component report](REPORT.md), [executed inspection notebook](../../notebooks/04_profit_lab.ipynb), implementation sources linked above, and [Step 8 results](../forecast_business_value/model_comparison.csv). Original CSV SHA-256: `f1672e728c28295b2b802d878fd38a158ba039827b429355e8438ee0463237a1`. Original data, model artifacts and forecast outputs were not modified during this review.
