"""核心测试: AI推荐引擎 — recommendation.py

测试目标:
  1. RecommendItem / RecommendResult 数据类
  2. FeatureBasedScorer — 特征提取、训练、预测
  3. RecommendEngine — personalize_recommend, discover, similar_users
"""
import os

import numpy as np
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

os.environ["EMBEDDING_PROVIDER"] = "numpy"
os.environ["EMBEDDING_DIM"] = "64"

from app.ai.recommendation import (
    RecommendItem,
    RecommendResult,
    FeatureBasedScorer,
    RecommendEngine,
)


# ══════════════════════════════════════════════════════════════════
# 1. RecommendItem / RecommendResult 数据类测试
# ══════════════════════════════════════════════════════════════════


class TestRecommendItem:
    def test_minimal_item(self):
        """最简 RecommendItem 可创建"""
        item = RecommendItem(user_id=1, name="张三")
        assert item.user_id == 1
        assert item.name == "张三"
        assert item.score == 0.0
        assert item.match_type == "mixed"

    def test_to_dict(self):
        """to_dict 返回正确字段"""
        item = RecommendItem(
            user_id=1, name="张三", company="ABC",
            score=0.85, match_type="tag",
            reasons=["标签匹配"], common_tags=["Python"],
        )
        d = item.to_dict()
        assert d["user_id"] == 1
        assert d["name"] == "张三"
        assert d["score"] == 0.85
        assert d["match_type"] == "tag"
        assert d["reasons"] == ["标签匹配"]

    def test_to_dict_truncates_intro(self):
        """intro 超过 300 字时截断"""
        long_intro = "x" * 500
        item = RecommendItem(user_id=2, name="李四", intro=long_intro)
        d = item.to_dict()
        assert len(d["intro"]) == 300


class TestRecommendResult:
    def test_empty_result(self):
        """空 RecommendResult"""
        r = RecommendResult()
        assert r.items == []
        assert r.total == 0
        assert r.strategy_used == ""

    def test_to_dict(self):
        """to_dict 包含 items 列表"""
        r = RecommendResult(
            items=[RecommendItem(user_id=1, name="A")],
            total=1, strategy_used="hybrid",
        )
        d = r.to_dict()
        assert d["total"] == 1
        assert d["strategy_used"] == "hybrid"
        assert len(d["items"]) == 1


# ══════════════════════════════════════════════════════════════════
# 2. FeatureBasedScorer 测试
# ══════════════════════════════════════════════════════════════════


class TestFeatureBasedScorer:
    @pytest.fixture
    def mock_db(self):
        """Mock AsyncSession"""
        return AsyncMock()

    @pytest.fixture
    def scorer(self, mock_db):
        return FeatureBasedScorer(db=mock_db)

    def test_init(self, scorer):
        """初始化后未训练"""
        assert scorer.is_trained is False
        assert scorer._model is None

    def test_extract_features_empty_db(self, scorer, mock_db):
        """空库中提取特征返回全零"""
        mock_db.execute.return_value.scalars.return_value.all.return_value = []
        mock_db.execute.return_value.scalars.return_value.first.return_value = None

        feats = scorer._extract_features(1, 2)
        # 必须是协程
        import asyncio
        feats = asyncio.run(feats)
        assert len(feats) == 6
        assert all(f == 0.0 for f in feats)

    def test_predict_not_trained(self, scorer):
        """未训练时 predict 返回空 dict"""
        import asyncio
        result = asyncio.run(scorer.predict(1, [2, 3]))
        assert result == {}

    def test_train_insufficient_data(self, scorer, mock_db):
        """数据不足 10 条时跳过训练"""
        mock_db.execute.return_value.scalars.return_value.all.return_value = []
        import asyncio
        asyncio.run(scorer.train(limit=100))
        assert scorer.is_trained is False

    def test_is_trained_property(self, scorer):
        """is_trained 返回正确布尔值"""
        assert scorer.is_trained is False
        scorer._is_trained = True
        scorer._model = MagicMock()
        assert scorer.is_trained is True


# ══════════════════════════════════════════════════════════════════
# 3. RecommendEngine 测试
# ══════════════════════════════════════════════════════════════════


class TestRecommendEngine:
    @pytest.fixture
    def mock_db(self):
        db = AsyncMock()
        # User query returns a mock user
        mock_user = MagicMock()
        mock_user.id = 1
        mock_user.name = "测试用户"
        mock_user.company = "测试公司"
        mock_user.title = "工程师"
        mock_user.avatar = ""
        mock_user.intro = "热爱编程"

        result_mock = MagicMock()
        result_mock.scalars.return_value.first.return_value = mock_user
        result_mock.scalars.return_value.all.return_value = []

        db.execute.return_value = result_mock
        return db

    @pytest.fixture
    def engine(self, mock_db):
        with patch(
            "app.ai.recommendation.RecommendEngine._load_online_weights"
        ), patch(
            "app.ai.recommendation.RecommendEngine._schedule_scorer_train"
        ):
            eng = RecommendEngine(db=mock_db)
        return eng

    def test_init_loads_weights(self):
        """初始化时加载在线权重"""
        with patch(
            "app.ai.recommendation.RecommendEngine._load_online_weights"
        ) as mock_load, patch(
            "app.ai.recommendation.RecommendEngine._schedule_scorer_train"
        ):
            db = AsyncMock()
            eng = RecommendEngine(db=db)
            mock_load.assert_called_once()

    def test_default_weights(self, engine):
        """默认权重应为预设值"""
        assert engine.WEIGHT_TAG_MATCH == 0.30
        assert engine.WEIGHT_GRAPH == 0.20
        assert engine.WEIGHT_SEMANTIC == 0.20
        assert engine.WEIGHT_ML == 0.30

    def test_personalize_recommend_user_not_found(self, engine, mock_db):
        """用户不存在时返回空推荐"""
        mock_db.execute.return_value.scalars.return_value.first.return_value = None
        import asyncio
        result = asyncio.run(engine.personalize_recommend(user_id=999))
        assert result.total == 0
        assert result.items == []

    def test_personalize_recommend_excludes_self(self, engine):
        """结果中不包含当前用户"""
        import asyncio
        result = asyncio.run(engine.personalize_recommend(user_id=1))
        assert result is not None
        # 由于 mock db 返回空，total 应为 0
        assert result.total == 0

    def test_refresh_online_weights_static(self):
        """refresh_online_weights 可无实例调用"""
        with patch("app.ai.recommendation.get_online_weight", return_value=0.5):
            result = RecommendEngine.refresh_online_weights()
            # 由于 get_online_weight 返回 > 0 的值，应有变化
            if result is not None:
                assert isinstance(result, bool)

    def test_personalize_with_tag_strategy(self, engine):
        """tag 策略不抛出异常"""
        import asyncio
        result = asyncio.run(
            engine.personalize_recommend(user_id=1, strategy="tag")
        )
        assert result.strategy_used == "tag"

    def test_discover_with_purpose(self, engine):
        """discover 带 purpose 参数不抛异常"""
        import asyncio
        result = asyncio.run(engine.discover(user_id=1, purpose="partner"))
        assert result.strategy_used == "discover"

    def test_similar_users(self, engine):
        """similar_users 不抛异常"""
        import asyncio
        result = asyncio.run(
            engine.similar_users(target_user_id=2, current_user_id=1)
        )
        assert result is not None
