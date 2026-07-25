"""
统一数据管道控制器 — 主入口
全自动7×24数据流：爬虫采集 → 数据治理 → 模型训练
"""
import os
import sys
import json
import time
import datetime
import logging

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
    handlers=[
        logging.StreamHandler(),
    ]
)
logger = logging.getLogger("PipelineController")


class PipelineController:
    """
    数据管道主控制器
    调度链：Data Collection → Curation → Model Feeding
    每轮执行步骤：
    1. 数据采集：跑所有到期的爬虫
    2. 数据治理：去重+标准化
    3. 模型训练：喂给所有到期的模型
    """

    def __init__(self):
        self._phase_times: dict = {}

    def run_full_cycle(self) -> dict:
        """执行完整数据管道周期"""
        start = time.time()
        logger.info("=" * 60)
        logger.info("🚀 统一数据管道启动 — 全周期")
        logger.info("=" * 60)

        # Phase 1: 数据采集
        t0 = time.time()
        logger.info("📡 Phase 1: 数据采集...")
        from app.data_pipeline.crawler_orchestrator import CrawlerOrchestrator
        crawler = CrawlerOrchestrator()
        crawl_results = crawler.collect_all_due()
        self._phase_times["crawl"] = time.time() - t0
        logger.info(f"✅ 采集完成: {len(crawl_results)} 个数据源, {sum(r.get('items_count',0) for r in crawl_results)} 条")

        # Phase 2: 数据治理
        t1 = time.time()
        logger.info("🧹 Phase 2: 数据治理...")
        from app.data_pipeline.data_curator import get_curator
        curator = get_curator()
        curation_stats = curator.get_stats()
        self._phase_times["curation"] = time.time() - t1
        logger.info(f"✅ 治理完成: {curation_stats.get('total_unique_records', 0)} 条唯一记录")

        # Phase 3: 模型训练
        t2 = time.time()
        logger.info("🧠 Phase 3: 模型训练...")
        from app.data_pipeline.model_feeder import ModelFeeder
        feeder = ModelFeeder()
        train_results = feeder.feed_all_due()
        self._phase_times["training"] = time.time() - t2
        logger.info(f"✅ 训练完成: {len(train_results)} 个模型检查")

        # 汇总报告
        elapsed = time.time() - start
        report = {
            "timestamp": datetime.datetime.utcnow().isoformat(),
            "total_elapsed_seconds": round(elapsed, 2),
            "phases": self._phase_times,
            "crawl": {
                "sources_collected": len(crawl_results),
                "items": sum(r.get("items_count", 0) for r in crawl_results),
                "errors": sum(1 for r in crawl_results if r["status"] == "error"),
            },
            "curation": curation_stats,
            "training": {
                "models_checked": len(train_results),
                "success": sum(1 for r in train_results if r["status"] in ("success", "online_model")),
                "failed": sum(1 for r in train_results if r["status"] in ("failed", "timeout", "exception")),
            },
            "crawler_status": crawler.get_status_report(),
            "feeder_status": feeder.get_status_report(),
        }

        logger.info("=" * 60)
        logger.info(f"🏁 全周期完成: {round(elapsed, 1)}s")
        logger.info("=" * 60)

        return report

    def run_collect_only(self) -> dict:
        """仅执行数据采集阶段"""
        from app.data_pipeline.crawler_orchestrator import CrawlerOrchestrator
        crawler = CrawlerOrchestrator()
        results = crawler.collect_all_due()
        return {
            "timestamp": datetime.datetime.utcnow().isoformat(),
            "sources_collected": len(results),
            "crawler_status": crawler.get_status_report(),
        }

    def run_train_only(self) -> dict:
        """仅执行模型训练阶段"""
        from app.data_pipeline.model_feeder import ModelFeeder
        feeder = ModelFeeder()
        results = feeder.feed_all_due()
        return {
            "timestamp": datetime.datetime.utcnow().isoformat(),
            "models_checked": len(results),
            "feeder_status": feeder.get_status_report(),
        }


def main():
    """主入口（cron调用）"""
    import argparse
    parser = argparse.ArgumentParser(description="统一数据管道控制器")
    parser.add_argument("--mode", choices=["full", "collect", "train", "status"],
                        default="full", help="运行模式")
    parser.add_argument("--json", action="store_true", help="JSON输出")
    args = parser.parse_args()

    controller = PipelineController()

    if args.mode == "full":
        report = controller.run_full_cycle()
    elif args.mode == "collect":
        report = controller.run_collect_only()
    elif args.mode == "train":
        report = controller.run_train_only()
    elif args.mode == "status":
        from app.data_pipeline.crawler_orchestrator import CrawlerOrchestrator
        from app.data_pipeline.model_feeder import ModelFeeder
        report = {
            "crawler": CrawlerOrchestrator().get_status_report(),
            "feeder": ModelFeeder().get_status_report(),
        }

    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    else:
        print(f"📊 管道状态报告")
        print(f"  采集: {report.get('crawl', {}).get('sources_collected', 0)} 数据源")
        print(f"  训练: {report.get('training', {}).get('models_checked', 0)} 模型检查")
        print(f"  耗时: {report.get('total_elapsed_seconds', 0)}s")

    # 失败告警
    failed = report.get("training", {}).get("failed", 0)
    if failed > 0:
        logger.warning(f"⚠️ {failed} 个模型训练失败，请检查日志")
        sys.exit(1)


if __name__ == "__main__":
    main()
