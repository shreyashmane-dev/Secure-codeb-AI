from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .api.auth import router as auth_router
from .api.report import router as report_router
from .api.scan import router as scan_router
from .api.upload import router as upload_router
from .config import get_settings
from .errors import register_error_handlers
from .logging_config import configure_logging
from .security.middleware import FirebaseAuthMiddleware

settings = get_settings()
configure_logging()

app = FastAPI(title=settings.app_name, debug=settings.debug)
app.add_middleware(FirebaseAuthMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=settings.cors_allow_methods,
    allow_headers=settings.cors_allow_headers,
)
register_error_handlers(app)

app.include_router(scan_router)
app.include_router(upload_router)
app.include_router(report_router)
app.include_router(auth_router)


@app.get("/health")
def health() -> dict:
    return {"status": "ok", "service": "securecode-ai-backend"}
