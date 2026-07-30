# Run database migrations as an explicit deployment step

Backend啟動時只檢查 schema revision，不自動執行 Alembic migration。正式 migration由 Owner核准的部署 wrapper在備份及驗證後執行，避免容器重啟或多實例競爭造成不可控 schema變更；無法安全 downgrade時以驗證過的備份還原。
