"""
AI数智名片 — 协同过滤引擎 (Collaborative Filtering Engine)
=========================================================

核心算法:
  1. ItemBasedCF: 基于匹配历史(MatchRecord)的"物品"级协同过滤
     — 将"用户"视为"物品", MatchRecord(用户A对用户B感兴趣)作为交互信号
     — 推荐: 找到用户已交互过的用户 → 推荐最相似的未交互用户
  2. UserBasedCF: 基于标签(UserTag)的用户协同过滤
     — 利用 UserTag (provide/need) 计算用户间标签相似度
     — 推荐: 找到与目标用户标签最相似的其他用户

数据源:
  - MatchRecord: user_a_id ↔ user_b_id (匹配/感兴趣关系)
  - UserTag: user_id → tag + tag_type + weight (标签向量)

内存管理:
  相似度矩阵在首次调用 build_similarity_matrix() 时构建,
  后续可周期性重建。

用法:
    cf = ItemBasedCF(min_interactions=2, top_k_similar=50)
    await cf.build_similarity_matrix(db)
    recs = await cf.recommend(user_id=42, limit=10)
    similar = await cf.get_similar_items(item_id=101, n=5)
"""

from __future__ import annotations

import json
import logging
import math
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Set, Tuple

from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.tag import MatchRecord, UserTag
from app.models.user import User

logger = logging.getLogger("app.cf_engine")

# ---------------------------------------------------------------------------
# 数据类型
# ---------------------------------------------------------------------------


@dataclass
class CFInteraction:
    """用户-用户交互原始数据 (协同过滤视角)

    在 AI数智名片 场景中:
      - user_id: 发起交互的用户
      - target_id: 被交互的目标用户 (即"物品")
      - weight: 交互强度
    """

    user_id: int
    target_id: int
    weight: float = 1.0


@dataclass
class SimilarityMatrix:
    """相似度矩阵 (内存)

    存储 target_id → [(similar_target_id, score), ...] 的映射。
    """

    # target_id → [(similar_target_id, score), ...]
    data: Dict[int, List[Tuple[int, float]]] = field(default_factory=dict)
    # 所有参与计算的 target ID 集合
    target_ids: Set[int] = field(default_factory=set)
    # 构建时间戳
    built_at: Optional[str] = None
    # 矩阵规模
    num_targets: int = 0
    num_interactions: int = 0


@dataclass
class CFRecommendation:
    """单条协同过滤推荐结果"""

    target_id: int
    score: float
    reason: str = ""


# ---------------------------------------------------------------------------
# ItemBasedCF — 基于匹配历史的物品协同过滤
# ---------------------------------------------------------------------------


