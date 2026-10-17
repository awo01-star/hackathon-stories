### Step 5 — Tuesday daily distributions (weekday-only comparator)

The requested code was run on unique transaction counts for each branch/date. All three branches have records on all 181 dates: **543 branch-days** in total. Tuesday has **78 branch-days**; the comparator has **309**. Here **other weekdays means Monday, Wednesday, Thursday and Friday only**. Saturday and Sunday appear in the boxplot but are excluded from the four printed comparison values. This differs from earlier comparisons against all six non-Tuesday days.

| Printed statistic | Transactions per branch-day |
|---|---:|
| Tuesday mean | 94.846154 |
| Other weekdays mean | 61.796117 |
| Tuesday median | 92.500000 |
| Other weekdays median | 59.000000 |

![Daily transaction distributions by weekday](../../figures/activity/tuesday_weekday_boxplot.png)

Both pooled Tuesday mean and median exceed the weekday-only comparator. The mean ratio is **1.535×**; the median ratio is **1.568×**. A higher median supports a shift in typical observed activity rather than relying only on the mean. It does not alone prove that exceptional dates play no role: branch scales and long-run growth are mixed together in the pooled boxes.

| Branch | Tuesday mean | Other weekday mean | Tuesday median | Other weekday median |
|---|---:|---:|---:|---:|
| Garden | 94.65 | 60.82 | 95.00 | 60.00 |
| Harbour | 136.73 | 89.55 | 136.00 | 88.00 |
| Uptown | 53.15 | 35.02 | 49.50 | 35.00 |

[Branch-stratified boxplots](../../figures/activity/tuesday_weekday_boxplot_by_branch.png) use the same vertical scale and show that the mean and median direction is shared by each branch. No formal significance claim is made. The earlier complete-week analysis is the stronger persistence check: Tuesday was the busiest network day in all 25 complete weeks, which is evidence beyond these pooled distributions. Neither check identifies customer motivation, payroll timing, promotion effects or achievable extra profit.

Reproduce: `python3 src/tuesday_distribution.py --data /path/to/stories_transactions.csv`. [Four values and branch diagnostics](../activity/step5_tuesday_distribution.json); [daily counts](../activity/step5_daily_transactions.csv). **No model was trained in Step 5.**
