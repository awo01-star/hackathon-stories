export function safeDiscountCeiling(price,cost,margin){if(price<=0||cost<0||margin<0||margin>=1)throw Error('Invalid economics');return 1-cost/(price*(1-margin));}
export function recomputeBundle(bundle,requestedDiscount,minMargin=.30){
 const price=bundle.items.reduce((s,i)=>s+i.price,0),cost=bundle.items.reduce((s,i)=>s+i.cost,0),ceiling=safeDiscountCeiling(price,cost,minMargin);
 if(!Number.isFinite(requestedDiscount)||requestedDiscount<0||requestedDiscount>Math.min(.12,ceiling)+1e-9)throw Error('Discount exceeds the 12% pilot limit or margin-safe ceiling');
 const salePrice=Math.ceil(price*(1-requestedDiscount)*100-1e-8)/100;
 return {...bundle,economics:{listPrice:price,cost,salePrice,grossProfit:salePrice-cost,grossMargin:(salePrice-cost)/salePrice,discount:1-salePrice/price,discountDollars:price-salePrice},discountCeiling:ceiling};
}
export function offerScenario(bundle,n,newShare,addonShare,promptCost=0){
 if(![n,newShare,addonShare,promptCost].every(Number.isFinite)||n<0||newShare<0||addonShare<0||newShare+addonShare>1+1e-9||promptCost<0)throw Error('New-basket and add-on shares must total at most 100%');
 const e=bundle.economics,drink=bundle.items[0],same=1-newShare-addonShare;
 return {deltaRevenue:n*(newShare*e.salePrice+addonShare*(e.salePrice-drink.price)-same*e.discountDollars),deltaGrossProfit:n*(newShare*e.grossProfit+addonShare*(e.grossProfit-(drink.price-drink.cost))-same*e.discountDollars)-promptCost,breakEvenNewShare:n?(e.discountDollars+promptCost/n)/(e.grossProfit+e.discountDollars):null};
}
export function simulateSlot(slot,bundles,{newShare=.25,addonShare=.25,takeup=1,promptCost=0,discount=.12,size='all'}={}){
 if(!Number.isFinite(takeup)||takeup<0||takeup>1||!Number.isFinite(promptCost)||promptCost<0)throw Error('Invalid take-up or campaign cost');
 if(newShare<0||addonShare<0||newShare+addonShare>1+1e-9)throw Error('New-basket and add-on shares must total at most 100%');
 const ids=size==='all'?slot.suggestedBundleIds:slot.alternativeBundleIds;
 const chosen=ids.map(id=>bundles.find(b=>b.id===id)).filter(b=>b&&(size==='all'||b.size===Number(size))).slice(0,slot.distinctBundles).map(b=>recomputeBundle(b,discount));
 const n=chosen.length?Math.floor(slot.redemptionCap*takeup):0;
 let deltaRevenue=0,deltaGrossProfit=0;const allocations=[];
 for(let i=0;i<chosen.length;i++){
  const count=Math.floor(n/chosen.length)+(i<n%chosen.length?1:0),b=chosen[i],s=offerScenario(b,count,newShare,addonShare,0);
  deltaRevenue+=s.deltaRevenue;deltaGrossProfit+=s.deltaGrossProfit;allocations.push({bundle:b,redemptions:count,...s});
 }
 const cost=chosen.length?promptCost:0;deltaGrossProfit-=cost;
 return {redemptions:n,allocations,deltaRevenue,deltaGrossProfit,campaignCost:cost};
}
