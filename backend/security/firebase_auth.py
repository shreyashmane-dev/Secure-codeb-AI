from __future__ import annotations

import json
import logging
import threading
from dataclasses import dataclass
from typing import Any, Dict, Optional

import firebase_admin
from firebase_admin import auth, credentials
from firebase_admin.exceptions import FirebaseError

from ..config import get_settings

logger = logging.getLogger(__name__)

_INIT_LOCK = threading.RLock()
_IS_INITIALIZED = False


class AuthVerificationError(Exception):
    def __init__(self, message: str, code: str = "AUTH_INVALID_TOKEN") -> None:
        super().__init__(message)
        self.code = code


@dataclass
class AuthenticatedUser:
    uid: str
    email: Optional[str]
    name: Optional[str]
    claims: Dict[str, Any]


def initialize_firebase_admin() -> bool:
    global _IS_INITIALIZED
    if _IS_INITIALIZED:
        return True

    settings = get_settings()
    with _INIT_LOCK:
        if _IS_INITIALIZED:
            return True
        try:
            firebase_admin.get_app()
            _IS_INITIALIZED = True
            return True
        except ValueError:
            pass

        cred = None
        options: Dict[str, Any] = {}

        if settings.firebase_project_id:
            options["projectId"] = settings.firebase_project_id

        if settings.firebase_service_account_json:
            try:
                payload = json.loads(settings.firebase_service_account_json)
                cred = credentials.Certificate(payload)
            except json.JSONDecodeError as exc:
                logger.error("Invalid FIREBASE_SERVICE_ACCOUNT_JSON: %s", exc)
                return False
        elif settings.firebase_service_account_path and settings.firebase_service_account_path.exists():
            cred = credentials.Certificate(str(settings.firebase_service_account_path))
        else:
            logger.warning(
                "Firebase Admin not initialized. Missing service account config. "
                "Set FIREBASE_SERVICE_ACCOUNT_PATH or FIREBASE_SERVICE_ACCOUNT_JSON."
            )
            return False

        try:
            firebase_admin.initialize_app(cred, options=options or None)
            _IS_INITIALIZED = True
            logger.info("Firebase Admin SDK initialized successfully.")
            return True
        except Exception as exc:
            logger.exception("Failed to initialize Firebase Admin SDK: %s", exc)
            return False


def verify_bearer_token(authorization_header: Optional[str]) -> AuthenticatedUser:
    if not authorization_header:
        raise AuthVerificationError("Missing Authorization header.", code="AUTH_MISSING_TOKEN")
    if not authorization_header.lower().startswith("bearer "):
        raise AuthVerificationError("Authorization header must start with 'Bearer '.", code="AUTH_INVALID_SCHEME")

    token = authorization_header.split(" ", 1)[1].strip()
    if not token:
        raise AuthVerificationError("Bearer token is empty.", code="AUTH_EMPTY_TOKEN")

    if not initialize_firebase_admin():
        raise AuthVerificationError(
            "Authentication service is not configured on the server.",
            code="AUTH_SERVICE_UNAVAILABLE",
        )

    try:
        decoded = auth.verify_id_token(token, check_revoked=True)
    except auth.ExpiredIdTokenError as exc:
        raise AuthVerificationError("Token expired.", code="AUTH_TOKEN_EXPIRED") from exc
    except auth.RevokedIdTokenError as exc:
        raise AuthVerificationError("Token has been revoked.", code="AUTH_TOKEN_REVOKED") from exc
    except auth.InvalidIdTokenError as exc:
        raise AuthVerificationError("Invalid ID token.", code="AUTH_INVALID_TOKEN") from exc
    except FirebaseError as exc:
        raise AuthVerificationError("Token verification failed.", code="AUTH_VERIFICATION_FAILED") from exc

    return AuthenticatedUser(
        uid=str(decoded.get("uid", "")),
        email=decoded.get("email"),
        name=decoded.get("name"),
        claims=decoded,
    )
