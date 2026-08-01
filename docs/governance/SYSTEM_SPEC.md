# Personal Asset OS 系統規格

版本：2.1（Usable Alpha擴充）

> Usable Alpha為Owner在原始Phase規劃後確認的快速上線範圍。本文第15節在交易、真實估值及非股票資產方面，明確覆寫原始Phase 1的Mock與不含交易限制；其餘安全、Decimal、備份、ARM64及部署規則維持不變。

## 1. 技術與執行基線

- OS：Ubuntu 24.04 LTS ARM64
- OCI：Ampere A1，2 OCPU、12 GB RAM、至少 100 GB 系統碟
- Runtime：Docker Engine、Docker Compose v2
- Backend：Python 3.12、FastAPI、SQLAlchemy 2、Alembic、Pydantic 2
- Python 套件：`uv`、`uv.lock`、`uv sync --locked`
- Frontend：React、TypeScript、Vite
- Node 套件：npm、`package-lock.json`、`npm ci`
- Database：PostgreSQL 16
- Session／Cache：Redis 7
- Web：單一 Nginx 容器提供編譯後靜態檔並代理 `/api`
- Test：pytest、Vitest、Playwright
- Quality：ruff、mypy、eslint、prettier

不得使用 `latest`。正式 release 必須記錄 Git SHA、migration revision、映像 digest及 ARM64 驗收證據。所有正式執行依賴必須原生支援 `linux/arm64`。

## 2. 專案目錄

```text
personal-asset-os/
├── backend/
│   ├── app/
│   │   ├── api/
│   │   ├── core/
│   │   ├── models/
│   │   ├── schemas/
│   │   ├── services/
│   │   ├── providers/
│   │   └── main.py
│   ├── migrations/
│   ├── tests/
│   ├── pyproject.toml
│   ├── uv.lock
│   └── Dockerfile
├── frontend/
│   ├── src/
│   ├── tests/
│   ├── package.json
│   └── package-lock.json
├── deploy/
│   ├── nginx/
│   ├── systemd/
│   └── compose.yaml
├── scripts/
│   ├── deploy/
│   ├── backup/
│   └── verify/
├── docs/
│   ├── adr/
│   └── governance/
├── CONTEXT.md
├── TASKS.md
├── SECURITY.md
├── LICENSE
├── .env.example
├── .gitignore
└── README.md
```

## 3. 部署與網路

正式 Compose 只有：

- `web`
- `backend`
- `postgres`
- `redis`

React／Vite 只在 build stage 執行。Phase 0／1 不建立產品 Worker 或 Scheduler。

- Tailscale 安裝於主機，使用 Tailscale Serve 將 HTTPS 轉送至只綁定 `127.0.0.1` 的 `web`。
- 禁用 Tailscale Funnel及公開分享。
- OCI 不開放公網 80、443、5432、6379。
- Backend、PostgreSQL、Redis 不發布主機 Port。
- PostgreSQL 使用 named volume；不得自動刪除正式 volume。
- AI-PM、Agent、systemd timer及部署 wrapper不屬於產品 Compose。

## 4. Phase 1 資料模型

所有時間使用 `TIMESTAMPTZ` 並儲存 UTC。資料表命名僅為規格名稱，實作仍須由 migration 驗證 constraints 與 index。

### owners

- `id`: UUID，PK
- `login_name`: 固定 `owner`，unique
- `password_hash`: TEXT，Argon2id
- `is_active`: BOOLEAN
- `session_version`: INTEGER
- `created_at`, `updated_at`, `password_changed_at`: TIMESTAMPTZ

只允許一個 Owner。不提供註冊、第二個使用者或修改登入名稱 API。

### accounts

- `id`: UUID，PK
- `name`: VARCHAR(100)，required
- `institution`: VARCHAR(100)，nullable
- `account_type`: VARCHAR(30)，default `brokerage`
- `base_currency`: CHAR(3)，Phase 1 固定 `TWD`
- `archived_at`: TIMESTAMPTZ，nullable
- `created_at`, `updated_at`: TIMESTAMPTZ

`Account` 專指金融帳戶；不得用來表示登入身分。不同帳戶可以同名，以 UUID 區分。

### assets

- `id`: UUID，PK
- `market`: VARCHAR(20)，Phase 1 僅 `TWSE`、`TPEx`
- `symbol`: VARCHAR(30)，required
- `name`: VARCHAR(150)，required
- `asset_type`: VARCHAR(30)，required
- `currency`: CHAR(3)，Phase 1 固定 `TWD`
- `created_at`, `updated_at`: TIMESTAMPTZ
- unique：`market + symbol`

代號視為字串，必須保留前導零；正規化為去除首尾空白及大寫。

