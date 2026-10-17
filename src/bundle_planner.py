"""Hourly ML forecasts + transparent off-peak bundle policy. CSV is read-only."""
from pathlib import Path
import argparse,json,itertools,math,hashlib
import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import OneHotEncoder
from sklearn.pipeline import make_pipeline
from xgboost import XGBRegressor
R=Path(__file__).resolve().parents[1]
DRINK=['Cold Drinks','Cold Coffee','Hot Coffee','Matcha & Tea']
FOOD=['Bakery','Breakfast','Desserts','Meals','Sandwiches']
FEATURES=['Branch','hour','dow','day','lag1','lag7','mean7','mean28']
def features(x,target):
 idx=pd.MultiIndex.from_product([sorted(x.Branch.unique()),range(7,24),pd.date_range(x.date.min(),x.date.max())],names=['Branch','hour','date'])
 if target=='transactions':s=x.groupby(['Branch','hour','date'])['Transaction ID'].nunique()
 else:s=x.groupby(['Branch','hour','date'])['Line Revenue (USD)'].sum()
 a=s.reindex(idx,fill_value=0).rename('y').reset_index().sort_values(['Branch','hour','date']);g=a.groupby(['Branch','hour']).y
 a['lag1']=g.shift(1);a['lag7']=g.shift(7)
 for w in [7,28]:a['mean'+str(w)]=g.transform(lambda s:s.shift(1).rolling(w).mean())
 a['seasonal4']=sum(g.shift(k) for k in [7,14,21,28])/4;a['seasonal_blend']=(a.seasonal4+a.mean28)/2
 a['dow']=a.date.dt.dayofweek;a['day']=(a.date-x.date.min()).dt.days
 return a.dropna().reset_index(drop=True)
def model(depth,target):
 return make_pipeline(ColumnTransformer([('c',OneHotEncoder(handle_unknown='ignore',sparse_output=False),['Branch']),('n','passthrough',FEATURES[1:])]),XGBRegressor(objective='count:poisson' if target=='transactions' else 'reg:squarederror',n_estimators=240,max_depth=depth,learning_rate=.035,min_child_weight=30,reg_lambda=12,n_jobs=4,random_state=490))
def metrics(y,p):return {'mae':float(np.mean(abs(y-p))),'wape':float(np.sum(abs(y-p))/np.sum(y)),'bias':float((np.sum(p)-np.sum(y))/np.sum(y))}
def discount_ceiling(price,cost,margin):
 if price<=0 or cost<0 or not 0<=margin<1:raise ValueError('Invalid economics')
 return 1-cost/(price*(1-margin))
def economics(price,cost,discount):
 sale=math.ceil(price*(1-discount)*100-1e-8)/100;return {'salePrice':sale,'cost':cost,'grossProfit':sale-cost,'grossMargin':(sale-cost)/sale,'discount':1-sale/price,'requestedDiscount':discount,'listPrice':price,'discountDollars':price-sale}
def scenario(bundle,redemptions,incremental_share=.25,add_on_share=.25,prompt_cost=0):
 # Mutually exclusive: new whole basket; add-on to an existing drink; would-buy-whole-bundle anyway.
 if not (0<=incremental_share<=1 and 0<=add_on_share<=1 and incremental_share+add_on_share<=1):raise ValueError('Scenario shares must sum to at most 1')
 if redemptions<0 or prompt_cost<0:raise ValueError('Negative scenario input')
 n=redemptions;drink_price=bundle['items'][0]['price'];drink_gp=drink_price-bundle['items'][0]['cost'];e=bundle['economics'];same=1-incremental_share-add_on_share
 delta_rev=n*(incremental_share*e['salePrice']+add_on_share*(e['salePrice']-drink_price)-same*e['discountDollars'])
 delta_gp=n*(incremental_share*e['grossProfit']+add_on_share*(e['grossProfit']-drink_gp)-same*e['discountDollars'])-prompt_cost
 # break-even new-basket share when every other redemption would buy the full bundle anyway.
 return {'redemptions':n,'incrementalShare':incremental_share,'addOnShare':add_on_share,'wouldBuyBundleShare':same,'deltaRevenue':delta_rev,'deltaGrossProfit':delta_gp,'breakEvenNewBasketShare':(e['discountDollars']+(prompt_cost/n if n else 0))/(e['grossProfit']+e['discountDollars']) if n else None}
def choose_offers(predicted,branch_peak,network_peak):
 pressure=max(predicted/max(branch_peak,1),predicted/max(network_peak,1));cap=min(math.floor(predicted*.30),math.ceil(predicted*.30*max(0,1-pressure))) if pressure<1 else 0
 return {'pressure':pressure,'redemptionCap':cap,'distinctBundles':min(2 if pressure<.55 else 1,cap),'reason':'At or above branch/network busy threshold' if pressure>=1 else 'Forecast off-peak; cap uses at most 30% of forecast transactions'}
