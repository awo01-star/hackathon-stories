import {interpretScores,menuOptions,getPairings,money} from './core.mjs';
const $=id=>document.getElementById(id);
let catalog,stream,worker,imageData=null,busy=false,timer,runId=0,started=0,visionGuess=null,confirmed=null;
let matchingMode='descriptions',referenceManifest;
const referencesEnabled=new URLSearchParams(location.search).get('references')!=='off'&&document.querySelector('meta[name="drink-lens-references"]')?.content!=='off';
const events=[],downloads=new Map();
const record=(type,data={})=>events.push({at:new Date().toISOString(),type,...data});
const show=(id,value=true)=>{$(id).hidden=!value;};
const error=text=>{$('error').textContent=text;show('error',!!text);};
const status=text=>{$('status').textContent=text;show('status-area');};
function stopCamera(){stream?.getTracks().forEach(t=>t.stop());stream=null;$('camera').srcObject=null;show('camera',false);show('capture',false);show('camera-stop',false);show('camera-open');show('camera-art',!imageData);$('finder-label').textContent='ONE DRINK. GOOD LIGHT. A CLOSER LOOK.';}
function setBusy(value){busy=value;document.body.classList.toggle('busy',value);$('scan').disabled=value||!imageData||!catalog;$('matching-modes').disabled=value;$('upload').disabled=value;$('manual-open').disabled=value;$('confirm').disabled=value;$('branch').disabled=value;$('camera-open').disabled=value;show('cancel',value);if(!value){clearTimeout(timer);show('progress',false);}}
function clearResults(){visionGuess=null;confirmed=null;show('vision-result',false);show('menu-confirm',false);show('pairing-section',false);show('basket-preview',false);show('empty-state');}
async function loadPhoto(file){
 if(busy)return;
 error('');if(!['image/jpeg','image/png','image/webp'].includes(file.type))return error('Please choose a JPG, PNG or WebP image. Convert HEIC photos to JPG first.');
 if(file.size>12*1024*1024)return error('This photo is larger than 12 MB. Please choose a smaller image.');
 const url=URL.createObjectURL(file);
 try{const img=new Image();img.src=url;await img.decode();
 if(!img.naturalWidth||img.naturalWidth*img.naturalHeight>50_000_000)throw new Error('Please choose a smaller photo (under 50 megapixels).');
 setPhoto(img,img.naturalWidth,img.naturalHeight);record('photo_selected');
 }catch(e){error(e.message||'This image could not be opened. Please try another JPG or PNG.');}finally{URL.revokeObjectURL(url);$('upload').value='';}
}
function setPhoto(source,width,height){
 const canvas=document.createElement('canvas');const scale=Math.min(1,1024/Math.max(width,height));canvas.width=Math.round(width*scale);canvas.height=Math.round(height*scale);canvas.getContext('2d').drawImage(source,0,0,canvas.width,canvas.height);imageData=canvas.toDataURL('image/jpeg',.9);
 stopCamera();clearResults();$('photo').src=imageData;show('photo');show('camera-art',false);$('source-tag').textContent='PHOTO READY';$('finder-label').textContent='READY FOR A CLOSER LOOK';$('scan').disabled=!catalog;show('status-area',false);
}
$('upload').addEventListener('change',e=>{if(e.target.files[0])loadPhoto(e.target.files[0]);});
$('camera-open').addEventListener('click',async()=>{
 error('');if(!navigator.mediaDevices?.getUserMedia)return error('Camera access needs HTTPS or localhost and a supported browser. Upload a photo instead.');
 const request=++runId;$('camera-open').disabled=true;
 try{
  const requested=await navigator.mediaDevices.getUserMedia({video:{facingMode:{ideal:'environment'},width:{ideal:1280},height:{ideal:960}},audio:false});
  if(request!==runId){requested.getTracks().forEach(t=>t.stop());return;}
  stopCamera();stream=requested;$('camera').srcObject=stream;show('camera');show('photo',false);show('camera-art',false);show('capture');show('camera-stop');show('camera-open',false);$('finder-label').textContent='FRAME ONE DRINK, THEN TAKE A PHOTO';await $('camera').play();record('camera_opened');
 }catch(e){stopCamera();show('photo',!!imageData);error(e.name==='NotAllowedError'?'Camera permission was denied. Allow camera access in your browser, or upload a photo.':'Could not open the camera. Check your camera connection, or upload a photo.');}
 finally{$('camera-open').disabled=busy;}
});
$('camera-stop').addEventListener('click',()=>{++runId;stopCamera();show('photo',!!imageData);});
$('capture').addEventListener('click',()=>{const v=$('camera');if(!v.videoWidth)return error('The camera is still starting. Please wait a moment.');setPhoto(v,v.videoWidth,v.videoHeight);record('photo_captured');});
function getWorker(){
 if(worker)return worker;
 worker=new Worker('./vision-worker.mjs',{type:'module'});
 worker.onmessage=({data})=>{
  if(!busy)return;
  if(data.type==='status')status(data.text);
  if(data.type==='progress'){
   if(Number.isFinite(data.total)&&data.total>0){downloads.set(data.file,{loaded:data.loaded,total:data.total});const entries=[...downloads.values()];const loaded=entries.reduce((a,v)=>a+v.loaded,0),total=entries.reduce((a,v)=>a+v.total,0);$('progress').max=total;$('progress').value=loaded;show('progress');status(`Downloading vision model · ${(loaded/1e6).toFixed(0)} MB of currently requested ${(total/1e6).toFixed(0)} MB. More files may follow.`);}
  }
  if(data.type==='result'||data.type==='reference_result'){
   setBusy(false);show('status-area',false);
   try{const result=data.type==='reference_result'?{ranked:data.ranked,uncertain:data.uncertain,mode:'references'}:{...interpretScores(data.scores),mode:'descriptions'};visionGuess=result.ranked[0].id;record('vision_result',{predictedFamily:visionGuess,mode:result.mode,ranked:result.ranked.slice(0,3).map(c=>({id:c.id,score:c.score})),uncertain:result.uncertain,latencyMs:Math.round(performance.now()-started)});renderVision(result);}catch(e){error('The model returned an unexpected result. You can choose your drink manually.');}
  }
  if(data.type==='error'){setBusy(false);show('status-area',false);worker?.terminate();worker=null;record('vision_error');error('The vision model could not run. Check your internet connection and available memory, then retry. You can still explore the menu manually.');console.error('Vision model error:',data.message);}
 };
 worker.onerror=()=>{setBusy(false);show('status-area',false);worker?.terminate();worker=null;error('The vision worker could not start. A browser or network restriction may be blocking it. Try a current browser or choose a drink manually.');};
 return worker;
}
$('scan').addEventListener('click',()=>{
 if(busy||!imageData||!catalog)return;
 error('');stopCamera();show('photo');clearResults();setBusy(true);started=performance.now();downloads.clear();status('Starting the vision model… First use needs an internet connection and a model download.');
 timer=setTimeout(()=>{worker?.terminate();worker=null;setBusy(false);show('status-area',false);error('The scan timed out after five minutes. Try again on a faster connection or choose your drink manually.');record('vision_timeout');},300_000);
 getWorker().postMessage({type:'classify',image:imageData,mode:matchingMode});
});
$('cancel').addEventListener('click',()=>{worker?.terminate();worker=null;setBusy(false);show('status-area',false);record('scan_cancelled');});
function renderVision({ranked,uncertain,mode='descriptions'}){
 const photoMode=mode==='references';
 show('empty-state',false);show('vision-result');$('match-label').textContent=uncertain?'LET’S TAKE A SECOND LOOK':'A POSSIBLE DRINK FAMILY';$('match-title').textContent=uncertain?'A little hard to tell.':`Looks like ${ranked[0].label.toLowerCase()}.`;
 $('match-description').textContent=uncertain?'The photo is ambiguous or may not show a drink. Try a brighter, closer photo, or choose a drink family below.':'Here are the closest visual descriptions. Choose a family, then confirm the actual Stories menu item.';
 if(photoMode){
  $('match-label').textContent='OPTIONAL REFERENCE-PHOTO MATCH';
  $('match-title').textContent=uncertain?'No clear photo match.':`Closest example: ${ranked[0].label.toLowerCase()}.`;
  $('match-description').textContent='These are the nearest outside example photos, not verified Stories products. A nearest match can still be wrong. Confirm the actual menu item.';
 }
 $('score-explanation').textContent=photoMode?'Cosine similarity measures appearance, not confidence. The small external gallery does not cover every drink.':'Similarity ranks are relative to these descriptions, not measured confidence.';
 $('visual-choices').replaceChildren();
 for(const c of ranked.filter(c=>c.id!=='other').slice(0,3)){
  const b=document.createElement('button');b.className='visual-option';const name=document.createElement('span');name.textContent=c.label;const note=document.createElement('small');note.textContent=photoMode?`Similarity ${c.score.toFixed(2)} · explore →`:'Explore matches →';if(photoMode&&c.reference){const image=document.createElement('img');image.src=c.reference.image;image.alt=`Outside reference: ${c.label}`;image.className='reference-thumb';b.append(image);}b.append(name,note);b.addEventListener('click',()=>openMenu(c.products));$('visual-choices').append(b);
 }
 if(!uncertain&&ranked[0].products.length)openMenu(ranked[0].products);
}
function openMenu(ids=null){
 if(!catalog)return error('The menu is still loading. Please retry in a moment.');
 show('empty-state',false);show('menu-confirm');const items=menuOptions(catalog,$('branch').value,ids);$('drink-select').replaceChildren();
 for(const p of items){const o=document.createElement('option');o.value=p.name;o.textContent=`${p.name} · ${money(p.price)}`;$('drink-select').append(o);}
 $('confirm').disabled=!items.length;$('menu-note').textContent=ids?'Choose the actual item. The camera cannot verify flavors or ingredients. Use “explore the menu” to see all drinks.':'Manual menu selection. This does not count as an image-recognition result.';
}
$('manual-open').addEventListener('click',()=>{error('');openMenu();record('manual_menu_opened');});
$('confirm').addEventListener('click',()=>{
 confirmed=$('drink-select').value;if(!confirmed)return;record('drink_confirmed',{branch:$('branch').value,drink:confirmed,predictedFamily:visionGuess,matchingMode,source:visionGuess?'vision-assisted':'manual'});renderPairings();
});
function renderPairings(){
 const branch=$('branch').value;const drink=menuOptions(catalog,branch).find(p=>p.name===confirmed);if(!drink)return;
 $('chosen-drink').textContent=`${drink.name} · ${money(drink.price)} · ${branch}`;$('pairings').replaceChildren();show('basket-preview',false);
 const pairings=getPairings(catalog,branch,drink.name);
 for(const [index,p] of pairings.entries()){
  const card=document.createElement('article');card.className='pairing-card';const category=document.createElement('div');category.className='category';category.textContent=`0${index+1} / ${p.category}`;const title=document.createElement('h3');title.textContent=p.product;const price=document.createElement('div');price.className='price';price.textContent=money(p.price);const detail=document.createElement('p');detail.textContent=p.support?`Seen together in ${p.support} of ${p.baskets} historical ${drink.name} baskets at ${branch}.`:'An exploratory pairing with limited co-purchase evidence.';const button=document.createElement('button');button.className='button outline';button.textContent='Preview this pairing +';button.addEventListener('click',()=>{record('pairing_previewed',{branch,drink:drink.name,product:p.product,rank:index+1});$('basket-preview').textContent=`Your pairing: ${drink.name} + ${p.product} · ${money(drink.price+p.price)} at historical menu prices. This is a preview; no order has been placed. Check current prices, availability and allergens with the store.`;show('basket-preview');});card.append(category,title,price,detail,button);$('pairings').append(card);
 }
 show('pairing-section');$('pairing-section').scrollIntoView({behavior:matchMedia('(prefers-reduced-motion: reduce)').matches?'instant':'smooth',block:'start'});$('pairing-section').focus({preventScroll:true});
}
$('branch').addEventListener('change',()=>{if(!$('menu-confirm').hidden){const previous=$('drink-select').value;openMenu();if([...$('drink-select').options].some(o=>o.value===previous))$('drink-select').value=previous;}if(confirmed)renderPairings();});
$('about-open').addEventListener('click',()=>$('about').showModal());$('about-close').addEventListener('click',()=>$('about').close());$('about').addEventListener('click',e=>{if(e.target===$('about')){const r=$('about').getBoundingClientRect();if(e.clientX<r.left||e.clientX>r.right||e.clientY<r.top||e.clientY>r.bottom)$('about').close();}});
$('export-feedback').addEventListener('click',()=>{
 const data={schemaVersion:1,app:'Stories Drink Lens',visionModel:'Xenova/clip-vit-base-patch32 q8',note:'Unverified session feedback, not a representative evaluation set or purchase log. No photos or customer IDs.',events};const blob=new Blob([JSON.stringify(data,null,2)],{type:'application/json'});const url=URL.createObjectURL(blob);const a=document.createElement('a');a.href=url;a.download='stories-drink-lens-session.json';a.click();setTimeout(()=>URL.revokeObjectURL(url),1000);
});

