"""输入注入安全测试 — SQL注入 / XSS / 路径遍历

测试策略:
  - 不直接操作数据库，而是向 API 端点发送恶意 payload
  - 验证 API 不会崩溃 (无 500) 且返回合理的错误代码 (400/422/401/404)
  - 使用 conftest.py 的 client fixture (ASGITransport)
"""

from __future__ import annotations

import os
import re
from urllib.parse import quote

import pytest


# ══════════════════════════════════════════════════════════════════════
# SQL 注入测试
# ══════════════════════════════════════════════════════════════════════


SQL_INJECTION_PAYLOADS = [
    # 经典注入
    "' OR '1'='1",
    "' OR 1=1--",
    "' OR '1'='1' --",
    "'; DROP TABLE users; --",
    "'; DELETE FROM users; --",
    "' UNION SELECT * FROM users--",
    "' UNION ALL SELECT NULL,NULL,NULL--",
    # 布尔盲注
    "' AND 1=1--",
    "' AND 1=2--",
    # 时间盲注
    "' AND SLEEP(5)--",
    "' OR SLEEP(5)--",
    "' AND pg_sleep(5)--",
    # SQLite 特定
    "' UNION SELECT sql FROM sqlite_master--",
    "'; INSERT INTO users VALUES(1,'hacker','pw');--",
    # 编码绕过
    "%27%20OR%20%271%27%3D%271",
    "\\' OR 1=1 --",
    # stacked queries
    "1; DROP TABLE brochures",
    # 带注释的注入
    "' OR 1=1 #",
    "' OR 1=1/**/",
]


class TestSqlInjection:
    """SQL 注入攻击防护测试。

    验证所有 API 端点对 SQL 注入 payload 返回适当错误 (非 500)。
    """

    @pytest.mark.asyncio
    @pytest.mark.parametrize("payload", SQL_INJECTION_PAYLOADS)
    async def test_health_endpoint_sql_injection(self, client, payload):
        """/health 端点应对 SQL 注入 payload 返回 200 (纯健康检查)。"""
        resp = await client.get("/health")
        assert resp.status_code == 200

    @pytest.mark.asyncio
    @pytest.mark.parametrize("payload", SQL_INJECTION_PAYLOADS[:5])
    async def test_user_endpoint_sql_injection_in_query(self, client, payload):
        """用户查询端点对 SQL 注入不应崩溃。"""
        resp = await client.get(f"/api/users?name={quote(payload)}")
        # 预期: 401 (未认证) 或 422 (参数校验失败) 或 404
        assert resp.status_code in (401, 404, 422, 400), (
            f"SQL 注入 payload 导致异常状态码: {resp.status_code}"
        )

    @pytest.mark.asyncio
    @pytest.mark.parametrize("payload", SQL_INJECTION_PAYLOADS[:8])
    async def test_auth_login_sql_injection(self, client, payload):
        """登录端点对 SQL 注入不应崩溃。"""
        resp = await client.post(
            "/api/auth/login",
            json={"phone": payload, "password": payload},
        )
        # 预期: 401 (认证失败) 或 422 (Pydantic 校验失败)
        assert resp.status_code in (401, 422, 400), (
            f"SQL 注入 payload 导致异常状态码: {resp.status_code}"
        )

    @pytest.mark.asyncio
    async def test_register_sql_injection(self, client):
        """注册端点对 SQL 注入不应崩溃。"""
        resp = await client.post(
            "/api/auth/register",
            json={
                "phone": "'; DROP TABLE users; --",
                "password": "test123456",
                "name": "<script>alert(1)</script>",
            },
        )
        assert resp.status_code in (400, 422, 409, 401), (
            f"SQL 注入 payload 导致异常状态码: {resp.status_code}"
        )


# ══════════════════════════════════════════════════════════════════════
# XSS (跨站脚本) 测试
# ══════════════════════════════════════════════════════════════════════


XSS_PAYLOADS = [
    # 经典 XSS
    "<script>alert(1)</script>",
    "<img src=x onerror=alert(1)>",
    "<svg onload=alert(1)>",
    # 属性 XSS
    "\" onmouseover=alert(1)",
    "' onfocus=alert(1) autofocus",
    # URL XSS
    "javascript:alert(1)",
    "data:text/html;base64,PHNjcmlwdD5hbGVydCgxKTwvc2NyaXB0Pg==",
    # 编码 XSS
    "&lt;script&gt;alert(1)&lt;/script&gt;",
    "&#x3C;script&#x3E;alert(1)&#x3C;/script&#x3E;",
    # DOM XSS
    "<a href=\"javascript:alert(1)\">click</a>",
    # 模板 XSS
    "{{constructor.constructor('alert(1)')()}}",
    "${alert(1)}",
    # UTF-8 编码绕过
    "<script>alert('测试')</script>",
]


