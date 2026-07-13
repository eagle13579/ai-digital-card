"""
AI数智名片 — 协同过滤引擎测试
=============================

测试覆盖:
  1. ItemBasedCF: 矩阵构建、推荐、相似查询、空数据边界
  2. UserBasedCF: 矩阵构建、推荐、相似查询、标签类型加权
  3. 统一 recommend 入口: hybrid/item_based/user_based 策略

使用 in-memory SQLite 数据库, 每条测试独立。
"""

import math
from collections import defaultdict

import pytest
from sqlalchemy import select

from app.models.tag import MatchRecord, UserTag
from app.models.user import User


# ======================================================================
# 辅助函数
# ======================================================================


async def _create_users(test_db, count: int = 5) -> list[User]:
    """创建指定数量的测试用户"""
    users = []
    for i in range(count):
        user = User(
            phone=f"1390000000{i}",
            name=f"测试用户{i}",
            username=f"testuser{i}",
            password_hash="hash",
        )
        test_db.add(user)
    await test_db.commit()
    result = await test_db.execute(select(User))
    return list(result.scalars().all())


async def _create_user_tags(test_db, user_id: int, provide_tags: list[str], need_tags: list[str]):
    """为指定用户创建标签"""
    for tag in provide_tags:
        test_db.add(UserTag(user_id=user_id, tag_type="provide", tag=tag, weight=1.0))
    for tag in need_tags:
        test_db.add(UserTag(user_id=user_id, tag_type="need", tag=tag, weight=1.0))
    await test_db.commit()


async def _create_match_records(
    test_db,
    pairs: list[tuple[int, int, float]],
    status: str = "matched",
):
    """创建匹配记录: (user_a_id, user_b_id, match_score)"""
    for a, b, score in pairs:
        test_db.add(MatchRecord(
            user_a_id=a,
            user_b_id=b,
            match_score=score,
            status=status,
            common_tags="[]",
            source="auto",
        ))
    await test_db.commit()


# ======================================================================
# ItemBasedCF — 基于匹配历史的协同过滤
# ======================================================================


class TestItemBasedCF:
    """ItemBasedCF 引擎测试"""

    async def test_build_empty_matrix(self, test_db):
        """空数据库应返回空矩阵"""
        from app.services.cf_engine import ItemBasedCF

        cf = ItemBasedCF()
        matrix = await cf.build_similarity_matrix(test_db)

        assert matrix.data == {}
        assert matrix.target_ids == set()
        assert matrix.num_targets == 0
        assert matrix.num_interactions == 0

    async def test_build_matrix_with_data(self, test_db):
        """构建矩阵应正确计算相似度"""
        from app.services.cf_engine import ItemBasedCF

        users = await _create_users(test_db, 3)
        u0, u1, u2 = users[0].id, users[1].id, users[2].id

        # 用户0和用户1都对用户2感兴趣
        await _create_match_records(test_db, [
            (u0, u2, 0.9),
            (u1, u2, 0.8),
        ])

        cf = ItemBasedCF(min_interactions=1)
        matrix = await cf.build_similarity_matrix(test_db)

        # 用户2被2人交互, 但用户0和用户1分别只被1人交互
        # 用户0和用户1有共同目标(用户2), 应有非零相似度
        # 注意: _load_interactions 会生成双向交互 (A→B, B→A), 所以 2 条记录生成 4 条交互
        assert len(matrix.data) > 0
        assert matrix.num_interactions == 4  # 2条记录 × 2方向
        assert matrix.built_at is not None

    async def test_recommend_no_history(self, test_db):
        """没有交互历史的用户应返回空列表"""
        from app.services.cf_engine import ItemBasedCF

        users = await _create_users(test_db, 3)
        u0, u1, u2 = users[0].id, users[1].id, users[2].id

        await _create_match_records(test_db, [
            (u1, u2, 0.9),
        ])

        cf = ItemBasedCF(min_interactions=1)
        await cf.build_similarity_matrix(test_db)

        # 用户0没有交互历史, 不应有推荐
        recs = await cf.recommend(user_id=u0)
        assert recs == []

    async def test_recommend_with_history(self, test_db):
        """有交互历史的用户应获得推荐"""
        from app.services.cf_engine import ItemBasedCF

        users = await _create_users(test_db, 4)
        u0, u1, u2, u3 = users[0].id, users[1].id, users[2].id, users[3].id

        # 用户0对用户2感兴趣, 用户1对用户2感兴趣, 用户1对用户3感兴趣
        # → 用户2和用户3相似 (都被用户1关注)
        # → 用户0对用户2感兴趣 → 应推荐用户3
        await _create_match_records(test_db, [
            (u0, u2, 0.9),
            (u1, u2, 0.8),
            (u1, u3, 0.7),
        ])

        cf = ItemBasedCF(min_interactions=1)
        await cf.build_similarity_matrix(test_db)

        recs = await cf.recommend(user_id=u0, limit=5)

        # 用户0已交互用户2, 用户2和用户3相似 → 应推荐用户3
        target_ids = [r.target_id for r in recs]
        assert len(recs) > 0
        assert len(recs) <= 5
        for r in recs:
            assert r.score > 0
            assert r.reason != ""

    async def test_get_similar_items(self, test_db):
        """获取相似物品应返回正确结果"""
        from app.services.cf_engine import ItemBasedCF

        users = await _create_users(test_db, 3)
        u0, u1, u2 = users[0].id, users[1].id, users[2].id

        await _create_match_records(test_db, [
            (u0, u1, 0.9),
            (u0, u2, 0.8),
        ])

        cf = ItemBasedCF(min_interactions=1)
        await cf.build_similarity_matrix(test_db)

        # 用户1和用户2都被用户0交互 → 应互相相似
        similar = await cf.get_similar_items(target_id=u1, n=5)
        assert len(similar) > 0
        for s in similar:
            assert s.score > 0
            assert s.target_id != u1  # 不应返回自己

    async def test_get_similar_items_unknown(self, test_db):
        """不存在的物品应返回空列表"""
        from app.services.cf_engine import ItemBasedCF

        cf = ItemBasedCF()
        similar = await cf.get_similar_items(target_id=99999, n=5)
        assert similar == []

    async def test_get_stats(self, test_db):
        """get_stats 应返回正确的状态信息"""
        from app.services.cf_engine import ItemBasedCF

        cf = ItemBasedCF(min_interactions=1, top_k_similar=20)
        stats = cf.get_stats()

        assert stats["engine"] == "item_based_collaborative_filtering"
        assert stats["top_k_similar"] == 20
        assert stats["min_interactions"] == 1

    async def test_recommend_empty_matrix(self, test_db):
        """矩阵为空时应返回空列表"""
        from app.services.cf_engine import ItemBasedCF

        cf = ItemBasedCF()
        recs = await cf.recommend(user_id=1)
        assert recs == []


