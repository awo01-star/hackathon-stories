"""Independent financial identities, input immutability and analytical fixtures."""
from pathlib import Path
import argparse
import json
import tempfile
import numpy as np
import pandas as pd
import nbformat
from forecast_business_value import ROOT, decision_loss, evaluate, load_forecasts, sha


def verify(data_path):
    out=ROOT/'reports/forecast_business_value'
    f=json.loads((out/'findings.json').read_text())
    assert sha(data_path)==f['sourceSHA256']
    for name,digest in f['lockedInputHashes'].items():
        p=Path(data_path) if name==Path(data_path).name else ROOT/name
        assert sha(p)==digest, f'Locked input changed: {name}'
    # Manual analytical fixture: missed demand and excess cannot coexist.
    under,over,uc,oc=decision_loss([10,10,10],[8,12,10],2,.5)
    np.testing.assert_array_equal(under,[2,0,0]);np.testing.assert_array_equal(over,[0,2,0])
    np.testing.assert_array_equal(uc,[4,0,0]);np.testing.assert_array_equal(oc,[0,1,0])
    # Independent 90-observation oracle and asymmetric-cost fixture.
    fixture=pd.MultiIndex.from_product([['Garden','Harbour','Uptown'],pd.date_range('2026-06-01','2026-06-30')],names=['Branch','Date']).to_frame(index=False)
    fixture=fixture.assign(Transactions=10,**{'Seasonal naive':8,'XGBoost':12})
    econ=pd.DataFrame({'Branch':['Garden','Harbour','Uptown'],'Period':'Jan-May calibration',
                       'GPPerTransactionUSD':4.,'InputCostPerTransactionUSD':2.})
    _,s,_,_=evaluate(fixture,econ)
    case=s[(s.Branch=='ALL')&(s.Scenario=='S0.5_W0.25')].set_index('Model')
    assert case.loc['Seasonal naive','TotalDecisionCostUSD']==360
    assert case.loc['XGBoost','TotalDecisionCostUSD']==90
    assert case.loc['Oracle','TotalDecisionCostUSD']==0
    # Independently price all saved June decisions directly from the original lines.
    x=pd.read_csv(data_path,parse_dates=['Date'])
    before=x[x.Date<'2026-06-01'];d=before.groupby('Branch')['Transaction ID'].nunique()
    gp=before.groupby('Branch')['Line Gross Profit (USD)'].sum()/d
    cost=(before.Quantity*before['Unit Cost (USD)']).groupby(before.Branch).sum()/d
    p=pd.read_csv(ROOT/'artifacts/daily_demand_models/test_predictions.csv',parse_dates=['Date'])
    targets=x[x.Date.between('2026-06-01','2026-06-30')].groupby(['Branch','Date'])['Transaction ID'].nunique()
    observed=p.set_index(['Branch','Date']).Transactions
    pd.testing.assert_series_equal(observed.sort_index(),targets.sort_index(),check_names=False)
    report=pd.read_csv(out/'decision_costs.csv');comparison=pd.read_csv(out/'model_comparison.csv')
    assert len(report)==108 and len(comparison)==36
    for r in report.itertuples():
        rows=p if r.Branch=='ALL' else p[p.Branch==r.Branch]
        capacity=rows.Transactions.to_numpy() if r.Model=='Oracle' else np.floor(rows[r.Model].to_numpy()+.5)
        shortage=np.maximum(rows.Transactions.to_numpy()-capacity,0)
        excess=np.maximum(capacity-rows.Transactions.to_numpy(),0)
        shortage_usd=sum(shortage*rows.Branch.map(gp).to_numpy()*r.ShortageFraction)
        waste_usd=sum(excess*rows.Branch.map(cost).to_numpy()*r.WasteFraction)
        assert np.isclose(shortage_usd,r.ShortageCostUSD)
        assert np.isclose(waste_usd,r.OverPreparationCostUSD)
        assert np.isclose(shortage_usd+waste_usd,r.TotalDecisionCostUSD)
    # Named column identity avoids positional dependence in tuple field renaming.
    np.testing.assert_allclose(comparison.NaiveMinusXGBoostUSD,comparison['Seasonal naive']-comparison.XGBoost)
    assert np.allclose(report[report.Model=='Oracle'].TotalDecisionCostUSD,0)
    # Fail closed on missing or duplicate June branch-days instead of dropping rows.
    transaction_days=x[['Branch','Date','Transaction ID']].drop_duplicates()
    with tempfile.TemporaryDirectory() as directory:
        for bad in [p.iloc[:-1],pd.concat([p.iloc[:-1],p.iloc[[0]]])]:
            path=Path(directory)/'bad.csv';bad.to_csv(path,index=False)
            try:load_forecasts(path,transaction_days)
            except ValueError:pass
            else:raise AssertionError('Invalid evaluation panel was accepted')
    n=nbformat.read(ROOT/'notebooks/04_forecast_business_value.ipynb',as_version=4);nbformat.validate(n)
    code=[c for c in n.cells if c.cell_type=='code']
    assert len(code)==8 and all(c.execution_count for c in code)
    assert not any(o.output_type=='error' for c in code for o in c.outputs)
    print('PASS: analytical penalty/oracle fixtures; all 108 independent cost reconstructions; aligned targets; 36 paired differences; missing/duplicate panel rejection; executed notebook; frozen source/forecasts/models.')

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--data',default='/Users/aya/Downloads/stories_transactions.csv');verify(p.parse_args().data)
