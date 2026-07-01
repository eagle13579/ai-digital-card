"""三级分层限流测试 — 覆盖 anonymous / standard / enterprise 三个等级。

测试策略：
  - 每个等级用独立的 ASGI scope + RateLimiterMiddleware 实例
  - 使用 1秒 窗口加速测试（实际线上 60秒）
  - 验证 RateLimit-Limit / RateLimit-Remaining / RateLimit-Reset 三头
  - 验证 request.state 提取等级、敏感端点减半
"""

import json
import time
import asyncio

import pytest


# ── 测试辅助 ──────────────────────────────────────────────────────────────────


async def _echo_app(scope, receive, send):
    """最小的 ASGI app: 返回 200 + 空 JSON 体。"""
    body = b'{"ok":true}'
    await send({
        "type": "http.response.start",
        "status": 200,
        "headers": [
            (b"content-type", b"application/json"),
            (b"content-length", str(len(body)).encode()),
        ],
    })
    await send({"type": "http.response.body", "body": body})


def _make_scope(*, path="/api/v1/cards", method="GET", headers=None, client=None,
                user_tier=None):
    """构建最小 ASGI scope，可选注入 user_tier。"""
    h = [(k.encode() if isinstance(k, str) else k,
          v.encode() if isinstance(v, str) else v)
         for k, v in (headers or {}).items()]
    scope = {
        "type": "http",
        "http_version": "1.1",
        "method": method,
        "path": path,
        "raw_path": path.encode(),
        "headers": h,
        "client": client or ["127.0.0.1", 54321],
        "query_string": b"",
        "scheme": "http",
    }
    if user_tier is not None:
        scope["state"] = {"user_tier": user_tier}
    return scope


async def _run_requests(mw, scope, count):
    """连续发送 count 次请求，返回响应列表。"""
    results = []
    for _ in range(count):
        responses = []

        async def _send(msg):
            responses.append(msg)

        await mw(scope, None, _send)
        results.append(responses)
    return results


def _normalize_headers(headers):
    """HTTP 头名大小写不敏感，统一转小写。"""
    return {k.lower(): v for k, v in headers.items()}


def _assert_rate_limit_headers(headers, expected_limit, expected_remaining_min,
                               expected_remaining_max):
    """验证 RateLimit 三头。"""
    h = _normalize_headers(headers)
    for name in (b"ratelimit-limit", b"ratelimit-remaining", b"ratelimit-reset"):
        assert name in h, f"缺少 {name.decode()} 头"

    assert int(h[b"ratelimit-limit"]) == expected_limit
    remaining = int(h[b"ratelimit-remaining"])
    assert expected_remaining_min <= remaining <= expected_remaining_max, \
        f"remaining={remaining}, 期望 [{expected_remaining_min}, {expected_remaining_max}]"
    # reset 必须是未来时间戳
    assert int(h[b"ratelimit-reset"]) > int(time.time()) - 1


# ══════════════════════════════════════════════════════════════════════
# 测试类: 三级分层限流
# ══════════════════════════════════════════════════════════════════════


