"""Reproduce Stories ProfitPilot. No network calls; source CSV remains private."""
from pathlib import Path
import argparse, json, hashlib
import numpy as np
import pandas as pd
from scipy.stats import norm
from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import OneHotEncoder
from sklearn.pipeline import make_pipeline
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score, average_precision_score, log_loss, brier_score_loss
from xgboost import XGBClassifier
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import joblib

ROOT=Path(__file__).resolve().parents[1]
FOOD=['Bakery','Breakfast','Desserts','Meals','Sandwiches']
DRINK=['Cold Drinks','Cold Coffee','Hot Coffee','Matcha & Tea']
CAT=['Branch','Order Type','anchor','candidate']
NUM=['hour','dow','day','weekend']

def metrics(y,p):
 return dict(roc_auc=float(roc_auc_score(y,p)),pr_auc=float(average_precision_score(y,p)),log_loss=float(log_loss(y,p)),brier=float(brier_score_loss(y,p)),prevalence=float(np.mean(y)))

def main(path):
 for d in ['reports','figures','artifacts']: (ROOT/d).mkdir(exist_ok=True)
 x=pd.read_csv(path); x['date']=pd.to_datetime(x.Date)
 audit={'rows':len(x),'baskets':int(x['Transaction ID'].nunique()),'dates':[x.Date.min(),x.Date.max()], 'sha256':hashlib.sha256(Path(path).read_bytes()).hexdigest(),'missing_customer_fraction':float(x['Customer ID'].isna().mean()),'exact_duplicate_rows':int(x.duplicated().sum()),'basket_inconsistent_fields':x.groupby('Transaction ID')[['Date','Time','Branch','Order Type','Customer ID']].nunique().max().to_dict()}
 rev=x.Quantity*x['Unit Price (USD)']*(1-x['Discount Rate'])
 gp=x['Line Revenue (USD)']-x.Quantity*x['Unit Cost (USD)']
 audit['revenue_max_abs_rounding_error']=float(abs(rev-x['Line Revenue (USD)']).max());audit['gross_profit_max_abs_rounding_error']=float(abs(gp-x['Line Gross Profit (USD)']).max())
 audit['negative_profit_lines']=int((x['Line Gross Profit (USD)']<0).sum())
 audit['total_revenue']=float(x['Line Revenue (USD)'].sum());audit['total_gross_profit']=float(x['Line Gross Profit (USD)'].sum())
 # One record per basket; anchor selection is deterministic, never uses food labels.
 bev=x[x.Category.isin(DRINK)].sort_values(['Transaction ID','Product']).drop_duplicates('Transaction ID')
 b=bev[['Transaction ID','date','Time','Branch','Order Type','Product']].rename(columns={'Product':'anchor'}).copy()
 b['hour']=b.Time.str[:2].astype(int);b['dow']=b.date.dt.dayofweek;b['weekend']=(b.dow>=5).astype(int);b['day']=(b.date-x.date.min()).dt.days
 labels=x[x.Category.isin(FOOD)].groupby(['Transaction ID','Category']).size().unstack(fill_value=0).reindex(columns=FOOD,fill_value=0).gt(0).astype(int)
 b=b.merge(labels,on='Transaction ID',how='left').fillna({c:0 for c in FOOD}).sort_values(['date','Transaction ID']).reset_index(drop=True)
 audit['beverage_baskets']=len(b);audit['multiple_distinct_beverages_fraction']=float((x[x.Category.isin(DRINK)].groupby('Transaction ID').Product.nunique()>1).mean())
 z=b.melt(id_vars=['Transaction ID','date','Branch','Order Type','anchor']+NUM,value_vars=FOOD,var_name='candidate',value_name='y')
 tr=z.date<'2026-05-01'; va=(z.date>='2026-05-01')&(z.date<'2026-06-01');te=z.date>='2026-06-01'
 features=CAT+NUM
 prep=lambda:ColumnTransformer([('cat',OneHotEncoder(handle_unknown='ignore',sparse_output=False),CAT),('num','passthrough',NUM)])
 # Smoothing strength fixed in advance. Validation used only to select ML model.
 def rates(train,test,keys):
  prior=train.groupby('candidate').y.mean()
  agg=train.groupby(keys).y.agg(['sum','count']);out=test[keys].merge(agg,left_on=keys,right_index=True,how='left')
  p=test.candidate.map(prior).to_numpy();return (out['sum'].fillna(0).to_numpy()+30*p)/(out['count'].fillna(0).to_numpy()+30)
 def base(train,test):
  return {'category_prior':test.candidate.map(train.groupby('candidate').y.mean()).to_numpy(),'branch_time':rates(train,test,['candidate','Branch','hour']),'drink_branch':rates(train,test,['candidate','Branch','anchor'])}
 models={'logistic':make_pipeline(prep(),LogisticRegression(max_iter=1500,C=.2)), 'boosted_depth2':make_pipeline(prep(),XGBClassifier(n_estimators=200,max_depth=2,learning_rate=.04,min_child_weight=50,subsample=.85,colsample_bytree=.9,reg_lambda=10,n_jobs=4,random_state=490,eval_metric='logloss')), 'boosted_depth4':make_pipeline(prep(),XGBClassifier(n_estimators=250,max_depth=4,learning_rate=.035,min_child_weight=40,subsample=.85,colsample_bytree=.9,reg_lambda=15,n_jobs=4,random_state=490,eval_metric='logloss'))}
 validation={};vp=base(z[tr],z[va])
 for name,m in models.items():
  m.fit(z.loc[tr,features],z.loc[tr,'y']);vp[name]=m.predict_proba(z.loc[va,features])[:,1]
 for name,p in vp.items(): validation[name]=metrics(z.loc[va,'y'],p)
 winner=min(models,key=lambda n:validation[n]['log_loss']); print('Validation',json.dumps(validation,indent=2),flush=True)
 train=z[tr|va];test=z[te].copy();pred=base(train,test)
 selected=models[winner];selected.fit(train[features],train.y);pred[winner]=selected.predict_proba(test[features])[:,1]
 result={'validation':validation,'selected_ml':winner,'test':{n:metrics(test.y,p) for n,p in pred.items()},'split':{'train':'Jan–Apr','validation':'May','test':'June','final_fit':'Jan–May'},'test_baskets':int(test['Transaction ID'].nunique())}
 # Compute uncertainty by resampling entire days, preserving category/basket dependence.
 rng=np.random.default_rng(490);days=test.date.unique();inds=[np.flatnonzero(test.date.to_numpy()==d) for d in days]
 bestbase=min(base(train,test),key=lambda n:validation[n]['log_loss'])
 diffs=[]
 for _ in range(500):
  ix=np.concatenate([inds[i] for i in rng.integers(0,len(days),len(days))]);y=test.y.to_numpy()[ix]
  diffs.append(log_loss(y,pred[bestbase][ix])-log_loss(y,pred[winner][ix]))
 result['paired_day_bootstrap']={'baseline':bestbase,'metric':'baseline log loss minus ML log loss (positive favors ML)','ci95':np.quantile(diffs,[.025,.975]).tolist(),'replicates':500}
 # Within-category performance prevents a high pooled AUC from hiding category prevalence.
 result['per_category']={}
 for c in FOOD:
  ix=(test.candidate==c).to_numpy();result['per_category'][c]={n:metrics(test.y.to_numpy()[ix],p[ix]) for n,p in pred.items()}
 result['per_branch']={}
 for c in sorted(test.Branch.unique()):
  ix=(test.Branch==c).to_numpy();result['per_branch'][c]=metrics(test.y.to_numpy()[ix],pred[winner][ix])
 # Same-basket held-out retrieval, not recommendation response or causal uplift.
 margins=x[(x.date<'2026-06-01')&x.Category.isin(FOOD)].groupby('Category').apply(lambda a:a['Line Gross Profit (USD)'].sum()/a.Quantity.sum(),include_groups=False).to_dict()
 branch_margins=x[(x.date<'2026-06-01')&x.Category.isin(FOOD)].groupby(['Branch','Category']).apply(lambda a:a['Line Gross Profit (USD)'].sum()/a.Quantity.sum(),include_groups=False)
 test['unit_margin']=[branch_margins.loc[(b,c)] for b,c in zip(test.Branch,test.candidate)]
 policies={};record=test[['Transaction ID','date','Branch','anchor','candidate','y']].copy()
 for n,p in pred.items():
  record[n]=p
  for profit in [False,True]:
   score=p*test.unit_margin.to_numpy() if profit else p
   choices=test.assign(score=score,p=p).sort_values(['Transaction ID','score'],ascending=[True,False]).drop_duplicates('Transaction ID')
   policies[n+('_margin' if profit else '_probability')]={'hit_rate':float(choices.y.mean()),'matched_margin_proxy':float((choices.y*choices.unit_margin).mean()),'choices':choices.candidate.value_counts().to_dict()}
 result['retrieval_policies']=policies;result['training_unit_margins']=margins
 record.to_csv(ROOT/'artifacts/heldout_predictions.csv',index=False)
 # Association confounding: total observed discount vs composition-adjusted margin accounting.
 x.groupby(['Branch','Category','Discount Rate']).agg(lines=('Product','size'),quantity=('Quantity','sum'),revenue=('Line Revenue (USD)','sum'),gross_profit=('Line Gross Profit (USD)','sum')).to_csv(ROOT/'reports/discount_audit.csv')
 monthly=x.groupby([x.date.dt.to_period('M').astype(str),'Branch']).agg(lines=('Product','size'),revenue=('Line Revenue (USD)','sum'),gross_profit=('Line Gross Profit (USD)','sum'));monthly.to_csv(ROOT/'reports/monthly_branch.csv')
 # Discrete associations with branch/time: inspect honest conditional attachment rates.
 summary=b.groupby(['Branch','hour'])[FOOD].agg(['mean','size']);summary.to_csv(ROOT/'reports/attachment_by_branch_hour.csv')
 x.groupby(['Branch','Product']).agg(quantity=('Quantity','sum'),revenue=('Line Revenue (USD)','sum'),gross_profit=('Line Gross Profit (USD)','sum')).to_csv(ROOT/'reports/product_economics.csv')
 joblib.dump(selected,ROOT/'artifacts/model.joblib')
 (ROOT/'reports/data_audit.json').write_text(json.dumps(audit,indent=2));(ROOT/'reports/metrics.json').write_text(json.dumps(result,indent=2))
 fig,ax=plt.subplots(figsize=(8,4)); names=list(result['test']);ax.bar(names,[result['test'][n]['log_loss'] for n in names]);ax.set_ylabel('June log loss (lower is better)');ax.set_title('Chronological holdout: ML versus simple baselines');fig.tight_layout();fig.savefig(ROOT/'figures/model_comparison.png',dpi=160);plt.close(fig)
 fig,ax=plt.subplots(figsize=(7,4))
 for n in [bestbase,winner]:
  f=pd.DataFrame({'p':pred[n],'y':test.y.to_numpy()}); f['bin']=pd.qcut(f.p,10,duplicates='drop');g=f.groupby('bin',observed=True).agg(predicted=('p','mean'),observed=('y','mean'));ax.plot(g.predicted,g.observed,'o-',label=n)
 ax.plot([0,.5],[0,.5],'k--');ax.set(xlabel='Predicted probability',ylabel='Observed attachment rate',title='June calibration (pooled categories)');ax.legend();fig.tight_layout();fig.savefig(ROOT/'figures/calibration.png',dpi=160);plt.close(fig)
 print(json.dumps(result,indent=2),flush=True)

if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--data',default='/Users/aya/Downloads/stories_transactions.csv');main(p.parse_args().data)
