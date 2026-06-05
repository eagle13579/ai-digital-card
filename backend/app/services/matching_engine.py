import json
import math
from typing import Optional

from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.ai.vector_search import (
    VectorSearchEngine,
    DocumentBuilder,
    cosine_similarity as vector_cosine_similarity,
)
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
    def _build_tag_vector(
        db: Session,
        user_id: int,
        tag_type: str,
    ) -> dict[str, float]:
        """构建用户标签向量 {tag: weight}"""
        tags = db.query(UserTag).filter(
            UserTag.user_id == user_id,
            UserTag.tag_type == tag_type,
        ).all()
        return {t.tag: t.weight for t in tags}

    @staticmethod
    def _cosine_similarity(
        vec_a: dict[str, float],
        vec_b: dict[str, float],
    ) -> float:
        """计算两个标签向量的余弦相似度

        Args:
            vec_a: 用户A的标签向量
            vec_b: 用户B的标签向量

        Returns:
            余弦相似度 [-1, 1] 归一化到 [0, 1]
        """
        # 获取所有标签的并集
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
        # 归一化到 [0, 1]
        return max(0.0, (cos_sim + 1.0) / 2.0)

    @staticmethod
    def _tag_overlap_score(
        provide_a: dict[str, float],
        need_b: dict[str, float],
        provide_b: dict[str, float],
        need_a: dict[str, float],
    ) -> tuple[float, list[dict]]:
        """计算标签重叠分数（双向匹配）

        Score = A提供∩B需要 + B提供∩A需要

        Returns:
            (score, common_tags_list)
        """
        score = 0.0
        common_tags = []

        # A provide ∩ B need
        for tag, weight_a in provide_a.items():
            if tag in need_b:
                match_weight = weight_a * need_b[tag]
                score += match_weight
                common_tags.append({"tag": tag, "direction": "我提供→对方需要", "weight": round(match_weight, 3)})

        # B provide ∩ A need
        for tag, weight_b in provide_b.items():
            if tag in need_a:
                match_weight = weight_b * need_a[tag]
                score += match_weight
                common_tags.append({"tag": tag, "direction": "我需要→对方提供", "weight": round(match_weight, 3)})

        return score, common_tags

    @staticmethod
    def _build_user_document(
        db: Session,
        user_id: int,
    ) -> list[str]:
        """构建用户的文本文档（用于语义相似度计算）

        拼接标签（带类型前缀）、简介、brochure 内容。

        Returns:
            文本片段列表
        """
        parts = []
        user = db.query(User).filter(User.id == user_id).first()
        if user and user.intro:
            parts.append(user.intro)

        tags = db.query(UserTag).filter(UserTag.user_id == user_id).all()
        for t in tags:
            type_label = "提供" if t.tag_type == "provide" else "需要"
            parts.append(f"{type_label}{t.tag}")

        brochures = db.query(Brochure).filter(
            Brochure.user_id == user_id,
            Brochure.status == "published",
        ).all()
        for brochure in brochures:
            if brochure.title:
                parts.append(brochure.title)
            pages = db.query(Page).filter(Page.brochure_id == brochure.id).all()
            for page in pages:
                if page.ai_summary:
                    parts.append(page.ai_summary)

        return parts

    @staticmethod
    def _compute_vector_semantic(
        db: Session,
        user_a_id: int,
        user_b_id: int,
    ) -> float:
        """计算两个用户标签+简介的向量语义相似度（使用 M3E/多后端 embedding）

        使用向量搜索引擎的语义匹配替代旧版 TF-IDF。

        Returns:
            语义相似度 [0, 1]
        """
        parts_a = MatchEngine._build_user_document(db, user_a_id)
        parts_b = MatchEngine._build_user_document(db, user_b_id)

        doc_a = " ".join(parts_a)
        doc_b = " ".join(parts_b)

        if not doc_a.strip() or not doc_b.strip():
            return 0.0

        # 使用 VectorSearchEngine 的语义相似度计算（M3E/numpy/API 多后端）
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
        """计算标签权重综合分

        基于双方标签数量和权重的归一化评分，鼓励有更多高质量标签的用户。

        Returns:
            权重分数 [0, 1]
        """
        total_tags_a = len(provide_a) + len(need_a)
        total_tags_b = len(provide_b) + len(need_b)

        if total_tags_a == 0 or total_tags_b == 0:
            return 0.0

        avg_weight_a = (sum(provide_a.values()) + sum(need_a.values())) / total_tags_a
        avg_weight_b = (sum(provide_b.values()) + sum(need_b.values())) / total_tags_b

        # 综合评分：标签数量归一化 + 平均权重归一化
        max_tags = max(total_tags_a, total_tags_b)
        tag_count_score = min(total_tags_a, total_tags_b) / max_tags if max_tags > 0 else 0.0

        avg_weight = (avg_weight_a + avg_weight_b) / 4.0  # normalize to [0, 1] (max weight ~ 4)
        weight_norm = min(1.0, avg_weight)

        return round(tag_count_score * 0.5 + weight_norm * 0.5, 4)

    @staticmethod
    def compute_similarity(
        db: Session,
        user_a_id: int,
        user_b_id: int,
    ) -> dict:
        """计算两个用户之间的综合匹配度（三层评分）

        Args:
            db: 数据库会话
            user_a_id: 用户A的ID
            user_b_id: 用户B的ID

        Returns:
            {
                "score": float,               # 综合匹配度 [0, 1]
                "tag_overlap": float,           # 标签重叠
                "tag_overlap_raw": float,       # 原始重叠分数
                "vector_semantic": float,       # 向量语义相似度
                "tag_weight": float,            # 标签权重综合分
                "common_tags": list[dict]
            }
        """
        provide_a = MatchEngine._build_tag_vector(db, user_a_id, "provide")
        need_a = MatchEngine._build_tag_vector(db, user_a_id, "need")
        provide_b = MatchEngine._build_tag_vector(db, user_b_id, "provide")
        need_b = MatchEngine._build_tag_vector(db, user_b_id, "need")

        # 1. 标签重叠分数（40%）
        overlap_raw, common_tags = MatchEngine._tag_overlap_score(
            provide_a, need_b, provide_b, need_a
        )
        max_possible_overlap = len(common_tags) * 1.0 if common_tags else 1.0
        tag_overlap = min(1.0, overlap_raw / max_possible_overlap) if max_possible_overlap > 0 else 0.0

        # 2. 向量语义相似度（40%）- 基于 TF-IDF + Cosine
        vector_semantic = MatchEngine._compute_vector_semantic(db, user_a_id, user_b_id)

        # 3. 标签权重综合分（20%）
        tag_weight = MatchEngine._compute_tag_weight_score(
            provide_a, need_a, provide_b, need_b
        )

        # 三层综合评分
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
    def hybrid_search(
        db: Session,
        query_text: str,
        current_user_id: int,
        top_k: int = 10,
        keyword_weight: float = 0.3,
        vector_weight: float = 0.7,
    ) -> list[dict]:
        """混合搜索：关键词匹配 + 向量语义匹配

        使用双重策略：
        1. 关键词搜索: 对标题、标签、简介做子串/分词匹配
        2. 向量搜索:   基于 TF-IDF + Cosine Similarity 的语义匹配
        3. 混合排序:   加权融合

        Args:
            db: 数据库会话
            query_text: 搜索文本
            current_user_id: 当前用户ID（排除自身）
            top_k: 返回结果数量上限
            keyword_weight: 关键词搜索权重
            vector_weight: 向量搜索权重

        Returns:
            混合排序的用户列表 [{user_id, user_name, ..., score, keyword_score, vector_score, ...}]
        """
        if not query_text.strip():
            return []

        query_terms = query_text.lower().split()

        # ── 1. 关键词搜索 ─────────────────────────────────────────
        other_users = db.query(User).filter(User.id != current_user_id).all()
        keyword_results: list[dict] = []

        for user in other_users:
            # 构建可搜索文本
            searchable = ""
            if user.name:
                searchable += user.name.lower() + " "
            if user.intro:
                searchable += user.intro.lower() + " "
            if user.company:
                searchable += user.company.lower() + " "
            if user.title:
                searchable += user.title.lower() + " "

            # 标签
            tags = db.query(UserTag).filter(UserTag.user_id == user.id).all()
            tag_texts = " ".join([f"{t.tag_type}:{t.tag}" for t in tags]).lower()
            searchable += tag_texts

            # 计算关键词匹配分数
            keyword_score = 0.0
            if query_text.lower() in searchable:
                keyword_score = 0.5  # 子串匹配

            for term in query_terms:
                count = searchable.count(term)
                if count > 0:
                    keyword_score += 0.05 * count

            # brochure 标题匹配（加分）
            brochures = db.query(Brochure).filter(
                Brochure.user_id == user.id,
                Brochure.status == "published",
            ).all()
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
        vse.build_index()
        vector_results = vse.search(
            query=query_text,
            top_k=50,  # 获取更多候选项用于混合
            min_score=0.0,
            exclude_user_id=current_user_id,
        )

        # 构建向量分数映射
        vector_score_map: dict[int, float] = {}
        for vr in vector_results:
            vector_score_map[vr["user_id"]] = vr["score"]

        # ── 3. 混合排序 ───────────────────────────────────────────
        # 合并关键词和向量结果
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

        # 补充只有向量命中但关键词未命中的结果
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

        # 按混合分数降序排列
        merged.sort(key=lambda x: x["score"], reverse=True)

        return merged[:top_k]

    @staticmethod
    def get_daily_recommendations(
        db: Session,
        user_id: int,
        limit: int = 10,
        min_score: float = 0.1,
    ) -> list[dict]:
        """获取每日推荐用户（所有其他用户按匹配度排序）

        同时保存匹配记录到数据库。

        Args:
            db: 数据库会话
            user_id: 当前用户ID
            limit: 返回数量上限
            min_score: 最低匹配分数阈值

        Returns:
            匹配用户列表 [{user_id, user_name, score, common_tags, ...}]
        """
        current_user = db.query(User).filter(User.id == user_id).first()
        if current_user is None:
            raise ValueError("用户不存在")

        other_users = db.query(User).filter(User.id != user_id).all()
        results = []

        for other in other_users:
            match_result = MatchEngine.compute_similarity(db, user_id, other.id)
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

        # 按分数降序排序
        results.sort(key=lambda x: x["score"], reverse=True)

        # 保存 top 匹配记录
        for match in results[:20]:
            existing = db.query(MatchRecord).filter(
                or_(
                    (MatchRecord.user_a_id == user_id) & (MatchRecord.user_b_id == match["user_id"]),
                    (MatchRecord.user_a_id == match["user_id"]) & (MatchRecord.user_b_id == user_id),
                )
            ).first()
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

        db.commit()
        return results[:limit]

    @staticmethod
    def record_interest(
        db: Session,
        user_id: int,
        target_user_id: int,
    ) -> MatchRecord:
        """记录兴趣（用户A对用户B感兴趣）

        Args:
            db: 数据库会话
            user_id: 当前用户ID
            target_user_id: 目标用户ID

        Returns:
            创建或更新的 MatchRecord
        """
        if user_id == target_user_id:
            raise ValueError("不能对自己感兴趣")

        # 查找已有的匹配记录
        record = db.query(MatchRecord).filter(
            or_(
                (MatchRecord.user_a_id == user_id) & (MatchRecord.user_b_id == target_user_id),
                (MatchRecord.user_a_id == target_user_id) & (MatchRecord.user_b_id == user_id),
            )
        ).first()

        if record:
            record.status = "matched"
        else:
            # 计算匹配度
            match_result = MatchEngine.compute_similarity(db, user_id, target_user_id)
            record = MatchRecord(
                user_a_id=user_id,
                user_b_id=target_user_id,
                match_score=match_result["score"],
                status="matched",
                common_tags=json.dumps(
                    [ct["tag"] for ct in match_result.get("common_tags", [])],
                    ensure_ascii=False,
                ),
                source="manual",
            )
            db.add(record)

        db.commit()
        db.refresh(record)
        return record

    @staticmethod
    def confirm_match(
        db: Session,
        record_id: int,
        user_id: int,
    ) -> MatchRecord:
        """确认匹配（双方确认才算 match confirmed）

        Args:
            db: 数据库会话
            record_id: 匹配记录ID
            user_id: 当前用户ID

        Returns:
            更新后的 MatchRecord
        """
        record = db.query(MatchRecord).filter(MatchRecord.id == record_id).first()
        if record is None:
            raise ValueError("匹配记录不存在")
        if record.user_a_id != user_id and record.user_b_id != user_id:
            raise PermissionError("无权操作此匹配记录")

        record.status = "confirmed"
        db.commit()
        db.refresh(record)
        return record
