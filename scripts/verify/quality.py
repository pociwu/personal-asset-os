#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import os
import shutil
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BACKEND = ROOT / "backend"
FRONTEND = ROOT / "frontend"


@dataclass(frozen=True)
class Check:
    label: str
    command: tuple[str, ...]
    cwd: Path


def resolve_command(*names: str) -> str:
    for name in names:
        resolved = shutil.which(name)
        if resolved:
            return resolved
    raise RuntimeError(f"required command is unavailable: {names[0]}")


def resolve_uv_command() -> tuple[str, ...]:
    executable = shutil.which("uv")
    if executable:
        return (executable,)
    if importlib.util.find_spec("uv"):
        return (sys.executable, "-m", "uv")
    raise RuntimeError("required command is unavailable: uv")


def checks() -> tuple[Check, ...]:
    uv = resolve_uv_command()
    npm = resolve_command("npm.cmd", "npm")
    return (
        Check("Backend dependency sync", (*uv, "sync", "--locked"), BACKEND),
        Check(
            "Backend lint",
            (
                *uv,
                "run",
                "--locked",
                "ruff",
                "check",
                "app",
                "tests",
                "../scripts/verify/quality.py",
            ),
            BACKEND,
        ),
        Check(
            "Backend format",
            (
                *uv,
                "run",
                "--locked",
                "ruff",
                "format",
                "--check",
                "app",
                "tests",
                "../scripts/verify/quality.py",
            ),
            BACKEND,
        ),
        Check(
            "Backend type check",
            (*uv, "run", "--locked", "mypy"),
            BACKEND,
        ),
        Check(
            "Backend unit tests",
            (*uv, "run", "--locked", "pytest"),
            BACKEND,
        ),
        Check("Frontend dependency sync", (npm, "ci"), FRONTEND),
        Check("Frontend lint", (npm, "run", "lint"), FRONTEND),
        Check("Frontend format", (npm, "run", "format:check"), FRONTEND),
        Check("Frontend type check", (npm, "run", "typecheck"), FRONTEND),
        Check("Frontend unit tests", (npm, "test"), FRONTEND),
        Check("Frontend production build", (npm, "run", "build"), FRONTEND),
    )


def main() -> int:
    try:
        quality_checks = checks()
    except RuntimeError as error:
        print(error, file=sys.stderr)
        return 2

    for index, check in enumerate(quality_checks, start=1):
        print(f"[{index}/{len(quality_checks)}] {check.label}", flush=True)
        environment = os.environ.copy()
        environment.setdefault("UV_CACHE_DIR", str(ROOT / ".uv-cache"))
        environment.setdefault("UV_PYTHON_DOWNLOADS", "never")
        result = subprocess.run(
            check.command,
            cwd=check.cwd,
            check=False,
            env=environment,
        )
        if result.returncode != 0:
            print(
                f"quality gate failed: {check.label}",
                file=sys.stderr,
            )
            return result.returncode

    print("quality gate passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
