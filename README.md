# Stories Coffee Hackathon (EECE490)

**Team:** Aya Oueidat (awo01@mail.aub.edu) · Hawraa Salloum (hhs28@mail.aub.edu) · Zahraa Salloum (zhs15@mail.aub.edu)

## Conclusion

**Stories' discounts lose money, and the file lets us measure it.** Harbour ran 15% off nine cold coffees and desserts for two 8-day windows (12 to 19 March, 12 to 19 May). Garden and Uptown sold the same nine items at full price, which makes them a control group. Compared with them, Harbour's units of those items rose **+6.1%** (95% placebo range −9% to +25%). A 15% cut on items with a 66% margin needs **+29%** more units just to break even. So the campaign cost about **$350 of gross profit in 16 days**, and we can say it lost money with about 99% confidence ([reports/promo_audit/REPORT.md](reports/promo_audit/REPORT.md)).

**The same result makes Garden's price test safer.** A 15% cut that moved volume at most +25% means customers respond weakly to price (elasticity −0.36, at most −1.38). Applied to Garden's +5% price test, that predicts a loss of 1.8% of customers (at most 6.5%). Both figures are below the 9.6% at which the test stops paying. Garden's price is exactly Harbour's ÷ 1.05 and its cost exactly Harbour's × 1.43 on all 45 products, so its $281.54 a day gap to Harbour is half traffic ($145.58) and half formulas ($140.39) that head office sets, not shop operations.

**Recommendation: four actions, ranked by value per dollar spent.**

1. **Stop untested blanket discounts. Put the rule `required lift = m / (m − d) − 1` on every promotion brief (cost: nothing).** At a 66% margin, 10% off needs +18% units and 15% off needs +29%. The one campaign we could measure fell short. Every future promotion runs at one branch with a sister branch as the control, exactly as in our audit, which costs nothing extra to analyse.
2. **Ask finance what Garden's ×1.43 contains (cost: one email).** It decides $0 to $26,000 of Garden's July to December gross profit. If it is an allocation, judge Garden's offers on Harbour-equivalent cost. If it is real cash cost, it is the biggest lever Stories has.
3. **Run a 4-week +5% price test on one Garden category.** The expected loss of customers (1.8%, at most 6.5%) is below break-even (9.6%). That puts the estimated value at about $4,900 to $6,500 over six months, with an upper bound of $6,000 to $8,000. The test is still needed, because the elasticity comes from a price cut at another branch.
4. **Staff Tuesday at about 1.5× and Saturday at about 0.7× other weekdays, after one check.** The ratios are identical at all three branches (Tuesday 1.535, Saturday 0.694), and basket value does not change. Compare 4 to 5 Tuesdays and Saturdays with raw till totals first, because real Stories shops show no Tuesday peak on Google Maps.

## Which result holds if the data is real, and which if it is generated

The `SYN-` transaction IDs, exact price and cost formulas, Poisson-level day-to-day noise (0.93 against 4.48 for real shops), one weekday shape shared by all branches, and random customer IDs (visits variance/mean 0.99, 94% seen at several branches) all suggest the file is generated or heavily transformed. We therefore split the actions:

| If Stories' tills confirm the file | If the file is generated or transformed |
|---|---|
| All four actions stand | Actions 2 and 4 are only as good as the generator. The deliverable becomes the **method**: the control-branch discount audit (`src/promo_audit.py`), the break-even rule, and the data fingerprint checks (`src/headline_checks.py`). Stories can run them on its real data in minutes |
| The discount loss is a measured fact | The discount rule is still correct arithmetic, and the control-branch design is still the right way to judge promotions |

## Measured versus estimated versus assumed

| Item | Status | Source |
|---|---|---|
| 15% campaign: +6.1% units vs control, 95% range −9% to +25%, break-even +29%, −$350 gross profit | Measured (difference in differences, placebo test over every 8-day window with no campaign) | [promo audit](reports/promo_audit/REPORT.md) |
| 10% discount is a random per-line flag ($1,707 in six months), so it carries no information about response | Measured | promo audit, section 2 |
| $281.54/day Garden gap: $145.58 traffic, $106.80 cost, $33.59 price | Measured (accounting split, not causal) | [root cause report](reports/root_cause/REPORT.md) |
| Garden cost = Harbour × 1.43, price = Harbour ÷ 1.05; Uptown cost = Harbour × 0.96, price ≈ Harbour × 0.914 (45 of 45) | Measured | [HEADLINE_CHECKS](reports/HEADLINE_CHECKS.md) |
| Uptown's $347/day gap to Harbour is 86% traffic; its profit per transaction is close to Harbour's | Measured | promo audit, section 4 |
| Tuesday 1.535× and Saturday 0.694× other weekdays, same basket size | Measured | HEADLINE_CHECKS |
| Elasticity −0.36 (at most −1.38) | Estimated from one price cut at Harbour, applied to a price rise at Garden | promo audit + this README |
| Garden July to December profit $56,800 to $77,300 | Estimated (trend forecast tested on May to June: 10% daily error vs 15% and 25% for baselines). The growth is uniform across branches and may be a generator setting | [notebook 11](notebooks/11_garden_profit_outlook.ipynb) |
| $0 to $26,000 from the cost gap | Estimated, conditional on what 1.43 means | notebook 11 |
| $4,900 to $6,500 from +5% price | Estimated, linear between notebook 11's $6,000 to $8,000 (no loss) and $0 (9.6% loss) at 1.8% loss | notebook 11 + promo audit |

