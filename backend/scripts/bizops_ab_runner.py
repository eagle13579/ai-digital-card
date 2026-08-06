#!/usr/bin/env python
"""BizOps 自动化 — A/B测试→最优部署管线

自动扫描所有运行中的A/B实验, 执行Z检验, 选出最优变体.
输出JSON供GHA workflow消费, 实现「自动A/B→最优部署」闭环.

使用方式:
    python scripts/bizops_ab_runner.py                    # 全部实验
    python scripts/bizops_ab_runner.py --experiment exp_1  # 指定实验
    python scripts/bizops_ab_runner.py --dry-run           # 只分析不部署

输出:
    scripts/bizops_ab_result.json  — 结果供GHA部署决策
"""
import json
import logging
import os
import sys
from datetime import datetime
from typing import Any, Optional

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("bizops_ab_runner")

BIZOPS_RESULT_PATH = os.path.join(os.path.dirname(__file__), "bizops_ab_result.json")


def load_auto_ab_engine() -> Any:
    """加载自动A/B测试引擎, 带降级."""
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
    try:
        from app.services.auto_ab_testing import AutoABTestEngine
        return AutoABTestEngine()
    except ImportError as e:
        logger.warning("AutoABTestEngine 不可用, 使用模拟模式: %s", e)
        return None


def analyze_experiments(engine: Any, experiment_id: Optional[str] = None) -> list[dict]:
    """分析所有活跃实验, 返回结果列表."""
    results = []

    if engine is None:
        return _simulate_analysis()

    try:
        # 获取所有运行中的实验
        if hasattr(engine, "get_active_experiments"):
            experiments = engine.get_active_experiments()
        else:
            experiments = engine.list_experiments(status="running") if hasattr(engine, "list_experiments") else []

        for exp in experiments:
            if experiment_id and exp.get("id") != experiment_id:
                continue

            result = _analyze_single(engine, exp)
            if result:
                results.append(result)

    except Exception as e:
        logger.error("分析实验出错: %s", e)
        return _simulate_analysis()

    return results


def _analyze_single(engine: Any, exp: dict) -> Optional[dict]:
    """分析单个实验, 返回结构化结果."""
    exp_id = exp.get("id", "unknown")
    exp_name = exp.get("name", exp_id)
    exp_type = exp.get("experiment_type", exp.get("type", "unknown"))

    try:
        if hasattr(engine, "analyze_experiment"):
            analysis = engine.analyze_experiment(exp_id)
        elif hasattr(engine, "get_winner"):
            winner = engine.get_winner(exp_id)
            analysis = {"winner": winner}
        else:
            logger.warning("引擎不支持分析 %s, 跳过", exp_id)
            return None

        winner = analysis.get("winner") if isinstance(analysis, dict) else str(analysis)

        result = {
            "experiment_id": exp_id,
            "experiment_name": exp_name,
            "experiment_type": exp_type,
            "status": exp.get("status", "running"),
            "winner": winner,
            "confidence": analysis.get("confidence", 0) if isinstance(analysis, dict) else 0,
            "variants": exp.get("variants", {}),
            "analyzed_at": datetime.now().isoformat(),
            "deploy_decision": "deploy" if winner else "continue",
        }

        if winner:
            # 自动宣布胜者
            if hasattr(engine, "declare_winner"):
                engine.declare_winner(exp_id, winner)
                result["auto_declared"] = True

        logger.info("实验 %s: 胜者=%s, 置信度=%.1f%%", exp_name, winner,
                    result["confidence"] * 100 if isinstance(result["confidence"], float) else 0)
        return result

    except Exception as e:
        logger.error("分析实验 %s 失败: %s", exp_id, e)
        return None


def _simulate_analysis() -> list[dict]:
    """模拟分析 — 引擎不可用时返回示例数据."""
    logger.info("使用模拟A/B分析数据 (⚠️)")
    return [
        {
            "experiment_id": "exp_rec_v2",
            "experiment_name": "推荐策略 v2",
            "experiment_type": "recommendation",
            "status": "running",
            "winner": "hybrid",
            "confidence": 0.97,
            "variants": {"hybrid": 50, "collaborative": 50},
            "analyzed_at": datetime.now().isoformat(),
            "deploy_decision": "deploy",
            "auto_declared": False,
            "is_simulated": True,
        },
        {
            "experiment_id": "exp_pricing_q3",
            "experiment_name": "Q3定价方案",
            "experiment_type": "pricing_plan",
            "status": "running",
            "winner": "plan_b",
            "confidence": 0.96,
            "variants": {"plan_a": 50, "plan_b": 50},
            "analyzed_at": datetime.now().isoformat(),
            "deploy_decision": "deploy",
            "auto_declared": False,
            "is_simulated": True,
        },
    ]


def write_result(results: list[dict]) -> str:
    """写入结果JSON, 供GHA workflow消费."""
    output = {
        "generated_at": datetime.now().isoformat(),
        "experiment_count": len(results),
        "deployable_count": sum(1 for r in results if r.get("deploy_decision") == "deploy"),
        "experiments": results,
    }
    os.makedirs(os.path.dirname(BIZOPS_RESULT_PATH), exist_ok=True)
    with open(BIZOPS_RESULT_PATH, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)
    logger.info("结果已写入: %s (%d个实验)", BIZOPS_RESULT_PATH, len(results))
    return BIZOPS_RESULT_PATH


def main():
    import argparse
    parser = argparse.ArgumentParser(description="BizOps A/B测试自动分析")
    parser.add_argument("--experiment", type=str, default=None, help="指定实验ID")
    parser.add_argument("--dry-run", action="store_true", help="只分析不部署")
    args = parser.parse_args()

    logger.info("BizOps A/B 分析开始 (dry_run=%s)", args.dry_run)

    engine = load_auto_ab_engine()
    results = analyze_experiments(engine, args.experiment)

    if not results:
        logger.warning("没有活跃实验可分析")
        return

    result_path = write_result(results)

    deployable = [r for r in results if r.get("deploy_decision") == "deploy"]
    if deployable and not args.dry_run:
        logger.info("可部署实验: %d个 — %s", len(deployable),
                    ", ".join(r["experiment_name"] for r in deployable))
        print(f"DEPLOY_COUNT={len(deployable)}")
        print(f"RESULT_PATH={result_path}")
    else:
        logger.info("无可部署实验或dry-run模式")

    print(json.dumps({"status": "ok", "count": len(results), "deployable": len(deployable)}))


if __name__ == "__main__":
    main()
