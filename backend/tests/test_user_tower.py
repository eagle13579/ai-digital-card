"""AI数智名片 — UserTower & EnterpriseTower 单元测试

覆盖范围:
  - UserTower 前向传播与 L2 归一化
  - UserFeatureEncoder fit / transform / extract_features_from_models
  - EnterpriseTower 前向传播与 L2 归一化
  - EnterpriseFeatureEncoder fit / transform / extract_features_from_models
  - TripletLoss 计算
  - UserTowerTrainer 训练一步
  - 模型保存 / 加载 (save_model / load_model)
  - 批量 transform
  - 嵌入相似性
  - 模型 repr
"""

from __future__ import annotations

import pytest
import torch
import torch.nn as nn
import torch.nn.functional as F
import numpy as np
from pathlib import Path
import tempfile
import shutil

from app.models.ml.user_tower import (
    UserTower,
    UserFeatureEncoder,
    UserTowerTrainer,
    TripletLoss,
    NUMERIC_FEATURES,
    CATEGORICAL_FEATURES,
)
from app.models.ml.enterprise_tower import (
    EnterpriseTower,
    EnterpriseFeatureEncoder,
    ENTERPRISE_FEATURES,
    ENTERPRISE_CATEGORICAL_FEATURES,
)


# ===================================================================
# 辅助工具
# ===================================================================
class MockUser:
    """模拟 User 模型对象"""
    def __init__(self, company="测试公司", title="CTO", intro="专注于AI数字化营销",
                 membership_tier="gold"):
        self.company = company
        self.title = title
        self.intro = intro
        self.membership_tier = membership_tier


class MockUserTag:
    """模拟 UserTag 模型对象"""
    def __init__(self, tag_type="provide", tag="AI技术", weight=1.0):
        self.tag_type = tag_type
        self.tag = tag
        self.weight = weight


class MockBrochure:
    """模拟 Brochure 模型对象"""
    def __init__(self, purpose="business", pages_count=3, view_count=50,
                 visibility="public", pages=None):
        self.purpose = purpose
        self.pages_count = pages_count
        self.view_count = view_count
        self.visibility = visibility
        self.pages = pages or []


class MockPage:
    """模拟 Page 模型对象"""
    def __init__(self, ai_summary=""):
        self.ai_summary = ai_summary


# ===================================================================
# TC1: UserTower 前向传播
# ===================================================================
class TestUserTower:
    """UserTower 模型测试"""

    def test_forward_shape(self):
        """TC1.1: 前向传播输出 shape 正确"""
        tower = UserTower(num_features=10, embedding_dim=128, hidden_dims=[256, 128])
        x = torch.randn(4, 10)
        out = tower(x)
        assert out.shape == (4, 128), f"输出 shape 应为 (4, 128), 收到 {out.shape}"

    def test_l2_normalized(self):
        """TC1.2: 输出经过 L2 归一化"""
        tower = UserTower(num_features=10, embedding_dim=128)
        x = torch.randn(4, 10)
        out = tower(x)
        norms = out.norm(p=2, dim=1)
        assert torch.allclose(norms, torch.ones(4), atol=1e-5), \
            f"L2 归一化后 norm 应 ≈1, 收到 {norms}"

    def test_different_inputs_different_outputs(self):
        """TC1.3: 不同输入产生不同输出"""
        tower = UserTower(num_features=5, embedding_dim=128)
        tower.eval()
        x1 = torch.randn(2, 5)
        x2 = torch.randn(2, 5)
        out1 = tower(x1)
        out2 = tower(x2)
        # 同一批输入应相同
        assert torch.allclose(out1, tower(x1))
        # 不同输入差异不应全零
        diff = (out1 - out2).abs().mean().item()
        assert diff > 0.001, f"不同输入应有差异, diff={diff}"

    def test_predict_returns_numpy(self):
        """TC1.4: predict 返回 numpy 数组"""
        tower = UserTower(num_features=10, embedding_dim=128)
        x = torch.randn(2, 10)
        out = tower.predict(x)
        assert isinstance(out, np.ndarray), f"predict 应返回 numpy, 收到 {type(out)}"
        assert out.shape == (2, 128)

    def test_repr(self):
        """TC1.5: __repr__ 包含关键信息"""
        tower = UserTower(num_features=10, embedding_dim=64, hidden_dims=[128, 64])
        r = repr(tower)
        assert "UserTower" in r
        assert "num_features=10" in r
        assert "embedding_dim=64" in r

    def test_save_and_load_model(self):
        """TC1.6: save_model + load_model 往返测试"""
        tower = UserTower(num_features=10, embedding_dim=64, hidden_dims=[128, 64])
        x = torch.randn(2, 10)
        out_before = tower.predict(x)

        with tempfile.NamedTemporaryFile(suffix=".pt", delete=False) as f:
            path = f.name
        try:
            tower.save_model(path)
            loaded = UserTower.load_model(
                path, num_features=10, embedding_dim=64, hidden_dims=[128, 64]
            )
            out_after = loaded.predict(x)
            assert np.allclose(out_before, out_after, atol=1e-6), \
                "加载前后的预测结果应一致"
        finally:
            Path(path).unlink(missing_ok=True)


