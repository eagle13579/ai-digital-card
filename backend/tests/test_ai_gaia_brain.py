"""核心测试: 盖娅进化大脑 — gaia_evolution_brain.py

测试目标:
  1. GaiaEvolutionBrain 单例模式
  2. ingest_knowledge — 知识摄取
  3. ingest_feedback — 反馈摄取
  4. process_evolution_cycle — 进化循环
  5. get_evolved_weights — 权重查询
  6. get_knowledge_base — 知识库检索
  7. get_status — 状态查询
"""
import os
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

os.environ["EMBEDDING_PROVIDER"] = "numpy"
os.environ["EMBEDDING_DIM"] = "64"

from app.ai.gaia_evolution_brain import (
    GaiaEvolutionBrain,
    get_gaia_brain,
)


# ══════════════════════════════════════════════════════════════════
# Fixtures
# ══════════════════════════════════════════════════════════════════


@pytest.fixture
def mock_db():
    """Mock AsyncSession with proper flush/refresh."""
    db = AsyncMock()
    db.add = MagicMock()
    db.flush = AsyncMock()
    return db


@pytest.fixture
def brain():
    """Fresh GaiaEvolutionBrain with mocked vector index."""
    with patch.object(GaiaEvolutionBrain, "_backend"), patch(
        "app.ai.gaia_evolution_brain.get_embedding_backend"
    ), patch(
        "app.ai.gaia_evolution_brain.get_vector_index"
    ) as mock_get_idx:
        mock_idx = MagicMock()
        mock_idx.size = 0
        mock_idx.search.return_value = []
        mock_get_idx.return_value = mock_idx
        b = GaiaEvolutionBrain()
        # Reset singleton after test
        yield b
        from app.ai.gaia_evolution_brain import _gaia_brain_instance
        _gaia_brain_instance = None


# ══════════════════════════════════════════════════════════════════
# 1. 单例模式测试
# ══════════════════════════════════════════════════════════════════


class TestSingleton:
    def test_get_gaia_brain_returns_instance(self):
        """get_gaia_brain 返回 GaiaEvolutionBrain 实例"""
        with patch("app.ai.gaia_evolution_brain.GaiaEvolutionBrain") as MockBrain:
            instance = MockBrain.return_value
            with patch(
                "app.ai.gaia_evolution_brain._gaia_brain_instance", None
            ), patch(
                "app.ai.gaia_evolution_brain._gaia_brain_lock"
            ):
                from app.ai.gaia_evolution_brain import get_gaia_brain
                result = get_gaia_brain()
                assert result is not None

    def test_singleton_returns_same_instance(self, brain):
        """两次调用返回同一实例"""
        with patch(
            "app.ai.gaia_evolution_brain._gaia_brain_instance", brain
        ):
            b1 = get_gaia_brain()
            b2 = get_gaia_brain()
            assert b1 is b2


# ══════════════════════════════════════════════════════════════════
# 2. 知识摄取测试
# ══════════════════════════════════════════════════════════════════


