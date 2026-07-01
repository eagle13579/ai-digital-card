"""CSRF 中间件独立测试 — 直接测试 ASGI 中间件逻辑，不依赖完整 FastAPI 应用。"""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.middleware.csrf_middleware import (
    CsrfMiddleware,
    CSRF_COOKIE_NAME,
    CSRF_HEADER_NAME,
    CSRF_TOKEN_PATH,
    EXCLUDED_PATHS,
)


# ── 模拟 ASGI 应用 ──────────────────────────────────────────────────────
class EchoASGIApp:
    """简单的 ASGI 应用，返回请求信息用于验证中间件行为。"""

    async def __call__(self, scope, receive, send):
        headers = dict(scope.get("headers", []))
        body = (
            '{"status":"ok","path":"' + scope.get("path", "") + '"}'
        ).encode("utf-8")

        await send({
            "type": "http.response.start",
            "status": 200,
            "headers": [
                (b"content-type", b"application/json"),
                (b"content-length", str(len(body)).encode("latin-1")),
            ],
        })
        await send({
            "type": "http.response.body",
            "body": body,
        })


# ── 辅助函数 ────────────────────────────────────────────────────────────

def _make_scope(method: str, path: str, headers: list | None = None, scheme: str = "http"):
    """构造 ASGI scope 字典。"""
    scope = {
        "type": "http",
        "method": method,
        "path": path,
        "scheme": scheme,
        "headers": headers or [],
        "query_string": b"",
        "http_version": "1.1",
        "client": ("127.0.0.1", 12345),
        "server": ("testserver", 80),
    }
    return scope


class ResponseCatcher:
    """捕获中间件 / 应用发起的 ASGI 事件。"""

    def __init__(self):
        self.start = None
        self.body = b""
        self.complete = asyncio.Event()

    async def __call__(self, message):
        if message["type"] == "http.response.start":
            self.start = message
        elif message["type"] == "http.response.body":
            self.body += message.get("body", b"")
            if not message.get("more_body", False):
                self.complete.set()

    async def wait(self, timeout=5):
        await asyncio.wait_for(self.complete.wait(), timeout=timeout)


# ── 测试用例 ────────────────────────────────────────────────────────────

async def test_csrf_token_generation():
    """测试 GET /api/csrf/token 生成 token 并设置 Cookie。"""
    middleware = CsrfMiddleware(EchoASGIApp())
    scope = _make_scope("GET", CSRF_TOKEN_PATH)
    catcher = ResponseCatcher()

    await middleware(scope, None, catcher)
    await catcher.wait()

    assert catcher.start["status"] == 200, f"Expected 200, got {catcher.start['status']}"
    headers = dict(catcher.start["headers"])
    assert (b"content-type", b"application/json") in catcher.start["headers"], "Missing content-type"

    import json
    body = json.loads(catcher.body)
    assert "token" in body, "Response body missing 'token' field"
    assert len(body["token"]) == 64, f"Expected 64-char token, got {len(body['token'])}"

    # 验证 Set-Cookie
    set_cookie = headers.get(b"set-cookie", b"").decode()
    assert CSRF_COOKIE_NAME in set_cookie, f"Cookie '{CSRF_COOKIE_NAME}' not in Set-Cookie header"
    assert "Path=/" in set_cookie, "Cookie missing Path=/"
    assert "SameSite=Lax" in set_cookie, "Cookie missing SameSite=Lax"
    # 非 HTTPS 不应有 Secure 标志
    assert "Secure" not in set_cookie, "Secure flag should not be set on HTTP"

    print(f"  ✅ GET {CSRF_TOKEN_PATH} → 200, token={body['token'][:16]}...")
    return body["token"]


async def test_safe_method_passthrough():
    """测试 GET/HEAD/OPTIONS 请求不加 CSRF token 也能通过。"""
    for method in ("GET", "HEAD", "OPTIONS"):
        middleware = CsrfMiddleware(EchoASGIApp())
        scope = _make_scope(method, "/api/user/profile")
        catcher = ResponseCatcher()

        await middleware(scope, None, catcher)
        await catcher.wait()

        assert catcher.start["status"] == 200, f"{method} should pass without CSRF, got {catcher.start['status']}"
        print(f"  ✅ {method} /api/user/profile → 200 (safe method)")


async def test_post_without_csrf():
    """测试 POST 无 CSRF token 返回 403。"""
    middleware = CsrfMiddleware(EchoASGIApp())
    scope = _make_scope("POST", "/api/user/profile")
    catcher = ResponseCatcher()

    await middleware(scope, None, catcher)
    await catcher.wait()

    assert catcher.start["status"] == 403, f"Expected 403, got {catcher.start['status']}"
    print(f"  ✅ POST /api/user/profile (no CSRF) → 403")


