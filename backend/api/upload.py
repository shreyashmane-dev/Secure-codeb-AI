from __future__ import annotations

import json
from pathlib import Path
from typing import List

from fastapi import APIRouter, BackgroundTasks, Depends, File, Form, HTTPException, UploadFile

from ..config import get_settings
from ..errors import error_payload
from ..runtime import scan_rate_limiter, scan_store
from ..security.dependencies import get_current_user
from ..security.firebase_auth import AuthenticatedUser
from ..services.scan_jobs import run_upload_scan_job
from ..utils.file_handler import validate_zip_file

router = APIRouter(tags=["upload"])


def _parse_list_field(value: str | None) -> List[str]:
    if not value:
        return []
    stripped = value.strip()
    if not stripped:
        return []
    if stripped.startswith("["):
        try:
            payload = json.loads(stripped)
            if isinstance(payload, list):
                return [str(item).strip() for item in payload if str(item).strip()]
        except json.JSONDecodeError:
            pass
    return [token.strip() for token in stripped.split(",") if token.strip()]


@router.post("/scan/upload")
async def scan_upload_archive(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    ai_mode: str = Form(default="basic"),
    include_extensions: str = Form(default=""),
    exclude_paths: str = Form(default=""),
    max_files: int = Form(default=1200),
    user: AuthenticatedUser = Depends(get_current_user),
):
    settings = get_settings()
    decision = scan_rate_limiter.check(f"{user.uid}:scan_submit")
    if not decision.allowed:
        raise HTTPException(
            status_code=429,
            detail=error_payload(
                code="RATE_LIMITED",
                message="Scan rate limit exceeded. Please retry later.",
                details={"retry_after_sec": decision.retry_after_sec},
            ),
        )

    ai_mode = (ai_mode or "basic").lower()
    if ai_mode not in {"basic", "advanced"}:
        raise HTTPException(
            status_code=400,
            detail=error_payload(
                code="INVALID_AI_MODE",
                message="ai_mode must be either 'basic' or 'advanced'.",
            ),
        )

    content = await file.read()
    filename = file.filename or "source.zip"

    try:
        validate_zip_file(filename, len(content))
    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail=error_payload(code="ZIP_VALIDATION_ERROR", message=str(exc)),
        ) from exc

    max_files = max(1, min(max_files, settings.max_scan_files))
    scan_id = scan_store.create_scan(source_type="upload", source_label=filename, owner_uid=user.uid)

    queue_dir = settings.temp_dir / "queued_uploads"
    queue_dir.mkdir(parents=True, exist_ok=True)
    zip_path = Path(queue_dir / f"{scan_id}.zip")
    zip_path.write_bytes(content)

    background_tasks.add_task(
        run_upload_scan_job,
        scan_id,
        zip_path,
        ai_mode,
        _parse_list_field(include_extensions),
        _parse_list_field(exclude_paths),
        max_files,
        settings.scan_timeout_sec,
    )
    return {
        "scan_id": scan_id,
        "status": "queued",
        "message": "Upload scan queued.",
        "ai_mode": ai_mode,
    }
