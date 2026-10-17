"""Verify economic safeguards, scenario accounting and hourly feature isolation."""
from pathlib import Path
import json
import numpy as np
import pandas as pd
from bundle_planner import features,choose_offers,discount_ceiling,economics,scenario
R=Path(__file__).resolve().parents[1]
def main(path):
 x=pd.read_csv(path);x['date']=pd.to_datetime(x.Date);x['hour']=x.Time.str[:2].astype(int)
 changed=x.copy();changed.loc[changed.date>='2026-06-01','Line Revenue (USD)']*=100
 changed.loc[changed.date>='2026-06-01','Transaction ID']='changed'
 for target in ['revenue','transactions']:
  a=features(x,target);b=features(changed,target);cols=['Branch','hour','date','lag1','lag7','mean7','mean28','seasonal_blend','dow','day'];pd.testing.assert_frame_equal(a.loc[a.date<='2026-06-01',cols],b.loc[b.date<='2026-06-01',cols])
 for y in np.linspace(0,30,301):
  p=choose_offers(y,10,15);assert 0<=p['redemptionCap']<=int(y*.3);assert p['distinctBundles']<=p['redemptionCap']
 assert choose_offers(10,10,15)['redemptionCap']==0
 assert choose_offers(5,10,15)['redemptionCap']>=choose_offers(9,10,15)['redemptionCap']
 assert discount_ceiling(10,8,.3)<0
 p=json.loads((R/'drink-lens/dist/assets/bundle-plan.json').read_text());assert len(p['slots'])==51
 for branch,bs in p['bundles'].items():
  for b in bs:
   e=b['economics'];assert e['grossMargin']>=.30-1e-9;assert 0<=e['discount']<=.12+1e-9;assert b['size'] in [2,3];assert len({i['name'] for i in b['items']})==b['size']
   assert np.isclose(scenario(b,1,0,0)['deltaGrossProfit'],-e['discountDollars']);assert np.isclose(scenario(b,1,1,0)['deltaGrossProfit'],e['grossProfit']);assert np.isclose(scenario(b,1,0,1)['deltaGrossProfit'],e['grossProfit']-(b['items'][0]['price']-b['items'][0]['cost']))
   share=scenario(b,1,0,0)['breakEvenNewBasketShare'];assert abs(scenario(b,1,share,0)['deltaGrossProfit'])<1e-8
 for s in p['slots']:
  assert s['redemptionCap']<=int(s['forecastTransactions']*.3);assert len(s['suggestedBundleIds'])<=s['redemptionCap'];assert s['forecastRevenue']>=0
  if s['pressure']>=1:assert not s['suggestedBundleIds']
 metrics=json.loads((R/'reports/bundle_forecast_metrics.json').read_text());pred=pd.read_csv(R/'artifacts/bundle_hourly_predictions.csv')
 for target,m in metrics.items():
  a=pred[pred.target==target];assert len(a)==1530;assert not a.duplicated(['Branch','hour','date']).any()
  for name,v in m['test'].items():assert np.isclose(abs(a.y-a[name]).mean(),v['mae'],rtol=1e-6)
 print('PASS hourly temporal isolation, margin/discount limits, cannibalization/add-on/new-basket accounting, cap conservation and reproduced June metrics.')
if __name__=='__main__':
 import argparse
 parser=argparse.ArgumentParser();parser.add_argument('--data',default='/Users/aya/Downloads/stories_transactions.csv');main(parser.parse_args().data)