class ItemBasedCF:
    """基于匹配历史的物品协同过滤引擎

    在 AI数智名片 场景中,"物品"即"用户"。
    利用 MatchRecord (谁对谁感兴趣) 构建用户间相似度矩阵,
    然后基于"用户A已对用户B/C感兴趣 → 推荐与B/C最相似的未交互用户"。

    用法:
        cf = ItemBasedCF(min_interactions=2, top_k_similar=50)
        await cf.build_similarity_matrix(db)
        recs = await cf.recommend(user_id=42, limit=10)
        similar = await cf.get_similar_items(target_id=101, n=5)
    """

    def __init__(
        self,
        min_interactions: int = 2,
        top_k_similar: int = 50,
        similarity_threshold: float = 0.05,
    ):
        """
        Args:
            min_interactions: 用户至少参与这么多次交互才参与计算
            top_k_similar: 每个"物品"保留的最相似物品数
            similarity_threshold: 相似度低于此值的忽略
        """
        self.min_interactions = min_interactions
        self.top_k_similar = top_k_similar
        self.similarity_threshold = similarity_threshold
        self.matrix = SimilarityMatrix()
        self._user_item_map: Dict[int, Set[int]] = {}  # user_id → {target_id, ...}
        self._item_user_map: Dict[int, Set[int]] = {}  # target_id → {user_id, ...}

    # ── 数据加载 ──────────────────────────────────────────────────────

    async def _load_interactions(self, db: AsyncSession) -> List[CFInteraction]:
        """从 MatchRecord 加载用户-用户交互数据

        把 MatchRecord 中 user_a_id → user_b_id 视为一次交互。
        交互来源:
          - status = 'matched' (自动匹配)
          - status = 'confirmed' (互感兴趣)

        Returns:
            List[CFInteraction]: 去重后的交互列表
        """
        interactions: List[CFInteraction] = []
        seen: Set[Tuple[int, int]] = set()

        try:
            result = await db.execute(
                select(MatchRecord).where(
                    MatchRecord.status.in_(["matched", "confirmed"]),
                )
            )
            records = result.scalars().all()

            for rec in records:
                # 双向交互: A→B 和 B→A 都视为交互
                for uid, tid in [(rec.user_a_id, rec.user_b_id), (rec.user_b_id, rec.user_a_id)]:
                    key = (uid, tid)
                    if key not in seen:
                        seen.add(key)
                        # 根据分数加权: 高匹配分 = 更强交互信号
                        weight = 1.0 + math.log1p(rec.match_score) if rec.match_score > 0 else 1.0
                        interactions.append(CFInteraction(user_id=uid, target_id=tid, weight=weight))

            logger.info("[ItemBasedCF] MatchRecord 交互加载: %d 条 (去重后)", len(interactions))
        except Exception as e:
            logger.warning("[ItemBasedCF] MatchRecord 加载失败: %s", e)

        return interactions

    # ── 矩阵构建 ──────────────────────────────────────────────────────

    async def build_similarity_matrix(self, db: AsyncSession) -> SimilarityMatrix:
        """构建用户间相似度矩阵 (余弦相似度)

        流程:
          1. 加载 MatchRecord 交互数据
          2. 构建用户-物品(用户)倒排索引
          3. 计算用户间余弦相似度
          4. 按 top_k_similar 截断保存

        Args:
            db: 异步数据库会话

        Returns:
            SimilarityMatrix: 构建好的相似度矩阵
        """
        logger.info("[ItemBasedCF] 开始构建相似度矩阵...")

        # 1. 加载数据
        interactions = await self._load_interactions(db)
        if not interactions:
            logger.warning("[ItemBasedCF] 无交互数据, 返回空矩阵")
            self.matrix = SimilarityMatrix()
            return self.matrix

        # 2. 构建 user → {target: weight} 映射
        user_targets: Dict[int, Dict[int, float]] = defaultdict(dict)
        for ia in interactions:
            user_targets[ia.user_id][ia.target_id] = ia.weight

        # 3. target → {user: weight} 倒排
        target_users: Dict[int, Dict[int, float]] = defaultdict(dict)
        for uid, targets in user_targets.items():
            for tid, w in targets.items():
                target_users[tid][uid] = w

        # 4. 过滤低频 target (被少于 min_interactions 个用户交互的忽略)
        valid_targets = {
            tid for tid, users in target_users.items()
            if len(users) >= self.min_interactions
        }
        logger.info(
            "[ItemBasedCF] 有效目标: %d / %d (min_interactions=%d)",
            len(valid_targets), len(target_users), self.min_interactions,
        )

        if not valid_targets:
            logger.warning("[ItemBasedCF] 过滤后无有效目标")
            self.matrix = SimilarityMatrix()
            return self.matrix

        # 5. 计算余弦相似度
        valid_list = sorted(valid_targets)
        cos_sim: Dict[int, List[Tuple[int, float]]] = defaultdict(list)
        total_pairs = len(valid_list) * (len(valid_list) - 1) // 2
        computed = 0

        for i in range(len(valid_list)):
            tid_a = valid_list[i]
            users_a = target_users[tid_a]
            norm_a = math.sqrt(sum(w * w for w in users_a.values()))
            if norm_a == 0:
                continue

            for j in range(i + 1, len(valid_list)):
                tid_b = valid_list[j]
                users_b = target_users[tid_b]
                norm_b = math.sqrt(sum(w * w for w in users_b.values()))
                if norm_b == 0:
                    continue

                # 计算共同用户的点积
                common_users = set(users_a.keys()) & set(users_b.keys())
                if not common_users:
                    continue

                dot_product = sum(users_a[u] * users_b[u] for u in common_users)
                similarity = dot_product / (norm_a * norm_b)

                if similarity >= self.similarity_threshold:
                    cos_sim[tid_a].append((tid_b, similarity))
                    cos_sim[tid_b].append((tid_a, similarity))

                computed += 1
                if computed % 50000 == 0:
                    logger.debug("[ItemBasedCF] 相似度计算进度: %d / %d", computed, total_pairs)

        # 6. 按相似度排序并截断
        for tid in cos_sim:
            cos_sim[tid].sort(key=lambda x: x[1], reverse=True)
            cos_sim[tid] = cos_sim[tid][: self.top_k_similar]

        logger.info(
            "[ItemBasedCF] 相似度矩阵构建完成: %d 个目标, %d 个相似对",
            len(cos_sim), sum(len(v) for v in cos_sim.values()),
        )

        # 7. 保存矩阵和映射
        self._user_item_map = {uid: set(targets.keys()) for uid, targets in user_targets.items()}
        self._item_user_map = {tid: set(users.keys()) for tid, users in target_users.items()}

        from datetime import datetime
        self.matrix = SimilarityMatrix(
            data=cos_sim,
            target_ids=valid_targets,
            built_at=datetime.utcnow().isoformat(),
            num_targets=len(cos_sim),
            num_interactions=len(interactions),
        )

        return self.matrix

    # ── 推荐 ──────────────────────────────────────────────────────────

    async def recommend(
        self,
        user_id: int,
        limit: int = 10,
    ) -> List[CFRecommendation]:
        """为用户生成 ItemBasedCF 推荐

        基于用户已交互过的 "物品" (即其他用户),
        推荐与这些物品最相似的、用户尚未交互过的物品。

        Args:
            user_id: 目标用户 ID
            limit: 返回的推荐数量

        Returns:
            List[CFRecommendation]: 按相似度得分降序排列
        """
        if not self.matrix.data:
            logger.warning("[ItemBasedCF] 相似度矩阵为空, 请先调用 build_similarity_matrix()")
            return []

        # 用户已交互的 target
        user_targets = self._user_item_map.get(user_id, set())
        if not user_targets:
            logger.info("[ItemBasedCF] 用户 %d 无交互历史, 无法生成推荐", user_id)
            return []

        # 候选: 用户未交互的, 但与其交互过的 target 相似
        candidate_scores: Dict[int, float] = defaultdict(float)

        for interacted_target in user_targets:
            if interacted_target not in self.matrix.data:
                continue
            for similar_target_id, sim_score in self.matrix.data[interacted_target]:
                if similar_target_id in user_targets:
                    continue  # 跳过已交互的
                candidate_scores[similar_target_id] += sim_score

        if not candidate_scores:
            logger.info("[ItemBasedCF] 用户 %d 无新物品可推荐", user_id)
            return []

        # 排序并截断
        sorted_candidates = sorted(
            candidate_scores.items(), key=lambda x: x[1], reverse=True
        )[:limit]

        recommendations = [
            CFRecommendation(
                target_id=target_id,
                score=round(score, 6),
                reason=f"基于 {len(user_targets)} 个已交互目标的协同过滤",
            )
            for target_id, score in sorted_candidates
        ]

        logger.info(
            "[ItemBasedCF] 用户 %d 推荐: %d 条 (共 %d 个候选)",
            user_id, len(recommendations), len(candidate_scores),
        )

        return recommendations

    async def get_similar_items(
        self,
        target_id: int,
        n: int = 10,
    ) -> List[CFRecommendation]:
        """获取与指定目标(用户)最相似的目标

        Args:
            target_id: 目标用户 ID
            n: 返回数量

        Returns:
            List[CFRecommendation]: 按相似度降序排列
        """
        if not self.matrix.data:
            logger.warning("[ItemBasedCF] 相似度矩阵为空")
            return []

        similar = self.matrix.data.get(target_id, [])
        if not similar:
            logger.info("[ItemBasedCF] 目标 %d 无相似记录 (可能低频或新用户)", target_id)
            return []

        result = [
            CFRecommendation(target_id=sid, score=round(score, 6), reason="物品协同过滤")
            for sid, score in similar[:n]
        ]

        logger.info("[ItemBasedCF] 目标 %d 相似: %d 条", target_id, len(result))
        return result

    # ── 状态查询 ──────────────────────────────────────────────────────

    def get_stats(self) -> dict:
        """返回 ItemBasedCF 引擎运行状态"""
        return {
            "engine": "item_based_collaborative_filtering",
            "num_targets": self.matrix.num_targets,
            "num_targets_total": len(self.matrix.target_ids),
            "num_interactions": self.matrix.num_interactions,
            "num_similar_pairs": sum(len(v) for v in self.matrix.data.values()),
            "built_at": self.matrix.built_at,
            "top_k_similar": self.top_k_similar,
            "similarity_threshold": self.similarity_threshold,
            "min_interactions": self.min_interactions,
        }


