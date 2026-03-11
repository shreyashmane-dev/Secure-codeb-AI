from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import List, Optional

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


BASE_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = BASE_DIR.parent


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_name: str = "SecureCode AI - Intelligent Code Risk & Quality Analyzer"
    debug: bool = False
    cors_origins: List[str] = Field(
        default_factory=lambda: [
            "http://localhost:5173",
            "http://127.0.0.1:5173",
        ]
    )
    cors_allow_methods: List[str] = Field(default_factory=lambda: ["GET", "POST"])
    cors_allow_headers: List[str] = Field(default_factory=lambda: ["Authorization", "Content-Type"])

    max_upload_size_mb: int = 25
    max_scan_files: int = 2500
    max_file_read_kb: int = 512
    scan_timeout_sec: int = 360

    scan_rate_limit_requests: int = 6
    scan_rate_limit_window_sec: int = 60

    firebase_project_id: Optional[str] = None
    firebase_service_account_path: Optional[Path] = None
    firebase_service_account_json: Optional[str] = None

    openai_api_key: Optional[str] = None
    openai_model: str = "gpt-4o-mini"
    openai_timeout_sec: int = 45
    advanced_ai_max_issues: int = 20
    allowed_scan_extensions: List[str] = Field(
        default_factory=lambda: [
            ".py",
            ".js",
            ".jsx",
            ".ts",
            ".tsx",
            ".java",
            ".go",
            ".rb",
            ".php",
            ".cs",
            ".cpp",
            ".c",
            ".json",
            ".yaml",
            ".yml",
            ".toml",
            ".ini",
            ".env",
            ".sql",
        ]
    )

    storage_dir: Path = PROJECT_ROOT / "backend" / "storage"
    temp_dir: Path = PROJECT_ROOT / "backend" / "storage" / "runtime_tmp"
    history_file: Path = PROJECT_ROOT / "backend" / "storage" / "scan_history.json"
    log_file: Path = PROJECT_ROOT / "backend" / "storage" / "scanner.log"

    github_clone_timeout_sec: int = 120

    @field_validator("allowed_scan_extensions", mode="before")
    @classmethod
    def normalize_extensions(cls, value: List[str]) -> List[str]:
        normalized: List[str] = []
        for item in value:
            if not item:
                continue
            ext = item.strip().lower()
            if not ext.startswith("."):
                ext = f".{ext}"
            normalized.append(ext)
        return sorted(set(normalized))

    @field_validator(
        "storage_dir",
        "temp_dir",
        "history_file",
        "log_file",
        "firebase_service_account_path",
        mode="before",
    )
    @classmethod
    def coerce_path(cls, value):
        if value is None or value == "":
            return None
        return Path(value)


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    settings = Settings()
    settings.storage_dir.mkdir(parents=True, exist_ok=True)
    settings.temp_dir.mkdir(parents=True, exist_ok=True)
    settings.history_file.parent.mkdir(parents=True, exist_ok=True)
    settings.log_file.parent.mkdir(parents=True, exist_ok=True)
    if not settings.history_file.exists():
        settings.history_file.write_text("[]", encoding="utf-8")
    return settings
