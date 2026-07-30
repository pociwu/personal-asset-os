# Personal Asset OS 執行計畫

版本：2.0（規格凍結候選）

## 1. 執行原則

- AI-PM 是唯一派工與驗收入口。
- 一次只執行一個 `READY` 任務包。
- 一個任務使用一個 `codex/<task-name>` 分支及一個語意單一的 commit。
- 開發型 Agent只回報候選完成與證據；AI-PM 才能將任務轉為 `VERIFIED`／`DONE`。
- Phase 的所有必要任務皆為 `DONE` 且 Phase Gate 通過後，才能完成該 Phase。
- 正式部署、migration及還原需 Owner 批准。
- 發現文件衝突時依 `docs/governance/CODEX_MASTER_PROMPT.md` 的權威順序處理；不得自行增加範圍。

## 2. 任務狀態

```text
BACKLOG → READY → IN_PROGRESS → IN_REVIEW → VERIFIED → DONE
```

例外狀態：

- `BLOCKED`：必須記錄阻礙與解除條件
- `CANCELLED`：由 Owner 或 AI-PM 決定不再執行

每個任務記錄 Task ID、Phase、目的、明確不做事項、依賴、Agent、分支、修改範圍、驗收方式、commit SHA、證據、限制及更新時間。

## 3. Phase 0 任務

1. `P0-001`：治理文件與公開 Repository 基線
2. `P0-002`：Backend 最小骨架與 liveness
3. `P0-003`：PostgreSQL、Redis、Compose及 readiness
4. `P0-004`：React build stage與單一 Nginx Web 映像
5. `P0-005`：secrets與正式設定邊界
6. `P0-006`：lint、type check、unit test及一致驗收入口
7. `P0-007`：手動備份、加密、驗證與隔離還原底座
8. `P0-008`：GitHub CI、secrets scan、依賴及映像掃描
9. `P0-009`：OCI 帳號、Tailscale與受限 wrapper
10. `P0-010`：實際 OCI ARM64 Phase Gate

### Phase 0 Gate

- Ubuntu 24.04 ARM64、2 OCPU、12 GB、至少 100 GB
- `compose config` 成功
- 原生 ARM64 build成功
- `web`、`backend`、`postgres`、`redis` healthy
- 首頁、`/health`、`/health/ready` 符合規格
- PostgreSQL 故障及恢復時 readiness 正確切換
- Compose restart 後服務恢復且 volume 資料存在
- 手動備份、加密、checksum及隔離還原成功
- Tailscale Serve可用且公網 Port未開放
- 候選 wrapper不能讀取正式 secrets或正式 volume

## 4. Phase 1 任務

1. `P1-001`：Owner、Account、Asset、Holding、Audit、Backup Run模型與 migration
2. `P1-002`：Owner 初始化、登入、登出與可撤銷 session
3. `P1-003`：CSRF、Origin、限速、Cookie、CORS及安全標頭
4. `P1-004`：金融帳戶 API、封存與還原
5. `P1-005`：Holding、Asset辨識、Mock Provider、transaction及 audit
6. `P1-006`：Decimal 計算與 Summary API
7. `P1-007`：登入與金融帳戶 UI
8. `P1-008`：持股、簡單 Summary、Mock警示及系統狀態 UI
9. `P1-009`：每日 systemd 備份、Instance Principal、Object Storage及 backup status
10. `P1-010`：整合、安全及 Chromium E2E
11. `P1-011`：OCI ARM64 Phase Gate

### Phase 1 Gate

- 固定 `00919` Mock 案例產生規格中的精確結果
- 所有認證、安全、API、Decimal、封存／還原、rollback及 audit測試通過
- 全站清楚顯示 Mock警示
- Compose重啟後資料存在
- 每日備份流程成功；隔離還原後資料與計算一致
- ARM64 Chromium E2E通過
- 不存在 Prices API、真實行情、交易、配置、歷史或 AI 功能

Phase 1 是功能驗證版；不得標示為真實行情日常可用。

## 5. 後續 Phase 邊界

- Phase 2：真實台股行情、保存、快取、重試、限流、過期與失敗降級
- Phase 3：配置、排行、歷史與 snapshot
- Phase 4：買入、賣出、股息、費用、稅額、平均成本重算與已實現損益
- Phase 5：現金流、負債與目標
- Phase 6：風險與再平衡
- Phase 7：Telegram及報告
- Phase 8：受控唯讀 AI 資產助理

不得要求每個 Phase 機械式新增 ADR；只有符合 ADR 三項條件的決策才建立。

## 6. 每個任務工作循環

1. AI-PM 確認任務為 `READY`、依賴完成且只有一個負責 Agent。
2. Agent讀取權威文件並檢查 Git／現有程式。
3. Agent回報目的、明確不做事項、修改檔案及驗收指令。
4. AI-PM 將任務轉為 `IN_PROGRESS`。
5. Agent實作最小變更並執行適用測試。
6. Agent建立單一 commit，回報 SHA與完整證據。
7. AI-PM 轉為 `IN_REVIEW`，檢查規格、範圍及證據。
8. 通過後為 `VERIFIED`；整合至受保護 `main` 且未破壞 Phase後為 `DONE`。
9. 失敗時退回 `IN_PROGRESS` 或標為 `BLOCKED`，不得宣稱完成。

## 7. Docker 驗證與部署

### 一般開發

- Agent可執行語言層 lint、type check及測試
- GitHub Actions執行 AMD64 build、integration及安全掃描
- Agent不接觸 OCI 正式 Docker

### ARM64 候選驗收

`verify-candidate` 只接受已提交 commit SHA，以獨立 Compose project、測試 secrets、測試 volume及本機測試 Port執行。不得接受任意命令、Compose路徑、volume或secret參數。

### 正式部署

`deploy-approved-release` 只接受 Owner核准 SHA，依序：

1. 檢查版本與 secrets
2. 建立並驗證部署前備份
3. 執行一次性 Alembic migration
4. 更新服務
5. 執行 readiness與 smoke test
6. 記錄 SHA、migration、映像 digest及結果

Backend不得在啟動時自動 migration。

## 8. Definition of Done

- 功能及明確不做事項符合權威規格
- 適用測試全部通過
- Lock file同步且無未授權依賴
- 無 secrets、真實財務資料或部署識別資訊進入 Git
- ARM64要求有實機證據
- migration、Log、錯誤處理及文件與任務風險相稱
- commit可單獨理解及回滾
- AI-PM已驗收，且 `main` 整合未破壞 Phase Gate

## 9. 禁止事項

- 自行擴充 Phase或把未來功能提前實作
- 自動下單、轉帳或保存券商密碼
- 使用 float計算金額
- 使用 `latest`
- 直接暴露 Web、PostgreSQL或Redis至公網
- Agent讀取正式 secrets、資料庫或備份私鑰
- 自動刪除正式 volume、未驗證備份或執行廣泛 prune
- 測試失敗時宣稱完成
- 未備份及未批准即執行正式 migration
