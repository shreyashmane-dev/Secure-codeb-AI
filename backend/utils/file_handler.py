from __future__ import annotations

import logging
import shutil
import tempfile
import zipfile
from pathlib import Path
from typing import Iterable, List, Sequence
from uuid import uuid4

from ..config import get_settings

logger = logging.getLogger(__name__)


def create_temp_workspace(prefix: str) -> Path:
    settings = get_settings()
    try:
        base = settings.temp_dir
        base.mkdir(parents=True, exist_ok=True)
        workspace = base / f"{prefix}_{uuid4().hex[:10]}"
        workspace.mkdir(parents=True, exist_ok=False)
        return workspace
    except PermissionError:
        logger.warning("Permission denied for configured temp dir %s. Falling back to system temp.", settings.temp_dir)
        fallback = Path(tempfile.gettempdir()) / f"{prefix}_{uuid4().hex[:10]}"
        fallback.mkdir(parents=True, exist_ok=False)
        return fallback


def cleanup_path(path: Path) -> None:
    try:
        if path.exists():
            shutil.rmtree(path, ignore_errors=True)
    except OSError as exc:
        logger.warning("Failed to cleanup temp path %s: %s", path, exc)


def validate_zip_file(filename: str, size_bytes: int) -> None:
    settings = get_settings()
    if not filename.lower().endswith(".zip"):
        raise ValueError("Only .zip uploads are supported.")
    max_size_bytes = settings.max_upload_size_mb * 1024 * 1024
    if size_bytes > max_size_bytes:
        raise ValueError(f"ZIP file exceeds {settings.max_upload_size_mb} MB limit.")


def save_upload_to_path(payload: bytes, destination: Path) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_bytes(payload)


def safe_extract_zip(zip_path: Path, destination: Path) -> None:
    destination.mkdir(parents=True, exist_ok=True)
    try:
        with zipfile.ZipFile(zip_path, "r") as archive:
            total_size = sum(member.file_size for member in archive.infolist())
            settings = get_settings()
            max_total_size = settings.max_upload_size_mb * 1024 * 1024
            if total_size > max_total_size:
                raise ValueError("Extracted archive size is too large.")

            for member in archive.infolist():
                member_name = member.filename.replace("\\", "/")
                if member_name.endswith("/"):
                    continue
                extracted_path = (destination / member_name).resolve()
                if not str(extracted_path).startswith(str(destination.resolve())):
                    raise ValueError("Unsafe archive path detected.")
                if member.file_size > settings.max_file_read_kb * 1024 * 8:
                    logger.info("Skipping oversized archive member: %s", member.filename)
                    continue
                archive.extract(member, destination)
    except zipfile.BadZipFile as exc:
        raise ValueError("Uploaded file is not a valid ZIP archive.") from exc


def _normalize_extensions(extensions: Sequence[str]) -> List[str]:
    normalized: List[str] = []
    for ext in extensions:
        if not ext:
            continue
        formatted = ext.lower().strip()
        if not formatted.startswith("."):
            formatted = f".{formatted}"
        normalized.append(formatted)
    return sorted(set(normalized))


def iter_source_files(
    root_dir: Path,
    include_extensions: Sequence[str] | None = None,
    exclude_paths: Sequence[str] | None = None,
    max_files: int | None = None,
) -> List[Path]:
    settings = get_settings()
    include = _normalize_extensions(include_extensions or settings.allowed_scan_extensions)
    excludes = [token.lower().strip() for token in (exclude_paths or []) if token.strip()]
    files: List[Path] = []
    max_count = max_files or settings.max_scan_files

    for file_path in root_dir.rglob("*"):
        if len(files) >= max_count:
            break
        if not file_path.is_file():
            continue
        if file_path.suffix.lower() not in include:
            continue
        relative = str(file_path.relative_to(root_dir)).replace("\\", "/").lower()
        if any(token in relative for token in excludes):
            continue
        files.append(file_path)
    return files


def read_text_file(path: Path) -> str:
    settings = get_settings()
    max_bytes = settings.max_file_read_kb * 1024
    with path.open("rb") as handle:
        data = handle.read(max_bytes + 1)
    if len(data) > max_bytes:
        data = data[:max_bytes]
    return data.decode("utf-8", errors="ignore")


def count_lines(content: str) -> int:
    return max(content.count("\n") + 1, 1)


def collect_file_map(paths: Iterable[Path], root_dir: Path) -> dict[str, str]:
    mapping: dict[str, str] = {}
    for file_path in paths:
        rel = str(file_path.relative_to(root_dir)).replace("\\", "/")
        mapping[rel] = read_text_file(file_path)
    return mapping
