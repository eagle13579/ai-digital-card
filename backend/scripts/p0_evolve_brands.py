"""P0 进化循环脚本 — 将 P0 注入的 76 条品牌设计数据向量化

用法:
    cd D:\\AI数智名片\\backend
    python -m scripts.p0_evolve_brands

功能:
    1. 初始化 gaia brain
    2. 检查 gaia_knowledge 表中未向量化的条目（source='design_brand' 或 'design_token'）
    3. 打印待处理数量
    4. 运行 process_evolution_cycle 向量化这些数据
    5. 验证向量索引大小
    6. 打印各个模块的进化后权重
"""

import asyncio
import logging
import sys
from pathlib import Path

# 将项目根目录加入 sys.path
_BACKEND_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_BACKEND_DIR))

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("p0_evolve_brands")

# ---- Dependencies are imported lazily to avoid startup circular imports ----

async def main():
    logger.info("=" * 60)
    logger.info("P0 进化循环脚本启动")
    logger.info("目标: 将 76 条品牌设计数据向量化")
    logger.info("=" * 60)

    # 延迟导入，避免循环依赖
    from sqlalchemy import select, func as sa_func
    from app.database import AsyncSessionLocal
    from app.ai.gaia_evolution_brain import get_gaia_brain
    from app.models.gaia import GaiaKnowledge, GaiaModelWeights

    brain = get_gaia_brain()
    logger.info("GaiaBrain 已初始化，embedding backend=%s, dim=%d",
                brain._backend.name, brain._backend.dimension)

    async with AsyncSessionLocal() as db:
        # ── Step 2: 检查未向量化的品牌设计条目 ──────────────────────────
        design_sources = ["design_brand", "design_token"]

        # 统计所有品牌设计条目
        total_stmt = (
            select(sa_func.count())
            .select_from(GaiaKnowledge)
            .where(GaiaKnowledge.source.in_(design_sources))
        )
        total_count = (await db.execute(total_stmt)).scalar() or 0
        logger.info("品牌设计知识总量: %d 条", total_count)

        # 统计未向量化的条目
        pending_stmt = (
            select(GaiaKnowledge)
            .where(GaiaKnowledge.source.in_(design_sources))
            .where(GaiaKnowledge.vector_embedded.is_(False))
        )
        pending_result = await db.execute(pending_stmt)
        pending_knowledge = list(pending_result.scalars().all())
        pending_count = len(pending_knowledge)

        logger.info("待向量化的品牌设计知识: %d 条", pending_count)

        if pending_count == 0:
            logger.info("没有待向量化的条目，检查所有待向量化条目...")
            # 也检查所有来源的未向量化条目
            all_pending_stmt = (
                select(sa_func.count())
                .select_from(GaiaKnowledge)
                .where(GaiaKnowledge.vector_embedded.is_(False))
                .where(GaiaKnowledge.is_active.is_(True))
            )
            all_pending = (await db.execute(all_pending_stmt)).scalar() or 0
            logger.info("所有来源的待向量化条目: %d 条", all_pending)
            if all_pending == 0:
                logger.info("没有待向量化的条目，跳过进化循环")

        # ── Step 4: 运行进化循环 ────────────────────────────────────────
        if pending_count > 0:
            logger.info("开始进化循环 process_evolution_cycle ...")
            result = await brain.process_evolution_cycle(db, trigger="manual")
            logger.info("进化循环完成，结果: %s", result)

            if result.get("status") == "failed":
                logger.error("进化循环失败: %s", result.get("error"))
                return

        # ── Step 5: 验证向量索引大小 ───────────────────────────────────
        vector_size = brain.vector_index.size
        logger.info("向量索引当前大小: %d 条", vector_size)

        # ── Step 6: 打印各个模块的进化后权重 ───────────────────────────
        modules = [
            "recommendation",
            "search",
            "extractor",
            "writing",
            "optimization",
            "rag",
            "knowledge_graph",
        ]

        logger.info("\n" + "=" * 60)
        logger.info("各模块进化后权重:")
        logger.info("=" * 60)

        for module in modules:
            weights = await brain.get_evolved_weights(db, module)
            if weights:
                logger.info("[%s] version=%s", module, weights.get("version"))
                for k, v in weights.get("weights", {}).items():
                    logger.info("  %s = %s", k, v)
            else:
                logger.info("[%s] 无权重记录", module)

        # ── 最终状态汇总 ───────────────────────────────────────────────
        status = await brain.get_status(db)
        logger.info("\n" + "=" * 60)
        logger.info("GaiaBrain 最终状态:")
        logger.info("=" * 60)
        logger.info("向量索引大小: %d", status.get("vector_index_size", 0))
        kb = status.get("knowledge", {})
        logger.info("知识总量: %d, 活跃: %d, 已向量化: %d",
                    kb.get("total", 0), kb.get("active", 0), kb.get("embedded", 0))
        tr = status.get("training", {})
        last_run = tr.get("last_run")
        if last_run:
            logger.info("上次训练: id=%s, status=%s, trigger=%s",
                        last_run.get("id"), last_run.get("status"), last_run.get("trigger"))
        wt = status.get("weights", {})
        logger.info("权重版本总量: %d, 活跃权重数: %d",
                    wt.get("total_versions", 0), wt.get("active_weights", 0))

    logger.info("\n" + "=" * 60)
    logger.info("P0 进化循环脚本执行完毕")
    logger.info("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
