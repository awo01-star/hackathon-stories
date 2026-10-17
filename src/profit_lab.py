"""Ideas 9–15: measured retrieval/forecasting plus separately labelled scenarios."""
from pathlib import Path
import argparse,json,math,hashlib
import numpy as np
import pandas as pd
from sklearn.metrics import log_loss,mean_pinball_loss,precision_score,recall_score
from sklearn.ensemble import HistGradientBoostingRegressor
from sklearn.pipeline import Pipeline
from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import OneHotEncoder
import joblib
R=Path(__file__).resolve().parents[1];OUT=R/'reports/profit_lab';ART=R/'artifacts/profit_lab'
DRINK=['Hot Coffee','Cold Coffee','Cold Drinks','Matcha & Tea'];FOOD=['Bakery','Breakfast','Desserts','Sandwiches','Meals']
def clean(x):
 x=x.copy();x['date']=pd.to_datetime(x.Date);x['hour']=x.Time.str[:2].astype(int);x['discountUSD']=x.Quantity*x['Unit Price (USD)']-x['Line Revenue (USD)'];return x

def basket_completion(x):
 foods=sorted(x[x.Category.isin(FOOD)].Product.unique())
 anchor=x[x.Category.isin(DRINK)].sort_values(['Transaction ID','Product']).drop_duplicates('Transaction ID')[['Transaction ID','Branch','date','Product']].rename(columns={'Product':'anchor'})
 labels=x[x.Category.isin(FOOD)].drop_duplicates(['Transaction ID','Product']).assign(present=1).pivot(index='Transaction ID',columns='Product',values='present').reindex(columns=foods).fillna(0)
 a=anchor.merge(labels,left_on='Transaction ID',right_index=True,how='left');a[foods]=a[foods].fillna(0)
 tr=a[a.date<'2026-05-01'];va=a[a.date.between('2026-05-01','2026-05-31')];te=a[a.date>='2026-06-01']
 def predict(train,test,strength):
  branch=train.groupby('Branch')[foods].mean();group=train.groupby(['Branch','anchor'])[foods].sum();n=train.groupby(['Branch','anchor']).size();rows=[]
  for r in test.itertuples():
   prior=branch.loc[r.Branch].to_numpy();key=(r.Branch,r.anchor);rows.append((group.loc[key].to_numpy()+strength*prior)/(n.loc[key]+strength) if key in n else prior)
  return np.asarray(rows)
 def prior(train,test):return train.groupby('Branch')[foods].mean().reindex(test.Branch).to_numpy()
 trials=[]
 for strength in [20,100]:
  p=predict(tr,va,strength);trials.append({'smoothing':strength,'MayLogLoss':float(log_loss(va[foods].to_numpy().ravel(),p.ravel()))})
 strength=min(trials,key=lambda r:r['MayLogLoss'])['smoothing'];fit=pd.concat([tr,va]);preds={'branch_popularity':prior(fit,te),'drink_branch_smoothed':predict(fit,te,strength)}
 margins=x[(x.date<'2026-06-01')&x.Category.isin(FOOD)].groupby(['Branch','Product']).apply(lambda g:g['Line Gross Profit (USD)'].sum()/g.Quantity.sum(),include_groups=False)
 mat=np.array([[margins.loc[(b,p)]for p in foods]for b in te.Branch]);y=te[foods].to_numpy();metrics={}
 for name,p in preds.items():
  for policy,scores in [('probability',p),('profit_weighted',p*mat)]:
   order=np.argsort(-scores,axis=1,kind='stable');top=order[:,0];metrics[name+'_'+policy]={'hitAt1':float(np.mean(y[np.arange(len(y)),top])),'hitAt3':float(np.mean(np.take_along_axis(y,order[:,:3],axis=1).max(axis=1))),'matchedUnitGPProxy':float(np.mean(y[np.arange(len(y)),top]*mat[np.arange(len(y)),top])),'pooledLogLoss':float(log_loss(y.ravel(),p.ravel()))}
 # Export only aggregate recommendation lists, never row-level customer or basket records.
 examples={}
 for branch in sorted(fit.Branch.unique()):
  examples[branch]={}
  for drink in sorted(fit.anchor.unique()):
   frame=pd.DataFrame({'Branch':[branch],'anchor':[drink]});probs=predict(fit,frame.assign(date=pd.Timestamp('2026-07-01')),strength)[0];scores=probs*np.array([margins.loc[(branch,p)]for p in foods]);ix=np.argsort(-scores)[:3]
   examples[branch][drink]=[{'product':foods[i],'purchaseRate':float(probs[i]),'unitGP':float(margins.loc[(branch,foods[i])]),'score':float(scores[i])}for i in ix]
 summary={'testBeverageBaskets':len(te),'foodCandidates':len(foods),'validationSearch':trials,'selectedSmoothing':strength,'test':metrics,'protocol':'Jan–Apr fit, May chooses smoothing by log loss, refit Jan–May, June masked same-basket product retrieval. Alphabetically first drink anchor; order sequence absent. June previously inspected.','interpretation':'Matched GP is the margin of one item already present in the historical basket. It is not incremental profit or recommendation acceptance. Category AUC from earlier work does not transfer to this product-level task.'}
 return {'metrics':summary,'recommendations':examples}

