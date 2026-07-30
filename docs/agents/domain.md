# Domain Docs

本專案採單一領域文件結構。

## Before exploring

- 讀取根目錄 `CONTEXT.md`。
- 讀取與工作範圍相關的 `docs/adr/`。
- 讀取 `docs/governance/DECISIONS.md` 及適用的系統規格。

文件不存在時可繼續，不得自行創造互相衝突的替代術語。

## Vocabulary

Issue標題、PRD、測試名稱、API討論及實作說明都必須使用 `CONTEXT.md` 的正式詞彙。避免使用 glossary列出的替代詞。

若需要的概念尚未定義，應回報 AI-PM並透過 domain-modeling流程補充，不得在任務中悄悄發明新語意。

## ADR conflicts

若提案與既有 ADR衝突，必須明確指出 ADR編號、衝突內容與重新開啟決策的理由；不得靜默覆蓋。
