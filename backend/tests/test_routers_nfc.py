"""NFC / 名片分享路由测试 — NFC标签配置 & QR码生成"""

from __future__ import annotations

import pytest


class TestNFCShareRoutes:
    """NFC 名片分享路由集成测试"""

    @pytest.mark.asyncio
    async def test_share_nfc_endpoint_exists_and_returns_json(self, client, test_db):
        """GET /share/nfc/{token} 应返回 200 + NFC NDEF JSON"""
        # 先创建一个已发布的 brochure
        from app.models.brochure import Brochure

        brochure = Brochure(
            user_id=1,
            title="测试名片",
            status="published",
            share_token="test_share_token_nfc_001",
        )
        test_db.add(brochure)
        await test_db.commit()

        resp = await client.get("/share/nfc/test_share_token_nfc_001")
        assert resp.status_code == 200, f"NFC 接口返回非 200: {resp.text}"
        body = resp.json()
        assert "share_url" in body
        assert "share_token" in body
        assert "ndef_records" in body
        assert len(body["ndef_records"]) > 0
        assert body["ndef_records"][0]["type"] == "uri"

    @pytest.mark.asyncio
    async def test_share_nfc_invalid_token_returns_404(self, client):
        """不存在的 share_token 应返回 404"""
        resp = await client.get("/share/nfc/nonexistent_token")
        assert resp.status_code == 404

    @pytest.mark.asyncio
    async def test_share_nfc_draft_brochure_returns_404(self, client, test_db):
        """未发布(draft)的名片 NFC 应返回 404"""
        from app.models.brochure import Brochure

        brochure = Brochure(
            user_id=1,
            title="草稿名片",
            status="draft",
            share_token="draft_share_token_nfc",
        )
        test_db.add(brochure)
        await test_db.commit()

        resp = await client.get("/share/nfc/draft_share_token_nfc")
        assert resp.status_code == 404

    @pytest.mark.asyncio
    async def test_share_nfc_ndef_record_format(self, client, test_db):
        """NFC NDEF 记录格式应包含 uri 和 android_aar"""
        from app.models.brochure import Brochure

        brochure = Brochure(
            user_id=1,
            title="NFC格式测试",
            status="published",
            share_token="nfc_format_test_token",
        )
        test_db.add(brochure)
        await test_db.commit()

        resp = await client.get("/share/nfc/nfc_format_test_token")
        assert resp.status_code == 200
        body = resp.json()

        # 检查NDEF记录结构
        assert isinstance(body["ndef_records"], list)
        assert body["ndef_records"][0]["uri"].startswith("http")
        assert "android_aar" in body
        assert "package_name" in body["android_aar"]
        assert "mime_type" in body
        assert body["mime_type"] == "application/vnd.nfc.ndef"

    @pytest.mark.asyncio
    async def test_share_qr_code_generation(self, client, test_db):
        """GET /share/qr/{token} 应返回 PNG 图片"""
        from app.models.brochure import Brochure

        brochure = Brochure(
            user_id=1,
            title="QR测试名片",
            status="published",
            share_token="qr_test_token_001",
        )
        test_db.add(brochure)
        await test_db.commit()

        resp = await client.get("/share/qr/qr_test_token_001")
        assert resp.status_code == 200
        # Content-Type 应为 image/png
        content_type = resp.headers.get("content-type", "")
        assert "image/png" in content_type or "image" in content_type
        # 响应体应有二进制数据
        assert len(resp.content) > 100

    @pytest.mark.asyncio
    async def test_share_qr_invalid_token_returns_404(self, client):
        """不存在的 share_token 请求 QR 码应返回 404"""
        resp = await client.get("/share/qr/invalid_qr_token")
        assert resp.status_code == 404

    @pytest.mark.asyncio
    async def test_vcard_generation_via_share_service(self):
        """generate_nfc_ndef_record 应生成完整 vCard 兼容数据结构"""
        from app.services.share_service import generate_nfc_ndef_record

        result = generate_nfc_ndef_record("test_vcard_token")
        assert result["share_token"] == "test_vcard_token"
        assert result["share_url"].endswith("/view/test_vcard_token")
        assert len(result["ndef_message"]) > 0
        # NDEF message 应该有 URI 记录
        assert any(msg["type"] == "U" for msg in result["ndef_message"])
