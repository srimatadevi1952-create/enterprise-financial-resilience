'use strict';

const DESIGN={w:1881,h:1073};
const CONTROLS=['Capital','Liquidity','Operations','Regulation','Merchants','Countries & Corridors'];
const PRESETS={
  base:[76,72,82,28,31,24],
  adverse:[64,60,67,46,49,43],
  severe:[45,40,48,70,67,65],
  recovery:[84,82,89,24,24,18],
};
const canvas=document.getElementById('console');
const ctx=canvas.getContext('2d');
const master=document.getElementById('master');
const announcer=document.getElementById('announcer');
const assuranceDescription=document.getElementById('assurance-description');
const statusEl=document.getElementById('status');
const app={
  scale:1,ox:0,oy:0,dpr:1,mode:'live',bootstrap:null,session:null,state:null,
  variables:{},variableState:{},overlay:null,panel:null,drag:null,readOnly:false,
  preset:'base',playback:{period:0,running:false,timer:null},share:null,
  assurance:null,assuranceView:'enterprise',assurancePanel:null,assuranceDrag:null,
  assuranceDetail:null,pendingAssuranceView:null,scenarioResult:null,
};

const api=(path,options={},principal='analyst')=>fetch(path,{...options,headers:{
  'Content-Type':'application/json','X-EFR-Principal':principal,...(options.headers||{})
}}).then(async response=>{const data=await response.json();if(!response.ok)throw new Error(data.error||'Request failed');return data});

function announce(message){
  announcer.textContent=message;statusEl.textContent=message;statusEl.classList.add('show');
  clearTimeout(announce.timer);announce.timer=setTimeout(()=>statusEl.classList.remove('show'),2600);
}
function fit(){
  app.dpr=Math.min(devicePixelRatio||1,2);canvas.width=Math.round(innerWidth*app.dpr);canvas.height=Math.round(innerHeight*app.dpr);
  app.scale=Math.min(innerWidth/DESIGN.w,innerHeight/DESIGN.h);app.ox=(innerWidth-DESIGN.w*app.scale)/2;app.oy=(innerHeight-DESIGN.h*app.scale)/2;draw();
}
function paper(alpha=.97){ctx.fillStyle=`rgba(241,238,231,${alpha})`;ctx.strokeStyle='#24231f'}
function setFont(size,weight='400',family='Arial Narrow, Arial'){ctx.font=`${weight} ${size}px ${family}`;ctx.textBaseline='middle'}
function point(event){return{x:(event.clientX-app.ox)/app.scale,y:(event.clientY-app.oy)/app.scale}}
function inside(p,r){return p.x>=r.x&&p.x<=r.x+r.w&&p.y>=r.y&&p.y<=r.y+r.h}
function button(r,label,active=false){ctx.fillStyle=active?'#ed4b15':'#e1ddd4';ctx.fillRect(r.x,r.y,r.w,r.h);ctx.strokeStyle='#24231f';ctx.lineWidth=1;ctx.strokeRect(r.x,r.y,r.w,r.h);ctx.fillStyle=active?'#fff':'#24231f';setFont(12,'700');ctx.fillText(label,r.x+16,r.y+r.h/2)}

function draw(){
  if(!master.complete||!master.naturalWidth)return;
  ctx.setTransform(app.dpr,0,0,app.dpr,0,0);ctx.clearRect(0,0,innerWidth,innerHeight);ctx.save();ctx.translate(app.ox,app.oy);ctx.scale(app.scale,app.scale);
  if(app.mode==='simulation')drawSimulationLayer();
  drawAssuranceLauncher();
  if(app.panel)drawParameterPanel();
  if(app.assurancePanel)drawAssurancePanel();
  if(app.overlay==='authorize')drawAuthorization();
  if(app.overlay==='share')drawShare();
  if(app.overlay==='role-authorize')drawRoleAuthorization();
  if(app.overlay==='decision-authorize')drawDecisionAuthorization();
  if(app.overlay==='scenario-result')drawScenarioResult();
  ctx.restore();
}

function drawSimulationLayer(){
  paper(.94);ctx.fillRect(686,34,354,49);ctx.strokeRect(686,34,354,49);ctx.fillStyle='#24231f';setFont(16,'700');ctx.fillText('LIVE MONITOR · CONTINUES',712,59);
  paper(.98);ctx.fillRect(1093,34,425,49);ctx.strokeStyle='#ed4b15';ctx.lineWidth=3;ctx.strokeRect(1093,34,425,49);ctx.fillStyle='#ed4b15';ctx.beginPath();ctx.arc(1120,58,10,0,Math.PI*2);ctx.fill();ctx.fillStyle='#24231f';setFont(18,'700');ctx.fillText('SIMULATION LAB',1142,59);setFont(10);ctx.fillText(app.readOnly?'SHARED VIEW · READ ONLY':'PRIVATE · NO LIVE ACTION',1325,59);
  paper(.97);ctx.fillRect(1541,34,285,49);ctx.strokeStyle='#24231f';ctx.lineWidth=1;ctx.strokeRect(1541,34,285,49);setFont(14,'700');ctx.fillText('SHARE CONSOLE',1580,59);
  drawScenarioTransport();
  if(app.state&&app.state.probability*app.state.impact>=3)drawDynamicRisk();
}
function riskColour(state){const severity=state.probability*state.impact;return severity<3?'#4c4b47':severity<18?'#f4c542':severity<45?'#f29a23':'#ed4b15'}
function drawDynamicRisk(){
  const s=app.state,colour=riskColour(s);ctx.save();ctx.globalCompositeOperation='color';ctx.globalAlpha=.72;ctx.fillStyle=colour;ctx.beginPath();
  ctx.ellipse(941,452,139,127,0,0,Math.PI*2);ctx.fill();ctx.restore();
  paper(.96);ctx.fillRect(1358,642,288,132);ctx.fillStyle=colour;setFont(122,'700','Georgia');ctx.fillText(String(s.resilience).padStart(2,'0'),1362,710);ctx.fillStyle='#24231f';setFont(34);ctx.fillText('/100',1555,737);
  const px=177+Math.min(2,s.probability/5)*72,py=690-Math.min(2,s.impact/5)*74;ctx.fillStyle=colour;ctx.strokeStyle='#24231f';ctx.lineWidth=3;ctx.beginPath();ctx.arc(px,py,10,0,Math.PI*2);ctx.fill();ctx.stroke();
  if(s.payment_disruption!=='stable'){ctx.fillStyle=colour;[[1476,279],[1476,312],[1476,344],[1476,377],[1677,279],[1677,312],[1677,344],[1677,377]].forEach(([x,y])=>ctx.fillRect(x-8,y-8,16,16))}
}

