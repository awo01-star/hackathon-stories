"""Export menu and aggregate pairing evidence fit only on January–May baskets.
No customer IDs, transaction IDs or row-level data enter the site bundle.
"""
from pathlib import Path
import json
import pandas as pd
R=Path(__file__).resolve().parents[1]
DRINK=['Cold Drinks','Cold Coffee','Hot Coffee','Matcha & Tea']
FOOD=['Bakery','Breakfast','Desserts','Meals','Sandwiches']
def export(path):
 x=pd.read_csv(path);x=x[x.Date<'2026-06-01'].copy()
 menu=x.groupby(['Branch','Product'],sort=True).agg(category=('Category','first'),price=('Unit Price (USD)','median'),cost=('Unit Cost (USD)','median')).reset_index()
 drinks=sorted(x[x.Category.isin(DRINK)].Product.unique());foods=sorted(x[x.Category.isin(FOOD)].Product.unique())
 pairings={}
 for branch in sorted(x.Branch.unique()):
  b=x[x.Branch==branch];food=b[b.Category.isin(FOOD)].drop_duplicates(['Transaction ID','Product'])
  allids=set(b['Transaction ID']);prior=food.Product.value_counts()/len(allids)
  bm=menu[menu.Branch==branch].set_index('Product');pairings[branch]={}
  for drink in drinks:
   ids=set(b.loc[b.Product==drink,'Transaction ID']);hits=food[food['Transaction ID'].isin(ids)].Product.value_counts();n=len(ids)
   ranked=[]
   for product in foods:
    support=int(hits.get(product,0));prob=(support+30*float(prior.get(product,0)))/(n+30);price=float(bm.loc[product,'price']);margin=price-float(bm.loc[product,'cost'])
    ranked.append({'product':product,'category':bm.loc[product,'category'],'price':price,'rate':round(prob,6),'support':support,'baskets':n,'rankScore':round(prob*margin,6)})
   pairings[branch][drink]=sorted(ranked,key=lambda r:r['rankScore'],reverse=True)[:3]
 out={'fitThrough':'2026-05-31','method':'Smoothed drink/branch product co-purchase rate × branch-specific unit gross margin; 30 pseudo-baskets. Product-level extension of the simple baseline; not the XGBoost model and not evaluated as a product recommender.','menu':[{'branch':r.Branch,'name':r.Product,'category':r.category,'price':float(r.price)} for r in menu.itertuples()],'pairings':pairings}
 p=R/'drink-lens/dist/assets/catalog.json';p.write_text(json.dumps(out,separators=(',',':')));print(f'Exported {len(menu)} branch/menu entries and {sum(len(v) for v in pairings.values())} drink/branch pairing lists; fit through May 31.')
if __name__=='__main__':
 import argparse
 p=argparse.ArgumentParser();p.add_argument('--data',default='/Users/aya/Downloads/stories_transactions.csv');export(p.parse_args().data)
