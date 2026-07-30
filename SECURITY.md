# Security Policy

## Supported Versions

目前尚未發布可執行版本。首個 release後，本節將列出仍接受安全修補的版本。

## Reporting a Vulnerability

請勿在公開 Issue、Discussion、Pull Request、Log或截圖中揭露可利用細節、憑證、真實部署位址或財務資料。請使用 GitHub Private Vulnerability Reporting；若 repository尚未啟用該功能，請先提交不含細節的聯絡請求，由維護者提供私人通道。

報告應包含：

- 受影響版本或 commit SHA
- 可重現步驟
- 影響範圍
- 已確認不包含真實 secrets或財務資料的最小證據
- 建議修正（如有）

維護者將確認收到、評估影響、建立私人修正任務，完成測試後再發布修補與必要公告。

## Public Repository Rules

不得提交：

- `.env`或 secret file
- 密碼、Token、Cookie、session ID、API Key或加密私鑰
- OCI OCID、私人 IP、Tailscale tailnet／主機識別
- PostgreSQL dump、Object Storage備份或正式 audit log
- 真實金融帳戶、持股、資產金額或含真實資料的截圖／trace

若 secret曾進入 Git，僅刪除檔案不足以解除風險；必須立即撤銷／輪替，並依事件範圍處理 Git歷史。

## Security Boundaries

- 正式服務只透過 Tailscale存取，Tailscale Funnel禁用。
- Agent不取得正式 secrets、Docker socket、資料庫或備份解密私鑰。
- 正式部署、migration及還原需 Owner批准。
- Phase 0／1測試只使用合成資料。
