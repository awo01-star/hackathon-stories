import {simulateSlot} from './bundle-core.mjs';
import {money} from './core.mjs';
const $=id=>document.getElementById(id);let plan,currentHour;
const pct=n=>(n*100).toFixed(1)+'%';
const hours=h=>String(h).padStart(2,'0')+':00';
function slots(){return plan.slots.filter(s=>s.branch===$('plan-branch').value);}
function selected(){return slots().find(s=>s.hour===currentHour);}
function assumptions(){return {newShare:Number($('new-share').value)/100,addonShare:Number($('addon-share').value)/100,takeup:Number($('takeup').value)/100,promptCost:Number($('campaign-cost').value),discount:Number($('bundle-discount').value),size:$('bundle-size').value};}
function text(id,v){$(id).textContent=v;}
function signed(n){return(n>=0?'+':'−')+money(Math.abs(n));}
function node(tag,value,className){const e=document.createElement(tag);if(value!==undefined)e.textContent=value;if(className)e.className=className;return e;}
function renderBranch(){
 const ss=slots();if(!ss.some(s=>s.hour===currentHour))currentHour=(ss.find(s=>s.redemptionCap>0)||ss[0]).hour;
 text('day-revenue',money(ss.reduce((a,s)=>a+s.forecastRevenue,0)));text('offer-hours',`${ss.filter(s=>s.redemptionCap>0).length} / ${ss.length}`);text('day-cap',ss.reduce((a,s)=>a+s.redemptionCap,0));
 const max=Math.max(...ss.map(s=>s.forecastTransactions),1);$('hour-chart').replaceChildren();
 for(const s of ss){const b=node('button',undefined,'hour-bar'+(s.redemptionCap?' eligible':''));b.type='button';b.setAttribute('aria-pressed',String(s.hour===currentHour));b.setAttribute('aria-label',`${hours(s.hour)}, ${s.forecastTransactions.toFixed(1)} forecast transactions, cap ${s.redemptionCap}`);const bar=node('span');bar.style.height=`${Math.max(3,s.forecastTransactions/max*145)}px`;b.append(node('b',s.forecastTransactions.toFixed(1)),bar,node('small',String(s.hour).padStart(2,'0')));b.onclick=()=>{currentHour=s.hour;renderBranch();};$('hour-chart').append(b);}
 renderSlot();
}
function renderSlot(){
 const s=selected();text('slot-title',`${s.branch} · ${hours(s.hour)}–${hours(s.hour+1)}`);text('slot-summary',`${s.forecastTransactions.toFixed(1)} forecast transactions · ${s.distinctBundles} suggested choices · ${s.redemptionCap} redemption cap`);text('slot-reason',s.redemptionCap?`${s.reason}. Pressure ${s.pressure.toFixed(2)}; no offer runs when pressure reaches 1.`:`No offer scheduled. ${s.reason}. Low-volume slots may also round down to a zero cap.`);
 renderScenario();
}
function renderScenario(){
 const s=selected(),a=assumptions();text('new-output',pct(a.newShare));text('addon-output',pct(a.addonShare));text('takeup-output',pct(a.takeup));
 try{
  const result=simulateSlot(s,plan.bundles[s.branch],a);$('scenario-error').hidden=true;$('bundle-cards').replaceChildren();
  if(!result.allocations.length)$('bundle-cards').append(node('p','No bundles for this selection. Keep the busy hour at full price, choose a quieter slot, or select another bundle size.','no-offers'));
  for(const allocation of result.allocations){const b=allocation.bundle,e=b.economics,card=node('article',undefined,'bundle-card');card.append(node('div',`${b.size} ITEMS · ${pct(e.discount)} EFFECTIVE DISCOUNT`,'tag'),node('h3',b.items.map(i=>i.name).join(' + ')));const price=node('div',money(e.salePrice),'bundle-price');price.append(node('del',money(e.listPrice)));card.append(price);const facts=node('div',undefined,'bundle-facts');for(const [label,value] of [['Unit cost',money(e.cost)],['Unit GP',money(e.grossProfit)],['Gross margin',pct(e.grossMargin)]]){const fact=node('div',value);fact.append(node('small',label));facts.append(fact);}card.append(facts,node('p',`${allocation.redemptions} assumed redemptions in this hour. ${b.support} complete co-purchase baskets in Jan–May; unadjusted lift ${b.lift.toFixed(2)}. Lift is descriptive and not proof of promotion demand.`),node('p',`Margin-safe ceiling at 30% GP margin: ${pct(b.discountCeiling)}. Pilot discount limit: 12%. Price rounds upward to the next cent.`));$('bundle-cards').append(card);}
  const baseGP=s.forecastRevenue*plan.historicalGrossMargin[s.branch];text('without-revenue',money(s.forecastRevenue));text('with-revenue',money(s.forecastRevenue+result.deltaRevenue));text('without-profit',money(baseGP));text('with-profit',money(baseGP+result.deltaGrossProfit));text('delta-revenue',signed(result.deltaRevenue));text('delta-profit',signed(result.deltaGrossProfit));$('delta-profit').className=result.deltaGrossProfit>=0?'positive':'negative';
  if(result.redemptions){const discountLoss=result.allocations.reduce((v,r)=>v+r.redemptions*r.bundle.economics.discountDollars,0),regularGP=result.allocations.reduce((v,r)=>v+r.redemptions*(r.bundle.economics.listPrice-r.bundle.economics.cost),0),threshold=(discountLoss+result.campaignCost)/regularGP;text('break-even',`${result.redemptions} assumed redemptions. Conservative break-even: ${pct(threshold)} must be truly new baskets if all other redemptions would buy the full bundle anyway (no add-on benefit). ${threshold>1?'This cannot break even under that assumption.':''}`);}
  else text('break-even','No assumed redemptions. No sales benefit is credited. Any scheduled campaign cost still applies.');
 }catch(e){text('scenario-error',e.message);$('scenario-error').hidden=false;for(const id of ['with-revenue','with-profit','delta-revenue','delta-profit'])text(id,'—');text('break-even','Correct the assumptions to calculate a scenario.');}
}
function evidence(){
 for(const target of ['transactions','revenue']){const m=plan.metrics[target],block=node('article');block.append(node('h3',target==='transactions'?'Hourly transactions':'Hourly revenue'));const table=node('table',undefined,'evidence-table');const head=node('tr');for(const label of ['June test','MAE ↓','WAPE ↓'])head.append(node('th',label));const thead=node('thead');thead.append(head);const body=node('tbody');for(const [name,v] of Object.entries(m.test)){const row=node('tr');row.append(node('td',name),node('td',target==='revenue'?money(v.mae):v.mae.toFixed(2)),node('td',pct(v.wape)));body.append(row);}table.append(thead,body);block.append(table,node('p',`Chosen for planning on May: ${m.selectedForPlanning}. Best baseline: ${m.bestBaseline}. June baseline MAE − ML MAE interval (positive favors ML): ${m.pairedDayBootstrapMAEImprovementCI95.map(v=>v.toFixed(3)).join(' to ')}. ${m.testCells} June slots.`));$('model-evidence').append(block);}
}
for(const id of ['new-share','addon-share','takeup','campaign-cost','bundle-discount','bundle-size'])$(id).addEventListener('input',()=>{if(plan)renderScenario();});
$('plan-branch').onchange=()=>{if(plan){currentHour=undefined;renderBranch();}};
$('download-plan').onclick=()=>{try{const a=assumptions();const data={note:'Historical demonstration. Scenario outcomes are assumptions, not predicted treatment effects. No live offers created.',asOf:plan.asOf,planningDate:plan.planningDate,branch:$('plan-branch').value,assumptions:a,slots:slots().map(s=>({...s,scenario:simulateSlot(s,plan.bundles[s.branch],a)}))};const url=URL.createObjectURL(new Blob([JSON.stringify(data,null,2)],{type:'application/json'}));const link=node('a');link.href=url;link.download=`stories-offer-plan-${plan.planningDate}-${data.branch}.json`;link.click();setTimeout(()=>URL.revokeObjectURL(url),1000);}catch(e){text('scenario-error',e.message);$('scenario-error').hidden=false;}};
try{const r=await fetch('./assets/bundle-plan.json');if(!r.ok)throw Error('Could not load the offer plan. Reload to retry.');plan=await r.json();text('demo-note',`HISTORICAL DEMO · Plan for ${plan.planningDate}, using records through ${plan.asOf}. This is not a current offer, live menu or measured revenue-uplift result.`);text('planning-date',plan.planningDate);$('planner').hidden=false;evidence();renderBranch();}catch(e){text('fatal',e.message);$('fatal').hidden=false;}
