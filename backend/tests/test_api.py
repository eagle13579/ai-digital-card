"""
API endpoint tests for AI Digital Business Card.

Tests cover:
- Health check
- User registration & login
- Brochure CRUD
- Brochure publish & share
- Tag CRUD
- Trust network
- Visitor logging

Each test uses an isolated in-memory SQLite database via conftest fixtures.
"""

import pytest
from fastapi import status


# ── Health Check ─────────────────────────────────────────────────────────────

class TestHealth:
    def test_health_endpoint(self, client):
        """GET /health should return 200 with status ok."""
        resp = client.get("/health")
        assert resp.status_code == status.HTTP_200_OK
        data = resp.json()
        assert data["status"] == "ok"
        assert "AI数字名片" in data.get("app", "")

    def test_api_health_endpoint(self, client):
        """GET /api/health should return 200 with status ok."""
        resp = client.get("/api/health")
        assert resp.status_code == status.HTTP_200_OK
        data = resp.json()
        assert data["status"] == "ok"


# ── Auth / Registration & Login ──────────────────────────────────────────────

class TestAuth:
    REGISTER_URL = "/api/auth/register"
    LOGIN_URL = "/api/auth/login"

    def test_register_success(self, client):
        """POST /api/auth/register should return 200 with token."""
        payload = {
            "phone": "13812345678",
            "password": "securepass",
            "name": "张三",
            "company": "示例科技",
            "title": "工程师",
        }
        resp = client.post(self.REGISTER_URL, json=payload)
        assert resp.status_code in (200, 201)
        data = resp.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
        assert data["user"]["name"] == "张三"
        assert data["user"]["phone"] == "13812345678"

    def test_register_duplicate_phone(self, client, test_user):
        """Registering with an existing phone should return 400."""
        payload = {
            "phone": "13800138000",
            "password": "anotherpass",
            "name": "李四",
        }
        resp = client.post(self.REGISTER_URL, json=payload)
        assert resp.status_code == status.HTTP_400_BAD_REQUEST

    def test_login_success(self, client, test_user):
        """POST /api/auth/login should return 200 with token."""
        payload = {"phone": "13800138000", "password": "testpass123"}
        resp = client.post(self.LOGIN_URL, json=payload)
        assert resp.status_code == status.HTTP_200_OK
        data = resp.json()
        assert "access_token" in data
        assert data["user"]["name"] == "测试用户"

    def test_login_wrong_password(self, client, test_user):
        """Login with wrong password should return 401."""
        payload = {"phone": "13800138000", "password": "wrongpass"}
        resp = client.post(self.LOGIN_URL, json=payload)
        assert resp.status_code == status.HTTP_401_UNAUTHORIZED

    def test_login_nonexistent_user(self, client):
        """Login with unregistered phone should return 401."""
        payload = {"phone": "19900000000", "password": "somepass"}
        resp = client.post(self.LOGIN_URL, json=payload)
        assert resp.status_code == status.HTTP_401_UNAUTHORIZED


# ── Brochure CRUD ───────────────────────────────────────────────────────────

class TestBrochure:
    BASE_URL = "/api/brochures"

    def test_create_brochure(self, client, auth_headers):
        """POST /api/brochures should create a brochure and return 201."""
        payload = {
            "title": "我的数字名片",
            "cover": "https://example.com/cover.jpg",
            "pages": [
                {"sort_order": 0, "content_type": "text", "content": "欢迎来到我的名片"},
                {"sort_order": 1, "content_type": "text", "content": "第二页内容"},
            ],
        }
        resp = client.post(self.BASE_URL, json=payload, headers=auth_headers)
        assert resp.status_code in (200, 201)
        data = resp.json()
        assert data["title"] == "我的数字名片"
        assert data["status"] == "draft"
        assert len(data["pages"]) == 2

    def test_create_brochure_without_auth(self, client):
        """Creating a brochure without auth should return 401."""
        payload = {"title": "无权限名片", "pages": []}
        resp = client.post(self.BASE_URL, json=payload)
        assert resp.status_code == status.HTTP_401_UNAUTHORIZED

    def test_list_brochures(self, client, auth_headers, test_user, test_db):
        """GET /api/brochures should return the brochures list."""
        # Create a brochure first
        from app.models.brochure import Brochure
        brochure = Brochure(user_id=test_user.id, title="测试列表")
        test_db.add(brochure)
        test_db.commit()

        resp = client.get(self.BASE_URL, headers=auth_headers)
        assert resp.status_code == status.HTTP_200_OK
        data = resp.json()
        assert isinstance(data, list)
        assert any(b["title"] == "测试列表" for b in data)

    def test_get_brochure_by_id(self, client, auth_headers, test_user, test_db):
        """GET /api/brochures/{id} should return the brochure."""
        from app.models.brochure import Brochure
        brochure = Brochure(user_id=test_user.id, title="详情测试")
        test_db.add(brochure)
        test_db.commit()

        resp = client.get(f"{self.BASE_URL}/{brochure.id}", headers=auth_headers)
        assert resp.status_code == status.HTTP_200_OK
        assert resp.json()["title"] == "详情测试"

    def test_get_nonexistent_brochure(self, client, auth_headers):
        """GET /api/brochures/99999 should return 404."""
        resp = client.get(f"{self.BASE_URL}/99999", headers=auth_headers)
        assert resp.status_code == status.HTTP_404_NOT_FOUND

    def test_delete_brochure(self, client, auth_headers, test_user, test_db):
        """DELETE /api/brochures/{id} should delete and return success."""
        from app.models.brochure import Brochure
        brochure = Brochure(user_id=test_user.id, title="待删除")
        test_db.add(brochure)
        test_db.commit()

        resp = client.delete(f"{self.BASE_URL}/{brochure.id}", headers=auth_headers)
        assert resp.status_code == status.HTTP_200_OK

        # Verify it's gone
        resp2 = client.get(f"{self.BASE_URL}/{brochure.id}", headers=auth_headers)
        assert resp2.status_code == status.HTTP_404_NOT_FOUND


