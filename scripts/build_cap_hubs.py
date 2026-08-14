#!/usr/bin/env python
"""Generate the three-year/five-subject hub, catalog data, and teacher hub."""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
YEARS = (115, 114, 113)
SUBJECTS = {
    "chinese": {"name": "國文", "icon": "國", "count": 42, "desc": "語文基礎、單題與題組閱讀"},
    "english": {"name": "英語", "icon": "英", "count": 64, "desc": "閱讀 43 題＋聽力 21 題與官方逐題音檔"},
    "math": {"name": "數學", "icon": "數", "count": 27, "desc": "選擇 25 題＋非選擇 2 題（非選題自行核對）"},
    "social": {"name": "社會", "icon": "社", "count": 54, "desc": "歷史、地理、公民與跨域題組"},
    "science": {"name": "自然", "icon": "自", "count": 50, "desc": "生物、理化、地科與探究題組"},
}

RESOURCES = [
    {
        "id": "science-book3-113-115",
        "title": "113–115 會考第三冊理化精選25題",
        "description": "嚴格篩選國二上第三冊範圍，六章各3–5題；支援隨機10題、完整25題、錯題練習與教師雲端紀錄。",
        "category": "正式自學",
        "kind": "國二上理化",
        "status": "recommended",
        "icon": "三",
        "meta": "113–115 年・第三冊・25 題",
        "href": "science/book3/",
        "teacherHref": "science/book3/teacher.html",
        "tags": ["113–115", "自然", "理化", "國二上", "第三冊", "25題"],
    },
    {
        "id": "science-114-summer",
        "title": "114 會考自然科暑期版",
        "description": "精選國一、國二範圍 30 題，保留官方題圖、自動評分、詳解與錯題練習。",
        "category": "正式自學",
        "kind": "精選題庫",
        "status": "live",
        "icon": "暑",
        "meta": "114 年・自然・30 題",
        "href": "science/114-summer/",
        "teacherHref": "science/114-summer/teacher.html",
        "tags": ["114", "自然", "國一", "國二", "暑假", "錯題"],
    },
    {
        "id": "science-fighter-years",
        "title": "自然科格鬥｜111–114 年度入口",
        "description": "四個年份、共 120 題的國一生物與國二理化完整題圖挑戰。",
        "category": "格鬥遊戲",
        "kind": "年度入口",
        "status": "recommended",
        "icon": "戰",
        "meta": "111–114 年・120 題",
        "href": "https://addielu-phy.github.io/cap-science-fighter-years/",
        "tags": ["自然", "生物", "理化", "年份入口", "遊戲"],
    },
    {
        "id": "science-fighter-111",
        "title": "111 會考科學格鬥",
        "description": "國一生物 14 題＋國二理化 16 題，支援 12 題快打、全題挑戰與錯題重練。",
        "category": "格鬥遊戲",
        "kind": "自然科",
        "status": "live",
        "icon": "111",
        "meta": "111 年・30 題",
        "href": "https://addielu-phy.github.io/cap-science-fighter-111-fit/",
        "tags": ["111", "自然", "生物", "理化", "遊戲"],
    },
    {
        "id": "science-fighter-112",
        "title": "112 會考科學格鬥",
        "description": "國一生物 16 題＋國二理化 14 題，完整題圖、計時挑戰與逐題詳解。",
        "category": "格鬥遊戲",
        "kind": "自然科",
        "status": "live",
        "icon": "112",
        "meta": "112 年・30 題",
        "href": "https://addielu-phy.github.io/cap-science-fighter-112-fit/",
        "tags": ["112", "自然", "生物", "理化", "遊戲"],
    },
    {
        "id": "science-fighter-113",
        "title": "113 會考科學格鬥",
        "description": "國一生物 13 題＋國二理化 15 題，完整題圖、快打與全題模式。",
        "category": "格鬥遊戲",
        "kind": "自然科",
        "status": "live",
        "icon": "113",
        "meta": "113 年・28 題",
        "href": "https://addielu-phy.github.io/cap-science-fighter-113-fit/",
        "tags": ["113", "自然", "生物", "理化", "遊戲"],
    },
    {
        "id": "science-fighter-114-fit",
        "title": "114 會考科學格鬥｜完整題圖版",
        "description": "國一生物 16 題＋國二理化 16 題；114 年目前建議使用的格鬥版。",
        "category": "格鬥遊戲",
        "kind": "自然科",
        "status": "recommended",
        "icon": "114",
        "meta": "114 年・32 題",
        "href": "https://addielu-phy.github.io/cap-science-fighter-114-fit/",
        "tags": ["114", "自然", "生物", "理化", "遊戲", "完整題圖"],
    },
    {
        "id": "science-fighter-114-legacy",
        "title": "114 會考科學格鬥｜早期版",
        "description": "保留舊連結使用；平常建議改用上方的完整題圖版。",
        "category": "舊版備用",
        "kind": "自然科舊版",
        "status": "legacy",
        "icon": "舊",
        "meta": "114 年・32 題",
        "href": "https://addielu-phy.github.io/cap-science-fighter-114/",
        "tags": ["114", "自然", "舊版", "備用"],
    },
    {
        "id": "english-fighter-years",
        "title": "英語格鬥｜113／114 年度入口",
        "description": "選擇年份後進入 43 題英語閱讀格鬥挑戰。",
        "category": "格鬥遊戲",
        "kind": "年度入口",
        "status": "recommended",
        "icon": "英",
        "meta": "113–114 年",
        "href": "https://addielu-phy.github.io/cap-english-fighter-years/",
        "tags": ["英語", "閱讀", "年份入口", "遊戲"],
    },
    {
        "id": "english-fighter-113",
        "title": "113 會考英語閱讀格鬥",
        "description": "43 題官方閱讀題面，每場可隨機 12 題，附計時與錯題重練。",
        "category": "格鬥遊戲",
        "kind": "英語閱讀",
        "status": "live",
        "icon": "E13",
        "meta": "113 年・43 題",
        "href": "https://addielu-phy.github.io/cap-english-fighter-113/",
        "tags": ["113", "英語", "閱讀", "遊戲"],
    },
    {
        "id": "english-fighter-114",
        "title": "114 會考英語閱讀格鬥",
        "description": "43 題官方閱讀題面，每場可隨機 12 題，附計時與錯題重練。",
        "category": "格鬥遊戲",
        "kind": "英語閱讀",
        "status": "live",
        "icon": "E14",
        "meta": "114 年・43 題",
        "href": "https://addielu-phy.github.io/cap-english-fighter/",
        "tags": ["114", "英語", "閱讀", "遊戲"],
    },
    {
        "id": "bio-fighter-114",
        "title": "114 會考生物格鬥",
        "description": "14 題生物題，涵蓋細胞、遺傳、生態、植物生理、人體恆定與科學探究。",
        "category": "格鬥遊戲",
        "kind": "生物",
        "status": "live",
        "icon": "生",
        "meta": "114 年・14 題",
        "href": "https://addielu-phy.github.io/cap-bio-fighter/",
        "tags": ["114", "自然", "生物", "遊戲"],
    },
    {
        "id": "history-cap-1-2",
        "title": "島嶼時光簿｜歷史第一、二冊",
        "description": "12 個核心單元、跨冊時間軸、48 題原創會考風格題與模擬測驗。",
        "category": "主題複習",
        "kind": "歷史",
        "status": "live",
        "icon": "史",
        "meta": "第一、二冊・48 題",
        "href": "https://addielu-phy.github.io/history-cap-review-1-2/",
        "tags": ["歷史", "第一冊", "第二冊", "模擬測驗"],
    },
    {
        "id": "civics-cap-1-2",
        "title": "公民一頁攻頂｜第一、二冊",
        "description": "六段核心整理，接續 111–114 年 20 題官方歷屆會考題。",
        "category": "主題複習",
        "kind": "公民",
        "status": "live",
        "icon": "公",
        "meta": "第一、二冊・20 題",
        "href": "https://addielu-phy.github.io/civics-cap-review-1-2/",
        "tags": ["公民", "第一冊", "第二冊", "官方歷屆題"],
    },
    {
        "id": "cap-115-physics",
        "title": "115 會考自然科物理試題整理",
        "description": "從自然科 50 題中整理 14 題物理相關題，依光、電、聲、力、熱與流體分類。",
        "category": "主題複習",
        "kind": "物理題整理",
        "status": "live",
        "icon": "物",
        "meta": "115 年・物理 14 題",
        "href": "https://addielu-phy.github.io/ai-coding-tools-free-comparison/exams/cap-115-nature-physics/",
        "tags": ["115", "自然", "物理", "試題整理"],
    },
    {
        "id": "summer-plan-2026",
        "title": "暑假會考複習每日進度表",
        "description": "7/10–8/31 共 53 天，安排五科、作文、模考、訂正與弱點補強。",
        "category": "讀書計畫",
        "kind": "每日進度",
        "status": "live",
        "icon": "程",
        "meta": "53 天・五科＋作文",
        "href": "https://addielu-phy.github.io/exam-review-summer-2026/",
        "tags": ["暑假", "進度", "模考", "訂正", "弱點補強"],
    },
    {
        "id": "physics-quiz",
        "title": "國二下理化期末自學評量",
        "description": "作答、自動評分、錯題分析與詳解；也是後續會考自學平台的重要前身。",
        "category": "相關題庫",
        "kind": "理化期末",
        "status": "live",
        "icon": "理",
        "meta": "國二下・50 題",
        "href": "https://addielu-phy.github.io/physics-quiz/",
        "teacherHref": "https://addielu-phy.github.io/physics-quiz/teacher.html",
        "tags": ["國二", "理化", "期末", "自動評分", "教師端"],
    },
    {
        "id": "wufu-friction",
        "title": "五福國中摩擦力歷屆題",
        "description": "近五年國二下定期評量摩擦力經典題，含互動測驗與觀念解析。",
        "category": "相關題庫",
        "kind": "五福國中",
        "status": "live",
        "icon": "摩",
        "meta": "國二下・摩擦力",
        "href": "https://addielu-phy.github.io/wu-fu-physics-quiz/",
        "tags": ["五福國中", "理化", "摩擦力", "段考"],
    },
    {
        "id": "wufu-buoyancy",
        "title": "五福國中浮力歷屆題",
        "description": "原題截圖、即時評分、錯題練習與詳解。",
        "category": "相關題庫",
        "kind": "五福國中",
        "status": "live",
        "icon": "浮",
        "meta": "國二下・浮力",
        "href": "https://addielu-phy.github.io/wu-fu-buoyancy-quiz/",
        "tags": ["五福國中", "理化", "浮力", "段考"],
    },
    {
        "id": "grade8-resources",
        "title": "國二學習資源總入口",
        "description": "彙整國二理化、數學、國文、英文、社會與錯題診斷資源。",
        "category": "資源總覽",
        "kind": "學習資源入口",
        "status": "live",
        "icon": "總",
        "meta": "國二・跨科",
        "href": "https://addielu-phy.github.io/ai-coding-tools-free-comparison/webpages/grade8-learning-resources/",
        "tags": ["國二", "跨科", "自學", "錯題"],
    },
    {
        "id": "all-webpages",
        "title": "盧老師全部網頁作品",
        "description": "依分類、關鍵字與狀態搜尋其他教學網站與互動作品。",
        "category": "資源總覽",
        "kind": "作品總覽",
        "status": "live",
        "icon": "網",
        "meta": "全部教學網頁",
        "href": "https://addielu-phy.github.io/ai-coding-tools-free-comparison/webpages/",
        "tags": ["作品", "總覽", "搜尋", "分類"],
    },
    {
        "id": "nature-114-legacy",
        "title": "114 自然科會考複習｜早期原型",
        "description": "保留歷史連結；平常建議使用三年五科中的 114 自然科正式版。",
        "category": "舊版備用",
        "kind": "自然科舊版",
        "status": "legacy",
        "icon": "舊",
        "meta": "114 年・自然",
        "href": "nature/",
        "tags": ["114", "自然", "舊版", "備用"],
    },
    {
        "id": "linear-motion-plan",
        "title": "106–115 直線運動互動題庫",
        "description": "Repository 已建立，但目前仍是空的，尚無可使用的網站。",
        "category": "規劃中",
        "kind": "自然科專題",
        "status": "planned",
        "icon": "規",
        "meta": "尚未上線",
        "repoHref": "https://github.com/addielu-phy/cap-linear-motion-10y",
        "tags": ["直線運動", "106–115", "規劃中"],
    },
]