def dollar_challenge(x):
 days=x.date.nunique();rows=[]
 for branch,g in x.groupby('Branch'):
  weighted=float((g.Quantity*(1-g['Discount Rate'])).sum()/days);step=math.ceil(100/weighted)/100;gp=float(g['Line Gross Profit (USD)'].sum()/days);lift=step*weighted
  rows.append({'branch':branch,'priceIncreaseUSD':step,'affectedUnitsPerDay':float(g.Quantity.sum()/days),'affectedTransactionsPerDay':float(g['Transaction ID'].nunique()/days),'sameVolumeGPIncreasePerDay':lift,'recordedGPPerDay':gp,'uniformVolumeLossBreakEven':lift/(gp+lift),'assumptions':'Same quantities, mix, unit costs and discount percentages; no rounding interaction. A price test is required.'})
 sku=[]
 for (branch,product),g in x.groupby(['Branch','Product']):
  weighted=float((g.Quantity*(1-g['Discount Rate'])).sum()/days);step=math.ceil(100/weighted)/100;price=float(g['Unit Price (USD)'].iloc[0])
  if step/price<=.05:sku.append({'branch':branch,'product':product,'increaseUSD':step,'priceChangeFraction':step/price,'affectedUnitsPerDay':float(g.Quantity.sum()/days),'sameVolumeGPIncreasePerDay':step*weighted})
 return {'allMenuCentPolicies':rows,'singleSKUUnder5Percent':sorted(sku,key=lambda z:(z['increaseUSD'],z['affectedUnitsPerDay']))[:15],'goalUSDPerDay':1,'interpretation':'Smallest whole-cent uniform price step within the enumerated branch-wide policy, or enumerated single-SKU policy with a 5% cap. Not a global optimum across all pricing/discount/mix changes. $1/day is a conditional accounting target, not proven attainable demand response.'}

def recipe_proxy(product,category):
 groups=[]
 if category in ['Hot Coffee','Cold Coffee']:groups.append('coffee')
 if category in ['Hot Coffee','Cold Coffee'] and product not in ['Espresso','Americano','Cold Brew','Iced Americano']:groups.append('milk')
 if 'Matcha' in product:groups+=['matcha','milk']
 if product=='Chai Latte':groups.append('milk')
 if category=='Bakery':groups.append('bakery')
 return sorted(set(groups))
def substitutions(x):
 profile=x[x.date<'2026-06-01'].groupby(['Product','hour']).Quantity.sum().unstack(fill_value=0);profile=profile.div(profile.sum(axis=1),axis=0)
 rows=[]
 for branch,g in x[x.date<'2026-06-01'].groupby('Branch'):
  m=g.groupby('Product').agg(category=('Category','first'),price=('Unit Price (USD)','first'),cost=('Unit Cost (USD)','first'))
  for product,row in m.iterrows():
   a=profile.loc[product].to_numpy();choices=[]
   for alt,r in m[m.category==row.category].iterrows():
    if alt==product:continue
    b=profile.loc[alt].to_numpy();similarity=float(np.dot(a,b)/(np.linalg.norm(a)*np.linalg.norm(b)))
    choices.append({'product':alt,'patternCosine':similarity,'unitGP':float(r.price-r.cost),'price':float(r.price),'assumedGroups':recipe_proxy(alt,r.category)})
   rows.append({'branch':branch,'product':product,'category':row.category,'assumedGroups':recipe_proxy(product,row.category),'alternatives':sorted(choices,key=lambda c:(-c['patternCosine'],-c['unitGP']))[:5]})
 return {'items':rows,'interpretation':'Same-category candidates ranked by similarity of historical hourly sales profiles, not an estimated consumer substitution probability. Correlated schedules may share seasonality or popularity. Ingredient groups are editable serving-equivalent assumptions, not verified recipes or allergen data. No automatic transfer of unavailable-product demand.'}

