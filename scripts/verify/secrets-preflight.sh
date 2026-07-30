#!/bin/sh
set -eu

secret_dir="${PAOS_SECRET_DIR:-/opt/ai-pm-os/secrets/personal-asset-os}"

fail() {
    printf '%s\n' "secret preflight failed: $1" >&2
    exit 1
}

[ -d "$secret_dir" ] || fail "secret directory is missing"
[ ! -L "$secret_dir" ] || fail "secret directory must not be a symlink"

directory_mode="$(stat -c '%a' -- "$secret_dir")"
directory_owner="$(stat -c '%u' -- "$secret_dir")"
[ "$directory_mode" = "700" ] || fail "secret directory mode must be 0700"

for secret_name in postgres_password redis_password; do
    secret_path="$secret_dir/$secret_name"
    [ -f "$secret_path" ] || fail "$secret_name is missing"
    [ ! -L "$secret_path" ] || fail "$secret_name must not be a symlink"

    file_mode="$(stat -c '%a' -- "$secret_path")"
    file_owner="$(stat -c '%u' -- "$secret_path")"
    file_size="$(stat -c '%s' -- "$secret_path")"

    [ "$file_mode" = "444" ] || fail "$secret_name mode must be 0444"
    [ "$file_owner" = "$directory_owner" ] ||
        fail "$secret_name owner must match the directory owner"
    [ "$file_size" -ge 32 ] || fail "$secret_name is too short"
    [ "$file_size" -le 513 ] || fail "$secret_name is too long"
done

printf '%s\n' "secret preflight passed"
