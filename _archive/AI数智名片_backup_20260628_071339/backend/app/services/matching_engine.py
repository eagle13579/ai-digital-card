import json
import math
from typing import Optional

from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.vector_search import (
    VectorSearchEngine,
    DocumentBuilder,
    cosine_similarity as vector_cosine_similarity,
)
from app.cache import cache, invalidate
from app.models.tag import MatchRecord, UserTag
from app.models.user import User
from app.models.brochure import Brochure, Page


class MatchEngine:
    """匹配引擎 - 三层综合评分（标签重叠 + 语义相似 + 标签权重）

    评分公式：
        score = tag_overlap * 0.40 + vector_semantic * 0.40 + tag_weight * 0.20

    其中：
        tag_overlap    : 标签供需匹配重叠分数（归一化到 [0,1]）
        vector_semantic: TF-IDF 向量语义相似度（基于标签+简介+brochure内容，零依赖纯Python实现）
        tag_weight     : 标签权重综合（双方标签个数+权重的归一化评分）
    """

    @staticmethod
    @cache(ttl=600, prefix="tag_vector")
    async def _build_tag_vector(
        db: AsyncSession,
        user_id: int,
        tag_type: str,
    ) -> dict[str, float]:
        """构建用户标签向量 {tag: weight}"""
        result = await db.execute(
            select(UserTag).where(
                UserTag.user_id == user_id,
                UserTag.tag_type == tag_type,
            )
        )
        tags = result.scalars().all()
        return {t.tag: t.weight for t in tags}

    @staticmethod
    def _cosine_similarity(
        vec_a: dict[str, float],
        vec_b: dict[str, float],
    ) -> float:
        """计算两个标签向量的余弦相似度"""
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
        return max(0.0, (cos_sim + 1.0) / 2.0)

    @staticmethod
    def _tag_overlap_score(
        provide_a: dict[str, float],
        need_b: dict[str, float],
        provide_b: dict[str, float],
        need_a: dict[str, float],
    ) -> tuple[float, list[dict]]:
        """计算标签重叠分数（双向匹配）"""
        score = 0.0
        common_tags = []

        for tag, weight_a in provide_a.items():
            if tag in need_b:
                match_weight = weight_a * need_b[tag]
                score += match_weight
                common_tags.append({"tag": tag, "direction": "我提供→对方需要", "weight": round(match_weight, 3)})

        for tag, weight_b in provide_b.items():
            if tag in need_a:
                match_weight = weight_b * need_a[tag]
                score += match_weight
                common_tags.append({"tag": tag, "direction": "我需要→对方提供", "weight": round(match_weight, 3)})

        return score, common_tags

    @staticmethod
    async def _build_user_document(
        db: AsyncSession,
        user_id: int,
    ) -> list[str]:
        """构建用户的文本文档（用于语义相似度计算）"""
        parts = []
        result = await db.execute(select(User).where(User.id == user_id))
        user = result.scalars().first()
        if user and user.intro:
            parts.append(user.intro)

        result = await db.execute(select(UserTag).where(UserTag.user_id == user_id))
        tags = result.scalars().all()
        for t in tags:
            type_label = "提供" if t.tag_type == "provide" else "需要"
            parts.append(f"{type_label}{t.tag}")

        result = await db.execute(
            select(Brochure).where(
                Brochure.user_id == user_id,
                Brochure.status == "published",
            )
        )
        brochures = result.scalars().all()
        for brochure in brochures:
            if brochure.title:
                parts.append(brochure.title)
            result = await db.execute(select(Page).where(Page.brochure_id == brochure.id))
            pages = result.scalars().all()
            for page in pages:
                if page.ai_summary:
                    parts.append(page.ai_summary)

        return parts

    @staticmethod
    async def _compute_vector_semantic(
        db: AsyncSession,
        user_a_id: int,
        user_b_id: int,
    ) -> float:
        """计算两个用户标签+简介的向量语义相似度"""
        parts_a = await MatchEngine._build_user_document(db, user_a_id)
        parts_b = await MatchEngine._build_user_document(db, user_b_id)

        doc_a = " ".join(parts_a)
        doc_b = " ".join(parts_b)

        if not doc_a.strip() or not doc_b.strip():
            return 0.0

        try:
            sim = VectorSearchEngine.compute_semantic_similarity(
                tags_a=parts_a,
                tags_b=parts_b,
            )
            return max(0.0, float(sim))
        except Exception:
            return 0.0

    @staticmethod
    def _compute_tag_weight_score(
        provide_a: dict[str, float],
        need_a: dict[str, float],
        provide_b: dict[str, float],
        need_b: dict[str, float],
    ) -> float:
        """计算标签权重综合分"""
        total_tags_a = len(provide_a) + len(need_a)
        total_tags_b = len(provide_b) + len(need_b)

        if total_tags_a == 0 or total_tags_b == 0:
            return 0.0

        avg_weight_a = (sum(provide_a.values()) + sum(need_a.values())) / total_tags_a
        avg_weight_b = (sum(provide_b.values()) + sum(need_b.values())) / total_tags_b

        max_tags = max(total_tags_a, total_tags_b)
        tag_count_score = min(total_tags_a, total_tags_b) / max_tags if max_tags > 0 else 0.0

        avg_weight = (avg_weight_a + avg_weight_b) / 4.0
        weight_norm = min(1.0, avg_weight)

        return round(tag_count_score * 0.5 + weight_norm * 0.5, 4)

    @staticmethod
    async def compute_similarity(
        db: AsyncSession,
        user_a_id: int,
        user_b_id: int,
    ) -> dict:
        """计算两个用户之间的综合匹配度（三层评分）"""
        provide_a = await MatchEngine._build_tag_vector(db, user_a_id, "provide")
        need_a = await MatchEngine._build_tag_vector(db, user_a_id, "need")
        provide_b = await MatchEngine._build_tag_vector(db, user_b_id, "provide")
        need_b = await MatchEngine._build_tag_vector(db, user_b_id, "need")

        overlap_raw, common_tags = MatchEngine._tag_overlap_score(
            provide_a, need_b, provide_b, need_a
        )
        max_possible_overlap = len(common_tags) * 1.0 if common_tags else 1.0
        tag_overlap = min(1.0, overlap_raw / max_possible_overlap) if max_possible_overlap > 0 else 0.0

        vector_semantic = await MatchEngine._compute_vector_semantic(db, user_a_id, user_b_id)

        tag_weight = MatchEngine._compute_tag_weight_score(
            provide_a, need_a, provide_b, need_b
        )

        final_score = tag_overlap * 0.40 + vector_semantic * 0.40 + tag_weight * 0.20

        return {
            "score": round(final_score, 4),
            "tag_overlap": round(tag_overlap, 4),
            "tag_overlap_raw": round(overlap_raw, 4),
            "vector_semantic": round(vector_semantic, 4),
            "tag_weight": round(tag_weight, 4),
            "common_tags": common_tags,
        }

    # ── 混合搜索（关键词 + 向量）─────────────────────────────────────────

    @staticmethod
    async def hybrid_search(
        db: AsyncSession,
        query_text: str,
        current_user_id: int,
        top_k: int = 10,
        keyword_weight: float = 0.3,
        vector_weight: float = 0.7,
    ) -> list[dict]:
        """混合搜索：关键词匹配 + 向量语义匹配"""
        if not query_text.strip():
            return []

        query_terms = query_text.lower().split()

        # ── 1. 关键词搜索 ─────────────────────────────────────────
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

            result = await db.execute(select(UserTag).where(UserTag.user_id == user.id))
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

        # ── 2. 向量搜索 ───────────────────────────────────────────
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

        # ── 3. 混合排序 ───────────────────────────────────────────
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
        return merged[:top_k]

    @staticmethod
    async def get_daily_recommendations(
        db: AsyncSession,
        user_id: int,
        limit: int = 10,
        min_score: float = 0.1,
    ) -> list[dict]:
        """获取每日推荐用户（所有其他用户按匹配度排序）"""
        result = await db.execute(select(User).where(User.id == user_id))
        current_user = result.scalars().first()
        if current_user is None:
            raise ValueError("用户不存在")

        result = await db.execute(select(User).where(User.id != user_id))
        other_users = result.scalars().all()
        results = []

        for other in other_users:
            match_result = await MatchEngine.compute_similarity(db, user_id, other.id)
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
                "common_tags": match_result["common_tags"],
            })

        results.sort(key=lambda x: x["score"], reverse=True)

        for match in results[:20]:
            result = await db.execute(
                select(MatchRecord).where(
                    or_(
                        (MatchRecord.user_a_id == user_id) & (MatchRecord.user_b_id == match["user_id"]),
                        (MatchRecord.user_a_id == match["user_id"]) & (MatchRecord.user_b_id == user_id),
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
                    source="auto",
                )
                db.add(record)

        await db.commit()
        return results[:limit]

    @staticmethod
    async def record_interest(
        db: AsyncSession,
        user_id: int,
        target_user_id: int,
    ) -> MatchRecord:
        """记录兴趣（用户A对用户B感兴趣）"""
        if user_id == target_user_id:
            raise ValueError("不能对自己感兴趣")

        result = await db.execute(
            select(MatchRecord).where(
                or_(
                    (MatchRecord.user_a_id == user_id) & (MatchRecord.user_b_id == target_user_id),
                    (MatchRecord.user_a_id == target_user_id) & (MatchRecord.user_b_id == user_id),
                )
            )
        )
        existing = result.scalars().first()
        if existing:
            existing.status = "confirmed"
            await db.commit()
            await db.refresh(existing)
            return existing

        record = MatchRecord(
            user_a_id=user_id,
            user_b_id=target_user_id,
            match_score=0.5,
            status="confirmed",
            common_tags="[]",
            source="manual",
        )
        db.add(record)
        await db.commit()
        await db.refresh(record)
        return record
