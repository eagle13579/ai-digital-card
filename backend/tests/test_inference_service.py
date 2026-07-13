"""
AI数智名片 — InferenceService 在线推理 API 服务 单元测试

覆盖:
  1. 初始化 (正常 / 降级 / 模型缺失 / PyTorch不可用)
  2. predict() 批量预测 (正常 / 降级 / 空候选 / 用户不存在)
  3. predict_pair() 单对评分 (正常 / 降级 / 用户不存在)
  4. get_embedding() 嵌入提取 (正常 / 降级)
  5. get_model_info() 元数据
  6. 特征计算函数
  7. 资源生命周期 (close, async context manager)

用法:
    cd backend
    pytest tests/test_inference_service.py -v
"""

from __future__ import annotations

import pickle
import tempfile
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import numpy as np
import pytest

# ── 跳过条件 ──
try:
    import torch
    import torch.nn as nn

    TORCH_AVAILABLE = True
except ImportError:
    TORCH_AVAILABLE = False

from app.services.inference_service import (
    ALL_FEATURES,
    OVERLAP_FEATURES,
    SEMANTIC_FEATURES,
    WEIGHT_FEATURES,
    InferenceService,
    MatchScore,
    ThreeTowerModel,
    UserData,
    UserDataLoader,
    build_user_document,
    compute_all_features,
    compute_semantic_similarity,
    compute_tag_overlap_features,
    compute_weight_features,
    validate_feature_dict,
)

# ══════════════════════════════════════════════════════════════════════
# 共享 Fixtures
# ══════════════════════════════════════════════════════════════════════


@pytest.fixture
def sample_user_a() -> UserData:
    """用户 A: 有 provide/need 标签和简介"""
    return UserData(
        user_id=1,
        name="张三",
        company="科技公司",
        title="CTO",
        intro="专注AI技术",
        provide_tags={"Python": 0.9, "AI": 0.8, "大数据": 0.6},
        need_tags={"投资": 0.7, "合作": 0.5},
        brochure_text="AI数智名片平台",
    )


@pytest.fixture
def sample_user_b() -> UserData:
    """用户 B: 与 A 有标签重叠 (需要 AI, 提供 投资)"""
    return UserData(
        user_id=2,
        name="李四",
        company="投资公司",
        title="投资经理",
        intro="寻找AI项目投资",
        provide_tags={"投资": 0.8, "渠道": 0.5},
        need_tags={"AI": 0.9, "Python": 0.6},
        brochure_text="创新投资方案",
    )


@pytest.fixture
def sample_user_c() -> UserData:
    """用户 C: 与 A/B 无共同标签"""
    return UserData(
        user_id=3,
        name="王五",
        company="餐饮公司",
        title="厨师",
        intro="中华美食文化",
        provide_tags={"烹饪": 0.7, "烘焙": 0.6},
        need_tags={"食材": 0.8, "厨师": 0.5},
        brochure_text="美味食谱分享",
    )


@pytest.fixture
def empty_user() -> UserData:
    """最小用户 (无标签、无简介)"""
    return UserData(user_id=99, name="空用户")


@pytest.fixture
def trained_model() -> ThreeTowerModel:
    """返回一个初始化的 ThreeTowerModel (未训练权重)"""
    if not TORCH_AVAILABLE:
        pytest.skip("PyTorch 不可用")
    return ThreeTowerModel()


@pytest.fixture
def model_checkpoint(trained_model: ThreeTowerModel) -> bytes:
    """返回模型 checkpoint 的 pickle bytes"""
    state = {
        "model_state_dict": trained_model.state_dict(),
        "feature_names": ALL_FEATURES,
        "overlap_features": OVERLAP_FEATURES,
        "semantic_features": SEMANTIC_FEATURES,
        "weight_features": WEIGHT_FEATURES,
        "metrics": {"accuracy": 0.85, "f1": 0.82},
    }
    # 不能用 pickle 保存 torch 对象, 直接用 state_dict
    import io

    buf = io.BytesIO()
    torch.save(state, buf)
    buf.seek(0)
    return buf.read()


