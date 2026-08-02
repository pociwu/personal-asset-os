#!/usr/bin/env bash

set -Eeuo pipefail

PROJECT_ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/../.." && pwd -P)"
COMPOSE_FILE="$PROJECT_ROOT/deploy/compose.yaml"
TEST_ROOT="$(mktemp -d)"
SECRET_DIR="$TEST_ROOT/secrets"
BACKUP_DIR="$TEST_ROOT/backups"
IDENTITY_FILE="$TEST_ROOT/age-identity"
PROJECT_NAME="paos-ci-${GITHUB_RUN_ID:-local}-${GITHUB_RUN_ATTEMPT:-1}"
WEB_PORT="${PAOS_TEST_WEB_PORT:-18080}"

compose() {
    docker compose \
        --project-name "$PROJECT_NAME" \
        --file "$COMPOSE_FILE" \
        "$@"
}

cleanup() {
    local exit_status=$?
    if ((exit_status != 0)); then
        compose ps --all >&2 || true
        compose logs --no-color --timestamps >&2 || true
    fi
    compose down --volumes --remove-orphans >/dev/null 2>&1 || true
    rm -rf -- "$TEST_ROOT"
    return "$exit_status"
}
trap cleanup EXIT

wait_for_status() {
    local path="$1"
    local expected="$2"
    local status

    for _ in {1..30}; do
        status="$(
            curl \
                --silent \
                --show-error \
                --output /dev/null \
                --write-out '%{http_code}' \
                "http://127.0.0.1:$WEB_PORT$path" ||
                true
        )"
        if [[ "$status" == "$expected" ]]; then
            return 0
        fi
        sleep 2
    done

    printf '%s\n' "expected HTTP $expected from $path, received $status" >&2
    return 1
}

for command_name in age age-keygen curl docker openssl; do
    command -v "$command_name" >/dev/null 2>&1 ||
        {
            printf '%s\n' "required command is unavailable: $command_name" >&2
            exit 1
        }
done
docker compose version >/dev/null

install -d -m 0700 "$SECRET_DIR" "$BACKUP_DIR"
openssl rand -hex 32 >"$SECRET_DIR/postgres_password"
openssl rand -hex 32 >"$SECRET_DIR/redis_password"
chmod 0444 "$SECRET_DIR/postgres_password" "$SECRET_DIR/redis_password"

age-keygen --output "$IDENTITY_FILE" >/dev/null 2>&1
chmod 0600 "$IDENTITY_FILE"
age-keygen -y "$IDENTITY_FILE" >"$SECRET_DIR/backup_age_recipient"
chmod 0444 "$SECRET_DIR/backup_age_recipient"

export PAOS_SECRET_DIR="$SECRET_DIR"
export PAOS_BACKUP_DIR="$BACKUP_DIR"
export PAOS_AGE_RECIPIENT_FILE="$SECRET_DIR/backup_age_recipient"
export PAOS_AGE_IDENTITY_FILE="$IDENTITY_FILE"
export PAOS_COMPOSE_PROJECT_NAME="$PROJECT_NAME"
export PAOS_WEB_PORT="$WEB_PORT"
export PAOS_IMAGE_TAG="candidate"

compose config --quiet
compose build backend web
compose up --detach --wait --wait-timeout 120 postgres redis
compose run --rm --no-deps backend \
    uv run --locked alembic -c alembic.ini upgrade head
compose up --detach --wait --wait-timeout 180

wait_for_status "/" "200"
wait_for_status "/api/v1/health" "200"
wait_for_status "/api/v1/health/ready" "200"

compose stop postgres
wait_for_status "/api/v1/health" "200"
wait_for_status "/api/v1/health/ready" "503"

compose start postgres
wait_for_status "/api/v1/health/ready" "200"

backup_output="$("$PROJECT_ROOT/scripts/backup/create-backup.sh")"
artifact_name="${backup_output##*: }"
[[ "$artifact_name" =~ ^postgres-[0-9]{8}T[0-9]{6}Z\.dump\.age$ ]]

"$PROJECT_ROOT/scripts/backup/verify-backup.sh" "$artifact_name"
"$PROJECT_ROOT/scripts/backup/restore-drill.sh" "$artifact_name"

printf '%s\n' "Ubuntu Compose, dependency recovery, backup, and restore checks passed"
