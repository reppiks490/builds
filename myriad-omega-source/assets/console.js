'use strict';
const $=s=>document.querySelector(s);
const el=(tag,cls,txt)=>{const n=document.createElement(tag);if(cls)n.className=cls;if(txt!=null)n.textContent=txt;return n};
const app={state:null,models:null,selected:'W01',filter:'all',search:'',motion:!matchMedia('(prefers-reduced-motion: reduce)').matches,
           ready:false,focus:false,activeJob:null,workflowNodes:[],taskPoll:null};
const fmt=n=>Number(n||0).toLocaleString('en-US');
const colors=['#e49c75','#75bedc','#d5af7f','#a98aee','#81cdad','#d98ba9','#9cc7e7','#d9ac7b'];
function safeText(s){return typeof s==='string'?s:JSON.stringify(s)}
async function request(url,body){
 const opts=body===undefined?{}:{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(body)};
 let r=await fetch(url,opts);let j=await r.json();if(!r.ok)throw new Error(j.error||'Request failed');return j;
}
function currentWorkflow(){return app.state?.workflows.find(w=>w.id===app.selected)}
function renderWorkflows(){
 const list=$('#workflowList');list.replaceChildren();
 for(const w of app.state?.workflows||[]){
  if(app.filter!=='all'&&w.domain!==app.filter)continue;
  if(app.search&&!`${w.id} ${w.name} ${w.domain} ${w.objective}`.toLowerCase().includes(app.search))continue;
  const b=el('button','flow-item'+(w.id===app.selected?' active':''));b.type='button';b.setAttribute('aria-current',w.id===app.selected?'true':'false');
  b.append(el('span','flow-index',w.id),el('span','flow-icon',['⌁','◈','✦','◇','∴','⌘','△','✧'][Number(w.id.slice(1))%8]));
  const t=el('span','flow-text');t.append(el('span','flow-name',w.name.toUpperCase()),el('span','flow-domain',w.domain+' · '+fmt(w.initial_agents||100)+' agents'));
  b.append(t,el('span','flow-arrow','›'));b.addEventListener('click',()=>selectWorkflow(w.id));list.append(b);
 }
 if(!list.children.length)list.append(el('p','notice','No matching workflow.'));
}
function selectWorkflow(id){
 if(!app.state?.workflows.some(w=>w.id===id))return;
 app.selected=id;const w=currentWorkflow();$('#selectedId').textContent=w.id;$('#selectedName').textContent=w.name.toUpperCase();
 $('#selectedObjective').textContent=w.objective;$('#selectedDeliverable').textContent=w.deliverable;
 $('#sceneHover').textContent=`SELECTED · ${w.id} · ${w.name.toUpperCase()}`;
 renderWorkflows();
}
function renderState(s){
 app.state=s;const dep=s.deployment||{};const count=dep.ready_actors||0;$('#actorLive').innerHTML=`${fmt(count)} <em>/ ${fmt(s.agent_total)}</em>`;$('#sceneActors').textContent=`${fmt(count)} / ${fmt(s.agent_total)}`;$('#actorCaption').textContent=dep.all_actors_ready?'IN-PROCESS FLEET READY':'ACTORS NOT FULLY STARTED';$('#meshStatus').textContent=dep.all_actors_ready?`${fmt(count)} LIVE IN-PROCESS WORKERS · ${dep.active_jobs||0} EXECUTING · ${dep.queued_mailboxes||0} MAILBOX QUEUED · MODEL SLOTS ${dep.max_parallel_model_pipelines||0}`:'Actor fleet unavailable; start the MYRIAD server to deploy workers.';$('#missionCount').textContent=fmt(s.jobs_total);
 $('#missionCaption').textContent=`${s.job_states.completed||0} completed · ${s.job_states.running||0} running`;
 renderWorkflows();selectWorkflow(app.selected);
 const feed=$('#events');feed.replaceChildren();for(const e of s.events.slice(0,17)){
   const row=el('div','event');const stamp=new Date(e.at).toLocaleTimeString([],{hour:'2-digit',minute:'2-digit',second:'2-digit'});
   row.append(el('span','event-time',stamp),el('span','event-kind',e.category),el('span','event-message',e.message));feed.append(row);
 }
}
function renderModels(m){
 app.models=m.brains;const online=Object.values(m.brains).filter(x=>x.status==='ready').length;
 app.ready=online===5;$('#brainOnline').innerHTML=`${online} <em>/ 5</em>`;$('#sceneConnectivity').textContent=`${online} / 5`;
 const banner=$('#globalStatus');banner.textContent=app.ready?'FIVE BRAINS CONNECTED':`${online} / 5 MODELS READY`;
 banner.closest('.status-pill').classList.toggle('online',app.ready);
 $('#footerMode').textContent=app.ready?'LIVE MODEL ROUTES READY':'OFFLINE MODEL ROUTES';
 const providers=$('#providers');providers.replaceChildren();
 for(const brain of ['NOESIS','MNEMOSYNE','PRAXIS','AEGIS','METIS']){
  const m=app.models[brain];const name=brain.toLowerCase();
  $('#'+name+'Status').textContent=m.status.toUpperCase();$('#'+name+'Status').classList.toggle('ready',m.status==='ready');
  $('#'+name+'Model').textContent=(m.backend||'unavailable')+' · '+(m.model||'not configured');
  const row=el('div','provider');const l=el('div');l.append(el('div','provider-name',brain),el('div','provider-detail',m.model||m.message||'No model found'));
  row.append(l,el('div','provider-state'+(m.status==='ready'?' ready':''),m.status.toUpperCase()));providers.append(row);
 }
 $('#submitMission').disabled=!app.ready;$('#commandNotice').textContent=app.ready?
  'All five model routes are ready. Submission will make five actual model requests and record their responses. No proposed actions are executed.':
  'Model inference is OFFLINE. Install/pull Ollama models or configure approved model endpoints. Deterministic samples are still available.';
}
function note(text){$('#commandNotice').textContent=text}
function outputText(title,message){const area=$('#taskOutput');area.replaceChildren();area.append(el('h4',null,title),el('pre',null,message))}
async function loadState(){try{renderState(await request('/api/state'))}catch(e){note('State unavailable: '+e.message)}}
async function loadFleetTraining(){
 try{
  const x=await request('/api/training/fleet');
  $('#agentWeightsTrained').textContent=fmt(x.gradient_trained_ledger_rows)+' / '+fmt(x.agents_target);
  $('#agentWeightsCaption').textContent=x.status==='bank_missing'?'No individual weight bank installed':
    `${fmt(x.gradient_steps_ledger)} stored gradient steps · ${x.status} · full byte audit pending`;
 }catch(e){$('#agentWeightsTrained').textContent='unavailable';$('#agentWeightsCaption').textContent=e.message}
}
async function loadModels(){try{renderModels(await request('/api/models'))}catch(e){note('Model inspection failed: '+e.message)}}
async function runSample(){
 $('#runSample').disabled=true;
 try{let x=await request('/api/evaluate',{workflow:app.selected});outputText('LOCAL DETERMINISTIC EXAMPLE / '+app.selected,JSON.stringify(x,null,2));note('Real local algorithm completed. This sample did not call an LLM or operate tools.');}
 catch(e){note(e.message)}finally{$('#runSample').disabled=false}
}
async function submitTask(){
 const objective=$('#missionText').value.trim();if(objective.length<5)return note('Provide a mission of at least 5 characters.');
 $('#submitMission').disabled=true;
 try{
  const job=await request('/api/tasks',{workflow:app.selected,objective});app.activeJob=job.id;
  outputText('MISSION '+job.id,`Agent ${job.agent} assigned to ${job.workflow}. Five-brain execution queued.`);
  note('Live request accepted. Five brain outputs will appear as the actual model responses arrive.');
  if(app.taskPoll)clearInterval(app.taskPoll);
  app.taskPoll=setInterval(async()=>{
   try{const x=await request('/api/tasks/'+job.id);displayTask(x);
    if(x.state==='completed'||x.state==='failed'){
      clearInterval(app.taskPoll);app.taskPoll=null;await loadState();$('#submitMission').disabled=!app.ready;
    }
   }catch(e){note('Mission status error: '+e.message)}
  },1800);
 }catch(e){note(e.message);$('#submitMission').disabled=!app.ready}
}
function displayTask(job){
 const area=$('#taskOutput');area.replaceChildren();area.append(el('h4',null,`${job.id} / ${job.state.toUpperCase()} / ${job.agent}`));
 if(job.error)area.append(el('p',null,'Provider failure: '+job.error));
 for(const brain of ['NOESIS','MNEMOSYNE','PRAXIS','AEGIS','METIS']){
  const r=job.brain_results?.[brain];if(!r)continue;
  const d=el('details');if(brain==='AEGIS')d.open=true;
  d.append(el('summary',null,brain+' · EVIDENCE '+r.digest),el('pre',null,r.answer));area.append(d);
 }
 if(job.state==='running'||job.state==='queued')area.append(el('p',null,'Processing real model calls…'));
}
// Reproducible visual-only particle orbital field: individual stars signify agent identities.
const c=$('#nexus'),ctx=c.getContext('2d',{alpha:true});
let cw=800,ch=470,dpr=1,frame=0,last=0,seed=17011;
const rand=()=>{seed=(Math.imul(seed,1664525)+1013904223)>>>0;return seed/4294967296};
const parts=Array.from({length:10000},(_,i)=>({sector:Math.floor(i/100),ang:rand()*Math.PI*2,r:.25+rand()*.75,vel:.3+rand()*.65,brightness:.2+rand()*.8}));
function resize(){let b=c.getBoundingClientRect();cw=b.width||800;ch=b.height||470;dpr=Math.min(devicePixelRatio||1,2);c.width=Math.round(cw*dpr);c.height=Math.round(ch*dpr);ctx.setTransform(dpr,0,0,dpr,0,0)}
function sectors(t){
 const cx=cw*.5,cy=ch*.5,r=Math.min(cw*.44,ch*.46);const nodes=[];
 for(let i=0;i<100;i++){
  let outer=i>=50;let k=i%50;let th=k*Math.PI*2/50-Math.PI/2 + (outer?.24:-.13)+(app.motion?t*(outer?-.004:.003):0);
  let rad=r*(outer?.97:.73);let x=cx+Math.cos(th)*rad,y=cy+Math.sin(th)*rad*.75;
  nodes.push({id:`W${String(i+1).padStart(2,'0')}`,x,y,r:outer?7:6,index:i});
 }
 return nodes;
}
function line(a,b,alpha=.5,width=1,color='#9fb4c2'){
 ctx.strokeStyle=color;ctx.globalAlpha=alpha;ctx.lineWidth=width;ctx.beginPath();ctx.moveTo(a.x,a.y);ctx.lineTo(b.x,b.y);ctx.stroke();ctx.globalAlpha=1;
}
function draw(t){
 if(!app.motion&&frame>2)return;frame++;const cx=cw*.5,cy=ch*.5,r=Math.min(cw*.44,ch*.46);
 ctx.clearRect(0,0,cw,ch);ctx.save();
 let shade=ctx.createRadialGradient(cx,cy,1,cx,cy,r*1.22);shade.addColorStop(0,'#27304077');shade.addColorStop(.5,'#111a2388');shade.addColorStop(1,'#04070b00');ctx.fillStyle=shade;ctx.fillRect(0,0,cw,ch);
 // Isometric reference rings + nested geometry
 for(let i=0;i<6;i++){
  ctx.beginPath();ctx.ellipse(cx,cy,r*(.3+.14*i),r*(.3+.14*i)*.75,-.13,0,Math.PI*2);
  ctx.strokeStyle=i===4?'#6d625d':'#2f3948';ctx.globalAlpha=i===4?.48:.44;ctx.lineWidth=i===4?1.15:.7;ctx.stroke();
 }
 ctx.globalAlpha=1;ctx.setLineDash([2,8]);line({x:cx-r,y:cy},{x:cx+r,y:cy},.19,.6);line({x:cx,y:cy-r},{x:cx,y:cy+r},.19,.6);ctx.setLineDash([]);
 const sn=sectors(t);app.workflowNodes=sn;
 const brains=[
 {x:cx,y:cy-r*.32,color:'#72d8f5',name:'N'},
 {x:cx+r*.30,y:cy-r*.07,color:'#b0bdfb',name:'M'},
 {x:cx+r*.19,y:cy+r*.27,color:'#edac78',name:'P'},
 {x:cx-r*.19,y:cy+r*.27,color:'#eb8db2',name:'A'},
 {x:cx-r*.30,y:cy-r*.07,color:'#c2e7a3',name:'T'}];
 // fan connections, higher emphasis for selected sector
 for(let i=0;i<100;i++){
  const b=brains[i%5],node=sn[i],sel=node.id===app.selected;
  if(sel||i%3===0)line(b,node,sel?.55:.09,sel?1.4:.6,sel?'#e9ad7e':'#79a1b3');
 }
 // Each star is one logical agent identity. This motion is topology visualization, NOT inference.
 const mobile=cw<520;let count=mobile?3000:10000;
 for(let i=0;i<count;i++){
  let p=parts[i],s=sn[p.sector],active=s.id===app.selected;
  let angle=p.ang+t*.025*p.vel*(p.sector%2?1:-1);
  let rad=(mobile?5:7)+p.r*(mobile?10:17),px=s.x+Math.cos(angle)*rad,py=s.y+Math.sin(angle)*rad*.74;
  const alpha=(active?.70:.17)+p.brightness*(active?.2:.14);
  ctx.fillStyle=colors[p.sector%colors.length];ctx.globalAlpha=alpha;
  ctx.fillRect(px,py,active?1.55:.85,active?1.55:.85);
 }
 ctx.globalAlpha=1;
 // Planetary workflow nodes
 for(let i=0;i<100;i++){
  const n=sn[i],sel=n.id===app.selected;
  if(sel){ctx.beginPath();ctx.arc(n.x,n.y,19+2*Math.sin(t*.08),0,Math.PI*2);ctx.strokeStyle='#f2b681';ctx.globalAlpha=.45;ctx.lineWidth=1;ctx.stroke();ctx.globalAlpha=1}
  ctx.beginPath();ctx.arc(n.x,n.y,sel?6.5:3.8,0,Math.PI*2);ctx.fillStyle=sel?'#f1c9a5':'#bac8d4';ctx.globalAlpha=sel?1:.77;ctx.fill();ctx.globalAlpha=1;
  if(sel||i%7===0){ctx.font='8px Consolas,monospace';ctx.fillStyle=sel?'#fbd6ae':'#95a5b6';ctx.fillText(n.id,n.x+9,n.y-8)}
 }
 // Golden armillary brain council, connected triangle
 for(let i=0;i<5;i++)line(brains[i],brains[(i+1)%5],.8,1.5,'#dcb18c');
 for(const b of brains){
  const rad=16+Math.sin(t*.065)*2;
  ctx.beginPath();ctx.arc(b.x,b.y,rad+9,0,Math.PI*2);ctx.strokeStyle=b.color;ctx.globalAlpha=.15;ctx.lineWidth=5;ctx.stroke();ctx.globalAlpha=1;
  ctx.beginPath();ctx.arc(b.x,b.y,rad,0,Math.PI*2);ctx.fillStyle='#10151d';ctx.strokeStyle=b.color;ctx.lineWidth=1.4;ctx.fill();ctx.stroke();
  ctx.font='bold 13px Georgia,serif';ctx.textAlign='center';ctx.textBaseline='middle';ctx.fillStyle=b.color;ctx.fillText(b.name,b.x,b.y);ctx.textAlign='start';ctx.textBaseline='alphabetic';
 }
 // Small light waves over the five-brain pentagon (visual only)
 let phase=(t*.008)%1;for(let i=0;i<5;i++){
  let a=brains[i],b=brains[(i+1)%5],x=a.x+(b.x-a.x)*phase,y=a.y+(b.y-a.y)*phase;
  ctx.beginPath();ctx.arc(x,y,2,0,Math.PI*2);ctx.fillStyle='#fff0d1';ctx.globalAlpha=.8;ctx.fill();ctx.globalAlpha=1;
 }
 ctx.restore();
}
function loop(ms){if(ms-last>=16){draw(ms*.018);last=ms}requestAnimationFrame(loop)}
function nearestFlow(ev){let r=c.getBoundingClientRect(),x=ev.clientX-r.left,y=ev.clientY-r.top,best=null,dist=24;
 for(let n of app.workflowNodes){let d=Math.hypot(n.x-x,n.y-y);if(d<dist){dist=d;best=n}}
 return best;
}
c.addEventListener('click',e=>{let n=nearestFlow(e);if(n)selectWorkflow(n.id)});
c.addEventListener('mousemove',e=>{const n=nearestFlow(e);c.style.cursor=n?'pointer':'default';if(n){const w=app.state?.workflows.find(w=>w.id===n.id);$('#sceneHover').textContent=w?`${w.id} · ${w.name.toUpperCase()} / CLICK TO SELECT`:n.id;}});
$('#toggleMotion').addEventListener('click',()=>{app.motion=!app.motion;$('#toggleMotion').textContent=app.motion?'Ⅱ   PAUSE VISUALS':'▷   RESUME VISUALS';$('#toggleMotion').setAttribute('aria-pressed',app.motion?'true':'false');if(!app.motion)frame=3;else frame=0;});
$('#focusSelected').addEventListener('click',()=>{const n=app.workflowNodes.find(x=>x.id===app.selected);$('#sceneHover').textContent=n?`${n.id} · SELECTED SECTOR · ${currentWorkflow()?.name.toUpperCase()}`:'No sector';frame=0;});
$('#workflowSearch').addEventListener('input',e=>{app.search=e.target.value.trim().toLowerCase();renderWorkflows()});
document.querySelectorAll('.filter').forEach(b=>b.addEventListener('click',()=>{app.filter=b.dataset.domain;document.querySelectorAll('.filter').forEach(x=>x.classList.toggle('active',x===b));renderWorkflows()}));
$('#runSample').addEventListener('click',runSample);$('#submitMission').addEventListener('click',submitTask);
$('#refreshModels').addEventListener('click',loadModels);
$('#agentInspect').addEventListener('click',async()=>{
 const a=$('#agentLookup').value.trim().toUpperCase();
 try{
  const x=await request('/api/agents/'+encodeURIComponent(a));
  $('#agentRecord').textContent=`${x.id} · ${x.workflow} · ${x.status}\nACTOR: ${x.runtime.actor_alive?'LIVE':'OFFLINE'} · MAILBOX: ${x.runtime.mailbox_depth||0}\nSHARED CAPABILITIES: ${x.capabilities.length} · PUPIL SLOTS: ${x.pupil_slots}\nRECENT MISSIONS: ${x.recent_jobs.map(j=>j.id+' '+j.state).join(', ')||'none'}`;
  const t=await request('/api/training/agents/'+encodeURIComponent(a));
  $('#agentWeightRecord').textContent=`WEIGHT BANK: ${t.status.toUpperCase()} · ${fmt(t.parameters)} parameters\nGRADIENT STEPS: ${t.gradient_steps||0} · CHECKSUM: ${t.byte_hash_verified?'VERIFIED':t.status==='reserved_not_initialized'?'NOT INITIALIZED':'FAILED'}\nEVIDENCE: ${t.training_scope} · NOT FOUNDATION-LLM FINETUNING`;
 }catch(e){$('#agentRecord').textContent=e.message;$('#agentWeightRecord').textContent='Weight telemetry unavailable';}
});
window.addEventListener('resize',()=>{resize();frame=0});
resize();requestAnimationFrame(loop);
loadState();loadModels();loadFleetTraining();setInterval(loadState,5000);setInterval(loadModels,20000);setInterval(loadFleetTraining,9000);