async function loadReferenceGallery(){
 if(!referencesEnabled)return;
 try{
  if(!referenceManifest){const response=await fetch('./assets/references/manifest.json');if(!response.ok)throw new Error('Unavailable');referenceManifest=await response.json();if(!referenceManifest.references?.length)throw new Error('Empty');}
  $('reference-grid').replaceChildren();show('reference-error',false);
  for(const ref of referenceManifest.references){
   const tile=document.createElement('div');tile.className='reference-tile';const image=document.createElement('img');image.src=ref.image;image.alt=ref.sourceTitle;image.loading='lazy';const title=document.createElement('strong');title.textContent=ref.sourceTitle;
   const credit=document.createElement('a');credit.href=ref.sourcePage;credit.target='_blank';credit.rel='noreferrer';credit.textContent=`${ref.author} · source ↗`;
   const license=document.createElement('a');license.href=ref.licenseUrl;license.target='_blank';license.rel='noreferrer';license.textContent=`${ref.license} · resized example`;
   tile.append(image,title,credit,license);$('reference-grid').append(tile);
  }
 }catch(e){$('reference-error').textContent='The optional reference gallery is unavailable. Menu descriptions still work; select that mode to continue.';show('reference-error');}
}
if(!referencesEnabled)show('reference-mode-choice',false);
for(const radio of document.querySelectorAll('input[name="matching-mode"]'))radio.addEventListener('change',()=>{
 if(busy||!radio.checked)return;
 matchingMode=radio.value==='references'&&referencesEnabled?'references':'descriptions';clearResults();error('');show('status-area',false);show('reference-gallery',matchingMode==='references');
 $('mode-description').textContent=matchingMode==='references'?'Optional image-to-image comparison with separate outside photos. The transaction CSV stays unchanged.':'Matches drink descriptions to the original menu names. The transaction CSV stays unchanged.';
 record('matching_mode_changed',{mode:matchingMode});if(matchingMode==='references')loadReferenceGallery();
});

window.addEventListener('pagehide',()=>{++runId;stopCamera();worker?.terminate();});
try{const response=await fetch('./assets/catalog.json');if(!response.ok)throw new Error('Menu unavailable');catalog=await response.json();$('scan').disabled=!imageData;}
catch(e){error('The menu could not load. Please reload this page.');$('manual-open').disabled=true;}