def profit_risk(x,features_path):
 a=pd.read_csv(features_path,parse_dates=['Date']);gp=x.groupby(['Branch','date'])['Line Gross Profit (USD)'].sum().rename('GP').reset_index().rename(columns={'date':'Date'});a=a.merge(gp,on=['Branch','Date']);a=a[a.Date>='2026-01-08'].copy()
 F=['Branch','DayOfWeek','Month','DayOfMonth','Weekend','Lag1','Lag7','RollingMean7'];tr=a[a.Date<='2026-04-30'];va=a[a.Date.between('2026-05-01','2026-05-31')];te=a[a.Date>='2026-06-01']
 prep=ColumnTransformer([('cat',OneHotEncoder(handle_unknown='ignore',sparse_output=False),['Branch','DayOfWeek']),('num','passthrough',[c for c in F if c not in ['Branch','DayOfWeek']])])
 model=Pipeline([('preprocess',prep),('quantile',HistGradientBoostingRegressor(loss='quantile',quantile=.1,max_iter=150,max_leaf_nodes=7,min_samples_leaf=15,learning_rate=.05,l2_regularization=5,random_state=490))]);model.fit(tr[F],tr.GP)
 # Conservative one-sided calibration on May; freeze Jan–Apr model for June.
 scores=model.predict(va[F])-va.GP.to_numpy();q=min(1,math.ceil((len(scores)+1)*.9)/len(scores));correction=max(0,float(np.quantile(scores,q,method='higher')))
 pred=np.maximum(model.predict(te[F])-correction,0);prior=tr.groupby('Branch').GP.quantile(.1);baseline=te.Branch.map(prior).to_numpy();threshold=tr.groupby('Branch').GP.quantile(.2);cut=te.Branch.map(threshold).to_numpy();actual=te.GP.to_numpy();flag=pred<cut;low=actual<cut
 summary={'alpha':.1,'calibrationCorrectionUSD':correction,'June':{},'lowProfitDefinition':'Below branch-specific 20th percentile of Jan 8–Apr 30 recorded daily GP','alertRule':'Calibrated lower GP forecast is below that low-profit threshold; not a probability estimate.','protocol':'Fixed quantile model fit Jan 8–Apr 30. May one-sided calibration. No refit before June; no June tuning. Normal historical conditions only.','limits':'Lower forecast is not a guaranteed floor. Time dependence, shared branches and distribution shift invalidate a simple independent/exchangeable coverage guarantee. It does not predict disruption outcomes.'}
 for name,p in [('branch_train_quantile',baseline),('quantile_model',pred)]:summary['June'][name]={'pinballLoss':float(mean_pinball_loss(actual,p,alpha=.1)),'lowerBoundCoverage':float(np.mean(actual>=p)),'meanLowerBound':float(p.mean())}
 summary['alerts']={'flaggedDays':int(flag.sum()),'actualLowDays':int(low.sum()),'precision':float(precision_score(low,flag,zero_division=0)),'recall':float(recall_score(low,flag,zero_division=0))}
 detail=te[['Branch','Date','GP']].copy();detail['lowerGP']=pred;detail['threshold']=cut;detail['flag']=flag;detail.to_csv(ART/'profit_risk_june.csv',index=False);joblib.dump({'model':model,'correction':correction,'features':F},ART/'profit_risk_model.joblib')
 # Next-observed-day historical demonstration, after June 30 closes.
 future=[]
 for branch,g in a.groupby('Branch'):
  g=g.sort_values('Date');date=g.Date.max()+pd.Timedelta(days=1);r={'Branch':branch,'Date':str(date.date()),'DayOfWeek':date.day_name(),'Month':date.month,'DayOfMonth':date.day,'Weekend':int(date.dayofweek>=5),'Lag1':g.Transactions.iloc[-1],'Lag7':g.Transactions.iloc[-7],'RollingMean7':g.Transactions.tail(7).mean()};lower=max(0,float(model.predict(pd.DataFrame([r])[F])[0]-correction));future.append({'branch':branch,'date':r['Date'],'lowerGP':lower,'threshold':float(threshold[branch]),'flag':bool(lower<threshold[branch])})
 return {'metrics':summary,'nextDay':future}