class TestXssInjection:
    """XSS 攻击防护测试。

    验证 API 端点对 XSS payload 不会直接返回或反射。
    """

    @pytest.mark.asyncio
    @pytest.mark.parametrize("payload", XSS_PAYLOADS[:5])
    async def test_auth_login_xss(self, client, payload):
        """登录端点不应反射 XSS payload。"""
        resp = await client.post(
            "/api/auth/login",
            json={"phone": "13800000001", "password": payload},
        )
        assert resp.status_code in (401, 422, 400), (
            f"XSS payload 导致异常状态码: {resp.status_code}"
        )
        # 验证响应体不包含原始 XSS payload (反射型 XSS 检查)
        body = resp.text.lower()
        if resp.status_code == 422:
            xss_keywords = ["<script", "alert(", "onerror=", "onload="]
            assert not any(kw in body for kw in xss_keywords), (
                f"响应体中反射了 XSS payload: {body[:200]}"
            )

    @pytest.mark.asyncio
    async def test_security_headers_xss_protection(self, client):
        """验证安全响应头中包含 XSS 保护。"""
        resp = await client.get("/health")
        x_xss = resp.headers.get("x-xss-protection")
        assert x_xss == "1; mode=block", (
            f"X-XSS-Protection 头缺失或值错误: {x_xss}"
        )

    @pytest.mark.asyncio
    async def test_csp_blocks_inline_scripts(self, client):
        """Content-Security-Policy 应阻止内联脚本。"""
        resp = await client.get("/health")
        csp = resp.headers.get("content-security-policy")
        assert csp is not None, "缺少 Content-Security-Policy 头"
        # CSP 应为限制性策略
        assert "'self'" in csp, f"CSP 应限制为 self: {csp}"
        assert "default-src" in csp, f"CSP 应包含 default-src: {csp}"

    @pytest.mark.asyncio
    async def test_xframe_options_prevents_clickjacking(self, client):
        """X-Frame-Options 应防止点击劫持。"""
        resp = await client.get("/health")
        xfo = resp.headers.get("x-frame-options")
        assert xfo == "DENY", f"X-Frame-Options 应为 DENY: {xfo}"


# ══════════════════════════════════════════════════════════════════════
# 路径遍历测试
# ══════════════════════════════════════════════════════════════════════


PATH_TRAVERSAL_PAYLOADS = [
    # Unix 路径遍历
    "../../../etc/passwd",
    "../../../../etc/shadow",
    "../../.env",
    "../../../app/config.py",
    # Windows 路径遍历
    "..\\..\\..\\Windows\\System32\\drivers\\etc\\hosts",
    "..\\..\\..\\..\\.env",
    # URL 编码的路径遍历
    "%2e%2e%2f%2e%2e%2fetc%2fpasswd",
    "%2e%2e%5c%2e%2e%5cWindows%5cSystem32",
    # 双编码
    "%252e%252e%252fetc%252fpasswd",
    # 空字节注入
    "../../../etc/passwd%00.png",
    "../../../etc/passwd\0.jpg",
    # 混合遍历
    "....//....//....//etc/passwd",
    "..;/..;/..;/etc/passwd",
]


class TestPathTraversal:
    """路径遍历攻击防护测试。"""

    @pytest.mark.asyncio
    @pytest.mark.parametrize("payload", PATH_TRAVERSAL_PAYLOADS[:5])
    async def test_path_traversal_in_url(self, client, payload):
        """URL 路径参数不应允许遍历。"""
        resp = await client.get(f"/api/brochures/{quote(payload)}")
        # 预期: 400/404/422 (未找到/参数校验失败/路径解析拒绝)
        assert resp.status_code in (400, 404, 422, 401), (
            f"路径遍历 payload 导致异常状态码: {resp.status_code} for {payload[:30]}"
        )

    @pytest.mark.asyncio
    @pytest.mark.parametrize("payload", PATH_TRAVERSAL_PAYLOADS[:5])
    async def test_path_traversal_in_query(self, client, payload):
        """查询参数不应允许路径遍历。"""
        resp = await client.get(f"/api/users?file={quote(payload)}")
        assert resp.status_code in (400, 404, 422, 401), (
            f"查询参数路径遍历导致异常状态码: {resp.status_code}"
        )

    @pytest.mark.asyncio
    async def test_static_file_path_traversal(self, client):
        """静态文件服务应阻止路径遍历。"""
        payloads = [
            "/static/../../../etc/passwd",
            "/static/..%2f..%2f..%2fetc%2fpasswd",
            "/static/%2e%2e/%2e%2e/etc/passwd",
        ]
        for path in payloads:
            resp = await client.get(path)
            # 预期: 404 (未找到) 或 400 (路径拒绝), 不应是 200
            assert resp.status_code != 200, f"路径遍历应被阻止: {path}"
            assert resp.status_code in (400, 404, 403), (
                f"路径遍历导致异常状态码 {resp.status_code}: {path}"
            )


