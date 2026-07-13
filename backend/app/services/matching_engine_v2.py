"""
匹配引擎 V2 — 五层综合评分（标签重叠 + 语义相似 + 标签权重 + 行业互补 + 注意力匹配）

基于 MatchEngine V1 升级，新增行业互补分析和多头注意力匹配机制。
评分公式（目标匹配度 ≥ 90%）:

    综合评分 = tag_overlap         × 0.35
              + vector_semantic    × 0.25
              + tag_weight         × 0.10
              + industry_complement × 0.20   ← 新增
              + attention_score     × 0.10   ← 新增（调用 AttentionMatcher）

使用方式:
    from app.services.matching_engine_v2 import MatchEngineV2

    score = await MatchEngineV2.compute_similarity_v2(db, user_a_id, user_b_id)
    results = await MatchEngineV2.hybrid_search_v2(db, query_text, user_id)
"""

from __future__ import annotations

import json
import math
from typing import Any, Optional

from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.attention_matcher import AttentionMatcher, UserFeatures
from app.ai.mmr_diversity import MMRDiversityEngine
from app.ai.vector_search import VectorSearchEngine
from app.cache import cache
from app.models.tag import MatchRecord, UserTag
from app.models.user import User
from app.models.brochure import Brochure, Page
from app.services.matching_engine import MatchEngine

# ── 行业互补配置 ─────────────────────────────────────────────────────────

# 10 类行业供需要素
INDUSTRY_CATEGORIES: list[str] = [
    "AI/科技", "金融/投资", "制造/工业", "教育/培训",
    "医疗/健康", "地产/物业", "电商/零售", "法律/合规",
    "品牌/营销", "传媒/内容",
]

# 行业 → 候选标签关键词（用于从用户标签中匹配行业）
INDUSTRY_KEYWORDS: dict[str, list[str]] = {
    "AI/科技":    ["ai", "人工智能", "科技", "互联网", "saas", "软件", "大数据", "云计算", "算法"],
    "金融/投资":  ["金融", "投资", "证券", "基金", "保险", "银行", "理财", "风控"],
    "制造/工业":  ["制造", "工业", "工厂", "生产", "供应链", "物流", "硬件", "芯片"],
    "教育/培训":  ["教育", "培训", "课程", "教学", "学习", "知识付费"],
    "医疗/健康":  ["医疗", "健康", "医药", "医院", "养生", "健身", "生物"],
    "地产/物业":  ["地产", "房产", "物业", "建筑", "装修", "家居"],
    "电商/零售":  ["电商", "零售", "跨境电商", "直播带货", "新零售", "o2o"],
    "法律/合规":  ["法律", "合规", "律师", "法务", "知识产权", "税务"],
    "品牌/营销":  ["品牌", "营销", "广告", "公关", "市场", "推广", "增长"],
    "传媒/内容":  ["传媒", "内容", "短视频", "自媒体", "新媒体", "影视", "娱乐"],
}

# 供需映射表：源头行业 → 可互补的目标行业列表
INDUSTRY_SUPPLY_DEMAND_MAP: dict[str, list[str]] = {
    "AI/科技":   ["制造/工业", "医疗/健康", "教育/培训", "金融/投资"],
    "金融/投资": ["AI/科技", "制造/工业", "医疗/健康"],
    "制造/工业": ["AI/科技", "电商/零售"],
    "品牌/营销": ["电商/零售", "教育/培训", "医疗/健康"],
    "传媒/内容": ["电商/零售", "品牌/营销"],
    "法律/合规": ["金融/投资", "AI/科技"],
}

# 同行业互补加分
SAME_INDUSTRY_BONUS: float = 0.1
# 跨行业供需互补加分
CROSS_INDUSTRY_BONUS: float = 0.3

# ── 五层评分权重系数 ───────────────────────────────────────────────────

WEIGHTS_V2: dict[str, float] = {
    "tag_overlap":         0.35,
    "vector_semantic":     0.25,
    "tag_weight":          0.10,
    "industry_complement": 0.20,
    "attention_score":     0.10,
}


# ======================================================================
# MatchEngineV2 — 升级版匹配引擎
# ======================================================================


