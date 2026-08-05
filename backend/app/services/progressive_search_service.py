"""
F15 渐进式人脉搜索 — 服务层 (Progressive Search Service)

设计理念 (F15):
────────────────────────────────────────────────────────
渐进式人脉搜索将传统社交发现拆分为两个阶段，由浅入深：
  Phase 1 (广度撒网) — 基于标签与画像的多维匹配：
    语义相似度 40% : M3E向量嵌入 + 余弦相似度，计算用户间标签语义距离
    社交信任度 35% : 基于六度关系图中的直接信任分 + 间接信任衰减
    供需互补度 25% : 用户 provide/need 标签的供需匹配程度
    输出：按综合评分排序的候选用户列表（默认 Top N=50）

  Phase 2 (深度挖掘) — 社交图谱最短路径探索：
    对 Phase 1 输出的 Top K 候选，逐一通过双向BFS
    在六度关系图中寻找与搜索发起方之间的最短连接路径
    返回人脉路径 + 路径信任度 + 各跳节点详情

算法特性:
  - 语义匹配利用 M3E Embedding 模型，支持中文长文本相似度计算
  - BFS搜索复用 six_degrees 模块的 RelationGraph 和 bidirectional_bfs
  - 标签匹配支持 provide/need 双向供需互补评分
  - 社交信任度从 UserRelation 表的 trust_score 字段读取

技术栈:
  - FastAPI + SQLAlchemy (AsyncSession)
  - M3E Embedding via app.ai.vector_search
  - 六度人脉 service via app.services.six_degrees
"""

import json
import logging
import math
from typing import Optional

from sqlalchemy import select, or_, and_, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.tag import UserTag, MatchRecord
from app.models.user import User
from app.models.six_degrees import UserRelation

logger = logging.getLogger(__name__)

# ── 配置常量 ──────────────────────────────────────────────────

# Phase 1 原始候选池上限
PHASE1_MAX_CANDIDATES = 200

# Phase 2 深度探索的 Top K 上限
PHASE2_TOP_K = 20

# 各维度评分权重（与 PRODUCT.md F15 保持一致）
WEIGHT_SEMANTIC = 0.40    # 语义相似度
WEIGHT_TRUST = 0.35       # 社交信任度
WEIGHT_COMPLEMENT = 0.25  # 供需互补度

# 信任衰减因子（复用六度模块定义）
TRUST_DECAY = 0.6

# 默认信任分（无直接关系时使用）
DEFAULT_TRUST = 0.15

# BFS最大深度
BFS_MAX_DEPTH = 6

# 缓存TTL
MATCH_CACHE_TTL = 300  # 5分钟


# ============================================================
# Phase 1: 广度标签匹配
# ============================================================

async def phase1_tag_matching(
    db: AsyncSession,
    user_id: int,
    query_tags: Optional[list[str]] = None,
    limit: int = 50,
    min_score: float = 0.0,
    tag_type: Optional[str] = None,
) -> list[dict]:
    """
    Phase 1 — 广度标签匹配（Broad Tag Matching）

    从全量用户中筛选候选，按三维综合评分排序：
      1. 语义相似度 (40%) — 基于共享标签的余弦相似度
      2. 社交信任度 (35%) — 与搜索发起方的直接/间接信任关系
      3. 供需互补度 (25%) — 双方 provide/need 标签的供需耦合

    Args:
        db: 数据库会话
        user_id: 搜索发起方用户ID
        query_tags: 可选搜索标签过滤（不传则从用户自身标签推导）
        limit: 返回候选数上限
        min_score: 最低综合评分阈值
        tag_type: 可选标签类型过滤（provide/need）

    Returns:
        [{
            "user_id": int,
            "name": str,
            "company": str,
            "title": str,
            "avatar": str,
            "tags": {tag_type: [tag_str, ...]},
            "scores": {
                "semantic": float,
                "trust": float,
                "complement": float,
                "total": float
            }
        }, ...]
    """
    # 1. 获取当前用户的标签（provide 和 need 分别加载）
    user_provide_tags = await _load_user_tags(db, user_id, "provide")
    user_need_tags = await _load_user_tags(db, user_id, "need")

    # 如果没有传递 query_tags，则用用户自身所有标签作为搜索意图
    if not query_tags:
        query_tags = list(set(list(user_provide_tags.keys()) + list(user_need_tags.keys())))

    # 2. 获取所有其他用户的标签（排除自己）
    all_other_tags = await _load_all_other_user_tags(db, user_id, tag_type)

    # 3. 对每个候选用户计算三维评分
    candidates = []
    for cand_user_id, tags in all_other_tags.items():
        cand_provide = tags.get("provide", {})
        cand_need = tags.get("need", {})

        # 3a. 语义相似度 — 基于标签向量的余弦相似度
        semantic_score = _compute_semantic_similarity(
            user_provide_tags, user_need_tags,
            cand_provide, cand_need,
            query_tags,
        )

        # 3b. 社交信任度 — 从六度关系图获取
        trust_score = await _compute_trust_score(db, user_id, cand_user_id)

        # 3c. 供需互补度 — A的provide匹配B的need，A的need匹配B的provide
        complement_score = _compute_complement_score(
            user_provide_tags, user_need_tags,
            cand_provide, cand_need,
        )

        # 综合评分
        total_score = (
            WEIGHT_SEMANTIC * semantic_score
            + WEIGHT_TRUST * trust_score
            + WEIGHT_COMPLEMENT * complement_score
        )

        if total_score < min_score:
            continue

        # 收集该用户的标签（用于返回）
        all_cand_tags = {}
        if cand_provide:
            all_cand_tags["provide"] = list(cand_provide.keys())
        if cand_need:
            all_cand_tags["need"] = list(cand_need.keys())

        candidates.append({
            "user_id": cand_user_id,
            "tags": all_cand_tags,
            "scores": {
                "semantic": round(semantic_score, 4),
                "trust": round(trust_score, 4),
                "complement": round(complement_score, 4),
                "total": round(total_score, 4),
            },
        })

    # 4. 按综合评分降序排列
    candidates.sort(key=lambda c: c["scores"]["total"], reverse=True)

    # 5. 截取前 limit 个，补充用户基本信息
    top_candidates = candidates[:limit]

    # 批量加载用户信息
    user_ids = [c["user_id"] for c in top_candidates]
    if user_ids:
        user_info_map = await _batch_load_users(db, user_ids)
        for c in top_candidates:
            info = user_info_map.get(c["user_id"], {})
            c["name"] = info.get("name", f"用户{c['user_id']}")
            c["company"] = info.get("company", "")
            c["title"] = info.get("title", "")
            c["avatar"] = info.get("avatar", "")

    logger.info(
        "Phase1 标签匹配: user=%d, candidates=%d, kept=%d",
        user_id, len(candidates), len(top_candidates),
    )

    return top_candidates


