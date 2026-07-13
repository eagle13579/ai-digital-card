"""
AI数智名片 — ML 模型综合测试

测试覆盖:
  - BehaviorTower: 前向传播、带掩码、predict、save/load
  - BehaviorSequenceEncoder: fit/transform、序列处理、批量、截断
  - TowerEnsemble: 前向传播、predict、save/load
  - MatchingScorer: score、forward、无行为回退
  - MatchingAPI: predict、save/load
  - OnlineWeightOptimizer: 更新、重置

用法:
    pytest test_models.py -v
    python test_models.py
"""

from __future__ import annotations

import sys
import math
from pathlib import Path
from typing import Optional

import numpy as np

# ── 确保能找到模块 ──
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent.parent))

try:
    import torch
    import torch.nn.functional as F
except ImportError:
    print("错误: 需要 PyTorch. 请执行: pip install torch")
    sys.exit(1)

try:
    import pandas as pd
except ImportError:
    print("错误: 需要 pandas. 请执行: pip install pandas")
    sys.exit(1)

from app.models.ml.behavior_tower import (
    BehaviorTower,
    BehaviorSequenceEncoder,
    BEHAVIOR_TYPE_MAP,
)
from app.models.ml.tower_ensemble import (
    TowerEnsemble,
    MatchingScorer,
    MatchingAPI,
    OnlineWeightOptimizer,
    MatchResult,
)


# ===================================================================
# BehaviorTower 测试
# ===================================================================
class TestBehaviorTower:
    """行为塔单元测试"""

    def test_forward(self):
        """TC-BT1: 模型前向传播"""
        tower = BehaviorTower(max_seq_len=50, feature_dim=32, hidden_dim=128)
        x = torch.randn(4, 50, 32)
        out = tower(x)
        assert out.shape == (4, 128), f"输出 shape 应为 (4, 128), 收到 {out.shape}"
        norms = out.norm(p=2, dim=1)
        assert torch.allclose(norms, torch.ones(4), atol=1e-5), \
            f"L2 归一化后 norm 应 ≈1, 收到 {norms}"

    def test_with_mask(self):
        """TC-BT2: 模型带掩码前向传播"""
        tower = BehaviorTower(max_seq_len=10, feature_dim=8, hidden_dim=64)
        x = torch.randn(4, 10, 8)
        mask = torch.ones(4, 10, dtype=torch.bool)
        mask[:, 5:] = False
        out = tower(x, mask)
        assert out.shape == (4, 128), f"输出 shape 应为 (4, 128), 收到 {out.shape}"

    def test_predict(self):
        """TC-BT3: predict 接口返回 numpy"""
        tower = BehaviorTower(max_seq_len=5, feature_dim=8, hidden_dim=64)
        x = torch.randn(2, 5, 8)
        out = tower.predict(x)
        assert isinstance(out, np.ndarray), f"predict 应返回 numpy, 收到 {type(out)}"
        assert out.shape == (2, 128)

    def test_save_load(self, tmp_path):
        """TC-BT4: save/load 接口"""
        tower = BehaviorTower(max_seq_len=5, feature_dim=8, hidden_dim=64)
        x = torch.randn(2, 5, 8)
        out_before = tower.predict(x)

        path = tmp_path / "behavior_tower.pt"
        tower.save(str(path))

        loaded = BehaviorTower.load(str(path), max_seq_len=5, feature_dim=8, hidden_dim=64)
        out_after = loaded.predict(x)

        assert np.allclose(out_before, out_after, atol=1e-6), \
            "save/load 前后输出应一致"

    def test_repr(self):
        """TC-BT5: 模型 repr"""
        tower = BehaviorTower(max_seq_len=10, feature_dim=16, hidden_dim=64)
        r = repr(tower)
        assert "BehaviorTower" in r
        assert "max_seq_len=10" in r


