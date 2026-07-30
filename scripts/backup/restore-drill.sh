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

container_name="paos-restore-drill-$$-$RANDOM"
container_started=false

cleanup() {
    if [[ "$container_started" == "true" ]]; then
        docker rm --force --volumes "$container_name" >/dev/null 2>&1 || true
    fi
}
trap cleanup EXIT

docker run \
    --detach \
    --name "$container_name" \
    --network none \
    --tmpfs /var/lib/postgresql/data:rw,noexec,nosuid,size=2g \
    --env POSTGRES_HOST_AUTH_METHOD=trust \
    "$POSTGRES_IMAGE" >/dev/null
container_started=true

database_ready=false
for _ in {1..30}; do
    if docker exec --user postgres "$container_name" \
        pg_isready --username postgres --dbname postgres >/dev/null 2>&1; then
        database_ready=true
        break
    fi
    sleep 1
done
[[ "$database_ready" == "true" ]] || fail "isolated PostgreSQL did not become ready"

docker exec --user postgres "$container_name" \
    createdb --username postgres "$DATABASE_NAME"

age --decrypt \
    --identity "$PAOS_AGE_IDENTITY_FILE" \
    "$BACKUP_ARTIFACT" |
    docker exec --interactive --user postgres "$container_name" \
        pg_restore \
        --exit-on-error \
        --no-owner \
        --no-acl \
        --dbname="$DATABASE_NAME" \
        --username=postgres

restored_database="$(
    docker exec --user postgres "$container_name" \
        psql \
        --tuples-only \
        --no-align \
        --username postgres \
        --dbname "$DATABASE_NAME" \
        --command 'SELECT current_database();'
)"
[[ "$restored_database" == "$DATABASE_NAME" ]] ||
    fail "isolated restore sanity check failed"

printf '%s\n' "isolated restore drill passed: $1"
