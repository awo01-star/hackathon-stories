"""Read-only accounting investigation of the existing 153-line Garden flag."""
from pathlib import Path
import argparse,hashlib,json
import numpy as np
import pandas as pd

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'reports/profit_lab'
DAYS=['Monday','Tuesday','Wednesday','Thursday','Friday','Saturday','Sunday']


def table(frame,money=(),percent=(),decimals=()):
    frame=frame.copy()
    for c in money:frame[c]=frame[c].map(lambda v:f'-${abs(v):,.2f}' if v<0 else f'${v:,.2f}')
    for c in percent:frame[c]=frame[c].map(lambda v:f'{v:.2%}')
    for c in decimals:frame[c]=frame[c].map(lambda v:f'{v:.4f}')
    return '| '+' | '.join(frame.columns)+' |\n|'+'|'.join(['---']*len(frame.columns))+'|\n'+'\n'.join('| '+' | '.join(str(v) for v in row)+' |'for row in frame.itertuples(index=False,name=None))


def aggregate(rows,keys):
    return rows.groupby(keys,as_index=False).agg(Lines=('Product','size'),Units=('Quantity','sum'),
        RevenueUSD=('Line Revenue (USD)','sum'),GPUSD=('Line Gross Profit (USD)','sum'),
        DiscountUSD=('DiscountUSD','sum'))


