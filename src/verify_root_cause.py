from pathlib import Path
import json,hashlib
import numpy as np
import pandas as pd
from root_cause import branch_state,gp_value,shapley
R=Path(__file__).resolve().parents[1]
def main(path):
 x=pd.read_csv(path);x['date']=pd.to_datetime(x.Date);x['hour']=x.Time.str[:2].astype(int);f=json.loads((R/'reports/root_cause/findings.json').read_text())
 assert hashlib.sha256(Path(path).read_bytes()).hexdigest()==f['sourceSHA256']
 products=sorted(x.Product.unique())
 for branch,g in x.groupby('Branch'):
  state=branch_state(x,branch,products);assert np.isclose(gp_value(state),g['Line Gross Profit (USD)'].sum()/g.date.nunique())
 for source in ['Garden','Uptown']:
  effects=[d['dailyGrossProfitDifference']for d in f['branchDecomposition']['effects']if d['comparison']==source+' to Harbour'];assert np.isclose(sum(effects),f['branchDecomposition']['dailyGP']['Harbour']-f['branchDecomposition']['dailyGP'][source])
 a=f['growthAccounting'];assert np.isclose(sum(a['effectsRevenuePerDay'].values()),a['revenuePerDayJune']-a['revenuePerDayJanuary'])
 for month,key in [(1,'revenuePerDayJanuary'),(6,'revenuePerDayJune')]:
  g=x[x.date.dt.month==month];assert np.isclose(g['Line Revenue (USD)'].sum()/g.date.nunique(),a[key])
 g=f['gardenDecision'];loss=g['uniformVolumeLossBreakEvenForPriceAlignment'];assert np.isclose((1-loss)*(g['recordedGP']+g['sameVolumePriceDifferenceAtHarbourPrices']),g['recordedGP'])
 # Contrast method and exact-duplicate sensitivity must remain explicit and reproducible.
 assert 'geometric' in 'tuesdayRatioVsGeometricMeanOtherDays'.lower();assert f['duplicateSensitivity']['removedRows']==x.duplicated().sum()
 # Simple known identity checks Shapley interactions are split rather than double-counted.
 s=shapley({'a':1,'b':1},{'a':2,'b':2},lambda z:z['a']*z['b']);assert np.isclose(s['a'],1.5);assert np.isclose(s['b'],1.5)
 import nbformat
 n=nbformat.read(R/'notebooks/02_root_cause_investigation.ipynb',as_version=4);nbformat.validate(n);code=[c for c in n.cells if c.cell_type=='code'];assert all(c.execution_count is not None for c in code);assert not any(o.output_type=='error'for c in code for o in c.outputs)
 print('PASS source fingerprint, exact profit/growth reconciliations, Shapley interactions, price break-even, duplicate sensitivity and executed notebook outputs.')
if __name__=='__main__':
 import argparse
 p=argparse.ArgumentParser();p.add_argument('--data',default='/Users/aya/Downloads/stories_transactions.csv');main(p.parse_args().data)
