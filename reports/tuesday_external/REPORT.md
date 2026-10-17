# Tuesday: explanations tested and external checks

Source notebook: [01_eda.ipynb](../../notebooks/01_eda.ipynb). Raw Google Maps readings: [google_popular_times.csv](google_popular_times.csv).

**Ratio definitions.** This report uses two Tuesday ratios. They are not interchangeable with the 1.535× (Tuesday vs Monday, Wednesday, Thursday and Friday) or the adjusted 1.66 in the main README:

- **Weekday index:** average daily transactions for a weekday divided by that branch's average over all seven days (1.00 = an average day). Stories Tuesday ≈ 1.52.
- **Within-week ratio:** Tuesday divided by the mean of the other six days of the same week. Stories median 1.61, range 1.44 to 1.81 over 25 full weeks.

This analysis removes the 132 exact duplicate rows (0.26%). The team's primary analysis keeps them; the effect on these ratios is negligible.

## Explanations tested inside the dataset

| Explanation | Test | Result |
|---|---|---|
| Promotion or discount day | Share of transactions with a discount, Tuesday vs other days | ✗ Ruled out: 10.1% vs 9.4% |
| Product-specific event (e.g. "matcha Tuesday") | Chi-square test of product mix | ✗ Ruled out: no product stands out (p = 0.33); every product rises 1.3× to 2.0× |
| Category or menu event | Chi-square test of category mix | ✗ Ruled out: p = 0.49 |
| Event at one location | Increase by branch; chi-square on branch mix | ✗ Ruled out: same at all three branches (p = 0.34) |
| Group or office catering orders | Basket size, takeaway share | ✗ Ruled out: both unchanged |
| A segment of "Tuesday regulars" | Each identified customer's Tuesday share vs a random-day (binomial) baseline | ✗ Ruled out: spread matches chance (SD 0.153 vs 0.150); every customer is about 50% more likely to come on a Tuesday |
| Same people visiting several times a day | Visits per identified customer per day | ✗ Ruled out: 1.03 vs 1.02 |
| Double posting or batch import | Identical baskets within 2 minutes at the same branch; transaction ID order | ✗ Ruled out: repeats rise only as expected from higher volume; IDs show no Tuesday batches |
| Holidays, payday or month position | Tuesday volume by week of month | ✗ Ruled out: flat across weeks 1 to 4 |
| Calendar inflating monthly growth | Tuesday vs the other days of the same week | ⚠ Real but separate: March and June contain 5 Tuesdays, which inflates their monthly totals |

The only measurable difference in *when* people buy: the Tuesday increase is somewhat stronger in daytime hours than in the evening (chi-square on hour mix, p = 0.004). The size difference is small.

The increase behaves like a **uniform multiplier**: every branch, hour, product and customer scales up by about the same factor. Two explanations remain that this dataset cannot separate: an **outside, chain-wide driver** (for example an app or loyalty campaign not recorded as a line discount) or a **data artifact** (for example a weekday weight in how the replacement dataset was generated).

## Is a Tuesday spike normal for coffee shops?

