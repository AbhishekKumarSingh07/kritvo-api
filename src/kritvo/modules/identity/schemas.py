"""Request/response models for the seven identity endpoints (LLD 12.1-12.2)."""

from uuid import UUID

from pydantic import BaseModel, ConfigDict


class OtpRequestIn(BaseModel):
    model_config = ConfigDict(extra="forbid")
    phone: str
    device_id: str


class OtpVerifyIn(BaseModel):
    model_config = ConfigDict(extra="forbid")
    phone: str
    code: str
    device_id: str
    platform: str = "pwa"


class LoginIn(BaseModel):
    model_config = ConfigDict(extra="forbid")
    identifier: str  # phone or email
    password: str


class TotpPendingOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    pending_token: str


class TotpVerifyIn(BaseModel):
    model_config = ConfigDict(extra="forbid")
    pending_token: str
    code: str
    device_id: str
    platform: str = "pwa"


class SwitchTenantIn(BaseModel):
    model_config = ConfigDict(extra="forbid")
    tenant_id: UUID


class TokenOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    access_token: str
    token_type: str = "bearer"  # noqa: S105 — the OAuth2 token type, not a credential
    expires_in: int


class LogoutOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    ok: bool = True


class OtpRequestOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    ok: bool = True
