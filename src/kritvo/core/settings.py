"""Application settings, loaded only from environment variables (and a local .env file)."""

from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_name: str = "Kritvo API"
    app_env: Literal["local", "test", "staging", "production"] = "local"
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR"] = "INFO"
    cors_origins: list[str] = Field(default_factory=lambda: ["http://localhost:5173"])
    # kritvo_app credentials (LLD section 2.1). Optional so the app and its tests can
    # start without a live database; docker-compose and production always set it.
    database_url: str | None = None

    # ===== Identity (TASK-003, LLD 12.1-12.2) =====
    # HMAC keys for one-way, lookup-only hashing (phone_hash, otp_codes.code_hash).
    # Kept separate so a leak of one never helps brute-force the other.
    phone_hmac_key: str = "change-me"
    otp_hmac_key: str = "change-me"
    # A single application-level key for the one encrypted column TASK-003 touches
    # (users.totp_secret_enc). This is deliberately not the per-tenant KMS envelope
    # encryption LLD 12.4 describes for phone/GSTIN columns — that is a larger,
    # separate undertaking TASK-003's scope does not require, since it never touches
    # phone_enc or any tenant-scoped encrypted column.
    totp_enc_key: str = "change-me-32-byte-urlsafe-base64-fernet-key="
    # A directory of "<kid>.pem" Ed25519 private keys; jwt_active_kid signs new access
    # tokens, but every key in the directory still verifies, so a just-retired kid
    # keeps validating tokens issued under it until they expire ("two keys active
    # during rotation").
    jwt_signing_keys_dir: Path = Path("./secrets/jwt_keys")
    jwt_active_kid: str = "dev"
    # Only "logging" (ADR-0008) exists today; TASK-013/TASK-019 add a real option here.
    notification_sender: Literal["logging"] = "logging"

    @property
    def docs_enabled(self) -> bool:
        return self.app_env != "production"


@lru_cache
def get_settings() -> Settings:
    return Settings()