class TestBehaviorSequenceEncoder:
    """行为序列编码器单元测试"""

    def test_fit(self):
        """TC-BE1: fit 方法"""
        df = pd.DataFrame({
            "behavior_type": ["view", "browse", "match_view"],
            "timestamp_gap": [0.0, 1.0, 5.0],
            "duration": [5.0, 30.0, 120.0],
            "target_id": [101, 102, 103],
            "action_value": [1.0, 2.0, 5.0],
        })
        encoder = BehaviorSequenceEncoder(max_seq_len=10, feature_dim=32)
        encoder.fit(df)
        assert encoder._fitted, "fit 后 _fitted 应为 True"
        assert "behavior_type" in encoder.categorical_cardinality

    def test_transform_single(self):
        """TC-BE2: transform 单条行为"""
        df = pd.DataFrame({
            "behavior_type": ["view"], "timestamp_gap": [0.0], "duration": [5.0],
            "target_id": [101], "action_value": [1.0],
        })
        encoder = BehaviorSequenceEncoder(max_seq_len=10, feature_dim=32)
        encoder.fit(df)

        tensor, mask = encoder.transform({
            "behavior_type": "view", "timestamp_gap": 0.0,
            "duration": 5.0, "target_id": 101, "action_value": 1.0,
        })
        assert tensor.shape == (1, 10, 32)
        assert mask.shape == (1, 10)
        assert mask[0, 0].item() is True

    def test_transform_sequence(self):
        """TC-BE3: transform 行为序列"""
        df = pd.DataFrame({
            "behavior_type": ["view", "browse"],
            "timestamp_gap": [0.0, 1.0],
            "duration": [5.0, 30.0],
            "target_id": [101, 102],
            "action_value": [1.0, 2.0],
        })
        encoder = BehaviorSequenceEncoder(max_seq_len=10, feature_dim=32)
        encoder.fit(df)

        seq = [{"behavior_type": "view", "timestamp_gap": 0.0, "duration": 5.0, "target_id": 101, "action_value": 1.0},
               {"behavior_type": "browse", "timestamp_gap": 1.0, "duration": 30.0, "target_id": 102, "action_value": 2.0}]
        tensor, mask = encoder.transform(seq)
        assert tensor.shape == (1, 10, 32)
        assert mask[0, :2].sum().item() == 2

    def test_transform_batch(self):
        """TC-BE4: transform 批量多用户"""
        df = pd.DataFrame({
            "behavior_type": ["view", "browse"],
            "timestamp_gap": [0.0, 1.0],
            "duration": [5.0, 30.0],
            "target_id": [101, 102],
            "action_value": [1.0, 2.0],
        })
        encoder = BehaviorSequenceEncoder(max_seq_len=10, feature_dim=32)
        encoder.fit(df)

        user1 = [{"behavior_type": "view", "timestamp_gap": 0.0, "duration": 5.0, "target_id": 101, "action_value": 1.0}]
        user2 = [{"behavior_type": "browse", "timestamp_gap": 1.0, "duration": 30.0, "target_id": 102, "action_value": 2.0}]
        tensor, mask = encoder.transform([user1, user2])
        assert tensor.shape == (2, 10, 32)

    def test_transform_truncation(self):
        """TC-BE5: 序列截断"""
        df = pd.DataFrame({
            "behavior_type": ["view"], "timestamp_gap": [0.0],
            "duration": [5.0], "target_id": [101], "action_value": [1.0],
        })
        encoder = BehaviorSequenceEncoder(max_seq_len=3, feature_dim=16)
        encoder.fit(df)

        long_seq = [{"behavior_type": "view", "timestamp_gap": float(i), "duration": 5.0, "target_id": 100 + i, "action_value": 1.0} for i in range(10)]
        tensor, mask = encoder.transform(long_seq)
        assert tensor.shape == (1, 3, 16)
        assert mask[0].sum().item() == 3

    def test_not_fitted(self):
        """TC-BE6: 未 fit 时 transform 应报错"""
        encoder = BehaviorSequenceEncoder()
        try:
            encoder.transform({"behavior_type": "view", "timestamp_gap": 0.0, "duration": 5.0, "target_id": 101, "action_value": 1.0})
            assert False, "应抛出 RuntimeError"
        except RuntimeError:
            pass


