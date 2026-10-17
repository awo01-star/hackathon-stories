"""Step 8: cost sensitivities from frozen Step 7 forecasts; no model fitting."""
from pathlib import Path
import argparse
import hashlib
import itertools
import json
import os
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
# Fixed before scoring: fractions of pre-June recorded branch-level economics.
SHORTAGE_FRACTIONS = (0.25, 0.50, 1.00)
WASTE_FRACTIONS = (0.10, 0.25, 0.50)
MODELS = ('Seasonal naive', 'XGBoost', 'Oracle')
BRANCHES = ('Garden', 'Harbour', 'Uptown')


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def transaction_economics(path):
    raw = pd.read_csv(path)
    raw['Date'] = pd.to_datetime(raw['Date'])
    required = ['Transaction ID', 'Branch', 'Date', 'Line Gross Profit (USD)',
                'Line Revenue (USD)', 'Quantity', 'Unit Cost (USD)']
    if raw[required].isna().any().any():
        raise ValueError('Missing required transaction data')
    if (raw.groupby('Transaction ID')[['Branch', 'Date']].nunique() > 1).any().any():
        raise ValueError('Transaction ID reused across dates or branches')
    # Retain every recorded line, including identical lines of unresolved origin.
    raw['RecordedInputCostUSD'] = raw.Quantity * raw['Unit Cost (USD)']
    transactions = raw.groupby(['Branch', 'Date', 'Transaction ID'], as_index=False).agg(
        RecordedGPUSD=('Line Gross Profit (USD)', 'sum'),
        RecordedRevenueUSD=('Line Revenue (USD)', 'sum'),
        RecordedInputCostUSD=('RecordedInputCostUSD', 'sum'))
    if not np.isclose(transactions.RecordedGPUSD.sum(), raw['Line Gross Profit (USD)'].sum()):
        raise AssertionError('Recorded GP reconciliation failed')
    frames = []
    for label, subset in [('Jan-May calibration', transactions[transactions.Date < '2026-06-01']),
                          ('June descriptive', transactions[transactions.Date.between('2026-06-01','2026-06-30')]),
                          ('Jan-June descriptive', transactions)]:
        table = subset.groupby('Branch').agg(
            Transactions=('RecordedGPUSD', 'size'), RecordedGPUSD=('RecordedGPUSD', 'sum'),
            RecordedRevenueUSD=('RecordedRevenueUSD', 'sum'),
            RecordedInputCostUSD=('RecordedInputCostUSD', 'sum')).reset_index()
        table['Period'] = label
        for field, total in [('GPPerTransactionUSD','RecordedGPUSD'),
                             ('InputCostPerTransactionUSD','RecordedInputCostUSD')]:
            table[field] = table[total] / table.Transactions
        frames.append(table)
    economics = pd.concat(frames, ignore_index=True)
    if set(economics.Branch) != set(BRANCHES):
        raise ValueError('Expected the three Stories branches')
    return raw, transactions, economics


def load_forecasts(path, transactions):
    forecasts = pd.read_csv(path, parse_dates=['Date'])
    columns = ['Branch', 'Date', 'Transactions', 'Seasonal naive', 'XGBoost']
    forecasts = forecasts[columns].copy()
    expected = pd.MultiIndex.from_product([BRANCHES, pd.date_range('2026-06-01','2026-06-30')], names=['Branch','Date'])
    actual_index = pd.MultiIndex.from_frame(forecasts[['Branch','Date']])
    if forecasts.duplicated(['Branch','Date']).any() or set(actual_index) != set(expected):
        raise ValueError('Forecasts must contain exactly 90 matching June branch-days')
    values = forecasts[['Transactions','Seasonal naive','XGBoost']].to_numpy(float)
    if not np.isfinite(values).all() or (values < 0).any():
        raise ValueError('Non-finite or negative forecasts/targets')
    actual = transactions.groupby(['Branch','Date']).size().rename('ActualFromSource').reset_index()
    merged = forecasts.merge(actual, on=['Branch','Date'], how='left', validate='one_to_one')
    if not (merged.Transactions == merged.ActualFromSource).all():
        raise ValueError('Saved June targets do not match unique source transactions')
    return forecasts.sort_values(['Date','Branch']).reset_index(drop=True)


