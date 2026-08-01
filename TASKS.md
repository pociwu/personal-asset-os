# TASKS

本檔由 AI-PM 管理正式狀態。開發型 Agent只能提交候選結果與證據，不得自行修改為 `VERIFIED`／`DONE`。

## 狀態

`BACKLOG → READY → IN_PROGRESS → IN_REVIEW → VERIFIED → DONE`  
例外：`BLOCKED`、`CANCELLED`

## CURRENT：Usable Alpha其他資產與收入

### A-002 黃金、保單、薪資端到端切片

- Status：`IN_REVIEW`
- Branch：`codex/alpha-other-assets-income`
- Purpose：以單一「其他資產與收入」入口完成手動黃金、保單及薪資記錄，並原子連動銀行現金。
- Includes：規格與領域語言、migration、Backend API與領域計算、臺銀／櫃買中心金價降級、三分頁UI、單元及契約測試。
- Excludes：截圖辨識、外部AI、Email、LINE、手機推播、自動網銀操作、保單損益。
- Acceptance：依`docs/governance/SYSTEM_SPEC.md`第15.6節。
- Dependency：Alpha股票與現金規則決策`c7b9723`。
- Candidate verification：Backend Ruff、format、mypy通過，45 tests passed；Frontend ESLint、Prettier、TypeScript、2 tests及production build通過；Alembic離線upgrade SQL成功；程式實際取得櫃買中心`AU9901`報價並換算每公克。
- Pending evidence：本機無Docker，PostgreSQL migration實跑、Compose整合、原生OCI ARM64及Owner登入安全驗收仍待Ubuntu／OCI環境執行；未完成前不得標示`VERIFIED`或部署正式資料。

## CURRENT：Phase 0 專案骨架與部署底座

### P0-001 治理文件與公開 Repository 基線

- Status：`DONE`
- Owner：AI-PM
- Purpose：將已確認決策寫入權威文件，建立公開專案安全與授權基線。
- Includes：六份治理文件、`CONTEXT.md`、`DECISIONS.md`、五份 ADR、`SECURITY.md`、MIT License。
- Excludes：產品程式碼、Compose、CI、部署腳本。
- Acceptance：
  - [x] 文件權威順序一致
  - [x] Phase 0／1 邊界一致
  - [x] Login、backup、ARM64、Agent權限及驗收可執行
  - [x] 無 secrets或真實財務資料
  - [x] Owner審閱並批准規格凍結
- Commit SHA：初始治理 baseline；以本任務的 Git commit metadata為準
- Evidence：Markdown結構與連結檢查通過；21個任務定義唯一；5份 ADR存在；基本 secret-pattern scan無結果；Owner已確認規格、Issue Tracker、labels與測試接縫。

### Phase 0 待派工

| Task ID | 狀態 | 任務 | 依賴 |
|---|---|---|---|
| P0-002 | DONE | Backend 最小骨架與 liveness | P0-001 |
| P0-003 | IN_REVIEW | PostgreSQL、Redis、Compose及 readiness | P0-002 |
| P0-004 | IN_REVIEW | React build stage與單一 Nginx Web 映像 | P0-003 |
| P0-005 | IN_REVIEW | Secrets與正式設定邊界 | P0-003 |
| P0-006 | IN_REVIEW | 品質與測試指令 | P0-002、P0-004 |
| P0-007 | IN_REVIEW | 手動備份、加密、驗證與隔離還原 | P0-003、P0-005 |
| P0-008 | IN_REVIEW | GitHub CI與安全掃描 | P0-006 |
| P0-009 | IN_REVIEW | OCI帳號、Tailscale與受限 wrapper | P0-005、P0-007、P0-008 |
| P0-010 | BACKLOG | OCI ARM64 Phase Gate | P0-002～P0-009 |

### P0-002 候選證據

- Branch：`codex/p0-002-backend-skeleton`
- Includes：FastAPI application、非敏感設定、request ID、結構化 JSON request Log、`GET /api/v1/health`、鎖檔與外部行為測試。
- Excludes：Compose、PostgreSQL、Redis、readiness、正式 secrets、登入及任何財務領域功能。
- Verification：
  - `uv sync --locked`：成功
  - `uv run --locked pytest`：候選提交前重新執行
  - Uvicorn HTTP smoke：`200`、`{"status":"ok","service":"backend"}`、有效 `X-Request-ID`、`Cache-Control: no-store`
- Commit SHA：候選 commit建立後以 Git metadata及 Issue留言為準

### P0-003 候選證據