@pytest.fixture
def scaler_data() -> bytes:
    """返回 scaler 数据的 pickle bytes"""
    data = {
        "overlap_mean": [0.1, 0.2, 0.3, 0.4],
        "overlap_scale": [1.0, 1.1, 1.2, 1.3],
        "semantic_mean": [0.5],
        "semantic_scale": [1.0],
        "weight_mean": [0.1, 0.2, 0.3, 0.4, 0.5],
        "weight_scale": [1.0, 1.1, 1.2, 1.3, 1.4],
    }
    import io

    buf = io.BytesIO()
    np.save(buf, data)
    buf.seek(0)
    return buf.read()


@pytest.fixture
def mock_db_path(tmp_path: Path) -> Path:
    """返回临时数据库目录 (不存在数据库文件, 用于测试降级模式)"""
    return tmp_path / "test_db"


# ══════════════════════════════════════════════════════════════════════
# 测试: 特征计算函数
# ══════════════════════════════════════════════════════════════════════


class TestFeatureComputation:
    """测试特征计算函数 (独立于模型)"""

    def test_compute_tag_overlap_features(self, sample_user_a, sample_user_b):
        """TC-1: 标签重叠特征计算"""
        features = compute_tag_overlap_features(
            sample_user_a.provide_tags,
            sample_user_b.need_tags,
            sample_user_b.provide_tags,
            sample_user_a.need_tags,
        )

        assert "tag_overlap_score" in features
        assert "common_tag_count" in features
        assert "overlap_provide_to_need" in features
        assert "overlap_need_to_provide" in features

        # A提供 Python(0.9),AI(0.8) ∩ B需要 AI(0.9),Python(0.6) → 2 common
        assert features["common_tag_count"] >= 2
        # A需要 投资(0.7),合作(0.5) ∩ B提供 投资(0.8),渠道(0.5) → 1 common
        assert features["overlap_need_to_provide"] > 0
        # Score 应在 [0, 1]
        assert 0.0 <= features["tag_overlap_score"] <= 1.0

    def test_compute_tag_overlap_no_overlap(self, sample_user_a, sample_user_c):
        """TC-2: 无标签重叠"""
        features = compute_tag_overlap_features(
            sample_user_a.provide_tags,
            sample_user_c.need_tags,
            sample_user_c.provide_tags,
            sample_user_a.need_tags,
        )
        assert features["common_tag_count"] == 0
        assert features["overlap_provide_to_need"] == 0.0
        assert features["overlap_need_to_provide"] == 0.0
        assert features["tag_overlap_score"] == 0.0

    def test_compute_tag_overlap_empty_tags(self, empty_user):
        """TC-3: 空标签边界"""
        features = compute_tag_overlap_features(
            empty_user.provide_tags,
            empty_user.need_tags,
            empty_user.provide_tags,
            empty_user.need_tags,
        )
        assert features["common_tag_count"] == 0
        assert features["tag_overlap_score"] == 0.0

    def test_compute_semantic_similarity(self):
        """TC-4: 语义相似度 (Jaccard 降级)"""
        sim = compute_semantic_similarity("AI 技术 投资", "AI 投资 项目", None)
        assert 0.0 <= sim <= 1.0
        # "AI" 和 "投资" 共同出现
        assert sim > 0.0

    def test_compute_semantic_similarity_no_overlap(self):
        """TC-5: 无共同词汇"""
        sim = compute_semantic_similarity("ABCDEF", "GHIJKL", None)
        assert sim == 0.0

    def test_compute_semantic_similarity_empty(self):
        """TC-6: 空文本"""
        assert compute_semantic_similarity("", "AI", None) == 0.0
        assert compute_semantic_similarity("AI", "", None) == 0.0
        assert compute_semantic_similarity("", "", None) == 0.0

    def test_compute_weight_features(self, sample_user_a, sample_user_b):
        """TC-7: 标签权重特征"""
        features = compute_weight_features(sample_user_a, sample_user_b)

        assert "tag_count_a" in features
        assert "tag_count_b" in features
        assert "avg_weight_a" in features
        assert "avg_weight_b" in features
        assert "tag_weight_score" in features

        # A: 3 provide + 2 need = 5; B: 2 provide + 2 need = 4
        assert features["tag_count_a"] == 5.0
        assert features["tag_count_b"] == 4.0

        # 共同标签: A.provide中的AI(0.8)∩B.need中的AI(0.9)=AI, 以及Python(0.9,0.6)
        # A.need中的投资(0.7)∩B.provide中的投资(0.8)=投资
        assert features["tag_weight_score"] > 0.0

    def test_compute_weight_features_empty(self, empty_user):
        """TC-8: 空标签权重边界"""
        features = compute_weight_features(empty_user, empty_user)
        assert features["tag_count_a"] == 0.0
        assert features["tag_count_b"] == 0.0
        assert features["tag_weight_score"] == 0.0

    def test_build_user_document(self, sample_user_a):
        """TC-9: 用户文档构建"""
        doc = build_user_document(sample_user_a)
        assert "张三" not in doc  # name 不包含在文档中
        assert "CTO" in doc  # title
        assert "专注AI技术" in doc  # intro
        assert "科技公司" in doc  # company
        assert "提供" in doc  # tag prefix
        assert "需要" in doc  # tag prefix

    def test_compute_all_features(self, sample_user_a, sample_user_b):
        """TC-10: 全量特征计算"""
        features = compute_all_features(sample_user_a, sample_user_b)
        assert len(features) == len(ALL_FEATURES)
        for name in ALL_FEATURES:
            assert name in features, f"缺少特征: {name}"
            assert isinstance(features[name], float)

    def test_validate_feature_dict(self, sample_user_a, sample_user_b):
        """TC-11: 特征验证"""
        features = compute_all_features(sample_user_a, sample_user_b)
        assert validate_feature_dict(features) is True
        # 缺失字段
        assert validate_feature_dict({}) is False
        assert validate_feature_dict({"tag_overlap_score": 0.5}) is False