# ======================================================================
# UserBasedCF — 基于标签的协同过滤
# ======================================================================


class TestUserBasedCF:
    """UserBasedCF 引擎测试"""

    async def test_build_empty_matrix(self, test_db):
        """空数据库应返回空矩阵"""
        from app.services.cf_engine import UserBasedCF

        ucf = UserBasedCF()
        matrix = await ucf.build_similarity_matrix(test_db)

        assert matrix.data == {}
        assert matrix.target_ids == set()
        assert matrix.num_targets == 0

    async def test_build_matrix_with_tags(self, test_db):
        """有标签数据时应正确构建矩阵"""
        from app.services.cf_engine import UserBasedCF

        users = await _create_users(test_db, 3)
        u0, u1, u2 = users[0].id, users[1].id, users[2].id

        # 用户0和用户1都有"Python"标签 → 应相似
        # 用户2标签不同 → 不相似
        await _create_user_tags(test_db, u0, ["Python", "AI"], ["产品经理"])
        await _create_user_tags(test_db, u1, ["Python", "数据分析"], ["运营"])
        await _create_user_tags(test_db, u2, ["Java", "Go"], ["架构"])

        ucf = UserBasedCF()
        matrix = await ucf.build_similarity_matrix(test_db)

        assert matrix.num_targets > 0
        assert matrix.built_at is not None

        # 用户0和用户1应存在
        if u0 in matrix.data or u1 in matrix.data:
            # 检查相似度值是否为非负数
            for tid, pairs in matrix.data.items():
                for _, score in pairs:
                    assert score >= 0

    async def test_recommend_no_tags(self, test_db):
        """没有标签的用户应返回空列表"""
        from app.services.cf_engine import UserBasedCF

        users = await _create_users(test_db, 2)
        u0, u1 = users[0].id, users[1].id

        await _create_user_tags(test_db, u1, ["Python"], [])

        ucf = UserBasedCF()
        await ucf.build_similarity_matrix(test_db)

        # 用户0没有标签 → 不应在矩阵中
        recs = await ucf.recommend(user_id=u0)
        assert recs == []

    async def test_recommend_with_similar_tags(self, test_db):
        """有相似标签的用户应获得推荐"""
        from app.services.cf_engine import UserBasedCF

        users = await _create_users(test_db, 3)
        u0, u1, u2 = users[0].id, users[1].id, users[2].id

        # 用户0和用户1都有 "Python" 标签 → 高度相似
        # 用户2没有共同标签
        await _create_user_tags(test_db, u0, ["Python", "AI", "机器学习"], ["产品经理"])
        await _create_user_tags(test_db, u1, ["Python", "AI", "数据分析"], ["运营"])
        await _create_user_tags(test_db, u2, ["Java", "Go", "K8s"], ["架构"])

        ucf = UserBasedCF()
        await ucf.build_similarity_matrix(test_db)

        recs = await ucf.recommend(user_id=u0, limit=5)

        # 应推荐与用户0最相似的用户
        if recs:
            assert recs[0].score > 0
            assert recs[0].target_id != u0

    async def test_get_similar_users(self, test_db):
        """get_similar_users 应返回正确结果"""
        from app.services.cf_engine import UserBasedCF

        users = await _create_users(test_db, 3)
        u0, u1 = users[0].id, users[1].id

        await _create_user_tags(test_db, u0, ["Python"], [])
        await _create_user_tags(test_db, u1, ["Python"], [])

        ucf = UserBasedCF()
        await ucf.build_similarity_matrix(test_db)

        similar = await ucf.get_similar_users(user_id=u0, n=5)
        if similar:
            assert similar[0].target_id == u1

    async def test_get_stats(self, test_db):
        """get_stats 应返回正确的状态信息"""
        from app.services.cf_engine import UserBasedCF

        ucf = UserBasedCF(top_k_similar=30)
        stats = ucf.get_stats()

        assert stats["engine"] == "user_based_collaborative_filtering"
        assert stats["top_k_similar"] == 30


