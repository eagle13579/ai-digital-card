"""画册API路由测试 — CRUD + 发布/分享/删除。"""

from __future__ import annotations

import pytest


BROCHURE_CREATE_PAYLOAD = {
    "title": "测试画册",
    "cover": "https://example.com/cover.jpg",
    "purpose": "partner",
    "pages": [
        {"sort_order": 0, "content_type": "cover", "content": "合作封面页"},
        {"sort_order": 1, "content_type": "text", "content": "团队背景介绍"},
    ],
}


class TestBrochureCreate:
    """创建画册测试"""

    @pytest.mark.asyncio
    async def test_create_brochure_success(self, client, test_db, test_user, auth_headers):
        """创建画册应返回画册详情"""
        resp = await client.post(
            "/api/v1/brochures",
            json=BROCHURE_CREATE_PAYLOAD,
            headers=auth_headers,
        )
        assert resp.status_code == 200, f"创建画册失败: {resp.text}"
        body = resp.json()
        assert body["title"] == "测试画册"
        assert body["purpose"] == "partner"
        assert body["pages_count"] == 2
        assert body["user_id"] == test_user.id

    @pytest.mark.asyncio
    async def test_create_brochure_no_auth(self, client):
        """未登录创建画册应返回 401"""
        resp = await client.post("/api/v1/brochures", json=BROCHURE_CREATE_PAYLOAD)
        assert resp.status_code == 401

    @pytest.mark.asyncio
    async def test_create_brochure_invalid_data(self, client, auth_headers):
        """无效数据创建画册应返回 422"""
        resp = await client.post(
            "/api/v1/brochures",
            json={"title": ""},  # 缺少必要字段
            headers=auth_headers,
        )
        assert resp.status_code == 422


class TestBrochureList:
    """画册列表测试"""

    @pytest.mark.asyncio
    async def test_list_brochures(self, client, test_db, test_user, auth_headers):
        """获取画册列表应返回分页数据"""
        # 先创建一个画册
        await client.post(
            "/api/v1/brochures",
            json=BROCHURE_CREATE_PAYLOAD,
            headers=auth_headers,
        )
        resp = await client.get("/api/v1/brochures", headers=auth_headers)
        assert resp.status_code == 200, f"获取列表失败: {resp.text}"
        body = resp.json()
        assert "items" in body or "data" in body

    @pytest.mark.asyncio
    async def test_list_brochures_no_auth(self, client):
        """未登录获取列表应返回 401"""
        resp = await client.get("/api/v1/brochures")
        assert resp.status_code == 401


class TestBrochureGet:
    """画册详情测试"""

    @pytest.mark.asyncio
    async def test_get_brochure(self, client, test_db, test_user, auth_headers):
        """获取画册详情应返回正确数据"""
        # 先创建
        create_resp = await client.post(
            "/api/v1/brochures",
            json=BROCHURE_CREATE_PAYLOAD,
            headers=auth_headers,
        )
        brochure_id = create_resp.json()["id"]

        # 获取详情
        resp = await client.get(f"/api/v1/brochures/{brochure_id}", headers=auth_headers)
        assert resp.status_code == 200
        body = resp.json()
        assert body["id"] == brochure_id
        assert body["title"] == "测试画册"

    @pytest.mark.asyncio
    async def test_get_nonexistent_brochure(self, client, auth_headers):
        """获取不存在的画册应返回 404"""
        resp = await client.get("/api/v1/brochures/99999", headers=auth_headers)
        assert resp.status_code == 404


class TestBrochureUpdate:
    """画册更新测试"""

    @pytest.mark.asyncio
    async def test_update_brochure(self, client, test_db, test_user, auth_headers):
        """更新画册应返回更新后的数据"""
        create_resp = await client.post(
            "/api/v1/brochures",
            json=BROCHURE_CREATE_PAYLOAD,
            headers=auth_headers,
        )
        brochure_id = create_resp.json()["id"]

        update_payload = {"title": "更新后的画册"}
        resp = await client.put(
            f"/api/v1/brochures/{brochure_id}",
            json=update_payload,
            headers=auth_headers,
        )
        assert resp.status_code == 200
        assert resp.json()["title"] == "更新后的画册"


class TestBrochureShare:
    """画册分享测试"""

    @pytest.mark.asyncio
    async def test_get_share_link(self, client, test_db, test_user, auth_headers):
        """获取分享链接应返回 share_token"""
        create_resp = await client.post(
            "/api/v1/brochures",
            json=BROCHURE_CREATE_PAYLOAD,
            headers=auth_headers,
        )
        brochure_id = create_resp.json()["id"]

        resp = await client.get(
            f"/api/v1/brochures/{brochure_id}/share-link",
            headers=auth_headers,
        )
        assert resp.status_code == 200
        body = resp.json()
        assert "share_token" in body
        assert "share_link" in body
