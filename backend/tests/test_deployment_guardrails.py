from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
POLICY = ROOT / "scripts" / "deploy" / "compose-policy.py"
WRAPPER = (ROOT / "scripts" / "deploy" / "verify-candidate").read_text(encoding="utf-8")
SUDOERS = (ROOT / "deploy" / "sudoers" / "paos-ai-pm").read_text(encoding="utf-8")
TAILSCALE = (ROOT / "scripts" / "deploy" / "configure-tailscale-serve.sh").read_text(
    encoding="utf-8"
)


def valid_configuration(candidate_root: Path) -> dict[str, Any]:
    secret_root = candidate_root / "secrets"
    repository = candidate_root / "repository"
    return {
        "services": {
            "web": {
                "build": {"context": str(repository)},
                "ports": [
                    {"host_ip": "127.0.0.1", "published": "18080", "target": 8080}
                ],
            },
            "backend": {"build": {"context": str(repository / "backend")}},
            "postgres": {
                "volumes": [
                    {
                        "type": "volume",
                        "source": "postgres_data",
                        "target": "/var/lib/postgresql/data",
                    }
                ],
                "secrets": [{"source": "postgres_password"}],
            },
            "redis": {"secrets": [{"source": "redis_password"}]},
        },
        "networks": {"edge": {}, "internal": {"internal": True}},
        "secrets": {
            "postgres_password": {"file": str(secret_root / "postgres_password")},
            "redis_password": {"file": str(secret_root / "redis_password")},
        },
    }


def run_policy(configuration: dict[str, Any], candidate_root: Path) -> int:
    result = subprocess.run(
        [sys.executable, str(POLICY), "--candidate-root", str(candidate_root)],
        input=json.dumps(configuration),
        text=True,
        capture_output=True,
        check=False,
    )
    return result.returncode


def test_compose_policy_accepts_only_isolated_candidate_shape(tmp_path: Path) -> None:
    assert run_policy(valid_configuration(tmp_path), tmp_path) == 0


def test_compose_policy_rejects_host_mounts_and_public_ports(tmp_path: Path) -> None:
    host_mount = valid_configuration(tmp_path)
    host_mount["services"]["backend"]["volumes"] = [
        {"type": "bind", "source": "/", "target": "/host"}
    ]
    assert run_policy(host_mount, tmp_path) == 1

    public_port = valid_configuration(tmp_path)
    public_port["services"]["web"]["ports"][0]["host_ip"] = "0.0.0.0"
    assert run_policy(public_port, tmp_path) == 1


def test_candidate_wrapper_has_fixed_inputs_and_never_runs_candidate_scripts() -> None:
    assert r"^[0-9a-f]{40}$" in WRAPPER
    assert "exactly one commit SHA is required" in WRAPPER
    assert "paos-compose-policy.py" in WRAPPER
    assert WRAPPER.index("compose config --format json") < WRAPPER.index("compose up")
    assert "$WORKTREE/scripts/" not in WRAPPER
    assert "Architecture" in WRAPPER and '"arm64"' in WRAPPER
    assert "/usr/local/sbin/paos-verify-candidate [0-9a-f]*" in SUDOERS


def test_tailscale_configuration_disables_funnel_and_targets_loopback() -> None:
    assert TAILSCALE.index("tailscale funnel off") < TAILSCALE.index(
        "tailscale serve --bg"
    )
    assert "http://127.0.0.1:8080" in TAILSCALE