const presetZones=['base','adverse','severe','recovery'].map((name,i)=>({name,x:1284+i*73,y:838,w:48,h:68}));
const transportZones={stop:{x:1386,y:936,w:52,h:55},play:{x:1458,y:936,w:52,h:55},pause:{x:1530,y:936,w:52,h:55}};
function drawScenarioTransport(){
  paper(.96);ctx.fillRect(1260,798,330,202);ctx.strokeStyle='#9f998f';ctx.strokeRect(1260,798,330,202);ctx.fillStyle='#716d65';setFont(11,'700');ctx.fillText('SCENARIO PRESETS · VERSION 1',1282,818);
  presetZones.forEach((z,i)=>{const active=app.preset===z.name;ctx.fillStyle=active?'#ed4b15':'#f3efe6';ctx.strokeStyle='#24231f';ctx.lineWidth=2;ctx.beginPath();ctx.arc(z.x+24,z.y+22,15,0,Math.PI*2);ctx.fill();ctx.stroke();ctx.fillStyle='#24231f';setFont(9,'700');ctx.textAlign='center';ctx.fillText(z.name.toUpperCase(),z.x+24,z.y+51);ctx.textAlign='left'});
  ctx.strokeStyle='#a9a399';ctx.beginPath();ctx.moveTo(1280,918);ctx.lineTo(1570,918);ctx.stroke();ctx.fillStyle='#24231f';ctx.fillRect(1399,951,22,22);ctx.beginPath();ctx.moveTo(1472,947);ctx.lineTo(1498,962);ctx.lineTo(1472,977);ctx.closePath();ctx.fill();ctx.fillRect(1542,947,9,30);ctx.fillRect(1558,947,9,30);
  ctx.fillStyle='#716d65';setFont(10,'700');ctx.fillText(`${app.playback.running?'PLAYING':'PERIOD'} ${app.playback.period}/8 · ${app.state?.as_of||'NOT RUN'}`,1282,990);
  if(app.playback.period>0){ctx.fillStyle='#ed4b15';ctx.fillRect(1008,132,Math.min(250,app.playback.period*31),3);ctx.beginPath();ctx.arc(1008+Math.min(250,app.playback.period*31),133,7,0,Math.PI*2);ctx.fill();ctx.fillStyle='#24231f';setFont(10,'700');ctx.fillText(`T+${app.playback.period}`,1270,133)}
}

