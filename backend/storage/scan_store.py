from __future__ import annotations

import json
import threading
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from pydantic import ValidationError

from ..models import ScanResult, ScanStatus


def utc_now() -> datetime:
    return datetime.now(tz=timezone.utc)


class ScanStore:
    def __init__(self, history_file: Path) -> None:
        self._history_file = history_file
        self._lock = threading.RLock()
        self._scans: Dict[str, ScanStatus] = {}
        self._history: List[Dict[str, Any]] = self._load_history()

    def _load_history(self) -> List[Dict[str, Any]]:
        if not self._history_file.exists():
            return []
        try:
            raw = self._history_file.read_text(encoding="utf-8")
            data = json.loads(raw)
            if isinstance(data, list):
                return data
        except (OSError, json.JSONDecodeError):
            pass
        return []

    def _save_history(self) -> None:
        self._history_file.parent.mkdir(parents=True, exist_ok=True)
        self._history_file.write_text(json.dumps(self._history, indent=2), encoding="utf-8")

    def create_scan(self, source_type: str, source_label: str, owner_uid: Optional[str] = None) -> str:
        scan_id = uuid.uuid4().hex
        now = utc_now()
        status = ScanStatus(
            scan_id=scan_id,
            owner_uid=owner_uid,
            status="queued",
            progress=0,
            message="Scan queued",
            source_type=source_type,
            source_label=source_label,
            created_at=now,
            updated_at=now,
        )
        with self._lock:
            self._scans[scan_id] = status
        return scan_id

    def set_running(self, scan_id: str, message: str = "Scan started") -> None:
        with self._lock:
            status = self._require(scan_id)
            status.status = "running"
            status.message = message
            status.updated_at = utc_now()
            self._scans[scan_id] = status

    def update_progress(self, scan_id: str, progress: int, message: Optional[str] = None) -> None:
        clamped = max(0, min(100, progress))
        with self._lock:
            status = self._require(scan_id)
            if status.status in {"completed", "failed"}:
                return
            status.status = "running"
            status.progress = clamped
            status.updated_at = utc_now()
            if message:
                status.message = message
            self._scans[scan_id] = status

    def set_result(self, scan_id: str, result_payload: Dict[str, Any]) -> None:
        with self._lock:
            status = self._require(scan_id)
            try:
                result = ScanResult.model_validate(result_payload)
            except ValidationError:
                raise
            status.status = "completed"
            status.progress = 100
            status.message = "Scan completed"
            status.result = result
            status.updated_at = utc_now()
            self._scans[scan_id] = status
            history_item = {
                "scan_id": scan_id,
                "owner_uid": status.owner_uid,
                "source_type": status.source_type,
                "source_label": status.source_label,
                "created_at": status.created_at.isoformat(),
                "updated_at": status.updated_at.isoformat(),
                "totals": result.totals.model_dump(),
                "scores": result.scores.model_dump(),
            }
            self._history.append(history_item)
            self._history = self._history[-100:]
            self._save_history()

    def set_failed(self, scan_id: str, error: Any) -> None:
        with self._lock:
            status = self._require(scan_id)
            status.status = "failed"
            if isinstance(error, str):
                status.error = error[:1200]
            else:
                status.error = error
            status.message = "Scan failed"
            status.updated_at = utc_now()
            self._scans[scan_id] = status

    def get_status(self, scan_id: str, owner_uid: Optional[str] = None) -> Optional[Dict[str, Any]]:
        with self._lock:
            status = self._scans.get(scan_id)
            if not status:
                return None
            if owner_uid and status.owner_uid and status.owner_uid != owner_uid:
                return None
            return status.model_dump(mode="json")

    def get_result(self, scan_id: str, owner_uid: Optional[str] = None) -> Optional[Dict[str, Any]]:
        with self._lock:
            status = self._scans.get(scan_id)
            if not status or not status.result:
                return None
            if owner_uid and status.owner_uid and status.owner_uid != owner_uid:
                return None
            return status.result.model_dump(mode="json")

    def list_history(self, limit: int = 20, owner_uid: Optional[str] = None) -> List[Dict[str, Any]]:
        with self._lock:
            items = self._history
            if owner_uid:
                items = [item for item in items if item.get("owner_uid") == owner_uid]
            return list(reversed(items[-limit:]))

    def analytics(self, owner_uid: Optional[str] = None) -> Dict[str, Any]:
        with self._lock:
            items = self._history
            if owner_uid:
                items = [item for item in items if item.get("owner_uid") == owner_uid]
            if not items:
                return {
                    "total_scans": 0,
                    "avg_security_score": 0,
                    "avg_reliability_score": 0,
                    "avg_quality_score": 0,
                    "avg_trust_score": 0,
                    "last_scan_at": None,
                }
            total = len(items)
            avg = lambda key: round(sum(item["scores"][key] for item in items) / total, 2)
            return {
                "total_scans": total,
                "avg_security_score": avg("security_score"),
                "avg_reliability_score": avg("reliability_score"),
                "avg_quality_score": avg("quality_score"),
                "avg_trust_score": avg("trust_score"),
                "last_scan_at": items[-1]["updated_at"],
            }

    def compare(self, scan_id_a: str, scan_id_b: str, owner_uid: Optional[str] = None) -> Dict[str, Any]:
        with self._lock:
            item_a = self._find_history(scan_id_a, owner_uid=owner_uid)
            item_b = self._find_history(scan_id_b, owner_uid=owner_uid)
            if not item_a or not item_b:
                raise KeyError("Both scan IDs must exist in scan history.")
            scores_a = item_a["scores"]
            scores_b = item_b["scores"]
            diff = {
                key: round(scores_b[key] - scores_a[key], 2)
                for key in scores_a.keys()
                if key in scores_b
            }
            return {
                "scan_a": item_a,
                "scan_b": item_b,
                "score_difference": diff,
            }

    def _find_history(self, scan_id: str, owner_uid: Optional[str] = None) -> Optional[Dict[str, Any]]:
        for item in self._history:
            if item.get("scan_id") == scan_id:
                if owner_uid and item.get("owner_uid") != owner_uid:
                    continue
                return item
        return None

    def _require(self, scan_id: str) -> ScanStatus:
        status = self._scans.get(scan_id)
        if not status:
            raise KeyError(f"Scan '{scan_id}' not found.")
        return status
