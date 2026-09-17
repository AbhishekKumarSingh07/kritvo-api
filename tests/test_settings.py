import pytest

from kritvo.core.settings import Settings


def test_defaults_are_safe_for_local() -> None:
    settings = Settings(_env_file=None)
    assert settings.app_env == "local"
    assert settings.docs_enabled is True


def test_production_hides_docs(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("APP_ENV", "production")
    settings = Settings(_env_file=None)
    assert settings.docs_enabled is False


def test_invalid_env_is_rejected(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("APP_ENV", "prod")
    with pytest.raises(ValueError, match="app_env"):
        Settings(_env_file=None)
