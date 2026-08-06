"""AI数智名片 — 核心路由端到端测试"""
import pytest
from unittest.mock import patch, AsyncMock

# ── 路由端到端测试 ──────────────────────────────

class TestBrochureRouter:
    """名片核心路由 — app/routers/brochure.py"""

    @pytest.mark.asyncio
    async def test_create_brochure(self):
        """创建名片应返回完整信息"""
        from app.routers.brochure import create_brochure
        # mock依赖注入
        with patch('app.routers.brochure.BrochureService') as MockService:
            service = MockService.return_value
            service.create.return_value = {"id": "bro_001", "name": "测试名片", "status": "active"}
            result = await create_brochure(
                {"name": "测试名片", "company": "测试公司"},
                user={"id": "user_001"},
                db=AsyncMock()
            )
            assert result is not None
            assert result.get("status") == "active"

    @pytest.mark.asyncio
    async def test_get_brochure_by_id(self):
        """按ID获取名片应返回正确数据"""
        from app.routers.brochure import get_brochure
        with patch('app.routers.brochure.BrochureService') as MockService:
            service = MockService.return_value
            service.get_by_id.return_value = {"id": "bro_001", "name": "测试名片"}
            result = await get_brochure(
                brochure_id="bro_001",
                user={"id": "user_001"},
                db=AsyncMock()
            )
            assert result is not None
            assert result["id"] == "bro_001"

    @pytest.mark.asyncio
    async def test_delete_brochure_unauthorized(self):
        """非拥有者删除名片应被拒绝"""
        from app.routers.brochure import delete_brochure
        with patch('app.routers.brochure.BrochureService') as MockService:
            service = MockService.return_value
            service.get_by_id.return_value = {"id": "bro_001", "owner_id": "other_user"}
            with pytest.raises(PermissionError):
                await delete_brochure(
                    brochure_id="bro_001",
                    user={"id": "user_001"},
                    db=AsyncMock()
                )


class TestMatchRouter:
    """人脉匹配路由 — app/routers/match.py"""

    @pytest.mark.asyncio
    async def test_find_matches(self):
        """找人脉应返回匹配结果列表"""
        from app.routers.match import find_matches
        with patch('app.routers.match.MatchingService') as MockService:
            service = MockService.return_value
            service.find_matches.return_value = [
                {"user_id": "u002", "score": 0.85},
                {"user_id": "u003", "score": 0.72}
            ]
            result = await find_matches(
                user={"id": "user_001"},
                criteria={"industry": "AI", "location": "北京"},
                limit=10
            )
            assert len(result) >= 2
            assert result[0]["score"] >= result[1]["score"]  # 按分数排序

    @pytest.mark.asyncio
    async def test_match_empty_criteria(self):
        """空筛选条件应返回空结果"""
        from app.routers.match import find_matches
        with patch('app.routers.match.MatchingService') as MockService:
            service = MockService.return_value
            service.find_matches.return_value = []
            result = await find_matches(
                user={"id": "user_001"},
                criteria={},
                limit=5
            )
            assert result == []


class TestAIAssistRouter:
    """AI助手路由 — app/routers/ai_assist.py"""

    @pytest.mark.asyncio
    async def test_ai_assist_chat(self):
        """AI对话应返回回复"""
        from app.routers.ai_assist import chat
        with patch('app.routers.ai_assist.AIAssistant') as MockAssistant:
            assistant = MockAssistant.return_value
            assistant.chat.return_value = {"reply": "你好！有什么可以帮你的？", "tokens_used": 15}
            result = await chat(
                user={"id": "user_001"},
                message={"content": "介绍一下名片功能"},
                db=AsyncMock()
            )
            assert "reply" in result
            assert result["tokens_used"] > 0

    @pytest.mark.asyncio
    async def test_ai_assist_empty_message(self):
        """空消息应返回提示"""
        from app.routers.ai_assist import chat
        with patch('app.routers.ai_assist.AIAssistant') as MockAssistant:
            assistant = MockAssistant.return_value
            assistant.chat.return_value = {"reply": "请输入您的问题"}
            result = await chat(
                user={"id": "user_001"},
                message={"content": ""},
                db=AsyncMock()
            )
            assert "reply" in result