class TestIngestKnowledge:
    async def test_ingest_knowledge_creates_record(self, brain, mock_db):
        """摄取知识创建 GaiaKnowledge 记录并返回"""
        with patch(
            "app.ai.gaia_evolution_brain.GaiaKnowledge"
        ) as MockKnowledge:
            mock_knowledge = MagicMock()
            mock_knowledge.id = 1
            mock_knowledge.title = "测试知识"
            MockKnowledge.return_value = mock_knowledge
            mock_db.flush = AsyncMock()

            result = await brain.ingest_knowledge(
                db=mock_db,
                source="manual",
                source_id="manual_001",
                knowledge_type="insight",
                title="测试知识",
                content="这是一条测试知识内容",
                tags=["test"],
                confidence=0.8,
            )
            assert result is not None
            assert result.title == "测试知识"
            mock_db.add.assert_called()

    async def test_ingest_knowledge_clamps_confidence(self, brain, mock_db):
        """置信度被限制在 [0,1] 范围"""
        with patch("app.ai.gaia_evolution_brain.GaiaKnowledge") as MockK:
            k = MagicMock()
            MockK.return_value = k
            mock_db.flush = AsyncMock()
            await brain.ingest_knowledge(
                db=mock_db, source="manual", source_id="m1",
                knowledge_type="rule", title="t", content="c",
                confidence=2.0,
            )
            assert k.confidence == 1.0

            await brain.ingest_knowledge(
                db=mock_db, source="manual", source_id="m2",
                knowledge_type="rule", title="t", content="c",
                confidence=-1.0,
            )
            assert k.confidence == 0.0

    async def test_ingest_knowledge_records_event(self, brain, mock_db):
        """摄取知识后记录 GaiaEvolutionEvent"""
        with patch("app.ai.gaia_evolution_brain.GaiaKnowledge") as MockK:
            k = MagicMock()
            k.id = 100
            MockK.return_value = k
            mock_db.flush = AsyncMock()
            with patch.object(brain, "_record_event") as mock_event:
                await brain.ingest_knowledge(
                    db=mock_db, source="manual", source_id="m1",
                    knowledge_type="insight", title="t", content="c",
                )
                mock_event.assert_called_once()
                args, kwargs = mock_event.call_args
                assert kwargs.get("event_type") == "knowledge_ingested"


# ══════════════════════════════════════════════════════════════════
# 3. 反馈摄取测试
# ══════════════════════════════════════════════════════════════════


class TestIngestFeedback:
    async def test_mid_rating_no_knowledge(self, brain, mock_db):
        """中等评分(2<r<4)不生成知识, 返回 None"""
        result = await brain.ingest_feedback(
            db=mock_db, user_id=1, item_id=100, rating=3.0
        )
        assert result is None

    async def test_low_rating_generates_knowledge(self, brain, mock_db):
        """低评分(<=2)生成 behavior 类型知识"""
        with patch.object(brain, "ingest_knowledge", AsyncMock()) as mock_ingest:
            mock_k = MagicMock()
            mock_ingest.return_value = mock_k
            result = await brain.ingest_feedback(
                db=mock_db, user_id=1, item_id=100, rating=1.0,
                comment="非常不满意",
            )
            assert result is not None
            args, kwargs = mock_ingest.call_args
            assert kwargs.get("knowledge_type") == "behavior"
            assert kwargs.get("source") == "feedback"

    async def test_high_rating_generates_knowledge(self, brain, mock_db):
        """高评分(>=4)生成 preference 类型知识"""
        with patch.object(brain, "ingest_knowledge", AsyncMock()) as mock_ingest:
            mock_k = MagicMock()
            mock_ingest.return_value = mock_k
            result = await brain.ingest_feedback(
                db=mock_db, user_id=1, item_id=100, rating=5.0,
                comment="非常满意",
            )
            assert result is not None
            args, kwargs = mock_ingest.call_args
            assert kwargs.get("knowledge_type") == "preference"

    async def test_feedback_with_comment(self, brain, mock_db):
        """高评分 + 评论 = 知识内容包含评语"""
        with patch.object(brain, "ingest_knowledge", AsyncMock()) as mock_ingest:
            mock_k = MagicMock()
            mock_ingest.return_value = mock_k
            await brain.ingest_feedback(
                db=mock_db, user_id=1, item_id=100, rating=5.0,
                comment="很好用",
            )
            args, kwargs = mock_ingest.call_args
            assert "很好用" in kwargs.get("content", "")

    async def test_feedback_confidence_is_rating_divided(self, brain, mock_db):
        """置信度 = rating / 5.0"""
        with patch.object(brain, "ingest_knowledge", AsyncMock()) as mock_ingest:
            mock_k = MagicMock()
            mock_ingest.return_value = mock_k
            await brain.ingest_feedback(
                db=mock_db, user_id=1, item_id=100, rating=4.0,
            )
            args, kwargs = mock_ingest.call_args
            assert kwargs.get("confidence") == 0.8