async def test_post_with_valid_csrf():
    """测试 POST 携带有效 CSRF token 通过。"""
    token = "a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6"

    middleware = CsrfMiddleware(EchoASGIApp())
    scope = _make_scope("POST", "/api/user/profile", [
        (b"cookie", f"{CSRF_COOKIE_NAME}={token}".encode("latin-1")),
        (CSRF_HEADER_NAME.lower().encode("latin-1"), token.encode()),
    ])
    catcher = ResponseCatcher()

    await middleware(scope, None, catcher)
    await catcher.wait()

    assert catcher.start["status"] == 200, f"Expected 200, got {catcher.start['status']}"
    print(f"  ✅ POST /api/user/profile (valid CSRF) → 200")


async def test_post_with_invalid_csrf():
    """测试 POST 携带无效 CSRF token 返回 403。"""
    middleware = CsrfMiddleware(EchoASGIApp())
    scope = _make_scope("POST", "/api/user/profile", [
        (b"cookie", f"{CSRF_COOKIE_NAME}=valid-token-value".encode("latin-1")),
        (CSRF_HEADER_NAME.lower().encode("latin-1"), b"invalid-token-value"),
    ])
    catcher = ResponseCatcher()

    await middleware(scope, None, catcher)
    await catcher.wait()

    assert catcher.start["status"] == 403, f"Expected 403, got {catcher.start['status']}"
    print(f"  ✅ POST /api/user/profile (mismatched CSRF) → 403")


async def test_post_without_cookie():
    """测试 POST 有 header 但无 Cookie 返回 403。"""
    middleware = CsrfMiddleware(EchoASGIApp())
    scope = _make_scope("POST", "/api/user/profile", [
        (CSRF_HEADER_NAME.lower().encode("latin-1"), b"some-token"),
        # 无 Cookie 头
    ])
    catcher = ResponseCatcher()

    await middleware(scope, None, catcher)
    await catcher.wait()

    assert catcher.start["status"] == 403, f"Expected 403, got {catcher.start['status']}"
    print(f"  ✅ POST /api/user/profile (no cookie) → 403")


async def test_excluded_paths():
    """测试排除路径绕过 CSRF 校验。"""
    for path_prefix in EXCLUDED_PATHS:
        test_path = path_prefix.rstrip("/") + "/test-action"
        middleware = CsrfMiddleware(EchoASGIApp())
        scope = _make_scope("POST", test_path)
        catcher = ResponseCatcher()

        await middleware(scope, None, catcher)
        await catcher.wait()

        assert catcher.start["status"] == 200, f"POST {test_path} should bypass CSRF, got {catcher.start['status']}"
        print(f"  ✅ POST {test_path} → 200 (excluded path)")


async def test_token_with_https():
    """测试 HTTPS 下 Secure 标志。"""
    middleware = CsrfMiddleware(EchoASGIApp())
    scope = _make_scope("GET", CSRF_TOKEN_PATH, scheme="https")
    catcher = ResponseCatcher()

    await middleware(scope, None, catcher)
    await catcher.wait()

    headers = dict(catcher.start["headers"])
    set_cookie = headers.get(b"set-cookie", b"").decode()
    assert "Secure" in set_cookie, "Secure flag should be set on HTTPS"
    assert "SameSite=Lax" in set_cookie, "Cookie missing SameSite=Lax"
    print(f"  ✅ GET {CSRF_TOKEN_PATH} (HTTPS) → Set-Cookie with Secure flag")


# ── 主入口 ──────────────────────────────────────────────────────────────

async def main():
    print("=" * 56)
    print("  CSRF Middleware Test Suite (Double Submit Cookie)")
    print("=" * 56)

    tests = [
        ("CSRF Token Generation", test_csrf_token_generation),
        ("Safe Method Passthrough", test_safe_method_passthrough),
        ("POST Without CSRF", test_post_without_csrf),
        ("POST With Valid CSRF", test_post_with_valid_csrf),
        ("POST With Invalid CSRF", test_post_with_invalid_csrf),
        ("POST Without Cookie", test_post_without_cookie),
        ("Excluded Paths", test_excluded_paths),
        ("HTTPS Secure Flag", test_token_with_https),
    ]

    passed = 0
    failed = 0
    for name, test_fn in tests:
        print(f"\n── {name} ──")
        try:
            await test_fn()
            passed += 1
        except AssertionError as e:
            print(f"  ❌ FAIL: {e}")
            failed += 1
        except Exception as e:
            print(f"  ❌ ERROR: {type(e).__name__}: {e}")
            failed += 1

    total = passed + failed
    print(f"\n{'='*56}")
    print(f"  Results: {total} tests — ✅ {passed} passed, ❌ {failed} failed")
    print(f"{'='*56}")
    return failed == 0


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
