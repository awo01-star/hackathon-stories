# Location research: what can be verified, and a solution without invented addresses

Research accessed October 17, 2026. This is external context and a proposed investigation, not a location-to-transaction join, trained targeting model, or explanation proven by the POS data.

## Search finding

The [Stories brand website](https://storiescoffee.com/) describes its Lebanese origin. The [storiescoffeelb location links](https://linktr.ee/storiescoffeelb) list real names such as Bliss Street, Le Mall Dbayeh, Rabieh and Zalka. I did not verify Garden, Harbour or Uptown as branches corresponding to the CSV. Exact-name searches did not yield an authoritative mapping. This is consistent with anonymization or fictional labels but does not prove it.

The transaction file provides no address, country, city, coordinates or branch key that permits a verified geographic join. Similar-sounding names, a waterfront setting, sales volume and product margins cannot recover that missing key. Keep all three dataset labels unmapped. Also distinguish the Lebanese brand from similarly named businesses elsewhere.

Current online context does not establish that a location was operating, had the same schedule, or served the same audience during January–June 2026. No historical mapping or traffic series was recovered.

## Two grounded external research cases

| Separate public case | Verified context | Audience hypothesis, not observed customer identity | Small intervention to investigate | Missing evidence |
|---|---|---|---|---|
| Stories, Bliss Street | Listed in the brand's location links. AUB's own campus page identifies Bliss Street at its main entrance. | Students, university employees or visitors could be relevant. Proximity does not establish their customer share. | Survey visit purpose and test a student/staff pre-order or off-peak work/study proposition if demand and seating allow. | Exact shop pin/walking route, customer purpose, class/exam calendar, occupancy, offer response and operating economics. |
| Stories, LeMall Dbayeh | Listed in the brand links; the mall's own tenant page places Stories on level L2 in Dbayeh. | Retail employees and shoppers could be relevant; their actual purchases and working schedules are unknown. | With verified management permission and eligibility, test a staff-oriented pre-order/pickup proposition against the existing service. | Actual staff demand/shift patterns, store partner interest, order exposure, preparation capacity and response costs. |

Sources: [brand location links](https://linktr.ee/storiescoffeelb), [AUB campus location](https://aub.edu/AboutUs/Pages/campus.aspx), [LeMall's Stories tenant listing](https://www.dev.lemall.com.lb/Shops/view/382/stories). The mall source is on its `dev` subdomain; corroborate the pin, operating status and details before a live intervention. No distances, walking times, university affiliation, partnership agreement or customer employment is claimed.

These cases **must not** be relabelled Garden or Harbour, assigned the anonymized branches' forecasts, or used to explain Tuesday demand in those branches. They demonstrate where to collect evidence for the idea if no branch crosswalk can be obtained. No business or individual was contacted.

## What can still be done with the anonymized transactions

A location-independent description remains valid. Aggregate all recorded lines within unique transaction ID; observed January–June counts divided by 181 calendar days give:

| Dataset branch | Transactions/calendar day | Dine-in share | Transactions at 09:00–16:59 | Mean recorded GP/transaction |
|---|---:|---:|---:|---:|
| Garden | 61.67 | 58.69% | 39.03% | $4.1919 |
| Harbour | 90.24 | 58.96% | 39.40% | $5.9847 |
| Uptown | 35.30 | 60.25% | 38.37% | $5.4589 |

The branches differ in transaction scale and recorded GP, but these broad visit shares are similar. They do not identify an office, campus, residential neighborhood or demographic group. Recorded GP is not profit after labor/overhead, and the Garden cost-allocation interpretation remains unresolved. This table describes the source, not current operating performance.

The earlier [Tuesday hypothesis check](TUESDAY_WORK_STUDY_HYPOTHESIS.md) found Tuesday dine-in share 58.34% versus 59.15% on other weekdays, and 09:00–16:59 share 39.31% versus 39.01%. These weak purpose proxies neither establish nor rule out a work/study mechanism. No verified source in this investigation establishes that Tuesday work-from-home schedules or lower traffic caused the observed Tuesday increase.

## Practical solution

1. **Keep the existing financial evidence and forecasting attached only to the dataset branch labels.** Do not manufacture a geographic mapping. No new location model can solve missing branch identity from these records alone.
2. **Use public locations as separately named case studies**, beginning with the two sourced examples above. A small voluntary visit-purpose survey and direct occupancy observations can test whether the hypothesized audience is present. Institutions nearby are a contextual indicator, not individual demographic data or proof of customer preferences.
3. **Select an intervention only after confirming the mechanism.** For workers, convenience/pre-ordering might be a better test than another discount. For study visits, verify available seating and GP per occupied seat-hour; attracting long stays could displace other purchases. Do not automatically target Tuesday, which is already busy in the source data.
4. **Set a control before measuring response.** Randomize eligible opportunities before purchase, or predefine balanced switchback periods if individual randomization is infeasible; account for repeat exposure and carryover. Compare total GP per assigned opportunity including nonbuyers, implementation/service cost, substitution and displaced purchases. Record actual exposure and eligibility. Any extra dollars remain unquantified until this test exists.
5. **If a verified alias crosswalk later becomes available**, pin each actual branch, record public POIs with sources and dates, validate historic relevance, and only then join neighborhood context to the matching daily panel. With only three branches, a rich geographic model risks fitting branch identity rather than learning a generalizable location effect; more independent locations or experimentally varied exposures would be needed for stronger ML claims.

A usable planning template is: `net incremental value = incremental recorded GP − campaign/service/implementation cost`, with both terms measured under assignment rather than inferred from gross sales alone. No conversion rate, cost, new-customer count or gain is invented here.

## Presentation wording

“We tested the work/study explanation but cannot identify customers' purposes or real branch locations from the anonymized POS file. Public sources identify university-adjacent and mall-based Stories contexts where the hypothesis could be tested. We propose a prospective, location-specific audience and profit experiment rather than falsely attributing Tuesday's sales to remote work.”

The main report should lead with the already documented accounting/financial investigation. This location work is an evidence-gathering extension, not a newly proven source of sales or profit. No ML was trained, source data changed, map coordinates invented, app feature built, or Git commit/push performed for this research.
