from __future__ import annotations

from .config import get_settings
from .security.rate_limiter import SlidingWindowRateLimiter
from .storage.scan_store import ScanStore


settings = get_settings()
scan_store = ScanStore(settings.history_file)
scan_rate_limiter = SlidingWindowRateLimiter(
    max_requests=settings.scan_rate_limit_requests,
    window_sec=settings.scan_rate_limit_window_sec,
)