function initVariableState(){
  CONTROLS.forEach(control=>{const baseline=app.bootstrap.live.controls[control];app.variableState[control]=(app.variables[control]||[]).map(v=>({...v,baseline_value:baseline,simulation_value:baseline,min_value:0,max_value:100}))});
}
function aggregateControl(control){const items=app.variableState[control]||[];return items.length?Math.round(items.reduce((sum,v)=>sum+v.simulation_value,0)/items.length):app.state.controls[control]}
function syncAggregates(){CONTROLS.forEach(control=>app.state.controls[control]=aggregateControl(control))}
function applyPreset(name){
  app.preset=name;CONTROLS.forEach((control,index)=>{(app.variableState[control]||[]).forEach(v=>v.simulation_value=PRESETS[name][index])});syncAggregates();app.playback.period=0;announce(`${name} preset loaded · private draft`);draw();
}
function openPanel(index){app.panel={index,control:CONTROLS[index],x:448,y:145,w:985,h:735,page:0,selected:0};draw()}
function drawParameterPanel(){
  const p=app.panel,items=app.variableState[p.control]||[],selected=items[p.selected]||items[0],pageSize=8,pages=Math.max(1,Math.ceil(items.length/pageSize));p.page=Math.min(p.page,pages-1);
  paper(.985);ctx.lineWidth=2;ctx.fillRect(p.x,p.y,p.w,p.h);ctx.strokeRect(p.x,p.y,p.w,p.h);ctx.fillStyle='#24231f';ctx.fillRect(p.x,p.y,p.w,64);ctx.fillStyle='#f3efe6';setFont(18,'700');ctx.fillText(`${String(p.index+1).padStart(2,'0')}  ${p.control.toUpperCase()} EXPERT PARAMETER DECK`,p.x+24,p.y+23);setFont(11);ctx.fillText(`${items.length} VARIABLES · ${app.mode==='live'?'READ ONLY':'PRIVATE DRAFT'} · PAGE ${p.page+1}/${pages}`,p.x+24,p.y+47);setFont(28);ctx.fillText('×',p.x+p.w-39,p.y+31);
  ctx.fillStyle='#24231f';setFont(12,'700');ctx.fillText('DERIVED CONTROL LEVEL',p.x+28,p.y+91);setFont(24,'700');ctx.fillText(String(aggregateControl(p.control)),p.x+p.w-65,p.y+91);ctx.strokeStyle='#a39d92';ctx.lineWidth=3;ctx.beginPath();ctx.moveTo(p.x+220,p.y+91);ctx.lineTo(p.x+p.w-100,p.y+91);ctx.stroke();ctx.strokeStyle='#ed4b15';ctx.lineWidth=5;ctx.beginPath();ctx.moveTo(p.x+220,p.y+91);ctx.lineTo(p.x+220+(p.w-320)*aggregateControl(p.control)/100,p.y+91);ctx.stroke();
  if(selected){const contribution=((selected.simulation_value-selected.baseline_value)/Math.max(1,items.length)).toFixed(2);ctx.fillStyle='#24231f';setFont(14,'700');ctx.fillText(selected.variable,p.x+28,p.y+133);ctx.fillStyle='#716d65';setFont(10);ctx.fillText(`${selected.variable_type} · UNIT: ${selected.typical_unit} · RANGE 0–100 NORMALISED`,p.x+28,p.y+155);ctx.fillStyle='#24231f';setFont(11,'700');ctx.fillText(`LIVE ${selected.baseline_value}`,p.x+28,p.y+184);ctx.fillText(`SIMULATED ${selected.simulation_value}`,p.x+150,p.y+184);ctx.fillStyle='#716d65';setFont(9);ctx.fillText(`AGGREGATE CONTRIBUTION ${contribution}`,p.x+p.w-360,p.y+153);const sx=p.x+275,sw=p.w-470,sy=p.y+184;ctx.strokeStyle='#9c968b';ctx.lineWidth=3;ctx.beginPath();ctx.moveTo(sx,sy);ctx.lineTo(sx+sw,sy);ctx.stroke();ctx.strokeStyle='#ed4b15';ctx.lineWidth=5;ctx.beginPath();ctx.moveTo(sx,sy);ctx.lineTo(sx+sw*selected.simulation_value/100,sy);ctx.stroke();ctx.fillStyle='#24231f';ctx.fillRect(sx+sw*selected.simulation_value/100-6,sy-11,12,22);button({x:p.x+p.w-176,y:p.y+166,w:145,h:36},'RESET VARIABLE')}
  const start=p.page*pageSize;items.slice(start,start+pageSize).forEach((v,i)=>{const idx=start+i,y=p.y+228+i*51,active=idx===p.selected,changed=v.baseline_value!==v.simulation_value;ctx.fillStyle=active?'#e2ddd3':'rgba(241,238,231,.15)';ctx.fillRect(p.x+24,y-18,p.w-48,43);ctx.strokeStyle='#b5afa5';ctx.beginPath();ctx.moveTo(p.x+24,y+25);ctx.lineTo(p.x+p.w-24,y+25);ctx.stroke();ctx.fillStyle=changed?'#ed4b15':'#24231f';setFont(12,active?'700':'400');ctx.fillText(`${v.parameter_id}  ${v.variable}`,p.x+34,y);ctx.fillStyle='#716d65';setFont(10);ctx.textAlign='right';ctx.fillText(`${v.baseline_value} → ${v.simulation_value} · ${v.variable_type}`,p.x+p.w-35,y);ctx.textAlign='left'});
  button({x:p.x+28,y:p.y+p.h-61,w:115,h:34},'‹ PREVIOUS',p.page>0);button({x:p.x+155,y:p.y+p.h-61,w:115,h:34},'NEXT ›',p.page<pages-1);button({x:p.x+p.w-185,y:p.y+p.h-61,w:155,h:34},'RESET ALL');ctx.fillStyle='#716d65';setFont(10);ctx.fillText(app.mode==='live'?'LIVE VALUES ARE INSPECT ONLY':'SELECT VARIABLE · EQUAL-WEIGHT NORMALISATION RULE V1 · PRIVATE DRAFT',p.x+292,p.y+p.h-44);
}

function drawAuthorization(){
  ctx.fillStyle='rgba(15,14,12,.55)';ctx.fillRect(0,0,DESIGN.w,DESIGN.h);const x=543,y=268,w=795,h=520;paper();ctx.lineWidth=2;ctx.fillRect(x,y,w,h);ctx.strokeRect(x,y,w,h);ctx.fillStyle='#24231f';setFont(22,'700');ctx.fillText('SIMULATION AUTHORIZATION',x+38,y+52);ctx.fillStyle='#ed4b15';ctx.fillRect(x+38,y+82,120,4);ctx.fillStyle='#24231f';setFont(15);ctx.fillText('Create a private workspace from the current timestamped enterprise state.',x+38,y+125);ctx.fillText('Live monitoring and every other user’s dashboard continue unchanged.',x+38,y+151);
  [['IDENTITY VERIFIED','Asha Iyer · local UAT identity'],['SIMULATION ENTITLED','Scope simulation:create verified'],['ISOLATION BOUNDARY','No live actions · private snapshot']].forEach((r,i)=>{const ry=y+205+i*67;ctx.strokeStyle='#938d83';ctx.strokeRect(x+38,ry,w-76,48);ctx.fillStyle='#24231f';setFont(13,'700');ctx.fillText('✓  '+r[0],x+56,ry+17);ctx.fillStyle='#716d65';setFont(11);ctx.fillText(r[1],x+56,ry+35)});
  button({x:x+38,y:y+h-72,w:220,h:42},'CANCEL');button({x:x+w-310,y:y+h-72,w:272,h:42},'ENTER SIMULATION LAB',true);
}
async function authorize(){try{app.session=await api('/api/simulation-sessions',{method:'POST',body:JSON.stringify({step_up_verified:true,purpose:'Enterprise stress and recovery analysis'})});app.state=structuredClone(app.session.state);initVariableState();app.mode='simulation';app.readOnly=false;app.overlay=null;applyPreset('base');announce('Private Simulation Lab created · live state unchanged')}catch(e){announce(e.message)}}
async function run(){if(app.mode!=='simulation'){app.overlay='authorize';draw();return}if(app.readOnly){announce('Shared viewer is read only');return}try{syncAggregates();const data=await api(`/api/simulation-sessions/${app.session.session_id}/run`,{method:'POST',body:JSON.stringify({controls:app.state.controls})});app.state=data.state;app.scenarioResult=data.scenario;app.playback.period=0;app.overlay='scenario-result';announce('Scenario calculated · explanation and results available');draw()}catch(e){announce(e.message)}}

