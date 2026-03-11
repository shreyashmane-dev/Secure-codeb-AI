from __future__ import annotations

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query

from ..config import get_settings
from ..errors import error_payload
from ..models import GitHubScanRequest
from ..runtime import scan_rate_limiter, scan_store
from ..security.dependencies import get_current_user
from ..security.firebase_auth import AuthenticatedUser
from ..services.scan_jobs import run_github_scan_job
from ..utils.git_handler import GitCloneError, validate_github_url

router = APIRouter(tags=["scan"])


@router.post("/scan/github")
async def scan_github_repository(
    payload: GitHubScanRequest,
    background_tasks: BackgroundTasks,
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

    max_files = min(payload.max_files, settings.max_scan_files)
    try:
        validate_github_url(payload.repo_url)
    except GitCloneError as exc:
        raise HTTPException(
            status_code=400,
            detail=error_payload(code=exc.code, message=str(exc)),
        ) from exc

    scan_id = scan_store.create_scan(source_type="github", source_label=payload.repo_url, owner_uid=user.uid)
    background_tasks.add_task(
        run_github_scan_job,
        scan_id,
        payload.repo_url,
        payload.branch,
        payload.ai_mode,
        payload.include_extensions,
        payload.exclude_paths,
        max_files,
        settings.scan_timeout_sec,
    )
    return {
        "scan_id": scan_id,
        "status": "queued",
        "message": "GitHub scan queued.",
        "ai_mode": payload.ai_mode,
    }


@router.get("/scan/status")
async def scan_status(
    scan_id: str = Query(..., min_length=6),
    user: AuthenticatedUser = Depends(get_current_user),
):
    status = scan_store.get_status(scan_id, owner_uid=user.uid)
    if not status:
        raise HTTPException(
            status_code=404,
            detail=error_payload(code="SCAN_NOT_FOUND", message="Scan not found."),
        )
    return status


@router.get("/scan/history")
async def scan_history(
    limit: int = Query(default=20, ge=1, le=100),
    user: AuthenticatedUser = Depends(get_current_user),
):
    return {"items": scan_store.list_history(limit=limit, owner_uid=user.uid)}


@router.get("/scan/analytics")
async def scan_analytics(user: AuthenticatedUser = Depends(get_current_user)):
    return scan_store.analytics(owner_uid=user.uid)


@router.get("/scan/export/{scan_id}")
async def export_scan_json(scan_id: str, user: AuthenticatedUser = Depends(get_current_user)):
    result = scan_store.get_result(scan_id, owner_uid=user.uid)
    if not result:
        raise HTTPException(
            status_code=404,
            detail=error_payload(code="SCAN_RESULT_NOT_FOUND", message="Scan result not found."),
        )
    return result


@router.get("/scan/compare")
async def compare_scans(
    scan_id_a: str = Query(...),
    scan_id_b: str = Query(...),
    user: AuthenticatedUser = Depends(get_current_user),
):
    try:
        return scan_store.compare(scan_id_a, scan_id_b, owner_uid=user.uid)
    except KeyError as exc:
        raise HTTPException(
            status_code=404,
            detail=error_payload(code="SCAN_COMPARE_NOT_FOUND", message=str(exc)),
        ) from exc
