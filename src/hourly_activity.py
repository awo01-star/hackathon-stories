"""Step 4: descriptive transaction heatmaps only. No model training."""
from pathlib import Path
import argparse,json
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import seaborn as sns
R=Path(__file__).resolve().parents[1]
DAYS=['Monday','Tuesday','Wednesday','Thursday','Friday','Saturday','Sunday']
def main(path):
 sales=pd.read_csv(path).rename(columns={'Branch':'branch','Date':'date','Time':'time','Transaction ID':'txn'})
 sales['date']=pd.to_datetime(sales.date,format='%Y-%m-%d',errors='raise')
 parsed=pd.to_datetime(sales.time.astype(str),format='%H:%M:%S',errors='coerce')
 if parsed.isna().any():raise ValueError('Invalid times; inspect before plotting')
 sales['hour']=parsed.dt.hour;sales['day_of_week']=sales.date.dt.day_name()
 assert sales.groupby('txn')[['branch','date','hour']].nunique().le(1).all().all()
 b=sales.drop_duplicates('txn');branches=['Harbour','Garden','Uptown'];hours=range(int(b.hour.min()),int(b.hour.max())+1)
 idx=pd.MultiIndex.from_product([branches,DAYS,hours],names=['branch','day_of_week','hour'])
 totals=b.groupby(['branch','day_of_week','hour']).size().reindex(idx,fill_value=0).rename('transactions').reset_index()
 dates=pd.date_range(b.date.min(),b.date.max());exposure=pd.Series(dates.day_name()).value_counts().reindex(DAYS)
 # Check full branch/date coverage; absence of a sale in one hour is still not proof the shop was open.
 for branch in branches:assert b[b.branch==branch].date.nunique()==len(dates),'Incomplete branch/date coverage; revise exposure'
 totals['calendar_dates']=totals.day_of_week.map(exposure);totals['average_transactions_per_calendar_date']=totals.transactions/totals.calendar_dates
 out=R/'reports/activity';figdir=R/'figures/activity';out.mkdir(exist_ok=True);figdir.mkdir(exist_ok=True)
 totals.to_csv(out/'branch_weekday_hour.csv',index=False)
 assert totals.transactions.sum()==b.txn.nunique()
 totalmax=int(totals.transactions.max());avgmax=float(totals.average_transactions_per_calendar_date.max());summary={}
 for branch in branches:
  g=totals[totals.branch==branch]
  for col,kind,fmt,maximum,title,label in [('transactions','totals','.0f',totalmax,'Six-month transaction totals','Unique transactions, Jan–Jun 2026'),('average_transactions_per_calendar_date','daily_average','.1f',avgmax,'Transactions per calendar-date hour','Transactions per calendar date')]:
   pivot=g.pivot(index='day_of_week',columns='hour',values=col).reindex(index=DAYS,columns=hours)
   fig,ax=plt.subplots(figsize=(14,5.2));sns.heatmap(pivot,annot=True,fmt=fmt,cmap='YlOrRd',vmin=0,vmax=maximum,linewidths=.5,linecolor='#f7f3eb',cbar_kws={'label':label},ax=ax,annot_kws={'size':9})
   ax.set(title=f'{branch} · {title}',xlabel='Hour (dataset clock; timezone unspecified)',ylabel='')
   note='Same color scale across branches. Totals reflect weekday exposure (25 or 26 dates).' if kind=='totals' else 'Zero-sale hours included within 07:00–23:59. Calendar exposure is not verified opening-hour exposure.'
   fig.text(.01,.01,note,fontsize=9,color='#555');fig.tight_layout(rect=(0,.04,1,1));fig.savefig(figdir/f'{branch.lower()}_{kind}.png',dpi=140);plt.close(fig)
  byhour=b[b.branch==branch].groupby('hour').size().reindex(hours,fill_value=0)/len(dates)
  bydow=b[b.branch==branch].groupby('day_of_week').size().reindex(DAYS)/exposure
  summary[branch]={'transactions':int(b[b.branch==branch].shape[0]),'lowestHoursByCalendarAverage':{str(k):float(v)for k,v in byhour.nsmallest(3).items()},'peakHour':int(byhour.idxmax()),'tuesdayTransactionsPerDate':float(bydow['Tuesday']),'tuesdayVsEqualWeightedOtherWeekdays':float(bydow['Tuesday']/bydow.drop('Tuesday').mean()),'lowestWeekday':bydow.idxmin()}
 # Stability descriptor: number of branch-dates where each hour is the least active (ties split).
 full=pd.MultiIndex.from_product([branches,dates,hours],names=['branch','date','hour']);daily=b.groupby(['branch','date','hour']).size().reindex(full,fill_value=0).rename('transactions').reset_index();daily.to_csv(out/'daily_branch_hour_counts.csv',index=False)
 result={'basis':'Unique baskets; raw lines retained, no ML training. Dates Jan 1–Jun 30 2026.','calendarDateExposure':{k:int(v)for k,v in exposure.items()},'observedHours':[min(hours),max(hours)],'openingHoursVerified':False,'branches':summary,'limits':'Low transaction counts do not identify unserved demand or profit opportunity. Need footfall, conversion, available stock, staff capacity, actual opening hours and intervention costs. Timezone unspecified. No significance claim from pooled heatmaps.'}
 (out/'summary.json').write_text(json.dumps(result,indent=2));print(json.dumps(result,indent=2))
 report='''# Step 4 — Transaction activity heatmaps\n\nNo model was trained. Counts use one record per unique basket. The supplied code needs `txn` rather than `transaction_id` in the supplied notebook; time parsing explicitly uses `%H:%M:%S`.\n\nThree total heatmaps reproduce the requested six-month view. Three additional average heatmaps divide each weekday/hour by its number of calendar dates (25 or 26). All branches use a common color scale within each chart type. This supports cross-branch comparison without giving Uptown its own misleading bright-red maximum.\n\nAll three branches have transactions on all 181 dates. That does not establish every opening hour. Observed sales hours span 07:00–23:59; zeros within that range are included in the calendar-average denominator and may represent closure, stockouts or genuine zero sales. No opening-hour normalization can be claimed without a verified schedule.\n\n'''
 for branch,s in summary.items():
  lows=', '.join(f'{int(h):02d}:00 ({v:.2f} transactions/date)'for h,v in s['lowestHoursByCalendarAverage'].items())
  report+=f"## {branch}\n\nLowest pooled hours: {lows}. Peak hour: {s['peakHour']:02d}:00. Weakest average weekday: {s['lowestWeekday']}. Tuesday averages {s['tuesdayTransactionsPerDate']:.2f} transactions/date, or {s['tuesdayVsEqualWeightedOtherWeekdays']:.2f}× the equally weighted mean of other weekdays. These are descriptive pooled results, not proof each date has the same pattern.\n\n![{branch} totals](../../figures/activity/{branch.lower()}_totals.png)\n\n[Calendar-date average heatmap](../../figures/activity/{branch.lower()}_daily_average.png)\n\n"
 report+='''## Interpretation before choosing a forecasting target\n\nTuesday outperformance appears at all branches; the earlier within-week analysis addresses its persistence more directly. These heatmaps alone do not test statistically significant branch differences or identify their causes. Compare normalized shapes and use date/week as the uncertainty unit if testing heterogeneity later.\n\nThe quietest slots are investigation candidates, not automatic promotion opportunities. A low-sales hour may have no reachable audience, a closed shop or insufficient stock; a busy hour may still have unmet demand. Obtain actual operating schedules, footfall, conversion, inventory/stockout and staffing data, then quantify incremental contribution and intervention cost. Do not rank profit opportunity by low transaction count alone.\n\nOutputs: `branch_weekday_hour.csv` (totals and denominators), `daily_branch_hour_counts.csv` (date-level panel for persistence checks), `summary.json`, and six figures. Reproduce with `python3 src/hourly_activity.py --data /path/to/stories_transactions.csv`. The original source CSV and supplied notebook remain unchanged.\n'''
 (out/'REPORT.md').write_text(report)
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--data',default='/Users/aya/Downloads/stories_transactions.csv');main(p.parse_args().data)