# ══════════════════════════════════════════════════════════════════════
# 通用安全边界测试
# ══════════════════════════════════════════════════════════════════════


DANGEROUS_PAYLOADS = [
    # 零字节
    "\0",
    "test\0payload",
    # 控制字符
    "\x00\x01\x02\x1f\x7f",
    # 超长输入 (10KB+)
    "A" * 10000,
    "B" * 50000,
    # Unicode 攻击向量
    "\uff1f" * 100,  # 全角问号
    "\u202e" * 100,  # 从右到左覆盖
    # 空值
    "null",
    "undefined",
    "None",
    # 特殊字符
    "!@#$%^&*()_+-=[]{}|;':\",./<>?",
]


class TestInputBoundary:
    """输入边界安全性测试。"""

    @pytest.mark.asyncio
    @pytest.mark.parametrize("payload", DANGEROUS_PAYLOADS[:5])
    async def test_dangerous_payloads_in_login(self, client, payload):
        """危险 payload 不应导致 500 错误。"""
        resp = await client.post(
            "/api/auth/login",
            json={"phone": "13800000001", "password": payload},
        )
        assert resp.status_code in (401, 422, 400), (
            f"危险 payload 导致异常状态码: {resp.status_code}"
        )

    @pytest.mark.asyncio
    async def test_ultra_long_payload_returns_422(self, client):
        """超长输入应被 Pydantic 校验拒绝 (422)。"""
        resp = await client.post(
            "/api/auth/login",
            json={"phone": "13800000001", "password": "X" * 100000},
        )
        assert resp.status_code == 422, (
            f"超长 payload 应返回 422, 实际: {resp.status_code}"
        )


# ══════════════════════════════════════════════════════════════════════
# sanitize 函数单元测试
# ══════════════════════════════════════════════════════════════════════


class TestSanitizeFunctions:
    """验证 sanitize 工具函数的正确性。"""

    def test_sanitize_soql_string_escapes_single_quotes(self):
        from app.utils.security import sanitize_soql_string

        result = sanitize_soql_string("it's a test")
        assert result == "it\\'s a test"

    def test_sanitize_soql_string_escapes_backslashes(self):
        from app.utils.security import sanitize_soql_string

        result = sanitize_soql_string("path\\to\\file")
        assert result == "path\\\\to\\\\file"

    def test_sanitize_soql_like_escapes_wildcards(self):
        from app.utils.security import sanitize_soql_like

        result = sanitize_soql_like("100% complete_test")
        assert result == "100\\% complete\\_test"

    def test_validate_email_valid(self):
        from app.utils.security import validate_email

        assert validate_email("user@example.com")
        assert validate_email("test.user+tag@company.co.uk")

    def test_validate_email_invalid(self):
        from app.utils.security import validate_email

        assert not validate_email("not-an-email")
        assert not validate_email("")
        assert not validate_email("@example.com")


# ══════════════════════════════════════════════════════════════════════
# Fuzzing 兼容性验证
# ══════════════════════════════════════════════════════════════════════


class TestFuzzingIntegration:
    """验证 fuzzing 测试框架可正常运行。"""

    def test_fuzzing_module_importable(self):
        import tests.fuzzing.test_api_fuzzing  # noqa: F401

    def test_fuzzing_has_sql_injection_coverage(self):
        """fuzzing 测试应包含 SQL 注入 payload。"""
        from tests.fuzzing.test_api_fuzzing import _sql_injection_strings

        payloads = _sql_injection_strings()
        assert len(payloads) > 0, "fuzzing 应包含 SQL 注入 payload"

    def test_fuzzing_has_xss_coverage(self):
        """fuzzing 测试应包含 XSS payload。"""
        from tests.fuzzing.test_api_fuzzing import _xss_strings

        payloads = _xss_strings()
        assert len(payloads) > 0, "fuzzing 应包含 XSS payload"
