from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, Field


Severity = Literal["critical", "high", "medium", "low"]
Category = Literal["security", "reliability", "quality", "maintainability", "dependency"]
AiMode = Literal["basic", "advanced"]


class Issue(BaseModel):
    issue_id: str
    issue_type: str
    category: Category
    severity: Severity
    file_path: str
    line: int = 1
    message: str
    code_snippet: str = ""
    risk_explanation: str = ""
    why_dangerous: str = ""
    real_world_attack_scenario: str = ""
    why_this_is_dangerous: str = ""
    secure_fix_explanation: str = ""
    refactored_code: str = ""
    best_practice_reference: str = ""
    performance_impact: str = ""
    confidence_score: str = "75%"
    before_code: str = ""
    after_code: str = ""
    improvement_reasoning: str = ""
    best_practice: str = ""
    suggested_code: str = ""
    refactored_example: str = ""
    confidence: float = Field(default=75.0, ge=0.0, le=100.0)
    tags: List[str] = Field(default_factory=list)


class FileMetrics(BaseModel):
    file_path: str
    language: str
    lines: int
    issue_count: int
    critical_count: int = 0
    high_count: int = 0
    medium_count: int = 0
    low_count: int = 0
    cyclomatic_complexity: float = 0.0
    maintainability_index: float = 0.0
    duplication_blocks: int = 0
    risk_score: float = 0.0


class ScoreBundle(BaseModel):
    security_score: int
    trust_score: int
    reliability_score: int
    quality_score: int
    improvement_potential: int


class ScanTotals(BaseModel):
    total_files_scanned: int
    total_lines_analyzed: int
    total_issues_found: int
    critical: int
    high: int
    medium: int
    low: int


class ScanResult(BaseModel):
    scan_id: str
    source_type: str
    source_label: str
    started_at: datetime
    finished_at: datetime
    duration_seconds: float
    totals: ScanTotals
    scores: ScoreBundle
    severity_distribution: Dict[str, int]
    score_radar: Dict[str, int]
    file_risk_heatmap: List[Dict[str, float | str | int]]
    recommendations: List[str] = Field(default_factory=list)
    issues: List[Issue]
    files: List[FileMetrics]
    metadata: Dict[str, Any] = Field(default_factory=dict)


class ScanStatus(BaseModel):
    scan_id: str
    owner_uid: Optional[str] = None
    status: Literal["queued", "running", "completed", "failed"]
    progress: int = Field(default=0, ge=0, le=100)
    message: str = "Queued"
    source_type: str
    source_label: str
    created_at: datetime
    updated_at: datetime
    error: Optional[Any] = None
    result: Optional[ScanResult] = None


class GitHubScanRequest(BaseModel):
    repo_url: str
    branch: Optional[str] = None
    ai_mode: AiMode = "basic"
    include_extensions: List[str] = Field(default_factory=list)
    exclude_paths: List[str] = Field(default_factory=list)
    max_files: int = Field(default=1200, ge=1, le=5000)


class UploadScanOptions(BaseModel):
    ai_mode: AiMode = "basic"
    include_extensions: List[str] = Field(default_factory=list)
    exclude_paths: List[str] = Field(default_factory=list)
    max_files: int = Field(default=1200, ge=1, le=5000)


class ReportRequest(BaseModel):
    scan_id: str
    report_type: Literal["pdf", "json"] = "pdf"
