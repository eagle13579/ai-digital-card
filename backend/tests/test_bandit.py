"""
多臂老虎机引擎测试 (8 个用例)
==============================
ThompsonSampling + BanditService 验证。
"""

import numpy as np
import pytest
from app.ai.bandit_engine import Arm, ThompsonSampling, BanditService


class TestThompsonSampling:
    """ThompsonSampling 核心算法测试"""

    def test_select_arm_returns_valid_index(self):
        """1. 选择返回有效索引"""
        ts = ThompsonSampling()
        arms = [Arm(arm_id="a"), Arm(arm_id="b"), Arm(arm_id="c")]
        ts.set_arms(arms)
        idx = ts.select_arm()
        assert 0 <= idx < 3

    def test_update_increases_alpha_on_reward(self):
        """2. 奖励 1 后 alpha 增加"""
        ts = ThompsonSampling()
        arms = [Arm(arm_id="x", alpha=1.0, beta=1.0)]
        ts.set_arms(arms)
        ts.update(0, 1.0)
        assert arms[0].alpha == 2.0
        assert arms[0].beta == 1.0

    def test_update_increases_beta_on_no_reward(self):
        """3. 奖励 0 后 beta 增加"""
        ts = ThompsonSampling()
        arms = [Arm(arm_id="y", alpha=1.0, beta=1.0)]
        ts.set_arms(arms)
        ts.update(0, 0.0)
        assert arms[0].alpha == 1.0
        assert arms[0].beta == 2.0

    def test_expected_value_formula(self):
        """4. 期望值 = alpha / (alpha + beta)"""
        ts = ThompsonSampling()
        arms = [Arm(arm_id="z", alpha=3.0, beta=7.0)]
        ts.set_arms(arms)
        ev = ts.get_expected_value(0)
        assert ev == pytest.approx(0.3)

    def test_convergence_to_best_arm(self):
        """5. 多次采样后收敛到最优臂（奖励概率最高的臂被选中 >60%）"""
        np.random.seed(42)
        ts = ThompsonSampling()
        # 臂 0 成功率 90%, 臂 1 成功率 10%
        arms = [Arm(arm_id="good"), Arm(arm_id="bad")]
        ts.set_arms(arms)
        # 模拟多次交互，让算法学到臂 0 更优
        for _ in range(200):
            idx = ts.select_arm()
            reward = 1.0 if (idx == 0 and np.random.random() < 0.9) else 0.0
            ts.update(idx, reward)
        # 理论上臂 0 的期望值应远高于臂 1
        assert ts.get_expected_value(0) > ts.get_expected_value(1)
        # 再次采样 100 次，大部分应选臂 0
        chosen = [ts.select_arm() for _ in range(100)]
        assert sum(chosen) < 40  # 臂 1 被选次数 < 40

    def test_select_arm_distribution(self):
        """6. 初始均匀分布下各臂被选概率大致均等"""
        np.random.seed(123)
        ts = ThompsonSampling()
        arms = [Arm(arm_id="a"), Arm(arm_id="b"), Arm(arm_id="c")]
        ts.set_arms(arms)
        counts = [0, 0, 0]
        for _ in range(3000):
            idx = ts.select_arm()
            counts[idx] += 1
        # 三个臂各约 1000 次 ± 300
        for c in counts:
            assert 400 <= c <= 1600


class TestBanditService:
    """BanditService 集成测试"""

    def test_empty_candidates_returns_empty(self):
        """7. 空候选列表返回空"""
        svc = BanditService()
        result = svc.recommend([], user_id="u1", top_k=5)
        assert result == []

    def test_full_flow(self):
        """8. 完整流程：推荐 + 记录奖励 + 期望值更新"""
        np.random.seed(7)
        svc = BanditService()
        candidates = [
            {"id": "item_1", "title": "A"},
            {"id": "item_2", "title": "B"},
            {"id": "item_3", "title": "C"},
        ]

        # 首次推荐
        result = svc.recommend(candidates, user_id="u1", top_k=3)
        assert len(result) == 3
        assert all(r in candidates for r in result)

        # 记录 reward：提升 item_1，压低 item_2
        for _ in range(50):
            svc.record_reward("u1", "item_1", 1.0)
            svc.record_reward("u1", "item_2", 0.0)

        arm1 = svc.user_arms["u1"]["item_1"]
        arm2 = svc.user_arms["u1"]["item_2"]
        # 臂 1 期望应显著高于臂 2
        assert arm1.alpha / (arm1.alpha + arm1.beta) > 0.8
        assert arm2.alpha / (arm2.alpha + arm2.beta) < 0.2

    def test_recommend_respects_top_k(self):
        """9. top_k 限制返回数量"""
        svc = BanditService()
        candidates = [{"id": f"item_{i}"} for i in range(20)]
        result = svc.recommend(candidates, user_id="u2", top_k=5)
        assert len(result) == 5
