"""
DesignQA Cron — 每30分钟自动审核ant-design组件

定时任务:
1. 从 gaia_knowledge 表获取未审核的设计条目（source='design'）
2. 运行 critique_design() + audit_accessibility() + audit_performance() + detect_antipatterns()
3. 将审核结果写入 gaia_evolution_events 表
4. 审核报告保存到 logs/design_qa_audit_{timestamp}.json
"""
import asyncio
import json
import logging
import os
import sys
from datetime import datetime, timezone

# 确保项目路径在 sys.path 中
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

logger = logging.getLogger("design_qa_cron")

LOG_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))), "logs")
os.makedirs(LOG_DIR, exist_ok=True)


async def run_design_qa_audit() -> dict:
    """执行一轮 DesignQA 审核

    Returns:
        dict: 审核结果报告
    """
    from app.database import AsyncSessionLocal, engine
    from app.models.gaia import GaiaKnowledge, GaiaEvolutionEvent
    from app.database import Base
    from sqlalchemy import select, and_
    from app.agents.design_qa_agent import DesignQAAgent
    from app.agents.base_agent import AgentConfig

    # 确保表已创建
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    start_time = datetime.now(timezone.utc)

    # 初始化 DesignQAAgent（无 brain/broker/event_bus 的独立运行模式）
    config = AgentConfig(
        agent_name="design_qa_cron",
        agent_role="design_quality_assurance_engineer",
    )
    agent = DesignQAAgent(config=config)
    await agent.init()

    results = {
        "cycle_start": start_time.isoformat(),
        "audited_count": 0,
        "findings_count": 0,
        "reports": [],
        "errors": [],
    }

    async with AsyncSessionLocal() as db:
        try:
            # 查询未审核的设计条目（source 包含 'design' 或 knowledge_type 为 'design_component'）
            stmt = select(GaiaKnowledge).where(
                and_(
                    GaiaKnowledge.is_active == True,
                    (
                        GaiaKnowledge.source.like("%design%")
                        | (GaiaKnowledge.knowledge_type == "design_component")
                        | (GaiaKnowledge.knowledge_type == "ui_pattern")
                    ),
                )
            ).limit(20)  # 每轮最多处理20条

            result = await db.execute(stmt)
            entries = result.scalars().all()

            if not entries:
                logger.info("未找到未审核的设计条目，本轮跳过")
                results["status"] = "skipped"
                results["message"] = "no_design_entries_found"
                return results

            logger.info("发现 %d 条待审核设计条目", len(entries))

            for entry in entries:
                target_name = entry.title or f"design_entry_{entry.id}"
                target_desc = entry.content[:500] if entry.content else target_name

                try:
                    # ── 四项审核 ──
                    critique_result = await agent.critique_design({"target": target_name, "context": target_desc})
                    accessibility_result = await agent.audit_accessibility({"target": target_name, "context": target_desc})
                    performance_result = await agent.audit_performance({"target": target_name, "context": target_desc})
                    antipattern_result = await agent.detect_antipatterns({"target": target_name, "context": target_desc})

                    # ── 写入 gaia_evolution_events ──
                    combined_findings = (
                        critique_result.get("findings", [])
                        + accessibility_result.get("findings", [])
                        + performance_result.get("findings", [])
                        + antipattern_result.get("findings", [])
                    )

                    event = GaiaEvolutionEvent(
                        event_type="design_qa_audit_completed",
                        event_source="cron_design_qa",
                        description=f"DesignQA审核: {target_name} — "
                                    f"critique={critique_result.get('score_pct', 0)}%, "
                                    f"accessibility={accessibility_result.get('score_pct', 0)}%, "
                                    f"performance={performance_result.get('score_pct', 0)}%, "
                                    f"antipatterns={antipattern_result.get('score_pct', 0)}%",
                        event_meta={
                            "knowledge_id": entry.id,
                            "target": target_name,
                            "scores": {
                                "critique": critique_result.get("score_pct", 0),
                                "accessibility": accessibility_result.get("score_pct", 0),
                                "performance": performance_result.get("score_pct", 0),
                                "antipatterns": antipattern_result.get("score_pct", 0),
                            },
                            "total_findings": len(combined_findings),
                            "severity_counts": {
                                "P0": sum(1 for f in combined_findings if f.get("severity") == "P0"),
                                "P1": sum(1 for f in combined_findings if f.get("severity") == "P1"),
                                "P2": sum(1 for f in combined_findings if f.get("severity") == "P2"),
                                "P3": sum(1 for f in combined_findings if f.get("severity") == "P3"),
                            },
                        },
                        reference_type="knowledge",
                        reference_id=entry.id,
                    )
                    db.add(event)

                    report = {
                        "knowledge_id": entry.id,
                        "target": target_name,
                        "scores": {
                            "critique": {"score": critique_result.get("score"), "max": critique_result.get("max_score"), "pct": critique_result.get("score_pct")},
                            "accessibility": {"score": accessibility_result.get("score"), "max": accessibility_result.get("max_score"), "pct": accessibility_result.get("score_pct")},
                            "performance": {"score": performance_result.get("score"), "max": performance_result.get("max_score"), "pct": performance_result.get("score_pct")},
                            "antipatterns": {"score": antipattern_result.get("score"), "max": antipattern_result.get("max_score"), "pct": antipattern_result.get("score_pct")},
                        },
                        "total_findings": len(combined_findings),
                        "severity_counts": {
                            "P0": sum(1 for f in combined_findings if f.get("severity") == "P0"),
                            "P1": sum(1 for f in combined_findings if f.get("severity") == "P1"),
                            "P2": sum(1 for f in combined_findings if f.get("severity") == "P2"),
                            "P3": sum(1 for f in combined_findings if f.get("severity") == "P3"),
                        },
                        "recommendations": (
                            critique_result.get("recommendations", [])
                            + accessibility_result.get("recommendations", [])
                            + performance_result.get("recommendations", [])
                            + antipattern_result.get("recommendations", [])
                        )[:20],  # 最多20条建议
                    }
                    results["reports"].append(report)
                    results["audited_count"] += 1
                    results["findings_count"] += len(combined_findings)

                    logger.info("✅ 审核完成: %s — %d 个问题", target_name, len(combined_findings))

                except Exception as e:
                    error_msg = f"审核条目 {entry.id} ({target_name}) 失败: {e}"
                    logger.error(error_msg, exc_info=True)
                    results["errors"].append(error_msg)

            # 提交所有事件
            await db.commit()

        except Exception as e:
            await db.rollback()
            logger.error("DesignQA审核循环异常: %s", e, exc_info=True)
            results["errors"].append(str(e))
            results["status"] = "failed"
            return results

    # ── 保存审核报告到 JSON 文件 ──
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    report_path = os.path.join(LOG_DIR, f"design_qa_audit_{timestamp}.json")

    report_data = {
        "cycle_id": timestamp,
        "executed_at": datetime.now(timezone.utc).isoformat(),
        "entries_audited": results["audited_count"],
        "total_findings": results["findings_count"],
        "errors": results["errors"],
        "reports": results["reports"],
    }

    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(report_data, f, ensure_ascii=False, indent=2, default=str)

    await agent.stop()

    results["status"] = "completed"
    results["report_file"] = report_path
    results["duration_seconds"] = round((datetime.now(timezone.utc) - start_time).total_seconds(), 2)

    logger.info("📊 DesignQA审核完成: %d 条目, %d 问题, 报告: %s",
                results["audited_count"], results["findings_count"], report_path)

    return results


