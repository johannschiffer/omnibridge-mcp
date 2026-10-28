"""
Adaptive Token Bucket Rate Limiter.
Prevents account bans and provider rate limiting from autonomous agent loops.
"""
import time
from typing import Dict


class RateLimiter:
    def __init__(self, default_rate: float = 5.0, default_burst: int = 10, max_buckets: int = 1000):
        if default_rate <= 0:
            raise ValueError("default_rate must be positive")
        if default_burst < 1:
            raise ValueError("default_burst must be at least 1")
        self.default_rate = float(default_rate)
        self.default_burst = int(default_burst)
        self.max_buckets = max(1, int(max_buckets))
        self.buckets: Dict[str, Dict[str, float]] = {}

    def _get_bucket(self, key: str, now: float) -> Dict[str, float]:
        if key not in self.buckets:
            if len(self.buckets) >= self.max_buckets:
                oldest = next(iter(self.buckets))
                self.buckets.pop(oldest, None)
            self.buckets[key] = {
                "tokens": float(self.default_burst),
                "last_update": now,
            }
        return self.buckets[key]

    def acquire(self, key: str, tokens: int = 1) -> bool:
        """Attempts to consume tokens. Returns True if granted, False if rate limited."""
        now = time.monotonic()
        bucket = self._get_bucket(key, now)
        elapsed = max(0.0, now - bucket["last_update"])
        bucket["last_update"] = now

        bucket["tokens"] = min(float(self.default_burst), bucket["tokens"] + elapsed * self.default_rate)

        if bucket["tokens"] >= tokens:
            bucket["tokens"] -= tokens
            return True
        return False