# ---------------------------------------------------------------------------
# UserBasedCF — 基于标签的用户协同过滤
# ---------------------------------------------------------------------------


class UserBasedCF:
    """基于标签(UserTag)的用户协同过滤引擎

    利用 UserTag 的 provide/need 标签构建用户标签向量,
    计算用户间的标签相似度 (余弦相似度)。
    标签重叠越多 → 相似度越高 → 推荐给彼此有共同标签的用户。

    用法:
        ucf = UserBasedCF(similarity_threshold=0.05)
        await ucf.build_similarity_matrix(db)
        recs = await ucf.recommend(user_id=42, limit=10)
    """

    def __init__(
        self,
        top_k_similar: int = 50,
        similarity_threshold: float = 0.05,
        tag_type_weight: Optional[Dict[str, float]] = None,
    ):
        """
        Args:
            top_k_similar: 每个用户保留的最相似用户数
            similarity_threshold: 相似度低于此值的忽略
            tag_type_weight: 不同类型标签的权重, 默认 {"provide": 1.0, "need": 1.0}
        """
        self.top_k_similar = top_k_similar
        self.similarity_threshold = similarity_threshold
        self.tag_type_weight = tag_type_weight or {"provide": 1.0, "need": 1.0}
        self.matrix = SimilarityMatrix()
        self._user_tag_vectors: Dict[int, Dict[str, float]] = {}  # user_id → {tag: weight}

    # ── 数据加载 ──────────────────────────────────────────────────────

    async def _load_tag_vectors(self, db: AsyncSession) -> Dict[int, Dict[str, float]]:
        """从 UserTag 加载所有用户的标签向量

        将 provide/need 标签合并为统一的用户标签向量,
        不同类型的标签按 self.tag_type_weight 加权。

        Args:
            db: 异步数据库会话

        Returns:
            Dict[int, Dict[str, float]]: user_id → {tag: combined_weight}
        """
        user_vectors: Dict[int, Dict[str, float]] = defaultdict(dict)

        try:
            result = await db.execute(select(UserTag))
            tags = result.scalars().all()

            for t in tags:
                type_weight = self.tag_type_weight.get(t.tag_type, 1.0)
                combined_weight = t.weight * type_weight
                # 如果同一用户有相同标签(跨类型), 累加权重
                if t.tag in user_vectors[t.user_id]:
                    user_vectors[t.user_id][t.tag] += combined_weight
                else:
                    user_vectors[t.user_id][t.tag] = combined_weight

            logger.info("[UserBasedCF] 标签向量加载: %d 个用户, %d 条标签",
                        len(user_vectors), len(tags))
        except Exception as e:
            logger.warning("[UserBasedCF] 标签加载失败: %s", e)

        return dict(user_vectors)

    # ── 矩阵构建 ──────────────────────────────────────────────────────

    async def build_similarity_matrix(self, db: AsyncSession) -> SimilarityMatrix:
        """构建用户标签相似度矩阵

        基于所有用户的标签向量, 计算用户间余弦相似度。

        Args:
            db: 异步数据库会话

        Returns:
            SimilarityMatrix: 构建好的相似度矩阵
        """
        logger.info("[UserBasedCF] 开始构建用户标签相似度矩阵...")

        # 1. 加载标签向量
        user_vectors = await self._load_tag_vectors(db)
        if not user_vectors:
            logger.warning("[UserBasedCF] 无标签数据, 返回空矩阵")
            self.matrix = SimilarityMatrix()
            return self.matrix

        self._user_tag_vectors = user_vectors

        # 2. 计算用户间余弦相似度
        user_ids = sorted(user_vectors.keys())
        cos_sim: Dict[int, List[Tuple[int, float]]] = defaultdict(list)
        total_pairs = len(user_ids) * (len(user_ids) - 1) // 2
        computed = 0

        for i in range(len(user_ids)):
            uid_a = user_ids[i]
            vec_a = user_vectors[uid_a]
            norm_a = math.sqrt(sum(w * w for w in vec_a.values()))
            if norm_a == 0:
                continue

            for j in range(i + 1, len(user_ids)):
                uid_b = user_ids[j]
                vec_b = user_vectors[uid_b]
                norm_b = math.sqrt(sum(w * w for w in vec_b.values()))
                if norm_b == 0:
                    continue

                # 计算共同标签的点积
                common_tags = set(vec_a.keys()) & set(vec_b.keys())
                if not common_tags:
                    continue

                dot_product = sum(vec_a[tag] * vec_b[tag] for tag in common_tags)
                similarity = dot_product / (norm_a * norm_b)

                if similarity >= self.similarity_threshold:
                    cos_sim[uid_a].append((uid_b, similarity))
                    cos_sim[uid_b].append((uid_a, similarity))

                computed += 1
                if computed % 50000 == 0:
                    logger.debug("[UserBasedCF] 相似度计算进度: %d / %d", computed, total_pairs)

        # 3. 按相似度排序并截断
        for uid in cos_sim:
            cos_sim[uid].sort(key=lambda x: x[1], reverse=True)
            cos_sim[uid] = cos_sim[uid][: self.top_k_similar]

        logger.info(
            "[UserBasedCF] 相似度矩阵构建完成: %d 个用户, %d 个相似对",
            len(cos_sim), sum(len(v) for v in cos_sim.values()),
        )

        # 4. 保存矩阵
        from datetime import datetime
        self.matrix = SimilarityMatrix(
            data=cos_sim,
            target_ids=set(user_ids),
            built_at=datetime.utcnow().isoformat(),
            num_targets=len(cos_sim),
            num_interactions=len(user_vectors),
        )

        return self.matrix

    # ── 推荐 ──────────────────────────────────────────────────────────

    async def recommend(
        self,
        user_id: int,
        limit: int = 10,
    ) -> List[CFRecommendation]:
        """为用户生成 UserBasedCF 推荐

        找到与目标用户标签最相似的 N 个用户。

        Args:
            user_id: 目标用户 ID
            limit: 返回的推荐数量

        Returns:
            List[CFRecommendation]: 按相似度得分降序排列
        """
        if not self.matrix.data:
            logger.warning("[UserBasedCF] 相似度矩阵为空, 请先调用 build_similarity_matrix()")
            return []

        similar = self.matrix.data.get(user_id, [])
        if not similar:
            logger.info("[UserBasedCF] 用户 %d 无相似用户 (可能无标签)", user_id)
            return []

        result = [
            CFRecommendation(
                target_id=sid,
                score=round(score, 6),
                reason="标签协同过滤",
            )
            for sid, score in similar[:limit]
        ]

        logger.info("[UserBasedCF] 用户 %d 推荐: %d 条", user_id, len(result))
        return result

    async def get_similar_users(
        self,
        user_id: int,
        n: int = 10,
    ) -> List[CFRecommendation]:
        """获取与指定用户最相似的用户 (别名)

        Args:
            user_id: 目标用户 ID
            n: 返回数量

        Returns:
            List[CFRecommendation]
        """
        return await self.recommend(user_id=user_id, limit=n)

    # ── 状态查询 ──────────────────────────────────────────────────────

    def get_stats(self) -> dict:
        """返回 UserBasedCF 引擎运行状态"""
        return {
            "engine": "user_based_collaborative_filtering",
            "num_users": self.matrix.num_targets,
            "num_users_total": len(self.matrix.target_ids),
            "num_tag_vectors": len(self._user_tag_vectors),
            "num_similar_pairs": sum(len(v) for v in self.matrix.data.values()),
            "built_at": self.matrix.built_at,
            "top_k_similar": self.top_k_similar,
            "similarity_threshold": self.similarity_threshold,
        }


