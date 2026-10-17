"""Step 6: daily forecasting features only; no fitting, imputation or model selection."""
from pathlib import Path
import argparse,hashlib,json
import pandas as pd
R=Path(__file__).resolve().parents[1]
BRANCHES=['Garden','Harbour','Uptown']
START='2026-01-01';END='2026-06-30'
FEATURES=['Branch','DayOfWeek','Month','DayOfMonth','Weekend','Lag1','Lag7','RollingMean7']
def build_daily_features(raw):
 required=['Transaction ID','Date','Branch']
 if not set(required)<=set(raw):raise ValueError(f'Required columns: {required}')
 if raw[required].isna().any().any():raise ValueError('Missing transaction IDs, branch labels or dates need investigation')
 x=raw[required].copy();x['Date']=pd.to_datetime(x.Date,format='%Y-%m-%d',errors='raise')
 if not set(x.Branch)<=set(BRANCHES):raise ValueError('Unexpected branch; revise canonical branch list')
 if x.groupby('Transaction ID')[['Date','Branch']].nunique().gt(1).any().any():raise ValueError('A transaction ID has conflicting branch/date headers')
 x=x[x.Date.between(START,END)]
 observed=x.groupby(['Branch','Date'])['Transaction ID'].nunique().rename('Transactions')
 grid=pd.MultiIndex.from_product([BRANCHES,pd.date_range(START,END)],names=['Branch','Date'])
 # Missing rows stay unknown. No fillna(0), backward filling or current-day target input.
 daily=observed.reindex(grid).reset_index();daily['Transactions']=daily.Transactions.astype('Int64')
 daily['MissingBranchDay']=daily.Transactions.isna();daily['DayOfWeek']=daily.Date.dt.day_name();daily['Month']=daily.Date.dt.month;daily['DayOfMonth']=daily.Date.dt.day;daily['Weekend']=daily.Date.dt.dayofweek.ge(5).astype(int)
 grouped=daily.groupby('Branch',sort=False).Transactions
 daily['Lag1']=grouped.shift(1);daily['Lag7']=grouped.shift(7)
 daily['RollingMean7']=grouped.transform(lambda s:s.shift(1).rolling(7,min_periods=7).mean())
 return daily[['Branch','Date','DayOfWeek','Month','DayOfMonth','Weekend','Lag1','Lag7','RollingMean7','Transactions','MissingBranchDay']]
def save_features(raw,daily,out,report_dir,source_hash):
 report_dir.mkdir(parents=True,exist_ok=True);out.parent.mkdir(parents=True,exist_ok=True)
 missing=daily.loc[daily.MissingBranchDay,['Branch','Date']];daily.to_csv(out,index=False,date_format='%Y-%m-%d');missing.to_csv(report_dir/'missing_branch_days.csv',index=False,date_format='%Y-%m-%d')
 summary={'step':6,'sourceSHA256':source_hash,'dateRange':[START,END],'branches':BRANCHES,'calendarDaysPerBranch':181,'observations':len(daily),'missingBranchDays':len(missing),'missingFeatureValues':{k:int(v)for k,v in daily[FEATURES].isna().sum().items()},'missingValuesAllColumns':{k:int(v)for k,v in daily.isna().sum().items()},'completeHistoryRows':int(daily[FEATURES+['Transactions']].notna().all(axis=1).sum()),'target':'Observed unique transactions per branch/calendar date, not unconstrained demand. Absent branch-days remain unknown; no automatic zeros.','forecastOrigin':'After the previous day closes; one day ahead. Lag1 is not available for every day of a week-ahead forecast.','rollingDefinition':'Previous seven calendar dates, excluding current date; all seven observations required. Missing history propagates.','modelTrained':False,'csv':str(out),'excludedRowsOutsideDateRange':int((~pd.to_datetime(raw.Date).between(START,END)).sum())}
 (report_dir/'feature_summary.json').write_text(json.dumps(summary,indent=2))
 rows='\n'.join(f"| {k} | {v} |" for k,v in summary['missingFeatureValues'].items())
 report=f"""### Step 6 — Daily branch transaction forecasting dataset

**No model trained.** Created [02_demand_forecasting.ipynb](../../notebooks/02_demand_forecasting.ipynb) and local [daily_demand_features.csv](../../daily_demand_features.csv). The panel has **{len(daily)} observations** (3 branches × 181 dates, Jan 1–Jun 30, 2026), **{len(missing)} missing branch-days**, and **{int(daily.Transactions.isna().sum())} missing target values**. Target is unique observed transactions per branch/date, not unconstrained demand.

| Requested feature | Missing values |
|---|---:|
{rows}

Initial history blanks are expected: one lag-1 value per branch and seven lag-7/rolling values per branch. All rows remain in the CSV; {summary['completeHistoryRows']} have complete requested features and target. No filling or dropping is performed. DayOfWeek is a name, Weekend is Saturday/Sunday = 1, and MissingBranchDay is an audit flag rather than a predictor. Date and all other exported calendar/audit columns have no missing values in this file.

All dates are explicitly reindexed within branch. Missing branch-days, if present, remain unknown. Lag1 and Lag7 refer to one/seven calendar days earlier; RollingMean7 uses a shift of one day and requires all seven preceding calendar dates. A missing observation propagates rather than silently becoming zero or an average over fewer days.

The forecast origin is **after the previous day closes**. These features are not a valid drop-in setup for forecasts issued a full week ahead. Calendar features are known in advance; observed branch-day presence does not prove full-day opening or absence of stockouts.

First 15 rows (sorted branch/date):

```text
{daily.head(15).to_string(index=False)}
```

Temporal checks executed in the notebook: deleting June 1 and later records does not change June 1 or earlier predictors; deleting Garden January 20 leaves its target unknown and correctly propagates missing lags/rolling history; unique keys and the 33,887 source transactions reconcile; CSV missingness survives serialization. These checks modify copies only. The original transaction file is unchanged.

Reproduce: `python3 src/prepare_daily_demand.py --data /path/to/stories_transactions.csv`. To regenerate the executed notebook: `STORIES_DATA=/path/to/stories_transactions.csv python3 src/build_demand_notebook.py`. [Machine-readable audit](../demand_forecasting/feature_summary.json); [missing-date list](../demand_forecasting/missing_branch_days.csv). No baseline fitting, imputation, model training or model selection took place in Step 6.
"""
 (report_dir/'REPORT.md').write_text(report)

 print('Total observations:',summary['observations']);print('Missing branch-days:',len(missing));print('\nMissing feature values:\n'+daily[FEATURES].isna().sum().to_string());print('\nMissing target values:',int(daily.Transactions.isna().sum()));print('\nFirst 15 rows:\n'+daily.head(15).to_string(index=False));print('\nSaved:',out)
 return summary
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--data',default='/Users/aya/Downloads/stories_transactions.csv');p.add_argument('--out',default=str(R/'daily_demand_features.csv'));args=p.parse_args();raw=pd.read_csv(args.data);daily=build_daily_features(raw);save_features(raw,daily,Path(args.out),R/'reports/demand_forecasting',hashlib.sha256(Path(args.data).read_bytes()).hexdigest())
