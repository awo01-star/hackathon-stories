export const VISUAL_CLASSES = [
 {id:'iced_matcha',label:'Iced matcha',prompt:'a photograph of an iced green matcha latte in a glass with milk and ice',products:['Iced Matcha']},
 {id:'hot_matcha',label:'Hot matcha',prompt:'a photograph of a hot green matcha latte in a ceramic cup',products:['Classic Matcha']},
 {id:'strawberry_matcha',label:'Strawberry matcha',prompt:'a photograph of a strawberry matcha latte with pink strawberry milk and green matcha layers',products:['Strawberry Matcha']},
 {id:'iced_milk_coffee',label:'Iced milk coffee',prompt:'a photograph of an iced latte, a light brown coffee with milk and ice in a glass',products:['Iced Latte','Iced Mocha']},
 {id:'hot_milk_coffee',label:'Hot milk coffee',prompt:'a photograph of a hot cappuccino or latte with creamy milk foam and latte art in a cup',products:['Cappuccino','Flat White','Vanilla Latte','Spanish Latte','Caramel Latte']},
 {id:'black_coffee',label:'Hot black coffee',prompt:'a photograph of black espresso or americano coffee in a small ceramic cup without milk',products:['Americano','Espresso']},
 {id:'iced_black_coffee',label:'Iced black coffee',prompt:'a photograph of a dark iced black coffee or cold brew in a glass with ice and no milk',products:['Iced Americano','Cold Brew']},
 {id:'fruit_drink',label:'Fruit drink',prompt:'a photograph of fresh orange juice or lemonade, a yellow or orange fruit drink in a glass',products:['Fresh Orange Juice','Lemonade']},
 {id:'tea',label:'Tea',prompt:'a photograph of a cup of brewed tea or iced tea with tea leaves or a tea bag',products:['English Breakfast Tea','Mint Tea','Peach Iced Tea','Chai Latte']},
 {id:'frappe',label:'Blended coffee',prompt:'a photograph of a blended frozen coffee frappe with whipped cream in a tall glass',products:['Coffee Frappe']},
 {id:'water',label:'Water',prompt:'a photograph of a clear glass or bottle of drinking water',products:['Still Water','Sparkling Water']},
 {id:'other',label:'Not a drink / unclear',prompt:'a photograph of a person, food, furniture or an object that is not a drink',products:[]}
];
export function interpretScores(scores) {
 const ranked=scores.map(s=>{const cls=VISUAL_CLASSES.find(c=>c.prompt===s.label);if(!cls||!Number.isFinite(s.score))throw new Error('Unrecognized model output');return {...cls,score:s.score};}).sort((a,b)=>b.score-a.score);
 if(ranked.length<2)throw new Error('Not enough model results');
 // Heuristic abstention only: these thresholds have NOT been calibrated on drink images.
 const uncertain=ranked[0].id==='other'||ranked[0].score<.22||ranked[0].score-ranked[1].score<.035;
 return {ranked,uncertain};
}
export function getPairings(catalog,branch,drink){return catalog.pairings[branch]?.[drink]??[];}
export function menuOptions(catalog,branch,ids=null){return catalog.menu.filter(p=>p.branch===branch&&['Cold Drinks','Cold Coffee','Hot Coffee','Matcha & Tea'].includes(p.category)&&(!ids||ids.includes(p.name)));}
export function money(value){return new Intl.NumberFormat('en-US',{style:'currency',currency:'USD'}).format(value);}
// Reference-photo retrieval stays independent of description-based classification.
export function cosineSimilarity(a,b){
 if(!a?.length||a.length!==b?.length)throw new Error('Embedding dimensions differ');
 let dot=0,na=0,nb=0;
 for(let i=0;i<a.length;i++){if(!Number.isFinite(a[i])||!Number.isFinite(b[i]))throw new Error('Invalid embedding');dot+=a[i]*b[i];na+=a[i]*a[i];nb+=b[i]*b[i];}
 if(!na||!nb)throw new Error('Zero embedding');return Math.max(-1,Math.min(1,dot/Math.sqrt(na*nb)));
}
export function rankReferences(query,references){
 const families=new Map();
 for(const ref of references){const cls=VISUAL_CLASSES.find(c=>c.id===ref.familyId&&c.id!=='other');if(!cls)throw new Error('Unknown reference family');const score=cosineSimilarity(query,ref.embedding);const {embedding,...metadata}=ref;const value={...cls,score,reference:metadata};if(!families.has(cls.id)||families.get(cls.id).score<score)families.set(cls.id,value);}
 const ranked=[...families.values()].sort((a,b)=>b.score-a.score);if(ranked.length<2)throw new Error('Too few reference families');
 return {ranked,uncertain:ranked[0].score<.65||ranked[0].score-ranked[1].score<.03};
}