def discount_review(x):
 g=x[x['Discount Rate']>0].copy();g['grossMargin']=g['Line Gross Profit (USD)']/g['Line Revenue (USD)'];g['period']=np.where((g.date.dt.dayofweek==1)|g.hour.between(19,22),'Tue OR 19–22','Other')
 groups=g.groupby(['Branch','Category','period']).agg(lines=('Product','size'),discountUSD=('discountUSD','sum'),revenue=('Line Revenue (USD)','sum'),GP=('Line Gross Profit (USD)','sum')).reset_index();groups['margin']=groups.GP/groups.revenue;groups=groups.sort_values('discountUSD',ascending=False)
 low=g[g.grossMargin<.30];groups.to_csv(OUT/'discount_review.csv',index=False)
 return {'totalRecordedDiscountUSD':float(g.discountUSD.sum()),'unroundedRateFormulaUSD':float((g.Quantity*g['Unit Price (USD)']*g['Discount Rate']).sum()),'roundingDifferenceUSD':float((g.Quantity*g['Unit Price (USD)']*g['Discount Rate']).sum()-g.discountUSD.sum()),'lowMarginDiscountedLines':len(low),'lowMarginDiscountUSD':float(low.discountUSD.sum()),'negativeGPDiscountedLines':int((g['Line Gross Profit (USD)']<0).sum()),'reviewGroups':groups.to_dict('records'),'interpretation':'Discount dollars measure fixed-volume financial exposure, not waste or recoverable savings. No recommendation exposure or randomized treatment exists. Larger baskets have more opportunities for a discounted line; no causal lift claim or automatic cancellation is justified.'}

def portfolio(x):
 p=pd.read_csv(R/'artifacts/demand_predictions.csv',parse_dates=['date']);train=x[x.date<'2026-06-01'];actual=x.groupby(['Branch','Product','date'])['Line Gross Profit (USD)'].sum();gp=train.groupby(['Branch','Product']).apply(lambda g:g['Line Gross Profit (USD)'].sum()/g.Quantity.sum(),include_groups=False);pop=train.groupby(['Branch','Product']).Quantity.sum();rows=[]
 for (branch,date),g in p.groupby(['Branch','date']):
  g=g.copy();g['actualGP']=[float(actual.get((branch,r.Product,date),0))for r in g.itertuples()];g['margin']=[float(gp.loc[(branch,v)])for v in g.Product];g['score']=g.poisson_depth4*g.margin;g['historyPop']=[float(pop.loc[(branch,v)])for v in g.Product]
  for name,col in [('historical_popularity','historyPop'),('forecast_popularity','poisson_depth4'),('forecast_margin','score')]:
   chosen=g.sort_values([col,'Product'],ascending=[False,True]).head(3);rows.append({'branch':branch,'date':str(date.date()),'policy':name,'matchedHistoricalGP':float(chosen.actualGP.sum()),'totalGP':float(g.actualGP.sum())})
 table=pd.DataFrame(rows);metrics={}
 for name,g in table.groupby('policy'):metrics[name]={'capturedHistoricalGP':float(g.matchedHistoricalGP.sum()),'captureShare':float(g.matchedHistoricalGP.sum()/g.totalGP.sum())}
 table.to_csv(ART/'portfolio_june.csv',index=False)
 future=pd.read_csv(R/'artifacts/next_day_forecast.csv');future['unitGP']=[float(gp.loc[(r.Branch,r.Product)]) for r in future.itertuples()];future['score']=future.forecast_units*future.unitGP
 items=[{'branch':r.Branch,'product':r.Product,'category':r.category,'forecastUnits':float(r.forecast_units),'unitGP':float(r.unitGP),'score':float(r.score)}for r in future.itertuples()]
 return {'metrics':metrics,'nextDayItems':items,'interpretation':'Top-three held-out retrieval of GP from products already sold in June. It measures historical profit concentration captured by a ranking, not extra GP caused by promotion. Product forecasts were selected in earlier work; June is an internal holdout. No arbitrary reassignment of demand is modeled.'}

