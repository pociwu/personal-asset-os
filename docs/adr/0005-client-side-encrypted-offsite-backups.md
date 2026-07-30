# Encrypt backups before off-site storage

PostgreSQL dump先使用 `age`公開金鑰加密，再由 OCI Instance Principal上傳私人 Object Storage；主機不長期保存解密私鑰。此設計同時避免靜態 OCI使用者 API Key，並確保主機或 bucket權限單獨失陷時不能直接讀取歷史財務資料。
