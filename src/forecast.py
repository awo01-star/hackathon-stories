"""Daily product/branch forecasts with lagged features and rolling one-day holdout."""
from pathlib import Path
import argparse,json
import numpy as np
import pandas as pd
from scipy.stats import poisson
from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import OneHotEncoder
from sklearn.pipeline import make_pipeline
from sklearn.metrics import mean_absolute_error,mean_poisson_deviance
from xgboost import XGBRegressor
R=Path(__file__).resolve().parents[1]
def build_features(x):
 idx=pd.MultiIndex.from_product([sorted(x.Branch.unique()),sorted(x.Product.unique()),pd.date_range(x.date.min(),x.date.max())],names=['Branch','Product','date'])
 a=x.groupby(['Branch','Product','date']).Quantity.sum().reindex(idx,fill_value=0).rename('units').reset_index().sort_values(['Branch','Product','date'])
 g=a.groupby(['Branch','Product']).units
 a['lag1']=g.shift(1);a['lag7']=g.shift(7)
 for w in [7,28]:a['mean'+str(w)]=g.transform(lambda s:s.shift(1).rolling(w).mean())
 a['seasonal4']=sum(g.shift(k) for k in [7,14,21,28])/4
 a['seasonal_blend']=(a['seasonal4']+a['mean28'])/2
 a['dow']=a.date.dt.dayofweek;a['day']=(a.date-x.date.min()).dt.days
 a=a.dropna().reset_index(drop=True)
 return a

def main(path):
 x=pd.read_csv(path);x['date']=pd.to_datetime(x.Date)
 a=build_features(x)
 cats=['Branch','Product'];nums=['lag1','lag7','mean7','mean28','dow','day'];features=cats+nums
 tr=a.date<'2026-05-01';va=(a.date>='2026-05-01')&(a.date<'2026-06-01');te=a.date>='2026-06-01'
 def model(depth):return make_pipeline(ColumnTransformer([('c',OneHotEncoder(handle_unknown='ignore',sparse_output=False),cats),('n','passthrough',nums)]),XGBRegressor(objective='count:poisson',n_estimators=250,max_depth=depth,learning_rate=.04,min_child_weight=25,reg_lambda=10,n_jobs=4,random_state=490))
 def metrics(y,p):return {'mae':float(mean_absolute_error(y,p)),'wape':float(abs(y-p).sum()/y.sum()),'poisson_deviance':float(mean_poisson_deviance(y,np.maximum(p,.001))),'bias_fraction':float((p.sum()-y.sum())/y.sum())}
 mods={f'poisson_depth{d}':model(d) for d in [2,4]};v={}
 for n,m in mods.items():m.fit(a.loc[tr,features],a.loc[tr,'units']);v[n]=metrics(a.loc[va,'units'].to_numpy(),m.predict(a.loc[va,features]))
 for col in ['lag7','mean7','mean28','seasonal4','seasonal_blend']:v[col]=metrics(a.loc[va,'units'].to_numpy(),a.loc[va,col].to_numpy())
 win=min(mods,key=lambda n:v[n]['poisson_deviance']);m=mods[win];m.fit(a.loc[tr|va,features],a.loc[tr|va,'units'])
 t=a[te].copy();pred={col:t[col].to_numpy() for col in ['lag7','mean7','mean28','seasonal4','seasonal_blend']};pred[win]=m.predict(t[features]);result={'validation':v,'selected_ml':win,'test':{n:metrics(t.units.to_numpy(),p) for n,p in pred.items()},'test_rows':len(t),'protocol':'One day ahead; observed preceding June days become available before the next forecast. Not a fixed June 1 month-ahead forecast.'}
 # Explicit scenario: all demand observed, all unsold units discarded, no substitution.
 economics=x[x.date<'2026-06-01'].groupby(['Branch','Product']).agg(price=('Unit Price (USD)','mean'),cost=('Unit Cost (USD)','mean'))
 t=t.join(economics,on=['Branch','Product']);q=(t.price-t.cost)/t.price
 policies={}
 food=t.Product.isin(x[x.Category.isin(['Bakery','Breakfast','Desserts','Meals','Sandwiches'])].Product.unique())
 for n,p in pred.items():
  stock=poisson.ppf(q,np.maximum(p,.001));sold=np.minimum(stock,t.units);profit=sold*t.price-stock*t.cost
  policies[n]={'simulated_gross_profit':float(profit[food].sum()),'unsold_units':float(np.maximum(stock-t.units,0)[food].sum()),'unserved_observed_units':float(np.maximum(t.units-stock,0)[food].sum())}
 result['scenario_only_poisson_stocking']=policies
 result['scenario_scope']='Food only; training mean undiscounted prices/costs; every unsold unit discarded; observed sales treated as demand. Not measured savings.'
 import joblib
 joblib.dump(m,R/'artifacts/demand_model.joblib')
 best=min(['lag7','mean7','mean28','seasonal4','seasonal_blend'],key=lambda n:v[n]['poisson_deviance']);rng=np.random.default_rng(490);ixs=[np.flatnonzero(t.date.to_numpy()==d) for d in t.date.unique()];diff=[]
 for _ in range(500):
  ix=np.concatenate([ixs[i] for i in rng.integers(len(ixs),size=len(ixs))]);y=t.units.to_numpy()[ix];diff.append(float(np.mean(abs(y-pred[best][ix])-abs(y-pred[win][ix]))))
 result['paired_day_bootstrap']={'baseline':best,'metric':'baseline MAE minus model MAE; positive favors model','ci95':np.quantile(diff,[.025,.975]).tolist()}
 for n,p in pred.items():t[n]=p
 t.to_csv(R/'artifacts/demand_predictions.csv',index=False);(R/'reports/forecast_metrics.json').write_text(json.dumps(result,indent=2));print(json.dumps(result,indent=2))
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--data',default='/Users/aya/Downloads/stories_transactions.csv');main(p.parse_args().data)
