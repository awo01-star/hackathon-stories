"""Step 5: requested daily weekday boxplot and four descriptive values. No ML."""
from pathlib import Path
import argparse,json,hashlib
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import seaborn as sns
R=Path(__file__).resolve().parents[1]
DAYS=['Monday','Tuesday','Wednesday','Thursday','Friday','Saturday','Sunday']
OTHERS=['Monday','Wednesday','Thursday','Friday']
def summarize(daily):
 t=daily.loc[daily.day=='Tuesday','transactions'];o=daily.loc[daily.day.isin(OTHERS),'transactions']
 return {'tuesdayMean':float(t.mean()),'otherWeekdaysMean':float(o.mean()),'tuesdayMedian':float(t.median()),'otherWeekdaysMedian':float(o.median()),'tuesdayBranchDays':int(len(t)),'otherWeekdayBranchDays':int(len(o)),'meanRatio':float(t.mean()/o.mean()),'medianRatio':float(t.median()/o.median())}
def main(path):
 sales=pd.read_csv(path).rename(columns={'Branch':'branch','Date':'date','Transaction ID':'txn'});sales['date']=pd.to_datetime(sales.date,format='%Y-%m-%d')
 daily=sales.groupby(['branch','date']).agg(transactions=('txn','nunique')).reset_index();daily['day']=daily.date.dt.day_name()
 # The supplied code omits branch/dates without transactions. Here all 543 branch/dates exist.
 expected=sales.branch.nunique()*sales.date.nunique();assert len(daily)==expected
 out=R/'reports/activity';figdir=R/'figures/activity';out.mkdir(exist_ok=True);figdir.mkdir(exist_ok=True)
 result={**summarize(daily),'comparator':OTHERS,'dateRange':[str(sales.date.min().date()),str(sales.date.max().date())],'sourceSHA256':hashlib.sha256(Path(path).read_bytes()).hexdigest(),'byBranch':{b:summarize(g)for b,g in daily.groupby('branch')},'limits':'Pooled branch-day distributions describe higher typical Tuesday activity; they do not alone prove persistence, statistical significance, causation, or incremental-profit opportunity. Weekends excluded from printed comparator; included as separate boxes in plot.'}
 fig,ax=plt.subplots(figsize=(12,6));sns.boxplot(data=daily,x='day',y='transactions',order=DAYS,color='#e6b36b',ax=ax,showfliers=True)
 ax.set(title='Daily Transaction Distribution by Weekday',ylabel='Transactions per Branch per Day',xlabel='');ax.tick_params(axis='x',rotation=30)
 fig.text(.01,.01,'Jan–Jun 2026 · 543 branch-days. Plot includes weekends; printed comparator uses Mon/Wed/Thu/Fri only. Dots are boxplot outliers, not errors.',fontsize=9,color='#555');fig.tight_layout(rect=(0,.045,1,1));fig.savefig(figdir/'tuesday_weekday_boxplot.png',dpi=150);plt.close(fig)
 # Preserve branch-specific diagnostics so the pooled plot is not interpreted as a typical individual branch.
 fig,axes=plt.subplots(1,3,figsize=(15,4.8),sharey=True)
 for ax,branch in zip(axes,['Harbour','Garden','Uptown']):
  sns.boxplot(data=daily[daily.branch==branch],x='day',y='transactions',order=DAYS,color='#b8c29b',ax=ax);ax.set(title=branch,xlabel='',ylabel='Transactions/day' if branch=='Harbour' else '');ax.set_xticks(range(7),['Mon','Tue','Wed','Thu','Fri','Sat','Sun'],rotation=45)
 fig.suptitle('Branch-stratified weekday distributions · common vertical scale');fig.tight_layout();fig.savefig(figdir/'tuesday_weekday_boxplot_by_branch.png',dpi=150);plt.close(fig)
 (out/'step5_tuesday_distribution.json').write_text(json.dumps(result,indent=2));daily.to_csv(out/'step5_daily_transactions.csv',index=False)
 rows='\n'.join(f"| {b} | {s['tuesdayMean']:.2f} | {s['otherWeekdaysMean']:.2f} | {s['tuesdayMedian']:.2f} | {s['otherWeekdaysMedian']:.2f} |"for b,s in result['byBranch'].items())
 report=f'''### Step 5 — Tuesday daily distributions (weekday-only comparator)

The requested code was run on unique transaction counts for each branch/date. All three branches have records on all 181 dates: **543 branch-days** in total. Tuesday has **{result['tuesdayBranchDays']} branch-days**; the comparator has **{result['otherWeekdayBranchDays']}**. Here **other weekdays means Monday, Wednesday, Thursday and Friday only**. Saturday and Sunday appear in the boxplot but are excluded from the four printed comparison values. This differs from earlier comparisons against all six non-Tuesday days.

| Printed statistic | Transactions per branch-day |
|---|---:|
| Tuesday mean | {result['tuesdayMean']:.6f} |
| Other weekdays mean | {result['otherWeekdaysMean']:.6f} |
| Tuesday median | {result['tuesdayMedian']:.6f} |
| Other weekdays median | {result['otherWeekdaysMedian']:.6f} |

![Daily transaction distributions by weekday](../../figures/activity/tuesday_weekday_boxplot.png)

Both pooled Tuesday mean and median exceed the weekday-only comparator. The mean ratio is **{result['meanRatio']:.3f}×**; the median ratio is **{result['medianRatio']:.3f}×**. A higher median supports a shift in typical observed activity rather than relying only on the mean. It does not alone prove that exceptional dates play no role: branch scales and long-run growth are mixed together in the pooled boxes.

| Branch | Tuesday mean | Other weekday mean | Tuesday median | Other weekday median |
|---|---:|---:|---:|---:|
{rows}

[Branch-stratified boxplots](../../figures/activity/tuesday_weekday_boxplot_by_branch.png) use the same vertical scale and show that the mean and median direction is shared by each branch. No formal significance claim is made. The earlier complete-week analysis is the stronger persistence check: Tuesday was the busiest network day in all 25 complete weeks, which is evidence beyond these pooled distributions. Neither check identifies customer motivation, payroll timing, promotion effects or achievable extra profit.

Reproduce: `python3 src/tuesday_distribution.py --data /path/to/stories_transactions.csv`. [Four values and branch diagnostics](../activity/step5_tuesday_distribution.json); [daily counts](../activity/step5_daily_transactions.csv). **No model was trained in Step 5.**
'''
 (out/'step5_tuesday_distribution.md').write_text(report)
 print('Tuesday mean:',result['tuesdayMean']);print('Other weekdays mean:',result['otherWeekdaysMean']);print('Tuesday median:',result['tuesdayMedian']);print('Other weekdays median:',result['otherWeekdaysMedian']);print('Branch-day counts:',result['tuesdayBranchDays'],result['otherWeekdayBranchDays']);print('Mean ratio:',result['meanRatio']);print(pd.DataFrame(result['byBranch']).T.to_string())
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--data',default='/Users/aya/Downloads/stories_transactions.csv');main(p.parse_args().data)
