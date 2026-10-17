"""Assumption-based menu/stock MILP; no war response learned from transactions."""
import numpy as np
import pandas as pd
from scipy.stats import poisson
from scipy.optimize import milp,Bounds,LinearConstraint
from scipy.sparse import coo_matrix

def optimize_crisis(future,groups,scenario,menu_cap=12,budget_fraction=.8,capacity_fraction=.8):
 data=future.sort_values(['Branch','Product']).reset_index(drop=True).copy();n=len(data);names=list(data.Product);branches=list(data.Branch);price=data.price.to_numpy(float);basecost=data.cost.to_numpy(float);base=data.forecast_units.to_numpy(float)
 means=base.copy();cost=basecost*(1+scenario.get('costIncrease',0));closed=scenario.get('closedBranch');blocked=scenario.get('blockedGroup')
 means*=1-scenario.get('demandDrop',0)
 if closed:means[np.array(branches)==closed]=0
 if 'takeawayFactors' in scenario:
  for i,r in enumerate(data.itertuples()):means[i]*=scenario['takeawayFactors'].get(r.Branch,{}).get(r.Product,1.)
 max_items={b:(0 if b==closed else menu_cap)for b in sorted(set(branches))};capacity={b:int(np.floor(base[np.array(branches)==b].sum()*capacity_fraction))for b in max_items}
 resources=sorted({g for gs in groups.values()for g in gs});resource_caps={g:float(np.floor(sum(base[i]for i,p in enumerate(names)if g in groups[p])*capacity_fraction))for g in resources}
 if blocked:resource_caps[blocked]=0
 budget=float(np.sum(base*basecost)*budget_fraction)
 rng=np.random.default_rng(490);u=rng.uniform(.0001,.9999,size=(16,n));D=poisson.ppf(u,means[None,:]).astype(float);M=D.max(axis=0)
 if blocked:
  for i,p in enumerate(names):
   if blocked in groups[p]:M[i]=0
 for i,b in enumerate(branches):
  if b==closed:M[i]=0
 # x integer preparations, z binary active menu, y_s continuous sales bounded by integer stock/demand.
 S=len(D);nv=2*n+S*n;objective=np.concatenate([cost,np.zeros(n),np.tile(-price/S,S)])
 lb=np.zeros(nv);ub=np.concatenate([M,(M>0).astype(float),D.ravel()]);integrality=np.concatenate([np.ones(2*n),np.zeros(S*n)])
 ri=[];ci=[];vv=[];lower=[];upper=[]
 def constraint(pairs,hi,lo=-np.inf):
  row=len(upper)
  for col,v in pairs:ri.append(row);ci.append(col);vv.append(v)
  lower.append(lo);upper.append(hi)
 for i in range(n):constraint([(i,1),(n+i,-M[i])],0);constraint([(n+i,1),(i,-1)],0)
 for b in max_items:
  ix=[i for i,br in enumerate(branches)if br==b];constraint([(i,1)for i in ix],capacity[b]);constraint([(n+i,1)for i in ix],max_items[b])
 constraint([(i,cost[i])for i in range(n)],budget)
 for g,cap in resource_caps.items():constraint([(i,1)for i,p in enumerate(names)if g in groups[p]],cap)
 for s in range(S):
  for i in range(n):constraint([(2*n+s*n+i,1),(i,-1)],0)
 A=coo_matrix((vv,(ri,ci)),shape=(len(upper),nv)).tocsc()
 res=milp(objective,integrality=integrality,bounds=Bounds(lb,ub),constraints=LinearConstraint(A,np.array(lower),np.array(upper)),options={'time_limit':12,'mip_rel_gap':.02})
 def feasible(q):
  assert np.all(q>=0)and np.all(q<=M+1e-6)
  assert q@cost<=budget+1e-5
  for b in max_items:
   z=q[np.array(branches)==b];assert z.sum()<=capacity[b]+1e-6;assert (z>0).sum()<=max_items[b]
  for g,cap in resource_caps.items():assert sum(q[i]for i,p in enumerate(names)if g in groups[p])<=cap+1e-6
 def greedy(score):
  q=np.zeros(n);used={b:0 for b in max_items};active={b:0 for b in max_items};resources_used={g:0 for g in resource_caps};money=0
  fractile=np.clip((price-cost)/price,0,1);desired=np.quantile(D,fractile,axis=0) # diagonal gives per-item empirical quantiles
  desired=np.diag(desired) if desired.ndim==2 else desired
  for i in np.argsort(-score,kind='stable'):
   b=branches[i];goal=int(min(M[i],max(0,np.ceil(desired[i]))))
   if price[i]<=cost[i]or active[b]>=max_items[b]:continue
   for _ in range(goal):
    if used[b]+1>capacity[b]or money+cost[i]>budget+1e-8 or any(resources_used[g]+1>resource_caps[g]for g in groups[names[i]]):break
    q[i]+=1;used[b]+=1;money+=cost[i]
    for g in groups[names[i]]:resources_used[g]+=1
   if q[i]>0:active[b]+=1
  return q
 plans={'popularity_baseline':greedy(means),'margin_baseline':greedy(means*np.maximum(price-cost,0))}
 if res.x is not None:plans['optimized']=np.rint(res.x[:n])
 else:plans['optimized']=plans['margin_baseline'].copy()
 for q in plans.values():feasible(q)
 # Fresh samples assess only this assumed Poisson world, not real crisis performance.
 ueval=np.random.default_rng(491).uniform(.0001,.9999,size=(512,n));actual=poisson.ppf(ueval,means[None,:]);scores={}
 for name,q in plans.items():
  sold=np.minimum(q[None,:],actual);profit=sold@price-q@cost
  scores[name]={'expectedScenarioGP':float(profit.mean()),'scenarioGP10thPercentile':float(np.quantile(profit,.1)),'stockCost':float(q@cost),'preparedUnits':int(q.sum()),'expectedUnsoldUnits':float((q-sold).sum(axis=1).mean()),'expectedUnservedUnits':float((actual-sold).sum(axis=1).mean()),'activeMenuItems':int((q>0).sum())}
 rec=[{'branch':branches[i],'product':names[i],'units':int(q),'price':float(price[i]),'cost':float(cost[i]),'assumedGroups':groups[names[i]]}for i,q in enumerate(plans['optimized'])if q>0]
 return {'id':scenario['id'],'title':scenario['title'],'assumptions':{k:v for k,v in scenario.items()if k!='takeawayFactors'},'constraints':{'budgetUSD':budget,'capacityUnitsByBranch':capacity,'menuItemsByBranch':max_items,'resourceServingEquivalents':resource_caps},'solver':{'status':int(res.status),'message':str(res.message),'mipGap':float(res.mip_gap)if getattr(res,'mip_gap',None)is not None else None,'withinRequestedTolerance':bool(res.success),'relativeGapTolerance':.02,'fallbackUsed':res.x is None},'policies':scores,'recommendations':rec,'scenarioMeanUnits':float(means.sum()),'interpretation':'16 planning and 512 independent evaluation Poisson draws from assumed means. Recorded sales forecasts treated as unconstrained demand; no promotion response or automatic substitution. Stock is integer, terminal salvage zero, no labor/rent/transfer cost, shared serving-equivalent resources are invented and require recipes/inventory validation. Allocation is from a hypothetical shared procurement budget, not measured physical stock transfers.'}