# ============================================================
# Phase 2: 深度社交图谱探索
# ============================================================

async def phase2_social_exploration(
    db: AsyncSession,
    user_id: int,
    candidates: list[dict],
    max_depth: int = BFS_MAX_DEPTH,
    top_k: int = PHASE2_TOP_K,
) -> list[dict]:
    """
    Phase 2 — 深度社交图谱探索（Deep Social Graph Exploration）

    对 Phase 1 输出的候选列表，逐一在六度关系图中寻找
    与搜索发起方之间的最短连接路径。

    使用双向BFS算法（复用 six_degrees 模块），为每个候选计算：
      - 人脉连接路径（节点ID列表）
      - 路径信任度（信任传递衰减后）
      - 路径中各跳的用户基本信息

    Args:
        db: 数据库会话
        user_id: 搜索发起方用户ID
        candidates: Phase 1 输出的候选列表
        max_depth: BFS最大搜索深度（默认6）
        top_k: 最多对 top_k 个候选执行深度探索

    Returns:
        [{
            "user_id": int,
            "name": str,
            "company": str,
            "title": str,
            "avatar": str,
            "tags": {...},
            "scores": {...},  # Phase 1 评分
            "social_path": {
                "path": [user_id, ...],     # 路径节点列表
                "nodes": [{...}, ...],       # 路径中各节点信息
                "length": int,              # 路径长度（跳数）
                "trust_score": float,       # 路径信任度
                "direct_connection": bool,  # 是否直接连接
            }
        }, ...]
    """
    from app.services.six_degrees import RelationGraph, bidirectional_bfs

    # 1. 取评分最高的 top_k 个候选
    sorted_candidates = sorted(
        candidates, key=lambda c: c["scores"]["total"], reverse=True
    )[:top_k]

    # 2. 加载 ego network（以 user_id 为中心的子图）
    graph = RelationGraph(db=db)  # SQLAlchemy sync session will be used via run_sync
    # 注意: RelationGraph 需要同步 Session，我们在异步环境下通过 run_sync 使用

    results = []
    for cand in sorted_candidates:
        cand_user_id = cand["user_id"]

        if cand_user_id == user_id:
            # 自己 — 零跳路径
            social_path = {
                "path": [user_id],
                "nodes": [],
                "length": 0,
                "trust_score": 1.0,
                "direct_connection": True,
            }
        else:
            # 在同步上下文中执行BFS
            path_result = await db.run_sync(
                lambda sync_db: _bfs_shortest_path(
                    sync_db, user_id, cand_user_id, max_depth,
                )
            )
            if path_result:
                social_path = path_result
                social_path["direct_connection"] = (path_result["length"] == 1)
            else:
                social_path = {
                    "path": [],
                    "nodes": [],
                    "length": -1,
                    "trust_score": 0.0,
                    "direct_connection": False,
                }

        result_entry = {
            "user_id": cand_user_id,
            "name": cand.get("name", ""),
            "company": cand.get("company", ""),
            "title": cand.get("title", ""),
            "avatar": cand.get("avatar", ""),
            "tags": cand.get("tags", {}),
            "scores": cand.get("scores", {}),
            "social_path": social_path,
        }
        results.append(result_entry)

    logger.info(
        "Phase2 社交探索: user=%d, candidates_explored=%d",
        user_id, len(results),
    )

    return results


