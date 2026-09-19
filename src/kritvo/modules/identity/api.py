"""Identity endpoints: OTP, password+TOTP login, tokens (LLD 5.2, 12.1-12.2)."""

from typing import Annotated

from fastapi import APIRouter, Cookie, Depends, Request, Response
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from kritvo.core.deps import get_app_settings, get_principal, get_sessionmaker
from kritvo.core.errors import AppError
from kritvo.core.principal import Principal
from kritvo.core.settings import Settings
from kritvo.core.tokens import ACCESS_TOKEN_TTL, KeyRing
from kritvo.modules.identity import service
from kritvo.modules.identity.schemas import (
    LoginIn,
    LogoutOut,
    OtpRequestIn,
    OtpRequestOut,
    OtpVerifyIn,
    SwitchTenantIn,
    TokenOut,
    TotpPendingOut,
    TotpVerifyIn,
)
from kritvo.modules.notifications.interface import NotificationSender

router = APIRouter(prefix="/auth", tags=["identity"])

_REFRESH_COOKIE = "refresh_token"
_REFRESH_COOKIE_PATH = "/api/v1/auth"


def _key_ring(request: Request) -> KeyRing:
    key_ring: KeyRing = request.app.state.key_ring
    return key_ring


def _sender(request: Request) -> NotificationSender:
    sender: NotificationSender = request.app.state.notification_sender
    return sender


SessionmakerDep = Annotated[async_sessionmaker[AsyncSession], Depends(get_sessionmaker)]
SettingsDep = Annotated[Settings, Depends(get_app_settings)]
KeyRingDep = Annotated[KeyRing, Depends(_key_ring)]
SenderDep = Annotated[NotificationSender, Depends(_sender)]


def _set_refresh_cookie(response: Response, token: str) -> None:
    response.set_cookie(
        _REFRESH_COOKIE,
        token,
        path=_REFRESH_COOKIE_PATH,
        httponly=True,
        secure=True,
        samesite="lax",
        max_age=int(service.REFRESH_TOKEN_TTL.total_seconds()),
    )


def _access_token_out(access_token: str) -> TokenOut:
    return TokenOut(access_token=access_token, expires_in=int(ACCESS_TOKEN_TTL.total_seconds()))


@router.post("/otp/request", response_model=OtpRequestOut)
async def request_otp(
    body: OtpRequestIn,
    sessionmaker: SessionmakerDep,
    settings: SettingsDep,
    sender: SenderDep,
) -> OtpRequestOut:
    await service.request_otp(
        sessionmaker, phone=body.phone, device_id=body.device_id, settings=settings, sender=sender
    )
    return OtpRequestOut()


@router.post("/otp/verify", response_model=TokenOut)
async def verify_otp(
    body: OtpVerifyIn,
    response: Response,
    sessionmaker: SessionmakerDep,
    settings: SettingsDep,
    key_ring: KeyRingDep,
) -> TokenOut:
    access_token, refresh_token = await service.verify_otp(
        sessionmaker,
        phone=body.phone,
        code=body.code,
        device_id=body.device_id,
        platform=body.platform,
        settings=settings,
        key_ring=key_ring,
    )
    _set_refresh_cookie(response, refresh_token)
    return _access_token_out(access_token)


@router.post("/login", response_model=TotpPendingOut)
async def login(
    body: LoginIn,
    sessionmaker: SessionmakerDep,
    settings: SettingsDep,
    key_ring: KeyRingDep,
) -> TotpPendingOut:
    pending_token = await service.login(
        sessionmaker,
        identifier=body.identifier,
        password=body.password,
        settings=settings,
        key_ring=key_ring,
    )
    return TotpPendingOut(pending_token=pending_token)


@router.post("/totp/verify", response_model=TokenOut)
async def verify_totp(
    body: TotpVerifyIn,
    response: Response,
    sessionmaker: SessionmakerDep,
    settings: SettingsDep,
    key_ring: KeyRingDep,
    sender: SenderDep,
) -> TokenOut:
    access_token, refresh_token = await service.verify_totp(
        sessionmaker,
        pending_token=body.pending_token,
        code=body.code,
        device_id=body.device_id,
        platform=body.platform,
        settings=settings,
        key_ring=key_ring,
        sender=sender,
    )
    _set_refresh_cookie(response, refresh_token)
    return _access_token_out(access_token)


@router.post("/refresh", response_model=TokenOut)
async def refresh(
    response: Response,
    sessionmaker: SessionmakerDep,
    key_ring: KeyRingDep,
    refresh_token: Annotated[str | None, Cookie(alias=_REFRESH_COOKIE)] = None,
) -> TokenOut:
    if refresh_token is None:
        raise AppError("INVALID_REFRESH_TOKEN", status=401, detail="Missing refresh cookie")
    access_token, new_refresh_token = await service.refresh(
        sessionmaker, refresh_token=refresh_token, key_ring=key_ring
    )
    _set_refresh_cookie(response, new_refresh_token)
    return _access_token_out(access_token)


@router.post("/logout", response_model=LogoutOut)
async def logout(
    response: Response,
    sessionmaker: SessionmakerDep,
    refresh_token: Annotated[str | None, Cookie(alias=_REFRESH_COOKIE)] = None,
) -> LogoutOut:
    if refresh_token is not None:
        await service.logout(sessionmaker, refresh_token=refresh_token)
    response.delete_cookie(_REFRESH_COOKIE, path=_REFRESH_COOKIE_PATH)
    return LogoutOut()


@router.post("/switch-tenant", response_model=TokenOut)
async def switch_tenant(
    body: SwitchTenantIn,
    response: Response,
    sessionmaker: SessionmakerDep,
    key_ring: KeyRingDep,
    principal: Annotated[Principal, Depends(get_principal)],
) -> TokenOut:
    access_token, refresh_token = await service.switch_tenant(
        sessionmaker, principal=principal, target_tenant_id=body.tenant_id, key_ring=key_ring
    )
    _set_refresh_cookie(response, refresh_token)
    return _access_token_out(access_token)
