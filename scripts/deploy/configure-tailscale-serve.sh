#!/usr/bin/env bash

set -Eeuo pipefail

[[ "$(id -u)" -eq 0 ]] || {
    printf '%s\n' "run with sudo" >&2
    exit 1
}
tailscale status >/dev/null
curl --fail --silent --show-error http://127.0.0.1:8080/healthz >/dev/null

tailscale funnel off
tailscale serve reset
tailscale serve --bg --yes --https=443 http://127.0.0.1:8080
tailscale serve status
