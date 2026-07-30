from pathlib import Path

from app.core.config import Settings


def test_settings_load_non_sensitive_paos_environment_values(
    monkeypatch,
) -> None:
    monkeypatch.setenv("PAOS_APP_NAME", "Personal Asset OS Test")
    monkeypatch.setenv("PAOS_APP_ENV", "test")
    monkeypatch.setenv("PAOS_LOG_LEVEL", "warning")
    monkeypatch.setenv(
        "PAOS_POSTGRES_PASSWORD_FILE",
        "/run/secrets/postgres_password",
    )
    monkeypatch.setenv(
        "PAOS_REDIS_PASSWORD_FILE",
        "/run/secrets/redis_password",
    )

    settings = Settings()

    assert settings.app_name == "Personal Asset OS Test"
    assert settings.app_env == "test"
    assert settings.log_level == "warning"
    assert settings.postgres_password_file == Path(
        "/run/secrets/postgres_password"
    )
    assert settings.redis_password_file == Path("/run/secrets/redis_password")
    assert not hasattr(settings, "postgres_password")
    assert not hasattr(settings, "redis_password")
