"""Per-user rate limiter (pure memory, sliding window)."""

import time
import math
from collections import defaultdict


class PerUserRateLimiter:
    """Sliding-window rate limiter per user. Returns headers-raw data."""

    def __init__(self, default_limit: int = 1000, window_seconds: int = 3600):
        self.default_limit = default_limit
        self.window_seconds = window_seconds
        # {user_id: [(timestamp, ...)]} sorted by insert order
        self._buckets: dict[str, list[float]] = defaultdict(list)

    def check_rate_limit(self, user_id: str):
        """
        Returns (allowed, remaining, reset_time).
        - allowed: bool
        - remaining: int (>=0)
        - reset_time: int (unix timestamp, when the window resets)
        """
        now = time.time()
        window_start = now - self.window_seconds

        bucket = self._buckets[user_id]

        # --- sliding window: purge expired timestamps ---
        # binary search for first valid index
        if bucket:
            lo, hi = 0, len(bucket)
            while lo < hi:
                mid = (lo + hi) // 2
                if bucket[mid] < window_start:
                    lo = mid + 1
                else:
                    hi = mid
            if lo > 0:
                del bucket[:lo]

        limit = self.default_limit
        current_count = len(bucket)

        if current_count >= limit:
            # Find reset time: oldest timestamp + window_seconds
            oldest = bucket[0] if bucket else now
            reset_time = math.ceil(oldest + self.window_seconds)
            return False, 0, reset_time

        # Allow: record timestamp
        bucket.append(now)
        allowed = True
        remaining = limit - (current_count + 1)
        # reset_time = oldest + window (or now+window if empty)
        oldest = bucket[0] if bucket else now
        reset_time = math.ceil(oldest + self.window_seconds)

        return allowed, remaining, reset_time
