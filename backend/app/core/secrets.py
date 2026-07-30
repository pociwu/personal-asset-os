from pathlib import Path

from pydantic import SecretStr

_MINIMUM_SECRET_LENGTH = 32
_MAXIMUM_SECRET_LENGTH = 512
_UNSAFE_VALUES = frozenset(
    {
        "changeme",
        "password",
        "personal_asset_os",
        "postgres",
        "redis",
        "secret",
    }
)


class SecretConfigurationError(RuntimeError):
    """Report an invalid secret boundary without exposing sensitive details."""


def load_secret_file(
    path: Path | None,
    *,
    name: str,
    required: bool,
) -> SecretStr | None:
    if path is None:
        if required:
            raise SecretConfigurationError(f"{name} secret file is required")
        return None

    try:
        raw_value = path.read_text(encoding="utf-8")
    except (OSError, UnicodeError):
        raise SecretConfigurationError(f"{name} secret file is unavailable") from None

    if raw_value.endswith("\r\n"):
        value = raw_value[:-2]
    elif raw_value.endswith("\n"):
        value = raw_value[:-1]
    else:
        value = raw_value

    if "\r" in value or "\n" in value:
        raise SecretConfigurationError(f"{name} secret must be one line")
    if not value or any(character.isspace() for character in value):
        raise SecretConfigurationError(f"{name} secret has an unsafe format")
    if value.casefold() in _UNSAFE_VALUES:
        raise SecretConfigurationError(f"{name} secret uses an unsafe value")
    if not _MINIMUM_SECRET_LENGTH <= len(value) <= _MAXIMUM_SECRET_LENGTH:
        raise SecretConfigurationError(f"{name} secret has an unsafe length")

    return SecretStr(value)
