"""Build and execute Step 8 from frozen forecasts, never loading/fitting a model."""
from pathlib import Path
import nbformat as nbf
from IPython.core.interactiveshell import InteractiveShell
from IPython.utils.capture import capture_output
ROOT=Path(__file__).resolve().parents[1]
cells=[]
def md(text):cells.append(nbf.v4.new_markdown_cell(text))
def code(text):cells.append(nbf.v4.new_code_cell(text))
md('''# Step 8 — Forecast business value

**Do XGBoost's improved June transaction forecasts yield better hypothetical preparation decisions than seasonal naive?** Use the existing Step 7 predictions and original recorded line gross profit. No ML model is retrained or regenerated. The oracle knows observed demand and represents an unattainable benchmark.

These are **assumption-dependent decision costs, not actual savings**. June has already been examined in earlier project work, so comparisons are exploratory internal holdouts. This notebook is separate from `04_profit_lab.ipynb` and does not replace it.''')
code('''from pathlib import Path
import sys, os, json, hashlib
import numpy as np
import pandas as pd
from IPython.display import display, Image, Markdown
ROOT=Path.cwd()
if not (ROOT/'src').exists(): ROOT=ROOT.parent
sys.path.insert(0,str(ROOT/'src'))
from forecast_business_value import (run, transaction_economics, load_forecasts, evaluate,
    decision_loss, SHORTAGE_FRACTIONS, WASTE_FRACTIONS, sha)
DATA=Path(os.environ.get('STORIES_DATA','/Users/aya/Downloads/stories_transactions.csv'))
PREDICTIONS=ROOT/'artifacts/daily_demand_models/test_predictions.csv'
OUT=ROOT/'reports/forecast_business_value'
locked=[DATA,PREDICTIONS,*sorted((ROOT/'artifacts/daily_demand_models').glob('*.joblib')),
        ROOT/'reports/demand_forecasting/selection_lock.json']
before={str(p):sha(p) for p in locked}
print('Frozen June forecasts:',PREDICTIONS)
print('Source SHA256:',sha(DATA))
print('Shortage fractions of Jan-May GP/transaction:',SHORTAGE_FRACTIONS)
print('Excess fractions of Jan-May recorded input cost/transaction:',WASTE_FRACTIONS)''')
md('''## 1. Historical gross profit per unique transaction

Sum **recorded line gross profit** within transaction ID (after confirming an ID identifies one branch/date), then average transaction totals by branch. Do not average line margins or multiply GP by quantity twice. Retain all recorded rows, consistent with the Step 7 targets; identical line entries have unresolved provenance.

Show Jan–June descriptively, but **use only Jan–May branch economics to set June penalty rates**. June-only economics are a descriptive check, not a pricing input. Recorded input cost = quantity × recorded unit cost; it is not demonstrated avoidable waste.''')
code('''raw,transactions,economics=transaction_economics(DATA)
display(economics[economics.Period=='Jan-June descriptive'].round(4))
display(economics[economics.Period=='Jan-May calibration'].round(4))
display(economics[economics.Period=='June descriptive'].round(4))
print('Recorded line GP total:',round(raw['Line Gross Profit (USD)'].sum(),2))
print('Grouped transaction GP total:',round(transactions.RecordedGPUSD.sum(),2))
assert np.isclose(raw['Line Gross Profit (USD)'].sum(),transactions.RecordedGPUSD.sum())''')
md('''## 2. Lock the same 90 June branch-days

Use the saved Seasonal naive and XGBoost columns, not refitted or reconstructed predictions. Check all 30 dates × three branches and reconcile targets to source unique transactions. Forecasts were issued after the previous day closed; this is not a month-ahead forecast.''')
code('''forecasts=load_forecasts(PREDICTIONS,transactions)
display(forecasts.head(15))
display(forecasts.groupby('Branch').agg(Days=('Date','size'),ActualTransactions=('Transactions','sum')))
print('Total branch-days:',len(forecasts))
for model in ['Seasonal naive','XGBoost']:
    print(model,'saved continuous forecast MAE:',np.mean(abs(forecasts[model]-forecasts.Transactions)))''')
