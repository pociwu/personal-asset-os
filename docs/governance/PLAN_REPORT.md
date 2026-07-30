# Personal Asset OS 計畫報告

版本：2.0（規格凍結候選）  
狀態：Owner 已確認，Phase 0 可開始  
部署環境：OCI Ampere A1，Ubuntu 24.04 LTS ARM64  
資源基線：2 OCPU、12 GB RAM、至少 100 GB 系統碟  
正式路徑：`/opt/ai-pm-os/projects/personal-asset-os`

## 1. 願景

Personal Asset OS 是單一 Owner 私人使用的資產管理系統。它逐步整合台股、其他資產、交易、股息、現金流、財務目標、風險分析、通知與唯讀 AI 資產助理。系統只提供記錄、查詢、計算與決策輔助，不執行下單、轉帳或未經確認的自動交易。

## 2. 治理與責任

- **系統擁有者**：決定產品範圍與高風險操作，批准正式部署、migration、還原及網路暴露。
- **AI-PM**：唯一派工與驗收入口，管理任務狀態、證據與 Phase Gate；不直接修改產品程式碼。
- **開發型 Agent**：只執行已指派任務，使用合成資料，不得自行部署或推進 Phase。
- **業務型 Agent**：Phase 0／1 不接觸正式財務資料。Phase 8 才能透過受控唯讀查詢服務運作。

AI-PM／Codex 與產品同機但分離部署、分離權限及分離生命週期。

## 3. 核心目標

1. 建立單 Owner、安全、可驗證備份的財務資料庫。
2. 以最少輸入維護金融帳戶及目前持股。
3. 使用 Decimal 正確計算投入成本、市值、未實現損益與報酬率。
4. 在 Phase 2 後提供可追溯、可降級的真實台股行情。
5. 建立資產配置、歷史趨勢、交易、現金流、目標與風險能力。
6. 最終提供有資料時間與來源依據的唯讀 AI 問答。

## 4. 永久非目標

- 券商自動下單或自動交易。
- 網銀轉帳。
- 保存券商或網銀密碼。
- 公開 SaaS 或多租戶。
- 法定報稅申報。
- Agent 直接連接正式資料庫或取得正式 secrets。

## 5. 部署邊界

產品 Compose 只有：

- `web`：Nginx 提供 React 靜態檔並代理 `/api`
- `backend`：FastAPI
- `postgres`：PostgreSQL 16
- `redis`：Redis 7

Tailscale、AI-PM、候選驗收 wrapper、正式部署 wrapper及備份 systemd timer 均位於產品 Compose 外。Web 僅透過 Tailscale Serve 存取；不得開放公網 80、443、5432 或 6379。

## 6. Phase

### Phase 0：部署底座

完成治理文件、專案骨架、四服務 Compose、健康檢查、secrets 邊界、品質指令、手動備份／還原、GitHub CI、OCI 權限 wrapper及 ARM64 Phase Gate。

### Phase 1：Mock 持股 MVP

完成 Owner 登入、金融帳戶、台股 Asset、彙總 Holding、封存／還原、audit、Decimal 計算、簡單 Summary、每日加密異地備份與 E2E。全站必須標示「Mock 測試行情，非真實市場價格」。

Phase 1 不含買入／賣出交易。修改數量只代表修正目前現況；交易帳本留到 Phase 4。

### Phase 2：真實台股行情

完成可替換 Provider、行情保存、Redis 快取、timeout、重試、限流防護、最後成功時間、過期標示與失敗降級。通過抽樣比對後才可標記為日常可用。

### Phase 3：儀表板與快照

完成配置、排行、歷史曲線與每日快照。

### Phase 4：交易與股息

完成買入、賣出、費用、稅額、股息、平均成本重算與已實現損益。

### Phase 5–8

- Phase 5：現金流、負債與財務目標
- Phase 6：風險與再平衡
- Phase 7：Telegram 通知與報告
- Phase 8：受控唯讀 AI 資產助理

## 7. 成功標準

- 每個 Phase 由小型任務 commit 組成，全部 `DONE` 後通過整體 Phase Gate。
- Phase 0 可在實際 OCI ARM64 原生建置、啟動、故障恢復及保存資料。
- Phase 1 固定 Mock 驗收數值可重現，認證、安全、封存、audit及備份還原測試通過。
- Phase 2 前不得把 Mock 結果描述為真實資產估值。
- 每日備份加密後異地保存，並可在隔離資料庫還原。
- 正式部署可追溯至 commit SHA、migration revision、映像 digest及驗收證據。

## 8. 主要風險與對策

- **ARM64 相容性**：只採用原生 `linux/arm64` 映像／套件，實機驗收。
- **行情失效**：Provider 介面、快取、重試、過期標示及最後成功價格。
- **財務誤差**：Decimal／NUMERIC、固定捨入規則、資料庫 constraints。
- **未授權存取**：Tailscale 私網、應用登入、CSRF、限速與 secrets 分離。
- **資料遺失**：持久化 volume、每日加密異地備份、checksum及每月還原演練。
- **Agent 權限擴張**：主機帳號分離、受限 wrapper、合成資料及 Owner 批准閘門。
- **磁碟耗盡**：Log 輪替、80% 警告、90% 停止非必要寫入。
