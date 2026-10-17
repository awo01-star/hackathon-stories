"""Accounting mechanisms and competing-explanation tests, not causal identification."""
from pathlib import Path
import itertools,json,hashlib,math
import numpy as np
import pandas as pd
from scipy.stats import t as student_t
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
R=Path(__file__).resolve().parents[1];OUT=R/'reports/root_cause';FIG=R/'figures/root_cause'

def basket_table(x):
 b=x.groupby('Transaction ID').agg(date=('date','first'),branch=('Branch','first'),hour=('hour','first'),customer=('Customer ID','first'),order=('Order Type','first'),revenue=('Line Revenue (USD)','sum'),profit=('Line Gross Profit (USD)','sum'),units=('Quantity','sum'),discount=('discount_dollars','sum'))
 b['dow']=b.date.dt.dayofweek;b['week']=b.date.dt.to_period('W-SUN').astype(str);return b

def shapley(a,b,value):
 keys=list(a);out={k:0. for k in keys}
 for perm in itertools.permutations(keys):
  state=a.copy();prev=value(state)
  for k in perm:
   state[k]=b[k];now=value(state);out[k]+=now-prev;prev=now
 return {k:v/math.factorial(len(keys)) for k,v in out.items()}

def branch_state(x,b,products):
 g=x[x.Branch==b];n=g['Transaction ID'].nunique();u=g.Quantity.sum();qty=g.groupby('Product').Quantity.sum().reindex(products,fill_value=0)
 pr=g.groupby('Product')['Unit Price (USD)'].first().reindex(products);co=g.groupby('Product')['Unit Cost (USD)'].first().reindex(products)
 rev=g.groupby('Product')['Line Revenue (USD)'].sum().reindex(products)
 return {'transactions_per_day':n/g.date.nunique(),'units_per_basket':u/n,'product_mix':(qty/u).to_numpy(),'unit_prices':pr.to_numpy(),'unit_costs':co.to_numpy(),'discounts':(1-rev/(qty*pr)).to_numpy()}
def gp_value(s):return float(s['transactions_per_day']*s['units_per_basket']*np.sum(s['product_mix']*(s['unit_prices']*(1-s['discounts'])-s['unit_costs'])))

def controlled_tuesday(daily):
 d=daily.copy();d['group']=d.branch+'|'+d.week;d['first3']=d.date.dt.day.le(3).astype(float);d['mid3']=d.date.dt.day.between(14,16).astype(float);d['end7']=d.date.dt.day.ge(25).astype(float)
 X=pd.concat([pd.Series(1.,index=d.index,name='intercept'),pd.get_dummies(d.group,prefix='g',drop_first=True,dtype=float),pd.get_dummies(d.dow,prefix='dow',drop_first=True,dtype=float),d[['first3','mid3','end7']]],axis=1)
 cols=list(X);A=X.to_numpy(float);y=np.log(d.transactions.to_numpy());beta=np.linalg.lstsq(A,y,rcond=None)[0];res=y-A@beta;bread=np.linalg.pinv(A.T@A);groups=d.week.unique();meat=np.zeros((A.shape[1],A.shape[1]))
 for g in groups:
  ix=d.week.eq(g).to_numpy();score=A[ix].T@res[ix];meat+=np.outer(score,score)
 rank=np.linalg.matrix_rank(A);cov=bread@meat@bread*len(groups)/(len(groups)-1)*(len(d)-1)/(len(d)-rank)
 contrast=np.zeros(len(cols));contrast[cols.index('dow_1')]=1
 for k in [2,3,4,5,6]:contrast[cols.index(f'dow_{k}')]-=1/6
 est=float(contrast@beta);se=float(np.sqrt(max(0,contrast@cov@contrast)));crit=student_t.ppf(.975,len(groups)-1)
 out={'observations':len(d),'weekClusters':len(groups),'tuesdayRatioVsGeometricMeanOtherDays':float(np.exp(est)),'ci95':np.exp([est-crit*se,est+crit*se]).tolist(),'specification':'log daily transactions ~ branch×week fixed effects + weekday + calendar proxies days1–3,14–16,25–end. SE clustered by week. Calendar windows are hypothetical, not actual paydays. Exploratory specification.'}
 out['calendarProxyRatios']={}
 for k in ['first3','mid3','end7']:
  i=cols.index(k);s=float(np.sqrt(max(0,cov[i,i])));out['calendarProxyRatios'][k]={'ratio':float(np.exp(beta[i])),'ci95':np.exp([beta[i]-crit*s,beta[i]+crit*s]).tolist()}
 return out

