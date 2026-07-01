"""
API Fuzzing tests — random extreme inputs against core endpoints.

Tests use only built-in Python + pytest + httpx (already installed).
No external fuzzing frameworks required.

Strategy:
  1. Generate random payloads with extreme values:
     - Ultra-long strings (10 KB+)
     - Special characters (null bytes, control chars, escapes)
     - Unicode / multi-byte (CJK, emoji, RTL, surrogates)
     - SQL injection attempts
     - XSS / HTML injection attempts
     - Boundary numeric values (negative, huge, float)
     - Empty / missing / null fields
     - Deeply nested JSON
     - Unexpected data types (list-as-dict, int-as-string)
  2. Send to core endpoints via async HTTP client (ASGITransport).
  3. Verify the API **does not crash** (no 500) and returns a reasonable
     error code (400 / 422 / 401 / 404).
"""

import itertools
import json
import math
import random
import string
import uuid

import pytest
from fastapi import status

# ══════════════════════════════════════════════════════════════════════
# Fuzz helpers
# ══════════════════════════════════════════════════════════════════════

SEED = 42
_random = random.Random(SEED)

# ── payload generators ──────────────────────────────────────────


def _long_string(min_kb: int = 10, max_kb: int = 50) -> str:
    """Generate a random ASCII string between *min_kb* and *max_kb* KB."""
    length = _random.randint(min_kb * 1024, max_kb * 1024)
    return "".join(_random.choices(string.ascii_letters + string.digits + " ", k=length))


def _special_chars_string() -> str:
    """String with null bytes, control characters, and shell escapes."""
    return (
        "\x00\x01\x02\x1f\x7f"
        "'; rm -rf /; '"
        '"; echo pwned; "'
        "`cat /etc/passwd`"
        "$(whoami)"
        "| shutdown -h now"
        "& ping &"
        "%00%0d%0a"
    )


def _unicode_string() -> str:
    """Mixed Unicode: CJK, emoji, RTL, combining marks, zero-width chars."""
    return (
        "中文数字名片测试"
        "🚀📇💼🔥🛡️"
        "\u200e\u200f\u200d\u200c"  # zero-width joiners / directional marks
        "ضصثقفغعهخحجد"
        "àáâãäåæçèéêë"
        "\u0300\u0301\u0302"  # combining accents (will attach to preceding char)
        "\U0001f600\U0001f644\U0001f92a"  # emoji beyond BMP
    )


def _sql_injection_strings() -> list[str]:
    """Common SQL injection payloads."""
    return [
        "' OR '1'='1",
        "'; DROP TABLE users; --",
        "\" OR 1=1 --",
        "' UNION SELECT * FROM users --",
        "admin'--",
        "1' OR '1'='1' /*",
        "' OR '1'='1' /*",
        "''; WAITFOR DELAY '0:0:10' --",
        "1; SELECT pg_sleep(10) --",
        "' UNION ALL SELECT NULL,NULL,NULL,NULL--",
        "admin' OR '1'='1' LIMIT 1 --",
    ]


def _xss_strings() -> list[str]:
    """Common XSS / HTML-injection payloads."""
    return [
        "<script>alert(1)</script>",
        "<img src=x onerror=alert(1)>",
        "<svg onload=alert(1)>",
        "javascript:alert(1)",
        "\" onmouseover=\"alert(1)",
        "<<SCRIPT>alert(1);//<</SCRIPT>",
        "<IMG SRC=javascript:alert('XSS')>",
        "<BODY ONLOAD=alert(1)>",
        "<details open ontoggle=alert(1)>",
        "{{constructor.constructor('alert(1)')()}}",
    ]