## Assumptions and what they change

| Assumption (we could not ask) | If wrong, the conclusion changes how |
|---|---|
| The CSV matches the real tills | See the table above: the actions become a method for Stories to run on its own data |
| Campaign dates were not chosen because a dip was expected | If they were, the lift is understated. It would need to be 5 times larger to break even |
| Price response to a cut at Harbour carries over to a rise at Garden | Customers may react more to increases. This is why action 3 is a test on one category, not a rollout |
| The campaign's value is the 16 days only | If it brought new customers who returned, there is value we cannot see, because customer IDs are random here. Stories' CRM can check |
| Recorded unit cost is the cost Stories cares about | If 1.43 is an allocation, the Garden cost gap is $0 of recoverable profit |
| Exact duplicate rows (132) are real sales | Removing them changes totals by about 0.3% and no conclusion |

## What we rejected and why

- **A dashboard or sales summary.** Stories' data team already has these.
- **A before/after comparison of the campaign at Harbour alone.** It would credit the discount with Harbour's January to June growth. The control branches remove that.
- **Learning price response from the 10% discount.** It is a random flag on 5.6% of lines (8.2% of baskets observed against 8.3% expected by chance), with no link to time, item or customer.
- **Loyalty, churn or repeat-visit models.** Customer IDs behave like random labels.
- **Ten explanations for Tuesday** (promotion, payday, catering, events, double posting, segments). None fits a uniform multiplier.
- **Selling the demand forecast as the result.** XGBoost beats seasonal naive by 5.2% on June MAE, but the 95% interval for the gain includes zero. It stays as supporting work.
- **The drink recognition app, crisis optimisers and location models.** They have no observed link to these branches and are listed as side projects below.

## Practical tests before wider use

| Test | Design | Decision rule |
|---|---|---|
| Next promotion | One branch discounts, one sister branch does not, 2 weeks. Run `src/promo_audit.py` with the new dates | Keep the promotion only if the lift beats m/(m − d) − 1 |
| Cost allocation check | Finance explains the 1.43 and 0.96 multipliers | Allocation: use Harbour-equivalent cost. Cash: open a Garden purchasing review |
| Garden price test | +5% on one category, 4 weeks, Uptown's same category as control | Keep it if gross profit rises and units fall less than 9.6% |
| Weekday check | Raw till totals for 4 to 5 Tuesdays and Saturdays against this file | Match: staff to 1.5× and 0.7×. Mismatch: stop using this file for planning |

## Data quality

51,177 line rows, 132 exact duplicates (kept, checked as a sensitivity), 18,691 missing customer IDs (36%), and revenue equals quantity × price × (1 − discount) to within half a cent on every row. 181 days at three branches with no missing branch-days. Details: [reports/HEADLINE_CHECKS.md](reports/HEADLINE_CHECKS.md) and [notebooks/01_eda.ipynb](notebooks/01_eda.ipynb).

## Where to look (core evidence, about 10 minutes)

1. [reports/promo_audit/REPORT.md](reports/promo_audit/REPORT.md): the discount audit, the Uptown split, customer IDs and the weekday table (`src/promo_audit.py`).
2. [reports/HEADLINE_CHECKS.md](reports/HEADLINE_CHECKS.md): every headline number, re-derived by one short script (`src/headline_checks.py`).
3. [notebooks/10_data_fingerprints.ipynb](notebooks/10_data_fingerprints.ipynb): which patterns are behaviour and which are fixed settings.
4. [notebooks/11_garden_profit_outlook.ipynb](notebooks/11_garden_profit_outlook.ipynb): the Garden outlook and lever values.
5. [reports/root_cause/REPORT.md](reports/root_cause/REPORT.md) and [reports/tuesday_external/REPORT.md](reports/tuesday_external/REPORT.md): the gap split and the Tuesday checks.

**Side projects (not part of the argument, no value counted):** demand forecasting and hybrid policy (notebooks 02 to 05, 12 and 13), Profit Lab, bundle and offer pilots (notebooks 06 to 09), the drink recognition app (`drink-lens/`), the crisis optimiser and the location research. They are documented in [FULL_REPORT.md](FULL_REPORT.md) and each one is tested against a baseline, but you can skip them.

## Reproduce

Put the CSV at `data/stories_transactions.csv` (git ignored, raw data is not published) or set `STORIES_DATA`.

```sh
pip install -r requirements.txt
python src/headline_checks.py --data data/stories_transactions.csv
python src/promo_audit.py --data data/stories_transactions.csv
```

Notebooks 01, 06 to 08, 10 and 11 run from the repository root. Notebook 10's outside benchmark needs the public [Maven Roasters file](https://mavenanalytics.io/data-playground/coffee-shop-sales) at `data/Coffee Shop Sales.xlsx` and is skipped without it. Full commands for the other pipelines are in [FULL_REPORT.md](FULL_REPORT.md).
