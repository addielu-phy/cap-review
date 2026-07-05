"use strict";

const QUIZ = window.QUIZ;
const app = document.getElementById("app");
const QMAP = Object.fromEntries(QUIZ.questions.map(q => [q.no, q]));
const STORE = `cap_teacher_${QUIZ.id}`;
let rows = [];
let dataSource = "local";
let lastCloudLoad = 0;

function esc(s){return String(s ?? "").replace(/[&<>"']/g, c => ({"&":"&amp;","<":"&lt;",">":"&gt;","\"":"&quot;","'":"&#39;"}[c]));}
function fmtDate(ts){if(!ts)return "—"; const d=new Date(ts); const p=n=>String(n).padStart(2,"0"); return `${d.getFullYear()}/${p(d.getMonth()+1)}/${p(d.getDate())} ${p(d.getHours())}:${p(d.getMinutes())}`;}
function pct(n,d){return d ? Math.round(n/d*100) : 0;}
function loadRows(){try{return JSON.parse(localStorage.getItem(STORE)) || [];}catch(e){return [];}}
function saveRows(){localStorage.setItem(STORE, JSON.stringify(rows));}
function cloudOn(){return !!(window.CLOUD && CLOUD.enabled && window.firebase && CLOUD.config && CLOUD.config.projectId);}
function cloudInit(){if(cloudOn() && !firebase.apps.length) firebase.initializeApp(CLOUD.config);}
function tsMillis(v){
  if(!v) return 0;
  if(typeof v === "number") return v;
  if(typeof v === "string") return Date.parse(v) || 0;
  if(v.toMillis) return v.toMillis();
  if(v.toDate) return v.toDate().getTime();
  if(v.seconds) return v.seconds * 1000;
  return 0;
}
function installTheme(){
  const saved=localStorage.getItem("cap_theme") || "dark";
  document.documentElement.dataset.theme=saved;
  const btn=document.getElementById("themeToggle");
  if(btn){btn.textContent=saved==="light"?"🌙":"☀️"; btn.onclick=()=>{const cur=document.documentElement.dataset.theme==="light"?"dark":"light";document.documentElement.dataset.theme=cur;localStorage.setItem("cap_theme",cur);btn.textContent=cur==="light"?"🌙":"☀️";};}
}
function normalizeAttempt(att, fallbackName){
  if(!att || !att.ids || !att.answers) return null;
  const ids = att.ids.map(Number).filter(n => QMAP[n]);
  const answers = att.answers || {};
  const wrongIds = (att.wrongIds && att.wrongIds.length) ? att.wrongIds.map(Number) : ids.filter(no => answers[no] !== QMAP[no].answer);
  const correct = typeof att.correct === "number" ? att.correct : ids.length - wrongIds.length;
  return {
    name: att.name || fallbackName || "未命名",
    quiz: att.quiz || att.quizId || QUIZ.id,
    quizId: att.quizId || att.quiz || QUIZ.id,
    quizTitle: att.quizTitle || QUIZ.title,
    subject: att.subject || QUIZ.subject,
    mode: att.mode || "full",
    attemptNo: att.attemptNo || att.n || null,
    ids, answers, wrongIds,
    correct, total: att.total || ids.length,
    score: typeof att.score === "number" ? att.score : Math.round(correct * (QUIZ.perScore || 2)),
    date: tsMillis(att.ts) || tsMillis(att.date) || tsMillis(att.clientTime) || Date.now(),
    durationSec: att.durationSec || 0,
    importedAt: Date.now(),
    cloudDocId: att.cloudDocId || ""
  };
}
function isThisQuiz(r){return !r || !r.quizId ? true : (r.quizId === QUIZ.id || r.quiz === QUIZ.id);}
function addPayload(payload){
  let added=0;
  if(Array.isArray(payload)){
    payload.forEach(p => { const n=normalizeAttempt(p, p.name); if(n && isThisQuiz(n)){rows.push(n); added++;} });
  } else if(payload && payload.type === "cap-review-student-export"){
    (payload.attempts || []).forEach(a => { const n=normalizeAttempt(a, payload.name); if(n && isThisQuiz(n)){rows.push(n); added++;} });
  } else if(payload && payload.attempts){
    (payload.attempts || []).forEach(a => { const n=normalizeAttempt(a, payload.name); if(n && isThisQuiz(n)){rows.push(n); added++;} });
  } else {
    const n=normalizeAttempt(payload, payload && payload.name); if(n && isThisQuiz(n)){rows.push(n); added++;}
  }
  dedupeAndSort();
  if(dataSource === "local") saveRows();
  return added;
}
function dedupeAndSort(){
  const seen=new Set();
  rows = rows.filter(r => { const key=[r.cloudDocId,r.name,r.date,r.mode,r.score,(r.wrongIds||[]).join("-")].join("|"); if(seen.has(key)) return false; seen.add(key); return true; });
  rows.sort((a,b)=>(b.date||0)-(a.date||0));
}
function stats(){
  const full = rows.filter(r => r.mode === "full");
  const assessable = rows.filter(r => r.ids && r.ids.length);
  const students = {};
  rows.forEach(r => { const k=r.name || "未命名"; if(!students[k]) students[k]=[]; students[k].push(r); });
  const qAtt = {}, qWrong = {};
  QUIZ.questions.forEach(q => { qAtt[q.no]=0; qWrong[q.no]=0; });
  assessable.forEach(r => {
    (r.ids || []).forEach(no => { if(qAtt[no] !== undefined) qAtt[no]++; });
    (r.wrongIds || []).forEach(no => { if(qWrong[no] !== undefined) qWrong[no]++; });
  });
  const qStats = QUIZ.questions.map(q => ({no:q.no, unit:q.unit, answer:q.answer, attempts:qAtt[q.no]||0, wrong:qWrong[q.no]||0, rate:qAtt[q.no]?qWrong[q.no]/qAtt[q.no]:0}));
  const unitMap = {};
  QUIZ.questions.forEach(q => { if(!unitMap[q.unit]) unitMap[q.unit]={unit:q.unit, attempts:0, wrong:0, qn:0}; unitMap[q.unit].qn++; });
  qStats.forEach(q => { unitMap[q.unit].attempts += q.attempts; unitMap[q.unit].wrong += q.wrong; });
  const scores = full.map(r => r.score);
  return {full, assessable, students, qStats, units:Object.values(unitMap), avg:scores.length?Math.round(scores.reduce((a,b)=>a+b,0)/scores.length):null, max:scores.length?Math.max(...scores):null, min:scores.length?Math.min(...scores):null};
}
function cloudBadge(){
  if(dataSource === "cloud") return `<span class="chip good">Firebase 雲端同步</span><span class="chip">${CLOUD.config.projectId}</span><span class="chip">${rows.length} 筆</span>`;
  return `<span class="chip warn">本機匯入模式</span>`;
}
function render(){
  const st = stats();
  const studentRows = Object.entries(st.students).sort(([a],[b])=>a.localeCompare(b,"zh-Hant")).map(([name,rs]) => {
    const latest = rs.slice().sort((a,b)=>(b.date||0)-(a.date||0))[0];
    const best = Math.max(...rs.map(r=>r.score));
    return `<tr><td>${esc(name)}</td><td class="right">${rs.length}</td><td class="right"><b>${best}</b></td><td class="right">${latest.score}</td><td class="small muted">${fmtDate(latest.date)}</td></tr>`;
  }).join("") || `<tr><td colspan="5" class="muted">尚無學生紀錄</td></tr>`;
  const wrongRows = st.qStats.filter(q=>q.attempts>0).sort((a,b)=>b.rate-a.rate || b.wrong-a.wrong).slice(0,20).map(q => `
    <tr><td><b>${q.no}</b></td><td><span class="chip unit">${esc(q.unit)}</span></td><td>${q.answer}</td><td class="right">${q.wrong}/${q.attempts}</td><td><div class="minibar"><span style="width:${pct(q.wrong,q.attempts)}%;background:${q.rate>=.4?'var(--bad)':q.rate>=.2?'var(--warn)':'var(--good)'}"></span></div></td><td class="right">${pct(q.wrong,q.attempts)}%</td></tr>`).join("") || `<tr><td colspan="6" class="muted">學生交卷上傳後會顯示全班最常錯題</td></tr>`;
  const unitRows = st.units.sort((a,b)=>(b.attempts?b.wrong/b.attempts:0)-(a.attempts?a.wrong/a.attempts:0)).map(u => `
    <tr><td>${esc(u.unit)}</td><td class="right">${u.qn}</td><td class="right">${u.wrong}/${u.attempts || 0}</td><td><div class="minibar"><span style="width:${pct(u.wrong,u.attempts)}%;background:${(u.attempts && u.wrong/u.attempts>=.4)?'var(--bad)':(u.attempts && u.wrong/u.attempts>=.2)?'var(--warn)':'var(--good)'}"></span></div></td><td class="right">${pct(u.wrong,u.attempts)}%</td></tr>`).join("");

  const cloudControls = dataSource === "cloud" ? `
    <div class="card">
      <div class="spread"><div><h3>雲端資料庫</h3><p class="muted small">學生交卷會寫入 Firebase Firestore <code>results</code> 集合；老師登入後可在任何手機、電腦或不同 Hermes 主機看同一份資料。</p></div>${cloudBadge()}</div>
      <div class="row" style="margin-top:12px"><button class="btn primary" onclick="reloadCloud()">重新讀取雲端</button><button class="btn" onclick="exportCSV()">匯出 CSV</button><button class="btn ghost" onclick="window.print()">列印</button><button class="btn ghost" onclick="doLogout()">登出</button></div>
      <p class="muted small">最後讀取：${fmtDate(lastCloudLoad)}</p>
    </div>` : `
    <div class="card">
      <h3>匯入學生練習紀錄</h3>
      <p class="muted small">Firebase 尚未啟用時，可先用本機 JSON 匯入備用。啟用後學生交卷會自動同步，不必再手動傳檔。</p>
      <input id="fileIn" type="file" accept="application/json,.json" multiple>
      <div class="row" style="margin-top:12px"><button class="btn primary" onclick="importFiles()">匯入 JSON</button><button class="btn" onclick="exportCSV()">匯出 CSV</button><button class="btn ghost" onclick="window.print()">列印</button><button class="btn bad" onclick="clearRows()">清空匯入資料</button></div>
      <p class="muted small">目前模式：本機匯入統計（不需要登入，不上傳學生資料）</p>
    </div>`;

  app.innerHTML = `
    <div class="spread"><div class="brand"><div class="logo">師</div><div><h1>教師版｜${esc(QUIZ.title)}</h1><div class="sub">${esc(QUIZ.subject)}・全班成績與錯題統計</div></div></div><a class="btn sm ghost" href="index.html">學生端</a></div>
    ${cloudControls}
    <div class="card"><h3>班級概況</h3><div class="kpi"><div class="b"><div class="n">${Object.keys(st.students).length}</div><div class="t">學生人數</div></div><div class="b"><div class="n">${rows.length}</div><div class="t">作答紀錄</div></div><div class="b"><div class="n">${st.avg ?? '—'}</div><div class="t">全卷平均</div></div><div class="b"><div class="n">${st.max ?? '—'}</div><div class="t">最高分</div></div></div></div>
    <div class="grid"><section class="card col-6"><h3>❌ 全班最常錯題</h3><table><tr><th>題</th><th>單元</th><th>正解</th><th class="right">錯/答</th><th>錯誤率</th><th class="right">%</th></tr>${wrongRows}</table></section><section class="card col-6"><h3>📚 單元弱點</h3><table><tr><th>單元</th><th class="right">題數</th><th class="right">錯/答</th><th>錯誤率</th><th class="right">%</th></tr>${unitRows}</table></section></div>
    <div class="card"><h3>👩‍🎓 學生列表</h3><table><tr><th>學生</th><th class="right">次數</th><th class="right">最佳</th><th class="right">最近</th><th>最近作答</th></tr>${studentRows}</table></div>
    <div class="foot">${dataSource === "cloud" ? "資料來源：Firebase Firestore。" : "教師版資料只存於此瀏覽器 localStorage。"}</div>`;
}
function renderLogin(msg=""){
  const teacher=CLOUD.teacherEmail || "老師 Google/Email 帳號";
  app.innerHTML = `
    <div class="brand"><div class="logo">師</div><div><h1>教師版雲端登入</h1><div class="sub">跨裝置查看全班練習紀錄</div></div></div>
    <div class="card">
      ${msg ? `<p class="chip bad">${esc(msg)}</p>` : ""}
      <p class="muted small">請用老師帳號登入：<b>${esc(teacher)}</b>。登入後會讀取 Firebase Firestore 的全班紀錄。</p>
      <div class="row"><button class="btn primary" onclick="doGoogleLogin()">使用 Google 登入</button></div>
      <hr style="border:none;border-top:1px solid var(--line);margin:18px 0">
      <label class="lbl">Email / 密碼登入</label>
      <input type="email" id="em" placeholder="teacher@example.com" autocomplete="username" value="${CLOUD.teacherEmail ? esc(CLOUD.teacherEmail) : ""}">
      <div style="height:10px"></div>
      <input type="password" id="pw" placeholder="Firebase Authentication 密碼" autocomplete="current-password" onkeydown="if(event.key==='Enter')doEmailLogin()">
      <div style="height:12px"></div><button class="btn" onclick="doEmailLogin()">Email 登入</button>
      <p class="muted small">若 Google 登入顯示 provider 未啟用，請改用 Email/Password，或到 Firebase Authentication 啟用 Google provider。</p>
    </div>`;
}
window.doGoogleLogin=function(){
  const provider=new firebase.auth.GoogleAuthProvider();
  firebase.auth().signInWithPopup(provider).catch(e => {
    if(String(e.code || "").includes("popup")) return firebase.auth().signInWithRedirect(provider);
    renderLogin(`Google 登入失敗：${e.code || e.message}`);
  });
};
window.doEmailLogin=function(){
  const em=document.getElementById("em").value.trim();
  const pw=document.getElementById("pw").value;
  if(!em || !pw){alert("請輸入 Email 與密碼"); return;}
  firebase.auth().signInWithEmailAndPassword(em, pw).catch(e => renderLogin(`Email 登入失敗：${e.code || e.message}`));
};
window.doLogout=function(){firebase.auth().signOut();};
async function loadCloudRows(user){
  app.innerHTML = `<div class="card center"><p>讀取 Firebase 全班紀錄中…</p></div>`;
  try{
    const snap = await firebase.firestore().collection("results").orderBy("ts", "desc").limit(1000).get();
    rows = snap.docs.map(d => normalizeAttempt(Object.assign({cloudDocId:d.id}, d.data()), d.data().name)).filter(Boolean).filter(isThisQuiz);
    dedupeAndSort(); dataSource="cloud"; lastCloudLoad=Date.now(); render();
  }catch(e){
    app.innerHTML = `<div class="brand"><div class="logo">師</div><div><h1>教師版讀取失敗</h1><div class="sub">${esc(user.email)}</div></div></div>
    <div class="card"><p class="chip bad">${esc(e.code || e.message)}</p>
    <p class="muted small">常見原因：Firestore 規則尚未允許這個老師 Email 讀取，或 Firebase Auth provider 未啟用。</p>
    <div class="row"><button class="btn primary" onclick="reloadCloud()">重試</button><button class="btn ghost" onclick="doLogout()">登出</button><button class="btn" onclick="useLocalFallback()">改用本機匯入模式</button></div></div>`;
  }
}
window.reloadCloud=function(){const user=firebase.auth().currentUser; if(user) loadCloudRows(user); else renderLogin();};
window.useLocalFallback=function(){dataSource="local"; rows=loadRows(); render();};
window.importFiles = async function(){
  const input=document.getElementById("fileIn");
  const files=[...(input.files||[])];
  if(!files.length){alert("請先選擇學生 JSON 檔"); return;}
  let added=0, failed=[];
  for(const file of files){
    try{ const txt=await file.text(); const payload=JSON.parse(txt); added += addPayload(payload); }
    catch(e){ failed.push(file.name); }
  }
  render();
  alert(`匯入 ${added} 筆紀錄${failed.length?`；失敗：${failed.join(', ')}`:''}`);
};
window.clearRows = function(){ if(confirm("確定清空教師版已匯入資料？學生端原始 JSON 不受影響。")){ rows=[]; saveRows(); render(); } };
window.exportCSV = function(){
  const header=["name","date","mode","score","correct","total","wrongIds","unitWeakness","source"];
  const lines=[header.join(",")];
  rows.forEach(r=>{
    const unitWrong={}; (r.wrongIds||[]).forEach(no=>{const q=QMAP[no]; if(q) unitWrong[q.unit]=(unitWrong[q.unit]||0)+1;});
    const vals=[r.name, fmtDate(r.date), r.mode, r.score, r.correct, r.total, (r.wrongIds||[]).join(" "), Object.entries(unitWrong).map(([u,n])=>`${u}:${n}`).join(";"), dataSource];
    lines.push(vals.map(v=>`"${String(v).replace(/"/g,'""')}"`).join(","));
  });
  const blob=new Blob(["\ufeff"+lines.join("\n")],{type:"text/csv;charset=utf-8"});
  const a=document.createElement("a"); a.href=URL.createObjectURL(blob); a.download=`teacher-${QUIZ.id}-results.csv`; a.click(); URL.revokeObjectURL(a.href);
};
installTheme();
if(cloudOn()){
  cloudInit();
  firebase.auth().onAuthStateChanged(user => {
    if(!user){renderLogin(); return;}
    if(CLOUD.teacherEmail && user.email !== CLOUD.teacherEmail){const mail=user.email; firebase.auth().signOut().finally(()=>renderLogin(`此帳號（${mail}）不是授權老師帳號。`)); return;}
    loadCloudRows(user);
  });
}else{
  rows = loadRows();
  render();
}
