"""Step 7. Fixed small search on May; one final rolling one-day June evaluation."""
from pathlib import Path
import argparse,hashlib,json
import numpy as np
import pandas as pd
import joblib
from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import OneHotEncoder
from sklearn.pipeline import Pipeline
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error,mean_squared_error
from xgboost import XGBRegressor
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
R=Path(__file__).resolve().parents[1]
FEATURES=['Branch','DayOfWeek','Month','DayOfMonth','Weekend','Lag1','Lag7','RollingMean7']
CAT=['Branch','DayOfWeek'];NUM=[f for f in FEATURES if f not in CAT]
GRID={
 'Random Forest':[{'n_estimators':300,'max_depth':depth,'min_samples_leaf':leaf,'max_features':1.0}for depth in [4,None]for leaf in [2,5]],
 'XGBoost':[{'n_estimators':n,'max_depth':d,'learning_rate':.03,'min_child_weight':5,'reg_lambda':10,'subsample':1.0,'colsample_bytree':1.0}for d in [2,3]for n in [150,300]]
}
def metric(y,p):
 y=np.asarray(y,float);p=np.asarray(p,float)
 return {'MAE':float(mean_absolute_error(y,p)),'RMSE':float(np.sqrt(mean_squared_error(y,p))),'WAPE':float(np.sum(abs(y-p))/np.sum(abs(y)))}
def build_model(name,params):
 pre=ColumnTransformer([('categorical',OneHotEncoder(handle_unknown='ignore',sparse_output=False),CAT),('numeric','passthrough',NUM)])
 estimator=RandomForestRegressor(**params,random_state=490,n_jobs=4) if name=='Random Forest' else XGBRegressor(**params,objective='reg:squarederror',tree_method='hist',random_state=490,n_jobs=4)
 return Pipeline([('preprocess',pre),('regressor',estimator)])
def split_data(path):
 x=pd.read_csv(path,parse_dates=['Date']).sort_values(['Date','Branch']).reset_index(drop=True)
 if x.duplicated(['Branch','Date']).any():raise ValueError('Duplicate branch/date keys')
 x=x[x.Date.between('2026-01-08','2026-06-30')].copy()
 if x[FEATURES+['Transactions']].isna().any().any():raise ValueError('Missing required history/target after warm-up; resolve without automatic imputation')
 train=x[x.Date<='2026-04-30'].copy();validation=x[x.Date.between('2026-05-01','2026-05-31')].copy();test=x[x.Date.between('2026-06-01','2026-06-30')].copy()
 assert train.Date.max()<validation.Date.min() and validation.Date.max()<test.Date.min()
 assert set(train.Branch)==set(validation.Branch)==set(test.Branch)=={'Harbour','Garden','Uptown'}
 return train,validation,test

def tune(train,validation,out):
 out=Path(out);out.mkdir(parents=True,exist_ok=True)
 # Persist the full candidate list before fitting; never expand after reading June scores.
 spec={'seed':490,'grid':GRID,'selectionMetric':'pooled May MAE','tieBreak':'fixed model/trial order','features':FEATURES,'target':'Transactions','testUsedForSelection':False,'preprocessing':'OneHotEncoder fit inside each training-only pipeline; categorical Branch/DayOfWeek; numeric passthrough; no imputation/scaling','forecastProtocol':'Rolling one-day ahead after yesterday closes. May/June lag features use earlier observed days, never the current date.'}
 (out/'search_spec.json').write_text(json.dumps(spec,indent=2));trials=[];chosen={};valpred={'Seasonal naive':validation.Lag7.to_numpy(float)}
 validation_rows={'Seasonal naive':metric(validation.Transactions,valpred['Seasonal naive'])}
 for name,grid in GRID.items():
  candidates=[]
  for i,params in enumerate(grid):
   model=build_model(name,params);model.fit(train[FEATURES],train.Transactions)
   pred=np.maximum(model.predict(validation[FEATURES]),0);scores=metric(validation.Transactions,pred)
   record={'model':name,'trial':i,'params':params,**scores};trials.append(record);candidates.append((scores['MAE'],i,params,pred))
  _,i,params,pred=min(candidates,key=lambda z:(z[0],z[1]));chosen[name]={'trial':i,'params':params};valpred[name]=pred;validation_rows[name]=metric(validation.Transactions,pred)
 winner=min(validation_rows,key=lambda n:validation_rows[n]['MAE'])
 lock={'selectedByMay':winner,'selectedSettings':chosen,'validationMetrics':validation_rows,'trainingRange':['2026-01-08','2026-04-30'],'validationRange':['2026-05-01','2026-05-31'],'testRange':['2026-06-01','2026-06-30'],'refitPolicy':'Refit each selected ML configuration and preprocessing on Jan 8–May 31 before June scoring. Never fit on June.'}
 (out/'selection_lock.json').write_text(json.dumps(lock,indent=2));pd.DataFrame([{**r,'params':json.dumps(r['params'],sort_keys=True)}for r in trials]).to_csv(out/'validation_search.csv',index=False)
 return lock,valpred

