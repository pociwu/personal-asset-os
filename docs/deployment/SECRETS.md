# Secret files

Personal Asset OS不透過`.env`、Compose environment或Git傳遞密碼。正式secret根目錄固定為：

```text
/opt/ai-pm-os/secrets/personal-asset-os/
```

P0-005目前需要兩個彼此獨立的檔案：

```text
postgres_password
redis_password
```

Phase 1的`session_secret`與備份加密設定必須另建檔案，不得重用上述密碼。尚未有消費者前，不提前掛載至任何容器。

## Owner建立程序

下列命令只能由Owner或之後核准的部署wrapper執行。不要把輸出顯示於終端、聊天、Issue或Log。

```bash
sudo install -d -m 0700 -o root -g root /opt/ai-pm-os/secrets/personal-asset-os
sudo sh -c 'umask 077; openssl rand -hex 32 > /opt/ai-pm-os/secrets/personal-asset-os/postgres_password'
sudo sh -c 'umask 077; openssl rand -hex 32 > /opt/ai-pm-os/secrets/personal-asset-os/redis_password'
sudo chmod 0444 /opt/ai-pm-os/secrets/personal-asset-os/postgres_password
sudo chmod 0444 /opt/ai-pm-os/secrets/personal-asset-os/redis_password
```

檔案使用`0444`是為了讓Compose的非root Backend可讀取file-backed secret；主機上層目錄的`0700 root:root`阻止其他使用者列舉或穿越。Compose只把每個secret唯讀掛載給明確列出的必要服務。

## 不讀取內容的前置檢查

檢查只讀取檔案metadata，不輸出secret內容：

```bash
sudo scripts/verify/secrets-preflight.sh
```

檢查通過後才可執行`docker compose config`或啟動服務。Backend在production模式還會拒絕缺檔、空白、多行、少於32字元、超過512字元及常見預設值；錯誤訊息不得包含secret內容或主機路徑。

## 輪替

PostgreSQL及Redis密碼輪替必須是獨立、Owner核准的操作，並同時更新服務內的credential。只替換主機檔案不會自動修改既有PostgreSQL角色密碼，也不會使已啟動的容器重新載入secret。P0-005不提供自動輪替。