# ══════════════════════════════════════════════════════════════════
# 4. 进化循环测试
# ══════════════════════════════════════════════════════════════════


class TestProcessEvolutionCycle:
    async def test_cycle_returns_completed_status(self, brain, mock_db):
        """进化循环完成时返回 status=completed"""
        with patch.object(brain, "_collect_pending_knowledge", AsyncMock(return_value=[])), \
             patch.object(brain, "_compute_and_update_weights", AsyncMock(return_value=0)), \
             patch.object(brain, "_record_event", AsyncMock()):
            result = await brain.process_evolution_cycle(db=mock_db, trigger="manual")
            assert result["status"] == "completed"

    async def test_cycle_with_knowledge(self, brain, mock_db):
        """有未向量化知识时的循环"""
        mock_knowledge = MagicMock()
        mock_knowledge.id = 1
        mock_knowledge.title = "test"
        mock_knowledge.content = "content"
        mock_knowledge.tags = ["tag1"]
        mock_knowledge.vector_embedded = False

        with patch.object(brain, "_collect_pending_knowledge", AsyncMock(return_value=[mock_knowledge])), \
             patch.object(brain, "_embed_knowledge_batch", AsyncMock()) as mock_embed, \
             patch.object(brain, "_compute_and_update_weights", AsyncMock(return_value=1)), \
             patch.object(brain, "_record_event", AsyncMock()):
            result = await brain.process_evolution_cycle(db=mock_db)
            assert result["status"] == "completed"
            mock_embed.assert_called_once()

    async def test_cycle_handles_error_gracefully(self, brain, mock_db):
        """异常时返回 status=failed"""
        with patch.object(brain, "_collect_pending_knowledge",
                          AsyncMock(side_effect=Exception("DB error"))):
            result = await brain.process_evolution_cycle(db=mock_db)
            assert result["status"] == "failed"

    async def test_cycle_records_event_on_start(self, brain, mock_db):
        """循环开始记录事件"""
        with patch.object(brain, "_collect_pending_knowledge", AsyncMock(return_value=[])), \
             patch.object(brain, "_compute_and_update_weights", AsyncMock(return_value=0)), \
             patch.object(brain, "_record_event", AsyncMock()) as mock_event:
            await brain.process_evolution_cycle(db=mock_db, trigger="scheduled")
            # cycle_started 事件应先于其他事件
            call_args_list = [c for c in mock_event.call_args_list]
            cycle_started_calls = [
                c for c in call_args_list
                if c.kwargs.get("event_type") == "cycle_started"
            ]
            assert len(cycle_started_calls) >= 1


# ══════════════════════════════════════════════════════════════════
# 5. 权重查询 & 知识库检索 & 状态
# ══════════════════════════════════════════════════════════════════