# ── Brochure Publish & Share ─────────────────────────────────────────────────

class TestBrochurePublishShare:
    BASE_URL = "/api/brochures"

    def test_publish_brochure(self, client, auth_headers, test_user, test_db):
        """POST /api/brochures/{id}/publish should set status to 'published'."""
        from app.models.brochure import Brochure
        brochure = Brochure(user_id=test_user.id, title="发布测试")
        test_db.add(brochure)
        test_db.commit()

        resp = client.post(f"{self.BASE_URL}/{brochure.id}/publish", headers=auth_headers)
        assert resp.status_code == status.HTTP_200_OK
        data = resp.json()
        assert data["status"] == "published"
        assert len(data["share_token"]) > 0

    def test_publish_others_brochure(self, client, auth_headers, test_db, second_user):
        """Publishing another user's brochure should return 403."""
        from app.models.brochure import Brochure
        brochure = Brochure(user_id=second_user.id, title="别人的画册")
        test_db.add(brochure)
        test_db.commit()

        resp = client.post(f"{self.BASE_URL}/{brochure.id}/publish", headers=auth_headers)
        assert resp.status_code == status.HTTP_403_FORBIDDEN

    def test_get_shared_brochure(self, client, test_user, test_db):
        """GET /api/brochures/share/{token} should return the brochure publicly."""
        from app.models.brochure import Brochure
        brochure = Brochure(
            user_id=test_user.id,
            title="分享测试",
            status="published",
            share_token="testsharetoken123",
        )
        test_db.add(brochure)
        test_db.commit()

        resp = client.get(f"{self.BASE_URL}/share/testsharetoken123")
        assert resp.status_code == status.HTTP_200_OK
        assert resp.json()["title"] == "分享测试"

    def test_get_shared_brochure_invalid_token(self, client):
        """GET /api/brochures/share/{invalid_token} should return 404."""
        resp = client.get(f"{self.BASE_URL}/share/nonexistenttoken")
        assert resp.status_code == status.HTTP_404_NOT_FOUND


# ── Tag CRUD ─────────────────────────────────────────────────────────────────

class TestTags:
    BASE_URL = "/api/tags"

    def test_get_my_tags_empty(self, client, auth_headers):
        """GET /api/tags/me should return empty lists initially."""
        resp = client.get(f"{self.BASE_URL}/me", headers=auth_headers)
        assert resp.status_code == status.HTTP_200_OK
        data = resp.json()
        assert data["provide"] == []
        assert data["need"] == []

    def test_add_tags(self, client, auth_headers):
        """POST /api/tags/me should add tags and return them."""
        payload = {
            "tags": [
                {"tag": "Python开发", "weight": 1.0},
                {"tag": "全栈工程师", "weight": 0.8},
            ],
            "tag_type": "provide",
            "source": "manual",
        }
        resp = client.post(f"{self.BASE_URL}/me", json=payload, headers=auth_headers)
        assert resp.status_code == status.HTTP_200_OK
        data = resp.json()
        assert len(data) == 2
        assert data[0]["tag_type"] == "provide"

    def test_add_and_retrieve_tags(self, client, auth_headers):
        """After adding tags, GET /api/tags/me should include them."""
        payload = {
            "tags": [{"tag": "数据分析", "weight": 0.9}],
            "tag_type": "need",
            "source": "manual",
        }
        client.post(f"{self.BASE_URL}/me", json=payload, headers=auth_headers)

        resp = client.get(f"{self.BASE_URL}/me", headers=auth_headers)
        data = resp.json()
        assert len(data["need"]) == 1
        assert data["need"][0]["tag"] == "数据分析"

    def test_delete_tag(self, client, auth_headers, test_user, test_db):
        """DELETE /api/tags/me/{tag_id} should delete the tag."""
        from app.models.tag import UserTag
        tag = UserTag(user_id=test_user.id, tag_type="provide", tag="待删除标签")
        test_db.add(tag)
        test_db.commit()

        resp = client.delete(f"{self.BASE_URL}/me/{tag.id}", headers=auth_headers)
        assert resp.status_code == status.HTTP_200_OK

        # Verify deletion
        resp2 = client.get(f"{self.BASE_URL}/me", headers=auth_headers)
        assert resp2.json()["provide"] == []

    def test_get_user_tags(self, client, test_user, test_db):
        """GET /api/tags/users/{user_id} should return tags for any user."""
        from app.models.tag import UserTag
        tag = UserTag(user_id=test_user.id, tag_type="provide", tag="公开标签")
        test_db.add(tag)
        test_db.commit()

        resp = client.get(f"{self.BASE_URL}/users/{test_user.id}")
        assert resp.status_code == status.HTTP_200_OK
        data = resp.json()
        assert len(data["provide"]) == 1


