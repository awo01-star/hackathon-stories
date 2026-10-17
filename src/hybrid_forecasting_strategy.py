"""Step 9: exploratory branch-policy accounting from frozen forecasts; no fitting."""
from pathlib import Path
import argparse
import json
import os
import numpy as np
import pandas as pd
from forecast_business_value import (ROOT, BRANCHES, SHORTAGE_FRACTIONS, WASTE_FRACTIONS,
    transaction_economics, load_forecasts, evaluate, sha, markdown_table)

POLICIES = {
    'A_AllNaive': {b:'Seasonal naive' for b in BRANCHES},
    'B_AllXGBoost': {b:'XGBoost' for b in BRANCHES},
    'C_Hybrid': {'Harbour':'Seasonal naive','Garden':'XGBoost','Uptown':'XGBoost'},
}


def combine_policies(step8_daily):
    """Apply the user-specified mapping, without optimizing it on these rows."""
    rows=[]
    for policy, mapping in POLICIES.items():
        selected=step8_daily[step8_daily.Model == step8_daily.Branch.map(mapping)].copy()
        selected=selected.rename(columns={'Model':'ForecastModel'}).assign(Policy=policy)
        if len(selected)!=810 or selected.duplicated(['Branch','Date','Scenario']).any():
            raise ValueError('Each policy must have the same 90 branch-days in all nine scenarios')
        rows.append(selected)
    daily=pd.concat(rows,ignore_index=True)
    keys=['Scenario','ShortageFraction','WasteFraction','Policy']
    amounts=['Transactions','PreparedTransactions','ShortageTransactions','ExcessTransactions',
             'ShortageCostUSD','OverPreparationCostUSD','TotalDecisionCostUSD']
    branch=daily.groupby(keys+['Branch'],as_index=False)[amounts].sum().assign(BranchDays=30)
    overall=daily.groupby(keys,as_index=False)[amounts].sum().assign(Branch='ALL',BranchDays=90)
    costs=pd.concat([overall,branch],ignore_index=True)
    comparison=costs.pivot(index=['Branch','Scenario','ShortageFraction','WasteFraction'],
        columns='Policy',values='TotalDecisionCostUSD').reset_index().rename(columns={
            'A_AllNaive':'AllNaiveCostUSD','B_AllXGBoost':'AllXGBoostCostUSD','C_Hybrid':'HybridCostUSD'})
    comparison.columns.name=None
    comparison['HybridImprovementVsNaiveUSD']=comparison.AllNaiveCostUSD-comparison.HybridCostUSD
    comparison['HybridImprovementVsXGBoostUSD']=comparison.AllXGBoostCostUSD-comparison.HybridCostUSD
    comparison['BestUniformCostUSD']=np.minimum(comparison.AllNaiveCostUSD,comparison.AllXGBoostCostUSD)
    comparison['HybridImprovementVsBestUniformUSD']=comparison.BestUniformCostUSD-comparison.HybridCostUSD
    comparison['HybridReductionVsBestUniformFraction']=comparison.HybridImprovementVsBestUniformUSD/comparison.BestUniformCostUSD
    def winners(r):
        values={'A_AllNaive':r.AllNaiveCostUSD,'B_AllXGBoost':r.AllXGBoostCostUSD,'C_Hybrid':r.HybridCostUSD}
        best=min(values.values())
        return ' + '.join(k for k,v in values.items() if abs(v-best)<1e-8)
    comparison['BestPolicy']=comparison.apply(winners,axis=1)
    comparison['StrongestUniformBaseline']=np.where(comparison.AllNaiveCostUSD<=comparison.AllXGBoostCostUSD,'A_AllNaive','B_AllXGBoost')
    return daily,costs,comparison