def _payload_variations(base: dict) -> list[dict]:
    """Generate many adversarial variations of a dict payload."""
    variations = []

    # ── over-length strings ──────────────────────────────────────
    for key in list(base.keys()):
        if isinstance(base[key], str):
            copy = dict(base)
            copy[key] = _long_string(10, 50)
            variations.append(copy)

    # ── special characters ───────────────────────────────────────
    for key in list(base.keys()):
        if isinstance(base[key], str):
            copy = dict(base)
            copy[key] = _special_chars_string()
            variations.append(copy)

    # ── unicode ─────────────────────────────────────────────────
    for key in list(base.keys()):
        if isinstance(base[key], str):
            copy = dict(base)
            copy[key] = _unicode_string()
            variations.append(copy)

    # ── SQL injection (each payload as a separate variation) ──────
    for sql_payload in _sql_injection_strings():
        for key in list(base.keys()):
            if isinstance(base[key], str):
                copy = dict(base)
                copy[key] = sql_payload
                variations.append(copy)

    # ── XSS injection (each payload as a separate variation) ──────
    for xss_payload in _xss_strings():
        for key in list(base.keys()):
            if isinstance(base[key], str):
                copy = dict(base)
                copy[key] = xss_payload
                variations.append(copy)

    # ── null / missing ───────────────────────────────────────────
    for key in list(base.keys()):
        copy = dict(base)
        copy[key] = None
        variations.append(copy)

    for key in list(base.keys()):
        copy = dict(base)
        del copy[key]
        variations.append(copy)

    # ── empty values ────────────────────────────────────────────
    for key in list(base.keys()):
        if isinstance(base[key], str):
            copy = dict(base)
            copy[key] = ""
            variations.append(copy)
        elif isinstance(base[key], list):
            copy = dict(base)
            copy[key] = []
            variations.append(copy)
        elif isinstance(base[key], dict):
            copy = dict(base)
            copy[key] = {}
            variations.append(copy)

    # ── wrong types ────────────────────────────────────────────
    for key in list(base.keys()):
        if isinstance(base[key], str):
            for wrong in [123, 3.14, True, [], {}, None]:
                copy = dict(base)
                copy[key] = wrong
                variations.append(copy)
        elif isinstance(base[key], (int, float)):
            for wrong in ["string", [], {}, None]:
                copy = dict(base)
                copy[key] = wrong
                variations.append(copy)

    # ── boundary numeric values ────────────────────────────────
    for key in list(base.keys()):
        if isinstance(base[key], (int, float)):
            for boundary in [-1, 0, 2**31, 2**63 - 1, -(2**31), 3.14e20, -3.14e20, math.nan, math.inf]:
                try:
                    copy = dict(base)
                    copy[key] = boundary
                    variations.append(copy)
                except Exception:
                    pass

    # ── deeply nested JSON ─────────────────────────────────────
    def _deep_nest(depth: int = 50) -> dict:
        return {"a": {"b": {"c": _deep_nest(depth - 1)}}} if depth > 0 else "leaf"

    copy = dict(base)
    copy["_nested"] = _deep_nest(50)
    variations.append(copy)

    # ── huge int / float fields ────────────────────────────────
    for key in list(base.keys()):
        if isinstance(base[key], str):
            copy = dict(base)
            copy[key] = 10**1000
            variations.append(copy)

    return variations


# ══════════════════════════════════════════════════════════════════════
# Endpoint definitions & fuzz targets
# ══════════════════════════════════════════════════════════════════════

# NOTE: keep these in sync with the actual API spec.
# These are the core endpoints the task specifies.

FUZZ_ENDPOINTS = [
    # ── Public / no-auth endpoints ──────────────────────────────
    {"method": "GET", "path": "/health", "auth": False},
    {"method": "GET", "path": "/api/health", "auth": False},
    # ── Auth ──────────────────────────────────────────────────
    {"method": "POST", "path": "/api/auth/register", "auth": False},
    {"method": "POST", "path": "/api/auth/login", "auth": False},
    # ── User ──────────────────────────────────────────────────
    {"method": "GET", "path": "/api/users/me", "auth": True},
    {"method": "PUT", "path": "/api/users/me", "auth": True},
    # ── Contacts (tags = contacts proxy) ──────────────────────
    {"method": "GET", "path": "/api/tags/me", "auth": True},
    {"method": "POST", "path": "/api/tags/me", "auth": True},
    {"method": "DELETE", "path": "/api/tags/me/99999", "auth": True},
    # ── Brochures ─────────────────────────────────────────────
    {"method": "GET", "path": "/api/brochures", "auth": True},
    {"method": "POST", "path": "/api/brochures", "auth": True},
    {"method": "GET", "path": "/api/brochures/99999", "auth": True},
    {"method": "DELETE", "path": "/api/brochures/99999", "auth": True},
    # ── Trust ─────────────────────────────────────────────────
    {"method": "GET", "path": "/api/trust/network", "auth": True},
    {"method": "POST", "path": "/api/trust/network", "auth": True},
]