def final_evaluation(train,validation,test,lock,valpred,out,artifacts):
 out=Path(out);artifacts=Path(artifacts);artifacts.mkdir(parents=True,exist_ok=True)
 fit=pd.concat([train,validation],ignore_index=True);testpred={'Seasonal naive':test.Lag7.to_numpy(float)};models={}
 for name,s in lock['selectedSettings'].items():
  model=build_model(name,s['params']);model.fit(fit[FEATURES],fit.Transactions);testpred[name]=np.maximum(model.predict(test[FEATURES]),0);models[name]=model
  joblib.dump(model,artifacts/('random_forest.joblib' if name=='Random Forest' else 'xgboost.joblib'))
 result={'validation':lock['validationMetrics'],'test':{n:metric(test.Transactions,p)for n,p in testpred.items()},'selectedByValidation':lock['selectedByMay'],'selectedSettings':lock['selectedSettings'],'splitObservations':{'train':len(train),'validation':len(validation),'test':len(test)},'perBranch':{},'protocol':lock['refitPolicy'],'holdoutQualification':'June was inspected in earlier project work. This new run excludes June from tuning, but is an internal chronological holdout, not an untouched external benchmark.','metricsDefinition':{'MAE':'Average absolute error, transactions per branch-day','RMSE':'Square root of average squared error, transactions per branch-day','WAPE':'Sum of absolute errors / sum of actual transaction counts; stored as fraction'},'rounding':'Predictions remain nonnegative continuous expected counts; no post-test calibration or rounding.'}
 for split,frame,preds in [('validation',validation,valpred),('test',test,testpred)]:
  result['perBranch'][split]={}
  for branch in ['Harbour','Garden','Uptown']:
   ix=frame.Branch.eq(branch).to_numpy();result['perBranch'][split][branch]={n:metric(frame.Transactions.to_numpy()[ix],p[ix])for n,p in preds.items()}
  record=frame[['Branch','Date','Transactions','Lag7']].copy()
  for name,p in preds.items():record[name]=p
  record.to_csv(artifacts/(split+'_predictions.csv'),index=False)
 # June winner is descriptive only; deployed/saved choice stays fixed by validation.
 result['lowestJuneMAE']=min(result['test'],key=lambda n:result['test'][n]['MAE']);result['JuneMAEReductionVsNaive']={n:1-v['MAE']/result['test']['Seasonal naive']['MAE']for n,v in result['test'].items()}
 # Paired bootstrap whole dates preserves same-day correlation across branches; no extra model selection.
 selected=lock['selectedByMay'];rng=np.random.default_rng(490);indices=[np.flatnonzero(test.Date.to_numpy()==d)for d in test.Date.unique()];deltas=[]
 for _ in range(1000):
  ix=np.concatenate([indices[i]for i in rng.integers(len(indices),size=len(indices))]);y=test.Transactions.to_numpy()[ix];deltas.append(float(np.mean(abs(y-testpred['Seasonal naive'][ix])-abs(y-testpred[selected][ix]))))
 result['selectedVsNaivePairedDayBootstrap']={'replicates':1000,'metric':'Naive MAE minus validation-selected model MAE; positive favors selected','ci95':np.quantile(deltas,[.025,.975]).tolist(),'limitation':'30 June dates; assumes date clusters sufficiently independent. Cross-day serial dependence may remain.'}
 manifest={'selectedByValidation':selected,'features':FEATURES,'fitThrough':'2026-05-31','fitStart':'2026-01-08','predictionRule':'Use pipeline.predict(features), clipped at zero' if selected in models else 'Use features.Lag7','oneDayAheadOnly':True,'selectionLock':'selection_lock.json'}
 joblib.dump({'model':models.get(selected),'manifest':manifest},artifacts/'best_model.joblib');(out/'best_model_manifest.json').write_text(json.dumps(manifest,indent=2));(out/'model_results.json').write_text(json.dumps(result,indent=2))
 rows=[]
 for split,scores in [('validation',result['validation']),('test',result['test'])]:
  for name,values in scores.items():rows.append({'split':split,'branch':'ALL','model':name,**values})
  for branch,scores in result['perBranch'][split].items():
   for name,values in scores.items():rows.append({'split':split,'branch':branch,'model':name,**values})
 pd.DataFrame(rows).to_csv(out/'model_comparison.csv',index=False)
 plot_test(test,testpred)
 return result

