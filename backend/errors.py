from __future__ import annotations

import logging
from typing import Any, Dict, Optional

from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

logger = logging.getLogger(__name__)


def error_payload(code: str, message: str, details: Optional[Any] = None) -> Dict[str, Any]:
    payload: Dict[str, Any] = {
        "error": {
            "code": code,
            "message": message,
        }
    }
    if details is not None:
        payload["error"]["details"] = details
    return payload


def register_error_handlers(app: FastAPI) -> None:
    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError):
        return JSONResponse(
            status_code=422,
            content=error_payload(
                code="VALIDATION_ERROR",
                message="Request validation failed.",
                details=exc.errors(),
            ),
        )

    @app.exception_handler(HTTPException)
    async def http_exception_handler(request: Request, exc: HTTPException):
        detail = exc.detail
        if isinstance(detail, dict) and "error" in detail:
            content = detail
        elif isinstance(detail, dict) and {"code", "message"} <= set(detail.keys()):
            content = error_payload(detail["code"], detail["message"], detail.get("details"))
        else:
            content = error_payload("HTTP_ERROR", str(detail))
        return JSONResponse(status_code=exc.status_code, content=content)

    @app.exception_handler(Exception)
    async def unhandled_exception_handler(request: Request, exc: Exception):
        logger.exception("Unhandled API error on %s: %s", request.url.path, exc)
        return JSONResponse(
            status_code=500,
            content=error_payload("INTERNAL_ERROR", "Unexpected server error."),
        )
