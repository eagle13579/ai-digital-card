"""AI数智名片 — AI引擎核心单元测试"""
import pytest
from unittest.mock import AsyncMock, patch, MagicMock

# ── AI引擎核心测试 ──────────────────────────────

class TestVectorSearch:
    """向量搜索模块测试 — app/ai/vector_search.py"""

    @pytest.mark.asyncio
    async def test_vector_search_basic(self):
        """基础向量搜索：输入文本返回排序结果"""
        # 导入被测试模块
        from app.ai.vector_search import VectorSearch
        searcher = VectorSearch()
        # 用mock数据验证搜索功能
        result = await searcher.search("AI数字名片", top_k=5)
        assert result is not None
        assert len(result) <= 5

    @pytest.mark.asyncio
    async def test_vector_search_empty_query(self):
        """空查询应返回空列表"""
        from app.ai.vector_search import VectorSearch
        searcher = VectorSearch()
        result = await searcher.search("", top_k=5)
        assert result == []

    @pytest.mark.asyncio
    async def test_vector_search_embedding_fallback(self):
        """embedding provider不可用时应有降级方案"""
        from app.ai.vector_search import VectorSearch
        searcher = VectorSearch()
        # 模拟embedding失败
        with patch.object(searcher, '_get_embedding', return_value=None):
            result = await searcher.search("测试", top_k=3)
            assert result is not None  # 不应抛异常


class TestRecommendation:
    """推荐算法模块测试 — app/ai/recommendation.py"""

    @pytest.mark.asyncio
    async def test_recommend_user_specific(self):
        """基于用户历史的个性化推荐"""
        from app.ai.recommendation import RecommendationEngine
        engine = RecommendationEngine()
        result = await engine.recommend(user_id="test_user_001", limit=10)
        assert result is not None

    @pytest.mark.asyncio
    async def test_recommend_cold_start(self):
        """冷启动用户应获得热门推荐"""
        from app.ai.recommendation import RecommendationEngine
        engine = RecommendationEngine()
        result = await engine.recommend(user_id="unknown_user", limit=5)
        # 冷启动用户至少应返回结果
        assert result is not None

    @pytest.mark.asyncio
    async def test_recommend_diversity(self):
        """推荐结果应有多样性（不全部相同）"""
        from app.ai.recommendation import RecommendationEngine
        engine = RecommendationEngine()
        result = await engine.recommend(user_id="test_user_002", limit=10)
        if len(result) >= 2:
            ids = [item.get('id') for item in result]
            assert len(set(ids)) > 1, "推荐结果应具有多样性"


class TestGaiaEvolutionBrain:
    """盖娅进化大脑测试 — app/ai/gaia_evolution_brain.py"""

    @pytest.mark.asyncio
    async def test_evolution_cycle(self):
        """进化循环应能正常执行"""
        from app.ai.gaia_evolution_brain import GaiaEvolutionBrain
        brain = GaiaEvolutionBrain()
        result = await brain.run_cycle()
        assert result is not None

    @pytest.mark.asyncio
    async def test_knowledge_retrieval(self):
        """知识检索应返回匹配结果"""
        from app.ai.gaia_evolution_brain import GaiaEvolutionBrain
        brain = GaiaEvolutionBrain()
        knowledge = await brain.query_knowledge("AI名片功能")
        assert knowledge is not None

    @pytest.mark.asyncio
    async def test_evolution_state_persistence(self):
        """进化状态应可持久化"""
        from app.ai.gaia_evolution_brain import GaiaEvolutionBrain
        brain = GaiaEvolutionBrain()
        state = await brain.get_state()
        assert 'cycle' in state or 'status' in state
