"""
Adaptive Token Bucket Rate Limiter.
Prevents account bans and provider rate limiting from autonomous agent loops.
"""
import time
from typing import Dict

class RateLimiter:
    def __init__(self, default_rate: float = 5.0, default_burst: int = 10):
        """
        :param default_rate: Tokens added per second.
        :param default_burst: Max bucket capacity.
        """
        self.default_rate = default_rate
        self.default_burst = default_burst
        self.buckets: Dict[str, Dict[str, float]] = {}

    def _get_bucket(self, key: str) -> Dict[str, float]:
        if key not in self.buckets:
            self.buckets[key] = {
                "tokens": float(self.default_burst),
                "last_update": time.time()
            }
        return self.buckets[key]

    def acquire(self, key: str, tokens: int = 1) -> bool:
        """Attempts to consume tokens. Returns True if granted, False if rate limited."""
        now = time.time()
        bucket = self._get_bucket(key)
        elapsed = now - bucket["last_update"]
        bucket["last_update"] = now

        # Replenish
        bucket["tokens"] = min(float(self.default_burst), bucket["tokens"] + elapsed * self.default_rate)

        if bucket["tokens"] >= tokens:
            bucket["tokens"] -= tokens
            return True
        return False