# ===================================================================
# TowerEnsemble 测试
# ===================================================================
class TestTowerEnsemble:
    """TowerEnsemble 单元测试"""

    def test_forward(self):
        """TC-TE1: 前向传播"""
        behav_tower = BehaviorTower(max_seq_len=5, feature_dim=8, hidden_dim=64)
        ensemble = TowerEnsemble(behavior_tower=behav_tower)

        b = torch.randn(3, 5, 8)
        m = torch.ones(3, 5, dtype=torch.bool)

        scores = ensemble(b, m)
        assert scores.shape == (3,), f"输出 shape 应为 (3,), 收到 {scores.shape}"
        assert (scores >= 0).all() and (scores <= 1).all(), "分数应在 [0,1]"

    def test_predict(self):
        """TC-TE2: predict 接口"""
        behav_tower = BehaviorTower(max_seq_len=5, feature_dim=8, hidden_dim=64)
        ensemble = TowerEnsemble(behavior_tower=behav_tower)

        b = torch.randn(2, 5, 8)
        m = torch.ones(2, 5, dtype=torch.bool)

        out = ensemble.predict(b, m)
        assert isinstance(out, np.ndarray)
        assert out.shape == (2,)

    def test_save_load(self, tmp_path):
        """TC-TE3: save/load 接口"""
        behav_tower = BehaviorTower(max_seq_len=5, feature_dim=8, hidden_dim=64)
        ensemble = TowerEnsemble(behavior_tower=behav_tower)

        b = torch.randn(2, 5, 8)
        m = torch.ones(2, 5, dtype=torch.bool)
        out_before = ensemble.predict(b, m)

        path = tmp_path / "tower_ensemble.pt"
        ensemble.save(str(path))

        behav_tower2 = BehaviorTower(max_seq_len=5, feature_dim=8, hidden_dim=64)
        loaded = TowerEnsemble.load(str(path), behavior_tower=behav_tower2)
        out_after = loaded.predict(b, m)

        assert np.allclose(out_before, out_after, atol=1e-6)


# ===================================================================
# MatchingScorer 测试
# ===================================================================
class TestMatchingScorer:
    """MatchingScorer 单元测试"""

    def test_score(self):
        """TC-MS1: score 基本评分"""
        behav_tower = BehaviorTower(max_seq_len=5, feature_dim=8, hidden_dim=64)
        scorer = MatchingScorer(behav_tower)

        u = torch.randn(1, 4)
        e = torch.randn(1, 6)
        b = torch.randn(1, 5, 8)
        m = torch.ones(1, 5, dtype=torch.bool)

        score = scorer.score(u, e, b, m)
        assert isinstance(score, float)
        assert 0.0 <= score <= 1.0

    def test_score_no_behavior(self):
        """TC-MS2: 无行为数据回退"""
        behav_tower = BehaviorTower(max_seq_len=5, feature_dim=8, hidden_dim=64)
        scorer = MatchingScorer(behav_tower)

        u = torch.randn(1, 4)
        e = torch.randn(1, 6)

        score = scorer.score(u, e)
        assert isinstance(score, float)
        assert 0.0 <= score <= 1.0

    def test_forward_batch(self):
        """TC-MS3: forward 批量评分"""
        behav_tower = BehaviorTower(max_seq_len=5, feature_dim=8, hidden_dim=64)
        scorer = MatchingScorer(behav_tower)

        B = 3
        u = torch.randn(B, 4)
        e = torch.randn(B, 6)
        b = torch.randn(B, 5, 8)
        m = torch.ones(B, 5, dtype=torch.bool)

        scores = scorer.forward(u, e, b, m)
        assert scores.shape == (B,)
        assert (scores >= 0).all() and (scores <= 1).all()

    def test_update_weights(self):
        """TC-MS4: 权重更新"""
        behav_tower = BehaviorTower(max_seq_len=5, feature_dim=8, hidden_dim=64)
        scorer = MatchingScorer(behav_tower, use_online_opt=True)

        u = torch.randn(1, 4)
        e = torch.randn(1, 6)
        b = torch.randn(1, 5, 8)
        m = torch.ones(1, 5, dtype=torch.bool)

        new_weights = scorer.update_weights(u, e, b, m, reward=1.0)
        assert "alpha" in new_weights
        assert abs(sum(new_weights.values()) - 1.0) < 0.01

    def test_set_get_weights(self):
        """TC-MS5: 设置和获取权重"""
        behav_tower = BehaviorTower(max_seq_len=5, feature_dim=8, hidden_dim=64)
        scorer = MatchingScorer(behav_tower)

        scorer.set_weights({"alpha": 0.6, "beta": 0.3, "gamma": 0.1})
        w = scorer.get_weights()
        assert abs(w["alpha"] - 0.6) < 0.01


