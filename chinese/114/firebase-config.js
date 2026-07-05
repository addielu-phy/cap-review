/* ===========================================================
   雲端設定（Firebase）— 114國文科教師端跨裝置集中收集全班成績用
   -----------------------------------------------------------
   專案：cap-review（cap-review-c2f24）／老師登入 Email：cylcphychem@gmail.com
   已啟用：學生每次交卷（隨手練習＋正式測驗）會上傳到 Firestore，
   老師以上述 Email 登入 chinese/114/teacher.html 即可跨裝置看全班成績。
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