function wrapped(text,x,y,maxWidth,lineHeight,maxLines=4){const words=String(text).split(/\s+/);let line='',lines=[];for(const word of words){const test=line?`${line} ${word}`:word;if(ctx.measureText(test).width>maxWidth&&line){lines.push(line);line=word}else line=test}if(line)lines.push(line);lines.slice(0,maxLines).forEach((value,index)=>ctx.fillText(value,x,y+index*lineHeight))}
function drawScenarioResult(){
  ctx.fillStyle='rgba(15,14,12,.58)';ctx.fillRect(0,0,DESIGN.w,DESIGN.h);const x=483,y=170,w=915,h=730,s=app.scenarioResult;paper(.995);ctx.fillRect(x,y,w,h);ctx.strokeStyle='#24231f';ctx.lineWidth=2;ctx.strokeRect(x,y,w,h);ctx.fillStyle='#24231f';ctx.fillRect(x,y,w,72);ctx.fillStyle='#fff';setFont(21,'700');ctx.fillText('SCENARIO EXPLANATION & RESULT',x+30,y+27);setFont(10);ctx.fillText(`${s?.scenario_id||'PENDING'} · ${s?.model_version||'UNKNOWN MODEL'} · PRIVATE SIMULATION`,x+30,y+53);setFont(30);ctx.fillText('×',x+w-48,y+35);
  ctx.fillStyle='#24231f';setFont(12,'700');ctx.fillText('SCENE',x+32,y+112);ctx.fillStyle='#716d65';setFont(13);wrapped(s?.explanation||'Scenario explanation unavailable.',x+32,y+144,w-64,24,4);
  const r=s?.results||{};const cards=[['PROBABILITY',r.probability??'—','0–10'],['IMPACT',r.impact??'—','0–10'],['RESILIENCE',r.resilience??'—','0–100'],['CONDITION',String(r.payment_disruption||'—').toUpperCase(),'CALCULATED']];cards.forEach((card,i)=>{const cx=x+32+i*211,cy=y+255;ctx.fillStyle='#ebe7de';ctx.fillRect(cx,cy,195,105);ctx.strokeStyle='#aaa399';ctx.strokeRect(cx,cy,195,105);ctx.fillStyle=i===2?'#ed4b15':'#24231f';setFont(i===3?18:34,'700');ctx.fillText(String(card[1]),cx+16,cy+39);ctx.fillStyle='#24231f';setFont(10,'700');ctx.fillText(card[0],cx+16,cy+72);ctx.fillStyle='#716d65';setFont(9);ctx.fillText(card[2],cx+16,cy+92)});
  ctx.fillStyle='#24231f';setFont(12,'700');ctx.fillText('CONNECTED PATHWAYS',x+32,y+405);ctx.fillStyle='#716d65';setFont(12);wrapped((s?.connected_pathways||[]).join('  ·  ')||'No connected pathway activated.',x+32,y+437,w-64,22,3);
  ctx.strokeStyle='#aaa399';ctx.strokeRect(x+32,y+515,w-64,95);ctx.fillStyle='#24231f';setFont(11,'700');ctx.fillText('PRECEDENT SEARCH',x+50,y+542);setFont(13);ctx.fillText(String(s?.precedent_search||'PENDING').replaceAll('_',' '),x+250,y+542);setFont(11,'700');ctx.fillText('LESSON STATE',x+50,y+580);setFont(13);ctx.fillText(String(s?.lesson_state||'PENDING').replaceAll('_',' '),x+250,y+580);
  ctx.fillStyle='#716d65';setFont(10);ctx.fillText('A precedent is advisory. Current-state validation, authority and rollback readiness remain mandatory.',x+32,y+644);button({x:x+w-206,y:y+h-61,w:174,h:36},'CLOSE',true);
}

function startPlayback(){if(!app.session||!app.state){announce('Calculate a scenario first');return}clearInterval(app.playback.timer);app.playback.running=true;app.playback.timer=setInterval(()=>{app.playback.period++;if(app.playback.period>=8){app.playback.period=8;pausePlayback();announce('Timeline complete')}draw()},650);announce('Scenario timeline playing');draw()}
function pausePlayback(){clearInterval(app.playback.timer);app.playback.timer=null;app.playback.running=false;draw()}
function stopPlayback(){pausePlayback();app.playback.period=0;announce('Timeline reset to T0');draw()}

function drawShare(){
  ctx.fillStyle='rgba(15,14,12,.55)';ctx.fillRect(0,0,DESIGN.w,DESIGN.h);const x=548,y=245,w=785,h=565;paper();ctx.fillRect(x,y,w,h);ctx.strokeRect(x,y,w,h);ctx.fillStyle='#24231f';setFont(22,'700');ctx.fillText('SHARE PRIVATE SIMULATION',x+38,y+45);setFont(11);ctx.fillText('AUTHENTICATED LOCAL UAT COLLABORATION · PRODUCTION CONNECTORS NOT CONFIGURED',x+38,y+73);
  button({x:x+38,y:y+105,w:330,h:78},'OPEN GOOGLE MEET');button({x:x+417,y:y+105,w:330,h:78},'OPEN ZOOM');button({x:x+38,y:y+220,w:330,h:78},'CREATE VIEWER INVITATION');button({x:x+417,y:y+220,w:330,h:78},'COPY SECURE JOIN LINK');
  ctx.fillStyle='#24231f';setFont(13,'700');ctx.fillText('COLLABORATION STATUS',x+38,y+337);ctx.strokeStyle='#aaa399';ctx.strokeRect(x+38,y+358,w-76,117);ctx.fillStyle='#716d65';setFont(11);const status=app.share?.invitation?`${app.share.invitation.actor_id} · ${app.share.invitation.role.toUpperCase()} · ${app.share.invitation.status} · EXPIRES ${app.share.invitation.expires_at}`:'NO INVITATION CREATED';ctx.fillText(status,x+56,y+386);ctx.fillText(app.share?.joinUrl||'Create an invitation to generate an expiring authenticated join link.',x+56,y+416);ctx.fillText('Viewer access is read only and restricted to this simulation.',x+56,y+446);if(app.share?.invitation&&app.share.invitation.status!=='REVOKED')button({x:x+38,y:y+h-58,w:190,h:34},'REVOKE ACCESS');button({x:x+w-176,y:y+h-58,w:138,h:34},'CLOSE',true);
}
async function createInvitation(){try{const invitation=await api(`/api/simulation-sessions/${app.session.session_id}/invitations`,{method:'POST',body:JSON.stringify({actor_id:'viewer-1',role:'viewer',ttl_minutes:30})});app.share={invitation,joinUrl:`${location.origin}/?invite=${encodeURIComponent(invitation.token)}`};announce('Viewer invitation created · expires in 30 minutes');draw()}catch(e){announce(e.message)}}
async function copyJoinLink(){if(!app.share?.joinUrl){announce('Create an invitation first');return}await navigator.clipboard.writeText(app.share.joinUrl);announce('Secure join link copied')}
async function revokeInvitation(){if(!app.share?.invitation)return;try{const invitation=await api(`/api/simulation-sessions/${app.session.session_id}/invitations/revoke`,{method:'POST',body:JSON.stringify({token:app.share.invitation.token})});app.share.invitation=invitation;announce('Viewer access revoked');draw()}catch(e){announce(e.message)}}

