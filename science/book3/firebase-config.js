/* ===========================================================
   雲端設定（Firebase）— 113–115第三冊理化25題教師端跨裝置成績
   -----------------------------------------------------------
   專案：cap-review（cap-review-c2f24）／沿用既有核准老師帳號。
   學生每次交卷（隨手練習＋完整測驗）會上傳到 Firestore，
   老師登入 science/book3/teacher.html 可依專屬 quizId 查看本題庫紀錄。
   =========================================================== */
window.CLOUD = {
  enabled: true,
  teacherEmail: "cylcphychem@gmail.com",   // 須與 Firestore 安全規則中的 Email 一致
  config: {
    apiKey: "AIzaSyDo_v6NF4lkmd-WEe6CVvweth4Y-O1-kv0",
    authDomain: "cap-review-c2f24.firebaseapp.com",
    projectId: "cap-review-c2f24",
    storageBucket: "cap-review-c2f24.firebasestorage.app",
    messagingSenderId: "875329911054",
    appId: "1:875329911054:web:e446db5ea5f663a0ce3f5f"
  }
};