def series_entries() -> list[dict]:
    rows = []
    for year in YEARS:
        for slug, meta in SUBJECTS.items():
            rows.append(
                {
                    "id": f"cap-{year}-{slug}",
                    "year": year,
                    "slug": slug,
                    "category": "三年五科",
                    "kind": "正式自學",
                    "status": "live",
                    "studentHref": f"{slug}/{year}/",
                    "teacherHref": f"{slug}/{year}/teacher.html",
                    "tags": [str(year), meta["name"], "官方題圖", "正式測驗", "錯題練習"],
                    **meta,
                }
            )
    return rows


def teacher_entries() -> list[dict]:
    rows = series_entries()
    rows.append(
        {
            "id": "cap-113-115-science-book3",
            "year": "113–115",
            "slug": "science",
            "name": "第三冊理化25題",
            "icon": "三",
            "count": 25,
            "desc": "國二上第三冊六章精選；隨機10題與完整25題",
            "studentHref": "science/book3/",
            "teacherHref": "science/book3/teacher.html",
        }
    )
    return rows


def catalog_page() -> str:
    return '''<!doctype html>
<html lang="zh-Hant">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">
  <meta name="theme-color" content="#0e1420">
  <title>會考自學總入口｜三年五科・格鬥遊戲・模擬練習</title>
  <meta name="description" content="彙整 113–115 會考三年五科 711 題、會考格鬥遊戲、歷史公民複習、讀書計畫、教師端與相關國中題庫。">
  <link rel="stylesheet" href="style.css">
  <link rel="stylesheet" href="hub.css">
</head>
<body>
<a class="skip-link" href="#catalogMain">跳到網站清單</a>
<main class="wrap catalog-wrap" id="catalogMain">
  <header class="catalog-hero">
    <div class="hero-copy">
      <span class="kicker">國中教育會考・自學網站全集</span>
      <h1>會考自學<span>總入口</span></h1>
      <p>三年五科、原題練習、正式測驗、錯題重練、格鬥遊戲與教師端，全部集中在這一頁。</p>
      <div class="hero-actions">
        <a class="btn primary" href="#series">開始三年五科</a>
        <a class="btn" href="#resources" data-set-category="格鬥遊戲">找格鬥遊戲</a>
        <a class="btn ghost" href="teacher.html">教師工作台</a>
      </div>
    </div>
    <div class="hero-stats" aria-label="網站統計">
      <div><strong>3</strong><span>年份</span></div>
      <div><strong>5</strong><span>科目</span></div>
      <div><strong>15</strong><span>正式題庫</span></div>
      <div><strong>711</strong><span>官方題目</span></div>
    </div>
  </header>

  <nav class="jump-nav" aria-label="頁面快速導覽">
    <a href="#series">三年五科</a><a href="#resources">延伸網站</a><a href="#about">使用說明</a><a href="teacher.html">教師端</a>
  </nav>

  <section class="catalog-controls" aria-labelledby="finderTitle">
    <div>
      <p class="eyebrow">FIND A SITE</p>
      <h2 id="finderTitle">快速找到要練的網站</h2>
    </div>
    <label class="search-box"><span>搜尋年份、科目或功能</span><input id="catalogSearch" type="search" placeholder="例如：115 自然、英語格鬥、模擬測驗" autocomplete="off"></label>
    <div class="category-filters" id="categoryFilters" aria-label="網站類型篩選"></div>
    <p class="catalog-summary" id="catalogSummary" aria-live="polite"></p>
  </section>

  <section class="catalog-section" id="series" data-catalog-section>
    <div class="section-heading"><div><p class="eyebrow">OFFICIAL PRACTICE</p><h2>113–115 三年五科</h2><p>每張卡都能直接進學生端，也能開啟該科教師端。</p></div><span class="section-count">15 個題庫・711 題</span></div>
    <div class="catalog-grid" id="seriesGrid"></div>
  </section>

  <section class="catalog-section" id="resources" data-catalog-section>
    <div class="section-heading"><div><p class="eyebrow">MORE WAYS TO PRACTICE</p><h2>遊戲、主題複習與相關網站</h2><p>完整保留新版、舊版、專題整理與國中段考自學站，狀態會明確標示。</p></div><span class="section-count" id="resourceCount"></span></div>
    <div class="catalog-grid" id="resourceGrid"></div>
  </section>

  <section class="info-band" id="about">
    <div><p class="eyebrow">HOW TO USE</p><h2>建議使用順序</h2></div>
    <ol>
      <li><b>先正式測驗：</b>選一個年份與科目，完成整卷後看單元診斷。</li>
      <li><b>再錯題重練：</b>針對最近答錯的題目反覆練習。</li>
      <li><b>最後換成遊戲：</b>用格鬥版做短時間計時挑戰，維持練習節奏。</li>
    </ol>
    <p class="source-note">題目、音檔與答案依國中教育會考官方公開資料整理；本站為自學用途，非官方網站。　<a href="https://cap.rcpet.edu.tw/examination.html" target="_blank" rel="noopener">查看官方歷屆試題</a></p>
  </section>

  <footer class="catalog-footer">會考自學總入口・學生端與教師端分流・規劃中網站不會假裝成已上線</footer>
</main>
<script src="catalog-data.js"></script>
<script src="catalog-app.js"></script>
<script src="theme.js"></script>
</body>
</html>\n'''