# ══════════════════════════════════════════════════════════════════════
# 测试: InferenceService 初始化
# ══════════════════════════════════════════════════════════════════════


class TestInferenceServiceInit:
    """测试初始化和生命周期"""

    @pytest.mark.asyncio
    async def test_init_degraded_no_model(self, tmp_path):
        """TC-12: 模型文件不存在 → 降级模式"""
        svc = InferenceService(
            model_path=tmp_path / "nonexistent.pt",
            db_path=tmp_path / "nonexistent.db",
        )
        await svc.initialize()
        assert svc._initialized
        assert svc._degraded
        assert svc._model is None
        info = svc.get_model_info()
        assert info["degraded"] is True
        assert info["initialized"] is True
        await svc.close()

    @pytest.mark.asyncio
    async def test_predict_degraded_returns_constant(self, tmp_path):
        """TC-13: 降级模式 predict 返回常数 0.5"""
        svc = InferenceService(
            model_path=tmp_path / "nonexistent.pt",
            db_path=tmp_path / "nonexistent.db",
        )
        await svc.initialize()
        results = await svc.predict(user_id=1, candidate_ids=[2, 3])
        assert len(results) == 2
        for r in results:
            assert r["score"] == 0.5
            assert r["user_id"] == 1
        await svc.close()

    @pytest.mark.asyncio
    async def test_predict_degraded_empty_candidates(self, tmp_path):
        """TC-14: 降级模式 + 空候选列表"""
        svc = InferenceService(
            model_path=tmp_path / "nonexistent.pt",
            db_path=tmp_path / "nonexistent.db",
        )
        await svc.initialize()
        results = await svc.predict(user_id=1, candidate_ids=[])
        assert results == []
        await svc.close()

    @pytest.mark.asyncio
    async def test_predict_pair_degraded(self, tmp_path):
        """TC-15: 降级模式 predict_pair"""
        svc = InferenceService(
            model_path=tmp_path / "nonexistent.pt",
            db_path=tmp_path / "nonexistent.db",
        )
        await svc.initialize()
        score = await svc.predict_pair(1, 2)
        assert score == 0.5
        await svc.close()

    @pytest.mark.asyncio
    async def test_get_embedding_degraded(self, tmp_path):
        """TC-16: 降级模式 get_embedding 返回 10 维向量"""
        svc = InferenceService(
            model_path=tmp_path / "nonexistent.pt",
            db_path=tmp_path / "nonexistent.db",
        )
        await svc.initialize()
        emb = await svc.get_embedding(1)
        assert len(emb) == 10
        await svc.close()

    @pytest.mark.asyncio
    async def test_get_model_info_before_init(self):
        """TC-17: 初始化前 get_model_info 返回未初始化状态"""
        svc = InferenceService()
        info = svc.get_model_info()
        assert info["initialized"] is False
        assert info["degraded"] is True

    @pytest.mark.asyncio
    async def test_close_double_safe(self, tmp_path):
        """TC-18: 重复调用 close 不崩溃"""
        svc = InferenceService(
            model_path=tmp_path / "nonexistent.pt",
            db_path=tmp_path / "nonexistent.db",
        )
        await svc.initialize()
        await svc.close()
        await svc.close()  # 第二次调用
        assert svc._initialized is False

    @pytest.mark.asyncio
    async def test_predict_not_initialized(self, tmp_path):
        """TC-19: 未初始化调用 predict 抛出 RuntimeError"""
        svc = InferenceService()
        with pytest.raises(RuntimeError, match="尚未初始化"):
            await svc.predict(1, [2, 3])

    @pytest.mark.asyncio
    async def test_predict_pair_not_initialized(self, tmp_path):
        """TC-20: 未初始化调用 predict_pair 抛出 RuntimeError"""
        svc = InferenceService()
        with pytest.raises(RuntimeError, match="尚未初始化"):
            await svc.predict_pair(1, 2)

    @pytest.mark.asyncio
    async def test_get_embedding_not_initialized(self, tmp_path):
        """TC-21: 未初始化调用 get_embedding 抛出 RuntimeError"""
        svc = InferenceService()
        with pytest.raises(RuntimeError, match="尚未初始化"):
            await svc.get_embedding(1)

    @pytest.mark.asyncio
    async def test_async_context_manager(self, tmp_path):
        """TC-22: async with 上下文管理器"""
        async with InferenceService(
            model_path=tmp_path / "nonexistent.pt",
            db_path=tmp_path / "nonexistent.db",
        ) as svc:
            assert svc._initialized
            info = svc.get_model_info()
            assert info["initialized"] is True
        # 退出后应已释放
        assert svc._initialized is False