class TestRateLimiterTiers:
    """三级分层限流：anonymous(100/min) / standard(1000/min) / enterprise(10000/min)。"""

    # ── 1) Anonymous tier ──────────────────────────────────────────────

    @pytest.mark.asyncio
    async def test_anonymous_tier_limit(self):
        """anonymous 等级限流 100/min（用小窗口 1s + 限量 3 加速验证）。"""
        from app.middleware.rate_limiter import RateLimiterMiddleware

        scope = _make_scope(user_tier="anonymous")
        mw = RateLimiterMiddleware(
            _echo_app,
            limits={"anonymous": 3, "standard": 1000, "enterprise": 10000},
            window_seconds=60,
        )

        # 前 3 次应通过
        for i in range(3):
            responses = []
            async def _send(msg):
                responses.append(msg)

            await mw(scope, None, _send)
            assert responses[0]["status"] == 200, f"anonymous 第 {i+1} 次应通过"

        # 第 4 次被限
        responses = []
        async def _send4(msg):
            responses.append(msg)

        await mw(scope, None, _send4)
        assert responses[0]["status"] == 429, "anonymous 超限应返回 429"

        # 验证 429 响应头
        headers = dict(responses[0].get("headers", []) or [])
        h = {k.lower(): v for k, v in headers.items()}
        assert int(h[b"ratelimit-limit"]) == 3
        assert h[b"ratelimit-remaining"] == b"0"

    @pytest.mark.asyncio
    async def test_anonymous_default_when_no_tier(self):
        """没有 user_tier 时默认 anonymous。"""
        from app.middleware.rate_limiter import RateLimiterMiddleware

        scope = _make_scope()  # 没有 user_tier
        mw = RateLimiterMiddleware(
            _echo_app,
            limits={"anonymous": 2, "standard": 1000, "enterprise": 10000},
            window_seconds=60,
        )

        results = await _run_requests(mw, scope, 3)
        assert results[0][0]["status"] == 200
        assert results[1][0]["status"] == 200
        assert results[2][0]["status"] == 429, "匿名默认应被限"

    # ── 2) Standard tier ───────────────────────────────────────────────

    @pytest.mark.asyncio
    async def test_standard_tier_limit(self):
        """standard 等级限流 1000/min（用 5 限额窗口加速验证）。"""
        from app.middleware.rate_limiter import RateLimiterMiddleware

        scope = _make_scope(user_tier="standard")
        mw = RateLimiterMiddleware(
            _echo_app,
            limits={"anonymous": 2, "standard": 5, "enterprise": 10000},
            window_seconds=60,
        )

        results = await _run_requests(mw, scope, 6)
        for i in range(5):
            assert results[i][0]["status"] == 200, f"standard 第 {i+1} 次应通过"
        assert results[5][0]["status"] == 429, "standard 超限应返回 429"

        # 验证 remaining 递减
        headers3 = dict(results[2][0].get("headers", []) or [])
        h3 = {k.lower(): v for k, v in headers3.items()}
        assert int(h3[b"ratelimit-remaining"]) == 2  # 5-3=2

        headers4 = dict(results[4][0].get("headers", []) or [])
        h4 = {k.lower(): v for k, v in headers4.items()}
        assert int(h4[b"ratelimit-remaining"]) == 0  # 5-5=0

    # ── 3) Enterprise tier ─────────────────────────────────────────────

    @pytest.mark.asyncio
    async def test_enterprise_tier_limit(self):
        """enterprise 等级配额远高于其他等级。"""
        from app.middleware.rate_limiter import RateLimiterMiddleware

        scope = _make_scope(user_tier="enterprise")
        mw = RateLimiterMiddleware(
            _echo_app,
            limits={"anonymous": 2, "standard": 3, "enterprise": 10},
            window_seconds=60,
        )

        # enterprise 可以连续发 10 次
        results = await _run_requests(mw, scope, 11)
        for i in range(10):
            assert results[i][0]["status"] == 200, f"enterprise 第 {i+1} 次应通过"
        assert results[10][0]["status"] == 429, "enterprise 超限应返回 429"

    # ── 4) Tier isolation ──────────────────────────────────────────────

    @pytest.mark.asyncio
    async def test_tiers_are_independent(self):
        """三个等级的配额互不影响。"""
        from app.middleware.rate_limiter import RateLimiterMiddleware

        # 每个等级限额 3，但使用不同 IP 确保隔离
        mw = RateLimiterMiddleware(
            _echo_app,
            limits={"anonymous": 3, "standard": 3, "enterprise": 3},
            window_seconds=60,
        )

        scope_anon = _make_scope(client=["10.0.0.10", 1], user_tier="anonymous")
        scope_std  = _make_scope(client=["10.0.0.20", 1], user_tier="standard")
        scope_ent  = _make_scope(client=["10.0.0.30", 1], user_tier="enterprise")

        # 每个等级发满 3 次
        for s in [scope_anon, scope_std, scope_ent]:
            for _ in range(3):
                responses = []
                async def _send(msg):
                    responses.append(msg)
                await mw(s, None, _send)
                assert responses[0]["status"] == 200

        # 每个等级再发 1 次 — 全部被限
        for s in [scope_anon, scope_std, scope_ent]:
            responses = []
            async def _send(msg):
                responses.append(msg)
            await mw(s, None, _send)
            assert responses[0]["status"] == 429, "所有等级超限都应 429"

    # ── 5) RateLimit headers ───────────────────────────────────────────

    @pytest.mark.asyncio
    async def test_ratelimit_headers_on_all_tiers(self):
        """三个等级的响应都包含正确的 RateLimit-* 头。"""
        from app.middleware.rate_limiter import RateLimiterMiddleware

        mw = RateLimiterMiddleware(
            _echo_app,
            limits={"anonymous": 10, "standard": 20, "enterprise": 30},
            window_seconds=60,
        )

        for tier, expected_limit in [("anonymous", 10), ("standard", 20), ("enterprise", 30)]:
            scope = _make_scope(client=[f"10.0.0.{hash(tier) % 100}", 1], user_tier=tier)
            responses = []
            async def _send(msg):
                responses.append(msg)
            await mw(scope, None, _send)

            headers = dict(responses[0].get("headers", []) or [])
            _assert_rate_limit_headers(
                headers,
                expected_limit=expected_limit,
                expected_remaining_min=expected_limit - 2,
                expected_remaining_max=expected_limit - 1,
            )

    # ── 6) Sensitive endpoint half-rate ─────────────────────────────────

    @pytest.mark.asyncio
    async def test_sensitive_endpoint_half_rate(self):
        """敏感端点 (/auth/*, /api/payment/*) 速率减半。"""
        from app.middleware.rate_limiter import RateLimiterMiddleware

        mw = RateLimiterMiddleware(
            _echo_app,
            limits={"anonymous": 4, "standard": 4, "enterprise": 4},
            window_seconds=60,
        )

        # 普通端点: anonymous 可以发 4 次
        scope_normal = _make_scope(
            path="/api/v1/cards",
            client=["10.0.0.1", 1],
            user_tier="anonymous",
        )
        for i in range(4):
            responses = []
            async def _send(msg):
                responses.append(msg)
            await mw(scope_normal, None, _send)
            assert responses[0]["status"] == 200, f"普通端点第 {i+1} 次应通过"

        # 敏感端点: anonymous 只有 2 次（4//2）
        scope_sensitive = _make_scope(
            path="/auth/login",
            client=["10.0.0.2", 1],
            user_tier="anonymous",
        )
        for i in range(2):
            responses = []
            async def _send(msg):
                responses.append(msg)
            await mw(scope_sensitive, None, _send)
            assert responses[0]["status"] == 200, f"敏感端点第 {i+1} 次应通过"

        # 第 3 次被限
        responses = []
        async def _send3(msg):
            responses.append(msg)
        await mw(scope_sensitive, None, _send3)
        assert responses[0]["status"] == 429, "敏感端点超限应 429"

    @pytest.mark.asyncio
    async def test_sensitive_enterprise_half_rate(self):
        """企业用户敏感端点也是 half-rate。"""
        from app.middleware.rate_limiter import RateLimiterMiddleware

        mw = RateLimiterMiddleware(
            _echo_app,
            limits={"anonymous": 2, "standard": 2, "enterprise": 6},
            window_seconds=60,
        )

        scope = _make_scope(
            path="/api/payment/checkout",
            client=["10.0.0.50", 1],
            user_tier="enterprise",
        )
        # 敏感端点: 6//2 = 3
        for i in range(3):
            responses = []
            async def _send(msg):
                responses.append(msg)
            await mw(scope, None, _send)
            assert responses[0]["status"] == 200, f"enterprise 敏感端点第 {i+1} 次应通过"

        responses = []
        async def _send4(msg):
            responses.append(msg)
        await mw(scope, None, _send4)
        assert responses[0]["status"] == 429, "enterprise 敏感端点超限应 429"

    # ── 7) request.state 提取等级 ──────────────────────────────────────

    @pytest.mark.asyncio
    async def test_tier_from_request_state(self):
        """中间件优先从 scope['state']['user_tier'] 提取等级。"""
        from app.middleware.rate_limiter import RateLimiterMiddleware

        scope = _make_scope(user_tier="enterprise")
        mw = RateLimiterMiddleware(
            _echo_app,
            limits={"anonymous": 1, "standard": 1, "enterprise": 5},
            window_seconds=60,
        )

        for i in range(5):
            responses = []
            async def _send(msg):
                responses.append(msg)
            await mw(scope, None, _send)
            assert responses[0]["status"] == 200, f"request.state enterprise 第 {i+1} 次应通过"

        # 第 6 次被限
        responses = []
        async def _send6(msg):
            responses.append(msg)
        await mw(scope, None, _send6)
        assert responses[0]["status"] == 429

    @pytest.mark.asyncio
    async def test_tier_fallback_chain(self):
        """等级降级链路: state -> scope -> override -> JWT -> anonymous。"""
        from app.middleware.rate_limiter import RateLimiterMiddleware

        mw = RateLimiterMiddleware(
            _echo_app,
            limits={"anonymous": 1, "standard": 5, "enterprise": 10},
            window_seconds=60,
        )

        # case 1: scope['state']['user_tier'] — enterprise
        scope1 = _make_scope(user_tier="enterprise", client=["10.0.0.100", 1])
        responses = []
        async def _send1(msg):
            responses.append(msg)
        await mw(scope1, None, _send1)
        h1 = {k.lower(): v for k, v in dict(responses[0].get("headers", []) or []).items()}
        assert int(h1[b"ratelimit-limit"]) == 10, "state enterprise 应得 10 限额"

        # case 2: scope['user_tier'] — standard（没有 state）
        scope2 = _make_scope(client=["10.0.0.101", 1])
        scope2["user_tier"] = "standard"
        responses = []
        async def _send2(msg):
            responses.append(msg)
        await mw(scope2, None, _send2)
        h2 = {k.lower(): v for k, v in dict(responses[0].get("headers", []) or []).items()}
        assert int(h2[b"ratelimit-limit"]) == 5, "scope user_tier standard 应得 5 限额"

        # case 3: anonymous（没有 state 也没有 user_tier）
        scope3 = _make_scope(client=["10.0.0.102", 1])
        responses = []
        async def _send3(msg):
            responses.append(msg)
        await mw(scope3, None, _send3)
        h3 = {k.lower(): v for k, v in dict(responses[0].get("headers", []) or []).items()}
        assert int(h3[b"ratelimit-limit"]) == 1, "默认 anonymous 应得 1 限额"

    # ── 8) 向后兼容: legacy mode ───────────────────────────────────────

    @pytest.mark.asyncio
    async def test_legacy_mode_backward_compat(self):
        """max_requests 参数（旧模式）仍然工作。"""
        from app.middleware.rate_limiter import RateLimiterMiddleware

        scope = _make_scope()
        mw = RateLimiterMiddleware(_echo_app, max_requests=5, window_seconds=60)

        results = await _run_requests(mw, scope, 6)
        for i in range(5):
            assert results[i][0]["status"] == 200, f"legacy 第 {i+1} 次应通过"
        assert results[5][0]["status"] == 429, "legacy 超限应 429"

    # ── 9) 窗口恢复 ─────────────────────────────────────────────────────

    @pytest.mark.asyncio
    async def test_window_recovers_after_expiry(self):
        """窗口过期后配额恢复（所有等级）。"""
        from app.middleware.rate_limiter import RateLimiterMiddleware

        mw = RateLimiterMiddleware(
            _echo_app,
            limits={"anonymous": 2, "standard": 2, "enterprise": 2},
            window_seconds=1,  # 1秒窗口加速
        )

        for tier in ("anonymous", "standard", "enterprise"):
            scope = _make_scope(client=[f"10.0.0.{hash(tier) % 100}", 1], user_tier=tier)

            # 用完 2 次
            for _ in range(2):
                responses = []
                async def _send(msg):
                    responses.append(msg)
                await mw(scope, None, _send)
                assert responses[0]["status"] == 200

            # 被限
            responses = []
            async def _send3(msg):
                responses.append(msg)
            await mw(scope, None, _send3)
            assert responses[0]["status"] == 429

            # 等待窗口过期
            await asyncio.sleep(1.1)

            # 恢复
            responses = []
            async def _send4(msg):
                responses.append(msg)
            await mw(scope, None, _send4)
            assert responses[0]["status"] == 200, f"{tier} 窗口过期后应恢复"

    # ── 10) 429 响应体 ─────────────────────────────────────────────────

    @pytest.mark.asyncio
    async def test_429_body_all_tiers(self):
        """429 响应体包含 detail 和 retry_after 字段。"""
        from app.middleware.rate_limiter import RateLimiterMiddleware

        mw = RateLimiterMiddleware(
            _echo_app,
            limits={"anonymous": 1, "standard": 1, "enterprise": 1},
            window_seconds=60,
        )

        for tier in ("anonymous", "standard", "enterprise"):
            scope = _make_scope(client=[f"10.0.0.{hash(tier) % 100}", 1], user_tier=tier)

            # 用满
            responses = []
            async def _send1(msg):
                responses.append(msg)
            await mw(scope, None, _send1)
            assert responses[0]["status"] == 200

            # 触发 429
            responses = []
            async def _send2(msg):
                responses.append(msg)
            await mw(scope, None, _send2)
            assert responses[0]["status"] == 429

            body = json.loads(responses[1]["body"])
            assert "detail" in body, f"{tier} 429 应包含 detail"
            assert "retry_after" in body, f"{tier} 429 应包含 retry_after"
            assert isinstance(body["retry_after"], int), "retry_after 应为整数"
