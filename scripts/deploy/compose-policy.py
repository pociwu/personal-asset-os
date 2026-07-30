#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

EXPECTED_SERVICES = {"web", "backend", "postgres", "redis"}
FORBIDDEN_SERVICE_KEYS = {
    "cap_add",
    "devices",
    "ipc",
    "network_mode",
    "pid",
    "privileged",
}


def fail(message: str) -> None:
    raise ValueError(message)


def validate_service(name: str, service: dict[str, Any], test_root: Path) -> None:
    for key in FORBIDDEN_SERVICE_KEYS:
        if service.get(key):
            fail(f"{name}: forbidden service option: {key}")

    volumes = service.get("volumes", [])
    if name == "postgres":
        if (
            len(volumes) != 1
            or volumes[0].get("type") != "volume"
            or volumes[0].get("source") != "postgres_data"
            or volumes[0].get("target") != "/var/lib/postgresql/data"
        ):
            fail("postgres: only the isolated named data volume is allowed")
    elif volumes:
        fail(f"{name}: volumes are not allowed")

    ports = service.get("ports", [])
    if name == "web":
        if len(ports) != 1:
            fail("web: exactly one loopback test port is required")
        port = ports[0]
        if (
            port.get("host_ip") != "127.0.0.1"
            or int(port.get("published", 0)) != 18080
            or int(port.get("target", 0)) != 8080
        ):
            fail("web: port must be 127.0.0.1:18080:8080")
    elif ports:
        fail(f"{name}: published ports are not allowed")

    for secret in service.get("secrets", []):
        source = secret.get("source")
        if source not in {"postgres_password", "redis_password"}:
            fail(f"{name}: unexpected secret grant")

    build = service.get("build")
    if build:
        context = Path(build["context"]).resolve()
        if not context.is_relative_to(test_root.resolve()):
            fail(f"{name}: build context escapes the candidate worktree")


def validate(configuration: dict[str, Any], test_root: Path) -> None:
    services = configuration.get("services", {})
    if set(services) != EXPECTED_SERVICES:
        fail("exactly web, backend, postgres, and redis services are required")

    for name, service in services.items():
        validate_service(name, service, test_root)

    networks = configuration.get("networks", {})
    if set(networks) != {"edge", "internal"}:
        fail("exactly edge and internal networks are required")
    if networks["internal"].get("internal") is not True:
        fail("the dependency network must remain internal")

    secrets = configuration.get("secrets", {})
    if set(secrets) != {"postgres_password", "redis_password"}:
        fail("exactly two synthetic secrets are required")
    for secret in secrets.values():
        secret_file = Path(secret["file"]).resolve()
        if not secret_file.is_relative_to(test_root.resolve()):
            fail("secret file escapes the isolated verification directory")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--candidate-root", type=Path, required=True)
    arguments = parser.parse_args()

    try:
        validate(json.load(sys.stdin), arguments.candidate_root)
    except (KeyError, TypeError, ValueError, json.JSONDecodeError) as error:
        print(f"compose policy rejected candidate: {error}", file=sys.stderr)
        return 1

    print("compose policy passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