# ===================================================================
# MatchingAPI 测试
# ===================================================================
class TestMatchingAPI:
    """MatchingAPI 单元测试"""

    def test_predict_with_candidates(self):
        """TC-MA1: predict 端到端"""
        behav_tower = BehaviorTower(max_seq_len=5, feature_dim=16, hidden_dim=64)

        behav_encoder = BehaviorSequenceEncoder(max_seq_len=5, feature_dim=16)
        behav_df = pd.DataFrame({
            "behavior_type": ["view", "browse"],
            "timestamp_gap": [0.0, 1.0],
            "duration": [5.0, 30.0],
            "target_id": [101, 102],
            "action_value": [1.0, 2.0],
        })
        behav_encoder.fit(behav_df)

        api = MatchingAPI(
            behavior_tower=behav_tower,
            behavior_encoder=behav_encoder,
            top_k=5,
        )

        behavior = [
            {"behavior_type": "view", "timestamp_gap": 0.0, "duration": 5.0, "target_id": 101, "action_value": 1.0},
            {"behavior_type": "browse", "timestamp_gap": 1.0, "duration": 30.0, "target_id": 102, "action_value": 2.0},
        ]

        candidates = [
            {"target_id": 1, "feature": [0.1, 0.2, 0.3, 0.4]},
            {"target_id": 2, "feature": [0.5, 0.6, 0.7, 0.8]},
            {"target_id": 3},
        ]

        results = api.predict(behavior_sequences=behavior, candidates=candidates)
        assert len(results) <= 5
        assert all(isinstance(r, MatchResult) for r in results)
        for i in range(len(results) - 1):
            assert results[i].score >= results[i + 1].score, "结果应按分数降序排列"

    def test_predict_no_behavior(self):
        """TC-MA2: 无行为序列"""
        behav_encoder = BehaviorSequenceEncoder(max_seq_len=5, feature_dim=16)
        behav_df = pd.DataFrame({
            "behavior_type": ["view"], "timestamp_gap": [0.0],
            "duration": [5.0], "target_id": [101], "action_value": [1.0],
        })
        behav_encoder.fit(behav_df)

        api = MatchingAPI(
            behavior_tower=BehaviorTower(max_seq_len=5, feature_dim=16, hidden_dim=64),
            behavior_encoder=behav_encoder,
            top_k=3,
        )
        results = api.predict(behavior_sequences=None)
        assert results == [], "无行为序列时应返回空列表"

    def test_save_load(self, tmp_path):
        """TC-MA3: save/load 接口"""
        behav_tower = BehaviorTower(max_seq_len=5, feature_dim=16, hidden_dim=64)
        behav_encoder = BehaviorSequenceEncoder(max_seq_len=5, feature_dim=16)
        behav_df = pd.DataFrame({
            "behavior_type": ["view"], "timestamp_gap": [0.0],
            "duration": [5.0], "target_id": [101], "action_value": [1.0],
        })
        behav_encoder.fit(behav_df)

        api = MatchingAPI(
            behavior_tower=behav_tower,
            behavior_encoder=behav_encoder,
            top_k=5,
        )

        save_dir = tmp_path / "matching_api"
        api.save(str(save_dir))

        loaded_api = MatchingAPI.load(str(save_dir), tower_kwargs={
            "max_seq_len": 5, "feature_dim": 16, "hidden_dim": 64,
        })
        assert loaded_api.top_k == 5
        assert loaded_api.behavior_encoder._fitted


