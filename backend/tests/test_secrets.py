from pathlib import Path

import pytest

from app.core.config import Settings
from app.core.secrets import SecretConfigurationError, load_secret_file
from app.main import create_app


def test_load_secret_file_returns_a_redacted_value(tmp_path: Path) -> None:
    secret_path = tmp_path / "postgres_password"
    secret_path.write_text("a" * 64 + "\n", encoding="utf-8")

    secret = load_secret_file(
        secret_path,
        name="postgres_password",
        required=True,
    )

    assert secret is not None
    assert secret.get_secret_value() == "a" * 64
    assert repr(secret) == "SecretStr('**********')"


@pytest.mark.parametrize(
    "value",
    [
        "",
        " " * 32,
        "short",
        "password",
        "a" * 513,
        f"{'a' * 32}\n{'b' * 32}",
    ],
)
def test_load_secret_file_rejects_unsafe_values_without_echoing_them(
    tmp_path: Path,
    value: str,
) -> None:
    secret_path = tmp_path / "redis_password"
    secret_path.write_text(value, encoding="utf-8")

    with pytest.raises(SecretConfigurationError) as captured:
        load_secret_file(
            secret_path,
            name="redis_password",
            required=True,
        )

    assert str(captured.value) in {
        "redis_password secret has an unsafe format",
        "redis_password secret has an unsafe length",
        "redis_password secret must be one line",
        "redis_password secret uses an unsafe value",
    }
    assert str(secret_path) not in str(captured.value)


def test_load_secret_file_is_required_in_production() -> None:
    with pytest.raises(
        SecretConfigurationError,
        match="postgres_password secret file is required",
    ):
        load_secret_file(
            None,
            name="postgres_password",
            required=True,
        )


def test_load_secret_file_can_be_absent_for_local_development() -> None:
    assert (
        load_secret_file(
            None,
            name="postgres_password",
            required=False,
        )
        is None
    )


def test_production_app_refuses_to_start_without_secret_files() -> None:
    with pytest.raises(
        SecretConfigurationError,
        match="postgres_password secret file is required",
    ):
        create_app(Settings(app_env="production", log_level="WARNING"))


def test_production_app_accepts_independent_valid_secret_files(
    tmp_path: Path,
) -> None:
    postgres_path = tmp_path / "postgres_password"
    redis_path = tmp_path / "redis_password"
    postgres_path.write_text("a" * 64, encoding="utf-8")
    redis_path.write_text("b" * 64, encoding="utf-8")

    app = create_app(
        Settings(
            app_env="production",
            log_level="WARNING",
            postgres_password_file=postgres_path,
            redis_password_file=redis_path,
        )
    )

    assert app.state.readiness_probe is not None
