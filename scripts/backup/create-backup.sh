#!/usr/bin/env bash

set -Eeuo pipefail
source "$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)/common.sh"

require_command age
require_command docker
require_command flock
require_command sha256sum
require_backup_directory
require_recipient_file
require_disk_headroom
acquire_backup_lock

timestamp="$(date -u '+%Y%m%dT%H%M%SZ')"
artifact_name="postgres-$timestamp.dump.age"
artifact_path="$BACKUP_DIR/$artifact_name"
checksum_path="$artifact_path.sha256"
temporary_artifact="$(mktemp "$BACKUP_DIR/.postgres-dump.XXXXXXXXXX")"
temporary_checksum="$(mktemp "$BACKUP_DIR/.postgres-checksum.XXXXXXXXXX")"

cleanup() {
    rm -f -- "$temporary_artifact" "$temporary_checksum"
}
trap cleanup EXIT

[[ ! -e "$artifact_path" ]] || fail "backup artifact already exists"

docker compose --file "$COMPOSE_FILE" exec --no-TTY --user postgres postgres \
    pg_dump \
    --format=custom \
    --no-owner \
    --no-acl \
    --dbname="$DATABASE_NAME" \
    --username="$DATABASE_USER" |
    age --encrypt \
        --recipients-file "$AGE_RECIPIENT_FILE" \
        --output "$temporary_artifact"

[[ -s "$temporary_artifact" ]] || fail "encrypted backup is empty"
chmod 0600 "$temporary_artifact"
mv -- "$temporary_artifact" "$artifact_path"

(
    cd -- "$BACKUP_DIR"
    sha256sum -- "$artifact_name" >"$temporary_checksum"
)
mv -- "$temporary_checksum" "$checksum_path"
chmod 0600 "$checksum_path"

resolve_backup_artifact "$artifact_name"
verify_checksum

printf '%s\n' "backup created and checksum verified: $artifact_name"
