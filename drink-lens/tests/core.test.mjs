import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {VISUAL_CLASSES,interpretScores,getPairings,menuOptions} from '../dist/core.mjs';
const catalog=JSON.parse(readFileSync(new URL('../dist/assets/catalog.json',import.meta.url)));
const scores=(first,second,a=.6,b=.1)=>VISUAL_CLASSES.map(c=>({label:c.prompt,score:c.id===first?a:c.id===second?b:.001}));
test('abstains on non-drink, weak and ambiguous matches',()=>{
 assert.equal(interpretScores(scores('other','iced_matcha')).uncertain,true);
 assert.equal(interpretScores(scores('iced_matcha','hot_matcha',.20,.19)).uncertain,true);
 assert.equal(interpretScores(scores('iced_matcha','hot_matcha',.40,.39)).uncertain,true);
 assert.equal(interpretScores(scores('iced_matcha','hot_matcha')).uncertain,false);
});
test('rejects invalid model outputs',()=>{
 assert.throws(()=>interpretScores([{label:'injected',score:.9}]));
 assert.throws(()=>interpretScores([{label:VISUAL_CLASSES[0].prompt,score:NaN}]));
});
test('visual mapping only points to existing drinks at every branch',()=>{
 for(const branch of ['Harbour','Garden','Uptown'])for(const c of VISUAL_CLASSES)for(const name of c.products)assert(menuOptions(catalog,branch).some(p=>p.name===name),`${name} missing at ${branch}`);
});
test('pairings use branch prices, finite scores, food products, and fit cutoff',()=>{
 assert.equal(catalog.fitThrough,'2026-05-31');assert.equal(catalog.menu.length,135);
 for(const branch of Object.keys(catalog.pairings))for(const [drink,ps] of Object.entries(catalog.pairings[branch])){
  assert.equal(getPairings(catalog,branch,drink).length,3);
  assert.equal(new Set(ps.map(p=>p.product)).size,3);
  for(const p of ps){const item=catalog.menu.find(m=>m.branch===branch&&m.name===p.product);assert(item);assert.equal(p.price,item.price);assert(!['Cold Drinks','Cold Coffee','Hot Coffee','Matcha & Tea'].includes(item.category));assert(p.support<=p.baskets);assert(p.rate>=0&&p.rate<=1);assert(Number.isFinite(p.rankScore));}
 }
 assert.deepEqual(getPairings(catalog,'missing','missing'),[]);
});
test('export contains no customer or transaction identifiers',()=>{
 const text=JSON.stringify(catalog);assert(!text.includes('Transaction ID'));assert(!text.includes('Customer ID'));assert(!text.includes('SYN-'));
});
import {cosineSimilarity,rankReferences} from '../dist/core.mjs';
test('reference retrieval compares image vectors independently of prompts',()=>{
 assert.equal(cosineSimilarity([1,0],[1,0]),1);assert.equal(cosineSimilarity([1,0],[0,1]),0);
 const refs=[{familyId:'iced_matcha',embedding:[1,0],id:'matcha'},{familyId:'hot_milk_coffee',embedding:[0,1],id:'coffee'}];
 const out=rankReferences([1,0],refs);assert.equal(out.ranked[0].id,'iced_matcha');assert.equal(out.uncertain,false);assert(!('embedding' in out.ranked[0].reference));
 assert(rankReferences([1,1],refs).uncertain);assert.throws(()=>cosineSimilarity([0,0],[1,0]));assert.throws(()=>cosineSimilarity([1],[1,2]));assert.throws(()=>rankReferences([1,0],[{familyId:'made-up',embedding:[1,0]}]));
});
test('external collection is separate, attributed and mapped to real menu names',()=>{
 const manifest=JSON.parse(readFileSync(new URL('../dist/assets/references/manifest.json',import.meta.url)));assert(manifest.notStoriesProductPhotos);assert(manifest.notTrainingData);assert(manifest.references.length>=3);
 for(const r of manifest.references){assert(VISUAL_CLASSES.some(c=>c.id===r.familyId));assert.equal(r.verifiedStoriesPhoto,false);assert(r.sourcePage.startsWith('https://commons.wikimedia.org/'));assert(r.author);assert(r.license);assert(r.licenseUrl);assert.equal(r.sha256.length,64);assert(readFileSync(new URL('../dist/'+r.image.slice(2),import.meta.url)).length>1000);}
});