def plot_test(test,testpred):
 figdir=R/'figures/demand_forecasting';figdir.mkdir(exist_ok=True)
 fig,axes=plt.subplots(3,1,figsize=(12,10),sharex=True)
 for ax,branch in zip(axes,['Harbour','Garden','Uptown']):
  ix=test.Branch.eq(branch).to_numpy();ax.plot(test.Date[ix],test.Transactions[ix],color='#252923',marker='o',ms=3,lw=2,label='Actual')
  for name,color in [('Seasonal naive','#c28b59'),('Random Forest','#587e99'),('XGBoost','#788752')]:ax.plot(test.Date[ix],testpred[name][ix],color=color,lw=1.4,alpha=.9,label=name)
  ax.set(title=branch,ylabel='Transactions/day');ax.grid(alpha=.2)
 axes[-1].xaxis.set_major_locator(mdates.DayLocator(interval=4));axes[-1].xaxis.set_major_formatter(mdates.DateFormatter('%b %d'));axes[-1].set_xlim(pd.Timestamp('2026-06-01'),pd.Timestamp('2026-06-30'))
 axes[0].legend(ncols=4,fontsize=9);axes[-1].set_xlabel('June 2026 · daily one-day-ahead forecasts');fig.suptitle('Actual versus predicted daily transactions · fixed May-selected configurations');fig.tight_layout();fig.savefig(figdir/'june_actual_vs_predicted.png',dpi=150);plt.close(fig)

