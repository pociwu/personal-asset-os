import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
WORKFLOW = (ROOT / ".github" / "workflows" / "ci.yml").read_text(encoding="utf-8")
INTEGRATION = (ROOT / "scripts" / "verify" / "ubuntu-integration.sh").read_text(
    encoding="utf-8"
)
WEB_DOCKERFILE = (ROOT / "deploy" / "nginx" / "Dockerfile").read_text(encoding="utf-8")
NGINX_CONFIG = (ROOT / "deploy" / "nginx" / "nginx.conf").read_text(encoding="utf-8")
COMPOSE = (ROOT / "deploy" / "compose.yaml").read_text(encoding="utf-8")


def test_all_actions_are_pinned_to_full_commit_shas() -> None:
    action_references = re.findall(
        r"^\s*uses:\s*[^@\s]+@([^\s#]+)",
        WORKFLOW,
        re.MULTILINE,
    )

    assert action_references
    assert all(re.fullmatch(r"[0-9a-f]{40}", ref) for ref in action_references)


def test_ci_covers_quality_dependencies_secrets_and_images() -> None:
    required_fragments = (
        "python scripts/verify/quality.py",
        "uv export --locked --no-dev --no-emit-project",
        "uv run --locked pip-audit --strict",
        "npm audit --audit-level=high",
        "gitleaks/gitleaks-action@",
        "scan-type: fs",
        "image-ref: personal-asset-os/backend:candidate",
        "image-ref: personal-asset-os/web:candidate",
    )

    assert all(fragment in WORKFLOW for fragment in required_fragments)


def test_integration_covers_health_failure_recovery_and_restore() -> None:
    required_fragments = (
        'wait_for_status "/api/v1/health" "200"',
        'wait_for_status "/api/v1/health/ready" "503"',
        "compose run --rm --no-deps backend alembic -c alembic.ini upgrade head",
        "compose stop postgres",
        "compose start postgres",
        "scripts/backup/create-backup.sh",
        "scripts/backup/verify-backup.sh",
        "scripts/backup/restore-drill.sh",
    )

    assert all(fragment in INTEGRATION for fragment in required_fragments)
    assert "docker compose down --volumes" not in INTEGRATION


def test_web_runtime_is_explicitly_non_root() -> None:
    assert "FROM alpine:3.23.5" in WEB_DOCKERFILE
    assert "'nginx~1.28'" in WEB_DOCKERFILE
    assert "USER nginx" in WEB_DOCKERFILE
    assert "pid /tmp/nginx.pid;" in NGINX_CONFIG
    assert "_temp_path /tmp/" in NGINX_CONFIG


def test_redis_runtime_does_not_depend_on_missing_privilege_helper() -> None:
    assert "user: redis" in COMPOSE
    assert "uid=999,gid=999" in COMPOSE
    assert "gosu" not in COMPOSE


def test_web_has_a_loopback_edge_while_dependencies_stay_internal() -> None:
    web_section, backend_and_dependencies = COMPOSE.split("\n  backend:", maxsplit=1)

    assert '"127.0.0.1:${PAOS_WEB_PORT:-8080}:8080"' in web_section
    assert "- edge" in web_section
    assert "- edge" not in backend_and_dependencies.split("\nnetworks:", maxsplit=1)[0]
    assert "internal:\n    internal: true" in COMPOSE