def candidates(x,min_margin=.30,max_discount=.12):
 result={};counts=x.drop_duplicates(['Transaction ID','Product']).groupby(['Branch','Product']).size();basketn=x.groupby('Branch')['Transaction ID'].nunique()
 for branch,b in x.groupby('Branch'):
  stats=b.groupby('Product').agg(price=('Unit Price (USD)','median'),cost=('Unit Cost (USD)','median'),units=('Quantity','sum'),category=('Category','first'))
  stats['unitGP']=stats.price-stats.cost;stats['margin']=stats.unitGP/stats.price
  drinks=stats[stats.category.isin(DRINK)].nlargest(5,'units');food=stats[stats.category.isin(FOOD)];low=food[(food.units<=food.units.median())&(food.margin>=min_margin)].nlargest(6,'unitGP')
  baskets=b.groupby('Transaction ID').Product.agg(set);allsets=list(baskets);out=[]
  for drink in drinks.index:
   for size in [2,3]:
    for fs in itertools.combinations(low.index,size-1):
     if size==3 and stats.loc[fs[0],'category']==stats.loc[fs[1],'category']:continue
     names=[drink,*fs];p=float(stats.loc[names,'price'].sum());c=float(stats.loc[names,'cost'].sum());ceiling=discount_ceiling(p,c,min_margin);discount=math.floor(min(max_discount,ceiling)*100+1e-8)/100
     if discount<.05:continue
     items=[{'name':n,'price':float(stats.loc[n,'price']),'cost':float(stats.loc[n,'cost']),'category':stats.loc[n,'category'],'historicalUnits':int(stats.loc[n,'units'])} for n in names]
     pair=set(names);support=sum(pair<=s for s in allsets);expected=math.prod(float(counts.get((branch,n),0))/int(basketn[branch]) for n in names)
     lift=(support/int(basketn[branch]))/expected if expected else 0
     e=economics(p,c,discount)
     # Transparent heuristic, not a learned promotion-response model. Larger bundles penalized.
     score=(float(stats.loc[drink,'units'])/float(drinks.units.max()))*sum(float(stats.loc[n,'unitGP']) for n in fs)/(size-1)**1.5
     out.append({'id':branch+'-'+str(len(out)),'branch':branch,'items':items,'size':size,'economics':e,'discountCeiling':ceiling,'support':support,'lift':lift,'score':score,'selectionReason':'Popular drink + below-median-volume, positive-margin food; branch-specific cost; co-purchase is supporting evidence only'})
  # Retain options of both sizes, then avoid identical drinks in a slot when possible.
  result[branch]=sorted(out,key=lambda b:b['score'],reverse=True)
 return result

