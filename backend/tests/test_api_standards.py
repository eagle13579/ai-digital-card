"""测试 API 标准：错误响应 & 分页响应。"""

from __future__ import annotations

import pytest

from app.utils.api_standards import error_response, paginated_response


# ══════════════════════════════════════════════════════════════════
# error_response 测试
# ══════════════════════════════════════════════════════════════════


class TestErrorResponse:
    """验证 error_response 格式与一致性。"""

    def test_basic_error_format(self):
        """标准 400 错误应包含 error 嵌套结构。"""
        resp = error_response(400, "BAD_REQUEST", "参数错误")
        assert resp.status_code == 400
        body = resp.body  # JSONResponse.body is bytes
        import json
        data = json.loads(body)
        assert "error" in data
        err = data["error"]
        assert err["code"] == "BAD_REQUEST"
        assert err["message"] == "参数错误"
        assert err["details"] is None
        assert isinstance(err["request_id"], str)
        assert len(err["request_id"]) == 12

    def test_error_with_details(self):
        """details 字段应能携带任意结构化信息。"""
        details = {"field": "email", "reason": "格式不正确"}
        resp = error_response(422, "VALIDATION_ERROR", "校验失败", details=details)
        data = resp.body
        import json
        body = json.loads(data)
        assert body["error"]["details"] == details

    def test_custom_request_id(self):
        """传入的 request_id 应被保留。"""
        resp = error_response(500, "DB_ERROR", "数据库异常", request_id="abc123")
        import json
        body = json.loads(resp.body)
        assert body["error"]["request_id"] == "abc123"

    def test_auto_request_id_generated(self):
        """未提供 request_id 时应自动生成。"""
        resp = error_response(403, "FORBIDDEN", "无权限")
        import json
        body = json.loads(resp.body)
        rid = body["error"]["request_id"]
        assert isinstance(rid, str)
        assert len(rid) == 12  # uuid4().hex[:12]

    def test_different_status_codes(self):
        """不同 status_code 应正确反映在响应中。"""
        codes = [400, 401, 403, 404, 409, 422, 429, 500, 502, 503]
        for sc in codes:
            resp = error_response(sc, f"ERR_{sc}", f"error {sc}")
            assert resp.status_code == sc

    def test_error_code_consistency(self):
        """传递的 code 应与响应中的 error.code 一致。"""
        resp = error_response(400, "RATE_LIMIT_EXCEEDED", "请求过于频繁")
        import json
        body = json.loads(resp.body)
        assert body["error"]["code"] == "RATE_LIMIT_EXCEEDED"


# ══════════════════════════════════════════════════════════════════
# paginated_response 测试
# ══════════════════════════════════════════════════════════════════


class TestPaginatedResponse:
    """验证 paginated_response 分页计算正确性。"""

    def test_basic_pagination(self):
        """正常分页：page=1, page_size=10, total=25 → 3 页。"""
        data = [{"id": i} for i in range(10)]
        result = paginated_response(data, page=1, page_size=10, total=25)
        assert result["data"] == data
        p = result["pagination"]
        assert p["page"] == 1
        assert p["page_size"] == 10
        assert p["total"] == 25
        assert p["total_pages"] == 3

    def test_exact_total_pages(self):
        """正好整除：total=20, page_size=10 → 2 页。"""
        data = [{"id": i} for i in range(10)]
        result = paginated_response(data, page=2, page_size=10, total=20)
        assert result["pagination"]["total_pages"] == 2

    def test_last_page(self):
        """最后一页不足 page_size。"""
        data = [{"id": i} for i in range(3)]
        result = paginated_response(data, page=2, page_size=10, total=13)
        assert len(result["data"]) == 3
        assert result["pagination"]["total_pages"] == 2

    def test_empty_data(self):
        """空数据：total=0 → total_pages=0。"""
        result = paginated_response([], page=1, page_size=20, total=0)
        assert result["data"] == []
        p = result["pagination"]
        assert p["total"] == 0
        assert p["total_pages"] == 0

    def test_single_item(self):
        """单条数据：total=1, page_size=10 → 1 页。"""
        result = paginated_response([{"id": 1}], page=1, page_size=10, total=1)
        assert result["pagination"]["total_pages"] == 1

    def test_page_0_should_clamp_to_1(self):
        """边缘：page=0 应被钳位为 1。"""
        result = paginated_response([], page=0, page_size=10, total=5)
        assert result["pagination"]["page"] == 1
        assert result["pagination"]["total_pages"] == 1

    def test_page_size_0_should_clamp_to_1(self):
        """边缘：page_size=0 应被钳位为 1。"""
        result = paginated_response([{"id": 1}], page=1, page_size=0, total=5)
        assert result["pagination"]["page_size"] == 1
        assert result["pagination"]["total_pages"] == 5

    def test_negative_page_should_clamp_to_1(self):
        """边缘：负数 page 应被钳位为 1。"""
        result = paginated_response([], page=-5, page_size=10, total=10)
        assert result["pagination"]["page"] == 1
        assert result["pagination"]["total_pages"] == 1

    def test_large_total(self):
        """大数据量分页计算正确。"""
        result = paginated_response(list(range(50)), page=1, page_size=50, total=9999)
        assert result["pagination"]["total_pages"] == 200