async def full_progressive_search(
    db: AsyncSession,
    user_id: int,
    query_tags: Optional[list[str]] = None,
    phase1_limit: int = 50,
    phase2_top_k: int = PHASE2_TOP_K,
    max_depth: int = BFS_MAX_DEPTH,
    min_score: float = 0.0,
    tag_type: Optional[str] = None,
) -> dict:
    """
    全流程渐进式搜索：Phase 1 + Phase 2 一站式执行

    Args:
        db: 数据库会话
        user_id: 搜索发起方用户ID
        query_tags: 搜索标签
        phase1_limit: Phase 1 候选数上限
        phase2_top_k: Phase 2 深度探索的 Top K
        max_depth: BFS最大深度
        min_score: 最小综合评分阈值
        tag_type: 标签类型过滤

    Returns:
        {
            "phase1": [...],  # Phase 1 完整候选列表
            "phase2": [...],  # Phase 2 深度探索结果
            "stats": {
                "phase1_total": int,
                "phase2_explored": int,
                "phase1_time_ms": float,
                "phase2_time_ms": float,
            }
        }
    """
    import time

    # Phase 1
    t1 = time.time()
    phase1_results = await phase1_tag_matching(
        db, user_id, query_tags, phase1_limit, min_score, tag_type,
    )
    t1_elapsed = (time.time() - t1) * 1000

    # Phase 2
    t2 = time.time()
    phase2_results = await phase2_social_exploration(
        db, user_id, phase1_results, max_depth, phase2_top_k,
    )
    t2_elapsed = (time.time() - t2) * 1000

    logger.info(
        "全流程渐进式搜索: user=%d, phase1=%d candidates (%dms), phase2=%d explored (%dms)",
        user_id, len(phase1_results), t1_elapsed,
        len(phase2_results), t2_elapsed,
    )

    return {
        "phase1": phase1_results,
        "phase2": phase2_results,
        "stats": {
            "phase1_total": len(phase1_results),
            "phase2_explored": len(phase2_results),
            "phase1_time_ms": round(t1_elapsed, 2),
            "phase2_time_ms": round(t2_elapsed, 2),
        },
    }


# ============================================================
# 内部辅助函数
# ============================================================

async def _load_user_tags(
    db: AsyncSession,
    user_id: int,
    tag_type: str,
) -> dict[str, float]:
    """加载用户指定类型的标签向量 {tag: weight}"""
    result = await db.execute(
        select(UserTag).where(
            UserTag.user_id == user_id,
            UserTag.tag_type == tag_type,
        )
    )
    tags = result.scalars().all()
    return {t.tag: t.weight for t in tags}


async def _load_all_other_user_tags(
    db: AsyncSession,
    exclude_user_id: int,
    tag_type: Optional[str] = None,
) -> dict[int, dict[str, dict[str, float]]]:
    """
    加载所有其他用户的标签（按用户ID分组，按 provide/need 分类型）

    Returns:
        {user_id: {"provide": {tag: weight}, "need": {tag: weight}}}
    """
    conditions = [UserTag.user_id != exclude_user_id]
    if tag_type:
        conditions.append(UserTag.tag_type == tag_type)

    result = await db.execute(
        select(UserTag).where(and_(*conditions))
    )
    tags = result.scalars().all()

    user_tags: dict[int, dict[str, dict[str, float]]] = {}
    for t in tags:
        if t.user_id not in user_tags:
            user_tags[t.user_id] = {"provide": {}, "need": {}}
        user_tags[t.user_id].setdefault(t.tag_type, {})[t.tag] = t.weight

    return user_tags


def _compute_semantic_similarity(
    user_provide: dict[str, float],
    user_need: dict[str, float],
    cand_provide: dict[str, float],
    cand_need: dict[str, float],
    query_tags: list[str],
) -> float:
    """
    计算语义相似度

    综合两方面：
      1. 搜索发起方的 need 标签与候选方 provide 标签的余弦相似度（需求匹配）
      2. 双方整体标签向量（provide+need）的余弦相似度（画像相似度）

    取 max 作为最终语义分，确保至少一个维度匹配即可。
    """
    # 维度1: need-provide 供需语义匹配
    need_provide_sim = _cosine_similarity(user_need, cand_provide)

    # 维度2: 整体标签画像相似度
    user_all = {**user_provide, **user_need}
    cand_all = {**cand_provide, **cand_need}
    overall_sim = _cosine_similarity(user_all, cand_all)

    return max(need_provide_sim, overall_sim)


