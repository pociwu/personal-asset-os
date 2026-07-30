from app.core.config import Settings


def test_settings_load_non_sensitive_paos_environment_values(
    monkeypatch,
) -> None:
    monkeypatch.setenv("PAOS_APP_NAME", "Personal Asset OS Test")
    monkeypatch.setenv("PAOS_APP_ENV", "test")
    monkeypatch.setenv("PAOS_LOG_LEVEL", "warning")

    settings = Settings()

    assert settings.app_name == "Personal Asset OS Test"
    assert settings.app_env == "test"
    assert settings.log_level == "warning"
