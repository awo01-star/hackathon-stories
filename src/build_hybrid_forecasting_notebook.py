"""Execute Step 9 accounting and displays; never fit or reload an ML model."""
from pathlib import Path
import nbformat as nbf
from IPython.core.interactiveshell import InteractiveShell
from IPython.utils.capture import capture_output
ROOT=Path(__file__).resolve().parents[1];cells=[]
def md(s):cells.append(nbf.v4.new_markdown_cell(s))
def code(s):cells.append(nbf.v4.new_code_cell(s))
md('''# Step 9 — Hybrid forecasting strategy

Evaluate three specified policies using **saved Step 7 June forecasts** and the **unchanged Step 8 financial assumptions**. No models are retrained.

**Methodological limit:** the hybrid (Harbour → naive; Garden/Uptown → XGBoost) was proposed after seeing June. Its June score is exploratory and cannot establish independent out-of-sample superiority or actual savings. No branch rule is optimized in this notebook.''')
code('''from pathlib import Path
import os, sys, json
import pandas as pd
import numpy as np
from IPython.display import display, Image, Markdown
ROOT=Path.cwd()
if not (ROOT/'src').exists(): ROOT=ROOT.parent
sys.path.insert(0,str(ROOT/'src'))
from hybrid_forecasting_strategy import run, POLICIES
from forecast_business_value import sha
DATA=Path(os.environ.get('STORIES_DATA','/Users/aya/Downloads/stories_transactions.csv'))
PREDICTIONS=ROOT/'artifacts/daily_demand_models/test_predictions.csv'
OUT=ROOT/'reports/hybrid_forecasting'
locked=[DATA,PREDICTIONS,*sorted((ROOT/'artifacts/daily_demand_models').glob('*')),
        *sorted(p for p in (ROOT/'reports/forecast_business_value').iterdir() if p.is_file()),
        ROOT/'reports/demand_forecasting/selection_lock.json']
before={str(p):sha(p) for p in locked}
display(pd.DataFrame(POLICIES).rename_axis('Branch'))
print('No model loading or fitting. No selection from validation or June in this run.')''')
md('''## 1. Frozen observations and hypothetical economics

Every policy scores June 1–30, three branches: **90 identical branch-days**. These are rolling next-day forecasts after yesterday closes, not one forecast of all June.

Capacity = `floor(forecast + 0.5)` transaction-equivalents. Shortage cost per missed transaction = 25%, 50%, or 100% of Jan–May branch GP/transaction. Excess cost per unused transaction-equivalent = 10%, 25%, or 50% of Jan–May recorded branch input cost/transaction. Score all nine cross-products.

`Total decision cost = shortage × assumed shortage penalty + excess × assumed excess penalty`.

Recorded GP and input costs are accounting inputs; these penalty fractions are assumptions. Lost sales, waste, salvage and service effects are not observed. The result is not net operating profit or actual cash saved.''')
code('''economics=pd.read_csv(ROOT/'reports/forecast_business_value/historical_economics.csv')
display(economics[economics.Period=='Jan-May calibration'].round(4))
unit_costs=pd.read_csv(ROOT/'reports/forecast_business_value/scenario_unit_costs.csv')
display(unit_costs.sort_values(['ShortageFraction','WasteFraction','Branch']).round(4))
predictions=pd.read_csv(PREDICTIONS,parse_dates=['Date'])
display(predictions.groupby('Branch').agg(BranchDays=('Date','size'),Transactions=('Transactions','sum')))
print('Saved forecasts:',len(predictions),'branch-days')''')
md('''## 2. Evaluate the three fixed policies

The runner checks source/prediction fingerprints, reconciles saved targets to original unique transactions, verifies historical economics and reproduces Step 8 cost components before combining branches. No tuning, safety buffers or branch search. Daily decisions stay in ignored `artifacts/hybrid_forecasting/`; aggregate evidence is saved in `reports/hybrid_forecasting/`.''')
code('''findings=run(DATA,PREDICTIONS)
costs=pd.read_csv(OUT/'decision_costs.csv')
comparison=pd.read_csv(OUT/'model_comparison.csv')
print('Independent validation:',findings['independentOutOfSampleValidation'])
print('Actual savings measured:',findings['actualSavingsMeasured'])''')
md('''## 3. Overall June costs, paired improvements and winner

Positive improvement means the hybrid has lower assumed cost. Compare to **both** uniform policies and to the stronger uniform policy in each scenario. That per-scenario stronger baseline is a descriptive June comparator, not an independently chosen deployment rule. All figures are totals for June; scenario rows are alternatives and must not be added together.''')
code('''overall=comparison[comparison.Branch=='ALL'].sort_values(['ShortageFraction','WasteFraction'])
display(overall.round(4))
display(costs[costs.Branch=='ALL'][['Scenario','Policy','ShortageCostUSD','OverPreparationCostUSD','TotalDecisionCostUSD']].round(2))
print('Hybrid strictly lower cost than both uniform policies in',findings['overallHybridWins'],'of 9 scenarios.')''')
md('''## 4. Branch-level costs and ties

Hybrid equals all-naive at Harbour. Hybrid equals all-XGBoost at Garden and Uptown. Report ties explicitly rather than crediting hybrid with an independent branch-level improvement.''')
code('''for branch in ['Garden','Harbour','Uptown']:
    display(Markdown('### '+branch))
    display(comparison[comparison.Branch==branch].sort_values(['ShortageFraction','WasteFraction']).round(4))
    display(costs[costs.Branch==branch][['Scenario','Policy','ShortageCostUSD','OverPreparationCostUSD','TotalDecisionCostUSD']].round(2))''')
