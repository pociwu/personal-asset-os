# Issue tracker: GitHub

本專案的 Issue 與 PRD 使用 GitHub Issues，目標 repository 為公開的 `pociwu/personal-asset-os`。使用 `gh` CLI 操作；repository remote建立後，由工作目錄自動推斷目標。

## Conventions

- 建立：`gh issue create --title "..." --body-file <file> --label "<label>"`
- 讀取：`gh issue view <number> --comments`
- 列表：`gh issue list --state open --json number,title,body,labels,comments`
- 留言：`gh issue comment <number> --body "..."`
- 標籤：`gh issue edit <number> --add-label "..."`／`--remove-label "..."`
- 關閉：`gh issue close <number> --comment "..."`

不得把 secret、真實財務資料、OCI／Tailscale識別資訊或私人部署細節寫入公開 Issue。

## Pull requests as a triage surface

**PRs as a request surface: no.**

外部 PR 不自動視為需求或進入 Issue triage流程；需要需求追蹤時，先建立或連結 Issue。

## Skill conventions

- 「publish to the issue tracker」代表建立 GitHub Issue。
- 「fetch the relevant ticket」代表執行 `gh issue view <number> --comments`。
- `to-spec` 發布完成後套用 `ready-for-agent`。
