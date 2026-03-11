from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse, JSONResponse
from starlette.background import BackgroundTask

from ..errors import error_payload
from ..models import ReportRequest
from ..runtime import scan_store
from ..security.dependencies import get_current_user
from ..security.firebase_auth import AuthenticatedUser
from ..utils.file_handler import cleanup_path, create_temp_workspace
from ..utils.report_generator import generate_pdf_report

router = APIRouter(tags=["report"])


@router.post("/generate/report")
async def generate_report(payload: ReportRequest, user: AuthenticatedUser = Depends(get_current_user)):
    result = scan_store.get_result(payload.scan_id, owner_uid=user.uid)
    if not result:
        raise HTTPException(
            status_code=404,
            detail=error_payload(code="SCAN_RESULT_NOT_FOUND", message="Scan result not found."),
        )

    if payload.report_type == "json":
        return JSONResponse(content=result)

    workspace = create_temp_workspace(f"report_{payload.scan_id[:8]}")
    output_path = workspace / f"SecureCodeAI-Report-{payload.scan_id[:8]}.pdf"
    generate_pdf_report(result, output_path)
    return FileResponse(
        path=output_path,
        media_type="application/pdf",
        filename=output_path.name,
        background=BackgroundTask(lambda: cleanup_path(workspace)),
    )