### holdings

- `id`: UUID，PK
- `account_id`: FK accounts
- `asset_id`: FK assets
- `quantity`: NUMERIC(24,8)，`CHECK quantity > 0`
- `average_cost`: NUMERIC(24,8)，`CHECK average_cost >= 0`
- `notes`: TEXT，nullable
- `archived_at`: TIMESTAMPTZ，nullable
- `created_at`, `updated_at`: TIMESTAMPTZ
- unique：`account_id + asset_id`，包含封存資料

同一金融帳戶＋Asset 終生只有一筆 Holding。Holding 是現況，不是交易。

### audit_logs

- `id`: BIGSERIAL，PK
- `owner_id`: FK owners
- `action`, `entity_type`, `entity_id`
- `before_data`, `after_data`: JSONB，僅保存必要業務變更
- `request_id`
- `created_at`: TIMESTAMPTZ

只允許新增；產品 API 不提供修改或刪除。不得保存密碼雜湊、Cookie、session ID、Token或 secret。

### backup_runs

- `id`: BIGSERIAL，PK
- `started_at`, `finished_at`
- `status`: running／succeeded／failed
- `checksum`
- `remote_object_id`
- `safe_error_code`

不得記錄金鑰、完整認證資訊或敏感檔名。

### Phase 2 之後

`market_prices`、portfolio snapshots、transactions、dividends及 cash flows 不在 Phase 1 migration。不得為未來功能提前建立空洞資料表。

## 5. Phase 1 API

除 `/health`、`/health/ready` 與登入外，所有 API 都需要 Owner session。

### Health

- `GET /api/v1/health`：只檢查 Backend 程序，正常回 `200`
- `GET /api/v1/health/ready`：檢查 PostgreSQL、Redis及 migration revision；未就緒回 `503`

不得在回應中輸出連線字串、內部路徑或詳細例外。

### Auth

- `POST /api/v1/auth/login`
- `POST /api/v1/auth/logout`
- `GET /api/v1/auth/session`

登入成功必須輪替 session ID。密碼變更、登出、停用 Owner或 session version 改變時撤銷 session。

### Accounts

- `GET /api/v1/accounts`
- `POST /api/v1/accounts` → `201`
- `GET /api/v1/accounts/{id}`
- `PATCH /api/v1/accounts/{id}`
- `DELETE /api/v1/accounts/{id}`：實際為封存
- `POST /api/v1/accounts/{id}/restore`

帳戶仍有有效 Holding 時，封存回 `409`。

### Holdings

- `GET /api/v1/holdings`
- `POST /api/v1/holdings` → `201`
- `GET /api/v1/holdings/{id}`
- `PATCH /api/v1/holdings/{id}`
- `DELETE /api/v1/holdings/{id}`：實際為封存
- `POST /api/v1/holdings/{id}/restore`

`POST /holdings` 接收 `account_id`、`market`、`symbol`、`quantity`、`average_cost`、選填 `notes`。在同一 transaction 中查找／建立 Asset、建立 Holding及寫入 audit；任一步驟失敗全部 rollback。

還原 Holding 必須由使用者明確確認，可同時提交新的 `quantity` 與 `average_cost`；還原、數值更新與 audit必須在同一 transaction完成。已封存 Account中的 Holding不得還原，必須先還原 Account。

- 有效重複持股：`409 HOLDING_ALREADY_EXISTS`
- 封存重複持股：`409 HOLDING_ARCHIVED`
- 不存在的帳戶：`404`
- 欄位驗證失敗：`422`

Phase 1 不提供獨立 Assets CRUD、Prices API、買入或賣出 API。

### Summary／Status

- `GET /api/v1/dashboard/summary`
- `GET /api/v1/system/status`

Phase 1 不提供 allocation、performance或 snapshot API。

### 錯誤格式

```json
{
  "code": "STABLE_MACHINE_CODE",
  "message": "適合使用者的訊息",
  "details": {},
  "request_id": "..."
}
```

正式回應不得含 stack trace。

## 6. 計算與序列化

- 投入成本＝數量×平均成本
- 目前市值＝數量×Mock Quote
- 未實現損益＝目前市值−投入成本
- 報酬率＝未實現損益÷投入成本×100%
- 投入成本為 0 時，報酬率回 `null`，UI 顯示「—」
- 所有中間計算保留完整 Decimal 精度
- 統一使用 `ROUND_HALF_UP`
- 彙總時先加總未量化數值，最後量化
- TWD API 金額輸出小數 2 位
- 百分比 API 輸出小數 4 位，UI 顯示小數 2 位
- Decimal 在 JSON 中一律使用字串
- 前端只格式化，不重新計算財務結果
- Phase 1 不保存投入成本、市值、損益或報酬率等衍生欄位

