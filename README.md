# Stories Coffee Hackathon (EECE490)

**Team:** Aya Oueidat (awo01@mail.aub.edu) · Hawraa Salloum (hhs28@mail.aub.edu) · Zahraa Salloum (zhs15@mail.aub.edu)

## Conclusion

**Garden earns $281.54 a day less gross profit than Harbour. About half of that gap ($145.58) is traffic, and the cost and price part ($140.39) is a set of exact formulas, not operations Stories can fix shop by shop.** Garden's unit cost is Harbour's × 1.43 and its price is Harbour's ÷ 1.05, to the cent on all 45 products. We re-derived this independently ([reports/HEADLINE_CHECKS.md](reports/HEADLINE_CHECKS.md)). So no supplier, recipe or waste difference explains it. Garden also runs at 68% of Harbour's traffic in every hour, weekday and month, so no time-targeted action closes that gap.

**Recommendation: three actions, in order of value per dollar spent.**

1. **Ask finance what the 1.43 contains (cost: one email).** It decides $0 to $26,000 of Garden's July to December gross profit. If it is an allocation, Garden's offers and discounts should be judged on Harbour-equivalent cost, and the offer break-even take-up falls from 9.2% and 5.4% to 6.1% and 2.8%. If it is real cash cost, it is the biggest lever Stories has.
2. **Run a 4-week, +5% price test on one Garden category.** Garden's price is already exactly 5% below Harbour's. If no customers leave it is worth up to $6,000 to $8,000 over six months. It breaks even if 9.6% of customers leave and loses $3,400 to $4,600 if 15% leave. Customer response has never been observed in this file, which is why this is a test and not a rollout.
3. **Staff and prepare for Tuesday at about 1.5 times other weekdays.** Tuesday has 94.8 transactions per branch-day against 61.8 for Mon/Wed/Thu/Fri, and it is higher in 100% of branch-weeks and in every branch, hour and product. Basket value is the same ($9.03 against $8.98), so the whole effect is extra transactions. A shift plan costs nothing to try. Before relying on it, compare a few Tuesdays with raw till totals, because the pattern looks too uniform to be organic (see the caveat below).

**Caveat that changes how much to trust the Tuesday action.** Real Stories shops in Lebanon show no Tuesday peak on Google Maps (index 0.74 to 1.10 across 10 branches), daily counts vary exactly as much as pure chance predicts (dispersion 0.93 here against 4.48 for real shops), and every branch shares one weekday and hourly shape. The file may be generated or transformed. We measured the Tuesday spike and the formulas. We did not measure why they exist, and we did not observe customer response to price or offers.

## Measured versus estimated versus assumed

| Item | Status | Source |
|---|---|---|
| $281.54/day gap; $145.58 traffic, $106.80 cost, $33.59 price | Measured (accounting split, not causal) | [root cause report](reports/root_cause/REPORT.md) |
| Garden cost = Harbour × 1.43, price = Harbour ÷ 1.05, 45 of 45 products | Measured | [HEADLINE_CHECKS](reports/HEADLINE_CHECKS.md), [notebook 10](notebooks/10_data_fingerprints.ipynb) |
| Tuesday = 1.535× other weekdays, same basket size | Measured | [HEADLINE_CHECKS](reports/HEADLINE_CHECKS.md), [Step 5](reports/activity/step5_tuesday_distribution.md) |
| Garden July to December profit $56,800 to $77,300 | Estimated (trend forecast, tested on May to June: 10% daily error, 0.4% on the two month total vs 15% and 25% for simple baselines) | [notebook 11](notebooks/11_garden_profit_outlook.ipynb) |
| $0 to $26,000 from the cost gap | Estimated, conditional on what 1.43 means | notebook 11 |
| $6,000 to $8,000 from +5% price | Hypothetical upper bound, customer response never observed | notebook 11 |
| Bundles worth $6,000 to $20,000 a year | Hypothetical, assumes 10 to 20% take-up, never observed | [notebook 06](notebooks/06_bundle_offers.ipynb) |

## Assumptions and what they change