def write_report(result,out):
 out=Path(out);rows=[]
 for name in ['Seasonal naive','Random Forest','XGBoost']:
  v=result['validation'][name];t=result['test'][name];rows.append(f"| {name} | {v['MAE']:.4f} | {v['RMSE']:.4f} | {v['WAPE']:.2%} | {t['MAE']:.4f} | {t['RMSE']:.4f} | {t['WAPE']:.2%} |")
 selected=result['selectedByValidation'];change=result['JuneMAEReductionVsNaive'][selected];ci=result['selectedVsNaivePairedDayBootstrap']['ci95']
 text=f'''### Step 7 — Daily transaction forecasting: first model comparison

Target: next-day unique recorded transactions per branch, using the eight Step 6 features. **Train: Jan 8–Apr 30 (339 rows); validation: May 1–31 (93 rows); test: June 1–30 (90 rows).** Each date stays in one partition. Predictions for May/June use observed prior-day histories as they become available, with no parameter updates during either evaluation month. This is not a June 1 forecast of the whole month.

The search was fixed in advance: **four Random Forest and four XGBoost settings**, seed 490, selected by pooled May MAE. Branch and weekday are one-hot encoded inside training-only pipelines. Numeric features pass through without scaling or imputation. After locking configurations and the overall winner on May, selected ML pipelines and preprocessing refit Jan 8–May 31, then score June. The original transaction CSV and feature CSV are unmodified.

| Model | May MAE | May RMSE | May WAPE | June MAE | June RMSE | June WAPE |
|---|---:|---:|---:|---:|---:|---:|
'''+ '\n'.join(rows)+f'''

**Selected on validation: {selected}.** Lowest June MAE (descriptive, not used to switch the choice): {result['lowestJuneMAE']}. The validation-selected method has **{abs(change):.2%} {'lower' if change>=0 else 'higher'} June MAE** than seasonal naive. MAE and RMSE are transactions per branch-day. WAPE is total absolute error divided by total transactions, not classification accuracy.

![Actual versus predicted daily transactions](../../figures/demand_forecasting/june_actual_vs_predicted.png)

#### Branch-level results

'''
 for split in ['validation','test']:
  text+=f'**{split.title()}**\n\n| Branch | Model | MAE | RMSE | WAPE |\n|---|---|---:|---:|---:|\n'
  for branch,scores in result['perBranch'][split].items():
   for name,v in scores.items():text+=f"| {branch} | {name} | {v['MAE']:.4f} | {v['RMSE']:.4f} | {v['WAPE']:.2%} |\n"
  text+='\n'
 rmse_winner=min(result['test'],key=lambda n:result['test'][n]['RMSE'])
 branch_winners={b:min(scores,key=lambda n:scores[n]['MAE']) for b,scores in result['perBranch']['test'].items()}
 text+=f"**Mixed evidence:** June RMSE is lowest for {rmse_winner}, so the MAE winner is not the winner on large-error penalties. June per-branch MAE winners are {branch_winners}. These are descriptive June comparisons; no branch-specific hybrid is selected from June. The paired-date interval {'includes zero, so this month does not establish a reliable improvement' if ci[0]<=0<=ci[1] else 'does not include zero under the stated resampling assumptions'}. Random Forest is retained in the report even if it loses to the baseline.\n\n"
 text+=f'''#### Interpretation and limits

The selected model misses by {result['test'][selected]['MAE']:.2f} transactions per branch-day on average in June, compared with {result['test']['Seasonal naive']['MAE']:.2f} for copying the same weekday last week. Better forecasts can guide staffing/preparation planning, but do not establish extra sales, dollars saved, optimum inventory or treatment effects. Transaction counts do not specify products or preparation quantities; product mix and cost/capacity information are needed before converting this target into stocking decisions.

Paired-date bootstrap 95% interval for baseline MAE minus the validation-selected model's MAE: **{ci[0]:.4f}–{ci[1]:.4f}** transactions/day (1,000 resamples, three branches kept together within each date). Only 30 June dates exist; serial dependence and explored model families limit generalization. This uncertainty summary is not used for selection.

June was already inspected during earlier EDA and separate model tasks. This run excludes June from tuning, but cannot retroactively make it an unseen external benchmark. Validate on later dates or a prospective shadow pilot. One-hot weekday is known for a forecast date; lag 1 and the rolling mean require the preceding day to have closed. No claim is made for a week-ahead forecast or disruption-specific performance.

Artifacts: [full results](../demand_forecasting/model_results.json), [all eight validation trials](../demand_forecasting/validation_search.csv), [predefined search](../demand_forecasting/search_spec.json), [selection lock](../demand_forecasting/selection_lock.json), [comparison CSV](../demand_forecasting/model_comparison.csv), [saved-model manifest](../demand_forecasting/best_model_manifest.json). The saved model bundle and row-level predictions stay in ignored `artifacts/daily_demand_models/`. Its pipeline is fit through May 31, not June. If the baseline wins, the bundle explicitly stores its Lag7 prediction rule rather than claiming an ML model won.

Reproduce: `python3 src/train_daily_models.py --data daily_demand_features.csv`. Executed notebook: `notebooks/03_ml_demand_models.ipynb`. No original transaction rows or source features are overwritten.
'''
 (out/'STEP7_REPORT.md').write_text(text)

def main(path):
 out=R/'reports/demand_forecasting';artifacts=R/'artifacts/daily_demand_models';train,validation,test=split_data(path);lock,valpred=tune(train,validation,out)
 print('VALIDATION ONLY:',json.dumps(lock,indent=2),flush=True)
 # The first use of June targets for any model score occurs after selection_lock.json exists.
 result=final_evaluation(train,validation,test,lock,valpred,out,artifacts);result['featureCSV_SHA256']=hashlib.sha256(Path(path).read_bytes()).hexdigest();(out/'model_results.json').write_text(json.dumps(result,indent=2));write_report(result,out);print('FINAL EVALUATION:',json.dumps(result,indent=2),flush=True);return result
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--data',default=str(R/'daily_demand_features.csv'));main(p.parse_args().data)