## 7. Phase 1 Mock Quote

Phase 1 必須使用固定資料：

- market：`TWSE`
- symbol：`00919`
- name：`群益台灣精選高息`
- currency：`TWD`
- price：`25.00`

全站清楚標示「Mock 測試行情，非真實市場價格」。Mock Quote 不寫入 `market_prices`。

## 8. 登入與 Web 安全

- Owner 密碼至少 12 字元，以互動初始化指令設定，不保存明文
- Argon2id
- Redis server-side session
- 30 天滑動到期
- Cookie：`HttpOnly`、`Secure`、`SameSite=Lax`
- 寫入請求：CSRF Token＋Origin 檢查
- 正式 CORS 只接受自己的 Tailscale HTTPS Origin
- 登入限速：帳號＋IP 15 分鐘最多 5 次，之後短暫鎖定
- 登入錯誤不洩漏帳號是否存在
- Nginx 設定 CSP、`X-Content-Type-Options`、`Referrer-Policy`
- API 例外只在去敏後寫入 Log

Phase 1 不含 OAuth、MFA、密碼重設郵件、角色權限、公開註冊或多使用者。

## 9. Secrets

- `.env` 只放非敏感設定；`.env.example` 只放安全範例
- 正式 secrets 位於專案外：`/opt/ai-pm-os/secrets/personal-asset-os/`
- 以唯讀 secret file 掛載至必要容器
- PostgreSQL 密碼、session 金鑰、備份設定不得共用
- 預設、空白或不安全金鑰必須使啟動失敗
- Agent 不得讀取正式 secrets
- Log、audit、錯誤回應及公開 Git 不得包含 secrets

## 10. Migration

- Backend 啟動時只檢查 revision，不自動執行 Alembic
- revision 不相容時 readiness 回 `503`
- 正式 migration 只能由核准 wrapper在部署前備份成功後執行
- 必須測試全新升級及前一版本升級
- 不要求所有 migration 虛假地支援 downgrade；無法安全 downgrade 時以驗證過的備份還原

## 11. 備份

- Phase 0：手動 `pg_dump` custom format、加密、驗證及隔離還原
- Phase 1：主機 systemd timer 每日 `03:00 Asia/Taipei`
- 使用鎖避免重疊
- 先以 `age` 公開金鑰加密，再透過 Instance Principal 上傳 Private OCI Object Storage
- 主機不長期保存解密私鑰
- 本機保留 7 份、遠端保留 30 份每日與 12 份每月
- 只有 dump、加密、可讀檢查、上傳、大小與 checksum 全部成功才記為 succeeded
- Redis 不備份
- 每月由 Owner提供私鑰，在隔離 PostgreSQL 執行還原演練，完成後移除私鑰
- 目標 RPO：24 小時；RTO：主機恢復後 2 小時

## 12. Log 與磁碟

- 應用以結構化 JSON 輸出 stdout／stderr
- 記錄時間、等級、服務、事件、request ID、HTTP 狀態與耗時
- 不記錄完整財務內容、Cookie、密碼、Token、連線字串或 secrets
- 每個產品容器一般 Log 約 100 MB 上限；四服務約 400 MB
- systemd journal 上限 500 MB
- Audit log 保存於 PostgreSQL，不受 Docker Log 輪替影響
- 磁碟 80% 警告；90% 禁止新 build、Playwright及還原演練
- 不得自動執行廣泛 `docker system prune`

## 13. UI

- 語言：繁體中文
- 市場選單：「上市（TWSE）」「上櫃（TPEx）」
- 新增持股必填：金融帳戶、市場、代號、數量、平均成本
- Asset 名稱、幣別、現價及衍生數值由系統產生
- 獲利／虧損同時顯示正負號與文字，不只依賴顏色
- 表單錯誤顯示於欄位下方
- 空資料提供明確引導
- 桌面優先並支援代表性手機 viewport
- Phase 1 顯示簡單總計，不顯示配置圖、排行、歷史曲線或每日快照

## 14. 可執行驗收

固定輸入：

- 金融帳戶：`測試證券帳戶`
- market：`TWSE`
- symbol：`00919`
- quantity：`40000`
- average cost：`22.50`
- Mock price：`25.00`

固定結果：

- 投入成本：`900000.00`
- 目前市值：`1000000.00`
- 未實現損益：`100000.00`
- API 報酬率：`11.1111`
- UI 報酬率：`+11.11%`

必要驗收：

