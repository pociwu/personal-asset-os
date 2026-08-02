# Ubuntu 24.04 ARM64 test host

本文件準備P0-010實際OCI ARM64 Phase Gate。P0-009只建立主機基線、Tailscale私人入口及受限wrapper；執行成功前不得宣稱OCI驗收完成。

## OCI網路

- Ubuntu 24.04 ARM64、2 OCPU、12 GB RAM、至少100 GB系統碟。
- OCI Security List／NSG不得開放公網`80`、`443`、`5432`、`6379`。
- SSH只允許Owner管理來源；Tailscale可只使用出站連線及DERP。
- 產品入口最終只有Tailscale Serve HTTPS；Compose Web只綁定`127.0.0.1:8080`。

## Docker與主機套件

依Docker官方Ubuntu apt repository安裝；不要使用convenience script。Docker官方支援Ubuntu 24.04及ARM64：

```bash
sudo apt-get update
sudo apt-get install --yes ca-certificates curl
sudo install -m 0755 -d /etc/apt/keyrings
sudo curl -fsSL https://download.docker.com/linux/ubuntu/gpg -o /etc/apt/keyrings/docker.asc
sudo chmod a+r /etc/apt/keyrings/docker.asc
sudo tee /etc/apt/sources.list.d/docker.sources >/dev/null <<EOF
Types: deb
URIs: https://download.docker.com/linux/ubuntu
Suites: $(. /etc/os-release && echo "${UBUNTU_CODENAME:-$VERSION_CODENAME}")
Components: stable
Architectures: $(dpkg --print-architecture)
Signed-By: /etc/apt/keyrings/docker.asc
EOF
sudo apt-get update
sudo apt-get install --yes docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
sudo apt-get install --yes age git openssl
docker compose version
```

依Tailscale官方Ubuntu Noble repository安裝後，由Owner互動登入：

```bash
sudo curl -fsSL https://pkgs.tailscale.com/stable/ubuntu/noble.noarmor.gpg -o /usr/share/keyrings/tailscale-archive-keyring.gpg
sudo curl -fsSL https://pkgs.tailscale.com/stable/ubuntu/noble.tailscale-keyring.list -o /etc/apt/sources.list.d/tailscale.list
sudo apt-get update
sudo apt-get install --yes tailscale
sudo tailscale up
tailscale status
```

不要把auth key、登入URL或tailnet名稱寫入Git、Issue或Log。

## 帳號與Docker權限

```bash
sudo adduser admin
sudo adduser ai-pm
sudo adduser deploy
sudo usermod -aG sudo admin
sudo usermod -aG docker deploy
```

`ai-pm`不得加入`docker`群組；開發型Agent不得登入`deploy`。設定Redis主機條件：

```bash
printf 'vm.overcommit_memory=1\n' | sudo tee /etc/sysctl.d/99-paos-redis.conf
sudo sysctl --system
```

正式Repository固定於`/opt/ai-pm-os/projects/personal-asset-os`並由`deploy`擁有。Secret依[Secret files操作指南](SECRETS.md)建立；備份recipient及目錄依[備份與隔離還原指南](BACKUP_RESTORE.md)建立。

首次建立公開Repository工作副本：

```bash
sudo install -d -m 0755 -o deploy -g deploy /opt/ai-pm-os/projects
sudo -u deploy git clone https://github.com/pociwu/personal-asset-os.git \
  /opt/ai-pm-os/projects/personal-asset-os
sudo -u deploy git -C /opt/ai-pm-os/projects/personal-asset-os fetch --prune origin
```

## 安裝root-owned驗證wrapper

由`admin`在已審閱的P0-009 commit執行：

```bash
sudo install -d -m 0755 /usr/local/libexec
sudo install -m 0755 scripts/deploy/compose-policy.py /usr/local/libexec/paos-compose-policy.py
sudo install -m 0755 scripts/deploy/verify-candidate /usr/local/sbin/paos-verify-candidate
sudo visudo -cf deploy/sudoers/paos-ai-pm
sudo install -m 0440 deploy/sudoers/paos-ai-pm /etc/sudoers.d/paos-ai-pm
sudo scripts/deploy/ubuntu-preflight.sh
```

Wrapper只接受一個完整小寫commit SHA，且SHA必須可由`origin`遠端分支到達。它使用固定Repository、合成secret、`127.0.0.1:18080`、獨立Compose project及測試volume；先拒絕host mount、額外服務、公開Port、privileged／host namespace及secret路徑逃逸，再依序執行原生ARM64 build、啟動PostgreSQL／Redis、一次性Alembic migration、啟動Web／Backend、health、故障及恢復驗證。清理只刪除該SHA的測試project、volume、映像與worktree。

AI-PM可執行：

```bash
sudo /usr/local/sbin/paos-verify-candidate <40-character-commit-sha>
```

本次公開候選分支可由`ai-pm`解析為完整SHA後送入wrapper：

```bash
REPOSITORY=/opt/ai-pm-os/projects/personal-asset-os
sudo -u deploy git -C "$REPOSITORY" fetch --prune origin
CANDIDATE_SHA="$(sudo -u deploy git -C "$REPOSITORY" \
  rev-parse origin/codex/alpha-other-assets-income)"
printf '%s\n' "$CANDIDATE_SHA"
sudo /usr/local/sbin/paos-verify-candidate "$CANDIDATE_SHA"
```

畫面列印SHA供Owner核對，不會列印secret。候選驗收會使用合成資料並在結束時清除，不會建立長期正式服務。

不能傳入命令、branch、Compose路徑、Port、volume或secret參數。

## Tailscale私人入口

正式四服務已由Owner啟動且`http://127.0.0.1:8080/healthz`成功後，由`admin`執行：

```bash
sudo scripts/deploy/configure-tailscale-serve.sh
```

腳本先關閉Funnel、重設此專用主機既有Serve設定，再持久化`HTTPS 443 → http://127.0.0.1:8080`。Owner須在tailnet ACL限制只有自己的使用者／裝置可連線，並從已加入tailnet的裝置驗證HTTPS；OCI公網IP上的80／443必須不可連線。

## P0-010需要保存的證據

- 核准commit SHA與`uname -m`／Ubuntu版本／資源preflight結果
- Backend與Web映像ID及`arm64`architecture
- 四服務health、首頁、liveness、readiness 200→503→200
- PostgreSQL重啟後資料持久性
- 加密備份、checksum、archive可讀及隔離還原
- Tailscale HTTPS成功、Funnel關閉及公網Port不可達

只記錄非敏感結果，不記錄IP、OCID、tailnet名稱、secret路徑內容或正式Log。