async function refreshAbilitySummary(){
 try{const s=await request('/api/abilities/summary');$('#abilityTrained').textContent=fmt(s.trained_synthetic)+' / '+fmt(s.abilities_reserved);}
 catch(e){$('#abilityTrained').textContent='UNAVAILABLE';}
}
async function inspectAbility(){
 const id=$('#abilityLookup').value.trim();
 if(!/^CAP-\d{8}$/.test(id)){ $('#abilityRecord').textContent='Use CAP- followed by eight digits.';return; }
 try{const a=await request('/api/abilities/'+encodeURIComponent(id));$('#abilityRecord').textContent=JSON.stringify(a,null,2);}
 catch(e){$('#abilityRecord').textContent=e.message;}
}
$('#abilityInspect').addEventListener('click',inspectAbility);
$('#abilityLookup').addEventListener('keydown',e=>{if(e.key==='Enter')inspectAbility();});
refreshAbilitySummary();setInterval(refreshAbilitySummary,60000);

async function inspectPipeline(){
 const id=$('#pipelineLookup').value.trim().toUpperCase();
 if(!/^P\d{4}$/.test(id)){$('#pipelineRecord').textContent='Use P followed by four digits.';return;}
 try{const x=await request('/api/pipelines/'+encodeURIComponent(id));
  $('#pipelineRecord').textContent=JSON.stringify(x,null,2);
 }catch(e){$('#pipelineRecord').textContent=e.message}
}
$('#pipelineInspect').addEventListener('click',inspectPipeline);
$('#pipelineLookup').addEventListener('keydown',e=>{if(e.key==='Enter')inspectPipeline()});

