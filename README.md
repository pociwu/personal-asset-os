# Personal Asset OS

Personal Asset OS 是部署於 OCI ARM64、供單一 Owner 私人使用的資產管理系統。專案採公開原始碼與 MIT License；正式財務資料、secrets、備份、Log及部署識別資訊永不進入 Git。

## 目前狀態

目前處於 **Phase 0 基礎建設候選實作階段**。Backend、PostgreSQL、Redis、React／Nginx Web、Compose及健康檢查已有候選；正式 secrets、備份與 OCI ARM64 Phase Gate仍未完成。

當前工作狀態見 [TASKS.md](TASKS.md)，系統契約見 [SYSTEM_SPEC.md](docs/governance/SYSTEM_SPEC.md)。

## 文件

- [計畫報告](docs/governance/PLAN_REPORT.md)
- [系統規格](docs/governance/SYSTEM_SPEC.md)
- [執行計畫](docs/governance/EXECUTION_PLAN.md)
- [任務狀態](TASKS.md)
- [正式領域術語](CONTEXT.md)
- [Codex 工作規則](docs/governance/CODEX_MASTER_PROMPT.md)
- [安全政策](SECURITY.md)
- [決策紀錄](docs/governance/DECISIONS.md)
- [架構決策](docs/adr/)

## 預定部署基線

- OCI Ampere A1 ARM64
- Ubuntu 24.04 LTS
- 2 OCPU、12 GB RAM
- 至少 100 GB 系統碟
- Docker Engine＋Docker Compose v2
- Tailscale Serve 私人存取
- 正式路徑：`/opt/ai-pm-os/projects/personal-asset-os`

產品 Compose 預定只執行 `web`、`backend`、`postgres`、`redis`。AI-PM、Tailscale、備份排程與部署 wrapper 不在產品 Compose 內。

## 開發原則

- AI-PM 是唯一派工與驗收入口。
- 一個任務、一個分支、一個語意單一的 commit。
- Phase 0／1 開發只使用合成資料。
- Phase 1 使用固定 Mock 行情，不可用於真實財務判斷。
- 不提供自動下單、轉帳或券商密碼保存。
- 正式部署必須經 Owner 批准並追溯至已驗收 commit SHA。

## Backend 與 Compose 開發候選

安裝 `uv` 後可執行 Backend測試：

```bash
cd backend
uv sync --locked
uv run --locked pytest
uv run --locked uvicorn app.main:app --host 127.0.0.1 --port 8000
```

Liveness：

```text
GET http://127.0.0.1:8000/api/v1/health
```

Compose候選位於`deploy/compose.yaml`。在未追蹤的`.env`中填入開發用的`POSTGRES_PASSWORD`與`REDIS_PASSWORD`後，可於已安裝 Docker Compose v2的環境執行：

```bash
docker compose --env-file .env -f deploy/compose.yaml config
docker compose --env-file .env -f deploy/compose.yaml up -d --build
docker compose --env-file .env -f deploy/compose.yaml ps
```

Readiness：

```text
GET /api/v1/health/ready
200: PostgreSQL與Redis均可用
503: 任一依賴不可用
```

P0-004加入唯一 Web入口`http://127.0.0.1:8080`，並由 Nginx代理`/api`；Backend、PostgreSQL及Redis仍不發布主機 Port。P0-005會把開發用`.env`密碼輸入替換為唯讀 secret files。不得把目前候選描述為 Phase 0完成。

前端可獨立驗證：

```bash
cd frontend
npm ci
npm test
npm run build
```

## 公開 Repository 安全

禁止提交 `.env`、secret file、資料庫 dump、真實帳戶／持股、OCI OCID、Tailscale 識別資訊、正式 Log、audit log、Playwright trace或含真實資料的截圖。安全問題請依 [SECURITY.md](SECURITY.md) 私下通報。

## License

[MIT](LICENSE)
