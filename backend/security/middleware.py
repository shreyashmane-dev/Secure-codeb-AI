from __future__ import annotations

from typing import Iterable

from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from .firebase_auth import AuthVerificationError, verify_bearer_token
from ..config import get_settings


def _is_public_path(path: str, public_prefixes: Iterable[str]) -> bool:
    return any(path == prefix or path.startswith(prefix) for prefix in public_prefixes)


class FirebaseAuthMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, public_prefixes: Iterable[str] | None = None) -> None:
        super().__init__(app)
        self.public_prefixes = list(
            public_prefixes
            or [
                "/health",
                "/openapi.json",
                "/docs",
                "/redoc",
            ]
        )

    async def dispatch(self, request: Request, call_next) -> Response:
        path = request.url.path
        if request.method == "OPTIONS":
            return await call_next(request)
        if _is_public_path(path, self.public_prefixes):
            return await call_next(request)

        try:
            user = verify_bearer_token(request.headers.get("Authorization"))
            request.state.user = user
        except AuthVerificationError as exc:
            return JSONResponse(
                status_code=401,
                content={
                    "error": {
                        "code": exc.code,
                        "message": str(exc),
                        "path": path,
                    }
                },
            )

        return await call_next(request)