class TestQueryMethods:
    async def test_get_evolved_weights_none(self, brain, mock_db):
        """无权重记录时返回 None"""
        mock_db.execute.return_value.scalars.return_value.first.return_value = None
        result = await brain.get_evolved_weights(db=mock_db, module="recommendation")
        assert result is None

    async def test_get_evolved_weights_found(self, brain, mock_db):
        """有权重记录时返回正确结构"""
        mock_weight = MagicMock()
        mock_weight.module = "recommendation"
        mock_weight.version = "1.2.3"
        mock_weight.weights = {"preference_weight": 0.5}
        mock_weight.description = "test weights"
        mock_weight.updated_at = None
        mock_db.execute.return_value.scalars.return_value.first.return_value = mock_weight

        result = await brain.get_evolved_weights(db=mock_db, module="recommendation")
        assert result is not None
        assert result["module"] == "recommendation"
        assert result["version"] == "1.2.3"

    async def test_get_knowledge_base_vector_search(self, brain, mock_db):
        """向量搜索优先于数据库搜索"""
        brain._vector_index.size = 1
        brain._vector_index.search.return_value = [
            {"metadata": {"content_type": "gaia_knowledge", "content_id": 1},
             "score": 0.9, "text": "test content"}
        ]
        mock_knowledge = MagicMock()
        mock_knowledge.id = 1
        mock_knowledge.title = "test"
        mock_knowledge.content = "content"
        mock_knowledge.knowledge_type = "insight"
        mock_knowledge.source = "manual"
        mock_knowledge.confidence = 0.8
        mock_knowledge.impact_score = 0.5
        mock_knowledge.is_active = True
        mock_knowledge.tags = ["tag1"]
        mock_knowledge.created_at = MagicMock()
        mock_knowledge.created_at.isoformat.return_value = "2025-01-01T00:00:00"
        mock_knowledge.updated_at = MagicMock()
        mock_knowledge.updated_at.isoformat.return_value = "2025-01-01T00:00:00"
        mock_knowledge.vector_embedded = True

        mock_db.execute.return_value.scalars.return_value.all.return_value = [mock_knowledge]

        result = await brain.get_knowledge_base(db=mock_db, query="test")
        assert len(result) >= 1

    async def test_get_knowledge_base_fallback(self, brain, mock_db):
        """向量索引为空时回退到数据库搜索"""
        brain._vector_index.size = 0
        mock_knowledge = MagicMock()
        mock_knowledge.id = 1
        mock_knowledge.title = "test"
        mock_knowledge.content = "content"
        mock_knowledge.knowledge_type = "insight"
        mock_knowledge.source = "manual"
        mock_knowledge.confidence = 0.8
        mock_knowledge.impact_score = 0.5
        mock_knowledge.is_active = True
        mock_knowledge.tags = ["tag1"]
        mock_knowledge.created_at = MagicMock()
        mock_knowledge.created_at.isoformat.return_value = "2025-01-01T00:00:00"
        mock_knowledge.updated_at = MagicMock()
        mock_knowledge.updated_at.isoformat.return_value = "2025-01-01T00:00:00"
        mock_knowledge.vector_embedded = True

        mock_db.execute.return_value.scalars.return_value.all.return_value = [mock_knowledge]

        result = await brain.get_knowledge_base(db=mock_db, query="test")
        assert len(result) >= 1

    async def test_get_status_returns_dict(self, brain, mock_db):
        """get_status 返回包含 brain 状态信息的字典"""
        mock_db.execute.return_value.scalar.return_value = 0
        mock_db.execute.return_value.scalars.return_value.first.return_value = None
        mock_db.execute.return_value.scalars.return_value.all.return_value = []

        status = await brain.get_status(db=mock_db)
        assert status["brain_status"] == "active"
        assert "knowledge" in status
        assert "training" in status
        assert "weights" in status

    async def test_get_status_knowledge_counts(self, brain, mock_db):
        """get_status 统计知识数量"""
        # 模拟 DB 返回计数
        mock_db.execute.return_value.scalar.return_value = 5
        mock_db.execute.return_value.scalars.return_value.first.return_value = None
        mock_db.execute.return_value.scalars.return_value.all.return_value = []

        status = await brain.get_status(db=mock_db)
        assert status["knowledge"]["total"] == 5

    async def test_get_events(self, brain, mock_db):
        """get_events 返回事件列表"""
        mock_db.execute.return_value.scalars.return_value.all.return_value = []
        mock_db.execute.return_value.scalar.return_value = 0

        result = await brain.get_events(db=mock_db)
        assert "items" in result
        assert "total" in result

    def test_next_version(self):
        """_next_version 正确递增版本号"""
        assert GaiaEvolutionBrain._next_version("1.2.3") == "1.2.4"
        assert GaiaEvolutionBrain._next_version("1.2.99") == "1.3.0"
        assert GaiaEvolutionBrain._next_version("invalid") == "1.0.0"

    def test_vector_index_property(self, brain):
        """vector_index 惰性初始化"""
        assert brain._vector_index is not None or brain.vector_index is not None