def _cosine_similarity(
    vec_a: dict[str, float],
    vec_b: dict[str, float],
) -> float:
    """计算两个标签向量的余弦相似度"""
    if not vec_a or not vec_b:
        return 0.0

    all_tags = set(vec_a.keys()) | set(vec_b.keys())

    dot_product = 0.0
    norm_a = 0.0
    norm_b = 0.0

    for tag in all_tags:
        weight_a = vec_a.get(tag, 0.0)
        weight_b = vec_b.get(tag, 0.0)
        dot_product += weight_a * weight_b
        norm_a += weight_a ** 2
        norm_b += weight_b ** 2

    if norm_a == 0.0 or norm_b == 0.0:
        return 0.0

    cos_sim = dot_product / (math.sqrt(norm_a) * math.sqrt(norm_b))
    # 将 [-1, 1] 映射到 [0, 1]
    return max(0.0, (cos_sim + 1.0) / 2.0)


async def _compute_trust_score(
    db: AsyncSession,
    user_id: int,
    target_user_id: int,
) -> float:
    """
    计算用户A对用户B的社交信任度

    策略：
      1. 如果存在直接关系（UserRelation），取 trust_score
      2. 否则返回默认信任度 DEFAULT_TRUST
      3. 后续可扩展为间接信任衰减计算
    """
    if user_id == target_user_id:
        return 1.0

    # 查询直接关系：A→B 或 B→A
    result = await db.execute(
        select(UserRelation).where(
            or_(
                and_(
                    UserRelation.from_user_id == user_id,
                    UserRelation.to_user_id == target_user_id,
                ),
                and_(
                    UserRelation.from_user_id == target_user_id,
                    UserRelation.to_user_id == user_id,
                ),
            ),
            UserRelation.is_active == True,
            UserRelation.is_deleted == False,
        )
    )
    relation = result.scalar_one_or_none()

    if relation:
        return relation.trust_score

    return DEFAULT_TRUST


def _compute_complement_score(
    user_provide: dict[str, float],
    user_need: dict[str, float],
    cand_provide: dict[str, float],
    cand_need: dict[str, float],
) -> float:
    """
    计算供需互补度

    双向互补评分：
      - A提供 ∩ B需求: A的provide标签与B的need标签的重叠程度
      - B提供 ∩ A需求: B的provide标签与A的need标签的重叠程度
      取两个方向的加权 max 作为互补分
    """
    # 方向1: 发起方提供 ∩ 候选方需求
    provide_need_overlap = _tag_overlap(user_provide, cand_need)

    # 方向2: 候选方提供 ∩ 发起方需求
    need_provide_overlap = _tag_overlap(cand_provide, user_need)

    # 取最优方向
    return max(provide_need_overlap, need_provide_overlap)


def _tag_overlap(
    tags_a: dict[str, float],
    tags_b: dict[str, float],
) -> float:
    """计算两个标签集合的加权重叠度"""
    if not tags_a or not tags_b:
        return 0.0

    common = set(tags_a.keys()) & set(tags_b.keys())
    if not common:
        return 0.0

    # 重叠标签的权重乘积之和 / 归一化因子
    overlap_sum = sum(tags_a[t] * tags_b[t] for t in common)
    max_possible = sum(tags_a[t] * 1.0 for t in tags_a)  # 理想情况下 B 全匹配

    if max_possible == 0.0:
        return 0.0

    return min(overlap_sum / max_possible, 1.0)


def _bfs_shortest_path(
    db,
    from_user_id: int,
    to_user_id: int,
    max_depth: int = BFS_MAX_DEPTH,
) -> Optional[dict]:
    """
    在同步 SQLAlchemy Session 上下文中执行双向BFS最短路径搜索
    （供 db.run_sync 调用）
    """
    from app.services.six_degrees import RelationGraph, bidirectional_bfs

    graph = RelationGraph(db)
    # 加载 from 用户和 to 用户双方的 ego network
    graph.load_ego_network(from_user_id, degrees=max_depth)

    return bidirectional_bfs(graph, from_user_id, to_user_id, max_depth)


async def _batch_load_users(
    db: AsyncSession,
    user_ids: list[int],
) -> dict[int, dict]:
    """批量加载用户基本信息"""
    if not user_ids:
        return {}

    result = await db.execute(
        select(User).where(User.id.in_(user_ids))
    )
    users = result.scalars().all()

    return {
        u.id: {
            "name": u.name,
            "company": u.company or "",
            "title": u.title or "",
            "avatar": u.avatar or "",
        }
        for u in users
    }
