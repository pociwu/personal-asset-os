# Confirmed Decisions

本文件記錄已確認、但不需要獨立 ADR 的決策。重大且難以逆轉的取捨見 `docs/adr/`。

## Governance

- 系統擁有者擁有產品與高風險操作的最終決定權。
- AI-PM 是唯一派工、驗收及 Phase 推進入口，不直接修改產品程式碼。
- 開發型 Agent只執行單一已指派任務，不得部署、讀取正式 secrets或操作正式資料。
- 業務型 Agent在 Phase 0／1 不接觸正式財務資料；Phase 8 才使用受控唯讀查詢服務。
- 任務狀態為 `BACKLOG → READY → IN_PROGRESS → IN_REVIEW → VERIFIED → DONE`，另有 `BLOCKED`、`CANCELLED`。
- 一個任務、一個 `codex/<task-name>` 分支、一個語意單一 commit。

## Host and Deployment

- OCI：Ampere A1、Ubuntu 24.04 ARM64、2 OCPU、12 GB、至少 100 GB。
- 產品 Compose 只有 `web`、`backend`、`postgres`、`redis`。
- React只在 build stage執行；Phase 0／1 不部署產品 Worker／Scheduler。
- Tailscale Serve位於 Compose外；禁用 Funnel，Web不開放公網。
- 主機帳號分為 `admin`、`ai-pm`、`deploy`；Agent沒有 Docker socket或任意 sudo。
- 一般測試、ARM候選驗收與正式部署分離；候選及部署使用不同受限 wrapper。
- 磁碟 80% 警告、90% 停止 build、Playwright及還原演練。
- 每個產品容器一般 Log約 100 MB；systemd journal上限 500 MB。

## Phase 0 and Phase 1

- Phase 0 分成 `P0-001`～`P0-010`。
- Phase 1 分成 `P1-001`～`P1-011`。
- Phase 1 是 Mock功能驗證版；Phase 2 真實行情通過後才可標記日常可用。
- Phase 1 僅支援 TWSE／TPEx、TWD、非放空、彙總 Holding。
- Phase 1 不含買入／賣出；修改數量只代表修正現況。交易帳本留到 Phase 4。
- Phase 1 只提供簡單 Summary，不提供配置、排行、歷史、snapshot或 AI。

## Data and API

- 登入識別固定為 `owner`；業務資料不加入形式上的 `user_id`。
- 新增 Holding在單一 transaction內辨識／建立 Asset、建立 Holding及寫 audit。
- Phase 1 不提供獨立 Assets CRUD、Prices API或 `market_prices`。
- 同一金融帳戶＋Asset終生只有一筆 Holding，可封存及明確還原。
- Account有有效 Holding時不得封存。
- 不可逆刪除不屬於 Phase 1一般操作。
- Decimal使用 `NUMERIC(24,8)`、`ROUND_HALF_UP`；API Decimal以字串輸出。
- 衍生金額不保存於 Holding；先完整計算，最後量化。

## Authentication and Security

- Argon2id、30天滑動可撤銷 session、HttpOnly／Secure／SameSite Cookie。
- 寫入請求使用 CSRF Token＋Origin檢查；登入採限速及統一錯誤訊息。
- 一般設定與 secrets分離；正式 secrets存於專案外，Agent不得讀取。
- 應用 Log、audit log及安全事件分離。

## Backup

- Phase 0提供手動備份、驗證與隔離還原。
- Phase 1每日 03:00由 systemd timer執行。
- 使用 Instance Principal、`age`用戶端加密及私人 OCI Object Storage。
- 主機只長期保存加密公鑰；解密私鑰由 Owner離線保存。
- 本機7份、遠端30份每日、12份每月；RPO 24小時、RTO 2小時。
- Redis不備份；每月在隔離 PostgreSQL執行還原演練。

## Build, Test, and Publication

- 公開 GitHub repository名稱為 `personal-asset-os`，採 MIT License。
- `main`受保護；正式部署只接受核准 commit SHA。
- Backend使用 `uv`／`uv.lock`；Frontend使用 npm／`package-lock.json`。
- 不使用 `latest`；release記錄映像 digest及ARM64證據。
- Playwright只存在獨立 Ubuntu／glibc測試環境；Phase 1在 OCI ARM64執行 Chromium E2E。
- 公開 Git不得包含真實財務資料、secrets、備份、正式 Log、OCI／Tailscale識別資訊或敏感測試產物。

## Fixed Phase 1 Fixture

- Account：`測試證券帳戶`
- Market／Symbol：`TWSE`／`00919`
- Quantity：`40000`
- Average cost：`22.50`
- Mock price：`25.00`
- Cost：`900000.00`
- Market value：`1000000.00`
- Unrealized profit：`100000.00`
- UI return：`+11.11%`

## Document Authority

Owner最新決策 → accepted ADR → `CONTEXT.md` → `docs/governance/SYSTEM_SPEC.md` → `docs/governance/EXECUTION_PLAN.md` → `TASKS.md` → `docs/governance/PLAN_REPORT.md` → `README.md` → `docs/governance/CODEX_MASTER_PROMPT.md`。
