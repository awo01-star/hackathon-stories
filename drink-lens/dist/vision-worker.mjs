import {VISUAL_CLASSES,rankReferences} from './core.mjs';
let classifier,extractor,library,referenceVectors;
const progress_callback=p=>{if(p.status==='progress')self.postMessage({type:'progress',file:p.file,loaded:p.loaded,total:p.total});};
async function runtime(){
 if(!library){library=await import('https://cdn.jsdelivr.net/npm/@huggingface/transformers@3.0.2/dist/transformers.min.js');library.env.allowLocalModels=false;library.env.backends.onnx.wasm.numThreads=1;}
 return library;
}
self.onmessage=async({data})=>{
 if(data.type!=='classify')return;
 try{
  const {pipeline}=await runtime();
  if(data.mode==='references'){
   if(classifier){await classifier.dispose();classifier=null;}
   if(!extractor){self.postMessage({type:'status',text:'Loading the vision encoder for optional reference-photo matching…'});extractor=await pipeline('image-feature-extraction','Xenova/clip-vit-base-patch32',{device:'wasm',dtype:'q8',progress_callback});}
   if(!referenceVectors){
    const response=await fetch('./assets/references/manifest.json');if(!response.ok)throw new Error('Optional reference collection is unavailable');
    const manifest=await response.json();if(manifest.kind!=='optional_external_reference_gallery'||!manifest.references?.length)throw new Error('Invalid reference collection');
    const vectors=[];
    for(const [i,ref] of manifest.references.entries()){
     self.postMessage({type:'status',text:`Reading optional reference photos · ${i+1} of ${manifest.references.length}…`});
     const tensor=await extractor(new URL(ref.image,self.location.href).href);vectors.push({...ref,embedding:Array.from(tensor.data)});
    }
    referenceVectors=vectors;
   }
   self.postMessage({type:'status',text:'Comparing your photo with the separate reference gallery…'});
   const query=await extractor(data.image);const result=rankReferences(Array.from(query.data),referenceVectors);
   self.postMessage({type:'reference_result',...result});return;
  }
  if(extractor){await extractor.dispose();extractor=null;}
  if(!classifier){
   self.postMessage({type:'status',text:'Loading the vision model. The first scan downloads model files; later scans reuse the cache.'});
   classifier=await pipeline('zero-shot-image-classification','Xenova/clip-vit-base-patch32',{device:'wasm',dtype:'q8',progress_callback});
  }
  self.postMessage({type:'status',text:'Comparing your photo with drink descriptions…'});
  const scores=await classifier(data.image,VISUAL_CLASSES.map(c=>c.prompt),{hypothesis_template:'{}'});
  self.postMessage({type:'result',scores});
 }catch(e){self.postMessage({type:'error',message:String(e.message||e)});}
};