def write_report(costs,comparison,output):
    overall=comparison[comparison.Branch=='ALL'].sort_values(['ShortageFraction','WasteFraction'])
    cols=['Scenario','AllNaiveCostUSD','AllXGBoostCostUSD','HybridCostUSD',
          'HybridImprovementVsNaiveUSD','HybridImprovementVsXGBoostUSD','HybridImprovementVsBestUniformUSD']
    table=markdown_table(overall[cols],cols[1:])
    text='''### Step 9 — Exploratory hybrid forecasting strategy

**The hybrid was specified after examining June. Its June advantage is a hindsight result, not independent out-of-sample validation or proven savings.** No model is retrained and no branch rule is selected by this analysis. It evaluates the requested rule exactly.

- **A — All-naive:** Seasonal naive for every branch.
- **B — All-XGBoost:** XGBoost for every branch.
- **C — Hybrid:** Seasonal naive for Harbour; XGBoost for Garden and Uptown.

All three policies use the same frozen Step 7 predictions and the same **90 June branch-days**, with rolling next-day information. Step 8 economics and cost assumptions are unchanged. Prepare `floor(forecast + 0.5)` transaction-equivalents. Shortage penalties are **25%, 50% or 100% of Jan–May recorded branch GP/transaction**; excess penalties are **10%, 25% or 50% of Jan–May recorded branch input cost/transaction**. Score all nine cross-products, with no safety buffers or June-tuned capacity adjustments.

`Decision cost = max(actual − prepared,0) × shortage penalty + max(prepared − actual,0) × excess penalty`.

These are **hypothetical shortage/excess costs**, not measured waste, actual expenses, operating profit or realized savings. The source transactions, saved predictions, model files, selection lock and Step 8 evidence are unchanged.

#### Overall June costs and paired dollar differences

Positive improvement means the hybrid has lower assumed cost. All amounts below are total June USD, not per-day figures. Differences use unrounded values. A scenario ID such as `S0.25_W0.1` means 25% of historical GP for shortages and 10% of historical input cost for excess.

'''+table+'\n\n'
    wins=int((overall.HybridImprovementVsBestUniformUSD>1e-8).sum())
    text+=f"**Descriptive result:** the hybrid has the lowest assumed overall decision cost in **{wins}/9** scenarios. It improves on all-naive by **${overall.HybridImprovementVsNaiveUSD.min():,.2f}–${overall.HybridImprovementVsNaiveUSD.max():,.2f}**, on all-XGBoost by **${overall.HybridImprovementVsXGBoostUSD.min():,.2f}–${overall.HybridImprovementVsXGBoostUSD.max():,.2f}**, and on the stronger uniform policy in each scenario by **${overall.HybridImprovementVsBestUniformUSD.min():,.2f}–${overall.HybridImprovementVsBestUniformUSD.max():,.2f}**.\n\n"
    text+='''The stronger uniform policy is all-naive in eight scenarios and all-XGBoost in one. Choosing the lower-cost uniform policy from June is itself a descriptive comparison benchmark, not a validated deployment rule. The hybrid's branch mapping stays fixed across all nine scenarios.

![Policy costs across nine assumptions](../../figures/hybrid_forecasting/policy_cost_comparison.png)

#### Branch results and ties

'''
    for branch in BRANCHES:
        g=comparison[comparison.Branch==branch].sort_values(['ShortageFraction','WasteFraction'])
        text+=f'**{branch}**\n\n'+markdown_table(g[cols+['BestPolicy']],cols[1:])+'\n\n'
    text+='''At Harbour, hybrid and all-naive use exactly the same predictions and tie. At Garden and Uptown, hybrid and all-XGBoost tie. The hybrid combines the previously observed June branch winners. Because every branch's chosen model already won all nine Step 8 assumptions, its overall dominance here follows from adding those selected branch costs; it is not a new independent confirmation. The nine rows reuse the same forecast errors and are not nine independent experiments.

Cost components (shortage, excess and total) are saved for every policy/branch/scenario in `decision_costs.csv`. No oracle is added as a fourth evaluated policy; Step 8's perfect-information benchmark remains zero regret by construction and is not deployable.

#### How to choose the branch rule in a future experiment

1. **Before opening the next test period**, fix the capacity/rounding rule, eligible forecasting methods, branch-selection rule and actual shortage/excess cost accounting with operations. If several cost scenarios remain plausible, predeclare how they are combined (for example, fixed weights or worst-case regret); do not retrospectively choose the most favorable scenario.
2. Generate or use saved rolling validation forecasts from models fitted only on preceding data. For the original timeline, May could select branch policies using Jan–Apr economics and the existing May forecasts, with a predeclared fallback to naive when evidence is weak or tied. **Do not use Jan–May monetary averages to claim a prospective May selection.** This notebook does not perform that new selection or substitute it for the requested hybrid.
3. Lock each branch's model and every cost/policy choice using validation only. Refit permitted base models only through the validation cutoff in that future experiment, or keep them fixed if the protocol requires it. Then evaluate on genuinely later, unopened dates. Because June has already been inspected, selecting on May now cannot restore independent validation for this project; obtain later observations or run a prospective shadow pilot.
4. Compare the locked hybrid against all-naive and all-XGBoost on identical later branch-days. Report paired costs, branch results, uncertainty with temporal/branch dependence respected, stockouts, waste, service effects and model/operational overhead. If further retuning occurs, reserve another future period.

For live use, historical sales may censor true demand; transaction-equivalent capacity is not SKU inventory, recipe yield or staffing capacity. Recapture, perishability, salvage, labor and implementation costs are unobserved. Any incremental model/selection/monitoring cost can consume the small apparent benefit. Neither the branch mapping nor the hypothetical cost savings is proven stable over time or under disruption.

**Business implication:** this is a concrete hypothesis for a prospective branch-policy test, not a deployment recommendation. Retain simple models where they perform well, validate the economic penalties, and require net measured value before adding operational complexity. These ordinary-operation results cannot establish how a branch should respond during war; the existing crisis optimizer remains a separately labelled scenario tool.

Files: `notebooks/05_hybrid_forecasting_strategy.ipynb`; `reports/hybrid_forecasting/decision_costs.csv`; `model_comparison.csv`; `findings.json`; the comparison figure; and local row-level decisions in ignored `artifacts/hybrid_forecasting/`. Source input is never overwritten.

Reproduce without training: `python3 src/hybrid_forecasting_strategy.py --data /path/to/stories_transactions.csv`; `python3 src/build_hybrid_forecasting_notebook.py`; verify with `python3 src/verify_hybrid_forecasting.py`.
'''
    (output/'REPORT.md').write_text(text)


