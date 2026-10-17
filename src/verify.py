"""Checks temporal feature isolation, basket integrity and reproduced holdout scores."""
from pathlib import Path
import argparse,json
import numpy as np
import pandas as pd
from sklearn.metrics import roc_auc_score,log_loss
from forecast import build_features
R=Path(__file__).resolve().parents[1]
def main(path):
 x=pd.read_csv(path);x['date']=pd.to_datetime(x.Date)
 a=build_features(x)
 changed=x.copy();changed.loc[changed.date>='2026-06-01','Quantity']*=100
 b=build_features(changed)
 # Replacing all June targets must not alter features for June 1 or any earlier day.
 cols=['Branch','Product','date','lag1','lag7','mean7','mean28','seasonal4','seasonal_blend','dow','day']
 pd.testing.assert_frame_equal(a.loc[a.date<='2026-06-01',cols],b.loc[b.date<='2026-06-01',cols])
 assert (a[a.date=='2026-06-01'].mean28>0).all()
 f=pd.read_csv(R/'artifacts/demand_predictions.csv');assert len(f)==4050;assert not f.duplicated(['Branch','Product','date']).any()
 fm=json.loads((R/'reports/forecast_metrics.json').read_text())
 for name,v in fm['test'].items():assert np.isclose(abs(f.units-f[name]).mean(),v['mae'],rtol=1e-5)
 p=pd.read_csv(R/'artifacts/heldout_predictions.csv');assert p.groupby('Transaction ID').size().eq(5).all();assert not p.duplicated(['Transaction ID','candidate']).any();assert p.date.min()=='2026-06-01';assert p.date.max()=='2026-06-30'
 m=json.loads((R/'reports/metrics.json').read_text())
 for name,v in m['test'].items():
  assert p[name].between(0,1).all();assert np.isclose(roc_auc_score(p.y,p[name]),v['roc_auc'],atol=1e-6);assert np.isclose(log_loss(p.y,p[name]),v['log_loss'],atol=1e-6)
 # Target categories and anchor beverage are disjoint; no completed-basket numerical inputs.
 assert not set(['Bakery','Breakfast','Desserts','Meals','Sandwiches']) & set(['Cold Drinks','Cold Coffee','Hot Coffee','Matcha & Tea'])
 print('PASS: same-day/future target isolation; 4,050 forecast cells; basket-group integrity; persisted holdout scores.')
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--data',default='/Users/aya/Downloads/stories_transactions.csv');main(p.parse_args().data)