function drawAssuranceLauncher(){const r={x:1575,y:744,w:252,h:36};paper(.93);ctx.fillRect(r.x,r.y,r.w,r.h);ctx.strokeStyle='#ed4b15';ctx.lineWidth=1.5;ctx.strokeRect(r.x,r.y,r.w,r.h);ctx.fillStyle='#ed4b15';ctx.beginPath();ctx.arc(r.x+19,r.y+18,6,0,Math.PI*2);ctx.fill();ctx.fillStyle='#24231f';setFont(11,'700');ctx.fillText('OPERATIONAL ASSURANCE  [A]',r.x+34,r.y+18)}
function assuranceRows(data){
  if(!data||!data.operating_model)return[];
  if(data.operating_model==='ENTERPRISE')return[['CONFIGURATION',`${data.configuration.status} · V${data.configuration.version} · ${data.configuration.processes} PROCESSES`,'Configuration'],['INFORMATION OBLIGATIONS',`${data.obligations.open} OPEN · ${data.obligations.overdue} OVERDUE`,'Information'],['GOVERNED CHANGES',`${data.changes.open} OPEN · ${data.changes.awaiting_approval} AWAITING APPROVAL`,'Changes'],['CASE INTELLIGENCE',`${data.knowledge.current_lessons} CURRENT LESSONS · ${data.knowledge.related_precedents} PRECEDENT`,'Prior Cases']];
  if(data.operating_model==='CONSULTANT')return[['ACTIVE CLIENT',data.active_client.toUpperCase(),'Client Portfolio'],['PORTFOLIO',`${data.portfolio.assigned_clients} ASSIGNED · ${data.portfolio.changes_to_review} CHANGE TO REVIEW`,'Change Inbox'],['CLIENT DECISIONS',`${data.portfolio.pending_client_decisions} PENDING`,'Client Decision'],['MANDATE',`${data.mandate.status} · ${data.mandate.mode} · SANDBOX ONLY`,'Implementation']];
  return[['RECOMMENDATION',data.recommendation.status.replaceAll('_',' '),'Consultant Assessment'],['IMPLEMENTATION MODE',data.recommendation.implementation_mode,'Authority Requested'],['SIMULATION EVIDENCE',data.recommendation.simulation_ref,'Simulated Effect'],['AUTHORITY',data.recommendation.authority,'Decision Evidence']].map(r=>[r[0],String(r[1]).toUpperCase(),r[2]]);
}
function drawAssurancePanel(){
  const p=app.assurancePanel,d=app.assurance;paper(.985);ctx.lineWidth=2;ctx.fillRect(p.x,p.y,p.w,p.h);ctx.strokeStyle='#24231f';ctx.strokeRect(p.x,p.y,p.w,p.h);ctx.fillStyle='#24231f';ctx.fillRect(p.x,p.y,p.w,62);ctx.fillStyle='#f3efe6';setFont(18,'700');ctx.fillText('OPERATIONAL ASSURANCE',p.x+26,p.y+22);setFont(10);ctx.fillText('LOCAL UAT ROLE PREVIEW · STEP-UP REQUIRED · DRAGGABLE',p.x+26,p.y+44);setFont(28);ctx.fillText('×',p.x+p.w-41,p.y+30);
  const tabs=[['enterprise','ENTERPRISE MODEL'],['consultant','CONSULTANT CENTRE'],['client','CLIENT APPROVAL']];tabs.forEach((t,i)=>button({x:p.x+26+i*310,y:p.y+78,w:286,h:39},t[1],app.assuranceView===t[0]));
  if(!d){ctx.fillStyle='#24231f';setFont(16,'700');ctx.fillText('LOADING GOVERNED VIEW…',p.x+32,p.y+160);return}
  ctx.fillStyle='#24231f';setFont(21,'700');ctx.fillText(d.workspace_title.toUpperCase(),p.x+28,p.y+148);ctx.fillStyle='#716d65';setFont(10);ctx.fillText(`${d.tenant_context.toUpperCase()} · ${d.principal.display_name.toUpperCase()} · ${d.data_mode}`,p.x+28,p.y+174);ctx.fillText(`${d.measure_context.reference} · AS OF ${d.measure_context.as_of}`,p.x+28,p.y+193);
  const s=d.risk_state,cards=[['RISK SEVERITY',s.severity,'EXPOSURE'],['EVIDENCE CONFIDENCE',s.confidence_pct+'%','QUALITY'],['RESILIENCE OUTCOME',s.resilience,'CALCULATED'],['WORKFLOW STATUS',s.workflow_status.replaceAll('_',' '),'STATE']];cards.forEach((c,i)=>{const x=p.x+28+i*237,y=p.y+212,w=215,h=94;ctx.fillStyle='#ebe7de';ctx.fillRect(x,y,w,h);ctx.strokeStyle='#aaa399';ctx.strokeRect(x,y,w,h);ctx.fillStyle=i===0?'#ed4b15':'#24231f';setFont(typeof c[1]==='number'?34:16,'700');ctx.fillText(String(c[1]),x+16,y+37);ctx.fillStyle='#24231f';setFont(10,'700');ctx.fillText(c[0],x+16,y+67);ctx.fillStyle='#716d65';setFont(8);ctx.fillText(c[2],x+16,y+84)});
  assuranceRows(d).forEach((row,i)=>{const y=p.y+336+i*52;ctx.fillStyle='rgba(226,221,211,.28)';ctx.fillRect(p.x+22,y-17,p.w-44,42);ctx.strokeStyle='#b5afa5';ctx.beginPath();ctx.moveTo(p.x+22,y+25);ctx.lineTo(p.x+p.w-22,y+25);ctx.stroke();ctx.fillStyle='#24231f';setFont(11,'700');ctx.fillText(row[0],p.x+28,y);setFont(13);ctx.fillText(row[1],p.x+300,y);ctx.fillStyle='#ed4b15';ctx.textAlign='right';setFont(10,'700');ctx.fillText('OPEN ›',p.x+p.w-35,y);ctx.textAlign='left'});
  if(app.assuranceView==='client'){button({x:p.x+28,y:p.y+556,w:200,h:38},'APPROVE',true);button({x:p.x+242,y:p.y+556,w:200,h:38},'REJECT');button({x:p.x+456,y:p.y+556,w:260,h:38},'RETURN FOR CLARIFICATION')}
  ctx.fillStyle='#24231f';setFont(10,'700');ctx.fillText('SELECTABLE PANELS',p.x+28,p.y+621);setFont(9);ctx.fillStyle='#716d65';ctx.fillText(d.panels.join('   ·   ').toUpperCase(),p.x+28,p.y+642);ctx.fillStyle='#ed4b15';ctx.fillRect(p.x,p.y+p.h-45,p.w,45);ctx.fillStyle='#fff';setFont(10,'700');ctx.fillText(`READ ONLY · LIVE ACTIONS 0 · ${d.measure_context.scope} · ${d.measure_context.scale}`,p.x+28,p.y+p.h-22);
  if(app.assuranceDetail)drawAssuranceDetail();
}
function drawAssuranceDetail(){const p=app.assurancePanel,d=app.assuranceDetail,x=p.x+108,y=p.y+165,w=p.w-216,h=470;ctx.fillStyle='rgba(15,14,12,.45)';ctx.fillRect(p.x,p.y+62,p.w,p.h-107);paper(.995);ctx.fillRect(x,y,w,h);ctx.strokeStyle='#24231f';ctx.lineWidth=2;ctx.strokeRect(x,y,w,h);ctx.fillStyle='#24231f';ctx.fillRect(x,y,w,58);ctx.fillStyle='#fff';setFont(18,'700');ctx.fillText(d.title.toUpperCase(),x+24,y+29);setFont(26);ctx.fillText('×',x+w-42,y+28);d.rows.forEach((row,i)=>{const ry=y+96+i*54;ctx.strokeStyle='#b5afa5';ctx.beginPath();ctx.moveTo(x+24,ry+22);ctx.lineTo(x+w-24,ry+22);ctx.stroke();ctx.fillStyle='#24231f';setFont(11,'700');ctx.fillText(row.label.toUpperCase(),x+28,ry);setFont(13);ctx.fillText(row.value,x+240,ry)});ctx.fillStyle='#716d65';setFont(10);ctx.fillText(`${d.source.reference} · ${d.source.as_of} · READ ONLY`,x+28,y+h-30)}
async function loadAssurance(view='enterprise'){
  const principal={enterprise:'analyst',consultant:'consultant',client:'client'}[view];app.assuranceView=view;app.assurancePanel=app.assurancePanel||{x:430,y:150,w:1020,h:720};app.assurance=null;app.assuranceDetail=null;draw();
  try{app.assurance=await api(`/api/operational-assurance/bootstrap?view=${view}`,{},principal);const s=app.assurance.risk_state;assuranceDescription.textContent=`${app.assurance.workspace_title}. ${app.assurance.tenant_context}. Risk severity ${s.severity}. Evidence confidence ${s.confidence_pct} percent. Resilience outcome ${s.resilience}. Workflow ${s.workflow_status.replaceAll('_',' ')}. Synthetic UAT data. Read only. Live actions zero.`;canvas.setAttribute('aria-describedby','assurance-description');announce(`${app.assurance.workspace_title} · ${app.assurance.data_mode}`)}catch(e){announce(e.message)}draw();
}
async function openAssuranceDetail(panel){const principal={enterprise:'analyst',consultant:'consultant',client:'client'}[app.assuranceView];try{app.assuranceDetail=await api(`/api/operational-assurance/detail?view=${app.assuranceView}&panel=${encodeURIComponent(panel)}`,{},principal);draw();announce(`${panel} detail opened`)}catch(e){announce(e.message)}}