def teacher_page() -> str:
    rows = json.dumps(teacher_entries(), ensure_ascii=False)
    teacher_count = len(teacher_entries())
    year_filters = [{"v": str(y), "t": str(y) + " 年"} for y in YEARS]
    year_filters.append({"v": "113–115", "t": "113–115 精選"})
    return f'''<!doctype html>
<html lang="zh-Hant"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">
<meta name="theme-color" content="#0e1420"><title>教師工作台｜113–115 會考</title>
<meta name="description" content="113、114、115 年國中教育會考五科教師端與113–115第三冊理化精選教師端總入口。">
<link rel="stylesheet" href="style.css"><link rel="stylesheet" href="hub.css"></head><body><main class="wrap teacher-wrap">
<div class="hero"><span class="kicker">教師總覽・Firebase 雲端後台</span><h1>會考 <span class="grad">教師工作台</span></h1><p>彙整最近三年五科 15 個正式教師端，加上第三冊理化精選，共 {teacher_count} 個教師端。登入後依唯一 quizId 查看學生作答、全班最常錯題、單元弱點、學生列表與 CSV。</p></div>
<div class="info-card"><div class="filters" id="yearFilters" aria-label="年份篩選"></div><div class="filters" id="subjectFilters" aria-label="科目篩選"></div><div class="summary" id="summary" aria-live="polite"></div></div>
<div class="subjects" id="cards"></div>
<div class="info-card"><h3>使用提醒</h3><ul><li>教師端需使用核准的教師帳號登入。</li><li>每個年份與科目使用獨立 quizId，紀錄不會混在一起。</li><li>數學非選擇題保留學生自行核對，不混入自動評分。</li></ul></div>
<div class="foot"><a href="index.html">回會考自學總入口</a>　・　<a href="https://addielu-phy.github.io/physics-quiz/teacher.html" target="_blank" rel="noopener">國二理化教師端</a></div></main>
<script>const DATA={rows};let year='all',subject='all';
function esc(s){{return String(s??'').replace(/[&<>"']/g,c=>({{'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}}[c]));}}
function buttons(id,items,current,setter){{document.getElementById(id).innerHTML=items.map(x=>`<button class="filter ${{x.v===current?'active':''}}" data-v="${{esc(x.v)}}" aria-pressed="${{x.v===current}}">${{esc(x.t)}}</button>`).join('');document.querySelectorAll(`#${{id}} .filter`).forEach(b=>b.onclick=()=>setter(b.dataset.v));}}
function render(){{buttons('yearFilters',[{{v:'all',t:'全部年份'}},...{json.dumps(year_filters,ensure_ascii=False)}],year,v=>{{year=v;render()}});buttons('subjectFilters',[{{v:'all',t:'全部科目'}},...{json.dumps([{'v': s, 't': m['name']} for s,m in SUBJECTS.items()],ensure_ascii=False)}],subject,v=>{{subject=v;render()}});const list=DATA.filter(x=>(year==='all'||String(x.year)===year)&&(subject==='all'||x.slug===subject));document.getElementById('summary').textContent=`顯示 ${{list.length}} / {teacher_count} 個教師端`;
document.getElementById('cards').innerHTML=list.map(x=>`<article class="subj live"><div class="top"><div class="ico subject-${{esc(x.slug)}}">${{esc(x.icon)}}</div><div><div class="nm">${{esc(x.year)}} 會考${{esc(x.name)}}教師端</div><div class="en">${{esc(x.id)}}</div></div></div><div class="desc">${{esc(x.desc)}}。查看作答紀錄、成績與錯題統計。</div><div class="meta"><span class="chip unit">${{esc(x.year)}} 會考</span><span class="chip">${{esc(x.count)}} 題</span><span class="chip">需教師登入</span></div><div class="card-actions"><a class="btn primary sm" href="${{esc(x.teacherHref)}}">開啟教師端</a><a class="btn sm" href="${{esc(x.studentHref)}}">查看學生端</a></div></article>`).join('');}}
render();</script><script src="theme.js"></script></body></html>\n'''


def main() -> None:
    series = json.dumps(series_entries(), ensure_ascii=False, indent=2)
    resources = json.dumps(RESOURCES, ensure_ascii=False, indent=2)
    (ROOT / "catalog-data.js").write_text(
        f"window.CAP_SERIES = {series};\nwindow.CAP_RESOURCES = {resources};\n",
        encoding="utf-8",
    )
    (ROOT / "index.html").write_text(catalog_page(), encoding="utf-8")
    (ROOT / "teacher.html").write_text(teacher_page(), encoding="utf-8")
    print(f"wrote index.html, teacher.html, and catalog-data.js ({len(series_entries())} series + {len(RESOURCES)} resources)")


if __name__ == "__main__":
    main()