async function runPolicySample(){
 const a=$('#agentLookup').value.trim().toUpperCase();
 if(!/^AG-\d{5}$/.test(a))return $('#agentPolicyRecord').textContent='Invalid agent ID';
 try{const r=await request('/api/training/policy/'+encodeURIComponent(a));
 $('#agentPolicyRecord').textContent=`${r.agent} / ${r.chosen_synthetic_action.toUpperCase()}\nMODEL: ${fmt(r.agent_specific_parameters)} trained parameters · ${r.gradient_steps_in_ledger} recorded gradient steps\nSCORES: ${r.action_scores.join(', ')}\nNO REAL TASK OR MODEL-LANGUAGE INFERENCE`;}
 catch(e){$('#agentPolicyRecord').textContent='Policy unavailable: '+e.message;}
}
$('#runPolicySample').addEventListener('click',runPolicySample);

async function refreshAdaptiveMemory(){
 try{const d=await request('/api/adaptation/summary');
  $('#adaptiveSummary').textContent=`${fmt(d.stored_candidate_count)} quarantined candidate adaptations across ${fmt(d.agents_with_memory)} agents. Auto-promotions: 0. All evidence is synthetic.`;
 }catch(e){$('#adaptiveSummary').textContent='Adaptive telemetry unavailable: '+e.message;}
}
async function inspectAdaptiveMemory(){
 const a=$('#adaptiveAgent').value.trim().toUpperCase();
 if(!/^AG-\d{5}$/.test(a))return $('#adaptiveRecord').textContent='Invalid agent ID';
 try{const d=await request('/api/adaptation/agents/'+encodeURIComponent(a));
  $('#adaptiveRecord').textContent=JSON.stringify(d,null,2);
 }catch(e){$('#adaptiveRecord').textContent=e.message;}
}
$('#adaptiveInspect').addEventListener('click',inspectAdaptiveMemory);
refreshAdaptiveMemory();setInterval(refreshAdaptiveMemory,30000);