def main(path,features_path):
 OUT.mkdir(exist_ok=True);ART.mkdir(exist_ok=True);x=clean(pd.read_csv(path));source_hash=hashlib.sha256(Path(path).read_bytes()).hexdigest();payload={'asOf':'2026-06-30','planningDate':'2026-07-01','historicalDemo':True,'sourceSHA256':source_hash,'modules':{}}
 for key,fn in [('basket',basket_completion),('dollar',dollar_challenge),('substitution',substitutions),('risk',lambda x:profit_risk(x,features_path)),('discount',discount_review),('portfolio',portfolio)]:
  print('Building',key,flush=True);payload['modules'][key]=fn(x)
  (OUT/'findings.json').write_text(json.dumps(payload,indent=2))
 print('Building constrained crisis scenarios',flush=True)
 from crisis_optimizer import optimize_crisis
 future=pd.read_csv(R/'artifacts/next_day_forecast.csv');groups={r.Product:recipe_proxy(r.Product,r.category)for r in future.itertuples()}
 # A takeaway switch changes product mix at constant expected unit volume; not new customers.
 hist=x[x.date<'2026-06-01'];factors={}
 for branch,g in hist.groupby('Branch'):
  mix=g.groupby(['Order Type','Product']).Quantity.sum().unstack(fill_value=0).reindex(columns=sorted(x.Product.unique()),fill_value=0);share=float(mix.loc['Takeaway'].sum()/mix.to_numpy().sum());newshare=min(.95,share+.2);profiles=mix.div(mix.sum(axis=1),axis=0);base=profiles.loc['Takeaway']*share+profiles.loc['Dine-in']*(1-share);shift=profiles.loc['Takeaway']*newshare+profiles.loc['Dine-in']*(1-newshare);ratios=shift/base
  bfuture=future[future.Branch==branch];den=float(sum(r.forecast_units*ratios.loc[r.Product]for r in bfuture.itertuples()));scale=float(bfuture.forecast_units.sum()/den);factors[branch]={p:float(r*scale)for p,r in ratios.items()}
 scenarios=[{'id':'ordinary','title':'Ordinary forecast · constrained resources'},{'id':'demand20','title':'Demand falls 20%','demandDrop':.2},{'id':'cost15','title':'Unit costs rise 15%','costIncrease':.15},{'id':'closed','title':'Harbour closed · no customer migration','closedBranch':'Harbour'},{'id':'milk','title':'Milk serving-equivalents unavailable','blockedGroup':'milk'},{'id':'takeaway','title':'Takeaway mix rises 20 percentage points','takeawayFactors':factors,'takeawayMixIncreasePP':20}]
 payload['modules']['crisis']={'recipeAssumptions':[{'product':p,'groups':g}for p,g in sorted(groups.items())],'scenarios':[],'note':'Assumed one serving-equivalent of each listed resource per stocked item. Not verified recipes, supply quantities or allergens. No actual war-response dataset. Frozen budgets/capacities come from 80% of the ordinary forecast; 12 active products maximum per open branch.'}
 for sc in scenarios:
  print('Scenario',sc['id'],flush=True);payload['modules']['crisis']['scenarios'].append(optimize_crisis(future,groups,sc))
 (OUT/'findings.json').write_text(json.dumps(payload,indent=2));(R/'drink-lens/dist/assets/profit-lab.json').write_text(json.dumps(payload,separators=(',',':')))
 print('Complete. Original source SHA256:',source_hash,flush=True)
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--data',default='/Users/aya/Downloads/stories_transactions.csv');p.add_argument('--features',default=str(R/'daily_demand_features.csv'));a=p.parse_args();main(a.data,a.features)