class MatchEngineV2:
    """匹配引擎 V2 — 五层综合评分

    相比 MatchEngine V1 新增:
        - industry_complement: 行业互补分析（10类行业供需映射）
        - attention_score: 多头注意力匹配（调用 AttentionMatcher）
        - MMR 多样性后处理（hybrid_search_v2）

    评分公式:
        score = tag_overlap * 0.35 + vector_semantic * 0.25
              + tag_weight * 0.10 + industry_complement * 0.20
              + attention_score * 0.10
    """

    # ── 行业检测 ─────────────────────────────────────────────────────

    @staticmethod
    def _detect_industries(
        provide_tags: dict[str, float],
        need_tags: dict[str, float],
    ) -> list[str]:
        """从用户标签中检测所属行业类别

        扫描用户的所有提供/需要标签，匹配预定义的行业关键词表。

        Args:
            provide_tags: 用户提供的标签向量 {tag: weight}
            need_tags: 用户需要的标签向量 {tag: weight}

        Returns:
            检测到的行业列表
        """
        all_tag_names = set(provide_tags.keys()) | set(need_tags.keys())
        detected: list[str] = []

        for industry, keywords in INDUSTRY_KEYWORDS.items():
            for tag in all_tag_names:
                tag_lower = tag.lower()
                for kw in keywords:
                    if kw in tag_lower or tag_lower in kw:
                        detected.append(industry)
                        break
                # 一个行业只记录一次
                if detected and detected[-1] == industry:
                    break

        return detected

    # ── 行业互补评分 ──────────────────────────────────────────────────

    @staticmethod
    def _industry_complement_score(
        provide_a: dict[str, float],
        need_a: dict[str, float],
        provide_b: dict[str, float],
        need_b: dict[str, float],
    ) -> float:
        """计算行业互补分数

        算法:
            1. 检测用户A和用户B的行业类别
            2. 对每对(A行业, B行业):
               - 同类行业 +0.1 (SAME_INDUSTRY_BONUS)
               - 供需互补 +0.3 (CROSS_INDUSTRY_BONUS)
            3. 得分 = 总加分 / max(1, 比较次数)，归一化到 [0, 1]

        Args:
            provide_a: 用户A的提供标签向量
            need_a: 用户A的需要标签向量
            provide_b: 用户B的提供标签向量
            need_b: 用户B的需要标签向量

        Returns:
            行业互补分数 [0, 1]
        """
        industries_a = MatchEngineV2._detect_industries(provide_a, need_a)
        industries_b = MatchEngineV2._detect_industries(provide_b, need_b)

        if not industries_a or not industries_b:
            return 0.0

        total_score = 0.0
        comparisons = 0

        for ind_a in industries_a:
            for ind_b in industries_b:
                comparisons += 1

                if ind_a == ind_b:
                    # 同类行业互补
                    total_score += SAME_INDUSTRY_BONUS
                else:
                    # 检查是否存在供需互补关系
                    supply_partners = INDUSTRY_SUPPLY_DEMAND_MAP.get(ind_a, [])
                    if ind_b in supply_partners:
                        total_score += CROSS_INDUSTRY_BONUS
                    else:
                        # 反向检查
                        reverse_partners = INDUSTRY_SUPPLY_DEMAND_MAP.get(ind_b, [])
                        if ind_a in reverse_partners:
                            total_score += CROSS_INDUSTRY_BONUS

        # 归一化到 [0, 1]
        normalized = total_score / max(1.0, float(comparisons))
        return min(1.0, normalized)

    # ── 注意力匹配评分 ────────────────────────────────────────────────

    @staticmethod
    def _build_user_features(
        provide_a: dict[str, float],
        need_a: dict[str, float],
        provide_b: dict[str, float],
        need_b: dict[str, float],
    ) -> tuple[UserFeatures, UserFeatures]:
        """从标签向量构建 UserFeatures（用于 AttentionMatcher）

        行业头: 从标签中检测行业关键词
        能力头: 提供标签 → capabilities
        地区头: 从标签中检测地区关键词
        热度头: 默认 0.5

        Args:
            provide_a: 用户A的提供标签
            need_a: 用户A的需要标签
            provide_b: 用户B的提供标签
            need_b: 用户B的需要标签

        Returns:
            (user_a_features, user_b_features)
        """
        # 行业检测
        industries_a = MatchEngineV2._detect_industries(provide_a, need_a)
        industries_b = MatchEngineV2._detect_industries(provide_b, need_b)

        # 能力头 = 提供标签的键名列表
        capabilities_a = list(provide_a.keys())
        capabilities_b = list(provide_b.keys())

        # 地区检测：从所有标签中查找地区关键词
        region_keywords = ["北京", "上海", "广州", "深圳", "杭州", "成都",
                           "武汉", "南京", "天津", "重庆", "苏州", "西安",
                           "长沙", "郑州", "东莞", "青岛", "沈阳", "宁波",
                           "昆明", "大连", "厦门", "合肥", "佛山", "福州",
                           "哈尔滨", "济南", "温州", "长春", "石家庄", "常州",
                           "泉州", "南宁", "贵阳", "南昌", "太原", "烟台",
                           "嘉兴", "南通", "金华", "珠海", "惠州", "徐州",
                           "海口", "乌鲁木齐", "绍兴", "中山", "台州", "兰州"]

        all_tags_a = set(provide_a.keys()) | set(need_a.keys())
        all_tags_b = set(provide_b.keys()) | set(need_b.keys())

        regions_a = [t for t in all_tags_a if any(r in t for r in region_keywords)]
        regions_b = [t for t in all_tags_b if any(r in t for r in region_keywords)]

        # 如果没有检测到地区，尝试从 need 标签中找
        if not regions_a:
            regions_a = list(need_a.keys())[:1] if need_a else []
        if not regions_b:
            regions_b = list(need_b.keys())[:1] if need_b else []

        features_a = UserFeatures(
            industries=industries_a,
            capabilities=capabilities_a,
            regions=regions_a,
            hotness=0.5,
        )
        features_b = UserFeatures(
            industries=industries_b,
            capabilities=capabilities_b,
            regions=regions_b,
            hotness=0.5,
        )
        return features_a, features_b

    @staticmethod
    async def _attention_score(
        provide_a: dict[str, float],
        need_a: dict[str, float],
        provide_b: dict[str, float],
        need_b: dict[str, float],
    ) -> float:
        """计算多头注意力匹配分数（调用 AttentionMatcher）

        Args:
            provide_a: 用户A提供标签向量
            need_a: 用户A需要标签向量
            provide_b: 用户B提供标签向量
            need_b: 用户B需要标签向量

        Returns:
            注意力匹配分数 [0, 1]
        """
        matcher = AttentionMatcher(temperature=0.8)
        features_a, features_b = MatchEngineV2._build_user_features(
            provide_a, need_a, provide_b, need_b,
        )
        score = await matcher.score(features_a, features_b)
        return float(score)

    # ── V2 综合评分 ──────────────────────────────────────────────────

    @staticmethod
    async def compute_similarity_v2(
        db: AsyncSession,
        user_a_id: int,
        user_b_id: int,
    ) -> dict[str, Any]:
        """V2 综合匹配度计算（五层评分）

        Args:
            db: 数据库会话
            user_a_id: 用户A ID
            user_b_id: 用户B ID

        Returns:
            匹配结果字典:
                - score: 综合评分 [0, 1]
                - tag_overlap: 标签重叠分
                - tag_overlap_raw: 标签重叠原始分
                - vector_semantic: 语义相似度
                - tag_weight: 标签权重分
                - industry_complement: 行业互补分
                - attention_score: 注意力匹配分
                - common_tags: 共同标签列表
        """
        # ── 1. 构建标签向量 ──
        provide_a = await MatchEngine._build_tag_vector(db, user_a_id, "provide")
        need_a = await MatchEngine._build_tag_vector(db, user_a_id, "need")
        provide_b = await MatchEngine._build_tag_vector(db, user_b_id, "provide")
        need_b = await MatchEngine._build_tag_vector(db, user_b_id, "need")

        # ── 2. 标签重叠分（复用 V1） ──
        overlap_raw, common_tags = MatchEngine._tag_overlap_score(
            provide_a, need_b, provide_b, need_a,
        )
        max_possible_overlap = len(common_tags) * 1.0 if common_tags else 1.0
        tag_overlap = (
            min(1.0, overlap_raw / max_possible_overlap)
            if max_possible_overlap > 0 else 0.0
        )

        # ── 3. 语义相似度（复用 V1） ──
        vector_semantic = await MatchEngine._compute_vector_semantic(
            db, user_a_id, user_b_id,
        )

        # ── 4. 标签权重分（复用 V1） ──
        tag_weight = MatchEngine._compute_tag_weight_score(
            provide_a, need_a, provide_b, need_b,
        )

        # ── 5. 行业互补分（新增 V2） ──
        industry_complement = MatchEngineV2._industry_complement_score(
            provide_a, need_a, provide_b, need_b,
        )

        # ── 6. 注意力匹配分（新增 V2） ──
        attention_score = await MatchEngineV2._attention_score(
            provide_a, need_a, provide_b, need_b,
        )

        # ── 7. 五层加权融合 ──
        final_score = (
            tag_overlap         * WEIGHTS_V2["tag_overlap"]
            + vector_semantic   * WEIGHTS_V2["vector_semantic"]
            + tag_weight        * WEIGHTS_V2["tag_weight"]
            + industry_complement * WEIGHTS_V2["industry_complement"]
            + attention_score   * WEIGHTS_V2["attention_score"]
        )

        return {
            "score": round(final_score, 4),
            "tag_overlap": round(tag_overlap, 4),
            "tag_overlap_raw": round(overlap_raw, 4),
            "vector_semantic": round(vector_semantic, 4),
            "tag_weight": round(tag_weight, 4),
            "industry_complement": round(industry_complement, 4),
            "attention_score": round(attention_score, 4),
            "common_tags": common_tags,
        }

    # ── V2 混合搜索（含 MMR 多样性后处理） ────────────────────────────

    @staticmethod
    async def hybrid_search_v2(
        db: AsyncSession,
        query_text: str,
        current_user_id: int,
        top_k: int = 10,
        keyword_weight: float = 0.3,
        vector_weight: float = 0.7,
        mmr_lambda: float = 0.5,
        mmr_enabled: bool = True,
    ) -> list[dict[str, Any]]:
        """V2 混合搜索：关键词匹配 + 向量语义匹配 + MMR多样性后处理

        在 V1 hybrid_search 基础上新增:
            - 返回结果中加入 v2_score 字段（五层评分）
            - MMR 多样性重排序（可选）

        Args:
            db: 数据库会话
            query_text: 搜索关键词
            current_user_id: 当前用户ID
            top_k: 返回前 top_k 个结果
            keyword_weight: 关键词权重
            vector_weight: 向量匹配权重
            mmr_lambda: MMR 多样性参数 [0, 1]，1=完全相关性，0=完全多样性
            mmr_enabled: 是否启用 MMR 多样性后处理

        Returns:
            搜索结果列表，按 score 降序排列（MMR 启用时按 mmr_score 排序）
        """
        if not query_text.strip():
            return []

        query_terms = query_text.lower().split()

        # ── 1. 关键词搜索 ─────────────────────────────────────────────
        result = await db.execute(select(User).where(User.id != current_user_id))
        other_users = result.scalars().all()
        keyword_results: list[dict] = []

        for user in other_users:
            searchable = ""
            if user.name:
                searchable += user.name.lower() + " "
            if user.intro:
                searchable += user.intro.lower() + " "
            if user.company:
                searchable += user.company.lower() + " "
            if user.title:
                searchable += user.title.lower() + " "

            result = await db.execute(
                select(UserTag).where(UserTag.user_id == user.id),
            )
            tags = result.scalars().all()
            tag_texts = " ".join([f"{t.tag_type}:{t.tag}" for t in tags]).lower()
            searchable += tag_texts

            keyword_score = 0.0
            if query_text.lower() in searchable:
                keyword_score = 0.5

            for term in query_terms:
                count = searchable.count(term)
                if count > 0:
                    keyword_score += 0.05 * count

            result = await db.execute(
                select(Brochure).where(
                    Brochure.user_id == user.id,
                    Brochure.status == "published",
                )
            )
            brochures = result.scalars().all()
            for b in brochures:
                if b.title and query_text.lower() in b.title.lower():
                    keyword_score += 0.3

            keyword_score = min(1.0, keyword_score)

            if keyword_score > 0:
                keyword_results.append({
                    "user_id": user.id,
                    "user_name": user.name,
                    "user_company": user.company,
                    "user_title": user.title,
                    "user_avatar": user.avatar or "",
                    "keyword_score": round(keyword_score, 4),
                })

        # ── 2. 向量搜索 ───────────────────────────────────────────────
        vse = VectorSearchEngine(db)
        await vse.build_index()
        vector_results = await vse.search(
            query=query_text,
            top_k=50,
            min_score=0.0,
            exclude_user_id=current_user_id,
        )

        vector_score_map: dict[int, float] = {}
        for vr in vector_results:
            vector_score_map[vr["user_id"]] = vr["score"]

        # ── 3. 混合排序 ───────────────────────────────────────────────
        seen_user_ids: set[int] = set()
        merged: list[dict] = []

        for kr in keyword_results:
            uid = kr["user_id"]
            vs = vector_score_map.get(uid, 0.0)
            final_score = keyword_weight * kr["keyword_score"] + vector_weight * vs
            merged.append({
                "user_id": uid,
                "user_name": kr["user_name"],
                "user_company": kr["user_company"],
                "user_title": kr["user_title"],
                "user_avatar": kr["user_avatar"],
                "score": round(final_score, 4),
                "keyword_score": kr["keyword_score"],
                "vector_score": round(vs, 4),
                "source": "hybrid",
            })
            seen_user_ids.add(uid)

        for vr in vector_results:
            uid = vr["user_id"]
            if uid not in seen_user_ids:
                final_score = vector_weight * vr["score"]
                merged.append({
                    "user_id": uid,
                    "user_name": vr["user_name"],
                    "user_company": vr["user_company"],
                    "user_title": vr["user_title"],
                    "user_avatar": vr["user_avatar"],
                    "score": round(final_score, 4),
                    "keyword_score": 0.0,
                    "vector_score": vr["score"],
                    "source": "vector_only",
                })

        merged.sort(key=lambda x: x["score"], reverse=True)

        # ── 4. V2 评分补充 ───────────────────────────────────────────
        # 对 top 候选计算五层综合评分
        top_candidates = merged[:top_k]
        for item in top_candidates:
            try:
                v2_result = await MatchEngineV2.compute_similarity_v2(
                    db, current_user_id, item["user_id"],
                )
                item["v2_score"] = v2_result["score"]
                item["tag_overlap"] = v2_result["tag_overlap"]
                item["vector_semantic"] = v2_result["vector_semantic"]
                item["tag_weight"] = v2_result["tag_weight"]
                item["industry_complement"] = v2_result["industry_complement"]
                item["attention_score"] = v2_result["attention_score"]
                item["common_tags"] = v2_result["common_tags"]
            except Exception:
                item["v2_score"] = item["score"]
                item["industry_complement"] = 0.0
                item["attention_score"] = 0.0

        # ── 5. MMR 多样性后处理 ──────────────────────────────────────
        if mmr_enabled and top_candidates:
            from app.ai.vector_search import embed_text

            try:
                query_embedding = await embed_text(query_text)
                mmr_engine = MMRDiversityEngine(lambda_param=mmr_lambda)

                # 为每个候选构建 embedding（使用已有的 vector_score 作为降维特征）
                mmr_candidates: list[dict] = []
                for item in top_candidates:
                    # 使用 vector_score 作为 relevance_score
                    mmr_candidates.append({
                        "user_id": item["user_id"],
                        "user_name": item["user_name"],
                        "user_company": item["user_company"],
                        "user_title": item["user_title"],
                        "user_avatar": item["user_avatar"],
                        "score": item["score"],
                        "v2_score": item.get("v2_score", item["score"]),
                        "keyword_score": item["keyword_score"],
                        "vector_score": item["vector_score"],
                        "source": item["source"],
                        "tag_overlap": item.get("tag_overlap", 0.0),
                        "vector_semantic": item.get("vector_semantic", 0.0),
                        "tag_weight": item.get("tag_weight", 0.0),
                        "industry_complement": item.get("industry_complement", 0.0),
                        "attention_score": item.get("attention_score", 0.0),
                        "common_tags": item.get("common_tags", []),
                        "embedding": query_embedding
                        if item["vector_score"] > 0
                        else [0.0],
                        "relevance_score": item["score"],
                    })

                reranked = await mmr_engine.rerank(
                    candidates=mmr_candidates,
                    query_embedding=query_embedding,
                    lambda_param=mmr_lambda,
                    top_n=top_k,
                )

                # 清理 embedding 字段
                for item in reranked:
                    item.pop("embedding", None)
                    item.pop("relevance_score", None)
                    item.pop("mmr_score", None)

                return reranked[:top_k]
            except Exception:
                # MMR 失败时降级到普通排序
                pass

        return top_candidates[:top_k]

    # ── V2 每日推荐 ──────────────────────────────────────────────────

    @staticmethod
    async def get_daily_recommendations_v2(
        db: AsyncSession,
        user_id: int,
        limit: int = 10,
        min_score: float = 0.1,
    ) -> list[dict[str, Any]]:
        """V2 每日推荐（使用五层评分）

        相比 V1:
            - 使用 compute_similarity_v2 替代 compute_similarity
            - 返回结果包含 industry_complement 和 attention_score

        Args:
            db: 数据库会话
            user_id: 当前用户ID
            limit: 返回结果数量上限
            min_score: 最低匹配分数阈值

        Returns:
            推荐用户列表（按 score 降序排列）
        """
        result = await db.execute(select(User).where(User.id == user_id))
        current_user = result.scalars().first()
        if current_user is None:
            raise ValueError("用户不存在")

        result = await db.execute(select(User).where(User.id != user_id))
        other_users = result.scalars().all()
        results: list[dict] = []

        for other in other_users:
            match_result = await MatchEngineV2.compute_similarity_v2(
                db, user_id, other.id,
            )
            if match_result["score"] < min_score:
                continue

            results.append({
                "user_id": other.id,
                "user_name": other.name,
                "user_company": other.company,
                "user_title": other.title,
                "user_avatar": other.avatar,
                "score": match_result["score"],
                "tag_overlap": match_result["tag_overlap"],
                "vector_semantic": match_result["vector_semantic"],
                "tag_weight": match_result["tag_weight"],
                "industry_complement": match_result["industry_complement"],
                "attention_score": match_result["attention_score"],
                "common_tags": match_result["common_tags"],
            })

        results.sort(key=lambda x: x["score"], reverse=True)

        # 记录 MatchRecord（避免重复）
        for match in results[:20]:
            result = await db.execute(
                select(MatchRecord).where(
                    or_(
                        (MatchRecord.user_a_id == user_id)
                        & (MatchRecord.user_b_id == match["user_id"]),
                        (MatchRecord.user_a_id == match["user_id"])
                        & (MatchRecord.user_b_id == user_id),
                    )
                )
            )
            existing = result.scalars().first()
            if not existing:
                record = MatchRecord(
                    user_a_id=user_id,
                    user_b_id=match["user_id"],
                    match_score=match["score"],
                    status="matched",
                    common_tags=json.dumps(
                        [ct["tag"] for ct in match.get("common_tags", [])],
                        ensure_ascii=False,
                    ),
                    source="auto_v2",
                )
                db.add(record)

        await db.commit()
        return results[:limit]

    # ── V2 兴趣记录（复用 V1） ──────────────────────────────────────

    @staticmethod
    async def record_interest_v2(
        db: AsyncSession,
        user_id: int,
        target_user_id: int,
    ) -> MatchRecord:
        """记录兴趣（委托给 V1 MatchEngine.record_interest）"""
        return await MatchEngine.record_interest(db, user_id, target_user_id)