def main(path):
 OUT.mkdir(exist_ok=True);FIG.mkdir(exist_ok=True)
 x=pd.read_csv(path);x['date']=pd.to_datetime(x.Date);x['hour']=x.Time.str[:2].astype(int);x['discount_dollars']=x.Quantity*x['Unit Price (USD)']-x['Line Revenue (USD)'];x['recorded_cost']=x.Quantity*x['Unit Cost (USD)'];b=basket_table(x)
 result={'sourceSHA256':hashlib.sha256(Path(path).read_bytes()).hexdigest(),'basis':'Original rows retained; removal of exact duplicates reported only as sensitivity. Same-product repeated lines might be genuine purchases.','notebookReview':{'source':'01_eda.ipynb (user-supplied, read-only)','duplicateAssumption':'Notebook drops 132 exact duplicates; source cannot prove they are export errors. We preserve raw rows and report both.','customerInference':'Similar branch-choice statistics do not prove replacement customer IDs are invalid or establish a closed customer base. First-observed is not first-ever; anonymous may mean capture failure rather than nonmember.','causality':'Similar Tuesday basket/customer shares do not prove the same individuals visit or reveal payday motivation.'}}
 daily=b.groupby(['branch','date']).agg(transactions=('revenue','size'),revenue=('revenue','sum'),profit=('profit','sum'),units=('units','sum')).reset_index();daily['dow']=daily.date.dt.dayofweek;daily['week']=daily.date.dt.to_period('W-SUN').astype(str)
 dates=daily[['date','week']].drop_duplicates();full=dates.groupby('week').size().loc[lambda s:s==7].index;d=daily[daily.week.isin(full)].copy().reset_index(drop=True)
 result['tuesdayControlled']=controlled_tuesday(d)
 network=d.groupby(['week','date','dow']).transactions.sum().reset_index();ratios=[];winners=[]
 for week,g in network.groupby('week'):
  ratios.append(float(g.loc[g.dow==1,'transactions'].iloc[0]/g.loc[g.dow!=1,'transactions'].mean()));winners.append(int(g.loc[g.transactions.idxmax(),'dow']))
 result['weeklyTuesday']={'fullWeeks':len(ratios),'tuesdayWins':winners.count(1),'ratioRange':[min(ratios),max(ratios)],'medianRatio':float(np.median(ratios))}
 weekbranch=[]
 for (branch,week),g in d.groupby(['branch','week']):weekbranch.append({'branch':branch,'week':week,'ratio':float(g.loc[g.dow==1,'transactions'].iloc[0]/g.loc[g.dow!=1,'transactions'].mean()),'tuesdayWins':int(g.loc[g.transactions.idxmax(),'dow']==1)})
 pd.DataFrame(weekbranch).to_csv(OUT/'tuesday_by_branch_week.csv',index=False)
 # Count dates, rather than treating 50k line items as independent days.
 exposure=x[['date','Branch','hour']].drop_duplicates();rows=[]
 for hour in sorted(b.hour.unique()):
  g=b[b.hour==hour];n1=g[g.dow==1].shape[0];n0=g[g.dow!=1].shape[0];days1=b.loc[b.dow==1,'date'].nunique();days0=b.loc[b.dow!=1,'date'].nunique();rows.append({'hour':int(hour),'tuesdayTransactionsPerDay':n1/days1,'otherTransactionsPerDay':n0/days0,'ratio':(n1/days1)/(n0/days0)})
 pd.DataFrame(rows).to_csv(OUT/'tuesday_hour_ratios.csv',index=False);result['tuesdayHourRatioRange']=[min(r['ratio']for r in rows),max(r['ratio']for r in rows)]
 comparisons={}
 for name,g in [('Tuesday',b[b.dow==1]),('OtherDays',b[b.dow!=1])]:
  comparisons[name]={'transactionsPerDate':len(g)/g.date.nunique(),'ticket':float(g.revenue.mean()),'unitsPerBasket':float(g.units.mean()),'discountedBasketShare':float(g.discount.gt(.00001).mean()),'identifiedBasketShare':float(g.customer.notna().mean()),'takeawayShare':float(g.order.eq('Takeaway').mean())}
 result['tuesdayBasketComparisons']=comparisons
 # Exclude every date with any recorded 15% line, including all other branches on those dates.
 promo_dates=set(x.loc[x['Discount Rate']==.15,'date']);no=d[~d.date.isin(promo_dates)].copy().reset_index(drop=True);result['tuesdayExcluding15PercentDates']=controlled_tuesday(no);result['excludedCampaignDates']=len(promo_dates)
 # Mix stability: total variation in unit shares; descriptive, not proof of equivalence.
 x['tuesday']=x.date.dt.dayofweek==1;mix=x.groupby(['tuesday','Category']).Quantity.sum().unstack(0);mix=mix/mix.sum();mix['difference']=mix[True]-mix[False];mix.to_csv(OUT/'tuesday_category_mix.csv');result['tuesdayCategoryTotalVariation']=float(abs(mix['difference']).sum()/2)
 # Branch matched product accounting: full Shapley averaging all 6! orders avoids arbitrary ordering.
 products=sorted(x.Product.unique());states={br:branch_state(x,br,products)for br in sorted(x.Branch.unique())};decomp=[]
 for branch in ['Garden','Uptown']:
  effects=shapley(states[branch],states['Harbour'],gp_value);before=gp_value(states[branch]);after=gp_value(states['Harbour']);assert np.isclose(sum(effects.values()),after-before)
  for factor,value in effects.items():decomp.append({'comparison':f'{branch} to Harbour','factor':factor,'dailyGrossProfitDifference':value,'sixMonthAccountingDifference':value*181})
 result['branchDecomposition']={'dailyGP':{k:gp_value(v)for k,v in states.items()},'effects':decomp,'interpretation':'Exact observed profit identity decomposition; volume, basket size and mix are accounting factors, not identified behavioral causes or recoverable savings.'};pd.DataFrame(decomp).to_csv(OUT/'branch_profit_shapley.csv',index=False)
 # Garden same volumes: cost and price hypotheses, with break-even volume-loss threshold.
 garden=x[x.Branch=='Garden'];h=x[x.Branch=='Harbour'].groupby('Product')[['Unit Price (USD)','Unit Cost (USD)']].first();cost_gap=float((garden.Quantity*(garden['Unit Cost (USD)']-garden.Product.map(h['Unit Cost (USD)']))).sum());price_gap=float((garden.Quantity*garden.Product.map(h['Unit Price (USD)'])*(1-garden['Discount Rate'])-garden['Line Revenue (USD)']).sum());gp=float(garden['Line Gross Profit (USD)'].sum());rev=float(garden['Line Revenue (USD)'].sum())
 result['gardenDecision']={'sixMonthRecordedCostGapAtHarbourCosts':cost_gap,'sameVolumePriceDifferenceAtHarbourPrices':price_gap,'recordedGP':gp,'recordedRevenue':rev,'uniformVolumeLossBreakEvenForPriceAlignment':price_gap/(gp+price_gap),'costRecoveryScenarios':{str(v):cost_gap*v for v in [.1,.25,.5]},'interpretation':'Fixed-volume accounting scenarios, not achievable savings or a safe pricing recommendation. Uniform volume response and fixed mix assumed; elasticity unobserved.'}
 pc=x.groupby(['Product','Branch'])[['Unit Price (USD)','Unit Cost (USD)']].first().unstack();rat=pd.DataFrame({'priceGardenHarbour':pc['Unit Price (USD)'].Garden/pc['Unit Price (USD)'].Harbour,'costGardenHarbour':pc['Unit Cost (USD)'].Garden/pc['Unit Cost (USD)'].Harbour});rat.to_csv(OUT/'matched_product_ratios.csv');result['gardenRatios']=rat.agg(['min','median','max']).to_dict()
 # January→June revenue/day decomposition removes month-length effects.
 states_month={}
 for month in [1,6]:
  z=x[x.date.dt.month==month];tx=b[b.date.dt.month==month];states_month[month]={'transactionsPerDay':len(tx)/tx.date.nunique(),'unitsPerBasket':float(z.Quantity.sum()/len(tx)),'netRevenuePerUnit':float(z['Line Revenue (USD)'].sum()/z.Quantity.sum())}
 val=lambda s:s['transactionsPerDay']*s['unitsPerBasket']*s['netRevenuePerUnit'];growth=shapley(states_month[1],states_month[6],val);result['growthAccounting']={'January':states_month[1],'June':states_month[6],'revenuePerDayJanuary':val(states_month[1]),'revenuePerDayJune':val(states_month[6]),'effectsRevenuePerDay':growth,'interpretation':'More transactions is observed; increased footfall, conversion and marketing acquisition cannot be separated without visit/exposure records.'}
 # Novel observed-first customer decomposition does not label customers as newly acquired.
 known=b[b.customer.notna()].copy();first=known.groupby('customer').date.min();known['firstObservedDate']=known.customer.map(first);known['cohort']=known.firstObservedDate.dt.to_period('M').astype(str);known['month']=known.date.dt.to_period('M').astype(str);coh=known.groupby(['month','cohort']).agg(transactions=('revenue','size'),revenue=('revenue','sum'),customers=('customer','nunique'));coh.to_csv(OUT/'observed_first_cohort_growth.csv')
 result['identifiedGrowth']={}
 for month in ['2026-01','2026-06']:
  g=known[known.month==month];early=g[g.cohort=='2026-01'];result['identifiedGrowth'][month]={'identifiedTransactions':len(g),'januaryObservedCohortTransactions':len(early),'januaryObservedCohortActiveCustomers':early.customer.nunique(),'januaryObservedCohortRevenue':float(early.revenue.sum()),'allIdentifiedRevenue':float(g.revenue.sum())}
 # Duplicate sensitivity, no unsupported POS-error assertion.
 dedup=x.drop_duplicates(subset=[c for c in x.columns if c not in ['date','hour','discount_dollars','recorded_cost','tuesday']]);gd=dedup[dedup.Branch=='Garden'];result['duplicateSensitivity']={'removedRows':len(x)-len(dedup),'revenueDifference':float(x['Line Revenue (USD)'].sum()-dedup['Line Revenue (USD)'].sum()),'gardenCostGapDeduplicated':float((gd.Quantity*(gd['Unit Cost (USD)']-gd.Product.map(h['Unit Cost (USD)']))).sum())}
 # Stable macro calendar pattern is compatible with many mechanisms; no geographic story inferred.
 daily.to_csv(OUT/'daily_branch_metrics.csv',index=False);(OUT/'findings.json').write_text(json.dumps(result,indent=2,default=lambda v:int(v) if isinstance(v,np.integer) else str(v)))
 fig,ax=plt.subplots(figsize=(9,4));g=pd.DataFrame(decomp).query("comparison=='Garden to Harbour'");ax.barh(g.factor,g.dailyGrossProfitDifference,color=['#6b7751' if v>0 else '#cb6844'for v in g.dailyGrossProfitDifference]);ax.axvline(0,color='#333',lw=.7);ax.set(xlabel='Contribution to observed GP/day difference (USD)',title='Why Harbour records more profit per day than Garden');fig.tight_layout();fig.savefig(FIG/'branch_profit_decomposition.png',dpi=150);plt.close(fig)
 fig,ax=plt.subplots(figsize=(8,4));r=pd.DataFrame(weekbranch)
 for name,g in r.groupby('branch'):ax.plot(range(len(g)),g.ratio,'o-',ms=3,label=name)
 ax.axhline(1,color='#555',ls='--');ax.set(xlabel='Complete week (chronological)',ylabel='Tuesday orders / mean other-day orders',title='Tuesday effect persists within weeks and branches');ax.legend();fig.tight_layout();fig.savefig(FIG/'tuesday_within_week.png',dpi=150);plt.close(fig)
 print(json.dumps(result,indent=2,default=lambda v:int(v) if isinstance(v,np.integer) else str(v)))
if __name__=='__main__':
 import argparse
 p=argparse.ArgumentParser();p.add_argument('--data',default='/Users/aya/Downloads/stories_transactions.csv');main(p.parse_args().data)
