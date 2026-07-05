"use strict";

const QUIZ = window.QUIZ;
const LETTERS = ["A", "B", "C", "D"];
const app = document.getElementById("app");
const lightbox = document.getElementById("lightbox");
const lbImg = document.getElementById("lbimg");
const STORE = `cap_review_${QUIZ.id}`;
const QMAP = Object.fromEntries(QUIZ.questions.map(q => [q.no, q]));
let session = null;

function esc(s){return String(s ?? "").replace(/[&<>"']/g, c => ({"&":"&amp;","<":"&lt;",">":"&gt;","\"":"&quot;","'":"&#39;"}[c]));}
function now(){return Date.now();}
function fmtDate(ts){const d=new Date(ts);const p=n=>String(n).padStart(2,"0");return `${d.getFullYear()}/${p(d.getMonth()+1)}/${p(d.getDate())} ${p(d.getHours())}:${p(d.getMinutes())}`;}
function fmtDur(sec){const m=Math.floor(sec/60),s=sec%60;return m?`${m}分${s}秒`:`${s}秒`;}
function pct(n,d){return d?Math.round(n/d*100):0;}
function shuffle(a){const x=a.slice();for(let i=x.length-1;i>0;i--){const j=Math.floor(Math.random()*(i+1));[x[i],x[j]]=[x[j],x[i]];}return x;}
function modeLabel(m){return m==="practice"?"隨手練習":m==="wrong"?"錯題練習":"全卷測驗";}
function answerIndex(q){return LETTERS.indexOf(q.answer);}
function scoreOf(correct,total){return Math.round(correct * (QUIZ.perScore || 2));}

function loadDB(){try{return JSON.parse(localStorage.getItem(STORE)) || {profiles:{},last:""};}catch(e){return {profiles:{},last:""};}}
function saveDB(db){localStorage.setItem(STORE, JSON.stringify(db));}
function getProfile(name){const db=loadDB();if(!db.profiles[name]) db.profiles[name]={created:now(),attempts:[]};saveDB(db);return db.profiles[name];}
function updateProfile(name, fn){const db=loadDB();if(!db.profiles[name]) db.profiles[name]={created:now(),attempts:[]};fn(db.profiles[name], db);db.last=name;saveDB(db);return db.profiles[name];}

function cloudOn(){return !!(window.CLOUD && CLOUD.enabled && window.firebase && CLOUD.config && CLOUD.config.projectId);}
function cloudInit(){if(cloudOn() && !firebase.apps.length) firebase.initializeApp(CLOUD.config);}
function pendingKey(){return `${STORE}_pending_cloud`;}
function cloudStatus(txt, cls){const el=document.getElementById("cloudStatus"); if(el){el.textContent=txt; el.className=`chip ${cls||""}`.trim();}}
function cloudPayload(att, name){
  return {
    name,
    mode: att.mode,
    attemptNo: att.attemptNo || null,
    quiz: QUIZ.id,              // 舊版教師端相容欄位
    quizId: QUIZ.id,
    quizTitle: QUIZ.title,
    subject: QUIZ.subject,
    score: att.score,
    correct: att.correct,
    total: att.total,
    ids: att.ids || [],
    answers: att.answers || {},
    wrongIds: att.wrongIds || [],
    durationSec: att.durationSec || 0,
    clientTime: att.date || Date.now(),
    date: att.date || Date.now(),
    source: "cap-review-pages"
  };
}
function getPending(){try{return JSON.parse(localStorage.getItem(pendingKey())) || [];}catch(e){return [];}}
function setPending(list){localStorage.setItem(pendingKey(), JSON.stringify(list));}
async function cloudSendOne(payload){
  cloudInit();
  await firebase.firestore().collection("results").add(Object.assign({}, payload, {
    ts: firebase.firestore.FieldValue.serverTimestamp()
  }));
}
async function flushPendingCloud(){
  if(!cloudOn()) return;
  const list=getPending();
  if(!list.length) return;
  const remain=[];
  for(const p of list){try{await cloudSendOne(p);}catch(e){remain.push(p);}}
  setPending(remain);
  if(!remain.length) cloudStatus("✓ 已補傳暫存紀錄", "good");
}
async function cloudPush(att, name){
  if(!cloudOn()) return;
  const payload=cloudPayload(att, name);
  cloudStatus("雲端上傳中…", "");
  try{
    await flushPendingCloud();
    await cloudSendOne(payload);
    cloudStatus("✓ 已上傳老師端（跨裝置可見）", "good");
  }catch(e){
    console.warn("cloud push failed", e);
    const list=getPending(); list.push(payload); setPending(list);
    cloudStatus("雲端暫時失敗，已存在本機待補傳", "warn");
  }
}