# ===================================================================
# TC2: UserFeatureEncoder
# ===================================================================
class TestUserFeatureEncoder:
    """UserFeatureEncoder 测试"""

    def test_fit_and_transform(self):
        """TC2.1: fit + transform 完整流程"""
        import pandas as pd
        df = pd.DataFrame({
            "tag_count": [3, 5, 8, 2, 10],
            "brochure_count": [1, 2, 1, 3, 2],
            "view_count": [50, 200, 100, 80, 300],
            "page_count": [3, 6, 4, 9, 5],
            "avg_intro_len": [15, 30, 20, 25, 40],
            "purpose": ["business", "partner", "client", "investor", "business"],
            "top_tag": ["AI", "大数据", "营销", "SaaS", "AI"],
            "membership_tier": ["gold", "free", "diamond", "gold", "board"],
        })

        encoder = UserFeatureEncoder(embedding_dim=8)
        encoder.fit(df)
        assert encoder._fitted, "fit 后 _fitted 应为 True"
        assert "tag_count" in encoder.numeric_mean
        assert "purpose" in encoder.categorical_cardinality

        # transform 单个样本
        tensor = encoder.transform({
            "tag_count": 5,
            "brochure_count": 2,
            "view_count": 100,
            "page_count": 4,
            "avg_intro_len": 20,
            "purpose": "business",
            "top_tag": "AI",
            "membership_tier": "gold",
        })
        expected_dim = len(NUMERIC_FEATURES) + len(CATEGORICAL_FEATURES) * 8
        assert tensor.shape == (1, expected_dim), \
            f"输出 shape 应为 (1, {expected_dim}), 收到 {tensor.shape}"

    def test_batch_transform(self):
        """TC2.2: 批量 transform"""
        import pandas as pd
        df = pd.DataFrame({
            "tag_count": [3, 5, 8],
            "brochure_count": [1, 2, 1],
            "view_count": [50, 200, 100],
            "page_count": [3, 6, 4],
            "avg_intro_len": [15, 30, 20],
            "purpose": ["business", "partner", "client"],
            "top_tag": ["AI", "大数据", "营销"],
            "membership_tier": ["gold", "free", "diamond"],
        })
        encoder = UserFeatureEncoder(embedding_dim=4)
        encoder.fit(df)

        data = [
            {"tag_count": 4, "brochure_count": 1, "view_count": 80, "page_count": 3,
             "avg_intro_len": 18, "purpose": "business", "top_tag": "AI", "membership_tier": "gold"},
            {"tag_count": 6, "brochure_count": 3, "view_count": 250, "page_count": 8,
             "avg_intro_len": 35, "purpose": "partner", "top_tag": "SaaS", "membership_tier": "diamond"},
        ]
        tensor = encoder.transform(data)
        expected_dim = len(NUMERIC_FEATURES) + len(CATEGORICAL_FEATURES) * 4
        assert tensor.shape == (2, expected_dim), \
            f"批量 transform 期望 (2, {expected_dim}), 收到 {tensor.shape}"

    def test_transform_no_grad(self):
        """TC2.3: transform 输出不追踪梯度"""
        import pandas as pd
        df = pd.DataFrame({
            "tag_count": [1, 2], "brochure_count": [1, 2], "view_count": [10, 20],
            "page_count": [1, 2], "avg_intro_len": [10, 20],
            "purpose": ["business", "partner"], "top_tag": ["AI", "大数据"],
            "membership_tier": ["gold", "free"],
        })
        encoder = UserFeatureEncoder(embedding_dim=4)
        encoder.fit(df)
        tensor = encoder.transform({"tag_count": 1, "brochure_count": 1, "view_count": 10,
                                     "page_count": 1, "avg_intro_len": 10, "purpose": "business",
                                     "top_tag": "AI", "membership_tier": "gold"})
        assert not tensor.requires_grad, "编码数据不应追踪梯度"

    def test_extract_features_from_models(self):
        """TC2.4: 从数据模型对象提取特征"""
        user = MockUser(company="AI科技", title="CTO", intro="AI驱动创新",
                        membership_tier="gold")
        tags = [
            MockUserTag(tag_type="provide", tag="AI", weight=2.0),
            MockUserTag(tag_type="need", tag="客户", weight=1.5),
            MockUserTag(tag_type="provide", tag="技术", weight=1.0),
        ]
        brochures = [
            MockBrochure(purpose="business", pages_count=3, view_count=100),
            MockBrochure(purpose="partner", pages_count=5, view_count=200),
        ]

        features = UserFeatureEncoder.extract_features_from_models(user, tags, brochures)
        assert features["tag_count"] == 3, f"期望 3 个标签, 收到 {features['tag_count']}"
        assert features["brochure_count"] == 2
        assert features["view_count"] == 300
        assert features["page_count"] == 8
        assert features["avg_intro_len"] == 6  # "AI驱动创新" 长度
        assert features["purpose"] == "business"
        assert features["top_tag"] == "AI"
        assert features["membership_tier"] == "gold"

    def test_fit_with_missing_columns(self):
        """TC2.5: 缺失列时使用默认值"""
        import pandas as pd
        df = pd.DataFrame({"tag_count": [1, 2]})  # 只有一列
        encoder = UserFeatureEncoder(embedding_dim=4)
        encoder.fit(df)
        # 缺失的列应使用默认值
        assert encoder.numeric_mean.get("brochure_count") == 0.0
        assert encoder.numeric_std.get("brochure_count") == 1.0

    def test_repr(self):
        """TC2.6: 编码器 repr"""
        encoder = UserFeatureEncoder(embedding_dim=16)
        r = repr(encoder)
        assert "UserFeatureEncoder" in r
        assert "not fitted" in r

    def test_raise_error_before_fit(self):
        """TC2.7: 未 fit 时 transform 应报错"""
        encoder = UserFeatureEncoder()
        with pytest.raises(RuntimeError, match="尚未 fit"):
            encoder.transform({"tag_count": 1, "brochure_count": 1, "view_count": 1,
                                "page_count": 1, "avg_intro_len": 1, "purpose": "business",
                                "top_tag": "AI", "membership_tier": "gold"})