# Typical valid payload shapes for each POST/PUT endpoint.
SAMPLE_BODIES: dict[str, dict] = {
    "/api/auth/register": {
        "phone": "13800000000",
        "password": "testpass123",
        "name": "测试用户",
        "company": "示例科技",
        "title": "工程师",
    },
    "/api/auth/login": {
        "phone": "13800000001",
        "password": "testpass123",
    },
    "/api/users/me": {
        "name": "新名字",
        "title": "高级工程师",
        "company": "新公司",
        "intro": "个人简介内容",
    },
    "/api/brochures": {
        "title": "我的数字名片",
        "cover": "https://example.com/cover.jpg",
        "pages": [
            {"sort_order": 0, "content_type": "text", "content": "内容"},
        ],
    },
    "/api/tags/me": {
        "tags": [
            {"tag": "Python开发", "weight": 1.0},
        ],
        "tag_type": "provide",
        "source": "manual",
    },
    "/api/trust/network": {
        "trusted_user_id": 1,
    },
}


def _get_body(method: str, path: str) -> dict | None:
    """Return a plausible valid body for the given path, or None."""
    if method not in ("POST", "PUT"):
        return None
    # Try exact match, then prefix match
    if path in SAMPLE_BODIES:
        return dict(SAMPLE_BODIES[path])
    # Strip trailing path segments for matching
    for known_path, body in SAMPLE_BODIES.items():
        if path.startswith(known_path):
            return dict(body)
    return None


# ══════════════════════════════════════════════════════════════════════
# Parametrized fuzz tests
# ══════════════════════════════════════════════════════════════════════


def _id_fn(val) -> str:
    """Short pytest id for a fuzz variation."""
    if isinstance(val, dict):
        summary = ",".join(
            f"{k}={type(v).__name__[:3] if v is not None else 'N'}[{str(v)[:20]}]"
            for k, v in list(val.items())[:2]
        )
        return summary
    return str(val)[:40]


@pytest.mark.fuzzing
@pytest.mark.parametrize(
    "endpoint",
    FUZZ_ENDPOINTS,
    ids=lambda ep: f"{ep['method']} {ep['path']}",
)
class TestAPIFuzzing:
    """
    Fuzz each core endpoint with random / extreme inputs.

    Every variation must either succeed (2xx) or return a non-500 error
    (400, 401, 403, 404, 422) — the API must never crash.
    """

    @staticmethod
    def _get_payloads(endpoint: dict) -> list[dict | None]:
        """Return a list of payloads (body dicts) to fuzz."""
        body = _get_body(endpoint["method"], endpoint["path"])
        if body is None:
            return [None]
        return _payload_variations(body)

    def test_fuzz_no_crash(
        self, client, auth_headers, endpoint: dict
    ):
        """Random fuzzing: send extreme input, verify no 500."""
        payloads = self._get_payloads(endpoint)
        method = endpoint["method"].lower()
        url = endpoint["path"]
        headers = auth_headers if endpoint["auth"] else {}

        errors = []
        for i, payload in enumerate(payloads):
            try:
                if method == "get":
                    resp = client.get(url, headers=headers)
                elif method == "post":
                    resp = client.post(url, json=payload, headers=headers)
                elif method == "put":
                    resp = client.put(url, json=payload, headers=headers)
                elif method == "delete":
                    resp = client.delete(url, headers=headers)
                else:
                    continue

                # Check the API does NOT crash with 500
                if resp.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR:
                    errors.append(
                        f"  [{i}] got 500 with payload: {json.dumps(payload, ensure_ascii=False)[:200]}"
                    )
                elif resp.status_code == status.HTTP_501_NOT_IMPLEMENTED:
                    errors.append(
                        f"  [{i}] got 501 with payload: {json.dumps(payload, ensure_ascii=False)[:200]}"
                    )
            except Exception as exc:
                # Connection errors / timeouts are also crashes in fuzzing
                errors.append(f"  [{i}] crash: {exc}")

        if errors:
            pytest.fail(
                f"Fuzzing FAILED for {endpoint['method']} {endpoint['path']} "
                f"({len(errors)}/{len(payloads)} payloads caused crashes):\n"
                + "\n".join(errors[:10])
                + (f"\n  ... and {len(errors) - 10} more" if len(errors) > 10 else "")
            )


