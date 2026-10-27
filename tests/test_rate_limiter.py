"""
Unit tests for OmniBridge rate limiter.
"""
from omnibridge.core.rate_limiter import RateLimiter

def test_rate_limiter_burst_and_exhaust():
    limiter = RateLimiter(default_rate=1.0, default_burst=2)

    # First 2 requests should be allowed immediately (burst)
    assert limiter.acquire("channel_a") is True
    assert limiter.acquire("channel_a") is True

    # Third immediate request should be rejected (exhausted)
    assert limiter.acquire("channel_a") is False

    # Different channel should have independent capacity
    assert limiter.acquire("channel_b") is True