function installTheme(){
  const saved=localStorage.getItem("cap_theme") || "dark";
  document.documentElement.dataset.theme=saved;
  const btn=document.getElementById("themeToggle");
  if(btn) btn.onclick=()=>{const cur=document.documentElement.dataset.theme==="light"?"dark":"light";document.documentElement.dataset.theme=cur;localStorage.setItem("cap_theme",cur);btn.textContent=cur==="light"?"🌙":"☀️";};
  if(btn) btn.textContent=saved==="light"?"🌙":"☀️";
}
window.zoom = src => { lbImg.src = src; lightbox.classList.add("on"); };
lightbox.onclick = () => lightbox.classList.remove("on");

function sourceHTML(q){
  return (q.images || []).map(src => `<img class="source-img" src="${esc(src)}" alt="第${q.no}題原題截圖" loading="lazy" onclick="zoom('${esc(src)}')">`).join("") + `<div class="source-note">點圖可放大；原題截圖為作答依據</div>`;
}
function optionHTML(q, chosen, reveal){
  const texts=q.options && q.options.length===4 ? q.options : ["選項 A", "選項 B", "選項 C", "選項 D"];
  return `<div class="grid col-12" style="grid-template-columns:1fr;gap:10px">${LETTERS.map((L,i)=>{
    let cls="btn option";
    if(chosen===L) cls += " selected";
    if(reveal && L===q.answer) cls += " correct";
    if(reveal && chosen===L && L!==q.answer) cls += " wrong";
    const label = texts[i] && texts[i] !== L ? `<span>${esc(texts[i])}</span>` : "";
    return `<button class="${cls}" onclick="choose('${L}')"><span class="key">${L}</span>${label}</button>`;
  }).join("")}</div>`;
}
function progressHTML(){
  const done=Object.keys(session.answers).length;
  return `<div class="pbar" title="${done}/${session.ids.length}"><span style="width:${pct(done,session.ids.length)}%"></span></div>`;
}

function viewLogin(){
  const db=loadDB(); const names=Object.keys(db.profiles || {});
  app.innerHTML = `
    <div class="brand"><div class="logo">會</div><div><h1>${esc(QUIZ.siteTitle || "會考複習自學平台")}</h1><div class="sub">${esc(QUIZ.title)}・${esc(QUIZ.subject)}</div></div></div>
    <div class="card">
      <h3>歡迎！先登錄你的名字</h3>
      <p class="muted small">成績會先存在這台裝置；若雲端已啟用，交卷後會自動同步到老師端，老師可跨手機/電腦/不同主機查看。</p>
      <label class="lbl" for="nm">你的名字 / 暱稱</label>
      <input id="nm" maxlength="24" placeholder="例如：小明" onkeydown="if(event.key==='Enter')startLogin()">
      <div style="height:12px"></div><button class="btn primary block" onclick="startLogin()">開始練習 →</button>
      ${names.length?`<hr style="border:none;border-top:1px solid var(--line);margin:18px 0"><label class="lbl">曾經練習過</label><div class="row">${names.map(n=>`<button class="btn sm" onclick="enter('${encodeURIComponent(n)}')">👤 ${esc(n)} <span class="muted">${db.profiles[n].attempts.length}次</span></button>`).join("")}</div>`:""}
    </div>
    <div class="grid">
      <div class="card col-8"><h3>本系列架構</h3><p>${esc(QUIZ.description)}</p><div class="row"><span class="chip unit">${QUIZ.questions.length}題</span><span class="chip">自動評分</span><span class="chip">錯題練習</span><span class="chip">原題截圖</span><span class="chip">教師版統計</span></div></div>
      <div class="card col-4 center"><div class="score">${QUIZ.totalScore}</div><div class="muted">滿分</div><a class="btn sm ghost" href="../../index.html">← 回系列首頁</a></div>
    </div>
    <div class="foot">來源：${esc(QUIZ.sourceLabel)}<br><a href="${esc(QUIZ.sourceUrl)}" target="_blank" rel="noopener">官方歷屆試題頁</a> · <a href="teacher.html">教師版</a></div>`;
  const inp=document.getElementById("nm"); if(db.last) inp.value=db.last; inp.focus();
}
window.startLogin=function(){const name=document.getElementById("nm").value.trim();if(!name){alert("請先輸入名字");return;}updateProfile(name,()=>{});viewDashboard(name);};
window.enter=function(enc){viewDashboard(decodeURIComponent(enc));};

