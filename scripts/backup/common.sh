#!/usr/bin/env bash

set -Eeuo pipefail

PROJECT_ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/../.." && pwd -P)"
COMPOSE_FILE="$PROJECT_ROOT/deploy/compose.yaml"
BACKUP_DIR="${PAOS_BACKUP_DIR:-/var/backups/personal-asset-os}"
AGE_RECIPIENT_FILE="${PAOS_AGE_RECIPIENT_FILE:-/opt/ai-pm-os/secrets/personal-asset-os/backup_age_recipient}"
POSTGRES_IMAGE="postgres:16.14-bookworm"
DATABASE_NAME="personal_asset_os"
DATABASE_USER="personal_asset_os"

fail() {
    printf '%s\n' "backup operation failed: $1" >&2
    exit 1
}

require_command() {
    command -v "$1" >/dev/null 2>&1 || fail "required command is unavailable: $1"
}

require_backup_directory() {
    [[ -d "$BACKUP_DIR" ]] || fail "backup directory is missing"
    [[ ! -L "$BACKUP_DIR" ]] || fail "backup directory must not be a symlink"
    [[ -w "$BACKUP_DIR" ]] || fail "backup directory is not writable"
}

require_recipient_file() {
    [[ -f "$AGE_RECIPIENT_FILE" ]] || fail "age recipient file is missing"
    [[ ! -L "$AGE_RECIPIENT_FILE" ]] || fail "age recipient file must not be a symlink"
}

require_identity_file() {
    local identity_file="${PAOS_AGE_IDENTITY_FILE:-}"
    [[ -n "$identity_file" ]] || fail "PAOS_AGE_IDENTITY_FILE is required"
    [[ -f "$identity_file" ]] || fail "age identity file is missing"
    [[ ! -L "$identity_file" ]] || fail "age identity file must not be a symlink"

    local identity_mode
    identity_mode="$(stat -c '%a' -- "$identity_file")"
    [[ "$identity_mode" == "600" ]] || fail "age identity file mode must be 0600"
}

require_disk_headroom() {
    local used_percent
    used_percent="$(df -P -- "$BACKUP_DIR" | awk 'NR == 2 {gsub(/%/, "", $5); print $5}')"
    [[ "$used_percent" =~ ^[0-9]+$ ]] || fail "unable to determine disk usage"
    ((used_percent < 90)) || fail "disk usage is 90 percent or higher"
}

acquire_backup_lock() {
    exec 9>"$BACKUP_DIR/.backup.lock"
    flock -n 9 || fail "another backup or restore operation is running"
}

resolve_backup_artifact() {
    local artifact_name="${1:-}"
    [[ "$artifact_name" =~ ^postgres-[0-9]{8}T[0-9]{6}Z\.dump\.age$ ]] ||
        fail "backup artifact name is invalid"

    BACKUP_ARTIFACT="$BACKUP_DIR/$artifact_name"
    BACKUP_CHECKSUM="$BACKUP_ARTIFACT.sha256"
    [[ -f "$BACKUP_ARTIFACT" ]] || fail "backup artifact is missing"
    [[ -f "$BACKUP_CHECKSUM" ]] || fail "backup checksum is missing"
    [[ ! -L "$BACKUP_ARTIFACT" ]] || fail "backup artifact must not be a symlink"
    [[ ! -L "$BACKUP_CHECKSUM" ]] || fail "backup checksum must not be a symlink"
}

verify_checksum() {
    (
        cd -- "$BACKUP_DIR"
        sha256sum --check --status -- "$(basename -- "$BACKUP_CHECKSUM")"
    ) || fail "backup checksum verification failed"
}
