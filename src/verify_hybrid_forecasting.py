"""Analytical policy-mapping fixture and independent frozen-result reconciliation."""
from pathlib import Path
import argparse,json
import numpy as np
import pandas as pd
import nbformat
from hybrid_forecasting_strategy import combine_policies, POLICIES
from forecast_business_value import ROOT, sha


def verify(data_path):
    output=ROOT/'reports/hybrid_forecasting'
    findings=json.loads((output/'findings.json').read_text())
    assert findings['exploratory'] and not findings['independentOutOfSampleValidation']
    assert not findings['actualSavingsMeasured'] and findings['noRetraining']
    for name,digest in findings['lockedInputHashes'].items():
        path=Path(data_path) if name==Path(data_path).name else ROOT/name
        assert sha(path)==digest,name
    # Hand-calculated 30-day fixture: A=(7+1+6)*30=420,
    # B=(2+5+3)*30=300; C=(2+1+3)*30=180 in every scenario.
    rows=[]
    for sf in [.25,.5,1.]:
        for wf in [.1,.25,.5]:
            for branch,naive,xgb in [('Garden',7,2),('Harbour',1,5),('Uptown',6,3)]:
                for model,loss in [('Seasonal naive',naive),('XGBoost',xgb)]:
                    for date in pd.date_range('2026-06-01','2026-06-30'):
                        rows.append(dict(Branch=branch,Date=date,Model=model,Scenario=f'S{sf:g}_W{wf:g}',
                            ShortageFraction=sf,WasteFraction=wf,Transactions=10,PreparedTransactions=8,
                            ShortageTransactions=2,ExcessTransactions=0,ShortageCostUSD=loss,
                            OverPreparationCostUSD=0,TotalDecisionCostUSD=loss))
    fixture=pd.DataFrame(rows);_,_,check=combine_policies(fixture)
    all_rows=check[check.Branch=='ALL']
    np.testing.assert_allclose(all_rows.AllNaiveCostUSD,420)
    np.testing.assert_allclose(all_rows.AllXGBoostCostUSD,300)
    np.testing.assert_allclose(all_rows.HybridCostUSD,180)
    np.testing.assert_allclose(all_rows.HybridImprovementVsNaiveUSD,240)
    np.testing.assert_allclose(all_rows.HybridImprovementVsXGBoostUSD,120)
    for bad in [fixture.iloc[1:],pd.concat([fixture,fixture.iloc[[0]]])]:
        try:combine_policies(bad)
        except ValueError:pass
        else:raise AssertionError('Missing or duplicated selected observations accepted')
    # Independently assemble each real branch/policy cost from Step 8 records.
    step8=pd.read_csv(ROOT/'reports/forecast_business_value/decision_costs.csv')
    step9=pd.read_csv(output/'decision_costs.csv')
    comparison=pd.read_csv(output/'model_comparison.csv')
    assert len(step9)==108 and len(comparison)==36
    components=['ShortageCostUSD','OverPreparationCostUSD','TotalDecisionCostUSD']
    for row in step9.to_dict('records'):
        candidates=step8[(step8.Scenario==row['Scenario'])&(step8.Branch!='ALL')]
        if row['Branch']!='ALL':candidates=candidates[candidates.Branch==row['Branch']]
        selected=candidates[candidates.Model==candidates.Branch.map(POLICIES[row['Policy']])]
        assert len(selected)==(3 if row['Branch']=='ALL' else 1)
        for field in components:assert np.isclose(row[field],selected[field].sum())
        assert np.isclose(row['TotalDecisionCostUSD'],row['ShortageCostUSD']+row['OverPreparationCostUSD'])
    for row in comparison.to_dict('records'):
        for policy,col in [('A_AllNaive','AllNaiveCostUSD'),('B_AllXGBoost','AllXGBoostCostUSD'),('C_Hybrid','HybridCostUSD')]:
            match=step9[(step9.Scenario==row['Scenario'])&(step9.Branch==row['Branch'])&(step9.Policy==policy)]
            assert len(match)==1 and np.isclose(row[col],match.TotalDecisionCostUSD.iloc[0])
        assert np.isclose(row['HybridImprovementVsNaiveUSD'],row['AllNaiveCostUSD']-row['HybridCostUSD'])
        assert np.isclose(row['HybridImprovementVsXGBoostUSD'],row['AllXGBoostCostUSD']-row['HybridCostUSD'])
        assert np.isclose(row['HybridImprovementVsBestUniformUSD'],min(row['AllNaiveCostUSD'],row['AllXGBoostCostUSD'])-row['HybridCostUSD'])
    assert (comparison[comparison.Branch=='Harbour'].BestPolicy=='A_AllNaive + C_Hybrid').all()
    assert (comparison[comparison.Branch.isin(['Garden','Uptown'])].BestPolicy=='B_AllXGBoost + C_Hybrid').all()
    # Independently reconcile row-level hybrid decisions to frozen source forecasts.
    daily=pd.read_csv(ROOT/'artifacts/hybrid_forecasting/daily_decisions.csv',parse_dates=['Date'])
    forecasts=pd.read_csv(ROOT/'artifacts/daily_demand_models/test_predictions.csv',parse_dates=['Date'])
    assert len(daily)==2430
    for policy,mapping in POLICIES.items():
        for branch,model in mapping.items():
            selected=daily[(daily.Policy==policy)&(daily.Branch==branch)]
            expected=forecasts[forecasts.Branch==branch][['Date',model]]
            merged=selected.merge(expected,on='Date',validate='many_to_one')
            assert len(merged)==270
            np.testing.assert_allclose(merged.PreparedTransactions,np.floor(merged[model]+.5))
    nb=nbformat.read(ROOT/'notebooks/05_hybrid_forecasting_strategy.ipynb',as_version=4);nbformat.validate(nb)
    cells=[c for c in nb.cells if c.cell_type=='code'];assert len(cells)==8 and all(c.execution_count for c in cells)
    assert not any(o.output_type=='error' for c in cells for o in c.outputs)
    print('PASS: analytical branch-mapping fixture; 108 Step 8 cost reconciliations; 36 paired comparisons; branch ties; all daily capacity mappings; invalid panel rejection; executed notebook; unchanged data/models/forecasts/Step 8 evidence.')


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--data',default='/Users/aya/Downloads/stories_transactions.csv');verify(parser.parse_args().data)