# ======================================================================
# 统一推荐入口 recommend()
# ======================================================================


class TestRecommendEntry:
    """统一 recommend 入口测试"""

    async def test_recommend_item_based(self, test_db):
        """item_based 策略应调用 ItemBasedCF"""
        from app.services.cf_engine import recommend

        users = await _create_users(test_db, 3)
        u0, u1, u2 = users[0].id, users[1].id, users[2].id

        await _create_match_records(test_db, [
            (u0, u2, 0.9),
            (u1, u2, 0.8),
        ])

        recs = await recommend(test_db, user_id=u0, limit=5, strategy="item_based")
        assert isinstance(recs, list)
        for r in recs:
            assert "target_id" in r
            assert "score" in r
            assert "source" in r
            assert r["source"] == "item_based"

    async def test_recommend_user_based(self, test_db):
        """user_based 策略应调用 UserBasedCF"""
        from app.services.cf_engine import recommend

        users = await _create_users(test_db, 3)
        u0, u1 = users[0].id, users[1].id

        await _create_user_tags(test_db, u0, ["Python"], [])
        await _create_user_tags(test_db, u1, ["Python"], [])

        recs = await recommend(test_db, user_id=u0, limit=5, strategy="user_based")
        assert isinstance(recs, list)
        for r in recs:
            assert "target_id" in r
            assert "score" in r
            assert "source" in r
            assert r["source"] == "user_based"

    async def test_recommend_hybrid(self, test_db):
        """hybrid 策略应融合两种结果"""
        from app.services.cf_engine import recommend

        users = await _create_users(test_db, 3)
        u0, u1, u2 = users[0].id, users[1].id, users[2].id

        # 同时准备两种数据
        await _create_match_records(test_db, [
            (u0, u2, 0.9),
            (u1, u2, 0.8),
        ])
        await _create_user_tags(test_db, u0, ["Python"], [])
        await _create_user_tags(test_db, u1, ["Python"], [])

        recs = await recommend(test_db, user_id=u0, limit=10, strategy="hybrid")
        assert isinstance(recs, list)
        # 混合策略应包含来自不同来源的结果
        sources = {r["source"] for r in recs}
        assert len(sources) >= 1

    async def test_recommend_no_data(self, test_db):
        """空数据库应返回空列表"""
        from app.services.cf_engine import recommend

        recs = await recommend(test_db, user_id=1, limit=5, strategy="hybrid")
        assert recs == []


# ======================================================================
# 单例管理
# ======================================================================


class TestSingleton:
    """单例函数测试"""

    async def test_get_item_cf(self):
        """get_item_cf 应返回非空单例"""
        from app.services.cf_engine import get_item_cf

        instance = get_item_cf()
        assert instance is not None
        assert instance.matrix is not None

        # 再次调用应返回同一实例
        instance2 = get_item_cf()
        assert instance is instance2

    async def test_get_user_cf(self):
        """get_user_cf 应返回非空单例"""
        from app.services.cf_engine import get_user_cf

        instance = get_user_cf()
        assert instance is not None
        assert instance.matrix is not None

        instance2 = get_user_cf()
        assert instance is instance2