md('''## 5. Comparison chart

Every bar uses the same observations, integer-capacity policy and scenario rates. The title retains the post-June selection warning.''')
code("display(Image(filename=str(ROOT/'figures/hybrid_forecasting/policy_cost_comparison.png')))")
md('''## 6. Interpretation: hindsight advantage is not validation

The mapping deliberately combines June's branch winners, and each branch's chosen model already won all nine Step 8 cost settings. Adding those selected costs mechanically favors the hybrid on these same observations. Nine scenarios reuse the same errors; they are not nine independent confirmations.

Evaluate whether the apparent advantage is large enough to pay for maintaining and monitoring a branch-specific policy. No model operating costs, real preparation batches, SKU mix, actual capacity, salvage, queues or recaptured demand are measured. Historical observed sales may already be constrained demand. None of these comparisons validates a response to war.''')
code('''print('Apparent June advantage vs all-naive USD:',findings['improvementVsNaiveRangeUSD'])
print('Apparent June advantage vs all-XGBoost USD:',findings['improvementVsXGBoostRangeUSD'])
print('Apparent June advantage vs stronger uniform baseline USD:',findings['improvementVsBestUniformRangeUSD'])
display(overall[['Scenario','StrongestUniformBaseline','HybridImprovementVsBestUniformUSD','HybridReductionVsBestUniformFraction']].round(4))
print('Potential implementation/monitoring cost and out-of-period policy instability are not priced.')''')
md('''## 7. Future experiment: choose the branch rule on validation only

1. Before opening a future test period, predefine the candidate models, capacity/rounding policy and operational penalty accounting. If several cost scenarios remain relevant, predefine how they are weighted or use a predeclared robust criterion; do not select the favorable scenario afterward.
2. Use earlier rolling validation predictions to choose the model per branch, with economics known before each validation forecast. For the original timeline, existing May predictions and **Jan–Apr** economics could support a branch-selection rule. Jan–May monetary averages would leak into a supposedly prospective May selection. Predeclare simple-model tie/weak-evidence fallback behavior.
3. Freeze the rule, and any permitted training/refit cutoff, before genuinely later unseen observations. June has already been examined: a new May selection now would not turn this project's June into independent validation. Obtain later data or a prospective shadow pilot.
4. Compare the locked policy against all-naive and all-XGBoost on matched future branch-days. Report paired uncertainty respecting temporal/shared-branch dependence and actual stockout/waste/service/implementation costs. Further tuning requires another test period.

This notebook does **not** select a new validation rule or claim a branch hybrid is proven superior. It supplies a transparent exploratory target for that future experiment.''')
code('''assert before=={str(p):sha(p) for p in locked}
assert len(costs)==108 and len(comparison)==36
for branch,expected in [('Harbour','AllNaiveCostUSD'),('Garden','AllXGBoostCostUSD'),('Uptown','AllXGBoostCostUSD')]:
    rows=comparison[comparison.Branch==branch]
    np.testing.assert_allclose(rows.HybridCostUSD,rows[expected])
print('PASS: source, saved models/predictions, selection lock and all Step 8 evidence unchanged.')
print('Outputs:',OUT)
print('Decision: prospectively test this hypothesis; no deployment or realized-savings claim.')''')
nb=nbf.v4.new_notebook(cells=cells,metadata={'kernelspec':{'name':'python3','display_name':'Python 3','language':'python'},'language_info':{'name':'python'}})
shell=InteractiveShell.instance();count=0
for cell in nb.cells:
    if cell.cell_type!='code':continue
    count+=1
    with capture_output() as cap:result=shell.run_cell(cell.source,store_history=False)
    if result.error_before_exec or result.error_in_exec:raise RuntimeError(f'Cell {count}: {result.error_before_exec or result.error_in_exec}')
    cell.execution_count=count;cell.outputs=[]
    if cap.stdout:cell.outputs.append(nbf.v4.new_output('stream',name='stdout',text=cap.stdout))
    if cap.stderr:cell.outputs.append(nbf.v4.new_output('stream',name='stderr',text=cap.stderr))
    for output in cap.outputs:cell.outputs.append(nbf.v4.new_output('display_data',data=output.data,metadata=output.metadata))
nbf.validate(nb);path=ROOT/'notebooks/05_hybrid_forecasting_strategy.ipynb';nbf.write(nb,path)
print(f'Executed {count} cells: {path}')
