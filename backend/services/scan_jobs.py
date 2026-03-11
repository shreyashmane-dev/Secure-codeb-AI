from __future__ import annotations

import logging
from pathlib import Path
from typing import List, Optional

from ..engine.analyzer import analyze_codebase
from ..runtime import scan_store
from ..utils.file_handler import cleanup_path, create_temp_workspace, safe_extract_zip
from ..utils.git_handler import GitCloneError, clone_repository

logger = logging.getLogger(__name__)


def _progress(scan_id: str, progress: int, message: str) -> None:
    scan_store.update_progress(scan_id, progress, message)


def run_upload_scan_job(
    scan_id: str,
    zip_path: Path,
    ai_mode: str = "basic",
    include_extensions: Optional[List[str]] = None,
    exclude_paths: Optional[List[str]] = None,
    max_files: int = 1200,
    timeout_sec: int = 360,
) -> None:
    workspace = create_temp_workspace(f"upload_{scan_id[:8]}")
    source_dir = workspace

    try:
        scan_store.set_running(scan_id, "Preparing uploaded archive")
        _progress(scan_id, 6, "Extracting archive")
        safe_extract_zip(zip_path, source_dir)
        _progress(scan_id, 10, "Archive extracted")

        status = scan_store.get_status(scan_id) or {}
        source_label = status.get("source_label", "Uploaded ZIP")

        result = analyze_codebase(
            scan_id=scan_id,
            source_type="upload",
            source_label=source_label,
            source_dir=source_dir,
            ai_mode=ai_mode,
            include_extensions=include_extensions,
            exclude_paths=exclude_paths,
            max_files=max_files,
            timeout_sec=timeout_sec,
            progress_callback=lambda p, m: _progress(scan_id, p, m),
        )
        scan_store.set_result(scan_id, result)
    except Exception as exc:
        logger.exception("Upload scan failed for %s", scan_id)
        code = "SCAN_FAILED"
        if isinstance(exc, TimeoutError):
            code = "SCAN_TIMEOUT"
        elif isinstance(exc, ValueError):
            code = "UPLOAD_VALIDATION_ERROR"
        scan_store.set_failed(scan_id, {"code": code, "message": str(exc)})
    finally:
        try:
            zip_path.unlink(missing_ok=True)
        except OSError:
            logger.warning("Could not remove temp zip file: %s", zip_path)
        cleanup_path(workspace)


def run_github_scan_job(
    scan_id: str,
    repo_url: str,
    branch: Optional[str] = None,
    ai_mode: str = "basic",
    include_extensions: Optional[List[str]] = None,
    exclude_paths: Optional[List[str]] = None,
    max_files: int = 1200,
    timeout_sec: int = 360,
) -> None:
    workspace = create_temp_workspace(f"github_{scan_id[:8]}")

    try:
        scan_store.set_running(scan_id, "Cloning GitHub repository")
        _progress(scan_id, 5, "Cloning repository")
        repo_path = clone_repository(repo_url, workspace, branch=branch)
        _progress(scan_id, 12, "Repository cloned")

        status = scan_store.get_status(scan_id) or {}
        source_label = status.get("source_label", repo_url)

        result = analyze_codebase(
            scan_id=scan_id,
            source_type="github",
            source_label=source_label,
            source_dir=repo_path,
            ai_mode=ai_mode,
            include_extensions=include_extensions,
            exclude_paths=exclude_paths,
            max_files=max_files,
            timeout_sec=timeout_sec,
            progress_callback=lambda p, m: _progress(scan_id, p, m),
        )
        scan_store.set_result(scan_id, result)
    except Exception as exc:
        logger.exception("GitHub scan failed for %s", scan_id)
        code = "SCAN_FAILED"
        if isinstance(exc, GitCloneError):
            code = exc.code
        elif isinstance(exc, TimeoutError):
            code = "SCAN_TIMEOUT"
        scan_store.set_failed(scan_id, {"code": code, "message": str(exc)})
    finally:
        cleanup_path(workspace)