def decision_loss(actual, prepared, shortage_unit_cost, waste_unit_cost):
    shortage = np.maximum(np.asarray(actual) - np.asarray(prepared), 0)
    excess = np.maximum(np.asarray(prepared) - np.asarray(actual), 0)
    return shortage, excess, shortage * shortage_unit_cost, excess * waste_unit_cost


def evaluate(forecasts, economics, integer=True):
    calibration = economics[economics.Period == 'Jan-May calibration'].set_index('Branch')
    daily = []
    for shortage_fraction, waste_fraction in itertools.product(SHORTAGE_FRACTIONS, WASTE_FRACTIONS):
        scenario = f'S{shortage_fraction:g}_W{waste_fraction:g}'
        for model in MODELS:
            frame = forecasts[['Branch','Date','Transactions']].copy()
            prediction = frame.Transactions.to_numpy(float) if model == 'Oracle' else forecasts[model].to_numpy(float)
            capacity = np.floor(prediction + .5) if integer else prediction
            shortage_cost = shortage_fraction * frame.Branch.map(calibration.GPPerTransactionUSD).to_numpy()
            waste_cost = waste_fraction * frame.Branch.map(calibration.InputCostPerTransactionUSD).to_numpy()
            shortage, excess, under_usd, over_usd = decision_loss(frame.Transactions, capacity, shortage_cost, waste_cost)
            frame = frame.assign(Scenario=scenario, Model=model, ShortageFraction=shortage_fraction,
                WasteFraction=waste_fraction, PreparedTransactions=capacity, ShortageTransactions=shortage,
                ExcessTransactions=excess, ShortageUnitCostUSD=shortage_cost, WasteUnitCostUSD=waste_cost,
                ShortageCostUSD=under_usd, OverPreparationCostUSD=over_usd, TotalDecisionCostUSD=under_usd+over_usd)
            daily.append(frame)
    daily = pd.concat(daily, ignore_index=True)
    columns = ['Transactions','ShortageTransactions','ExcessTransactions','ShortageCostUSD','OverPreparationCostUSD','TotalDecisionCostUSD']
    keys = ['Scenario','ShortageFraction','WasteFraction','Model']
    branch = daily.groupby(keys+['Branch'],as_index=False)[columns].sum()
    branch['BranchDays'] = 30
    overall = daily.groupby(keys,as_index=False)[columns].sum().assign(Branch='ALL',BranchDays=90)
    summary = pd.concat([overall,branch],ignore_index=True)
    comparison = summary.pivot(index=['Branch','Scenario','ShortageFraction','WasteFraction'],columns='Model',values='TotalDecisionCostUSD').reset_index()
    comparison.columns.name = None
    comparison['XGBoostMinusNaiveUSD'] = comparison.XGBoost - comparison['Seasonal naive']
    comparison['NaiveMinusXGBoostUSD'] = -comparison.XGBoostMinusNaiveUSD
    comparison['XGBoostReductionFraction'] = comparison.NaiveMinusXGBoostUSD / comparison['Seasonal naive']
    comparison['Winner'] = np.where(np.isclose(comparison.XGBoost,comparison['Seasonal naive']),'Tie',
                                   np.where(comparison.XGBoost < comparison['Seasonal naive'],'XGBoost','Seasonal naive'))
    # Raw directional errors are invariant to scenario costs and explain reversals.
    directional = daily[daily.Scenario == daily.Scenario.iloc[0]].groupby(['Branch','Model'],as_index=False)[['ShortageTransactions','ExcessTransactions']].sum()
    return daily, summary, comparison, directional


def markdown_table(frame, money=()):
    frame = frame.copy()
    for col in money:
        frame[col] = frame[col].map(lambda x:f'${x:,.2f}')
    return '| ' + ' | '.join(frame.columns) + ' |\n|' + '|'.join(['---']*len(frame.columns)) + '|\n' + '\n'.join('| '+' | '.join(str(v) for v in row)+' |' for row in frame.itertuples(index=False,name=None))