- Branch：`codex/p0-003-compose-readiness`
- Includes：Backend容器映像、PostgreSQL 16、Redis 7、內部 Compose network、PostgreSQL named volume、依賴健康檢查及`GET /api/v1/health/ready`。
- Excludes：Web/Nginx、正式 secret files、migration revision、備份、OCI ARM64實機驗收及財務領域功能。
- Verification：
  - `uv lock`與`uv sync --locked`：成功
  - `uv run --locked pytest`：9 passed
  - Python compile與 Compose靜態斷言：成功
  - Docker Compose啟動與故障恢復：本機未安裝 Docker，待具備 Docker的驗收環境執行
- Commit SHA：候選 commit建立後以 Git metadata及 Issue留言為準

### P0-004 候選證據

- Branch：`codex/p0-004-web-image`
- Base：P0-003候選分支；P0-003通過驗收前不得獨立合併至`main`。
- Includes：React／TypeScript／Vite首頁、服務狀態顯示、npm鎖檔、Node build stage、單一 Nginx runtime、SPA fallback、`/api`代理、安全標頭、Web healthcheck及唯一 loopback Port。
- Excludes：登入、財務功能、Tailscale主機設定、正式 secret files、CI及 OCI ARM64實機驗收。
- Verification：
  - `npm install`：0 vulnerabilities
  - `npm test`：2 passed
  - `npm run build`：成功
  - 桌面及390px手機瀏覽器渲染：成功，無水平溢位
  - Compose與Nginx靜態斷言：候選提交前重新執行
  - Docker映像 build與四服務啟動：本機未安裝 Docker，待具備 Docker的驗收環境執行
- Commit SHA：候選 commit建立後以 Git metadata及 Issue留言為準

### P0-005 候選證據

- Branch：`codex/p0-005-secret-files`
- Base：P0-004堆疊候選；上游通過驗收前不得獨立合併至`main`。
- Includes：Repository外secret根目錄、Compose file-backed secrets、per-service授權、Backend production啟動驗證、Redis暫存ACL、非敏感`.env.example`、metadata-only preflight及Owner操作文件。
- Excludes：真實secret值、自動密碼輪替、session secret消費者、備份加密設定、部署wrapper及正式部署。
- Verification：
  - Backend tests：20 passed
  - Frontend tests：2 passed；production build成功
  - Compose secret授權與無敏感environment靜態斷言：成功
  - Secret preflight Shell語法檢查：成功
  - 直接密碼environment掃描：無結果
  - Docker secrets實際掛載：本機未安裝 Docker，待具備 Docker的驗收環境執行
- Commit SHA：候選 commit建立後以 Git metadata及 Issue留言為準

### P0-006 候選證據

- Branch：`codex/p0-006-quality-gate`
- Base：P0-005堆疊候選；上游通過驗收前不得獨立合併至`main`。
- Includes：Backend Ruff／format／mypy strict／pytest、Frontend ESLint／Prettier／TypeScript／Vitest／build，以及跨Windows／Ubuntu的單一`quality.py`驗收入口。
- Excludes：Git hook、GitHub Actions、Docker integration、Playwright E2E、安全掃描及OCI ARM64驗收。
- Verification：
  - `python scripts/verify/quality.py`：11/11 checks passed
  - Backend：Ruff通過、17 files格式通過、mypy 17 files無錯誤、20 tests passed
  - Frontend：ESLint、Prettier、TypeScript通過、2 tests passed、production build成功
  - `uv.lock`與`package-lock.json`：同步成功
  - npm audit：0 vulnerabilities
- Commit SHA：候選 commit建立後以 Git metadata及 Issue留言為準

### P0-007 候選證據

- Branch：`codex/p0-007-backup-restore`
- Base：P0-006堆疊候選；上游通過驗收前不得獨立合併至`main`。
- Includes：PostgreSQL custom-format dump直接串流至`age`、SHA-256驗證、嚴格artifact命名、操作鎖、磁碟容量防護、離線archive驗證及無網路／tmpfs的一次性PostgreSQL隔離還原。
- Excludes：Redis備份、排程、OCI Object Storage上傳、保留政策自動化、正式資料及長期存放解密私鑰。
- Verification：
  - `python scripts/verify/quality.py`：11/11 checks passed；Backend 24 tests及Frontend 2 tests通過
  - Backup腳本Bash語法檢查：4個檔案通過
  - 明文dump、Redis、`latest`及正式volume靜態防護測試：4項
  - 實際加密備份及隔離還原：本機未安裝Docker及`age`，納入P0-008 Ubuntu整合驗收
