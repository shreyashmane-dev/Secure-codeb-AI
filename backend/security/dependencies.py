from __future__ import annotations

from fastapi import HTTPException, Request

from .firebase_auth import AuthenticatedUser


def get_current_user(request: Request) -> AuthenticatedUser:
    user = getattr(request.state, "user", None)
    if not user:
        raise HTTPException(
            status_code=401,
            detail={
                "code": "AUTH_REQUIRED",
                "message": "Authentication required.",
            },
        )
    return user
