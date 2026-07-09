# 國中教育會考 · 自學複習系列

一系列把國中教育會考歷屆試題做成「可作答、自動評分、單元錯題分析、附詳解、可重複練習」的自學網站。
純前端（HTML/CSS/JS + localStorage，離線可用），部署於 GitHub Pages。老師端可選配 Firebase 集中看全班成績。

## 目前內容

| 科目 | 狀態 | 路徑 | 題數 |
|------|------|------|------|
| 自然 | ✅ 已上線 | [`science/114/`](science/114/) | 114 年會考 50 題（生物・理化・地科） |
| 自然暑期版 | ✅ 已上線 | [`science/114-summer/`](science/114-summer/) | 114 年會考精選 30 題（國一＋國二，排除國三理化・地科・天文） |
| 國文 | ✅ 已上線 | [`chinese/114/`](chinese/114/) | 114 年會考 42 題（單題＋題組閱讀） |
| 高一數學段考逐題詳解 | ✅ 已上線 | [`period-exams/math/khsh-114-2-mid2/`](period-exams/math/khsh-114-2-mid2/) | 高師大附中 114-2 第二次段考 16 題組（原題截圖＋詳細推導） |
| 英語 | 🚧 規劃中 | `english/` | — |
| 數學 | 🚧 規劃中 | `math/` | — |
| 社會 | 🚧 規劃中 | `social/` | — |

- 首頁（學科入口）：`index.html`
- 教師總覽：`teacher.html`
- 學生端（自然）：`science/114/index.html`
- 老師後台（自然）：`science/114/teacher.html`
- 學生端（自然暑期版）：`science/114-summer/index.html`
- 老師後台（自然暑期版）：`science/114-summer/teacher.html`
- 學生端（國文）：`chinese/114/index.html`
- 老師後台（國文）：`chinese/114/teacher.html`
- 段考逐題詳解（高一數學）：`period-exams/math/khsh-114-2-mid2/index.html`

## 架構

```
site/
├── index.html          # 系列首頁：五科入口卡片（自然已上線，其餘「即將推出」）
├── hub.css             # 首頁樣式
├── style.css           # 共用主題樣式（深色/淺色 × 多強調色）
├── theme.js            # 右下角外觀切換器
├── teacher.html        # 教師總覽：彙整各科學生端與老師後台
├── science/114/        # 自然科（共用 shared/ quiz app）
│   ├── index.html      # 學生端
│   ├── teacher.html    # 老師後台
│   ├── firebase-config.js
│   ├── data.js         # ★ 題庫（window.QUIZ + 50 題）
│   └── assets/         # 原題截圖
├── science/114-summer/ # 自然科暑期版（國一＋國二範圍，重用 science/114/assets）
│   ├── index.html      # 學生端
│   ├── teacher.html    # 老師後台
│   ├── firebase-config.js
│   ├── data.js         # ★ 題庫（window.QUIZ + 30 題）
│   └── README.md       # 篩選規則與題號
├── chinese/114/        # 國文科（共用 shared/ quiz app）
│   ├── index.html      # 學生端
│   ├── teacher.html    # 老師後台
│   ├── firebase-config.js
│   ├── data.js         # ★ 題庫（window.QUIZ + 42 題）
│   └── assets/         # 原題截圖與題組選文頁
├── period-exams/math/khsh-114-2-mid2/
│   ├── index.html      # 高一數學段考逐題詳解
│   ├── data.js         # 詳解資料（window.EXAM_QUESTIONS）
│   ├── solution.css
│   └── assets/         # 原題截圖與試卷頁面備查
└── nature/             # 舊版自然科原型（保留）
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

1. 複製 `science/114/` 整包成新路徑，例如 `social/114/`。
2. 換掉該科 `data.js`（`window.QUIZ`），並把原題截圖放進 `assets/`。
3. 在首頁 `index.html` 與教師總覽 `teacher.html` 加上學生端／教師端入口。
4. `git add -A && git commit && git push`，Pages 自動更新。

## 換題目

編輯對應科目的 `data.js`（每題欄位：`id` 題號、`u` 單元、`s` 題幹(可含 HTML/表格)、`o` 四選項、
`a` 正解索引 0=A、`e` 詳解、`img` 附圖陣列、`oi` 選項是否在圖中），存檔後 push 即可。

## 老師後台（選配）

目前 `science/114/`、`science/114-summer/` 與 `chinese/114/` 均使用 Firebase 專案 `cap-review-c2f24`，學生端交卷後寫入 Firestore `results` 集合，教師端依 `quizId` 分科／分版本過濾。老師 Email 設定於各科 `firebase-config.js`。

---
題目來源為國中教育會考官方公開歷屆試題（cap.rcpet.edu.tw），僅供教育自學用途。
