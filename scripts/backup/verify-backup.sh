#!/usr/bin/env bash

set -Eeuo pipefail
source "$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)/common.sh"

[[ "$#" -eq 1 ]] || fail "exactly one backup artifact name is required"

require_command age
require_command docker
require_command flock
require_command sha256sum
require_backup_directory
require_identity_file
require_disk_headroom
acquire_backup_lock
resolve_backup_artifact "$1"
verify_checksum

age --decrypt \
    --identity "$PAOS_AGE_IDENTITY_FILE" \
    "$BACKUP_ARTIFACT" |
    docker run \
        --rm \
        --interactive \
        --network none \
        "$POSTGRES_IMAGE" \
        pg_restore --list >/dev/null

printf '%s\n' "backup decrypted and archive structure verified: $1"
