"""Generate a next-day forecast and a clearly labelled food-stock scenario."""
from pathlib import Path
import argparse
import joblib
import numpy as np
import pandas as pd
from scipy.stats import poisson
from forecast import build_features
R=Path(__file__).resolve().parents[1]
def main(path,out):
 x=pd.read_csv(path);x['date']=pd.to_datetime(x.Date);next_day=x.date.max()+pd.Timedelta(days=1)
 future=pd.MultiIndex.from_product([x.Branch.unique(),x.Product.unique(),[next_day]],names=['Branch','Product','date']).to_frame(index=False);future['Quantity']=0
 a=build_features(pd.concat([x[['Branch','Product','date','Quantity']],future],ignore_index=True));a=a[a.date==next_day].copy()
 if a.empty:raise ValueError('At least 28 days of history are required')
 m=joblib.load(R/'artifacts/demand_model.joblib');a['forecast_units']=m.predict(a[['Branch','Product','lag1','lag7','mean7','mean28','dow','day']])
 econ=x.groupby(['Branch','Product']).agg(price=('Unit Price (USD)','mean'),cost=('Unit Cost (USD)','mean'),category=('Category','first'));a=a.join(econ,on=['Branch','Product']);food=a.category.isin(['Bakery','Breakfast','Desserts','Meals','Sandwiches']);a['food_stock_scenario']=np.where(food,poisson.ppf(((a.price-a.cost)/a.price).clip(0,1),a.forecast_units.clip(lower=.001)),np.nan)
 cols=['date','Branch','Product','category','forecast_units','food_stock_scenario','price','cost'];a[cols].to_csv(out,index=False)
 print(f'Wrote {len(a)} forecasts for {next_day.date()} to {out}. Stock quantities are a zero-salvage Poisson scenario; validate before operational use. Model parameters were fit through May 31.')
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--data',default='/Users/aya/Downloads/stories_transactions.csv');p.add_argument('--out',default=str(R/'artifacts/next_day_forecast.csv'));v=p.parse_args();main(v.data,v.out)
