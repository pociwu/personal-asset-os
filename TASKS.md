# TASKS

本檔由 AI-PM 管理正式狀態。開發型 Agent只能提交候選結果與證據，不得自行修改為 `VERIFIED`／`DONE`。

## 狀態

`BACKLOG → READY → IN_PROGRESS → IN_REVIEW → VERIFIED → DONE`  
例外：`BLOCKED`、`CANCELLED`

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
| P0-002 | IN_REVIEW | Backend 最小骨架與 liveness | P0-001 |
| P0-003 | BACKLOG | PostgreSQL、Redis、Compose及 readiness | P0-002 |
| P0-004 | BACKLOG | React build stage與單一 Nginx Web 映像 | P0-003 |
| P0-005 | BACKLOG | Secrets與正式設定邊界 | P0-003 |
| P0-006 | BACKLOG | 品質與測試指令 | P0-002、P0-004 |
| P0-007 | BACKLOG | 手動備份、加密、驗證與隔離還原 | P0-003、P0-005 |
| P0-008 | BACKLOG | GitHub CI與安全掃描 | P0-006 |
| P0-009 | BACKLOG | OCI帳號、Tailscale與受限 wrapper | P0-005、P0-007、P0-008 |
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
