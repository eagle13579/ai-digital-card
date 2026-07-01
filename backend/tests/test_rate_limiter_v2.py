"""Tests for PerUserRateLimiter (8+ cases)."""

import time
import pytest
from app.services.rate_limiter_v2 import PerUserRateLimiter


class TestPerUserRateLimiter:
    """Per-user sliding-window rate limiter tests."""

    def test_first_request_allows_and_remaining_correct(self):
        limiter = PerUserRateLimiter(default_limit=1000, window_seconds=3600)
        allowed, remaining, reset_time = limiter.check_rate_limit("alice")
        assert allowed is True
        assert remaining == 999  # 1000 - 1

    def test_consecutive_requests_decrement_remaining(self):
        limiter = PerUserRateLimiter(default_limit=5, window_seconds=3600)
        for i in range(4):
            allowed, remaining, _ = limiter.check_rate_limit("bob")
            assert allowed is True
            assert remaining == (4 - i)  # 4,3,2,1

    def test_rejected_when_over_limit(self):
        limiter = PerUserRateLimiter(default_limit=3, window_seconds=3600)
        for _ in range(3):
            limiter.check_rate_limit("charlie")
        allowed, remaining, reset_time = limiter.check_rate_limit("charlie")
        assert allowed is False
        assert remaining == 0
        assert isinstance(reset_time, int)

    def test_different_users_have_independent_counts(self):
        limiter = PerUserRateLimiter(default_limit=2, window_seconds=3600)
        a1, r1, _ = limiter.check_rate_limit("user_a")
        b1, r2, _ = limiter.check_rate_limit("user_b")
        assert a1 is True and r1 == 1
        assert b1 is True and r2 == 1
        a2, r3, _ = limiter.check_rate_limit("user_a")
        assert a2 is True and r3 == 0
        b2, r4, _ = limiter.check_rate_limit("user_b")
        assert b2 is True and r4 == 0
        # Now user_a should be blocked, user_b should also be blocked
        a3, _, _ = limiter.check_rate_limit("user_a")
        assert a3 is False
        b3, _, _ = limiter.check_rate_limit("user_b")
        assert b3 is False

    def test_window_resets_after_expiry(self):
        limiter = PerUserRateLimiter(default_limit=1, window_seconds=0.05)
        a1, _, _ = limiter.check_rate_limit("dave")
        assert a1 is True
        a2, _, _ = limiter.check_rate_limit("dave")
        assert a2 is False
        time.sleep(0.06)
        a3, _, _ = limiter.check_rate_limit("dave")
        assert a3 is True

    def test_high_concurrency_burst(self):
        limiter = PerUserRateLimiter(default_limit=1005, window_seconds=3600)
        for i in range(1000):
            allowed, remaining, _ = limiter.check_rate_limit("eve")
            if not allowed:
                pytest.fail(f"Blocked at request {i+1}")
        # After 1000 requests, limit is 1005, so remaining = 5
        _, remaining, _ = limiter.check_rate_limit("eve")
        assert remaining == 4

    def test_boundary_limit_one(self):
        limiter = PerUserRateLimiter(default_limit=1, window_seconds=3600)
        a1, r1, _ = limiter.check_rate_limit("frank")
        assert a1 is True and r1 == 0
        a2, r2, _ = limiter.check_rate_limit("frank")
        assert a2 is False and r2 == 0
        # different user unaffected
        b1, r3, _ = limiter.check_rate_limit("george")
        assert b1 is True and r3 == 0

    def test_remaining_never_negative(self):
        limiter = PerUserRateLimiter(default_limit=2, window_seconds=3600)
        for _ in range(5):
            allowed, remaining, _ = limiter.check_rate_limit("hannah")
            assert remaining >= 0
            if not allowed:
                assert remaining == 0
