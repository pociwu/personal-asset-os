# Backup and isolated restore

Phase 0只提供Owner手動執行的PostgreSQL備份、驗證及隔離還原底座。Redis是可重建的session／cache，不納入備份。排程、Object Storage上傳及保留政策自動化屬於Phase 1。

## 安全邊界

- `pg_dump`使用PostgreSQL custom format。
- dump直接串流至`age`，主機不建立明文dump。
- 加密檔與SHA-256 checksum位於Repository外的`/var/backups/personal-asset-os/`。
- 主機長期只保存`age`recipient公鑰，不保存identity私鑰。
- identity只在Owner核准的驗證／還原演練期間提供，完成後卸載或移除。
- 還原只使用`--network none`、tmpfs資料目錄及固定PostgreSQL映像的一次性容器；不掛載正式volume。
- 所有操作使用同一把`flock`，避免備份與還原重疊。
- 磁碟使用率達90%時拒絕建立備份或執行還原演練。

## Ubuntu前置準備

Owner在離線裝置產生identity，identity不得複製至Repository或長期保存在OCI：

```bash
age-keygen -o paos-backup-identity.txt
age-keygen -y paos-backup-identity.txt > backup_age_recipient
chmod 0600 paos-backup-identity.txt
```

只把`backup_age_recipient`傳至主機，並準備備份目錄：

```bash
sudo install -d -m 0700 -o deploy -g deploy /var/backups/personal-asset-os
sudo install -m 0444 -o root -g root backup_age_recipient /opt/ai-pm-os/secrets/personal-asset-os/backup_age_recipient
```

主機需要Docker Compose v2、`age`、`flock`及GNU coreutils。

## 建立加密備份

由Owner或核准的部署帳號執行：

```bash
scripts/backup/create-backup.sh
```

成功後只輸出通用artifact名稱，例如：

```text
postgres-YYYYMMDDTHHMMSSZ.dump.age
postgres-YYYYMMDDTHHMMSSZ.dump.age.sha256
```

任何dump、加密、檔案大小或checksum步驟失敗時，腳本返回非零狀態且不保留半成品。

## 解密可讀驗證

Owner暫時提供identity檔案，權限必須為`0600`：

```bash
export PAOS_AGE_IDENTITY_FILE=/media/owner-key/paos-backup-identity.txt
scripts/backup/verify-backup.sh postgres-YYYYMMDDTHHMMSSZ.dump.age
```

驗證流程檢查checksum，串流解密後以固定PostgreSQL 16映像執行`pg_restore --list`；不建立明文dump。

## 隔離還原演練

```bash
export PAOS_AGE_IDENTITY_FILE=/media/owner-key/paos-backup-identity.txt
scripts/backup/restore-drill.sh postgres-YYYYMMDDTHHMMSSZ.dump.age
unset PAOS_AGE_IDENTITY_FILE
```

演練建立無網路、tmpfs資料目錄的一次性PostgreSQL容器，還原成功並完成基本查詢後立即移除。Phase 1有正式模型與固定fixture後，必須擴充為Owner、金融帳戶、Asset、Holding、audit及固定Decimal結果驗證。

目標RPO為24小時，主機恢復後RTO為2小時；Phase 1才加入每日03:00排程、本機7份、遠端30份每日／12份每月及Private Object Storage。