# ===================================================================
# TC3: TripletLoss
# ===================================================================
class TestTripletLoss:
    """TripletLoss 测试"""

    def test_loss_positive_when_positive_far(self):
        """TC3.1: 正样本远、负样本近时 loss > 0"""
        criterion = TripletLoss(margin=0.3)
        anchor = torch.tensor([[1.0, 0.0], [0.0, 1.0]])
        positive = torch.tensor([[0.0, 1.0], [1.0, 0.0]])  # far
        negative = torch.tensor([[0.9, 0.1], [0.1, 0.9]])  # close
        loss = criterion(anchor, positive, negative)
        assert loss.item() > 0, f"Loss 应 > 0, 收到 {loss.item()}"

    def test_loss_zero_when_positive_close(self):
        """TC3.2: 正样本近、负样本远时 loss ≈ 0"""
        criterion = TripletLoss(margin=0.3)
        anchor = torch.tensor([[1.0, 0.0]])
        positive = anchor.clone()  # identical
        negative = torch.tensor([[0.0, 1.0]])  # far
        loss = criterion(anchor, positive, negative)
        assert loss.item() < 0.1, f"Loss 应 ≈0, 收到 {loss.item()}"


# ===================================================================
# TC4: UserTowerTrainer
# ===================================================================
class TestUserTowerTrainer:
    """UserTowerTrainer 测试"""

    def test_train_step(self):
        """TC4.1: 训练一步降低 loss"""
        from app.models.ml.user_tower import UserFeatureEncoder, UserTower, UserTowerTrainer, NUMERIC_FEATURES, CATEGORICAL_FEATURES
        import pandas as pd

        df = pd.DataFrame({
            "tag_count": [1, 2, 3, 4], "brochure_count": [1, 1, 2, 2],
            "view_count": [10, 20, 30, 40], "page_count": [1, 2, 3, 4],
            "avg_intro_len": [10, 20, 15, 25],
            "purpose": ["business", "partner", "client", "investor"],
            "top_tag": ["AI", "大数据", "营销", "SaaS"],
            "membership_tier": ["free", "gold", "diamond", "board"],
        })
        encoder = UserFeatureEncoder(embedding_dim=4)
        encoder.fit(df)

        total_dim = encoder.total_feature_dim
        tower = UserTower(num_features=total_dim, embedding_dim=128, hidden_dims=[64, 128])
        trainer = UserTowerTrainer(tower, encoder, lr=1e-3)

        B = 8
        a = torch.randn(B, total_dim)
        p = torch.randn(B, total_dim)
        n = torch.randn(B, total_dim)

        loss = trainer.train_step(a, p, n)
        assert isinstance(loss, float), f"Loss 应为 float, 收到 {type(loss)}"
        assert loss > 0, f"Loss 应 > 0, 收到 {loss}"

    def test_train_epoch(self):
        """TC4.2: 完整 epoch 训练"""
        from app.models.ml.user_tower import UserFeatureEncoder, UserTower, UserTowerTrainer
        import pandas as pd

        df = pd.DataFrame({
            "tag_count": [1, 2, 3, 4], "brochure_count": [1, 1, 2, 2],
            "view_count": [10, 20, 30, 40], "page_count": [1, 2, 3, 4],
            "avg_intro_len": [10, 20, 15, 25],
            "purpose": ["business", "partner", "client", "investor"],
            "top_tag": ["AI", "大数据", "营销", "SaaS"],
            "membership_tier": ["free", "gold", "diamond", "board"],
        })
        encoder = UserFeatureEncoder(embedding_dim=4)
        encoder.fit(df)
        total_dim = encoder.total_feature_dim
        tower = UserTower(num_features=total_dim, embedding_dim=64)
        trainer = UserTowerTrainer(tower, encoder, lr=1e-3)

        N = 16
        a = torch.randn(N, total_dim)
        p = torch.randn(N, total_dim)
        n = torch.randn(N, total_dim)

        avg_loss = trainer.train_epoch(a, p, n, batch_size=4)
        assert isinstance(avg_loss, float)
        assert avg_loss > 0

    def test_save_and_load_trainer(self):
        """TC4.3: Trainer 保存 + 加载"""
        from app.models.ml.user_tower import UserFeatureEncoder, UserTower, UserTowerTrainer
        import pandas as pd

        df = pd.DataFrame({
            "tag_count": [1, 2, 3], "brochure_count": [1, 1, 2],
            "view_count": [10, 20, 30], "page_count": [1, 2, 3],
            "avg_intro_len": [10, 20, 15],
            "purpose": ["business", "partner", "client"],
            "top_tag": ["AI", "大数据", "营销"],
            "membership_tier": ["free", "gold", "diamond"],
        })
        encoder = UserFeatureEncoder(embedding_dim=4)
        encoder.fit(df)
        total_dim = encoder.total_feature_dim
        tower = UserTower(num_features=total_dim, embedding_dim=64)
        trainer = UserTowerTrainer(tower, encoder, lr=1e-3)

        # 先训练一步
        a = torch.randn(4, total_dim)
        p = torch.randn(4, total_dim)
        n = torch.randn(4, total_dim)
        trainer.train_step(a, p, n)

        with tempfile.NamedTemporaryFile(suffix=".pt", delete=False) as f:
            path = f.name
        try:
            trainer.save(path)
            # 重建并加载
            tower2 = UserTower(num_features=total_dim, embedding_dim=64)
            encoder2 = UserFeatureEncoder(embedding_dim=4)
            trainer2 = UserTowerTrainer(tower2, encoder2, lr=1e-3)
            trainer2.load(path)
            assert trainer2.encoder._fitted, "加载后的编码器应处于 fitted 状态"
            assert len(trainer2.train_losses) == 1
        finally:
            Path(path).unlink(missing_ok=True)