def run(data_path,predictions_path=None):
    predictions_path=Path(predictions_path or ROOT/'artifacts/daily_demand_models/test_predictions.csv')
    output=ROOT/'reports/hybrid_forecasting';output.mkdir(parents=True,exist_ok=True)
    artifacts=ROOT/'artifacts/hybrid_forecasting';artifacts.mkdir(parents=True,exist_ok=True)
    step8=ROOT/'reports/forecast_business_value'
    locked=[Path(data_path),predictions_path,*sorted((ROOT/'artifacts/daily_demand_models').glob('*')),
            *sorted(p for p in step8.iterdir() if p.is_file()),ROOT/'reports/demand_forecasting/selection_lock.json']
    before={str(p):sha(p) for p in locked}
    prior=json.loads((step8/'findings.json').read_text())
    if sha(data_path)!=prior['sourceSHA256'] or sha(predictions_path)!=prior['predictionSHA256']:
        raise ValueError('Inputs differ from frozen Step 8 inputs')
    if list(SHORTAGE_FRACTIONS)!=prior['shortageFractionsOfGP'] or list(WASTE_FRACTIONS)!=prior['wasteFractionsOfRecordedInputCost']:
        raise ValueError('Scenario assumptions differ from Step 8')
    _,transactions,economics=transaction_economics(data_path)
    saved_economics=pd.read_csv(step8/'historical_economics.csv')
    pd.testing.assert_frame_equal(economics,saved_economics,check_dtype=False)
    forecasts=load_forecasts(predictions_path,transactions)
    step8_daily,step8_costs,_,_=evaluate(forecasts,saved_economics)
    keys=['Scenario','Branch','Model']
    previous=pd.read_csv(step8/'decision_costs.csv').sort_values(keys).reset_index(drop=True)
    current=step8_costs.sort_values(keys).reset_index(drop=True)
    pd.testing.assert_frame_equal(current[previous.columns],previous,check_dtype=False)
    daily,costs,comparison=combine_policies(step8_daily)
    daily.to_csv(artifacts/'daily_decisions.csv',index=False)
    costs.to_csv(output/'decision_costs.csv',index=False)
    comparison.to_csv(output/'model_comparison.csv',index=False)
    os.environ.setdefault('MPLCONFIGDIR','/tmp/stories-matplotlib')
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    overall=comparison[comparison.Branch=='ALL'].sort_values(['ShortageFraction','WasteFraction'])
    fig,ax=plt.subplots(figsize=(13,6),layout='constrained');positions=np.arange(len(overall));width=.25
    for offset,column,label,color in [(-1,'AllNaiveCostUSD','A: All-naive','#686a58'),(0,'AllXGBoostCostUSD','B: All-XGBoost','#b55d3a'),(1,'HybridCostUSD','C: Hybrid (post-June rule)','#3b6570')]:
        ax.bar(positions+offset*width,overall[column],width,label=label,color=color)
    ax.set_xticks(positions,[f'S {r.ShortageFraction:.0%}\nW {r.WasteFraction:.0%}'for r in overall.itertuples()])
    ax.set_ylabel('Hypothetical total June decision cost (USD; lower is better)')
    ax.set_xlabel('S = fraction of Jan–May GP/transaction; W = fraction of Jan–May input cost/transaction')
    ax.set_title('Exploratory June comparison — hybrid chosen after seeing June\nSame 90 branch-days and Step 8 costs; not realized savings')
    ax.legend();ax.grid(axis='y',alpha=.2);ax.set_axisbelow(True)
    figure=ROOT/'figures/hybrid_forecasting/policy_cost_comparison.png';figure.parent.mkdir(parents=True,exist_ok=True)
    fig.savefig(figure,dpi=150);plt.close(fig)
    assert before=={str(p):sha(p) for p in locked},'Frozen inputs changed'
    f={'step':9,'exploratory':True,'independentOutOfSampleValidation':False,'actualSavingsMeasured':False,
       'selectionTiming':'Hybrid specified after examining June; hindsight comparison only.',
       'noRetraining':True,'policyMappings':POLICIES,'branchDays':90,'daysPerBranch':30,
       'dates':['2026-06-01','2026-06-30'],'economicsWindow':['2026-01-01','2026-05-31'],
       'shortageFractionsOfGP':SHORTAGE_FRACTIONS,'wasteFractionsOfRecordedInputCost':WASTE_FRACTIONS,
       'capacityRule':'floor(forecast + 0.5), same as Step 8',
       'lockedInputHashes':{str(p.relative_to(ROOT)) if p.is_relative_to(ROOT) else p.name:sha(p) for p in locked},
       'overallComparisons':overall.to_dict('records'),
       'overallHybridWins':int((overall.HybridImprovementVsBestUniformUSD>1e-8).sum()),
       'improvementVsNaiveRangeUSD':[float(overall.HybridImprovementVsNaiveUSD.min()),float(overall.HybridImprovementVsNaiveUSD.max())],
       'improvementVsXGBoostRangeUSD':[float(overall.HybridImprovementVsXGBoostUSD.min()),float(overall.HybridImprovementVsXGBoostUSD.max())],
       'improvementVsBestUniformRangeUSD':[float(overall.HybridImprovementVsBestUniformUSD.min()),float(overall.HybridImprovementVsBestUniformUSD.max())]}
    (output/'findings.json').write_text(json.dumps(f,indent=2)+'\n')
    write_report(costs,comparison,output)
    print(overall[['Scenario','AllNaiveCostUSD','AllXGBoostCostUSD','HybridCostUSD','HybridImprovementVsBestUniformUSD']].round(2).to_string(index=False))
    print('PASS: unchanged Step 8 assumptions/costs and frozen inputs; hybrid mapping fixed, not validated.')
    return f


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--data',default='/Users/aya/Downloads/stories_transactions.csv');parser.add_argument('--predictions',default=None)
    args=parser.parse_args();run(args.data,args.predictions)