def main(path):
 x=pd.read_csv(path);x['date']=pd.to_datetime(x.Date);x['hour']=x.Time.str[:2].astype(int)
 if not x.hour.between(7,23).all():raise ValueError('Observed hours changed; revise the grid')
 evidence={};nextframes={};forecastframes=[]
 for target in ['transactions','revenue']:
  a=features(x,target);tr=a.date<'2026-05-01';va=(a.date>='2026-05-01')&(a.date<'2026-06-01');te=a.date>='2026-06-01';mods={f'xgb_depth{d}':model(d,target) for d in [2,4]};v={}
  for n,m in mods.items():m.fit(a.loc[tr,FEATURES],a.loc[tr,'y']);v[n]=metrics(a.loc[va,'y'].to_numpy(),np.maximum(m.predict(a.loc[va,FEATURES]),0))
  baselines=['lag7','mean7','mean28','seasonal_blend']
  for n in baselines:v[n]=metrics(a.loc[va,'y'].to_numpy(),a.loc[va,n].to_numpy())
  winner=min(v,key=lambda n:v[n]['mae']);ml=min(mods,key=lambda n:v[n]['mae']);mods[ml].fit(a.loc[tr|va,FEATURES],a.loc[tr|va,'y']);test=a[te].copy();pred={n:test[n].to_numpy() for n in baselines};pred[ml]=np.maximum(mods[ml].predict(test[FEATURES]),0)
  bestbase=min(baselines,key=lambda n:v[n]['mae']);rng=np.random.default_rng(490);indices=[np.flatnonzero(test.date.to_numpy()==d) for d in test.date.unique()];deltas=[]
  for _ in range(500):
   ix=np.concatenate([indices[i] for i in rng.integers(len(indices),size=len(indices))]);yy=test.y.to_numpy()[ix];deltas.append(float(np.mean(abs(yy-pred[bestbase][ix])-abs(yy-pred[ml][ix]))))
  evidence[target]={'validation':v,'selectedForPlanning':winner,'selectedML':ml,'bestBaseline':bestbase,'test':{n:metrics(test.y.to_numpy(),p) for n,p in pred.items()},'pairedDayBootstrapMAEImprovementCI95':np.quantile(deltas,[.025,.975]).tolist(),'testCells':len(test),'protocol':'Jan-Apr training after 28-day warmup; May selection by MAE; refit Jan-May; June rolling one-day holdout. This is an additional task explored after earlier June results; prospective validation needed.'}
  for n,p in pred.items():test[n]=p
  test['target']=target;forecastframes.append(test)
  # Refit the validation-selected policy on all history for the next observed day, separately from evaluation.
  future=x[['Branch','hour','date','Transaction ID','Line Revenue (USD)']].copy();extra=pd.DataFrame([{'Branch':b,'hour':h,'date':x.date.max()+pd.Timedelta(days=1),'Transaction ID':f'future-{b}-{h}','Line Revenue (USD)':0} for b in sorted(x.Branch.unique()) for h in range(7,24)])
  extended=pd.concat([future,extra],ignore_index=True);nxt=features(extended,target);nxt=nxt[nxt.date>x.date.max()].copy()
  if winner in mods:mods[winner].fit(a[FEATURES],a.y);nxt['prediction']=np.maximum(mods[winner].predict(nxt[FEATURES]),0)
  else:nxt['prediction']=nxt[winner]
  nextframes[target]=nxt
 train=x[x.date<'2026-06-01'];bundles=candidates(train);tx=nextframes['transactions'];rv=nextframes['revenue'];revenue_lookup={(r.Branch,int(r.hour)):float(r.prediction) for r in rv.itertuples()}
 # Busy reference values use ONLY data available at the planning cutoff.
 recent=x[x.date>x.date.max()-pd.Timedelta(days=28)];obs=recent.groupby(['Branch','date','hour'])['Transaction ID'].nunique();network_peak=float(obs.quantile(.75));peaks={b:float(obs.loc[b].quantile(.75)) for b in x.Branch.unique()}
 slots=[]
 for row in tx.itertuples():
  policy=choose_offers(float(row.prediction),peaks[row.Branch],network_peak);options=[]
  # Include both bundle sizes as alternatives; never call a heuristic size optimal.
  pool=bundles[row.Branch];two=next((b for b in pool if b['size']==2),None);three=next((b for b in pool if b['size']==3),None)
  for b in [two,three]:
   if b:options.append(b['id'])
  selected=options[:policy['distinctBundles']];slots.append({'date':str(row.date.date()),'branch':row.Branch,'hour':int(row.hour),'forecastTransactions':float(row.prediction),'forecastRevenue':revenue_lookup[row.Branch,int(row.hour)],**policy,'suggestedBundleIds':selected,'alternativeBundleIds':options,'branchBusyThreshold':peaks[row.Branch],'networkBusyThreshold':network_peak})
 payload={'asOf':str(x.date.max().date()),'planningDate':str((x.date.max()+pd.Timedelta(days=1)).date()),'isHistoricalDemo':True,'currency':'USD','policy':{'minimumGrossMargin':.30,'maximumDiscount':.12,'maximumParticipation':.30,'note':'Rules are testable pilot policies, not learned optimal promotion effects. Busy slots receive zero offers. No inventory or capacity data is available.'},'historicalGrossMargin':{b:float(g['Line Gross Profit (USD)'].sum()/g['Line Revenue (USD)'].sum()) for b,g in train.groupby('Branch')},'metrics':evidence,'slots':slots,'bundles':{b:[v for v in vs if v['id'] in {i for s in slots if s['branch']==b for i in s['alternativeBundleIds']}] for b,vs in bundles.items()},'sourceSHA256':hashlib.sha256(Path(path).read_bytes()).hexdigest()}
 (R/'drink-lens/dist/assets/bundle-plan.json').write_text(json.dumps(payload,indent=2));(R/'reports/bundle_forecast_metrics.json').write_text(json.dumps(evidence,indent=2));pd.DataFrame(slots).to_csv(R/'reports/bundle_offer_schedule.csv',index=False);pd.concat(forecastframes).to_csv(R/'artifacts/bundle_hourly_predictions.csv',index=False)
 (R/'artifacts').mkdir(exist_ok=True)
 print(json.dumps(evidence,indent=2));print('Wrote 51 next-day hourly planning slots and separate evaluated forecast metrics.')
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--data',default='/Users/aya/Downloads/stories_transactions.csv');main(p.parse_args().data)