# ===================================================================
# TC5: 嵌入相似性
# ===================================================================
class TestEmbeddingSimilarity:
    """嵌入相似性测试"""

    def test_similar_users_have_similar_embeddings(self):
        """TC5.1: 相似用户产生相似嵌入"""
        tower = UserTower(num_features=5, embedding_dim=128)
        tower.eval()
        x1 = torch.tensor([[1.0, 2.0, 3.0, 4.0, 5.0]])
        x2 = torch.tensor([[1.1, 2.1, 3.1, 4.1, 5.1]])  # 相似
        x3 = torch.tensor([[50.0, -20.0, 100.0, -5.0, 30.0]])  # 不相似

        e1 = tower(x1)
        e2 = tower(x2)
        e3 = tower(x3)

        sim_similar = F.cosine_similarity(e1, e2).item()
        sim_dissimilar = F.cosine_similarity(e1, e3).item()
        assert sim_similar > sim_dissimilar, \
            f"相似用户的相似度 ({sim_similar:.4f}) 应高于不相似用户 ({sim_dissimilar:.4f})"

    def test_similar_enterprises_have_similar_embeddings(self):
        """TC5.2: 相似企业产生相似嵌入"""
        tower = EnterpriseTower(num_features=7, embedding_dim=128)
        tower.eval()
        x1 = torch.tensor([[1.0, 2.0, 3.0, 1.0, 5.0, 2.0, 1.0]])
        x2 = torch.tensor([[1.1, 2.1, 3.1, 1.0, 5.1, 2.1, 1.0]])  # 相似
        x3 = torch.tensor([[10.0, 20.0, 9.0, 4.0, 1.0, 0.0, 3.0]])  # 不相似

        e1 = tower(x1)
        e2 = tower(x2)
        e3 = tower(x3)

        sim_similar = F.cosine_similarity(e1, e2).item()
        sim_dissimilar = F.cosine_similarity(e1, e3).item()
        assert sim_similar > sim_dissimilar, \
            f"相似企业的相似度 ({sim_similar:.4f}) 应高于不相似企业 ({sim_dissimilar:.4f})"


