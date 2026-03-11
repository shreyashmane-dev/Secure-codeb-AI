from __future__ import annotations

import threading
import time
from collections import defaultdict, deque
from dataclasses import dataclass
from typing import Deque, Dict


@dataclass
class RateLimitDecision:
    allowed: bool
    retry_after_sec: int = 0


class SlidingWindowRateLimiter:
    def __init__(self, max_requests: int, window_sec: int) -> None:
        self.max_requests = max(1, max_requests)
        self.window_sec = max(1, window_sec)
        self._events: Dict[str, Deque[float]] = defaultdict(deque)
        self._lock = threading.RLock()

    def check(self, key: str) -> RateLimitDecision:
        now = time.time()
        lower_bound = now - self.window_sec
        with self._lock:
            queue = self._events[key]
            while queue and queue[0] < lower_bound:
                queue.popleft()

            if len(queue) >= self.max_requests:
                retry_after = int(max(1, self.window_sec - (now - queue[0])))
                return RateLimitDecision(allowed=False, retry_after_sec=retry_after)

            queue.append(now)
            return RateLimitDecision(allowed=True)