// Immutable, untrusted model evidence memory. Read only: never auto-fed into prompts.
async function refreshEvidenceVault(){
 try {const s=await request('/api/memory/summary');
 $('#evidenceSummary').textContent=`${fmt(s.observations)} model observations · ${fmt(s.agents_with_observations)} agents · ${fmt(s.jobs)} jobs · 0 trusted claims / 0 auto-promotions. Hash chain only proves local integrity.`;
 } catch(e){$('#evidenceSummary').textContent='Evidence service unavailable: '+e.message;}
}
async function inspectEvidenceVault(){
 const a=$('#evidenceAgent').value.trim().toUpperCase();
 if(!/^AG-\d{5}$/.test(a))return $('#evidenceRecord').textContent='Invalid agent ID';
 try{const r=await request('/api/memory/agents/'+encodeURIComponent(a));
  $('#evidenceRecord').textContent=JSON.stringify(r,null,2);
 }catch(e){$('#evidenceRecord').textContent=e.message;}
}
$('#evidenceInspect').addEventListener('click',inspectEvidenceVault);
$('#evidenceAgent').addEventListener('keydown',e=>{if(e.key==='Enter')inspectEvidenceVault()});
refreshEvidenceVault();setInterval(refreshEvidenceVault,30000);

// Privacy-preserving benchmark telemetry. There is intentionally NO web
// button that starts provider calls or changes an agent's weights.
async function refreshHoldoutLab(){
 try{
  const d=await request('/api/evaluations/holdout');
  $('#holdoutSummary').textContent=`${d.verified_runs} verified local evaluation receipts / ${d.available_runs} examined. No real-world or trading mastery certified.`;
  $('#holdoutRecords').textContent=d.runs.length ? d.runs.slice(0,6).map(r=>`${r.id} · ${r.verification} · ${r.correct??'–'}/${r.total??'–'} synthetic tasks · ${r.run_status}`).join('\n') : 'NO REAL MODEL EVALUATION RECEIPTS. Run python -m training.independent_eval manually with explicit provider opt-in.';
 }catch(e){$('#holdoutSummary').textContent='Benchmark archive unavailable: '+e.message;}
}
refreshHoldoutLab();setInterval(refreshHoldoutLab,30000);
