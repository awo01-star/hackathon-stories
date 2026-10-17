from pathlib import Path
import argparse,hashlib,json
import numpy as np
import pandas as pd
import joblib,nbformat
from train_daily_models import split_data,FEATURES,GRID,metric
R=Path(__file__).resolve().parents[1]
def main(path):
 out=R/'reports/demand_forecasting';art=R/'artifacts/daily_demand_models';r=json.loads((out/'model_results.json').read_text());lock=json.loads((out/'selection_lock.json').read_text());train,val,test=split_data(path)
 assert [len(train),len(val),len(test)]==[339,93,90]
 assert hashlib.sha256(Path(path).read_bytes()).hexdigest()==r['featureCSV_SHA256']
 assert r['selectedByValidation']==min(r['validation'],key=lambda n:r['validation'][n]['MAE'])==lock['selectedByMay']
 search=pd.read_csv(out/'validation_search.csv');assert len(search)==sum(map(len,GRID.values()))==8
 for name,s in lock['selectedSettings'].items():
  rows=search[search.model==name];best=rows.sort_values(['MAE','trial']).iloc[0];assert int(best.trial)==s['trial']
  assert s['params']==GRID[name][s['trial']]
 for split,frame in [('validation',val),('test',test)]:
  p=pd.read_csv(art/(split+'_predictions.csv'),parse_dates=['Date']);assert len(p)==len(frame);assert not p.duplicated(['Branch','Date']).any();assert np.array_equal(p.Transactions,frame.Transactions)
  assert np.allclose(p['Seasonal naive'],frame.Lag7)
  for name,v in r[split].items():
   got=metric(p.Transactions,p[name]);assert all(np.isclose(v[k],got[k])for k in v)
  for branch,models in r['perBranch'][split].items():
   b=p[p.Branch==branch]
   for name,v in models.items():assert all(np.isclose(v[k],metric(b.Transactions,b[name])[k])for k in v)
 bundle=joblib.load(art/'best_model.joblib');assert bundle['manifest']['selectedByValidation']==r['selectedByValidation'];assert bundle['manifest']['fitThrough']=='2026-05-31'
 pred=np.maximum(bundle['model'].predict(test[FEATURES]),0) if bundle['model'] is not None else test.Lag7.to_numpy()
 assert np.allclose(pred,pd.read_csv(art/'test_predictions.csv')[r['selectedByValidation']])
 n=nbformat.read(R/'notebooks/03_ml_demand_models.ipynb',as_version=4);nbformat.validate(n);assert all(c.execution_count for c in n.cells if c.cell_type=='code');assert not any(o.output_type=='error'for c in n.cells if c.cell_type=='code'for o in c.outputs)
 print('PASS fixed chronological splits, eight-candidate validation selection, all pooled/branch metrics, exact baseline predictions, saved-model reload, CSV fingerprint and executed notebook.')
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--data',default=str(R/'daily_demand_features.csv'));main(p.parse_args().data)
