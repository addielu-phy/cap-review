# Firebase 雲端教師端（114 會考自然科）

目的：讓學生在 GitHub Pages 學生端交卷後，自動把練習紀錄寫入 Firebase Firestore；老師在 `teacher.html` 登入後，可跨手機、電腦與不同 Hermes 主機查看同一份全班資料。

## 已接上的檔案

- `science/114/firebase-config.js`：Firebase Web app 設定與老師 Email。
- `science/114/index.html`：載入 Firebase SDK 與設定。
- `shared/quiz-app.js`：學生交卷後寫入 Firestore `results` 集合；離線/失敗會暫存在本機，下次開頁補傳。
- `science/114/teacher.html` + `shared/teacher.js`：老師登入後讀 Firestore `results` 集合並統計全班錯題、單元弱點與 CSV。

## Firestore 資料形狀

集合：`results`

每筆學生紀錄大致包含：

```js
{
  name: "學生暱稱",
  quiz: "cap-114-science",
  quizId: "cap-114-science",
  quizTitle: "114年國中教育會考自然科",
  subject: "自然科",
  mode: "full" | "practice" | "wrong",
  score: 0-100,
  correct: 0-50,
  total: 50,
  ids: [1,2,3,...],
  answers: { "1": "C", "2": "B" },
  wrongIds: [ ... ],
  durationSec: 123,
  clientTime: 178...,     // 學生端時間
  ts: serverTimestamp()   // Firebase 伺服器時間
}
```

## 建議 Firestore Rules

把 `cylcphychem@gmail.com` 換成實際老師登入 Email（目前 `firebase-config.js` 使用此 Email）：

```js
rules_version = '2';
service cloud.firestore {
  match /databases/{database}/documents {
    match /results/{id} {
      allow create: if isValidSubmission(request.resource.data);
      allow read: if request.auth != null
        && request.auth.token.email == "cylcphychem@gmail.com";
      allow update, delete: if false;

      function isValidSubmission(d) {
        return d.name is string && d.name.size() > 0 && d.name.size() <= 40
          && d.quizId is string && d.quizId.size() <= 80
          && d.score is int && d.score >= 0 && d.score <= 100
          && d.correct is int && d.correct >= 0 && d.correct <= 50
          && d.total is int && d.total > 0 && d.total <= 50
          && d.ids is list && d.ids.size() > 0 && d.ids.size() <= 50
          && d.wrongIds is list && d.wrongIds.size() <= 50
          && d.ts == request.time;
      }
    }
  }
}
```

## Firebase Authentication

教師端支援兩種登入：

1. Google 登入：Firebase Authentication 要啟用 Google provider。
2. Email/Password：Firebase Authentication 要啟用 Email/Password，並建立老師帳號。

學生端不需要登入；交卷時只新增成績，不能讀取全班資料。