function drawRoleAuthorization(){ctx.fillStyle='rgba(15,14,12,.58)';ctx.fillRect(0,0,DESIGN.w,DESIGN.h);const x=610,y=320,w=660,h=390;paper();ctx.fillRect(x,y,w,h);ctx.strokeRect(x,y,w,h);ctx.fillStyle='#24231f';setFont(21,'700');ctx.fillText('AUTHORIZE LOCAL UAT ROLE PREVIEW',x+34,y+48);ctx.fillStyle='#ed4b15';ctx.fillRect(x+34,y+75,110,4);setFont(14);ctx.fillStyle='#24231f';ctx.fillText(`Requested view: ${String(app.pendingAssuranceView).toUpperCase()}`,x+34,y+120);ctx.fillText('This changes only your private local preview.',x+34,y+153);ctx.fillText('Production will use organisational identity and mandate claims.',x+34,y+181);ctx.strokeStyle='#aaa399';ctx.strokeRect(x+34,y+215,w-68,62);setFont(12,'700');ctx.fillText('STEP-UP VERIFIED · TRANSITION AUDITED · LIVE SESSION UNCHANGED',x+54,y+246);button({x:x+34,y:y+h-66,w:190,h:38},'CANCEL');button({x:x+w-270,y:y+h-66,w:236,h:38},'AUTHORIZE PREVIEW',true)}
function drawDecisionAuthorization(){ctx.fillStyle='rgba(15,14,12,.58)';ctx.fillRect(0,0,DESIGN.w,DESIGN.h);const x=610,y=320,w=660,h=390;paper();ctx.fillRect(x,y,w,h);ctx.strokeRect(x,y,w,h);ctx.fillStyle='#24231f';setFont(21,'700');ctx.fillText('CLIENT DECISION AUTHORIZATION',x+34,y+48);ctx.fillStyle='#ed4b15';ctx.fillRect(x+34,y+75,110,4);setFont(14);ctx.fillStyle='#24231f';ctx.fillText(`Decision: ${String(app.pendingDecision).replaceAll('_',' ')}`,x+34,y+120);ctx.fillText('Identity: Arun Mehta · client decision authority',x+34,y+153);ctx.fillText('The decision enables sandbox progression only; live actions remain zero.',x+34,y+181);ctx.strokeStyle='#aaa399';ctx.strokeRect(x+34,y+215,w-68,62);setFont(12,'700');ctx.fillText('STEP-UP VERIFIED · SEGREGATION OF DUTY PASSED · AUDIT REQUIRED',x+54,y+246);button({x:x+34,y:y+h-66,w:190,h:38},'CANCEL');button({x:x+w-270,y:y+h-66,w:236,h:38},'RECORD DECISION',true)}
async function recordDecision(){try{const result=await api('/api/operational-assurance/client-decision',{method:'POST',body:JSON.stringify({decision:app.pendingDecision,step_up_verified:true,rationale:'Recorded during controlled UAT'})},'client');app.overlay=null;await loadAssurance('client');announce(`Client decision recorded: ${result.status}`)}catch(e){announce(e.message)}}