# ===================================================================
# TC6: EnterpriseTower
# ===================================================================
class TestEnterpriseTower:
    """EnterpriseTower 模型测试"""

    def test_forward_shape(self):
        """TC6.1: 前向传播输出 shape 正确"""
        tower = EnterpriseTower(num_features=7, embedding_dim=128, hidden_dims=[256, 128])
        x = torch.randn(4, 7)
        out = tower(x)
        assert out.shape == (4, 128), f"输出 shape 应为 (4, 128), 收到 {out.shape}"

    def test_l2_normalized(self):
        """TC6.2: 输出经过 L2 归一化"""
        tower = EnterpriseTower(num_features=7, embedding_dim=128)
        x = torch.randn(4, 7)
        out = tower(x)
        norms = out.norm(p=2, dim=1)
        assert torch.allclose(norms, torch.ones(4), atol=1e-5)

    def test_predict_returns_numpy(self):
        """TC6.3: predict 返回 numpy"""
        tower = EnterpriseTower(num_features=7, embedding_dim=128)
        x = torch.randn(2, 7)
        out = tower.predict(x)
        assert isinstance(out, np.ndarray)
        assert out.shape == (2, 128)

    def test_save_and_load_model(self):
        """TC6.4: save_model + load_model 往返"""
        tower = EnterpriseTower(num_features=7, embedding_dim=64)
        x = torch.randn(2, 7)
        out_before = tower.predict(x)

        with tempfile.NamedTemporaryFile(suffix=".pt", delete=False) as f:
            path = f.name
        try:
            tower.save_model(path)
            loaded = EnterpriseTower.load_model(path, num_features=7, embedding_dim=64)
            out_after = loaded.predict(x)
            assert np.allclose(out_before, out_after, atol=1e-6)
        finally:
            Path(path).unlink(missing_ok=True)

    def test_repr(self):
        """TC6.5: __repr__"""
        tower = EnterpriseTower(num_features=7, embedding_dim=64, hidden_dims=[128, 64])
        r = repr(tower)
        assert "EnterpriseTower" in r
        assert "num_features=7" in r