# ---------------------------------------------------------------------------
# 统一推荐入口
# ---------------------------------------------------------------------------


async def recommend(
    db: AsyncSession,
    user_id: int,
    limit: int = 10,
    strategy: str = "hybrid",
    item_cf: Optional[ItemBasedCF] = None,
    user_cf: Optional[UserBasedCF] = None,
) -> List[dict]:
    """统一协同过滤推荐入口

    支持三种策略:
      - "item_based": 仅使用 ItemBasedCF (基于匹配历史)
      - "user_based": 仅使用 UserBasedCF (基于标签)
      - "hybrid" (默认): 融合两种策略的结果

    Args:
        db: 异步数据库会话
        user_id: 目标用户 ID
        limit: 返回数量
        strategy: 推荐策略 ("item_based" | "user_based" | "hybrid")
        item_cf: 可选的 ItemBasedCF 实例, 不传则内部创建
        user_cf: 可选的 UserBasedCF 实例, 不传则内部创建

    Returns:
        List[dict]: 每条包含 target_id, score, reason, source 等字段
    """
    results: List[dict] = []

    if strategy in ("item_based", "hybrid"):
        if item_cf is None:
            item_cf = ItemBasedCF()
            if not item_cf.matrix.data:
                await item_cf.build_similarity_matrix(db)
        elif not item_cf.matrix.data:
            await item_cf.build_similarity_matrix(db)

        item_recs = await item_cf.recommend(user_id=user_id, limit=limit * 2)
        for rec in item_recs:
            results.append({
                "target_id": rec.target_id,
                "score": rec.score,
                "reason": rec.reason,
                "source": "item_based",
            })

    if strategy in ("user_based", "hybrid"):
        if user_cf is None:
            user_cf = UserBasedCF()
            if not user_cf.matrix.data:
                await user_cf.build_similarity_matrix(db)
        elif not user_cf.matrix.data:
            await user_cf.build_similarity_matrix(db)

        user_recs = await user_cf.recommend(user_id=user_id, limit=limit * 2)
        for rec in user_recs:
            results.append({
                "target_id": rec.target_id,
                "score": rec.score,
                "reason": rec.reason,
                "source": "user_based",
            })

    if strategy == "hybrid" and results:
        # 合并排序: 相同 target 取最高分
        merged: Dict[int, dict] = {}
        for r in results:
            tid = r["target_id"]
            if tid not in merged or r["score"] > merged[tid]["score"]:
                merged[tid] = r

        # 按分数降序
        results = sorted(merged.values(), key=lambda x: x["score"], reverse=True)[:limit]

    else:
        results = sorted(results, key=lambda x: x["score"], reverse=True)[:limit]

    return results


# ---------------------------------------------------------------------------
# 单例管理 (进程内共享)
# ---------------------------------------------------------------------------

_item_cf_instance: Optional[ItemBasedCF] = None
_user_cf_instance: Optional[UserBasedCF] = None


def get_item_cf() -> ItemBasedCF:
    """获取 ItemBasedCF 单例"""
    global _item_cf_instance
    if _item_cf_instance is None:
        _item_cf_instance = ItemBasedCF()
    return _item_cf_instance


def get_user_cf() -> UserBasedCF:
    """获取 UserBasedCF 单例"""
    global _user_cf_instance
    if _user_cf_instance is None:
        _user_cf_instance = UserBasedCF()
    return _user_cf_instance


async def rebuild_item_cf_matrix(db: AsyncSession) -> SimilarityMatrix:
    """便捷函数: 重建 ItemBasedCF 矩阵"""
    engine = get_item_cf()
    return await engine.build_similarity_matrix(db)


async def rebuild_user_cf_matrix(db: AsyncSession) -> SimilarityMatrix:
    """便捷函数: 重建 UserBasedCF 矩阵"""
    engine = get_user_cf()
    return await engine.build_similarity_matrix(db)
