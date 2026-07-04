# 國中教育會考 · 自學複習系列

一系列把國中教育會考歷屆試題做成「可作答、自動評分、單元錯題分析、附詳解、可重複練習」的自學網站。
純前端（HTML/CSS/JS + localStorage，離線可用），部署於 GitHub Pages。老師端可選配 Firebase 集中看全班成績。

## 目前內容

| 科目 | 狀態 | 路徑 | 題數 |
|------|------|------|------|
| 自然 | ✅ 已上線 | [`nature/`](nature/) | 114 年會考 50 題（生物・理化・地科） |
| 國文 | 🚧 規劃中 | `chinese/` | — |
| 英語 | 🚧 規劃中 | `english/` | — |
| 數學 | 🚧 規劃中 | `math/` | — |
| 社會 | 🚧 規劃中 | `social/` | — |

- 首頁（學科入口）：`index.html`
- 學生端（自然）：`nature/index.html`
- 老師後台（自然）：`nature/teacher.html`

## 架構

```
site/
├── index.html          # 系列首頁：五科入口卡片（自然已上線，其餘「即將推出」）
├── hub.css             # 首頁樣式
├── style.css           # 共用主題樣式（深色/淺色 × 多強調色）
├── theme.js            # 右下角外觀切換器
└── nature/             # 自然科（完整的一份自學評量網站，自成一包）
    ├── index.html      # 學生端
    ├── app.js          # 主程式（登入 / 作答 / 評分 / 錯題分析 / 詳解）
    ├── style.css
    ├── theme.js
    ├── data.js         # ★ 題庫（QUIZ_META + 50 題）
    ├── teacher.html    # 老師後台
    ├── teacher.js
    ├── firebase-config.js
    └── assets/         # 試卷附圖（q*.png）
```

## 新增一個科目（例如國文）

1. 複製 `nature/` 整包成 `chinese/`。
2. 換掉 `chinese/data.js`（`QUIZ_META` 與 `QUESTIONS`），並把附圖放進 `chinese/assets/`。
   - `QUIZ_META.logo`（顯示用單字，如「國」）、`QUIZ_META.appName`（如「國文會考複習」）會自動套進介面。
3. 在首頁 `index.html` 把該科的 `<div class="subj soon">` 改成 `<a class="subj live" href="chinese/index.html">`，並更新徽章與說明。
4. `git add -A && git commit && git push`，Pages 自動更新。

## 換題目

編輯對應科目的 `data.js`（每題欄位：`id` 題號、`u` 單元、`s` 題幹(可含 HTML/表格)、`o` 四選項、
`a` 正解索引 0=A、`e` 詳解、`img` 附圖陣列、`oi` 選項是否在圖中），存檔後 push 即可。

## 老師後台（選配）

依 `nature/FIREBASE_SETUP.md` 建立 Firebase 專案，把設定填入 `nature/firebase-config.js` 並將 `enabled` 改為 `true`，
即可讓學生成績（隨手練習與正式測驗）上傳、由老師 Email 登入後台查看班級概況、最常錯題、單元弱點與學生明細（可匯出 CSV）。

---
題目來源為國中教育會考官方公開歷屆試題（cap.rcpet.edu.tw），僅供教育自學用途。
