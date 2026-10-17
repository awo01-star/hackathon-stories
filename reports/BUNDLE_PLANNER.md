# Stories Offer Studio: off-peak bundle planner

## Implemented decision chain

Forecast branch × day × hour transactions and revenue, identify relatively quiet slots, generate popular-drink + lower-volume food candidates, apply branch-specific gross-margin constraints, set pilot redemption caps, and calculate explicit revenue/profit scenarios. This is a decision-support prototype; no offers are sent or activated.

## Forecast evaluation

### transactions

May-selected planning method: xgb_depth4. June MAE: 1.6763 versus 1.7326 for seasonal_blend, a 3.25% reduction. WAPE: 37.14%. Paired-day bootstrap 95% interval for baseline MAE minus ML MAE: [0.0298, 0.0887].

Jan-Apr training after 28-day warmup; May selection by MAE; refit Jan-May; June rolling one-day holdout. This is an additional task explored after earlier June results; prospective validation needed.

### revenue

May-selected planning method: xgb_depth4. June MAE: 16.7812 versus 17.2339 for seasonal_blend, a 2.63% reduction. WAPE: 40.99%. Paired-day bootstrap 95% interval for baseline MAE minus ML MAE: [0.1607, 0.8057].

Jan-Apr training after 28-day warmup; May selection by MAE; refit Jan-May; June rolling one-day holdout. This is an additional task explored after earlier June results; prospective validation needed.

## Honest scope

The evaluated hourly task is new and was developed after previous June analyses. It is an internal chronological holdout, not an untouched external benchmark. One June month and day-bootstrap intervals do not resolve serial dependence. Sales are observed transactions, not unconstrained demand. Zero-filled 07:00–23:00 slots assume operating opportunity; opening hours and stockouts need verification.

The forecast models predict ordinary observed revenue and transaction counts. No model learns promotional uplift, optimal bundle size, discount elasticity or the optimal number of offers: the CSV has no randomized offer exposure, proposed bundle menus or causal outcomes. These decisions use disclosed policy rules.

## Candidate selection and safeguards

January–May only supplies product popularity, cost, price, co-purchase support and unadjusted lift. For each branch, combine a top-five drink with one or two foods from below-median food volume and positive gross margin. Rank by normalized drink popularity × food unit GP with a size penalty. This is a transparent heuristic, not an estimated purchase probability. Co-purchase counts and lifts are diagnostic only; no significance claim is made and multiple-comparison adjustment has not been performed.

Keep the highest-ranked two-item and three-item alternatives. The default policy prefers the two-item option when only one distinct offer is permitted; the UI can compare a three-item alternative. No invented claim that one size is optimal.

Minimum recorded gross margin: 30%. Maximum pilot discount: 12%. Ceiling = 1 − cost / (list price × (1 − margin)). Reject ceilings below the 5% candidate-generation minimum; round effective prices upward to the cent. Branch-specific costs matter; positive gross margin excludes labor, overhead, waste and campaign cost.

Busy pressure = max(predicted transactions / branch recent p75, predicted transactions / network recent p75). Recent p75 uses observed branch/day/hour counts from the preceding 28 days. At pressure ≥1 give zero offers. Otherwise cap=min(floor(0.30×forecast transactions), ceil(0.30×forecast transactions×(1−pressure))). Up to two choices if pressure<0.55, otherwise one; choices cannot exceed the cap. These thresholds express a cautious pilot policy, not capacity estimates. Inventory, eligibility and capacity must constrain a real rollout.

## Revenue and profit scenario accounting

Treat redemption groups as mutually exclusive: (a) truly new baskets, (b) adds food to a drink that would be bought anyway, (c) would buy the whole bundle anyway. For each redemption, compare bundle receipts and costs with that counterfactual basket. Group (c) loses the discount amount; group (b) subtracts the original drink gross profit; group (a) adds bundle GP. Subtract extra slot campaign cost. Eligible redemptions are assumed to have no other overlapping promotion. Holding demand fixed is an assumption, not an elasticity estimate.

Baseline GP is baseline forecast revenue multiplied by branch Jan–May recorded gross-margin ratio: it is a proxy, not a separately validated GP forecast. With-offer revenue and GP are scenarios built on that baseline. Do not present them as measured uplift. Cap redemptions are integer allocations shared across offers; changing take-up cannot exceed the total cap. Campaign cost still applies if offers are scheduled but nobody redeems.

Conservative break-even new-basket share = (discount dollars per redemption + allocated campaign cost per redemption) / regular full-price bundle GP, assuming every other redeemer would buy the whole bundle anyway and no add-on benefit. If the threshold exceeds 100%, that scenario cannot break even.

## Historical demonstration, not live forecasting

The UI plans 2026-07-01 from data through 2026-06-30. The planning models refit on all available history after evaluation; test scores describe separate Jan–May fits. There are 51 branch/hour slots, 16 eligible offer slots and 16 total redemption caps under the default rule. These are conservative pilot allocations, not predictions of bundle sales. It is not an October forecast or a current menu.

## Practical validation

Reconcile branch costs and check inventory before any discount. Run a shadow phase, then randomize eligible slot blocks within branch/day/hour strata to control versus offers. Log all assigned slots, exposures, completed baskets, prices, waste, stockouts, incremental staff cost and cross-slot substitution. Primary endpoint: total GP net of waste and additional cost per assigned slot. Analyze by assigned arm using clustering/carryover controls; choose sample size from pilot variance and the minimum worthwhile net gain. No live activation is implemented.

## Reproduce

```sh
python3 src/bundle_planner.py --data /path/to/stories_transactions.csv
python3 src/verify_bundles.py --data /path/to/stories_transactions.csv
cd drink-lens
npm test
node tests/bundle-browser.mjs
```

`reports/bundle_forecast_metrics.json` stores complete validation/test comparisons; `reports/bundle_offer_schedule.csv` stores the 51-slot plan; ignored `artifacts/bundle_hourly_predictions.csv` stores row-level evaluation predictions. The app loads aggregate `drink-lens/dist/assets/bundle-plan.json`; no customer or transaction records are published. Source CSV remains read-only.

The planner lives at `bundles.html` alongside the existing Drink Lens app. Changes to the scenario sliders run the actual accounting functions in the browser. Export downloads a reviewable JSON plan, with assumptions and allocations; it does not send promotions.
