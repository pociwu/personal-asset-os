# Use a true single-owner data model

Personal Asset OS 是單一 Owner實例；Owner認證資料獨立保存，Account專指金融帳戶，Asset與Holding等業務資料不加入形式上的 `user_id`。多使用者與多租戶明確不在範圍內；若未來需要，必須重新設計隔離模型，而不是以一欄假裝完成。
