"""
社交匹配增强服务 — 将BFS社交路径整合进现有匹配推荐引擎

功能:
  1. match_with_social_path(): 属性匹配 + BFS社交路径增强排序
  2. get_social_based_recommendations(): 基于社交图谱的人脉推荐（二度/三度人脉）

依赖:
  - social_connect_service.find_path() BFS算法
  - social_connect_service.get_connection_recommendations() 二度人脉
  - visibility_service 四级可见性过滤
"""
import asyncio
import logging
from typing import Optional

from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.social_connection import SocialConnection
from app.models.tag import UserTag
from app.models.user import User
from app.services.social_connect_service import SocialConnectService
from app.services.visibility_service import VisibilityService

logger = logging.getLogger(__name__)


class SocialMatchService:
    """社交匹配增强服务"""

    @staticmethod
    async def match_with_social_path(
        db: AsyncSession,
        viewer_id: int,
        keyword: str = "",
        industry: str = "",
        city: str = "",
        limit: int = 20,
        include_path: bool = True,
    ) -> list[dict]:
        """
        属性匹配 + BFS社交路径增强

        流程:
          1. 先用关键词/行业/城市匹配用户（基于 name / company / title / intro）
          2. 对每个匹配结果，检查当前用户到目标用户的社交距离（BFS）
          3. 排序: 有社交路径的排在无社交路径的前面（同距离按匹配度降序）
          4. 返回: 匹配结果 + 距离 + 路径摘要

        Args:
            db: 异步数据库会话
            viewer_id: 当前用户ID
            keyword: 搜索关键词（模糊匹配 name / company / title）
            industry: 行业标签过滤（匹配 UserTag.tag）
            city: 城市过滤（匹配 User.city — 若 User 无 city 字段则跳过）
            limit: 最大返回数量
            include_path: 是否包含社交路径信息

        Returns:
            list[dict]: [
                {
                    "user_id": int,
                    "name": str,
                    "company": str,
                    "title": str,
                    "avatar": str,
                    "intro": str,
                    "match_type": str,        # keyword/industry/city 或组合
                    "social_distance": int,    # -1=无路径, 0=自己, 1=好友, 2=二度, 3=三度
                    "social_path": list[int],  # 如果include_path=True且有路径
                    "path_summary": str,       # 人类可读的路径摘要
                },
                ...
            ]
        """
        # ── 1. 构建查询条件 ──────────────────────────────────────────────────
        conditions = [User.id != viewer_id]
        match_type_parts = []

        if keyword:
            keyword_filter = or_(
                User.name.ilike(f"%{keyword}%"),
                User.company.ilike(f"%{keyword}%"),
                User.title.ilike(f"%{keyword}%"),
            )
            conditions.append(keyword_filter)
            match_type_parts.append("keyword")

        if industry:
            # 通过 UserTag 表过滤拥有该行业标签的用户
            conditions.append(
                User.id.in_(
                    select(UserTag.user_id).where(
                        UserTag.tag == industry,
                    )
                )
            )
            match_type_parts.append("industry")

        if city:
            # 如果 User 表有 city 字段，这里可以使用；目前 User 无 city 字段，
            # 保留接口为后续扩展。可以基于 company 所在城市做近似匹配。
            # 暂时跳过 city 过滤（User 模型无 city 字段）
            logger.debug("city filter requested but User model has no city field; skipping")

        # 若无任何过滤条件，默认返回匹配引擎结果（所有其他用户）
        query = select(User).where(*conditions) if conditions else select(User).where(User.id != viewer_id)
        query = query.limit(limit * 3)  # 放宽限制，后续排序后截断

        result = await db.execute(query)
        matched_users = result.scalars().all()

        if not matched_users:
            return []

        match_type_str = "+".join(match_type_parts) if match_type_parts else "all"

        # ── 2. 对每个匹配结果获取BFS社交路径 ────────────────────────────────
        enriched = []
        # 为加速，批量检查直接好友关系
        direct_friend_ids = await SocialMatchService._get_direct_friend_ids(db, viewer_id)

        for user in matched_users:
            distance = -1
            path = []
            path_summary = "无社交连接路径"

            if user.id == viewer_id:
                distance = 0
                path = [viewer_id]
                path_summary = "自己"
            elif user.id in direct_friend_ids:
                distance = 1
                path = [viewer_id, user.id]
                path_summary = f"直接好友: {user.name}"
            else:
                # BFS搜索最短路径
                path_result = await SocialConnectService.find_path(
                    db=db, user_id=viewer_id, target_user_id=user.id
                )
                distance = path_result.get("distance", -1)
                path = path_result.get("path", [])
                path_summary = path_result.get("message", "无社交连接路径")

            entry = {
                "user_id": user.id,
                "name": user.name,
                "company": user.company or "",
                "title": user.title or "",
                "avatar": user.avatar or "",
                "intro": user.intro or "",
                "match_type": match_type_str,
                "social_distance": distance,
            }

            if include_path and path:
                entry["social_path"] = path
                entry["path_summary"] = path_summary

            enriched.append(entry)

        # ── 3. 排序: 有社交路径 (distance > 0) 排在无路径 (distance == -1) 前面
        #    同距离按用户ID降序（近似按新用户优先）
        enriched.sort(key=lambda x: (
            0 if x["social_distance"] > 0 else 1,  # 有路径优先
            x["social_distance"] if x["social_distance"] > 0 else 999,  # 短距离优先
            -x["user_id"],  # 新用户优先（近似）
        ))

        return enriched[:limit]

    @staticmethod
    async def get_social_based_recommendations(
        db: AsyncSession,
        viewer_id: int,
        limit: int = 10,
        min_strength: float = 0.0,
    ) -> list[dict]:
        """
        基于社交图谱的推荐（二度/三度人脉）

        流程:
          1. 获取当前用户的好友（直接好友）
          2. 取好友的好友（二度人脉），排除自己和已连接
          3. 取二度人脉的好友（三度人脉），排除自己和已连接
          4. 按关系强度排序（如果有strength字段）
          5. 返回推荐人列表

        Args:
            db: 异步数据库会话
            viewer_id: 当前用户ID
            limit: 最大返回数量
            min_strength: 最小关系强度阈值（0.0 ~ 1.0）

        Returns:
            list[dict]: [
                {
                    "user_id": int,
                    "name": str,
                    "company": str,
                    "title": str,
                    "avatar": str,
                    "intro": str,
                    "degree": int,          # 1=直接好友, 2=二度人脉, 3=三度人脉
                    "strength": float,      # 关系强度 (0.0~1.0)
                    "via_users": list[int], # 中间人用户ID列表
                    "common_tags": list[str], # 共同标签
                },
                ...
            ]
        """
        # ── 1. 获取直接好友 ──────────────────────────────────────────────────
        direct_friend_ids = await SocialMatchService._get_direct_friend_ids(db, viewer_id)
        all_connected_ids = set(direct_friend_ids)
        all_connected_ids.add(viewer_id)

        # 获取直接好友的详细信息
        direct_recommendations = await SocialMatchService._build_recommendation_entries(
            db=db,
            user_ids=direct_friend_ids,
            viewer_id=viewer_id,
            degree=1,
            via_users=None,
        )

        # ── 2. 获取二度人脉（好友的好友） ────────────────────────────────────
        second_degree_ids = set()
        second_degree_via = {}  # user_id -> list of intermediary friend IDs
        for fid in direct_friend_ids:
            friend_friends = await SocialMatchService._get_direct_friend_ids(db, fid)
            for candidate_id in friend_friends:
                if candidate_id not in all_connected_ids:
                    second_degree_ids.add(candidate_id)
                    second_degree_via.setdefault(candidate_id, []).append(fid)

        all_connected_ids.update(second_degree_ids)

        second_recommendations = await SocialMatchService._build_recommendation_entries(
            db=db,
            user_ids=list(second_degree_ids),
            viewer_id=viewer_id,
            degree=2,
            via_users=second_degree_via,
        )

        # ── 3. 取三度人脉 ──────────────────────────────────────────────────
        third_degree_ids = set()
        third_degree_via = {}
        for sid in second_degree_ids:
            friend_friends = await SocialMatchService._get_direct_friend_ids(db, sid)
            for candidate_id in friend_friends:
                if candidate_id not in all_connected_ids:
                    third_degree_ids.add(candidate_id)
                    third_degree_via.setdefault(candidate_id, []).append(sid)

        third_recommendations = await SocialMatchService._build_recommendation_entries(
            db=db,
            user_ids=list(third_degree_ids),
            viewer_id=viewer_id,
            degree=3,
            via_users=third_degree_via,
        )

        # ── 4. 合并、排序、过滤 ──────────────────────────────────────────────
        all_recs = direct_recommendations + second_recommendations + third_recommendations

        # 过滤最小关系强度
        if min_strength > 0.0:
            all_recs = [r for r in all_recs if r.get("strength", 0.0) >= min_strength]

        # 排序: 度数近优先 > 关系强度高优先 > 用户ID新优先
        all_recs.sort(key=lambda x: (
            x.get("degree", 999),
            -x.get("strength", 0.0),
            -x.get("user_id", 0),
        ))

        return all_recs[:limit]

    # =====================================================================
    # 内部辅助方法
    # =====================================================================

    @staticmethod
    async def _get_direct_friend_ids(db: AsyncSession, user_id: int) -> set[int]:
        """获取指定用户的直接好友ID集合"""
        result = await db.execute(
            select(SocialConnection.contact_id).where(
                SocialConnection.user_id == user_id,
                SocialConnection.status == "approved",
            )
        )
        return set(result.scalars().all())

    @staticmethod
    async def _build_recommendation_entries(
        db: AsyncSession,
        user_ids: list[int],
        viewer_id: int,
        degree: int,
        via_users: Optional[dict[int, list[int]]],
    ) -> list[dict]:
        """构建推荐条目列表"""
        if not user_ids:
            return []

        result = await db.execute(
            select(User).where(User.id.in_(user_ids))
        )
        users = {u.id: u for u in result.scalars().all()}

        # 批量获取共同标签（I provide & they need, or vice versa）
        # 先获取 viewer 的标签
        viewer_tags_result = await db.execute(
            select(UserTag).where(UserTag.user_id == viewer_id)
        )
        viewer_tags = viewer_tags_result.scalars().all()
        viewer_provide = {t.tag for t in viewer_tags if t.tag_type == "provide"}
        viewer_need = {t.tag for t in viewer_tags if t.tag_type == "need"}

        entries = []
        for uid in user_ids:
            user = users.get(uid)
            if not user:
                continue

            # 计算关系强度（默认基于degree）
            if degree == 1:
                strength = 0.8  # 直接好友的默认强度
            elif degree == 2:
                strength = 0.5
            else:
                strength = 0.3

            # 共同标签: 我提供且对方需要 | 我需要且对方提供
            common_tags = []
            other_tags_result = await db.execute(
                select(UserTag).where(UserTag.user_id == uid)
            )
            other_tags = other_tags_result.scalars().all()
            other_provide = {t.tag for t in other_tags if t.tag_type == "provide"}
            other_need = {t.tag for t in other_tags if t.tag_type == "need"}

            for tag in viewer_provide & other_need:
                common_tags.append(f"我提供→对方需要:{tag}")
            for tag in viewer_need & other_provide:
                common_tags.append(f"我需要→对方提供:{tag}")

            entry = {
                "user_id": uid,
                "name": user.name,
                "company": user.company or "",
                "title": user.title or "",
                "avatar": user.avatar or "",
                "intro": user.intro or "",
                "degree": degree,
                "strength": round(strength, 2),
                "via_users": list(set(via_users.get(uid, []))) if via_users else [],
                "common_tags": common_tags,
            }
            entries.append(entry)

        return entries