The same day-of-week tests on [Maven Roasters coffee shop sales](https://mavenanalytics.io/data-playground/coffee-shop-sales): 149,116 line items, 3 New York coffee shops, Jan to Jun 2023 (public domain), with almost the same structure as the Stories data. Weekday index:

| | Mon | **Tue** | Wed | Thu | Fri | Sat | Sun |
|---|---|---|---|---|---|---|---|
| Maven, Astoria | 1.02 | **0.97** | 1.01 | 1.02 | 1.01 | 0.99 | 0.97 |
| Maven, Hell's Kitchen | 0.97 | **1.03** | 0.98 | 1.00 | 1.03 | 0.98 | 1.01 |
| Maven, Lower Manhattan | 1.04 | **0.98** | 0.99 | 1.01 | 1.00 | 1.02 | 0.97 |
| Stories, Harbour | 0.94 | **1.52** | 1.01 | 0.96 | 1.06 | 0.68 | 0.83 |
| Stories, Garden | 0.97 | **1.53** | 0.98 | 0.95 | 1.04 | 0.69 | 0.83 |
| Stories, Uptown | 0.95 | **1.51** | 0.98 | 0.99 | 1.05 | 0.69 | 0.83 |

| | Maven | Stories |
|---|---|---|
| Tuesday vs other days in the same week (median) | 0.96× | 1.61× |
| Range over 25 full weeks | 0.77× to 1.09× | 1.44× to 1.81× |
| Weeks in which Tuesday was the busiest day | 2 of 25 | 25 of 25 |

In the Maven shops no weekday stands out, and Tuesday is below average. In Google popularity data for 22 cafés in central Auckland, Tuesday ranks 4th of 7 days ([JLL Research](https://www.jll.com/en-au/guides/exploring-auckland-cbds-cafe-culture-peak-times-and-trends)).

**Caveat:** Maven Roasters is also a fictitious dataset, and the Auckland data gives ranks, not volumes. The benchmark shows a Tuesday spike is not a general coffee-shop pattern; it cannot show what causes the spike at Stories.

## Do real Stories shops peak on Tuesday? (Google Maps popular times)

**Method.** The Google Maps "Popular times" chart for real Stories branches in Lebanon, read in a normal browser session (no sign-in, read-only) on 17 Oct 2026. Each hourly bar carries a label such as "86% busy at 6 PM", so the labelled values were used (0 to 100, where 100 is the tallest bar that branch shows in the week) rather than bar heights judged by eye. Weekday index computed per branch using only hours shown on every day. Branches are ordered by Google review count, a rough guide to chart reliability.

| Branch (reviews) | Mon | **Tue** | Wed | Thu | Fri | Sat | Sun | Busiest day | Tue rank (of 7) | Peak hour |
|---|---|---|---|---|---|---|---|---|---|---|
| Zalka (342) | 0.97 | **1.07** | 1.08 | 1.07 | 1.04 | 0.91 | 0.85 | Wed | 2 | 22:00 |
| Ain Al Mraiseh (211) | 0.96 | **0.91** | 1.04 | 0.97 | 0.97 | 1.00 | 1.13 | Sun | 7 | 20:00 |
| Antelias (148) | 1.04 | **0.96** | 1.11 | 1.01 | 1.03 | 0.84 | 1.01 | Wed | 6 | 19:00 |
| Khaldeh (148) | 0.89 | **1.01** | 0.98 | 0.87 | 1.03 | 1.17 | 1.05 | Sat | 4 | 21:00 |
| Jnah, Bir Hassan (141) | 1.11 | **1.03** | 1.10 | 1.13 | 1.11 | 0.84 | 0.68 | Thu | 5 | 15:00 |
| Le Mall, Dbayeh (81), Thu and Fri missing | 0.75 | **0.97** | 0.92 | n/a | n/a | 1.22 | 1.14 | Sat | 3 of 5 | 22:00 |
| Centro Mall (66) | 0.83 | **1.08** | 0.82 | 1.39 | 1.30 | 0.81 | 0.76 | Thu | 3 | 21:00 |
| Rabieh (50) | 0.91 | **1.10** | 0.85 | 0.88 | 1.13 | 1.09 | 1.03 | Fri | 2 | 20:00 |
| Saida (50) | 0.79 | **0.74** | 0.80 | 0.95 | 1.32 | 1.27 | 1.12 | Fri | 7 | 21:00 |
| Batroun (48) | 0.78 | **0.82** | 0.92 | 0.96 | 1.04 | 1.23 | 1.24 | Sun | 6 | 20:00 |
| Raouche (20) | 1.05 | **0.80** | 1.31 | 0.95 | 1.09 | 0.94 | 0.86 | Wed | 7 | 21:00 |
| **Mean of the 10 full-week branches** | 0.93 | **0.95** | 1.00 | 1.02 | 1.11 | 1.01 | 0.97 | Fri | 6 | n/a |
| Stories dataset, weekly mean | 0.95 | **1.52** | 0.99 | 0.97 | 1.05 | 0.69 | 0.83 | Tue | 1 | about 21:00 |

- **Tuesday:** between 0.74 and 1.10 at all 10 full-week branches and **never the busiest day**. Mean over the 5 branches with 100+ reviews is 1.00.
- **Saturday:** no consistent dip like the dataset's 0.69; it is among the strongest days at Saida, Batroun, Khaldeh and Rabieh.
- **Peak hour:** evening (19:00 to 22:00) at 10 of 11 branches, matching the dataset. Only Jnah peaks in the afternoon.
- **Not usable:** Verdun and Dunes Verdun show no chart; Le Mall lacks Thursday and Friday; no separate Bliss Street listing; Kouraytem is permanently closed; Khaldeh Drive-Thru (4 reviews) not read.

**Conclusion.** At real Stories shops Tuesday looks ordinary, nowhere near the dataset's 1.5×. This does not support an outside driver that lifts every real shop on Tuesdays, so it makes the **data artifact** explanation more likely. It does not prove it: a campaign that ran only in Jan to Jun 2026 would not show in popular times collected afterwards.

**Caveats**
- Popular times are relative busyness from phone location data, not sales.
- They reflect recent months, not Jan to Jun 2026.
- Values are scaled to each branch's tallest bar, so branches compare only through the weekday index. Branches with few reviews have coarse, noisy charts.
- For the current day's live-hour bar (Saturday), the chart's "usually" value was used, not the live reading.
- The dataset's branches (Harbour, Garden, Uptown) cannot be matched to specific real shops.

## Recommended next step

Compare raw POS or card-terminal totals for a few Tuesdays with this file, and check the marketing and loyalty-app calendar. If the driver is real, it lifts traffic by about 60% at no visible discount cost and is worth testing on Saturday. If it is an artifact, Tuesday-based staffing, targets and forecasts are built on false demand.
