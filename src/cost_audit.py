from pathlib import Path
import argparse,json
import pandas as pd
R=Path(__file__).resolve().parents[1]
def main(path):
 x=pd.read_csv(path)
 # Median product unit cost comparison; actual Garden quantity holds mix constant.
 p=x.groupby(['Product','Branch'])['Unit Cost (USD)'].median().unstack()
 p['garden_harbour_ratio']=p.Garden/p.Harbour
 g=x[x.Branch=='Garden'].copy();g['harbour_cost']=g.Product.map(p.Harbour)
 g['cost_gap']=g.Quantity*(g['Unit Cost (USD)']-g.harbour_cost)
 out={'median_garden_harbour_unit_cost_ratio':float(p.garden_harbour_ratio.median()),'ratio_range':[float(p.garden_harbour_ratio.min()),float(p.garden_harbour_ratio.max())],'garden_cost_gap_at_harbour_costs':float(g.cost_gap.sum()),'garden_recorded_cost':float((g.Quantity*g['Unit Cost (USD)']).sum()),'garden_revenue':float(g['Line Revenue (USD)'].sum()),'garden_gross_profit':float(g['Line Gross Profit (USD)'].sum()),'cost_unique_max_within_branch_product':int(x.groupby(['Branch','Product'])['Unit Cost (USD)'].nunique().max()),'price_unique_max_within_branch_product':int(x.groupby(['Branch','Product'])['Unit Price (USD)'].nunique().max()),'interpretation':'Accounting sensitivity, not achievable savings. Uniform multiplier may reflect cost allocation, procurement, recipe or dataset construction; validate with finance.'}
 out['recoverable_gap_scenarios']={str(k):float(g.cost_gap.sum()*k) for k in [.1,.25,.5,1]}
 g.groupby('Product').cost_gap.sum().sort_values(ascending=False).to_csv(R/'reports/garden_cost_gap.csv');p.to_csv(R/'reports/matched_product_costs.csv');(R/'reports/cost_audit.json').write_text(json.dumps(out,indent=2));print(json.dumps(out,indent=2))
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--data',default='/Users/aya/Downloads/stories_transactions.csv');main(p.parse_args().data)