def write_report(economics, comparison, summary, directional, output):
    all_rows = comparison[comparison.Branch == 'ALL'].sort_values(['ShortageFraction','WasteFraction'])
    display_columns = ['Scenario','Seasonal naive','XGBoost','Oracle','NaiveMinusXGBoostUSD','Winner']
    table = markdown_table(all_rows[display_columns],display_columns[1:5])
    wins = comparison.groupby(['Branch','Winner']).size().unstack(fill_value=0).reset_index()
    money = economics[economics.Period == 'Jan-May calibration'][['Branch','Transactions','RecordedGPUSD','GPPerTransactionUSD','InputCostPerTransactionUSD']]
    text = '''### Step 8 — Do better demand forecasts improve financial decisions?

Uses the **saved Step 7 June predictions**, with no retraining, prediction regeneration or cost-based model selection. Each model scores the same 90 branch-days (June 1–30, three branches). These remain rolling next-day forecasts after yesterday closes, not a single month-ahead forecast. June was already examined elsewhere in the project: these are exploratory internal comparisons.

#### Historical economics, separated from assumed costs

First sum recorded line gross profit within each unique transaction ID, verifying branch/date consistency, then divide total transaction GP by transaction count per branch. Recorded input cost is Quantity × recorded unit cost, also aggregated per transaction. All recorded rows are retained; identical-line origin is unresolved. No claim that these costs are avoidable cash costs is implied.

Jan–May values below price every June decision. Full six-month and June-only descriptive values are saved separately; June realized margins are not used to set penalty rates.

'''+markdown_table(money,['RecordedGPUSD','GPPerTransactionUSD','InputCostPerTransactionUSD'])+'''

#### Hypothetical operational policy and nine scenarios

Prepared capacity is **floor(max(forecast,0) + 0.5)** transaction-equivalents, the same nearest-integer policy for both models. This is an illustrative aggregate capacity proxy, not SKU inventory or staffing. A continuous-capacity sensitivity is also saved. No safety buffer or economically optimal quantile is selected from June.

- Shortage penalty: **25%, 50% or 100% of Jan–May branch GP/transaction** per unserved transaction-equivalent. This assumes that fraction of recorded gross margin is at risk; actual balking, queues, recapture and lifetime value are unobserved.
- Over-preparation penalty: **10%, 25% or 50% of Jan–May recorded branch input cost/transaction** per excess transaction-equivalent. This assumes that fraction is prepared, unsalvageable and avoidable; recipes, waste and salvage are unobserved. It is not measured waste.
- Evaluate all nine cross-products without choosing a preferred rate from the result. Shortage/excess quantities are identical across scenarios for a model; only their prices change.

`Shortage = max(actual − capacity, 0)`; `Excess = max(capacity − actual, 0)`.

`Decision cost = shortage × assumed shortage penalty + excess × assumed over-preparation penalty`.

The **oracle** sets capacity equal to observed demand, so both penalties equal zero by construction. It is an unattainable information benchmark, not a competing deployable model. Costs represent regret-like penalties, not total operating expenditure, accounting profit or actual savings. Do not subtract them from recorded GP and call the result measured profit.

#### Overall June results (USD)

Positive **NaiveMinusXGBoostUSD** means a lower assumed cost for XGBoost; negative means seasonal naive wins. Differences are computed before rounding.

'''+table+'\n\n#### Winners by branch across the nine assumptions\n\n'+markdown_table(wins)+'''

These scenario rows reuse the same errors and are not independent confirmations. Branch winners are descriptive: do not create and claim an out-of-sample branch-specific hybrid using June. Instead predefine a branch policy using earlier validation and verified operational costs, then compare prospectively on later dates.

#### Directional errors explain the cost differences

'''+markdown_table(directional)+'''

A lower pooled MAE can coexist with higher shortage or excess at one branch. Different penalties and branch GP/input costs reweight those directional errors. The saved branch comparison reports both cost components, not just a single score.

Transaction sales are used as a demand proxy; lost sales and actual capacity are unobserved. If historical sales were already constrained, even the oracle's observed-demand benchmark understates true demand. Product mix, transaction size, batch constraints, perishability, labor, fixed costs, model maintenance and service effects are omitted. A small assumed advantage could be outweighed by these costs. None of this validates wartime behavior or promotion effects.

**Business action:** inspect where under/over-forecasting occurs, verify shortage and salvage costs with operations, and run a shadow pilot using prospectively fixed capacity rules. Measure actual stockouts, waste, queues, service costs and GP. Retain a baseline where it wins; neither lower MAE nor simulated dollar differences justify universal deployment.

Files: `notebooks/04_forecast_business_value.ipynb`; `reports/forecast_business_value/historical_economics.csv`; `decision_costs.csv`; `model_comparison.csv`; `continuous_model_comparison.csv`; `scenario_unit_costs.csv`; `findings.json`; and `figures/forecast_business_value/decision_cost_difference.png`. Row-level hypothetical decisions stay in ignored `artifacts/forecast_business_value/`.

Reproduce without training: `python3 src/forecast_business_value.py --data /path/to/stories_transactions.csv`; `python3 src/build_forecast_business_value_notebook.py`. Original data, predictions and saved models are unchanged.
'''
    overall_wins = all_rows.Winner.value_counts().to_dict()
    integer_winner_note = f"**Observed outcome:** seasonal naive wins {overall_wins.get('Seasonal naive',0)} of 9 overall scenarios; XGBoost wins {overall_wins.get('XGBoost',0)}. This does not establish a universal financial improvement from the MAE winner.\n\n"
    for branch in BRANCHES:
        counts = comparison[comparison.Branch == branch].Winner.value_counts().to_dict()
        integer_winner_note += f"{branch}: {counts}. "
    integer_winner_note += '\n\n'
    harbour = directional[directional.Branch == 'Harbour'].set_index('Model')
    integer_winner_note += (f"With integer capacity, Harbour's shortage totals are {harbour.loc['Seasonal naive','ShortageTransactions']:.0f} transaction-equivalents under naive and {harbour.loc['XGBoost','ShortageTransactions']:.0f} under XGBoost; excess totals are {harbour.loc['Seasonal naive','ExcessTransactions']:.0f} and {harbour.loc['XGBoost','ExcessTransactions']:.0f}, respectively. Shortage-heavy assumptions price that tradeoff against XGBoost. ")
    integer_winner_note += f"Overall naive-minus-XGBoost differences range from ${all_rows.NaiveMinusXGBoostUSD.min():,.2f} to ${all_rows.NaiveMinusXGBoostUSD.max():,.2f}. These are total June differences, before implementation costs, not per-day savings.\n\n"
    continuous = pd.read_csv(output/'continuous_model_comparison.csv')
    paired = comparison.merge(continuous,on=['Branch','Scenario'],suffixes=('_integer','_continuous'),validate='one_to_one')
    changed = int((paired.Winner_integer != paired.Winner_continuous).sum())
    integer_winner_note += f"Continuous-capacity sensitivity changes the winner in {changed} of {len(paired)} branch/overall scenario comparisons.\n\n![Hypothetical cost differences](../../figures/forecast_business_value/decision_cost_difference.png)\n\n"
    text = text.replace('#### Winners by branch across the nine assumptions', integer_winner_note + '#### Winners by branch across the nine assumptions')
    (output/'REPORT.md').write_text(text)


