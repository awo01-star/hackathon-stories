from pathlib import Path
import hashlib,json
import numpy as np
import pandas as pd
from profit_lab import clean,recipe_proxy
from crisis_optimizer import optimize_crisis
R=Path(__file__).resolve().parents[1]
def main(path):
 p=json.loads((R/'reports/profit_lab/findings.json').read_text());x=clean(pd.read_csv(path));assert hashlib.sha256(Path(path).read_bytes()).hexdigest()==p['sourceSHA256'];m=p['modules'];assert set(m)=={'basket','dollar','substitution','risk','discount','portfolio','crisis'}
 b=m['basket']['metrics'];assert len(b['validationSearch'])==2;assert b['selectedSmoothing']==min(b['validationSearch'],key=lambda r:r['MayLogLoss'])['smoothing'];assert b['testBeverageBaskets']==4734
 for branch,drinks in m['basket']['recommendations'].items():
  for drink,recs in drinks.items():
   assert len(recs)==3;assert len({r['product']for r in recs})==3
   for r in recs:assert 0<=r['purchaseRate']<=1;assert np.isclose(r['score'],r['unitGP']*r['purchaseRate'])
 for d in m['dollar']['allMenuCentPolicies']:
  assert d['sameVolumeGPIncreasePerDay']>=1;weighted=d['sameVolumeGPIncreasePerDay']/d['priceIncreaseUSD'];assert weighted*(d['priceIncreaseUSD']-.01)<1
  assert np.isclose((1-d['uniformVolumeLossBreakEven'])*(d['recordedGPPerDay']+d['sameVolumeGPIncreasePerDay'])-d['recordedGPPerDay'],0)
 for item in m['substitution']['items']:
  for alt in item['alternatives']:
   assert alt['product']!=item['product'];assert 0<=alt['patternCosine']<=1+1e-9
 discounted=x[x['Discount Rate']>0];assert np.isclose(discounted.discountUSD.sum(),m['discount']['totalRecordedDiscountUSD']);assert np.isclose(sum(r['discountUSD']for r in m['discount']['reviewGroups']),m['discount']['totalRecordedDiscountUSD'])
 risk=pd.read_csv(R/'artifacts/profit_lab/profit_risk_june.csv');assert len(risk)==90;assert np.isclose((risk.GP>=risk.lowerGP).mean(),m['risk']['metrics']['June']['quantile_model']['lowerBoundCoverage']);assert risk.flag.sum()==m['risk']['metrics']['alerts']['flaggedDays']
 for scenario in m['crisis']['scenarios']:
  rec=scenario['recommendations'];c=scenario['constraints'];assert sum(r['units']*r['cost']for r in rec)<=c['budgetUSD']+1e-5
  for branch in c['capacityUnitsByBranch']:
   rows=[r for r in rec if r['branch']==branch];assert sum(r['units']for r in rows)<=c['capacityUnitsByBranch'][branch];assert len(rows)<=c['menuItemsByBranch'][branch]
  for group,cap in c['resourceServingEquivalents'].items():assert sum(r['units']for r in rec if group in r['assumedGroups'])<=cap+1e-6
  if scenario['id']=='closed':assert not any(r['branch']=='Harbour'for r in rec)
  if scenario['id']=='milk':assert not any('milk'in r['assumedGroups']for r in rec)
  for scores in scenario['policies'].values():assert scores['stockCost']<=c['budgetUSD']+1e-5;assert scores['expectedUnsoldUnits']>=0;assert scores['expectedUnservedUnits']>=0
 # Solve small independent feasibility cases; severe costs should select no unprofitable preparations.
 small=pd.DataFrame({'Branch':['B','B'],'Product':['A','C'],'category':['Other','Other'],'forecast_units':[4.,3.],'price':[5.,4.],'cost':[2.,2.]})
 q=optimize_crisis(small,{'A':['milk'],'C':[]},{'id':'test','title':'Test','blockedGroup':'milk'},menu_cap=1)
 assert not any(r['product']=='A'for r in q['recommendations']);assert len(q['recommendations'])<=1
 q=optimize_crisis(small,{'A':[],'C':[]},{'id':'expensive','title':'Costs','costIncrease':10});assert not q['recommendations']
 assets=json.loads((R/'drink-lens/dist/assets/profit-lab.json').read_text());assert assets==p
 assert not any(k in (R/'drink-lens/dist/assets/profit-lab.json').read_text()for k in ['SYN-','Customer ID','Transaction ID'])
 print('PASS seven modules, source fingerprint, recommendation scores, cent-step minimality, break-even, discount reconciliation, risk metrics, MILP constraints, closed/blocked states and no-negative-margin solver case.')
if __name__=='__main__':
 import argparse
 a=argparse.ArgumentParser();a.add_argument('--data',default='/Users/aya/Downloads/stories_transactions.csv');main(a.parse_args().data)
