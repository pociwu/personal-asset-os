#!/usr/bin/env bash

set -Eeuo pipefail

fail() {
    printf '%s\n' "Ubuntu preflight failed: $1" >&2
    exit 1
}

[[ "$(id -u)" -eq 0 ]] || fail "run with sudo"
source /etc/os-release
[[ "${ID:-}" == "ubuntu" && "${VERSION_ID:-}" == "24.04" ]] ||
    fail "Ubuntu 24.04 is required"
[[ "$(dpkg --print-architecture)" == "arm64" ]] || fail "native arm64 is required"
(( $(nproc) >= 2 )) || fail "at least 2 OCPU are required"
memory_kib="$(awk '/MemTotal/ {print $2}' /proc/meminfo)"
((memory_kib >= 11000000)) || fail "at least 12 GB RAM is required"
disk_kib="$(df -Pk / | awk 'NR == 2 {print $2}')"
((disk_kib >= 100000000)) || fail "at least 100 GB system disk is required"

for command_name in age curl docker flock git openssl tailscale; do
    command -v "$command_name" >/dev/null 2>&1 ||
        fail "required command is unavailable: $command_name"
done
docker compose version >/dev/null

for account in admin ai-pm deploy; do
    id "$account" >/dev/null 2>&1 || fail "required account is missing: $account"
done
id -nG ai-pm | grep -qw docker && fail "ai-pm must not be in the docker group"
id -nG deploy | grep -qw docker || fail "deploy must be in the docker group"
[[ "$(sysctl -n vm.overcommit_memory)" == "1" ]] ||
    fail "vm.overcommit_memory must be 1 for Redis"

printf '%s\n' "Ubuntu ARM64 host preflight passed"