const zones={live:{x:686,y:32,w:360,h:54},simulation:{x:1090,y:32,w:430,h:54},share:{x:1538,y:30,w:292,h:60},assurance:{x:1575,y:744,w:252,h:36},run:{x:1576,y:793,w:154,h:190}};
const controlZones=CONTROLS.map((name,i)=>({name,x:49+i*198,y:793,w:188,h:197}));

canvas.addEventListener('pointerdown',async event=>{
  const p=point(event);if(p.x<0||p.y<0||p.x>DESIGN.w||p.y>DESIGN.h)return;
  if(app.overlay==='authorize'){if(inside(p,{x:1028,y:716,w:272,h:42}))await authorize();else if(inside(p,{x:581,y:716,w:220,h:42})){app.overlay=null;draw()}return}
  if(app.overlay==='role-authorize'){if(inside(p,{x:1000,y:644,w:236,h:38})){const view=app.pendingAssuranceView;app.overlay=null;await loadAssurance(view)}else if(inside(p,{x:644,y:644,w:190,h:38})){app.overlay=null;draw()}return}
  if(app.overlay==='decision-authorize'){if(inside(p,{x:1000,y:644,w:236,h:38}))await recordDecision();else if(inside(p,{x:644,y:644,w:190,h:38})){app.overlay=null;draw()}return}
  if(app.overlay==='scenario-result'){if(inside(p,{x:1192,y:839,w:174,h:36})||inside(p,{x:1338,y:170,w:60,h:72})){app.overlay=null;draw()}return}
  if(app.overlay==='share'){
    if(inside(p,{x:586,y:350,w:330,h:78}))window.open('https://meet.google.com/new','_blank','noopener');
    else if(inside(p,{x:965,y:350,w:330,h:78}))window.open('https://zoom.us/start/videomeeting','_blank','noopener');
    else if(inside(p,{x:586,y:465,w:330,h:78}))await createInvitation();
    else if(inside(p,{x:965,y:465,w:330,h:78}))await copyJoinLink();
    else if(inside(p,{x:586,y:752,w:190,h:34}))await revokeInvitation();
    else if(inside(p,{x:1157,y:752,w:138,h:34})){app.overlay=null;draw()}return;
  }
  if(app.assurancePanel){const q=app.assurancePanel;
    if(app.assuranceDetail){const dx=q.x+108,dy=q.y+165,dw=q.w-216;if(inside(p,{x:dx+dw-60,y:dy,w:60,h:58})){app.assuranceDetail=null;draw();return}}
    if(inside(p,{x:q.x+q.w-60,y:q.y,w:60,h:62})){app.assurancePanel=null;draw();return}
    if(inside(p,{x:q.x,y:q.y,w:q.w,h:62})){app.assuranceDrag={dx:p.x-q.x,dy:p.y-q.y};canvas.setPointerCapture(event.pointerId);return}
    for(let i=0;i<3;i++){if(inside(p,{x:q.x+26+i*310,y:q.y+78,w:286,h:39})){const view=['enterprise','consultant','client'][i];if(view===app.assuranceView)await loadAssurance(view);else{app.pendingAssuranceView=view;app.overlay='role-authorize';draw()}return}}
    const rows=assuranceRows(app.assurance||{});for(let i=0;i<rows.length;i++){if(inside(p,{x:q.x+22,y:q.y+319+i*52,w:q.w-44,h:49})){await openAssuranceDetail(rows[i][2]);return}}
    if(app.assuranceView==='client'){
      if(inside(p,{x:q.x+28,y:q.y+556,w:200,h:38})){app.pendingDecision='APPROVED';app.overlay='decision-authorize';draw();return}
      if(inside(p,{x:q.x+242,y:q.y+556,w:200,h:38})){app.pendingDecision='REJECTED';app.overlay='decision-authorize';draw();return}
      if(inside(p,{x:q.x+456,y:q.y+556,w:260,h:38})){app.pendingDecision='CLARIFICATION_REQUESTED';app.overlay='decision-authorize';draw();return}
    }
  }
  if(app.panel){const q=app.panel,items=app.variableState[q.control]||[],pageSize=8;
    if(inside(p,{x:q.x+q.w-60,y:q.y,w:60,h:64})){app.panel=null;draw();return}
    if(inside(p,{x:q.x,y:q.y,w:q.w,h:64})){app.drag={dx:p.x-q.x,dy:p.y-q.y};canvas.setPointerCapture(event.pointerId);return}
    if(inside(p,{x:q.x+275,y:q.y+162,w:q.w-470,h:48})&&app.mode==='simulation'&&!app.readOnly){const v=items[q.selected];v.simulation_value=Math.round(Math.max(0,Math.min(1,(p.x-(q.x+275))/(q.w-470)))*100);syncAggregates();draw();return}
    if(inside(p,{x:q.x+q.w-176,y:q.y+166,w:145,h:36})&&app.mode==='simulation'&&!app.readOnly){items[q.selected].simulation_value=items[q.selected].baseline_value;syncAggregates();draw();return}
    for(let i=0;i<8;i++){if(inside(p,{x:q.x+24,y:q.y+210+i*51,w:q.w-48,h:49})){const idx=q.page*pageSize+i;if(idx<items.length){q.selected=idx;draw()}return}}
    if(inside(p,{x:q.x+28,y:q.y+q.h-61,w:115,h:34})){q.page=Math.max(0,q.page-1);draw();return}
    if(inside(p,{x:q.x+155,y:q.y+q.h-61,w:115,h:34})){q.page=Math.min(Math.ceil(items.length/pageSize)-1,q.page+1);draw();return}
    if(inside(p,{x:q.x+q.w-185,y:q.y+q.h-61,w:155,h:34})&&app.mode==='simulation'&&!app.readOnly){items.forEach(v=>v.simulation_value=v.baseline_value);syncAggregates();draw();return}
  }
  if(inside(p,zones.assurance)){await loadAssurance();return}
  if(inside(p,zones.live)){pausePlayback();app.mode='live';app.state=structuredClone(app.bootstrap.live);app.panel=null;app.readOnly=false;announce('Live Monitor · read only');draw();return}
  if(inside(p,zones.simulation)){if(app.session){app.mode='simulation';app.state=app.session.state;draw()}else{app.overlay='authorize';draw()}return}
  if(inside(p,zones.share)){if(app.mode==='simulation'&&app.session&&!app.readOnly){app.overlay='share';draw()}else announce('Private simulation owner access required');return}
  if(inside(p,zones.run)){await run();return}
  if(app.mode==='simulation'){for(const z of presetZones){if(inside(p,z)){if(app.readOnly)announce('Shared viewer is read only');else applyPreset(z.name);return}}if(inside(p,transportZones.stop)){stopPlayback();return}if(inside(p,transportZones.play)){startPlayback();return}if(inside(p,transportZones.pause)){pausePlayback();announce('Timeline paused');return}}
  const index=controlZones.findIndex(z=>inside(p,z));if(index>=0)openPanel(index);
});