# ══════════════════════════════════════════════════════════════════════
# 测试: InferenceService 正常模式 (Mock 模型和数据)
# ══════════════════════════════════════════════════════════════════════


@pytest.mark.skipif(not TORCH_AVAILABLE, reason="PyTorch 不可用")
class TestInferenceServiceNormal:
    """测试正常模式 (mock 模型和数据加载器)"""

    async def _create_mocked_svc(
        self, tmp_path: Path,
    ) -> InferenceService:
        """创建 InferenceService 并注入 mock"""
        svc = InferenceService(
            model_path=str(tmp_path / "model.pt"),
            db_path=str(tmp_path / "mock_db"),
        )

        # Mock data_loader
        mock_loader = AsyncMock(spec=UserDataLoader)

        async def _load_user(uid: int):
            if uid == 1:
                return UserData(
                    user_id=1,
                    name="张三",
                    company="科技公司",
                    title="CTO",
                    intro="AI专家",
                    provide_tags={"AI": 0.9, "Python": 0.8},
                    need_tags={"投资": 0.7},
                    brochure_text="",
                )
            elif uid == 2:
                return UserData(
                    user_id=2,
                    name="李四",
                    company="投资公司",
                    title="经理",
                    intro="寻找AI项目",
                    provide_tags={"投资": 0.8},
                    need_tags={"AI": 0.9, "Python": 0.7},
                    brochure_text="",
                )
            elif uid == 3:
                return UserData(
                    user_id=3,
                    name="王五",
                    company="餐饮公司",
                    title="厨师",
                    intro="美食",
                    provide_tags={"烹饪": 0.7},
                    need_tags={"食材": 0.8},
                    brochure_text="",
                )
            return None

        mock_loader.load_user = _load_user
        svc._data_loader = mock_loader

        # 加载真实模型 (不需要 trained weights, 初始化即可)
        svc._model = ThreeTowerModel()
        svc._model.eval()
        # 不使用 scalers, 直接用原始特征
        svc._scalers = None
        svc._device = "cpu"
        svc._initialized = True
        svc._degraded = False
        svc._model_metadata["initialized"] = True
        svc._model_metadata["degraded"] = False
        svc._model_metadata["device"] = "cpu"

        return svc

    @pytest.mark.asyncio
    async def test_predict_normal(self, tmp_path):
        """TC-23: 正常模式 predict"""
        svc = await self._create_mocked_svc(tmp_path)
        results = await svc.predict(user_id=1, candidate_ids=[2, 3])

        assert len(results) == 2
        for r in results:
            assert "user_id" in r
            assert "candidate_id" in r
            assert "score" in r
            assert "features" in r
            assert 0.0 <= r["score"] <= 1.0

        # 验证特征计算正确性 (不依赖模型权重)
        r2 = next(r for r in results if r["candidate_id"] == 2)
        r3 = next(r for r in results if r["candidate_id"] == 3)

        # 用户2有标签重叠 (AI/Python matching)
        assert r2["features"]["tag_overlap_score"] > r3["features"]["tag_overlap_score"]
        assert r2["features"]["common_tag_count"] > r3["features"]["common_tag_count"]
        assert r2["features"]["tag_weight_score"] > r3["features"]["tag_weight_score"]
        # 语义相似度 (Jaccard降级) 中文无tokenizer时可能为0, 不强制比较

        await svc.close()

    @pytest.mark.asyncio
    async def test_predict_with_top_k(self, tmp_path):
        """TC-24: predict 的 top_k 参数"""
        svc = await self._create_mocked_svc(tmp_path)
        results = await svc.predict(
            user_id=1, candidate_ids=[2, 3], top_k=1
        )
        assert len(results) == 1
        await svc.close()

    @pytest.mark.asyncio
    async def test_predict_nonexistent_user(self, tmp_path):
        """TC-25: 用户不存在返回空列表"""
        svc = await self._create_mocked_svc(tmp_path)
        results = await svc.predict(user_id=999, candidate_ids=[2, 3])
        assert results == []
        await svc.close()

    @pytest.mark.asyncio
    async def test_predict_pair_normal(self, tmp_path):
        """TC-26: predict_pair 正常"""
        svc = await self._create_mocked_svc(tmp_path)
        score = await svc.predict_pair(1, 2)
        assert isinstance(score, float)
        assert 0.0 <= score <= 1.0
        await svc.close()

    @pytest.mark.asyncio
    async def test_predict_pair_nonexistent(self, tmp_path):
        """TC-27: predict_pair 用户不存在返回 0.5"""
        svc = await self._create_mocked_svc(tmp_path)
        score = await svc.predict_pair(1, 999)
        assert score == 0.5
        await svc.close()

    @pytest.mark.asyncio
    async def test_get_embedding_normal(self, tmp_path):
        """TC-28: get_embedding 返回 10 维向量"""
        svc = await self._create_mocked_svc(tmp_path)
        emb = await svc.get_embedding(1)
        assert len(emb) == 10
        # 所有元素应为 float
        for v in emb:
            assert isinstance(v, float)
        await svc.close()

    @pytest.mark.asyncio
    async def test_get_embedding_nonexistent(self, tmp_path):
        """TC-29: get_embedding 用户不存在返回 10 维零向量"""
        svc = await self._create_mocked_svc(tmp_path)
        emb = await svc.get_embedding(999)
        assert len(emb) == 10
        assert emb == [0.0] * 10
        await svc.close()

    @pytest.mark.asyncio
    async def test_get_model_info_after_init(self, tmp_path):
        """TC-30: get_model_info 返回完整元数据"""
        svc = await self._create_mocked_svc(tmp_path)
        info = svc.get_model_info()
        assert info["model_type"] == "ThreeTowerModel"
        assert info["version"] == "1.0.0"
        assert info["initialized"] is True
        assert info["degraded"] is False
        assert "features" in info
        assert "overlap" in info["features"]
        assert "semantic" in info["features"]
        assert "weight" in info["features"]
        await svc.close()