# ── Trust Network ────────────────────────────────────────────────────────────

class TestTrustNetwork:
    BASE_URL = "/api/trust"

    def test_get_empty_network(self, client, auth_headers):
        """GET /api/trust/network should return empty lists."""
        resp = client.get(f"{self.BASE_URL}/network", headers=auth_headers)
        assert resp.status_code == status.HTTP_200_OK
        data = resp.json()
        assert data["trusting"] == []
        assert data["trusted_by"] == []

    def test_add_trust(self, client, auth_headers, test_db, second_user):
        """POST /api/trust/network should create trust relationship."""
        payload = {"trusted_user_id": second_user.id}
        resp = client.post(f"{self.BASE_URL}/network", json=payload, headers=auth_headers)
        assert resp.status_code == status.HTTP_200_OK
        data = resp.json()
        assert data["trusted_user_id"] == second_user.id

    def test_add_trust_self(self, client, auth_headers, test_user):
        """Adding trust to self should return 400."""
        payload = {"trusted_user_id": test_user.id}
        resp = client.post(f"{self.BASE_URL}/network", json=payload, headers=auth_headers)
        assert resp.status_code == status.HTTP_400_BAD_REQUEST

    def test_add_duplicate_trust(self, client, auth_headers, test_db, second_user):
        """Adding duplicate trust should return 400."""
        from app.models.trust import TrustNetwork
        trust = TrustNetwork(user_id=test_user.id, trusted_user_id=second_user.id)
        test_db.add(trust)
        test_db.commit()

        payload = {"trusted_user_id": second_user.id}
        resp = client.post(f"{self.BASE_URL}/network", json=payload, headers=auth_headers)
        assert resp.status_code == status.HTTP_400_BAD_REQUEST

    def test_remove_trust(self, client, auth_headers, test_db, second_user):
        """DELETE /api/trust/network/{trusted_user_id} should remove trust."""
        from app.models.trust import TrustNetwork
        trust = TrustNetwork(user_id=test_user.id, trusted_user_id=second_user.id)
        test_db.add(trust)
        test_db.commit()

        resp = client.delete(f"{self.BASE_URL}/network/{second_user.id}", headers=auth_headers)
        assert resp.status_code == status.HTTP_200_OK

        resp2 = client.get(f"{self.BASE_URL}/network", headers=auth_headers)
        assert resp2.json()["trusting"] == []

    def test_trust_network_endpoint_without_auth(self, client):
        """Trust endpoints should require authentication."""
        resp = client.get(f"{self.BASE_URL}/network")
        assert resp.status_code == status.HTTP_401_UNAUTHORIZED


# ── User Profile ─────────────────────────────────────────────────────────────

class TestUserProfile:
    BASE_URL = "/api/users"

    def test_get_my_profile(self, client, auth_headers, test_user):
        """GET /api/users/me should return the current user's profile."""
        resp = client.get(f"{self.BASE_URL}/me", headers=auth_headers)
        assert resp.status_code == status.HTTP_200_OK
        data = resp.json()
        assert data["name"] == test_user.name
        assert data["phone"] == test_user.phone

    def test_update_profile(self, client, auth_headers):
        """PUT /api/users/me should update user profile."""
        payload = {"name": "新名字", "title": "高级工程师"}
        resp = client.put(f"{self.BASE_URL}/me", json=payload, headers=auth_headers)
        assert resp.status_code == status.HTTP_200_OK
        data = resp.json()
        assert data["name"] == "新名字"
        assert data["title"] == "高级工程师"

    def test_get_user_by_id(self, client, test_user, test_db):
        """GET /api/users/{user_id} should return user info (public)."""
        resp = client.get(f"{self.BASE_URL}/{test_user.id}")
        assert resp.status_code == status.HTTP_200_OK
        data = resp.json()
        assert data["name"] == test_user.name
