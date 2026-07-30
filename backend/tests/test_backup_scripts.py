from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BACKUP_SCRIPTS = ROOT / "scripts" / "backup"


def read_script(name: str) -> str:
    return (BACKUP_SCRIPTS / name).read_text(encoding="utf-8")


def test_backup_streams_dump_directly_to_age() -> None:
    script = read_script("create-backup.sh")

    assert "pg_dump" in script
    assert "|\n    age --encrypt" in script
    assert ".dump.age" in script
    assert '.dump"' not in script
    assert "redis" not in script.lower()


def test_verification_uses_fixed_offline_postgres_image() -> None:
    common = read_script("common.sh")
    script = read_script("verify-backup.sh")

    assert 'POSTGRES_IMAGE="postgres:16.14-bookworm"' in common
    assert "--network none" in script
    assert "pg_restore --list" in script
    assert "latest" not in common


def test_restore_drill_cannot_mount_production_storage() -> None:
    script = read_script("restore-drill.sh")

    assert "--network none" in script
    assert "--tmpfs /var/lib/postgresql/data:" in script
    assert "docker rm --force --volumes" in script
    assert "postgres_data" not in script
    assert "/opt/ai-pm-os" not in script


def test_private_identity_is_explicit_and_mode_checked() -> None:
    common = read_script("common.sh")

    assert 'local identity_file="${PAOS_AGE_IDENTITY_FILE:-}"' in common
    assert '[[ "$identity_mode" == "600" ]]' in common
    assert "AGE-SECRET-KEY" not in common