def run(path):
    path=Path(path);before=hashlib.sha256(path.read_bytes()).hexdigest()
    prior=json.loads((OUT/'findings.json').read_text())
    assert before==prior['sourceSHA256'],'Source differs from reviewed source'
    x=pd.read_csv(path);original_columns=list(x.columns)
    x['Date']=pd.to_datetime(x.Date);x['Hour']=x.Time.str[:2].astype(int)
    x['DiscountUSD']=x.Quantity*x['Unit Price (USD)']-x['Line Revenue (USD)']
    x['Margin']=x['Line Gross Profit (USD)']/x['Line Revenue (USD)']
    g=x[x.Branch=='Garden'].copy()
    f=g[(g['Discount Rate']>0)&(g.Margin<.30)].copy()
    assert len(f)==prior['modules']['discount']['lowMarginDiscountedLines']==153
    assert np.isclose(f.DiscountUSD.sum(),prior['modules']['discount']['lowMarginDiscountUSD'])
    products=sorted(f.Product.unique());eligible=g[g.Product.isin(products)].copy()
    full=eligible[eligible['Discount Rate']==0]
    assert (f['Discount Rate']==.1).all()
    assert len(eligible[eligible['Discount Rate']>0])==len(f)
    assert (eligible.groupby('Product')[['Unit Price (USD)','Unit Cost (USD)']].nunique()==1).all().all()
    assert not f.duplicated(subset=original_columns).any()
    # Both observed GP and list-price sensitivity reconcile to recorded unit costs.
    assert np.allclose(f['Line Gross Profit (USD)'],f['Line Revenue (USD)']-f.Quantity*f['Unit Cost (USD)'])
    Q=int(f.Quantity.sum());R=float(f['Line Revenue (USD)'].sum());G=float(f['Line Gross Profit (USD)'].sum());D=float(f.DiscountUSD.sum())
    list_gp=float((f.Quantity*(f['Unit Price (USD)']-f['Unit Cost (USD)'])).sum())
    assert np.isclose(list_gp,G+D)
    product=aggregate(f,'Product').sort_values(['DiscountUSD','Product'],ascending=[False,True])
    product['ExposureShare']=product.DiscountUSD/D
    nondiscount=aggregate(full,'Product').rename(columns={k:'NonDiscount'+k for k in ['Lines','Units','RevenueUSD','GPUSD','DiscountUSD']})
    compare=product.merge(nondiscount,on='Product',validate='one_to_one')
    compare['DiscountedGPPerUnitUSD']=compare.GPUSD/compare.Units
    compare['NonDiscountGPPerUnitUSD']=compare.NonDiscountGPUSD/compare.NonDiscountUnits
    compare['DiscountedMargin']=compare.GPUSD/compare.RevenueUSD
    compare['NonDiscountMargin']=compare.NonDiscountGPUSD/compare.NonDiscountRevenueUSD
    compare['TreatedUnitsBreakEvenLoss']=compare.DiscountUSD/(compare.GPUSD+compare.DiscountUSD)
    np.testing.assert_allclose(compare.NonDiscountGPPerUnitUSD,(compare.GPUSD+compare.DiscountUSD)/compare.Units)
    def concentration(key):
        e=eligible.groupby(key,as_index=False).agg(SameProductLines=('Product','size'))
        a=aggregate(f,key)
        t=e.merge(a,on=key,how='left').fillna(0)
        t[['Lines','Units']]=t[['Lines','Units']].astype(int)
        t['FlaggedLineRate']=t.Lines/t.SameProductLines
        t['ExposureShare']=t.DiscountUSD/D
        return t
    for z in [eligible,f]:
        z['Month']=z.Date.dt.strftime('%Y-%m');z['Weekday']=z.Date.dt.day_name()
    hours=concentration('Hour');dates=concentration('Date');months=concentration('Month');weekdays=concentration('Weekday')
    weekdays=weekdays.set_index('Weekday').reindex(DAYS).reset_index()
    topdates=dates.sort_values(['DiscountUSD','Date'],ascending=[False,True]).head(5).copy();topdates.Date=topdates.Date.dt.strftime('%Y-%m-%d')
    scopes=[]
    for label,scope in [('Discounted units only; unchanged affected-product mix',f),
                         ('All seven products; uniform volume/mix change',eligible),
                         ('Whole Garden branch; uniform volume/mix change',g)]:
        gp=float(scope['Line Gross Profit (USD)'].sum());after=gp+D;loss=D/after
        assert np.isclose((1-loss)*after-gp,0)
        scopes.append({'Scope':label,'BaselineGPUSD':gp,'NoDiscountSameVolumeGPUSD':after,
                       'ExposureUSD':D,'UniformUnitLossBreakEven':loss,'BaselineUnits':int(scope.Quantity.sum())})
    scope_table=pd.DataFrame(scopes)
    sensitivity=[]
    for loss in [0,.1,.2,D/(G+D),.3,.4]:
        sensitivity.append({'TreatedUnitLoss':loss,'HypotheticalGPUSD':(1-loss)*(G+D),
                            'ChangeVsObservedGPUSD':(1-loss)*(G+D)-G})
    sensitivity=pd.DataFrame(sensitivity)
    sensitivity.loc[np.isclose(sensitivity.ChangeVsObservedGPUSD,0),'ChangeVsObservedGPUSD']=0.
    # Only aggregates are saved: no customer/transaction identifiers or individual lines.
    for name,t in [('products',product),('same_product_comparison',compare),('hours',hours),('dates',dates),
                   ('months',months),('weekdays',weekdays),('break_even_scopes',scope_table),('volume_sensitivity',sensitivity)]:
        t.to_csv(OUT/f'garden_discount_{name}.csv',index=False)
    top=product.iloc[0];top3=float(product.head(3).DiscountUSD.sum())
    top_hour=hours.sort_values('DiscountUSD',ascending=False).iloc[0]
    tue=weekdays[weekdays.Weekday=='Tuesday'].iloc[0]
    peak=hours[hours.Hour.between(19,22)]
    overall_rate=len(f)/len(eligible)
    units_non=int(full.Quantity.sum());rev_non=float(full['Line Revenue (USD)'].sum());gp_non=float(full['Line Gross Profit (USD)'].sum())
    baskets=g[g['Transaction ID'].isin(f['Transaction ID'])]
    rate_formula=float((f.Quantity*f['Unit Price (USD)']*f['Discount Rate']).sum())
    text=f'''# Garden discount investigation: the 153 low-margin lines

## Three actionable findings

1. **Use a product-defined review, not an invented narrow time window.** All **153 lines** have a recorded **10% discount**, covering **seven products, 162 units and 152 unique transactions across 101 dates**. {top.Product} has the largest exposure, **${top.DiscountUSD:.2f} ({top.ExposureShare:.1%})**. The top three products account for **${top3:.2f} ({top3/D:.1%})**, so no single product contains most of the exposure. Verify eligibility for these seven products before choosing a test; a one-product/hour test would have very little historical volume.
2. **The observed exposure is small and the volume-loss denominator matters.** These lines record **${R:,.2f} revenue**, **${G:,.2f} GP** and **${D:.2f} discount exposure**. At unchanged purchases and costs, the no-discount accounting sensitivity is **${G+D:.2f} GP**, an increase of **${D:.2f} over the entire six-month file**—about **${D/181:.2f}/calendar day**. The break-even unit loss is **{D/(G+D):.2%}** if only affected discounted-item volume changes, but **{scope_table.iloc[1].UniformUnitLossBreakEven:.2%}** if volume falls proportionally across all sales of these seven products. This is a sensitivity, not a predicted customer response or actual saving.
3. **Reconcile Garden costing and review product margins before changing offers.** Sparkling Water's non-discounted recorded margin is already **29.82%**, below the 30% screen; removing its discount would not move it above that threshold. Turkey & Cheese Sandwich is only **30.05%** at full price. No flagged line is loss-making at the recorded GP level. Check the branch cost-allocation rule and promotion rationale, then consider a controlled eligibility/discount test with total basket GP and lost purchases measured.

## Scope and definitions

Source: original `stories_transactions.csv`, January 1–June 30, 2026. Reproduce the flag exactly: `Branch == Garden`, `Discount Rate > 0`, and `Line Gross Profit / Line Revenue < 0.30`. Thirty percent is a screening choice, not a measured optimal margin. This is a line-level selection: 153 lines belong to 152 baskets, not 153 customers.

Observed discount dollars are `Quantity × Unit Price − recorded Line Revenue` on those lines. Use recorded revenue and GP without recomputing them from an unrounded discount percentage. The unrounded rate formula gives **${rate_formula:.4f}**, versus **${D:.2f}** recorded exposure; the small rounding difference is not extra leakage. Recorded input cost for the flagged lines is **${R-G:.2f}**. All seven products have constant recorded list prices and unit costs at Garden throughout the period.

Keep all original recorded lines, consistent with the existing audit. **None of the flagged lines is an exact duplicate** under the source columns; other file-wide duplicate-origin concerns remain unresolved. No model was trained, application feature added, source row changed, or individual customer/transaction record published.

## Products and observed dollars

'''+table(product,['RevenueUSD','GPUSD','DiscountUSD'],['ExposureShare'])+f'''

Totals: **{len(f)} lines; {Q} units; ${R:,.2f} revenue; ${G:,.2f} recorded GP; ${D:.2f} discount exposure**. Aggregate recorded margin is **{G/R:.2%}**. Each flagged line still has positive recorded GP. The observed discount exposure is part of Garden's existing $555.90 total and the network's $2,178.09 total; do not add the subset to those totals.

## Comparison with non-discounted Garden sales of the same products

Every discounted sale of these seven products is in the flagged set; there are no additional positive-discount sales of these products outside it. The comparison group contains **{len(full):,} non-discounted lines, {units_non:,} units, ${rev_non:,.2f} revenue and ${gp_non:,.2f} GP**. The same seven products have **{len(eligible):,} total lines and {int(eligible.Quantity.sum()):,} units** at Garden. Discounted lines are **{overall_rate:.2%}** of those lines.

Non-discounted observed sales and both per-unit comparisons:

'''+table(compare[['Product','NonDiscountLines','NonDiscountUnits','NonDiscountRevenueUSD','NonDiscountGPUSD','DiscountedGPPerUnitUSD','NonDiscountGPPerUnitUSD']],['NonDiscountRevenueUSD','NonDiscountGPUSD'],decimals=['DiscountedGPPerUnitUSD','NonDiscountGPPerUnitUSD'])+'''

Per-unit GP is **sum recorded line GP / sum Quantity**, not an average of line margins or a count of baskets. Four decimal places retain quantity/rounding effects; all amounts are USD. The product-matched comparison avoids simply contrasting different product mixes.

'''+table(compare[['Product','DiscountedMargin','NonDiscountMargin','TreatedUnitsBreakEvenLoss']],percent=['DiscountedMargin','NonDiscountMargin','TreatedUnitsBreakEvenLoss'])+f'''

Pooled observed GP/unit is **${G/Q:.4f}** for the discounted lines and **${gp_non/units_non:.4f}** for non-discounted lines; these pooled groups also have different product weights. At the **discounted group's own product mix**, hypothetical full-price GP/unit is **${(G+D)/Q:.4f}**. Prefer the product-matched rows to interpreting the pooled difference as a policy effect.

**This is an accounting comparison, not a causal estimate.** The groups are not randomized, and the flag itself selects low realized margins. Constant recorded price/cost and different recorded discounts reconcile the unit-GP differences arithmetically; they do not establish that offering or withdrawing a promotion changes overall profitability in the same way. Customer intent, eligibility, timing, basket composition and purchases that would not occur at full price are unobserved.

## Concentration by dates, weekdays and hours

There is exposure on **{f.Date.nunique()} of 181 calendar dates**, in **all six months**, and across **all 17 recorded hours (07:00–23:59)**. Observed sales hours do not establish opening schedules. No single date or hour contains most of the dollars; this does not rule out an unrecorded eligibility rule or statistically meaningful pattern.

Denominators below are **all Garden lines of the same seven products in that period**, including discounted and non-discounted lines. `FlaggedLineRate` is a descriptive incidence among sold lines, not a customer discount probability, footfall conversion rate or causal effect. Date/hour scans are exploratory and unadjusted for product mix or multiple comparisons.

### Months

'''+table(months[['Month','SameProductLines','Lines','DiscountUSD','FlaggedLineRate']],['DiscountUSD'],['FlaggedLineRate'])+'''

### Weekdays

'''+table(weekdays[['Weekday','SameProductLines','Lines','DiscountUSD','FlaggedLineRate']],['DiscountUSD'],['FlaggedLineRate'])+f'''

Tuesday has **${tue.DiscountUSD:.2f}** of exposure, but its flagged-line incidence is **{tue.FlaggedLineRate:.2%}**, close to the pooled **{overall_rate:.2%}**. A higher raw Tuesday count is not evidence that the discount is targeted disproportionately to Tuesday.

### Hours

'''+table(hours[['Hour','SameProductLines','Lines','DiscountUSD','FlaggedLineRate']],['DiscountUSD'],['FlaggedLineRate'])+f'''

The largest raw-dollar hour is **{int(top_hour.Hour):02d}:00–{int(top_hour.Hour):02d}:59**, with **${top_hour.DiscountUSD:.2f} ({top_hour.ExposureShare:.1%})**, **{int(top_hour.Lines)} flagged lines among {int(top_hour.SameProductLines)} same-product lines**, and a **{top_hour.FlaggedLineRate:.2%}** flagged-line rate. That does not exceed the pooled rate. The 17:00 hour has a higher descriptive incidence (**15/132 = 11.36%**) but only **$11.35** exposure and no causal or confirmatory significance claim.

The 19:00–22:59 window contains **${peak.DiscountUSD.sum():.2f} ({peak.DiscountUSD.sum()/D:.1%})** of exposure and **{int(peak.Lines.sum())} flagged lines among {int(peak.SameProductLines.sum())} same-product lines**. Narrowing a test to peak periods is not justified solely by raw traffic or exposure.

### Five dates with largest exposure

'''+table(topdates[['Date','SameProductLines','Lines','DiscountUSD','ExposureShare']],['DiscountUSD'],['ExposureShare'])+f'''

The largest date contributes **{topdates.iloc[0].ExposureShare:.2%}**; the top five dates together contribute **{topdates.DiscountUSD.sum()/D:.2%}**. Full day-level aggregates, including zero-flag days, are in [garden_discount_dates.csv](garden_discount_dates.csv). A few exceptional dates do not account for most of the $121.63.

## Hypothetical no-discount exposure and break-even purchasing loss

**Observed:** flagged-line GP is ${G:.2f}; recorded discount exposure is ${D:.2f}. **Hypothetical:** if the exact same {Q} units were bought at recorded list prices with unchanged recorded unit costs, GP would be **${G+D:.2f}**, an increase of **${D:.2f}**. This is the maximum direct accounting uplift from removing only these discounts at those fixed quantities, not a prediction of attainable profit or a bound on every possible longer-run policy outcome. No extrapolation to future demand or annual savings is made.

For a defined affected scope with current GP `G_scope` and exposure `D = $121.63`, assume a proportional unit-volume decline `L`, stable product mix, unchanged prices and unit costs, no replacement purchases, and that recorded unit costs scale with retained units:

`GP_after(L) = (1 − L) × (G_scope + D)`.

`Incremental GP(L) = (1 − L) × (G_scope + D) − G_scope`.

`Break-even unit-volume loss = D / (G_scope + D)`.

At equality the policies tie on this accounting model; losses above the boundary make discount removal worse. This is **not** `discount / revenue`, a sales elasticity estimate, a customer-loss probability or a guarantee about avoidable cash cost.

'''+table(scope_table[['Scope','BaselineGPUSD','NoDiscountSameVolumeGPUSD','UniformUnitLossBreakEven']],['BaselineGPUSD','NoDiscountSameVolumeGPUSD'],['UniformUnitLossBreakEven'])+'''

- **Discounted-only boundary:** 29.85% refers only to the 162 previously discounted units, at their same mix, with every other purchase unchanged. It does **not** mean Garden can lose 29.85% of customers or all sales. Product-specific discounted-only boundaries are in the comparison table above (approximately 27.34%–33.43%). Which products are lost matters.
- **Seven-product boundary:** 1.93% assumes proportional loss across all 2,510 units of these products, including full-price units, while other products are unaffected.
- **Whole-branch boundary:** 0.259% assumes proportional loss across all 17,833 Garden units and their existing mix. This illustrates exposure to broader basket/retention effects; it is not evidence that such a loss will occur.

These are alternative loss scopes, not interchangeable estimates. If particular baskets disappear, their own GP must be used; transaction count alone is insufficient. The 152 baskets containing flagged lines record **'''+f'${baskets["Line Revenue (USD)"].sum():,.2f} revenue and ${baskets["Line Gross Profit (USD)"].sum():,.2f} total basket GP**'+''', including other purchases. This observed context is not proof that any of those baskets depend on the discount, and it must not be added to the discount exposure.

Discounted-only volume sensitivity:

'''+table(sensitivity,money=['HypotheticalGPUSD','ChangeVsObservedGPUSD'],percent=['TreatedUnitLoss'])+'''

The calculation ignores fixed overhead, labor changes, ingredient shelf life, disposal of prepared items, marketing/monitoring cost, substitution and long-run retention. It also treats recorded unit cost as scaling with units, although Garden's uniform branch cost multiplier may include allocations. Confirm avoidable costs before translating accounting GP into cash benefit.

## Practical controlled experiment

First ask finance to reconcile Garden's cost rule and operations to identify the promotion eligibility/reason codes for the seven products. The 30% outcome screen is for this audit; do not use realized low margin after purchase to assign treatment.

If the small available exposure justifies the implementation/measurement cost, predefine a product/eligibility population **before purchase** and randomize eligible offer opportunities between the existing 10% policy and a no-discount policy. Keep stock availability, placement and service comparable; record assignments, offers, nonpurchases/abandonment where feasible, quantities and complete baskets. Avoid selecting dates/hours from this retrospective scan simply because they look unusual. Consider repeat-customer exposure and contamination when choosing the randomization unit.

Use **total recorded GP per assigned eligible opportunity**, with verified cost accounting and implementation cost, as the primary endpoint. Track product units, total basket GP, substitution, customer response and service. Including nonbuyers avoids falsely concluding that higher GP per completed sale necessarily means a better policy. Predefine the sample plan, net-value decision rule and stopping conditions; the historical 153 discounted lines over six months warn that a very narrow test could be slow or underpowered. No sample size or causal effect is established by this audit.

## Evidence and reproduction

- [Product totals](garden_discount_products.csv), [same-product comparison](garden_discount_same_product_comparison.csv), [hours](garden_discount_hours.csv), [dates](garden_discount_dates.csv), [months](garden_discount_months.csv), [weekdays](garden_discount_weekdays.csv), [break-even scopes](garden_discount_break_even_scopes.csv), [volume sensitivities](garden_discount_volume_sensitivity.csv). These are aggregates without customer or transaction identifiers.
- [Financial ranking being investigated](FINANCIAL_EVIDENCE_RANKING.md), [saved Profit Lab totals](findings.json), [root-cause costing investigation](../root_cause/REPORT.md).
- Reproduce: `python3 src/investigate_garden_discounts.py --data /path/to/stories_transactions.csv`. The script contains no model imports, fitting or application-feature changes. It checks the 153-line/$121.63 reconciliation, unit-cost/GP identities, fixed price/cost comparisons and break-even equality before writing this report.

Source SHA-256: `'''+before+'''`. Original data remain unchanged. All dollar values are recorded accounting amounts unless explicitly labelled hypothetical; none is a measured saving or a causal estimate of removing discounts.
'''
    (OUT/'GARDEN_DISCOUNT_INVESTIGATION.md').write_text(text)
    assert hashlib.sha256(path.read_bytes()).hexdigest()==before
    print(f'PASS: {len(f)} lines, {Q} units, revenue ${R:.2f}, GP ${G:.2f}, discount exposure ${D:.2f}; original source unchanged.')
    print(scope_table[['Scope','UniformUnitLossBreakEven']].to_string(index=False))
    print(OUT/'GARDEN_DISCOUNT_INVESTIGATION.md')


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--data',default='/Users/aya/Downloads/stories_transactions.csv');run(p.parse_args().data)
