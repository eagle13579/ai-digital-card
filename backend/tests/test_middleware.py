"""
AI数字名片 — 中间件单元测试
==============================

覆盖范围:
  P0: RateLimiterMiddleware — 限流 (6 tests)
  P1: RequestIDMiddleware — 请求ID追踪 (6 tests)
  P1: MetricsMiddleware — APM监控 (8 tests)
  P2: I18nMiddleware — 国际化 (9 tests)

测试策略:
  每个中间件作为独立的 ASGI 中间件单元测试，使用最小的 ASGI echo app，
  避免被其他中间件或 FastAPI 全栈干扰。
"""

import json
import time
import asyncio

import pytest


# ══════════════════════════════════════════════════════════════════════
# 测试辅助工具
# ══════════════════════════════════════════════════════════════════════


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


def _make_scope(*, path="/test", method="GET", headers=None, client=None):
    """构建最小 ASGI scope。"""
    h = [(k.encode() if isinstance(k, str) else k,
          v.encode() if isinstance(v, str) else v)
         for k, v in (headers or {}).items()]
    return {
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


# ══════════════════════════════════════════════════════════════════════
# P0 — RateLimiterMiddleware
# ══════════════════════════════════════════════════════════════════════

class TestRateLimiter:
    """速率限制中间件核心功能。"""

    @pytest.mark.asyncio
    async def test_normal_request_passes(self):
        """正常请求通过，状态码 200。"""
        from app.middleware.rate_limiter import RateLimiterMiddleware

        scope = _make_scope()
        mw = RateLimiterMiddleware(_echo_app, max_requests=100, window_seconds=60)
        responses = []

        async def _send(msg):
            responses.append(msg)

        await mw(scope, None, _send)
        assert responses[0]["status"] == 200

    @pytest.mark.asyncio
    async def test_headers_present_on_success(self):
        """成功请求返回 RateLimit-* 响应头。"""
        from app.middleware.rate_limiter import RateLimiterMiddleware

        scope = _make_scope()
        mw = RateLimiterMiddleware(_echo_app, max_requests=100, window_seconds=60)
        responses = []

        async def _send(msg):
            responses.append(msg)

        await mw(scope, None, _send)
        headers = dict(responses[0].get("headers", []) or [])
        h = {k.lower(): v for k, v in headers.items()}
        assert b"ratelimit-limit" in h
        assert b"ratelimit-remaining" in h
        assert b"ratelimit-reset" in h
        assert h[b"ratelimit-limit"] == b"100"

    @pytest.mark.asyncio
    async def test_rate_limit_exceeded_returns_429(self):
        """超限请求返回 429 + retry-after 头。"""
        from app.middleware.rate_limiter import RateLimiterMiddleware

        scope = _make_scope()
        mw = RateLimiterMiddleware(_echo_app, max_requests=2, window_seconds=60)

        # 前 2 次通过
        for i in range(2):
            responses = []

            async def _send(msg):
                responses.append(msg)

            await mw(scope, None, _send)
            assert responses[0]["status"] == 200, f"第 {i+1} 次请求应通过"

        # 第 3 次被限
        responses = []

        async def _send3(msg):
            responses.append(msg)

        await mw(scope, None, _send3)
        assert responses[0]["status"] == 429

        rsp_headers = dict(responses[0].get("headers", []) or [])
        rh = {k.lower(): v for k, v in rsp_headers.items()}
        assert b"retry-after" in rh
        assert b"ratelimit-remaining" in rh
        assert rh[b"ratelimit-remaining"] == b"0"
        retry_after = int(rsp_headers[b"retry-after"])
        assert retry_after > 0

    @pytest.mark.asyncio
    async def test_different_ips_independent_quotas(self):
        """不同 IP 拥有独立的配额。"""
        from app.middleware.rate_limiter import RateLimiterMiddleware

        mw = RateLimiterMiddleware(_echo_app, max_requests=2, window_seconds=60)

        # IP_A 用满配额
        scope_a = _make_scope(client=["10.0.0.1", 12345])
        for _ in range(2):
            responses = []

            async def _send(msg):
                responses.append(msg)

            await mw(scope_a, None, _send)
            assert responses[0]["status"] == 200

        # IP_B 仍有自己的配额 — 可以再发 2 次
        scope_b = _make_scope(client=["10.0.0.2", 54321])
        for i in range(2):
            responses = []

            async def _send(msg):
                responses.append(msg)

            await mw(scope_b, None, _send)
            assert responses[0]["status"] == 200, f"IP B 第 {i+1} 次应通过"

        # IP_A 已被限
        responses = []

        async def _send_a(msg):
            responses.append(msg)

        await mw(scope_a, None, _send_a)
        assert responses[0]["status"] == 429, "IP A 应被限"

    @pytest.mark.asyncio
    async def test_x_forwarded_for_ip_extraction(self):
        """通过 X-Forwarded-For 头提取客户端 IP。"""
        from app.middleware.rate_limiter import RateLimiterMiddleware

        mw = RateLimiterMiddleware(_echo_app, max_requests=1, window_seconds=60)
        scope = _make_scope(headers={"x-forwarded-for": "203.0.113.5, 10.0.0.1"})

        # 第一次通过
        responses = []

        async def _send(msg):
            responses.append(msg)

        await mw(scope, None, _send)
        assert responses[0]["status"] == 200

        # 第二次 — 同一个 X-Forwarded-For IP 应被限
        responses = []

        async def _send2(msg):
            responses.append(msg)

        await mw(scope, None, _send2)
        assert responses[0]["status"] == 429

    @pytest.mark.asyncio
    async def test_window_expiration(self):
        """窗口过期后配额恢复。"""
        from app.middleware.rate_limiter import RateLimiterMiddleware

        scope = _make_scope()
        mw = RateLimiterMiddleware(_echo_app, max_requests=1, window_seconds=1)

        responses = []

        async def _send(msg):
            responses.append(msg)

        # 用满
        await mw(scope, None, _send)
        assert responses[0]["status"] == 200

        # 被限
        responses = []

        async def _send2(msg):
            responses.append(msg)

        await mw(scope, None, _send2)
        assert responses[0]["status"] == 429

        # 等待窗口过期
        await asyncio.sleep(1.1)

        responses = []

        async def _send3(msg):
            responses.append(msg)

        await mw(scope, None, _send3)
        assert responses[0]["status"] == 200, "窗口过期后应恢复"

    @pytest.mark.asyncio
    async def test_retry_after_reasonable(self):
        """429 响应中 retry_after 值合理。"""
        from app.middleware.rate_limiter import RateLimiterMiddleware

        scope = _make_scope()
        mw = RateLimiterMiddleware(_echo_app, max_requests=1, window_seconds=5)

        responses = []

        async def _send(msg):
            responses.append(msg)

        await mw(scope, None, _send)

        responses = []

        async def _send2(msg):
            responses.append(msg)

        await mw(scope, None, _send2)

        headers = dict(responses[0].get("headers", []) or [])
        retry_after = int(headers[b"retry-after"])
        assert 1 <= retry_after <= 6, f"retry_after={retry_after} 超出预期范围"

    @pytest.mark.asyncio
    async def test_429_body_contains_detail_and_retry_after(self):
        """429 响应体包含 detail 和 retry_after 字段。"""
        from app.middleware.rate_limiter import RateLimiterMiddleware

        scope = _make_scope()
        mw = RateLimiterMiddleware(_echo_app, max_requests=1, window_seconds=60)

        responses = []

        async def _send(msg):
            responses.append(msg)

        await mw(scope, None, _send)

        responses = []

        async def _send2(msg):
            responses.append(msg)

        await mw(scope, None, _send2)

        body = json.loads(responses[1]["body"])
        assert "detail" in body
        assert "retry_after" in body
        assert isinstance(body["retry_after"], int)

    @pytest.mark.asyncio
    async def test_non_http_scope_passthrough(self):
        """非 HTTP scope（如 websocket）直接透传。"""
        from app.middleware.rate_limiter import RateLimiterMiddleware

        ws_scope = {"type": "websocket", "path": "/ws"}
        called = False

        async def fake_app(s, r, send):
            nonlocal called
            called = True

        mw = RateLimiterMiddleware(fake_app)
        await mw(ws_scope, None, None)
        assert called, "websocket scope 应直接透传"


# ══════════════════════════════════════════════════════════════════════
# P1 — RequestIDMiddleware
# ══════════════════════════════════════════════════════════════════════

class TestRequestID:
    """请求ID追踪中间件核心功能。"""

    @pytest.mark.asyncio
    async def test_auto_assigns_uuid_hex(self):
        """自动分配 X-Request-ID（32 字符 UUID hex）。"""
        from app.middleware.request_id import RequestIDMiddleware

        scope = _make_scope()
        app = RequestIDMiddleware(_echo_app)
        responses = []

        async def _send(msg):
            responses.append(msg)

        await app(scope, None, _send)
        headers = dict(responses[0].get("headers", []) or [])
        rid = headers.get(b"x-request-id", b"").decode()
        assert len(rid) == 32, f"UUID hex 应为 32 字符, got {len(rid)}: {rid}"
        int(rid, 16)  # 验证是合法 hex

    @pytest.mark.asyncio
    async def test_reuses_client_request_id(self):
        """复用客户端传入的 X-Request-ID（ASGI header names 应为小写）。"""
        from app.middleware.request_id import RequestIDMiddleware

        client_rid = "my-custom-trace-id-12345"
        # ASGI 规范要求 header name 为小写
        scope = _make_scope(headers={"x-request-id": client_rid})
        app = RequestIDMiddleware(_echo_app)
        responses = []

        async def _send(msg):
            responses.append(msg)

        await app(scope, None, _send)
        headers = dict(responses[0].get("headers", []) or [])
        assert headers.get(b"x-request-id", b"").decode() == client_rid

    @pytest.mark.asyncio
    async def test_request_id_in_response_headers(self):
        """X-Request-ID 出现在响应头中。"""
        from app.middleware.request_id import RequestIDMiddleware

        scope = _make_scope()
        app = RequestIDMiddleware(_echo_app)
        responses = []

        async def _send(msg):
            responses.append(msg)

        await app(scope, None, _send)
        headers = dict(responses[0].get("headers", []) or [])
        assert b"x-request-id" in headers

    @pytest.mark.asyncio
    async def test_context_var_set(self):
        """request_id_var contextvar 在请求期间被正确设置。"""
        from app.middleware.request_id import RequestIDMiddleware, request_id_var

        scope = _make_scope()
        captured = []

        async def capturing_app(s, r, send):
            captured.append(request_id_var.get())
            await _echo_app(s, r, send)

        app = RequestIDMiddleware(capturing_app)
        responses = []

        async def _send(msg):
            responses.append(msg)

        await app(scope, None, _send)
        assert len(captured) == 1
        rid = captured[0]
        assert len(rid) == 32
        int(rid, 16)

    @pytest.mark.asyncio
    async def test_context_var_cleanup(self):
        """请求结束后 request_id_var 恢复为请求前的值。"""
        from app.middleware.request_id import RequestIDMiddleware, request_id_var

        scope = _make_scope()
        app = RequestIDMiddleware(_echo_app)
        responses = []

        async def _send(msg):
            responses.append(msg)

        # 默认值为空字符串
        await app(scope, None, _send)
        assert request_id_var.get() == "", "context 应被清理为默认值"

    @pytest.mark.asyncio
    async def test_unique_per_request(self):
        """每次请求生成唯一的 X-Request-ID（100 次无重复）。"""
        from app.middleware.request_id import RequestIDMiddleware

        ids = set()
        for _ in range(100):
            scope = _make_scope()
            app = RequestIDMiddleware(_echo_app)
            responses = []

            async def _send(msg):
                responses.append(msg)

            await app(scope, None, _send)
            headers = dict(responses[0].get("headers", []) or [])
            rid = headers[b"x-request-id"].decode()
            ids.add(rid)

        assert len(ids) == 100, "100 次请求应生成 100 个不同的 ID"

    @pytest.mark.asyncio
    async def test_non_http_scope_passthrough(self):
        """非 HTTP scope 直接透传。"""
        from app.middleware.request_id import RequestIDMiddleware

        ws_scope = {"type": "websocket"}
        called = False

        async def fake_app(s, r, send):
            nonlocal called
            called = True

        app = RequestIDMiddleware(fake_app)
        await app(ws_scope, None, None)
        assert called


# ══════════════════════════════════════════════════════════════════════
# P1 — MetricsMiddleware
# ══════════════════════════════════════════════════════════════════════

class TestMetrics:
    """APM 监控中间件核心功能。"""

    @pytest.mark.asyncio
    async def test_metrics_passthrough(self):
        """/metrics 请求透传到内部 app（中间件不拦截）。"""
        from app.middleware.metrics import MetricsMiddleware

        scope = _make_scope(path="/metrics")

        async def metrics_app(s, r, send):
            body = b"# HELP test\n# TYPE test counter\ntest_total 1\n"
            await send({
                "type": "http.response.start",
                "status": 200,
                "headers": [(b"content-type", b"text/plain")],
            })
            await send({"type": "http.response.body", "body": body})

        mw = MetricsMiddleware(metrics_app)
        responses = []

        async def _send(msg):
            responses.append(msg)

        await mw(scope, None, _send)
        assert responses[0]["status"] == 200
        assert b"# HELP test" in responses[1]["body"]

    @pytest.mark.asyncio
    async def test_metrics_not_counted(self):
        """/metrics 不计入自身指标（递归防护）。"""
        from app.middleware.metrics import MetricsMiddleware

        app = MetricsMiddleware(_echo_app)

        async def _send(msg):
            pass

        for _ in range(10):
            scope = _make_scope(path="/metrics")
            await app(scope, None, _send)

        assert app.total_requests == 0, "/metrics 不应计入 total_requests"
        assert app.total_count == 0, "/metrics 不应计入 histogram"

    @pytest.mark.asyncio
    async def test_request_count_increases(self):
        """请求计数器随请求增加。"""
        from app.middleware.metrics import MetricsMiddleware

        app = MetricsMiddleware(_echo_app)

        async def _send(msg):
            pass

        for _ in range(5):
            scope = _make_scope(path="/api/test")
            await app(scope, None, _send)

        assert app.total_requests == 5
        assert app.successful_requests == 5

    @pytest.mark.asyncio
    async def test_status_classification_2xx(self):
        """2xx 状态码归类到 successful_requests。"""
        from app.middleware.metrics import MetricsMiddleware

        async def app_200(s, r, send):
            await send({"type": "http.response.start", "status": 200, "headers": []})
            await send({"type": "http.response.body", "body": b""})

        mw = MetricsMiddleware(app_200)
        scope = _make_scope(path="/ok")

        async def _send(msg):
            pass

        await mw(scope, None, _send)
        assert mw.successful_requests == 1
        assert mw.client_errors == 0
        assert mw.server_errors == 0

    @pytest.mark.asyncio
    async def test_status_classification_4xx(self):
        """4xx 状态码归类到 client_errors。"""
        from app.middleware.metrics import MetricsMiddleware

        async def app_404(s, r, send):
            await send({"type": "http.response.start", "status": 404, "headers": []})
            await send({"type": "http.response.body", "body": b""})

        mw = MetricsMiddleware(app_404)
        scope = _make_scope(path="/notfound")

        async def _send(msg):
            pass

        await mw(scope, None, _send)
        assert mw.client_errors == 1
        assert mw.successful_requests == 0

    @pytest.mark.asyncio
    async def test_status_classification_5xx(self):
        """5xx 状态码归类到 server_errors。"""
        from app.middleware.metrics import MetricsMiddleware

        async def app_500(s, r, send):
            await send({"type": "http.response.start", "status": 500, "headers": []})
            await send({"type": "http.response.body", "body": b""})

        mw = MetricsMiddleware(app_500)
        scope = _make_scope(path="/error")

        async def _send(msg):
            pass

        await mw(scope, None, _send)
        assert mw.server_errors == 1

    @pytest.mark.asyncio
    async def test_duration_histogram(self):
        """延迟直方图存在且 count/sum 正确。"""
        from app.middleware.metrics import MetricsMiddleware

        async def slow_app(s, r, send):
            await asyncio.sleep(0.01)
            await send({"type": "http.response.start", "status": 200, "headers": []})
            await send({"type": "http.response.body", "body": b""})

        mw = MetricsMiddleware(slow_app)
        scope = _make_scope(path="/slow")

        async def _send(msg):
            pass

        await mw(scope, None, _send)
        assert mw.total_count == 1
        assert mw.total_sum > 0.005

        bucket_sum = sum(mw.bucket_counts.values())
        assert bucket_sum >= 1, f"至少应有一个 bucket, got {bucket_sum}"

    @pytest.mark.asyncio
    async def test_generate_metrics_output(self):
        """generate_metrics() 输出完整的 Prometheus 文本格式。"""
        from app.middleware.metrics import MetricsMiddleware

        app = MetricsMiddleware(_echo_app)

        async def _send(msg):
            pass

        # 产生一些指标
        for _ in range(3):
            scope = _make_scope(path="/test")
            await app(scope, None, _send)

        output = app.generate_metrics()

        # 指标名称
        assert "ncard_http_requests_total" in output
        assert "ncard_http_request_duration_seconds" in output
        assert "ncard_http_active_requests" in output

        # Prometheus 格式约定
        assert "# HELP" in output
        assert "# TYPE" in output
        assert '_bucket{le="+Inf"}' in output
        assert "_count" in output
        assert "_sum" in output

        # 有计数
        assert 'ncard_http_requests_total{status="2xx"} 3' in output
        assert 'ncard_http_requests_total{status="4xx"} 0' in output
        assert 'ncard_http_requests_total{status="5xx"} 0' in output

    @pytest.mark.asyncio
    async def test_get_metrics_instance(self):
        """get_metrics_instance() 返回正确实例。"""
        from app.middleware.metrics import MetricsMiddleware, get_metrics_instance
        import app.middleware.metrics as mmod

        mmod._metrics_instance = None
        assert get_metrics_instance() is None

        mw = MetricsMiddleware(_echo_app)
        assert get_metrics_instance() is mw

    @pytest.mark.asyncio
    async def test_non_http_scope_passthrough(self):
        """非 HTTP scope 不计数。"""
        from app.middleware.metrics import MetricsMiddleware

        ws_scope = {"type": "websocket"}
        called = False

        async def fake_app(s, r, send):
            nonlocal called
            called = True

        mw = MetricsMiddleware(fake_app)
        await mw(ws_scope, None, None)
        assert called
        assert mw.total_requests == 0

    @pytest.mark.asyncio
    async def test_active_requests_gauge(self):
        """活跃请求仪表盘在请求结束后归零。"""
        from app.middleware.metrics import MetricsMiddleware

        mw = MetricsMiddleware(_echo_app)
        assert mw.active_requests == 0

        scope = _make_scope(path="/test")

        async def _send(msg):
            pass

        await mw(scope, None, _send)
        assert mw.active_requests == 0


# ══════════════════════════════════════════════════════════════════════
# P2 — I18nMiddleware
# ══════════════════════════════════════════════════════════════════════

class TestI18n:
    """国际化中间件核心功能。"""

    @pytest.mark.asyncio
    async def test_accept_language_zh_cn(self):
        """Accept-Language: zh-CN → gettext 返回中文。"""
        from app.middleware.i18n_middleware import I18nMiddleware, gettext, locale_var

        captured_locale = []

        async def capturing_app(s, r, send):
            captured_locale.append(locale_var.get())
            await _echo_app(s, r, send)

        scope = _make_scope(headers={"accept-language": "zh-CN,zh;q=0.9"})
        app = I18nMiddleware(capturing_app)

        async def _send(msg):
            pass

        await app(scope, None, _send)
        assert captured_locale[0] == "zh"
        assert gettext("success", "zh") == "操作成功"
        assert gettext("not_found", "zh") == "资源不存在"

    @pytest.mark.asyncio
    async def test_accept_language_en_us(self):
        """Accept-Language: en-US → gettext 返回英文。"""
        from app.middleware.i18n_middleware import I18nMiddleware, gettext, locale_var

        captured_locale = []

        async def capturing_app(s, r, send):
            captured_locale.append(locale_var.get())
            await _echo_app(s, r, send)

        scope = _make_scope(headers={"accept-language": "en-US,en;q=0.9"})
        app = I18nMiddleware(capturing_app)

        async def _send(msg):
            pass

        await app(scope, None, _send)
        # 在请求期间捕获 locale
        assert captured_locale[0] == "en"
        # gettext 在当前线程无请求时使用默认 locale "zh"，
        # 但用指定 locale 可以正确翻译
        assert gettext("success", "en") == "Success"

    @pytest.mark.asyncio
    async def test_no_accept_language_default_zh(self):
        """无 Accept-Language 头 → 默认中文。"""
        from app.middleware.i18n_middleware import I18nMiddleware, gettext, locale_var

        captured_locale = []

        async def capturing_app(s, r, send):
            captured_locale.append(locale_var.get())
            await _echo_app(s, r, send)

        scope = _make_scope()
        app = I18nMiddleware(capturing_app)

        async def _send(msg):
            pass

        await app(scope, None, _send)
        assert captured_locale[0] == "zh"
        assert gettext("success", "zh") == "操作成功"

    @pytest.mark.asyncio
    async def test_context_cleanup(self):
        """请求结束后 locale_var 被清理为默认值。"""
        from app.middleware.i18n_middleware import I18nMiddleware, locale_var

        scope = _make_scope(headers={"accept-language": "en-US"})
        app = I18nMiddleware(_echo_app)

        locale_var.set("zh")

        async def _send(msg):
            pass

        await app(scope, None, _send)
        assert locale_var.get() == "zh", "context 应被清理为默认值 'zh'"

    def test_gettext_with_explicit_locale(self):
        """gettext(key, locale) 指定语言优先。"""
        from app.middleware.i18n_middleware import gettext

        assert gettext("success", "zh") == "操作成功"
        assert gettext("success", "en") == "Success"
        assert gettext("internal_error", "zh") == "服务器内部错误"
        assert gettext("internal_error", "en") == "Internal Server Error"

    def test_gettext_missing_key(self):
        """不存在的 key 返回 key 本身。"""
        from app.middleware.i18n_middleware import gettext

        assert gettext("nonexistent_key_xyz", "zh") == "nonexistent_key_xyz"
        assert gettext("nonexistent_key_xyz", "en") == "nonexistent_key_xyz"

    @pytest.mark.asyncio
    async def test_accept_language_zh_tw(self):
        """Accept-Language: zh-TW → 检测为 zh。"""
        from app.middleware.i18n_middleware import I18nMiddleware, locale_var

        captured_locale = []

        async def capturing_app(s, r, send):
            captured_locale.append(locale_var.get())
            await _echo_app(s, r, send)

        scope = _make_scope(headers={"accept-language": "zh-TW"})
        app = I18nMiddleware(capturing_app)

        async def _send(msg):
            pass

        await app(scope, None, _send)
        assert captured_locale[0] == "zh"

    @pytest.mark.asyncio
    async def test_non_http_scope_passthrough(self):
        """非 HTTP scope 直接透传。"""
        from app.middleware.i18n_middleware import I18nMiddleware

        ws_scope = {"type": "websocket"}
        called = False

        async def fake_app(s, r, send):
            nonlocal called
            called = True

        app = I18nMiddleware(fake_app)
        await app(ws_scope, None, None)
        assert called

    @pytest.mark.asyncio
    async def test_multiple_languages_in_header(self):
        """多语言 Accept-Language 头 — detect_lang 优先匹配 zh 再匹配 en。"""
        from app.middleware.i18n_middleware import I18nMiddleware, locale_var

        captured = []

        async def cap_app(s, r, send):
            captured.append(locale_var.get())
            await _echo_app(s, r, send)

        # 只有 en，不含 zh → en
        scope = _make_scope(headers={"accept-language": "en;q=0.9, fr;q=0.5"})
        app = I18nMiddleware(cap_app)

        async def _send(msg):
            pass

        await app(scope, None, _send)
        assert captured[0] == "en"

        # 含 zh 始终优先（detect_lang 先检查 zh）
        captured.clear()
        scope2 = _make_scope(headers={"accept-language": "en;q=0.9, zh-CN;q=0.5"})
        app2 = I18nMiddleware(cap_app)
        await app2(scope2, None, _send)
        assert captured[0] == "zh"

    def test_locale_var_type(self):
        """locale_var 是 ContextVar[str] 类型。"""
        from app.middleware.i18n_middleware import locale_var
        assert hasattr(locale_var, "get")
        assert hasattr(locale_var, "set")
        assert hasattr(locale_var, "reset")