# ===================================================================
# OnlineWeightOptimizer 测试
# ===================================================================
class TestOnlineWeightOptimizer:
    """OnlineWeightOptimizer 单元测试"""

    def test_initial_weights(self):
        """TC-OW1: 初始权重"""
        opt = OnlineWeightOptimizer()
        w = opt.get_weights()
        assert abs(w["alpha"] - 0.5) < 0.01
        assert abs(w["beta"] - 0.3) < 0.01
        assert abs(w["gamma"] - 0.2) < 0.01

    def test_update_positive(self):
        """TC-OW2: 正反馈更新"""
        opt = OnlineWeightOptimizer(lr=0.1)
        w = opt.update(
            sim_user_ent=0.9, sim_behavior_ent=0.3, sim_user_behavior=0.5, reward=1.0
        )
        assert opt.total_updates == 1
        assert all(0.05 <= v <= 0.9 for v in w.values())
        assert abs(sum(w.values()) - 1.0) < 0.01

    def test_update_negative(self):
        """TC-OW3: 负反馈更新"""
        opt = OnlineWeightOptimizer(lr=0.1)
        w = opt.update(
            sim_user_ent=0.2, sim_behavior_ent=0.8, sim_user_behavior=0.3, reward=-0.5
        )
        assert opt.total_updates == 1
        assert all(0.05 <= v <= 0.9 for v in w.values())
        assert abs(sum(w.values()) - 1.0) < 0.01

    def test_reset(self):
        """TC-OW4: 权重重置"""
        opt = OnlineWeightOptimizer()
        opt.update(sim_user_ent=0.5, sim_behavior_ent=0.5, sim_user_behavior=0.5, reward=1.0)
        opt.reset_weights()
        w = opt.get_weights()
        assert abs(w["alpha"] - 0.5) < 0.01
        assert abs(w["beta"] - 0.3) < 0.01

    def test_history(self):
        """TC-OW5: 历史记录"""
        opt = OnlineWeightOptimizer()
        opt.update(sim_user_ent=0.5, sim_behavior_ent=0.5, sim_user_behavior=0.5, reward=1.0)
        opt.update(sim_user_ent=0.6, sim_behavior_ent=0.4, sim_user_behavior=0.5, reward=0.5)
        assert len(opt.reward_history) == 2
        assert len(opt.weight_history) == 2


# ===================================================================
# MatchResult 测试
# ===================================================================
class TestMatchResult:
    """MatchResult 单元测试"""

    def test_sorting(self):
        """TC-MR1: 排序"""
        r1 = MatchResult(target_id=1, score=0.9)
        r2 = MatchResult(target_id=2, score=0.5)
        r3 = MatchResult(target_id=3, score=0.7)

        sorted_results = sorted([r1, r2, r3], reverse=True)
        assert sorted_results[0].score == 0.9
        assert sorted_results[1].score == 0.7
        assert sorted_results[2].score == 0.5


# ===================================================================
# 模块 __all__ 测试
# ===================================================================
class TestModuleExports:
    """模块导出测试"""

    def test_imports(self):
        """TC-ME1: 所有导出的类可导入"""
        from app.models.ml import BehaviorTower, BehaviorSequenceEncoder
        from app.models.ml import TowerEnsemble, MatchingScorer, MatchingAPI
        from app.models.ml import OnlineWeightOptimizer, MatchResult

        assert BehaviorTower is not None
        assert BehaviorSequenceEncoder is not None
        assert TowerEnsemble is not None
        assert MatchingScorer is not None
        assert MatchingAPI is not None
        assert OnlineWeightOptimizer is not None
        assert MatchResult is not None


# ===================================================================
# 主入口 (直接运行)
# ===================================================================
def _run_tests():
    """运行所有测试 (非 pytest 环境)"""
    import inspect

    test_classes = [
        TestBehaviorTower,
        TestBehaviorSequenceEncoder,
        TestTowerEnsemble,
        TestMatchingScorer,
        TestMatchingAPI,
        TestOnlineWeightOptimizer,
        TestMatchResult,
        TestModuleExports,
    ]

    passed = 0
    failed = 0
    for cls in test_classes:
        inst = cls()
        for name, method in inspect.getmembers(inst, predicate=inspect.ismethod):
            if name.startswith("test_"):
                try:
                    if "tmp_path" in inspect.signature(method).parameters:
                        import tempfile
                        with tempfile.TemporaryDirectory() as td:
                            method(Path(td))
                    else:
                        method()
                    print(f"  ✓ {cls.__name__}.{name}")
                    passed += 1
                except Exception as e:
                    print(f"  ✗ {cls.__name__}.{name}: {e}")
                    import traceback
                    traceback.print_exc()
                    failed += 1

    print()
    print("=" * 60)
    print(f"  结果: {passed} 通过, {failed} 失败, {passed + failed} 总计")
    if failed == 0:
        print("  ✓ 全部通过!")
    else:
        print("  ✗ 存在失败的测试!")
    print("=" * 60)

    return failed == 0


if __name__ == "__main__":
    success = _run_tests()
    sys.exit(0 if success else 1)
