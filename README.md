# Personal Asset OS

Personal Asset OS 是部署於 OCI ARM64、供單一 Owner 私人使用的資產管理系統。專案採公開原始碼與 MIT License；正式財務資料、secrets、備份、Log及部署識別資訊永不進入 Git。

## 目前狀態

目前處於 **Usable Alpha候選實作階段**。Phase 0基礎設施之上已加入銀行現金、黃金、保單與薪資的手動輸入切片；Ubuntu PostgreSQL整合、Owner登入與 OCI ARM64 Alpha Gate仍未完成，因此尚不可視為正式可用版本。

當前工作狀態見 [TASKS.md](TASKS.md)，系統契約見 [SYSTEM_SPEC.md](docs/governance/SYSTEM_SPEC.md)。

## 文件

- [計畫報告](docs/governance/PLAN_REPORT.md)
- [系統規格](docs/governance/SYSTEM_SPEC.md)
- [執行計畫](docs/governance/EXECUTION_PLAN.md)
- [任務狀態](TASKS.md)
- [正式領域術語](CONTEXT.md)
- [Codex 工作規則](docs/governance/CODEX_MASTER_PROMPT.md)
- [安全政策](SECURITY.md)
- [Secret files操作指南](docs/deployment/SECRETS.md)
- [備份與隔離還原指南](docs/deployment/BACKUP_RESTORE.md)
- [GitHub CI](.github/workflows/ci.yml)
- [Ubuntu ARM64測試主機指南](docs/deployment/UBUNTU_ARM64_TEST.md)
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
- 開發與驗收只使用合成資料；正式資料不得進入Git、Log或測試產物。
- Usable Alpha黃金估值首選臺灣銀行公開本行買進價，受阻時改用櫃買中心官方 `AU9901` 臺銀金買進報價並揭露來源；台股正式行情仍須依Alpha股票規格完成驗收。
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

首次啟動或升級前必須由核准部署流程顯式執行migration；Backend不會在啟動時自動建表：

```bash
cd backend
uv run --locked alembic upgrade head
```

Compose候選可在PostgreSQL healthy且部署前備份完成後，以相同Backend映像執行一次性migration：

```bash
docker compose --env-file .env -f deploy/compose.yaml run --rm backend \
  alembic -c alembic.ini upgrade head
```

Liveness：

```text
GET http://127.0.0.1:8000/api/v1/health
```

Compose候選位於`deploy/compose.yaml`。`.env`只允許保存`.env.example`列出的非敏感設定；PostgreSQL與Redis密碼必須依[Secret files操作指南](docs/deployment/SECRETS.md)建立於Repository外。Owner完成不讀取內容的preflight後，才可於已安裝 Docker Compose v2的環境執行：

```bash
cp .env.example .env
sudo scripts/verify/secrets-preflight.sh
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

唯一 Web入口為`http://127.0.0.1:8080`，並由 Nginx代理`/api`；Backend、PostgreSQL及Redis仍不發布主機 Port。Secret只以唯讀檔案授權給必要容器，不會進入`.env`或Compose environment。不得把目前候選描述為 Phase 0完成。

前端可獨立驗證：

```bash
cd frontend
npm ci
npm test
npm run build
```

## 統一品質閘門

安裝 Python 3.12、`uv`、Node.js 24及npm後，從Repository根目錄執行：

```bash
python scripts/verify/quality.py
```

此唯一入口會以鎖檔同步Backend與Frontend依賴，依序執行Ruff lint／format、mypy strict、pytest、ESLint、Prettier、TypeScript、Vitest及production build。任一步驟失敗即以非零狀態停止；GitHub Actions會呼叫同一入口。

GitHub CI候選另在Ubuntu 24.04執行依賴稽核、Git history secret scan、filesystem／映像掃描，以及使用合成secret與獨立volume的Compose故障恢復、加密備份及隔離還原。CI測試清理volume只限一次性Compose project，絕不指向正式project。

## 加密備份候選

Phase 0備份底座只處理PostgreSQL；Redis是可重建的session／cache。建立備份時，custom-format dump直接串流至`age`，不在主機寫入明文dump。解密私鑰由Owner於驗證或隔離還原演練時暫時提供，詳細前置條件與指令見[備份與隔離還原指南](docs/deployment/BACKUP_RESTORE.md)。

## 公開 Repository 安全

禁止提交 `.env`、secret file、資料庫 dump、真實帳戶／持股、OCI OCID、Tailscale 識別資訊、正式 Log、audit log、Playwright trace或含真實資料的截圖。安全問題請依 [SECURITY.md](SECURITY.md) 私下通報。

## License

[MIT](LICENSE)