| Assumption (we could not ask) | If wrong, the conclusion changes how |
|---|---|
| The CSV matches the real tills | If Tuesday or the formulas are artifacts of the extract, action 3 falls away and action 1 becomes "ask how the file was produced" |
| Recorded unit cost is the cost Stories cares about | If 1.43 is an allocation, the cost gap is $0 of recoverable profit and Garden's offers become cheaper to run |
| Customers react to a 5% price rise with under 9.6% loss | Above 9.6%, the price test loses money. This is why it runs on one category for 4 weeks |
| A pilot of 4 weeks at three branches detects about 4% bundle take-up | A smaller true take-up would be missed, and the pilot would read as null |
| Exact duplicate rows (132) are real sales | Removing them changes totals by about 0.3% and no conclusion. Primary analysis keeps them, offers notebooks remove them |
| Customer IDs (36% missing) are not needed for the decision | Only loyalty and repeat visit questions are affected, and we make no claim on them |

## What we rejected and why

- **A "query the database" dashboard or a sales summary.** Stories' data team already has these.
- **Treating Tuesday as a promotion, payday, catering, event, double posting or customer segment effect.** We tested ten such explanations. None explains it, because it behaves like a uniform multiplier.
- **Selling the demand forecast as the main result.** XGBoost beats seasonal naive by 5.2% on June MAE, but the 95% interval for the gain is −0.73 to +1.81 transactions a day and includes zero, and the hybrid policy was chosen after seeing June. It stays as supporting work and is not counted as value.
- **Crisis optimisers, a drink recognition app and location models.** No observed link to the three branches, so they are labelled experimental.
- **Estimating cost savings from the 1.43 gap as if recoverable.** It is shown only as a conditional range.

## Practical test before wider use

| Test | Design | Decision rule |
|---|---|---|
| Cost allocation check | Finance explains the 1.43 multiplier | Allocation: use Harbour-equivalent cost for operating decisions. Cash: open a Garden purchasing review |
| Price test | +5% on one Garden category for 4 weeks, matched against the same category at Garden's earlier weeks and at Uptown | Keep the rise if gross profit rises and transaction loss stays under 9.6% |
| Tuesday check | Raw till totals for 4 to 5 Tuesdays against this file | Match: staff to 1.5×. Mismatch: stop using this file for weekday planning |
| Bundle pilot | Two bundles at 10% off, 4 weeks, separate weeks for each | Roll out only if measured take-up beats the break-even of 3 to 9% by branch |

## Data quality

51,177 line rows, 132 exact duplicates (kept in the primary analysis, checked as a sensitivity), 18,691 missing customer IDs (36%), and revenue equals quantity × price × (1 − discount) to within half a cent on every row. The 181 days at three branches have no missing branch-days. Details: [reports/HEADLINE_CHECKS.md](reports/HEADLINE_CHECKS.md) and [notebooks/01_eda.ipynb](notebooks/01_eda.ipynb).

## Where to look

1. [reports/HEADLINE_CHECKS.md](reports/HEADLINE_CHECKS.md): the numbers above, re-derived by one short script (`src/headline_checks.py`).
2. [notebooks/10_data_fingerprints.ipynb](notebooks/10_data_fingerprints.ipynb): which patterns are real behaviour and which are fixed settings.
3. [notebooks/11_garden_profit_outlook.ipynb](notebooks/11_garden_profit_outlook.ipynb): Garden outlook and the three levers.
4. [reports/root_cause/REPORT.md](reports/root_cause/REPORT.md) and [reports/tuesday_external/REPORT.md](reports/tuesday_external/REPORT.md): the gap decomposition and the Tuesday checks.
5. [FULL_REPORT.md](FULL_REPORT.md): every step in full. Everything on demand forecasting, hybrid policy, Profit Lab, the drink camera app, location research and week ahead forecasts is **supporting work**. It is tested against baselines but does not carry the argument and adds no value to the estimates above.

## Reproduce

Put the CSV at `data/stories_transactions.csv` (git ignored, raw data is not published) or set `STORIES_DATA`.

```sh
pip install -r requirements.txt
python src/headline_checks.py --data data/stories_transactions.csv
```

Notebooks 01, 06 to 08, 10 and 11 run from the repository root. Notebook 10's outside benchmark needs the public [Maven Roasters file](https://mavenanalytics.io/data-playground/coffee-shop-sales) at `data/Coffee Shop Sales.xlsx` and is skipped without it. Full commands for the other pipelines are in [FULL_REPORT.md](FULL_REPORT.md).
