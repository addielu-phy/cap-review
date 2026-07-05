# Firebase 雲端教師端（114 會考國文科）

目的：讓學生在 `chinese/114/` 交卷後，自動把國文科練習紀錄寫入 Firebase Firestore；老師在 `chinese/114/teacher.html` 登入後，可跨手機、電腦與不同 Hermes 主機查看同一份全班資料。

## 路徑

- 學生端：`chinese/114/index.html`
- 教師端：`chinese/114/teacher.html`
- 彙整教師入口：`teacher.html`
- Firestore 集合：`results`
- 科目過濾欄位：`quizId = "cap-114-chinese"`

## 建議 Firestore Rules

同一 Firebase 專案可同時收自然與國文，只要用 `quizId` 區分。若老師帳號為 `cylcphychem@gmail.com`，可用：

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
          && d.score is number && d.score >= 0 && d.score <= 100
          && d.correct is int && d.correct >= 0 && d.correct <= 60
          && d.total is int && d.total > 0 && d.total <= 60
          && d.ids is list && d.ids.size() > 0 && d.ids.size() <= 60
          && d.wrongIds is list && d.wrongIds.size() <= 60
          && d.ts == request.time;
      }
    }
  }
}
```

學生端不需要登入，只能新增自己的作答紀錄；教師端需要 Firebase Auth 登入才能讀取全班。