async def main():
    import argparse

    parser = argparse.ArgumentParser(description="DesignQA Cron — 每30分钟自动审核ant-design组件")
    parser.add_argument("--watch", action="store_true", help="持续监视模式（每30分钟自动运行）")
    parser.add_argument("--interval", type=int, default=30, help="监视模式的间隔分钟数（默认: 30）")
    parser.add_argument("--once", action="store_true", help="仅运行一次（默认行为）")

    args = parser.parse_args()

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
    )

    if args.watch:
        logger.info("🔁 DesignQA 审核 — 监视模式启动 (间隔=%d分钟)", args.interval)
        while True:
            try:
                result = await run_design_qa_audit()
                logger.info("📊 本轮结果: %s", result.get("status", "unknown"))
            except Exception as e:
                logger.error("DesignQA 审核异常: %s", e, exc_info=True)
            logger.info("💤 休眠 %d 分钟...", args.interval)
            await asyncio.sleep(args.interval * 60)
    else:
        # 单次运行
        logger.info("⚡ DesignQA 审核 — 单次运行")
        result = await run_design_qa_audit()
        print(f"\n📊 DesignQA 审核报告:")
        print(f"  状态: {result.get('status', 'unknown')}")
        print(f"  审核条目: {result.get('audited_count', 0)} 条")
        print(f"  发现问题: {result.get('findings_count', 0)} 个")
        print(f"  耗时: {result.get('duration_seconds', 0)}s")
        print(f"  报告: {result.get('report_file', 'N/A')}")
        if result.get("errors"):
            print(f"  错误: {len(result['errors'])} 个")
            for err in result["errors"][:3]:
                print(f"    - {err}")
        for report in result.get("reports", []):
            print(f"\n  📄 {report['target']}:")
            for name, score in report["scores"].items():
                print(f"    {name}: {score['pct']}% ({score['score']}/{score['max']})")
            print(f"    问题: {report['total_findings']} 个 "
                  f"(P0:{report['severity_counts']['P0']} "
                  f"P1:{report['severity_counts']['P1']} "
                  f"P2:{report['severity_counts']['P2']} "
                  f"P3:{report['severity_counts']['P3']})")


if __name__ == "__main__":
    asyncio.run(main())