# ══════════════════════════════════════════════════════════════════════
# 测试: ThreeTowerModel
# ══════════════════════════════════════════════════════════════════════


@pytest.mark.skipif(not TORCH_AVAILABLE, reason="PyTorch 不可用")
class TestThreeTowerModel:
    """测试 ThreeTowerModel 基本功能"""

    def test_model_forward(self):
        """TC-31: 前向传播"""
        model = ThreeTowerModel()
        B = 4
        x_o = torch.randn(B, 4)
        x_s = torch.randn(B, 1)
        x_w = torch.randn(B, 5)
        out = model(x_o, x_s, x_w)
        assert out.shape == (B,)
        assert (out >= 0).all() and (out <= 1).all()

    def test_model_predict_numpy(self):
        """TC-32: predict 接受 numpy 输入"""
        model = ThreeTowerModel()
        B = 3
        x_o = np.random.randn(B, 4).astype(np.float32)
        x_s = np.random.randn(B, 1).astype(np.float32)
        x_w = np.random.randn(B, 5).astype(np.float32)
        out = model.predict(x_o, x_s, x_w)
        assert out.shape == (B,)
        assert (out >= 0).all() and (out <= 1).all()

    def test_model_structure(self):
        """TC-33: 模型结构正确"""
        model = ThreeTowerModel()
        # 检查塔结构
        assert hasattr(model, "tower_overlap")
        assert hasattr(model, "tower_semantic")
        assert hasattr(model, "tower_weight")
        assert hasattr(model, "combined")

        # 验证参数数量大于 0
        params = sum(p.numel() for p in model.parameters())
        assert params > 0

    def test_model_same_input_consistent(self):
        """TC-34: 相同输入产生相同输出 (确定性的)"""
        model = ThreeTowerModel()
        model.eval()
        x_o = torch.randn(1, 4)
        x_s = torch.randn(1, 1)
        x_w = torch.randn(1, 5)
        out1 = model(x_o, x_s, x_w)
        out2 = model(x_o, x_s, x_w)
        assert torch.allclose(out1, out2), "相同输入应产生相同输出"


# ══════════════════════════════════════════════════════════════════════
# 测试: MatchScore 数据类
# ══════════════════════════════════════════════════════════════════════


class TestMatchScore:
    """测试 MatchScore 排序"""

    def test_match_score_sorting(self):
        """TC-35: MatchScore 按分数降序排列"""
        scores = [
            MatchScore(user_id=1, candidate_id=3, score=0.7),
            MatchScore(user_id=1, candidate_id=2, score=0.9),
            MatchScore(user_id=1, candidate_id=1, score=0.5),
        ]
        scores.sort(key=lambda r: r.score, reverse=True)
        assert scores[0].candidate_id == 2
        assert scores[1].candidate_id == 3
        assert scores[2].candidate_id == 1

    def test_match_score_details(self):
        """TC-36: MatchScore 携带 details"""
        r = MatchScore(
            user_id=1,
            candidate_id=2,
            score=0.8,
            details={"tag_overlap_score": 0.6},
        )
        assert r.details["tag_overlap_score"] == 0.6