- 未登入受保護 API 回 `401`
- 登入、登出、session 撤銷、CSRF及限速測試通過
- CRUD、封存／還原、唯一性、transaction rollback及 audit 測試通過
- Compose 重啟後資料仍存在
- PostgreSQL 暫停時 `/health` 為 `200`、`/health/ready` 為 `503`；恢復後 readiness 自動回 `200`
- 備份還原後 Owner、帳戶、Asset、Holding及 audit存在，固定計算結果一致
- OCI ARM64 原生 build、四服務 healthcheck、Chromium E2E及 smoke test通過

Playwright 只存在於獨立 Ubuntu／glibc 測試環境，版本與測試映像完全一致；不得進入正式映像。

## 15. Usable Alpha：其他資產與收入

### 15.1 銀行現金

- 銀行餘額必須由期初現金及已確認現金事件推導，不提供直接覆寫餘額。
- 黃金買賣、保費、保險給付及薪資入帳都建立可追溯現金事件。
- 任何會使銀行現金為負的支出整筆拒絕。
- 資產／收入事件、銀行現金事件、衍生現況及audit必須在同一PostgreSQL transaction完成。

### 15.2 黃金

- 類型：`physical`、`passbook`。
- 輸入單位：`gram`、`mace`（台錢）、`tael`（台兩）；`1台錢=3.75公克`、`1台兩=37.5公克`。
- 正式數量以`NUMERIC(24,8)`公克保存，原始數量與單位另外保存。
- 實體黃金純度為大於0且小於等於1的Decimal；黃金存摺固定為1。
- 期初黃金保存數量及總成本，不建立銀行扣款。
- 買入總成本為成交價款加費用；賣出淨收入為成交價款減費用。
- 買入後以移動平均成本更新每公克成本；賣出按賣出前平均成本轉出成本並計算已實現損益。
- 賣出數量超過持有量或買入付款超過銀行現金時硬性拒絕。
- 預設估值首選臺灣銀行新臺幣黃金存摺本行買進價；若臺銀頁面拒絕或無法解析，改用櫃買中心官方 OpenAPI 的 `AU9901` 臺銀金買進報價，按 `1 台錢 = 3.75 公克` 換算。保存價格、掛牌時間、取得時間及實際來源，不把備援報價標示成黃金存摺牌價。
- 來源失敗時使用最後成功價格並揭露日期；沒有任何價格時估值未知，不得使用0。
- 實體黃金預設市值為公克數×純度×參考價；Owner可保存有日期及原因、已含純度與回收折價的每公克實際回收價覆寫，覆寫時不再重複乘純度。

### 15.3 保單

- 保單保存保險公司、名稱、類型、狀態、累計保費、累計領回金額、目前現金價值及估值日期。
- 期初保單不建立銀行事件。
- 繳費事件從指定銀行扣款並增加累計保費，不直接增加保單現金價值。
- 給付事件增加指定銀行現金及累計領回金額；Owner同時選擇結束保單或保存給付後現金價值。
- 現金價值更新不改變銀行現金；超過365天未更新顯示過期提醒。
- 第一版不計算保單損益、投資報酬率或自動推估現金價值。

### 15.4 薪資

- 薪資範本保存公司、預設發薪日、預設銀行與選填收入／扣除明細。
- 提醒或複製上月只建立草稿，不改變銀行現金。
- 正式薪資紀錄必須包含實領金額、入帳銀行及入帳日；確認後增加銀行現金。
- 本薪、加班費、獎金、津貼、勞健保、所得稅及其他扣除皆為選填明細。
- 扣除明細可納入支出統計，但不得再次建立銀行扣款。

### 15.5 更正、API與UI

- 草稿可修改或刪除；已確認紀錄禁止原地修改或刪除。
- 已確認紀錄只允許建立帶原因及原紀錄關聯的沖銷／更正；原內容永久保留。
- API Decimal一律以字串輸出，前端不得重新計算正式財務結果。
- UI使用單一「其他資產與收入」入口及黃金、保單、薪資三個分頁。
- 首頁顯示銀行現金、黃金估值、保單現金價值、估值過期提醒及待確認薪資提醒。
- 第一版不包含截圖辨識、外部AI、自動網銀操作、Email、LINE或手機推播。

### 15.6 驗收

- 期初黃金及保單不改變銀行現金。
- 黃金買入／賣出、保費／給付及薪資確認的銀行連動可實際操作且具rollback測試。
- 黃金移動平均成本、已實現損益、單位換算及純度估值使用Decimal並有精確測試。
- 金價取得失敗可沿用最後成功值；無歷史值時顯示未知。
- 已確認紀錄不可PATCH或DELETE，沖銷可恢復正確銀行與資產現況。
- 首頁彙總與各分頁明細一致。
- 原生`linux/arm64`四服務Compose及端到端smoke test通過。