def run(data_path, predictions_path=None):
    predictions_path = Path(predictions_path or ROOT/'artifacts/daily_demand_models/test_predictions.csv')
    output=ROOT/'reports/forecast_business_value'; output.mkdir(parents=True,exist_ok=True)
    art=ROOT/'artifacts/forecast_business_value';art.mkdir(parents=True,exist_ok=True)
    locked = [Path(data_path),predictions_path,*sorted((ROOT/'artifacts/daily_demand_models').glob('*.joblib')),
              ROOT/'reports/demand_forecasting/selection_lock.json']
    before={str(p):sha(p) for p in locked}
    raw, transactions, economics = transaction_economics(data_path)
    forecasts=load_forecasts(predictions_path,transactions)
    daily,summary,comparison,directional=evaluate(forecasts,economics)
    _,continuous_summary,continuous_comparison,_=evaluate(forecasts,economics,integer=False)
    economics.to_csv(output/'historical_economics.csv',index=False)
    summary.to_csv(output/'decision_costs.csv',index=False)
    comparison.to_csv(output/'model_comparison.csv',index=False)
    directional.to_csv(output/'directional_errors.csv',index=False)
    continuous_summary.to_csv(output/'continuous_decision_costs.csv',index=False)
    continuous_comparison.to_csv(output/'continuous_model_comparison.csv',index=False)
    daily[['Scenario','Branch','ShortageFraction','WasteFraction','ShortageUnitCostUSD','WasteUnitCostUSD']].drop_duplicates().to_csv(output/'scenario_unit_costs.csv',index=False)
    daily.to_csv(art/'daily_decisions.csv',index=False)
    os.environ.setdefault('MPLCONFIGDIR','/tmp/stories-matplotlib')
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    fig,axes=plt.subplots(2,2,figsize=(12,8),layout='constrained')
    bound=max(abs(comparison.NaiveMinusXGBoostUSD))
    for ax,branch in zip(axes.flat,['ALL',*BRANCHES]):
        matrix=comparison[comparison.Branch==branch].pivot(index='ShortageFraction',columns='WasteFraction',values='NaiveMinusXGBoostUSD').sort_index()
        ax.imshow(matrix,cmap='RdYlGn',vmin=-bound,vmax=bound,aspect='auto')
        ax.set_xticks(range(3),[f'{v:.0%}' for v in matrix.columns]);ax.set_yticks(range(3),[f'{v:.0%}' for v in matrix.index])
        for (i,j),value in np.ndenumerate(matrix.to_numpy()):ax.text(j,i,f'${value:+.2f}',ha='center',va='center')
        ax.set_title(branch);ax.set_xlabel('Excess penalty / historical input cost');ax.set_ylabel('Shortage penalty / historical GP')
    fig.suptitle('Hypothetical June cost: naive minus XGBoost (USD)\nPositive = XGBoost lower cost; negative = naive lower cost')
    figure=ROOT/'figures/forecast_business_value/decision_cost_difference.png';figure.parent.mkdir(parents=True,exist_ok=True)
    fig.savefig(figure,dpi=150);plt.close(fig)
    assert before=={str(p):sha(p) for p in locked},'Locked inputs changed'
    findings={'step':8,'noRetraining':True,'sourceSHA256':sha(data_path),'predictionSHA256':sha(predictions_path),
        'lockedInputHashes':{str(p.relative_to(ROOT)) if p.is_relative_to(ROOT) else p.name:sha(p) for p in locked},
        'branchDays':len(forecasts),'dates':['2026-06-01','2026-06-30'],'calibrationEnd':'2026-05-31',
        'shortageFractionsOfGP':SHORTAGE_FRACTIONS,'wasteFractionsOfRecordedInputCost':WASTE_FRACTIONS,
        'capacityRule':'nearest integer: floor(forecast + 0.5); continuous sensitivity also saved',
        'economics':economics.to_dict('records'),'comparisons':comparison.to_dict('records'),
        'wins':comparison.groupby(['Branch','Winner']).size().rename('scenarios').reset_index().to_dict('records'),
        'continuousWins':continuous_comparison.groupby(['Branch','Winner']).size().rename('scenarios').reset_index().to_dict('records'),
        'actualSavingsMeasured':False,'oracleCostZeroByConstruction':True}
    (output/'findings.json').write_text(json.dumps(findings,indent=2)+'\n')
    write_report(economics,comparison,summary,directional,output)
    print(comparison[comparison.Branch=='ALL'][['Scenario','Seasonal naive','XGBoost','NaiveMinusXGBoostUSD','Winner']].to_string(index=False))
    print('Wins:',findings['wins']);print('PASS: 90 aligned branch-days; locked inputs unchanged; no retraining.')
    return findings


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--data',default='/Users/aya/Downloads/stories_transactions.csv');parser.add_argument('--predictions',default=None)
    args=parser.parse_args();run(args.data,args.predictions)