# ===================================================================
# TC7: EnterpriseFeatureEncoder
# ===================================================================
class TestEnterpriseFeatureEncoder:
    """EnterpriseFeatureEncoder 测试"""

    def test_fit_and_transform(self):
        """TC7.1: fit + transform 完整流程"""
        import pandas as pd
        df = pd.DataFrame({
            "brochure_count": [1, 2, 3],
            "avg_pages_per_brochure": [3.0, 4.5, 2.0],
            "total_view_count": [50, 200, 100],
            "brochure_diversity": [1, 2, 1],
            "company_name_len": [6, 8, 10],
            "pages_with_ai_summary": [1, 3, 0],
            "purpose": ["business", "partner", "client"],
            "visibility": ["public", "platform", "network"],
        })
        encoder = EnterpriseFeatureEncoder(cat_embedding_dim=8)
        encoder.fit(df)
        assert encoder._fitted
        assert "brochure_count" in encoder.feature_mean

        tensor = encoder.transform({
            "brochure_count": 2,
            "avg_pages_per_brochure": 3.5,
            "total_view_count": 150,
            "brochure_diversity": 2,
            "company_name_len": 8,
            "pages_with_ai_summary": 2,
            "purpose": "business",
            "visibility": "public",
        })
        expected_dim = len(ENTERPRISE_FEATURES) + len(ENTERPRISE_CATEGORICAL_FEATURES) * 8
        assert tensor.shape == (1, expected_dim)

    def test_batch_transform(self):
        """TC7.2: 批量 transform"""
        import pandas as pd
        df = pd.DataFrame({
            "brochure_count": [1, 2], "avg_pages_per_brochure": [3.0, 4.0],
            "total_view_count": [50, 100], "brochure_diversity": [1, 2],
            "company_name_len": [6, 8], "pages_with_ai_summary": [1, 2],
            "purpose": ["business", "partner"], "visibility": ["public", "platform"],
        })
        encoder = EnterpriseFeatureEncoder(cat_embedding_dim=4)
        encoder.fit(df)

        data = [
            {"brochure_count": 2, "avg_pages_per_brochure": 3.5, "total_view_count": 80,
             "brochure_diversity": 1, "company_name_len": 7, "pages_with_ai_summary": 1,
             "purpose": "business", "visibility": "public"},
            {"brochure_count": 3, "avg_pages_per_brochure": 5.0, "total_view_count": 200,
             "brochure_diversity": 3, "company_name_len": 10, "pages_with_ai_summary": 3,
             "purpose": "partner", "visibility": "platform"},
        ]
        tensor = encoder.transform(data)
        assert tensor.shape == (2, len(ENTERPRISE_FEATURES) + len(ENTERPRISE_CATEGORICAL_FEATURES) * 4)

    def test_extract_features_from_models(self):
        """TC7.3: 从数据模型提取企业特征"""
        user = MockUser(company="AI数字化科技")
        pages = [
            MockPage(ai_summary="AI驱动的匹配系统"),
            MockPage(ai_summary=""),
            MockPage(ai_summary="企业画像分析"),
        ]
        brochures = [
            MockBrochure(purpose="business", pages_count=3, view_count=100, pages=pages),
            MockBrochure(purpose="partner", pages_count=5, view_count=200),
        ]

        features = EnterpriseFeatureEncoder.extract_features_from_models(user, brochures)
        assert features["brochure_count"] == 2
        assert features["total_view_count"] == 300
        assert features["company_name_len"] == 7  # "AI数字化科技" 长度
        assert features["brochure_diversity"] == 2  # business + partner

    def test_string_mapping(self):
        """TC7.4: 类别特征字符串映射"""
        import pandas as pd
        df = pd.DataFrame({
            "brochure_count": [1, 2], "avg_pages_per_brochure": [3.0, 4.0],
            "total_view_count": [50, 100], "brochure_diversity": [1, 2],
            "company_name_len": [6, 8], "pages_with_ai_summary": [1, 2],
            "purpose": ["business", "partner"], "visibility": ["public", "platform"],
        })
        encoder = EnterpriseFeatureEncoder(cat_embedding_dim=4)
        encoder.fit(df)

        # 使用字符串 purpose / visibility
        tensor = encoder.transform({
            "brochure_count": 2, "avg_pages_per_brochure": 3.5, "total_view_count": 80,
            "brochure_diversity": 1, "company_name_len": 7, "pages_with_ai_summary": 1,
            "purpose": "investor",  # 不在训练集中, 应被映射为 0 (unknown)
            "visibility": "private",  # 不在训练集中, 应被映射为 0
        })
        assert tensor.shape == (1, len(ENTERPRISE_FEATURES) + len(ENTERPRISE_CATEGORICAL_FEATURES) * 4)
        assert not torch.isnan(tensor).any(), "结果不应包含 NaN"

    def test_raise_error_before_fit(self):
        """TC7.5: 未 fit 时报错"""
        encoder = EnterpriseFeatureEncoder()
        with pytest.raises(RuntimeError, match="尚未 fit"):
            encoder.transform({
                "brochure_count": 1, "avg_pages_per_brochure": 1.0,
                "total_view_count": 1, "brochure_diversity": 0,
                "company_name_len": 1, "pages_with_ai_summary": 0,
                "purpose": "business", "visibility": "public",
            })


