"""Errors as RFC 9457 problem details (LLD 5.1)."""

import logging
from http import HTTPStatus
from typing import Any

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

PROBLEM_JSON = "application/problem+json"
ERROR_TYPE_BASE = "https://docs.kritvo.app/errors/"  # placeholder until the domain is registered

logger = logging.getLogger(__name__)


class AppError(Exception):
    """Raise from services; the handler turns it into a problem-details response."""

    def __init__(
        self,
        code: str,
        status: int = 400,
        title: str | None = None,
        detail: str | None = None,
        errors: list[dict[str, Any]] | None = None,
    ) -> None:
        super().__init__(code)
        self.code = code
        self.status = status
        self.title = title or HTTPStatus(status).phrase
        self.detail = detail
        self.errors = errors or []


def problem(
    status: int,
    code: str,
    title: str,
    detail: str | None = None,
    errors: list[dict[str, Any]] | None = None,
) -> JSONResponse:
    body: dict[str, Any] = {
        "type": ERROR_TYPE_BASE + code.lower().replace("_", "-"),
        "title": title,
        "status": status,
        "code": code,
    }
    if detail:
        body["detail"] = detail
    if errors:
        body["errors"] = errors
    return JSONResponse(body, status_code=status, media_type=PROBLEM_JSON)


async def _app_error(_: Request, exc: Exception) -> JSONResponse:
    if not isinstance(exc, AppError):
        raise exc
    return problem(exc.status, exc.code, exc.title, exc.detail, exc.errors)


async def _http_error(_: Request, exc: Exception) -> JSONResponse:
    if not isinstance(exc, StarletteHTTPException):
        raise exc
    phrase = HTTPStatus(exc.status_code).phrase
    code = phrase.upper().replace(" ", "_").replace("-", "_")
    detail = exc.detail if isinstance(exc.detail, str) and exc.detail != phrase else None
    return problem(exc.status_code, code, phrase, detail)


async def _validation_error(_: Request, exc: Exception) -> JSONResponse:
    if not isinstance(exc, RequestValidationError):
        raise exc
    errors = [
        {
            "field": ".".join(str(part) for part in err.get("loc", ())[1:]) or None,
            "code": str(err.get("type", "invalid")).upper(),
            "msg": err.get("msg"),
        }
        for err in exc.errors()
    ]
    return problem(422, "VALIDATION_ERROR", "Request validation failed", errors=errors)


async def _unhandled(_: Request, exc: Exception) -> JSONResponse:
    logger.exception("Unhandled error", exc_info=exc)
    return problem(500, "INTERNAL_ERROR", "Internal Server Error")


def install_error_handlers(app: FastAPI) -> None:
    app.add_exception_handler(AppError, _app_error)
    app.add_exception_handler(StarletteHTTPException, _http_error)
    app.add_exception_handler(RequestValidationError, _validation_error)
    app.add_exception_handler(Exception, _unhandled)
