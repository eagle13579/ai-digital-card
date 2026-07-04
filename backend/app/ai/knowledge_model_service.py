"""
心智模型服务 (Knowledge Model Service)

提供心智模型的查询、管理、训练对接接口。

核心功能:
1. 从 knowledge_models 表查询心智模型
2. 同步至 gaia_knowledge 表供进化大脑使用
3. 按类别/成员分组获取模型用于训练
"""

from __future__ import annotations

import logging
from typing import Any

from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.gaia import KnowledgeModel, GaiaKnowledge

logger = logging.getLogger(__name__)


class KnowledgeModelService:
    """心智模型服务"""

    async def get_all_models(
        self, db: AsyncSession, category: str | None = None, active_only: bool = True
    ) -> list[KnowledgeModel]:
        """获取心智模型列表"""
        conditions = []
        if active_only:
            conditions.append(KnowledgeModel.is_active.is_(True))
        if category:
            conditions.append(KnowledgeModel.category == category)

        stmt = select(KnowledgeModel)
        if conditions:
            stmt = stmt.where(and_(*conditions))
        stmt = stmt.order_by(KnowledgeModel.model_id)
        result = await db.execute(stmt)
        return list(result.scalars().all())

    async def get_model_by_id(self, db: AsyncSession, model_id: str) -> KnowledgeModel | None:
        """按模型ID获取"""
        stmt = select(KnowledgeModel).where(KnowledgeModel.model_id == model_id)
        result = await db.execute(stmt)
        return result.scalars().first()

    async def get_categories(self, db: AsyncSession) -> list[dict[str, Any]]:
        """获取分类统计"""
        stmt = (
            select(
                KnowledgeModel.category,
                func.count().label("count"),
                func.avg(KnowledgeModel.confidence).label("avg_confidence"),
            )
            .where(KnowledgeModel.is_active.is_(True))
            .group_by(KnowledgeModel.category)
            .order_by(KnowledgeModel.category)
        )
        result = await db.execute(stmt)
        return [
            {
                "category": row.category,
                "count": row.count,
                "avg_confidence": round(row.avg_confidence, 2) if row.avg_confidence else 0,
            }
            for row in result.all()
        ]

    async def sync_to_gaia_knowledge(self, db: AsyncSession) -> dict[str, int]:
        """将 knowledge_models 同步到 gaia_knowledge 表
        
        让盖娅进化大脑可以消费这些心智模型进行向量化和训练。
        """
        models = await self.get_all_models(db, active_only=True)
        synced = 0
        skipped = 0

        for model in models:
            # 检查是否已同步（通过source_id判断）
            existing_stmt = select(GaiaKnowledge).where(
                and_(
                    GaiaKnowledge.source == "knowledge_model",
                    GaiaKnowledge.source_id == model.model_id,
                )
            )
            result = await db.execute(existing_stmt)
            existing = result.scalars().first()

            if existing:
                skipped += 1
                continue

            # 同步到 gaia_knowledge
            knowledge = GaiaKnowledge(
                source="knowledge_model",
                source_id=model.model_id,
                knowledge_type="pattern",
                title=model.name,
                content=f"[{model.category}] {model.content[:2000]}",
                tags=model.tags if model.tags else [],
                confidence=model.confidence,
                impact_score=model.confidence * 0.9,
                is_active=True,
                vector_embedded=False,
            )
            db.add(knowledge)
            synced += 1

            # 也标记模型已同步
            model.vector_embedded = True

        await db.flush()

        logger.info(
            "同步完成: %d 条新增, %d 条已存在",
            synced, skipped,
        )
        return {"synced": synced, "skipped": skipped, "total": synced + skipped}


# 服务单例
_knowledge_model_service: KnowledgeModelService | None = None


def get_knowledge_model_service() -> KnowledgeModelService:
    global _knowledge_model_service
    if _knowledge_model_service is None:
        _knowledge_model_service = KnowledgeModelService()
    return _knowledge_model_service