md('''## 3. Define the policy and nine hypothetical cost combinations

Prepare nearest-integer **transaction-equivalent capacity**: `floor(forecast + 0.5)`. This is a proxy, not a SKU preparation plan. Apply the same policy to both models without safety buffers or a June-tuned quantile. Oracle capacity equals actual observed demand.

For each branch, shortage costs are 25%, 50%, or 100% of historical Jan–May GP/transaction. Excess costs are 10%, 25%, or 50% of historical Jan–May recorded input cost/transaction. Evaluate all nine cross-products. These fractions are assumed, not estimated lost-sale or waste rates.

`shortage = max(actual − prepared, 0)`; `excess = max(prepared − actual, 0)`.

`total decision cost = shortage × shortage unit penalty + excess × excess unit penalty`.

No goodwill, fixed operating or model maintenance costs are included; do not interpret these penalty totals as operating profit or actual cash spending.''')
code('''findings=run(DATA,PREDICTIONS)
unit_costs=pd.read_csv(OUT/'scenario_unit_costs.csv')
display(unit_costs.sort_values(['ShortageFraction','WasteFraction','Branch']).round(4))
print('Penalty rates are fixed across June; no test-period margin calibration.')''')
md('''## 4. Overall decision costs and dollar differences

Positive **NaiveMinusXGBoostUSD** means XGBoost has lower assumed cost. These are paired comparisons on the same dates. Oracle cost is zero by construction and excludes perfect-information acquisition cost.''')
code('''summary=pd.read_csv(OUT/'decision_costs.csv')
comparison=pd.read_csv(OUT/'model_comparison.csv')
display(summary[summary.Branch=='ALL'][['Scenario','Model','ShortageCostUSD','OverPreparationCostUSD','TotalDecisionCostUSD']].round(2))
display(comparison[comparison.Branch=='ALL'].sort_values(['ShortageFraction','WasteFraction']).round(4))''')
md('''## 5. Branch-level results

A global MAE advantage can hide directional errors at one branch. Show both shortage and over-preparation components plus the paired cost difference for every branch and assumption. Do not choose a new branch-specific policy from June and call it independently validated.''')
code('''for branch in ['Garden','Harbour','Uptown']:
    display(Markdown('### '+branch))
    display(comparison[comparison.Branch==branch].sort_values(['ShortageFraction','WasteFraction']).round(4))
    display(summary[summary.Branch==branch][['Scenario','Model','ShortageCostUSD','OverPreparationCostUSD','TotalDecisionCostUSD']].round(2))
display(pd.DataFrame(findings['wins']))''')
md('''## 6. Explain directional errors; check rounding sensitivity

The rounding policy makes capacity operationally integral but slightly changes the loss relative to Step 7's continuous MAE. Repeat the same costs with continuous forecasts without selecting whichever presentation looks better. Cost assumptions rescale the same error quantities; nine wins are not nine independent experiments.''')
code('''display(pd.read_csv(OUT/'directional_errors.csv'))
continuous=pd.read_csv(OUT/'continuous_model_comparison.csv')
display(continuous[continuous.Branch=='ALL'].round(4))
joined=comparison.merge(continuous,on=['Branch','Scenario'],suffixes=('_integer','_continuous'),validate='one_to_one')
print('Rounding changes winner in',int((joined.Winner_integer!=joined.Winner_continuous).sum()),'of',len(joined),'branch/overall scenario comparisons.')
display(Image(filename=str(ROOT/'figures/forecast_business_value/decision_cost_difference.png')))''')
md('''## 7. Business interpretation, assumptions and limits

Historical transactions proxy demand; unobserved stockouts may censor it. Recorded gross margin is not contribution after labor and overhead. Aggregate transactions do not reveal SKU requirements, recipe yield, perishability or capacity. The shortage fraction assumes some at-risk sales are lost; the excess fraction assumes some prepared cost is avoidable and unsalvageable. None is observed here.

Use branch differences to form a **prospective hypothesis**, not a new test-selected deployment rule. Verify operational penalties, predefine buffers and any branch-specific selection on earlier data, then shadow-test on later dates. Measure actual stockouts, waste, service and implementation costs. The oracle's zero regret does not mean zero operating cost. No war-response accuracy, causal profit uplift or actual savings is established.''')
code('''all_rows=comparison[comparison.Branch=='ALL']
print('Overall scenario winners:',all_rows.Winner.value_counts().to_dict())
print('XGBoost lower assumed June cost in every scenario:',bool((all_rows.NaiveMinusXGBoostUSD>0).all()))
for branch in ['Garden','Harbour','Uptown']:
    rows=comparison[comparison.Branch==branch]
    print(branch,'winners:',rows.Winner.value_counts().to_dict(),
          'naive-minus-XGBoost range USD:',round(rows.NaiveMinusXGBoostUSD.min(),2),round(rows.NaiveMinusXGBoostUSD.max(),2))
assert before=={str(p):sha(p) for p in locked}
assert np.allclose(summary.loc[summary.Model=='Oracle','TotalDecisionCostUSD'],0)
print('PASS: source, saved forecasts, selection lock and saved models unchanged; no retraining.')
print('Outputs:',OUT)
print('All dollar differences are hypothetical decision-cost comparisons, not actual savings.')''')
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
nbf.validate(nb);path=ROOT/'notebooks/04_forecast_business_value.ipynb';nbf.write(nb,path)
print(f'Executed {count} cells: {path}')
