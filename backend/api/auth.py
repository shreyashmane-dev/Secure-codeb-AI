from __future__ import annotations

from fastapi import APIRouter, Depends

from ..security.dependencies import get_current_user
from ..security.firebase_auth import AuthenticatedUser

router = APIRouter(tags=["auth"])


@router.get("/auth/me")
async def auth_me(user: AuthenticatedUser = Depends(get_current_user)):
    return {
        "uid": user.uid,
        "email": user.email,
        "name": user.name,
    }