function latestWrongIds(prof){
  const last=[...(prof.attempts||[])].reverse().find(a => a.quizId===QUIZ.id && a.wrongIds && a.wrongIds.length);
  return last ? last.wrongIds.slice() : [];
}
function unitStats(att){
  const map={};
  (att.ids||[]).forEach(no=>{const q=QMAP[no]; if(!q) return; if(!map[q.unit]) map[q.unit]={total:0,correct:0}; map[q.unit].total++; if(!(att.wrongIds||[]).includes(no)) map[q.unit].correct++;});
  return map;
}
function viewDashboard(name){
  const prof=getProfile(name); const atts=(prof.attempts||[]).filter(a=>a.quizId===QUIZ.id); const last=atts[atts.length-1]; const wrong=latestWrongIds(prof);
  const hist=atts.length ? atts.slice().reverse().map((a,ri)=>{const i=atts.length-1-ri; return `<div class="att"><div class="badge">${a.score}</div><div class="grow"><b>第 ${i+1} 次</b> <span class="chip">${modeLabel(a.mode)}</span> ${a.mode==="full"?"<span class='chip unit'>正式</span>":""}<div class="muted small">答對 ${a.correct}/${a.total} 題・${fmtDur(a.durationSec)}・${fmtDate(a.date)}</div></div><button class="btn sm" onclick="viewSavedResult('${encodeURIComponent(name)}',${i})">解析</button></div>`;}).join("") : `<p class="muted">還沒有紀錄，開始第一次練習吧。</p>`;
  let weak="";
  if(last){const us=Object.entries(unitStats(last)).filter(([,v])=>v.correct/v.total<0.7).sort((a,b)=>a[1].correct/a[1].total-b[1].correct/b[1].total); if(us.length) weak=`<div class="card"><h3>最近弱點單元</h3><div class="row">${us.map(([u,v])=>`<span class="chip bad">${esc(u)} ${v.correct}/${v.total}</span>`).join("")}</div></div>`;}
  app.innerHTML=`
    <div class="spread"><div class="brand"><div class="logo">自</div><div><h1>${esc(name)} 的練習室</h1><div class="sub">${esc(QUIZ.title)}・${QUIZ.subject}</div></div></div><button class="btn sm ghost" onclick="viewLogin()">切換</button></div>
    <div class="card"><h3>選擇練習方式</h3><p class="muted small">${QUIZ.questions.length} 題，每題 ${QUIZ.perScore} 分，滿分 ${QUIZ.totalScore} 分。</p><div class="modegrid">
      <button class="modecard" onclick="startMode('${encodeURIComponent(name)}','practice')"><div class="mi">⚡</div><div class="mt">隨手練習</div><div class="md">隨機出題，選完立即看正解與詳解。</div></button>
      <button class="modecard" onclick="startMode('${encodeURIComponent(name)}','full')"><div class="mi">📝</div><div class="mt">正式測驗</div><div class="md">整卷作答，最後一次評分與單元診斷。</div></button>
      <button class="modecard" ${wrong.length?`onclick="startMode('${encodeURIComponent(name)}','wrong')"`:"disabled"}><div class="mi">🎯</div><div class="mt">錯題練習</div><div class="md">${wrong.length?`練最近錯的 ${wrong.length} 題。`:"先完成一次練習就會出現錯題。"}</div></button>
    </div><div style="height:12px"></div><button class="btn sm" onclick="exportProfile('${encodeURIComponent(name)}')">⬇️ 匯出我的練習紀錄給老師</button> <span id="cloudStatus" class="chip ${cloudOn()?"good":"warn"}">${cloudOn()?"雲端同步已啟用":"本機保存模式"}</span></div>
    ${weak}<div class="card"><h3>練習紀錄 <span class="muted small">${atts.length}次</span></h3>${hist}</div>
    <div class="foot"><a href="teacher.html">教師版入口</a> · <a href="../../index.html">系列首頁</a></div>`;
}
window.startMode=function(enc,mode){
  const name=decodeURIComponent(enc); const prof=getProfile(name); let ids=QUIZ.questions.map(q=>q.no);
  if(mode==="practice") ids=shuffle(ids);
  if(mode==="wrong"){ids=latestWrongIds(prof); if(!ids.length){alert("目前沒有錯題可練。"); return;}}
  session={name,mode,ids,i:0,answers:{},revealed:{},start:now(),saved:false}; renderQuestion();
};
function renderQuestion(){
  const no=session.ids[session.i]; const q=QMAP[no]; const chosen=session.answers[no]; const reveal=!!session.revealed[no];
  app.innerHTML=`
    <div class="spread"><div><h2>${modeLabel(session.mode)} <span class="muted small">${session.i+1}/${session.ids.length}</span></h2><div class="sub">${esc(q.unit)}</div></div><button class="btn sm ghost" onclick="viewDashboard('${esc(session.name)}')">離開</button></div>
    <div class="card tight">${progressHTML()}</div>
    <div class="grid"><div class="card col-8"><div class="spread"><div class="row"><span class="chip unit">第 ${q.no} 題</span><span class="chip">${esc(q.unit)}</span></div>${reveal?`<span class="chip ${chosen===q.answer?"good":"bad"}">${chosen===q.answer?"答對":"答錯"}</span>`:""}</div>${sourceHTML(q)}${optionHTML(q, chosen, reveal)}${reveal?`<div class="explain"><b>正解：${q.answer}</b><br>${esc(q.explanation)}</div>`:""}</div>
      <div class="card col-4"><h3>題號</h3><div class="qnav">${session.ids.map((id,idx)=>{const ans=session.answers[id]; const qq=QMAP[id]; let cls=idx===session.i?"cur":""; if(ans) cls+=" done"; if(session.revealed[id]) cls += ans===qq.answer?" right":" wrong"; return `<button class="${cls}" onclick="jump(${idx})">${id}</button>`;}).join("")}</div><p class="muted small">正式測驗會在交卷後才顯示正解；隨手練習會立即顯示。</p></div></div>
    <div class="stickybar"><div class="spread"><button class="btn" onclick="prevQ()" ${session.i===0?"disabled":""}>← 上一題</button><div class="row"><button class="btn" onclick="nextQ()" ${session.i===session.ids.length-1?"disabled":""}>下一題 →</button><button class="btn primary" onclick="finishSession()">${Object.keys(session.answers).length===session.ids.length?"交卷 / 結算":"結算目前作答"}</button></div></div></div>`;
}
window.choose=function(L){const no=session.ids[session.i]; session.answers[no]=L; if(session.mode!=="full") session.revealed[no]=true; renderQuestion();};
window.jump=function(i){session.i=i;renderQuestion();};
window.prevQ=function(){if(session.i>0){session.i--;renderQuestion();}};
window.nextQ=function(){if(session.i<session.ids.length-1){session.i++;renderQuestion();}};
window.finishSession=function(){
  if(session.mode==="full" && Object.keys(session.answers).length < session.ids.length && !confirm("還有題目未作答，確定要交卷嗎？")) return;
  const att=buildAttempt(session); saveAttempt(att); viewResult(att, true);
};
function buildAttempt(s){
  const wrongIds=[]; let correct=0;
  s.ids.forEach(no=>{const q=QMAP[no]; if(s.answers[no]===q.answer) correct++; else wrongIds.push(no);});
  return {quizId:QUIZ.id, quizTitle:QUIZ.title, subject:QUIZ.subject, mode:s.mode, ids:s.ids.slice(), answers:Object.assign({},s.answers), wrongIds, correct, total:s.ids.length, score:scoreOf(correct,s.ids.length), date:now(), durationSec:Math.max(1,Math.round((now()-s.start)/1000))};
}
function saveAttempt(att){
  if(session.saved) return; session.saved=true;
  const count=updateProfile(session.name, p=>{p.attempts.push(att);}).attempts.length;
  att.attemptNo=count; cloudPush(att, session.name);
}
function viewResult(att, fresh){
  const byUnit=Object.entries(unitStats(att)).sort((a,b)=>a[0].localeCompare(b[0],"zh-Hant"));
  const diag=byUnit.map(([u,v])=>`<tr><td><span class="chip unit">${esc(u)}</span></td><td class="right">${v.correct}/${v.total}</td><td><div class="minibar"><span style="width:${pct(v.correct,v.total)}%;background:${v.correct/v.total>=.7?'var(--good)':v.correct/v.total>=.4?'var(--warn)':'var(--bad)'}"></span></div></td><td class="right">${pct(v.correct,v.total)}%</td></tr>`).join("");
  const review=att.ids.map(no=>{const q=QMAP[no], ans=att.answers[no]||"未作答", ok=ans===q.answer; return `<div class="card tight"><div class="spread"><div><span class="chip ${ok?'good':'bad'}">第${no}題 ${ok?'✓':'✗'}</span> <span class="chip unit">${esc(q.unit)}</span></div><b>你的答案：${ans}　正解：${q.answer}</b></div>${sourceHTML(q)}<div class="explain">${esc(q.explanation)}</div></div>`;}).join("");
  app.innerHTML=`<div class="spread"><div class="brand"><div class="logo">${att.score}</div><div><h1>練習結果</h1><div class="sub">${modeLabel(att.mode)}・${fmtDur(att.durationSec)}</div></div></div><button class="btn sm ghost" onclick="viewDashboard('${esc(session?.name || loadDB().last || '')}')">回練習室</button></div>
  <div class="card center"><div class="score">${att.score}</div><h3>答對 ${att.correct}/${att.total} 題</h3><p id="cloudStatus" class="chip ${cloudOn()?"":"warn"}">${fresh && cloudOn()?"雲端上傳中…":"已保存在本機"}</p></div>
  <div class="card"><h3>單元診斷</h3><table><tr><th>單元</th><th class="right">答對</th><th>比例</th><th class="right">%</th></tr>${diag}</table></div>
  <div class="spread"><h3>逐題解析</h3><button class="btn sm" onclick="window.print()">列印</button></div>${review}`;
}
window.viewSavedResult=function(enc,i){const name=decodeURIComponent(enc);const att=(getProfile(name).attempts||[]).filter(a=>a.quizId===QUIZ.id)[i];session={name};viewResult(att,false);};
window.exportProfile=function(enc){
  const name=decodeURIComponent(enc); const prof=getProfile(name); const payload={type:"cap-review-student-export",version:1,quizId:QUIZ.id,quizTitle:QUIZ.title,name,exportedAt:new Date().toISOString(),attempts:(prof.attempts||[]).filter(a=>a.quizId===QUIZ.id)};
  const blob=new Blob([JSON.stringify(payload,null,2)],{type:"application/json;charset=utf-8"}); const a=document.createElement("a"); a.href=URL.createObjectURL(blob); a.download=`cap-review-${QUIZ.id}-${name}.json`; a.click(); URL.revokeObjectURL(a.href);
};

installTheme();
viewLogin();
if(cloudOn()) flushPendingCloud();
