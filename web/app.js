'use strict';
const $=id=>document.getElementById(id);
const el=(tag,text,cls)=>{const n=document.createElement(tag);if(text!==undefined)n.textContent=text;if(cls)n.className=cls;return n;};
let blobURLs=[];
async function api(path,body,key){
 const headers={'Authorization':'Bearer '+$('token').value};
 if(body){headers['Content-Type']='application/json';}
 if(key)headers['Idempotency-Key']=key;
 const r=await fetch(path,{method:body?'POST':'GET',headers,body:body?JSON.stringify(body):undefined});
 const d=await r.json();if(!r.ok)throw new Error(`${d.code||r.status}: ${d.detail||'Request failed'}`);return d;
}
async function submit(frame,decision,answer){
 $('error').textContent='';
 const a={dgp:'0.1',assessment_id:'a-'+crypto.randomUUID(),frame_id:frame.frame_id,
  decision_id:decision.decision_id,mode:'live',resolver:{kind:'human'},result:{status:'answered',answer}};
 await api('/dgp/assessments',a);
 const body={dgp:'0.1',frame_id:frame.frame_id,decision_id:decision.decision_id,assessment_id:a.assessment_id};
 const key='k-'+crypto.randomUUID();
 // Keep the exact request visible if the response is lost; a retry must reuse its key.
 $('result').textContent=JSON.stringify({pending_commit:body,idempotency_key:key},null,2);
 const receipt=await api('/dgp/commits',body,key);
 $('result').textContent=JSON.stringify(receipt,null,2);await refresh();
}
function safe(fn){return async()=>{try{await fn();}catch(e){$('error').textContent=e.message;}};}
async function frameCard(surface){
 const f=await api(surface.frame_href+'?disclosure='+$('disclosure').value+'&horizon=2');
 const c=el('article',undefined,'card');c.append(el('h2',surface.title),el('p',`State: ${surface.state} · ${f.policy_ref}`,'meta'));
 for(const e of f.observations){
  if(e.kind==='text'&&e.evidence_id!=='failure-log'&&e.evidence_id!=='draft')continue;
  if(e.kind==='text')c.append(el('p',e.content,'meaning'));
  if(e.kind==='image'){
   const r=await fetch(e.blob.href,{headers:{Authorization:'Bearer '+$('token').value}});
   if(!r.ok)throw new Error('Could not fetch required image evidence.');
   const bytes=await r.arrayBuffer();
   const sha=Array.from(new Uint8Array(await crypto.subtle.digest('SHA-256',bytes)),v=>v.toString(16).padStart(2,'0')).join('');
   if(bytes.byteLength!==e.blob.byte_length||sha!==e.blob.sha256)throw new Error('Image evidence failed integrity verification.');
   const u=URL.createObjectURL(new Blob([bytes],{type:e.mime_type}));blobURLs.push(u);const img=el('img');img.src=u;img.alt='User-supplied evidence';c.append(img);
  }
 }
 for(const d of f.decisions){
  const section=el('section',undefined,'decision');section.append(el('h3',d.question));
  if(d.kind==='choice'){
   const actions=el('div',undefined,'actions');
   for(const o of d.options){const b=el('button',o.label);b.title=o.meaning;b.onclick=safe(async()=>{if(o.effect.required_actor==='human'&&!confirm('Publish this exact draft to the LOCAL demo bulletin?'))return;b.disabled=true;try{await submit(f,d,{choice:o.id,input:{}});}finally{b.disabled=false;}});actions.append(b);}section.append(actions);
  }else if(d.node_id==='attach_image'){
   const file=el('input');file.type='file';file.accept='image/png,image/jpeg,image/webp';
   const b=el('button','Attach as required evidence');b.onclick=safe(async()=>{const image=file.files[0];if(!image)throw new Error('Choose an image.');if(image.size>256*1024)throw new Error('Maximum image size is 256 KiB.');const bytes=new Uint8Array(await image.arrayBuffer());let str='';for(const x of bytes)str+=String.fromCharCode(x);await submit(f,d,{value:{mime_type:image.type,data_base64:btoa(str)}});});section.append(file,b);
  }else{
   const name=d.input_schema.required[0];const input=el('textarea');input.maxLength=d.input_schema.properties[name].maxLength;
   const b=el('button','Submit text');b.onclick=safe(()=>submit(f,d,{value:{[name]:input.value}}));section.append(input,b);
  }c.append(section);
 }
 const details=el('details');details.append(el('summary','Inspect immutable decision frame'),el('pre',JSON.stringify(f,null,2)));c.append(details);return c;
}
async function refresh(){
 $('error').textContent='';for(const u of blobURLs)URL.revokeObjectURL(u);blobURLs=[];
 const {surfaces}=await api('/dgp/surfaces');const cards=await Promise.all(surfaces.map(frameCard));$('threads').replaceChildren(...cards);
 const b=await api('/dgp/bulletin');$('bulletin').replaceChildren(...b.entries.map(e=>el('article',e.text,'bullet')));
}
$('connect').onclick=safe(refresh);$('disclosure').onchange=safe(refresh);
$('graph').onclick=safe(async()=>{$('result').textContent=JSON.stringify(await api('/dgp/graphs/thread-recovery'),null,2);});
