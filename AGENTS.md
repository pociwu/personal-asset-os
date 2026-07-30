# Agent Instructions

本專案的產品規格、工作流程與文件權威順序定義於 `docs/governance/`。所有 Agent 都必須遵循 `docs/governance/CODEX_MASTER_PROMPT.md`，並由 AI-PM 派工及驗收。

## Agent skills

### Issue tracker

Issues 與 PRD 使用 GitHub Issues，透過 `gh` CLI 操作。詳見 `docs/agents/issue-tracker.md`。

### Triage labels

使用預設標籤：`needs-triage`、`needs-info`、`ready-for-agent`、`ready-for-human`、`wontfix`。詳見 `docs/agents/triage-labels.md`。

### Domain docs

本專案採單一領域結構；開始工作前讀取根目錄 `CONTEXT.md` 及相關 `docs/adr/`。詳見 `docs/agents/domain.md`。