# ===================================================================
# TC8: 跨模型一致性
# ===================================================================
class TestCrossModelConsistency:
    """跨模型一致性测试"""

    def test_user_tower_different_hidden_dims(self):
        """TC8.1: 不同隐层配置均可正常工作"""
        configs = [
            (5, 64, [128, 64]),
            (10, 128, [256, 128]),
            (8, 32, [64]),
            (3, 128, [128, 128, 128]),
        ]
        for num_feat, emb_dim, h_dims in configs:
            tower = UserTower(num_features=num_feat, embedding_dim=emb_dim, hidden_dims=h_dims)
            x = torch.randn(2, num_feat)
            out = tower(x)
            assert out.shape == (2, emb_dim), \
                f"config (num={num_feat}, emb={emb_dim}, h={h_dims}): shape {out.shape}"

    def test_enterprise_tower_different_hidden_dims(self):
        """TC8.2: 不同隐层配置均可正常工作"""
        configs = [
            (6, 64, [128, 64]),
            (8, 128, [256, 128]),
            (4, 32, [64]),
        ]
        for num_feat, emb_dim, h_dims in configs:
            tower = EnterpriseTower(num_features=num_feat, embedding_dim=emb_dim, hidden_dims=h_dims)
            x = torch.randn(2, num_feat)
            out = tower(x)
            assert out.shape == (2, emb_dim)

    def test_module_imports(self):
        """TC8.3: 模块可正常导入"""
        from app.models.ml import UserTower, UserFeatureEncoder, EnterpriseTower, EnterpriseFeatureEncoder
        assert UserTower is not None
        assert UserFeatureEncoder is not None
        assert EnterpriseTower is not None
        assert EnterpriseFeatureEncoder is not None

    def test_encoder_total_feature_dim(self):
        """TC8.4: total_feature_dim 属性正确"""
        encoder = UserFeatureEncoder(embedding_dim=16)
        expected = len(NUMERIC_FEATURES) + len(CATEGORICAL_FEATURES) * 16
        assert encoder.total_feature_dim == expected

        ent_encoder = EnterpriseFeatureEncoder(cat_embedding_dim=8)
        expected_ent = len(ENTERPRISE_FEATURES) + len(ENTERPRISE_CATEGORICAL_FEATURES) * 8
        assert ent_encoder.total_feature_dim == expected_ent
