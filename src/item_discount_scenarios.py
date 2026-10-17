"""Existing product forecasts plus transparent discount arithmetic; no retraining."""
from pathlib import Path
import argparse,hashlib,json,os
import numpy as np
import pandas as pd
R=Path(__file__).resolve().parents[1]

def run(data_path):
 source=Path(data_path);forecast=R/'artifacts/next_day_forecast.csv';before={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in [source,forecast]}
 x=pd.read_csv(source,parse_dates=['Date']);f=pd.read_csv(forecast);out=R/'reports/item_discount_scenarios';out.mkdir(exist_ok=True)
 x['RecordedCostUSD']=x.Quantity*x['Unit Cost (USD)']
 h=x.groupby(['Branch','Product'],as_index=False).agg(HistoricalUnits=('Quantity','sum'),HistoricalRevenueUSD=('Line Revenue (USD)','sum'),HistoricalGPUSD=('Line Gross Profit (USD)','sum'),HistoricalRecordedCostUSD=('RecordedCostUSD','sum'),HistoricalTransactionCount=('Transaction ID','nunique'))
 h['HistoricalGPPerUnitUSD']=h.HistoricalGPUSD/h.HistoricalUnits;h['HistoricalUnitsPerCalendarDay']=h.HistoricalUnits/x.Date.nunique()
 a=f.merge(h,on=['Branch','Product'],validate='one_to_one');assert len(a)==135
 a['NoDiscountUnitGPUSD']=a.price-a.cost;a['ForecastNoDiscountGPUSD']=a.forecast_units*a.NoDiscountUnitGPUSD
 # Descriptive history is separate from the full-list-price forecast reference.
 h.to_csv(out/'historical_product_economics.csv',index=False)
 a.to_csv(out/'forecast_reference.csv',index=False)
 rows=[]
 for r in a.itertuples():
  for d in [0,.05,.10,.15,.20,.30]:
   m=r.price*(1-d)-r.cost;required=r.ForecastNoDiscountGPUSD/m if m>0 else np.nan
   for u in [0,.05,.10,.20,.30,.50]:
    q=r.forecast_units*(1+u);gp=q*m
    rows.append(dict(Branch=r.Branch,Product=r.Product,PlanningDate=r.date,DiscountFraction=d,AssumedUnitLift=u,
      BaselineForecastUnits=r.forecast_units,NoDiscountReferenceGPUSD=r.ForecastNoDiscountGPUSD,
      DiscountedUnitGPUSD=m,ScenarioUnits=q,ScenarioGPUSD=gp,GPChangeUSD=gp-r.ForecastNoDiscountGPUSD,
      RequiredUnitsToPreserveGP=required,RequiredExtraUnits=required-r.forecast_units if m>0 else np.nan,
      MinimumWholeUnitsToPreserveGP=int(np.ceil(required-1e-10)) if m>0 else np.nan,
      RequiredUnitLift=required/r.forecast_units-1 if m>0 else np.nan,
      MaxDiscountAtAssumedLift=(r.price-r.cost)/r.price*u/(1+u),
      PreservesReferenceGP=bool(gp>=r.ForecastNoDiscountGPUSD-1e-8),PositiveUnitGP=bool(m>0)))
 t=pd.DataFrame(rows);assert np.allclose(t.ScenarioGPUSD-t.NoDiscountReferenceGPUSD,t.GPChangeUSD)
 assert (t[(t.DiscountFraction>0)&(t.AssumedUnitLift==0)].GPChangeUSD<0).all()
 b=t[t.DiscountedUnitGPUSD>0];assert np.allclose(b.RequiredUnitsToPreserveGP*b.DiscountedUnitGPUSD,b.NoDiscountReferenceGPUSD)
 t.to_csv(out/'discount_scenarios.csv',index=False)
 examples=t[(t.DiscountFraction==.1)&(t.AssumedUnitLift==.2)&t.Product.isin(['Iced Latte','Chicken Pesto Sandwich'])].sort_values(['Product','Branch'])
 def money(v):return f'${v:.2f}'
 lines=['| Branch | Product | Forecast units | Reference GP | GP at 10% off / assumed +20% units | GP change | Required unit lift to preserve reference |','|---|---|---:|---:|---:|---:|---:|']
 for z in examples.itertuples():lines.append(f'| {z.Branch} | {z.Product} | {z.BaselineForecastUnits:.2f} | {money(z.NoDiscountReferenceGPUSD)} | {money(z.ScenarioGPUSD)} | {money(z.GPChangeUSD)} | {z.RequiredUnitLift:.1%} |')
 text='''# Item forecasts, discounts and gross-profit preservation

## Purpose and status

Use the **existing** product-demand forecast to ask how much extra volume a proposed discount would need to preserve gross profit. No demand model is trained, discount response inferred, or location-to-dataset mapping invented. The forecast date is **July 1, 2026**, from records through June 30: a historical demonstration, **not a current live forecast**. A forecast estimates baseline sales; it does not predict the causal response to a new offer.

Historical quantities, revenue and recorded GP are observed aggregates. `historical_product_economics.csv` reports all 135 branch/product combinations, including unit counts, transaction counts and GP/unit. These retain all source lines. Historical transaction counts are per product and must not be summed as unique branch visits.

`forecast_reference.csv` lists each saved forecast and full-list-price reference GP. `discount_scenarios.csv` evaluates 6 discount rates (0/5/10/15/20/30%) × 6 explicitly assumed unit lifts (0/5/10/20/30/50%) for every branch/product. No scenario is an estimated take-up rate or measured profit gain. Values are USD; price changes use continuous arithmetic, without POS cent rounding.

## Reference and formulas

For list price P, recorded unit cost C and saved expected units Q:

- Reference GP: `G0 = Q × (P − C)`. This is a **no-discount full-list-price benchmark**, not measured future profit or a forecast of the current discount policy. Historical realized GP/unit is provided separately and not silently substituted into this benchmark.
- With discount d and an assumed unit lift u: `G1 = Q × (1+u) × [P × (1−d) − C]`.
- Conditional difference: `G1 − G0`.
- Required units to preserve reference: `Qrequired = G0 / [P × (1−d) − C]`, only if discounted unit GP is positive. Also report extra units, minimum whole units and required percentage lift. If unit GP is nonpositive, no finite nonnegative volume can preserve positive reference GP.
- Maximum discount at an assumed lift: `dmax = [(P−C)/P] × u/(1+u)`. This is the limit for GP preservation under the assumptions, **not** the much looser discount limit for merely positive unit margin.

At zero incremental volume, every positive discount in this grid reduces reference GP. Positive unit margin alone does not preserve total profit. Rows marked `PreservesReferenceGP` satisfy the accounting condition **only under the assumed volume**, not a guaranteed profit floor. Required extra sales may be impossible; no elasticity or conversion curve exists here.

## Illustrative 10%-discount scenarios

The +20% quantity lift below is **assumed**, not predicted:

'''+ '\n'.join(lines)+'''

Use the complete CSV to examine any item. Do not add overlapping alternative scenarios. If discounting only incremental purchases rather than existing demand, use a separately specified eligibility/cannibalization model; these calculations apply the discount to **all units of the selected product in the modeled period**. No automatic substitution or add-on response is assumed.

## Location-aware suggestions: a policy prototype, not a trained response model

The separate [location research](../root_cause/LOCATION_RESEARCH_AND_SAFE_SOLUTION.md) verifies public context for Bliss Street/AUB and LeMall Dbayeh but does not map either to Garden, Harbour or Uptown. No anonymized product forecast or cost is assigned to those public places. A university context can suggest a study/pre-order hypothesis; a mall context can suggest a staff/pickup hypothesis. Neither establishes actual customer identities, useful offer timing or incremental demand.

A defensible future system would combine verified branch coordinates, dated nearby institutions, a branch crosswalk, baseline product forecasts, actual recipes/costs/capacity, and randomized offer exposure/response data. Until response labels exist, use a transparent human-reviewed context rule and a break-even filter. Do not call that a trained geographical targeting or uplift model. With only three independent branches, a rich location model would risk memorizing branch identity.

## Practical action and limits

First check costs and capacity. Choose a narrow non-overlapping eligible population before purchase, randomize an offer against the existing policy, and measure total GP per assigned opportunity including nonbuyers, campaign cost and cannibalization. Prefer not to subsidize already likely purchases without evidence. Require measured net value before rollout.

This arithmetic assumes every modeled unit is sold and costed at the recorded unit cost, stable mix/prices, and no incremental labor, implementation, preparation waste, stockouts, capacity limits or future demand uncertainty. These omissions can reverse the sign of a small apparent gain. Recorded Garden costs may include allocations; GP is not cash profit after overhead. Forecast error means even a mathematically preserving scenario can fail in practice. No pricing, offers, inventory or orders are activated.

Reproduce without training: `python3 src/item_discount_scenarios.py --data /path/to/stories_transactions.csv`. Inspection notebook: `notebooks/09_item_discount_business_value.ipynb`. Original input and saved forecast remain unchanged. No hypothetical amount in this report is realized savings or validated wartime performance.
'''
 (out/'REPORT.md').write_text(text)
 assert before=={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in [source,forecast]}
 (out/'audit.json').write_text(json.dumps({'sourceSHA256':before[str(source)],'forecastSHA256':before[str(forecast)],'rows':len(t),'branchProducts':len(a),'planningDate':str(f.date.iloc[0]),'noRetraining':True,'assumedUpliftNotEstimated':True,'reference':'full-list-price, no-discount GP','originalInputsUnchanged':True},indent=2))
 print(examples[['Branch','Product','GPChangeUSD','RequiredUnitLift']].to_string(index=False));print('PASS: historical aggregates, 135 forecasts, 4860 scenario identities and break-even equality; inputs unchanged.')
 return out

if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--data',default='/Users/aya/Downloads/stories_transactions.csv');run(p.parse_args().data)