canvas.addEventListener('pointermove',event=>{const p=point(event);if(app.assuranceDrag&&app.assurancePanel){app.assurancePanel.x=Math.max(0,Math.min(DESIGN.w-app.assurancePanel.w,p.x-app.assuranceDrag.dx));app.assurancePanel.y=Math.max(0,Math.min(DESIGN.h-app.assurancePanel.h,p.y-app.assuranceDrag.dy));draw();return}if(app.drag&&app.panel){app.panel.x=Math.max(0,Math.min(DESIGN.w-app.panel.w,p.x-app.drag.dx));app.panel.y=Math.max(0,Math.min(DESIGN.h-app.panel.h,p.y-app.drag.dy));draw();return}canvas.style.cursor='pointer'});
canvas.addEventListener('pointerup',()=>{app.drag=null;app.assuranceDrag=null});canvas.addEventListener('pointercancel',()=>{app.drag=null;app.assuranceDrag=null});
addEventListener('keydown',event=>{if(event.key==='Escape'){app.overlay=null;app.panel=null;app.assuranceDetail=null;draw()}else if(event.key.toLowerCase()==='a'){app.assurancePanel?app.assurancePanel=null:loadAssurance();draw()}else if(event.key.toLowerCase()==='l'){pausePlayback();app.mode='live';app.state=structuredClone(app.bootstrap.live);draw()}else if(event.key.toLowerCase()==='s'){app.session?app.mode='simulation':app.overlay='authorize';draw()}else if(event.key.toLowerCase()==='r')run();else if(/^[1-6]$/.test(event.key))openPanel(+event.key-1)});
addEventListener('resize',fit);

async function joinFromUrl(){const token=new URLSearchParams(location.search).get('invite');if(!token)return false;try{const result=await api('/api/collaboration/join',{method:'POST',body:JSON.stringify({token})},'viewer');app.session=result.session;app.state=result.session.state;app.mode='simulation';app.readOnly=result.read_only;announce('Joined shared simulation as read-only viewer');return true}catch(e){announce(e.message);return false}}
master.onload=async()=>{fit();try{app.bootstrap=await api('/api/bootstrap');app.state=structuredClone(app.bootstrap.live);app.variables=app.bootstrap.variables;initVariableState();const joined=await joinFromUrl();draw();if(!joined)announce('Live Monitor ready · read only')}catch(e){announce(e.message)}};