- Commit SHA：候選 commit建立後以 Git metadata及 Issue留言為準

### P0-008 候選證據

- Branch：`codex/p0-008-ci-security`
- Base：P0-007堆疊候選；上游通過驗收前不得獨立合併至`main`。
- Includes：Ubuntu 24.04 GitHub Actions、統一品質閘門、Python／npm依賴稽核、Git history secret scan、Trivy filesystem／映像掃描、四服務Compose整合、依賴故障恢復，以及實際`age`備份／驗證／隔離還原。
- Excludes：OCI ARM64原生驗收、Chromium E2E、正式secrets、正式volume、正式部署及自動合併。
- Verification：
  - 所有Action固定完整40字元commit SHA
  - 整合測試使用合成secret、獨立Compose project、測試volume及loopback測試Port
  - `python scripts/verify/quality.py`：Ubuntu CI 11/11 checks passed；Backend 30 tests及Frontend 2 tests通過
  - Workflow／Dependabot YAML解析及5個Bash檔案語法檢查：通過
  - `pip-audit`與`npm audit`：0 known vulnerabilities
  - GitHub Actions：push／PR兩組共8個jobs全部通過；Compose故障恢復、`age`加密備份、archive驗證、tmpfs隔離還原及三類Trivy掃描均成功
- Commit SHA：候選 commit建立後以 Git metadata及 Issue留言為準

### P0-009 候選證據

- Branch：`codex/p0-009-ubuntu-guardrails`
- Base：P0-008堆疊候選；上游通過驗收前不得獨立合併至`main`。
- Includes：Ubuntu 24.04 ARM64資源／帳號preflight、Owner操作指南、Tailscale Serve私人入口、AI-PM單一sudo命令、只接受完整SHA的root-owned驗證wrapper、Compose隔離policy及原生ARM64映像證據。
- Excludes：建立OCI資源、寫入真實OCID／IP／tailnet資料、正式部署、自動migration、Agent Docker權限及P0-010實機Phase Gate。
- Verification：
  - Compose policy接受固定四服務隔離形狀，拒絕host mount與公網Port
  - Wrapper不執行候選Shell、不接受任意路徑／Port／volume／secret參數
  - Tailscale設定先關閉Funnel，只轉送loopback Web
  - `python scripts/verify/quality.py`：11/11 checks passed；Backend 34 tests及Frontend 2 tests通過
  - 3個部署Bash腳本、Compose policy Python語法及Ruff：通過
  - GitHub Ubuntu CI及實際ARM64 wrapper：推送候選及P0-010主機驗收時執行
- Commit SHA：候選commit建立後以Git metadata及Issue留言為準

## NEXT：Phase 1 Mock 持股 MVP

| Task ID | 狀態 | 任務 | 依賴 |
|---|---|---|---|
| P1-001 | BACKLOG | Owner、Account、Asset、Holding、Audit、Backup Run模型與 migration | Phase 0 DONE |
| P1-002 | BACKLOG | Owner初始化、登入及 session | P1-001 |
| P1-003 | BACKLOG | Web安全防護 | P1-002 |
| P1-004 | BACKLOG | 金融帳戶 API | P1-001、P1-003 |
| P1-005 | BACKLOG | Holding、Asset辨識與 Mock Provider | P1-004 |
| P1-006 | BACKLOG | Decimal計算與 Summary API | P1-005 |
| P1-007 | BACKLOG | 登入與金融帳戶 UI | P1-003、P1-004 |
| P1-008 | BACKLOG | 持股、Summary、Mock警示及狀態 UI | P1-006、P1-007 |
| P1-009 | BACKLOG | 每日加密異地備份 | P1-001、Phase 0備份底座 |
| P1-010 | BACKLOG | 整合、安全及 Chromium E2E | P1-002～P1-009 |
| P1-011 | BACKLOG | OCI ARM64 Phase Gate | P1-010 |

## Phase 1 明確不做

- 真實行情、Prices API、`market_prices`
- 買入、賣出、股息、費用、稅額及已實現損益
- 美股、外幣、匯率、現金與負債
- 配置圖、排行、歷史曲線及 snapshot
- Telegram、風險、再平衡及 AI 資產助理
- OAuth、MFA、多使用者、角色及公開註冊

## 後續

- Phase 2：真實台股行情
- Phase 3：儀表板與快照
- Phase 4：交易與股息
- Phase 5：現金流與財務目標
- Phase 6：風險與再平衡
- Phase 7：Telegram與報告
- Phase 8：唯讀 AI 資產助理
