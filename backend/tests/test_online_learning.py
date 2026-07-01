"""OnlineLearningPipeline 测试 — 至少 8 个用例，覆盖交互记录、趋势、历史与线程安全。"""

import time
import threading
import pytest

from app.ai.online_learning import OnlineLearningPipeline


@pytest.fixture
def pipeline():
    return OnlineLearningPipeline()


class TestOnlineLearningPipeline:
    """在线学习管道测试套件。"""

    def test_record_single_interaction(self, pipeline):
        """1. 记录单条交互 → 成功记录"""
        pipeline.record_interaction("user1", "item_a", "view")
        history = pipeline.get_user_history("user1")
        assert len(history) == 1
        assert history[0]["item_id"] == "item_a"
        assert history[0]["action"] == "view"
        assert isinstance(history[0]["timestamp"], float)

    def test_trending_correct_order(self, pipeline):
        """2. 多条交互 → 热门趋势按交互量降序排列"""
        pipeline.record_interaction("u1", "hot1", "view")
        pipeline.record_interaction("u2", "hot1", "click")
        pipeline.record_interaction("u3", "hot1", "share")
        pipeline.record_interaction("u4", "hot2", "view")
        pipeline.record_interaction("u5", "hot2", "view")
        # hot1=3, hot2=2
        trending = pipeline.get_trending(hours=24, limit=10)
        assert len(trending) == 2
        assert trending[0]["item_id"] == "hot1"
        assert trending[0]["count"] == 3
        assert trending[1]["item_id"] == "hot2"
        assert trending[1]["count"] == 2

    def test_action_type_filtering(self, pipeline):
        """3. 不同 action 类型均可被记录和查询"""
        pipeline.record_interaction("u1", "item_x", "view")
        pipeline.record_interaction("u1", "item_x", "click")
        pipeline.record_interaction("u1", "item_x", "share")
        pipeline.record_interaction("u1", "item_x", "save")
        history = pipeline.get_user_history("u1", limit=10)
        actions = {h["action"] for h in history}
        assert actions == {"view", "click", "share", "save"}
        # 热门趋势中全部算入
        trend = pipeline.get_trending(hours=24)
        assert trend[0]["count"] == 4

    def test_empty_data_returns_empty(self, pipeline):
        """4. 无任何交互时，历史与趋势均返回空列表"""
        assert pipeline.get_user_history("nonexistent") == []
        assert pipeline.get_trending(hours=24) == []

    def test_user_history_reverse_chronological(self, pipeline):
        """5. 用户历史按时间倒序排列"""
        t0 = 1000.0
        pipeline.record_interaction("u1", "old", "view", timestamp=t0)
        pipeline.record_interaction("u1", "mid", "click", timestamp=t0 + 10)
        pipeline.record_interaction("u1", "new", "save", timestamp=t0 + 20)
        history = pipeline.get_user_history("u1")
        timestamps = [h["timestamp"] for h in history]
        assert timestamps == sorted(timestamps, reverse=True)
        assert history[0]["item_id"] == "new"
        assert history[-1]["item_id"] == "old"

    def test_trending_time_window(self, pipeline):
        """6. 热门趋势只统计指定时间窗口内的交互"""
        now = time.time()
        pipeline.record_interaction("u1", "old_item", "view", timestamp=now - 7200)  # 2h ago
        pipeline.record_interaction("u2", "new_item", "view", timestamp=now - 600)  # 10min ago
        # 限定1小时内 → 只有 new_item
        trending = pipeline.get_trending(hours=1)
        assert len(trending) == 1
        assert trending[0]["item_id"] == "new_item"
        # 限定4小时内 → 两者都有
        trending_wide = pipeline.get_trending(hours=4, limit=10)
        assert len(trending_wide) == 2

    def test_get_user_history_limit(self, pipeline):
        """7. 用户历史 limit 参数正常工作"""
        for i in range(20):
            pipeline.record_interaction("u_limit", f"item_{i}", "view", timestamp=float(i))
        # 限制5条
        history = pipeline.get_user_history("u_limit", limit=5)
        assert len(history) == 5
        # 按时间倒序，所以最新的(top)在前
        timestamps = [h["timestamp"] for h in history]
        assert timestamps == sorted(timestamps, reverse=True)

    def test_thread_safety(self, pipeline):
        """8. 线程安全: 并发写入不丢失数据"""
        n = 200
        errors = []

        def writer(uid_start):
            try:
                for i in range(n):
                    pipeline.record_interaction(
                        f"user_{uid_start}", f"item_{i}", "view"
                    )
            except Exception as e:
                errors.append(e)

        t1 = threading.Thread(target=writer, args=(1,))
        t2 = threading.Thread(target=writer, args=(2,))
        t3 = threading.Thread(target=writer, args=(3,))

        t1.start()
        t2.start()
        t3.start()
        t1.join()
        t2.join()
        t3.join()

        assert not errors, f"线程异常: {errors}"
        # 总数 = 3 * 200 = 600
        total = 0
        for uid in ["user_1", "user_2", "user_3"]:
            total += len(pipeline.get_user_history(uid, limit=1000))
        assert total == 600, f"期望600条, 实际{total}条"

    def test_invalid_action_raises(self, pipeline):
        """9. 无效 action 抛出 ValueError"""
        with pytest.raises(ValueError, match="无效 action"):
            pipeline.record_interaction("u1", "item1", "invalid_action")

    def test_different_users_isolated(self, pipeline):
        """10. 不同用户的交互互不干扰"""
        pipeline.record_interaction("alice", "item1", "view")
        pipeline.record_interaction("bob", "item2", "click")
        alice_hist = pipeline.get_user_history("alice")
        bob_hist = pipeline.get_user_history("bob")
        assert len(alice_hist) == 1
        assert alice_hist[0]["item_id"] == "item1"
        assert len(bob_hist) == 1
        assert bob_hist[0]["item_id"] == "item2"