# ══════════════════════════════════════════════════════════════════════
# Targeted adversarial scenarios
# ══════════════════════════════════════════════════════════════════════


class TestFuzzingAdversarialScenarios:
    """Specific adversarial scenarios beyond random fuzzing."""

    @staticmethod
    def _make_auth_headers(test_user) -> dict:
        """Build auth headers for a given user."""
        from app.routers.auth import create_access_token

        token = create_access_token({"sub": str(test_user.id)})
        return {"Authorization": f"Bearer {token}"}

    # ── SQL injection across endpoints ──────────────────────────────

    @pytest.mark.fuzzing
    @pytest.mark.parametrize(
        "url",
        [
            "/api/users/me",
            "/api/brochures",
            "/api/tags/me",
            "/api/trust/network",
        ],
    )
    @pytest.mark.parametrize(
        "sql_payload", _sql_injection_strings(), ids=lambda s: s[:30]
    )
    def test_sql_injection_no_crash(
        self, client, auth_headers, url: str, sql_payload: str
    ):
        """SQL injection payloads must not crash the API (no 500)."""
        if url == "/api/users/me":
            resp = client.get(url, headers=auth_headers)
        elif url == "/api/brochures":
            resp = client.post(
                url,
                json={"title": sql_payload, "pages": [{"sort_order": 0, "content_type": "text", "content": sql_payload}]},
                headers=auth_headers,
            )
        elif url == "/api/tags/me":
            resp = client.post(
                url,
                json={"tags": [{"tag": sql_payload, "weight": 1.0}], "tag_type": "provide", "source": "manual"},
                headers=auth_headers,
            )
        elif url == "/api/trust/network":
            resp = client.post(
                url,
                json={"trusted_user_id": 1},
                headers=auth_headers,
            )
        else:
            resp = client.get(url, headers=auth_headers)

        assert resp.status_code != status.HTTP_500_INTERNAL_SERVER_ERROR, (
            f"SQL injection '{sql_payload}' on {url} caused 500"
        )
        assert resp.status_code != status.HTTP_501_NOT_IMPLEMENTED, (
            f"SQL injection '{sql_payload}' on {url} caused 501"
        )

    # ── XSS injection across endpoints ──────────────────────────────

    @pytest.mark.fuzzing
    @pytest.mark.parametrize(
        "url",
        [
            "/api/users/me",
            "/api/brochures",
        ],
    )
    @pytest.mark.parametrize("xss_payload", _xss_strings(), ids=lambda s: s[:25])
    def test_xss_injection_no_crash(
        self, client, auth_headers, url: str, xss_payload: str
    ):
        """XSS payloads must not crash the API (no 500)."""
        if url == "/api/users/me":
            resp = client.put(
                url,
                json={"name": xss_payload, "title": xss_payload, "intro": xss_payload},
                headers=auth_headers,
            )
        else:
            resp = client.post(
                url,
                json={"title": xss_payload, "pages": [{"sort_order": 0, "content_type": "text", "content": xss_payload}]},
                headers=auth_headers,
            )

        assert resp.status_code != status.HTTP_500_INTERNAL_SERVER_ERROR, (
            f"XSS '{xss_payload}' on {url} caused 500"
        )

    # ── Unicode boundary tests ─────────────────────────────────────

    @pytest.mark.fuzzing
    @pytest.mark.parametrize(
        "url,field",
        [
            ("/api/users/me", "name"),
            ("/api/brochures", "title"),
            ("/api/brochures", "content"),
        ],
    )
    def test_unicode_boundary_no_crash(
        self, client, auth_headers, url: str, field: str
    ):
        """Max-length Unicode strings must not crash the API."""
        huge_unicode = "\u4e00" * 10000 + "\U0001f600" * 1000  # 11K chars
        payload = {field: huge_unicode}
        if url == "/api/users/me":
            resp = client.put(url, json=payload, headers=auth_headers)
        elif url == "/api/brochures":
            if field == "title":
                resp = client.post(url, json={"title": huge_unicode, "pages": []}, headers=auth_headers)
            else:
                resp = client.post(
                    url,
                    json={"title": "test", "pages": [{"sort_order": 0, "content_type": "text", "content": huge_unicode}]},
                    headers=auth_headers,
                )
        else:
            resp = client.get(url, headers=auth_headers)

        assert resp.status_code != status.HTTP_500_INTERNAL_SERVER_ERROR, (
            f"Unicode overload on {url}.{field} caused 500"
        )

    # ── Auth token fuzzing ──────────────────────────────────────────

    @pytest.mark.fuzzing
    def test_fuzzed_auth_tokens(self, client):
        """Various malformed auth tokens must not crash the API."""
        fuzzed_tokens = [
            "Bearer " + _long_string(1, 5),
            "Bearer " + _special_chars_string(),
            "Bearer " + _unicode_string(),
            "Bearer " + _random.choice(_sql_injection_strings()),
            "Bearer " + _random.choice(_xss_strings()),
            "Bearer invalid-token-format",
            "Basic dGVzdDp0ZXN0",
            "",
            "Bearer ",
            "bearer token",
        ]
        for token in fuzzed_tokens:
            resp = client.get(
                "/api/users/me",
                headers={"Authorization": token} if token else {},
            )
            assert resp.status_code != status.HTTP_500_INTERNAL_SERVER_ERROR, (
                f"Fuzzed token caused 500: {token[:50]}"
            )

    # ── Path traversal / injection ──────────────────────────────────

    @pytest.mark.fuzzing
    @pytest.mark.parametrize(
        "bad_path",
        [
            "/api/users/../../etc/passwd",
            "/api/brochures/%00",
            "/api/brochures/null",
            "/api/brochures/0x1",
            "/api/brochures/9999999999999999999999",
            "/api/brochures/-1",
            "/api/brochures/' OR '1'='1",
            "/api/users/me; DROP TABLE users",
            "/api/brochures/<script>",
        ],
    )
    def test_path_injection_no_crash(self, client, bad_path: str):
        """Malformed / injected URL paths must not crash the API."""
        resp = client.get(bad_path)
        assert resp.status_code != status.HTTP_500_INTERNAL_SERVER_ERROR, (
            f"Path '{bad_path}' caused 500"
        )

    # ── Request header fuzzing ──────────────────────────────────────

    @pytest.mark.fuzzing
    @pytest.mark.parametrize(
        "header_name,header_value",
        [
            ("Content-Type", "application/xml"),
            ("Content-Type", "text/plain"),
            ("Content-Type", ""),
            ("Accept", "text/html"),
            ("X-Forwarded-For", _long_string(5, 10)),
            ("X-Forwarded-For", _special_chars_string()),
            ("X-Forwarded-For", _unicode_string()),
            ("User-Agent", "\x00\x01\x02" * 100),
            ("Referer", "javascript:alert(1)"),
            ("Cookie", "' OR '1'='1"),
        ],
    )
    def test_fuzzed_headers_no_crash(
        self, client, auth_headers, header_name: str, header_value: str
    ):
        """Fuzzed HTTP headers must not crash the API."""
        headers = dict(auth_headers)
        headers[header_name] = header_value
        resp = client.get("/api/users/me", headers=headers)
        # 401 is expected if the header corruption breaks auth parsing
        assert resp.status_code != status.HTTP_500_INTERNAL_SERVER_ERROR, (
            f"Header '{header_name}: {header_value[:30]}' caused 500"
        )

    # ── Query-parameter fuzzing ─────────────────────────────────────

    @pytest.mark.fuzzing
    @pytest.mark.parametrize(
        "query_params",
        [
            {"page": -1},
            {"page": 0},
            {"page": 999999999999},
            {"page": "string"},
            {"page": []},
            {"limit": 0},
            {"limit": -1},
            {"limit": 1000000},
            {"q": _long_string(10, 20)},
            {"q": _sql_injection_strings()[0]},
            {"q": _xss_strings()[0]},
            {"sort": "'; DROP TABLE brochures; --"},
            {"filter": '{"$gt": ""}'},
        ],
    )
    def test_fuzzed_query_params_no_crash(
        self, client, auth_headers, query_params: dict
    ):
        """Fuzzed query parameters must not crash the API."""
        resp = client.get(
            "/api/brochures",
            params=query_params,
            headers=auth_headers,
        )
        assert resp.status_code != status.HTTP_500_INTERNAL_SERVER_ERROR, (
            f"Query params {query_params} caused 500"
        )

    # ── Content-Type mismatch ───────────────────────────────────────

    @pytest.mark.fuzzing
    def test_content_type_mismatch(self, client, auth_headers):
        """Sending non-JSON content to JSON endpoints must not crash."""
        test_cases = [
            ("application/x-www-form-urlencoded", "title=test&pages="),
            ("text/plain", "plain text body"),
            ("application/xml", "<root><title>test</title></root>"),
            ("multipart/form-data; boundary=boundary", "--boundary\r\nContent-Disposition: form-data; name=\"title\"\r\n\r\ntest\r\n--boundary--"),
        ]
        for content_type, body in test_cases:
            resp = client.post(
                "/api/brochures",
                content=body,
                headers={
                    "Content-Type": content_type,
                    **auth_headers,
                },
            )
            assert resp.status_code != status.HTTP_500_INTERNAL_SERVER_ERROR, (
                f"Content-Type '{content_type}' caused 500"
            )

    # ── JSON structure bombs ────────────────────────────────────────

    @pytest.mark.fuzzing
    def test_json_structure_bombs(self, client, auth_headers):
        """JSON that could cause resource exhaustion must not crash."""
        bombs = [
            # Deeply nested
            {"a": {"b": {"c": {"d": {"e": "x" * 1000}}}}},
            # Billion laughs (XML-style JSON expansion)
            {"a": [{"a": [{"a": [{"a": [{"a": "x"}]}]}]}]},
            # Wide keys (many fields)
            {str(i): "v" for i in range(1000)},
            # Mixed array types
            {"data": [1, "two", None, [], {}, 3.14, True, [1, [2, [3]]]]},
            # Very long key names
            {"x" * 10000: "value"},
        ]
        for bomb in bombs:
            resp = client.post(
                "/api/brochures",
                json=bomb,
                headers=auth_headers,
            )
            assert resp.status_code != status.HTTP_500_INTERNAL_SERVER_ERROR, (
                f"JSON structure bomb caused 500: {str(bomb)[:100]}"
            )


# ══════════════════════════════════════════════════════════════════════
# Quick smoke: verify the fuzzing infrastructure itself works
# ══════════════════════════════════════════════════════════════════════


class TestFuzzInfrastructure:
    """Meta-tests for the fuzzing helpers."""

    def test_long_string_generates_correct_size(self):
        s = _long_string(10, 10)
        assert len(s) >= 10 * 1024

    def test_payload_variations_count(self):
        base = {"name": "张三", "age": 30}
        vars_ = _payload_variations(base)
        # Should produce many variations
        assert len(vars_) > 10

    def test_sql_injection_strings_non_empty(self):
        assert len(_sql_injection_strings()) > 5

    def test_xss_strings_non_empty(self):
        assert len(_xss_strings()) > 5
