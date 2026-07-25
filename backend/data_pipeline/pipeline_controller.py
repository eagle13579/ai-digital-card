"""
统一数据管道控制器 — 主入口
全自动7×24数据流：爬虫采集 → 数据清洗 → 模型训练

P1升级：
- Phase 2 真正清洗数据：去重/标准化/质量控制
- 采集的原始数据过data_curator后才喂给模型
- 清洗后的数据落盘到 data/curated/
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
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger("PipelineController")

BACKEND_DIR = os.path.normpath(os.path.join(os.path.dirname(__file__), ".."))  # data_pipeline/ → backend/
RAW_DATA_DIR = os.path.join(BACKEND_DIR, "data", "raw")
CURATED_DATA_DIR = os.path.join(BACKEND_DIR, "data", "curated")


class PipelineController:
    """
    数据管道主控制器
    调度链：Data Collection → Data Cleaning → Model Feeding

    清洗流程:
      1. 采集原始数据 → data/raw/{source}_{ts}.json
      2. 清洗原始数据 → data_curator去重+标准化
      3. 输出清洗后数据 → data/curated/{source}.json
      4. 喂给模型训练 → model_feeder调度
    """

    def __init__(self):
        self._phase_times: dict = {}
        os.makedirs(CURATED_DATA_DIR, exist_ok=True)

    def run_full_cycle(self) -> dict:
        """执行完整数据管道周期"""
        start = time.time()
        logger.info("=" * 60)
        logger.info("🚀 统一数据管道启动 — 全周期 (含数据清洗)")
        logger.info("=" * 60)

        # ─── Phase 1: 数据采集 ───
        t0 = time.time()
        logger.info("📡 Phase 1: 数据采集...")
        from crawler_orchestrator import CrawlerOrchestrator
        crawler = CrawlerOrchestrator()
        crawl_results = crawler.collect_all_due()
        self._phase_times["crawl"] = time.time() - t0

        total_crawled = sum(r.get("items_count", 0) for r in crawl_results)
        logger.info(f"  → 采集 {len(crawl_results)} 个数据源, {total_crawled} 条原始数据")

        # ─── Phase 2: 数据清洗 ───
        t1 = time.time()
        logger.info("🧹 Phase 2: 数据清洗（去重+标准化）...")
        from data_curator import get_curator
        curator = get_curator()

        cleaned_count = 0
        dup_removed = 0
        curation_files = []

        # 2a. 读取所有新采集的raw文件
        for result in crawl_results:
            src_id = result.get("source_id", "")
            raw_file = result.get("output_file", "")
            raw_items = []

            if raw_file and os.path.exists(raw_file):
                try:
                    with open(raw_file, "r", encoding="utf-8") as f:
                        raw_data = json.load(f)
                    raw_items = raw_data.get("items", [])
                except Exception as e:
                    logger.warning(f"    ⚠️ 读取 {raw_file} 失败: {e}")

            if not raw_items:
                continue

            logger.info(f"  🔄 清洗 {src_id}: {len(raw_items)} 条原始数据...")

            # 2b. 通过curator去重+标准化
            valid_items, dup_count, err_count = curator.batch_process(
                raw_items,
                source_type=self._detect_source_type(src_id)
            )

            cleaned_count += len(valid_items)
            dup_removed += dup_count

            logger.info(f"    ✅ {len(valid_items)} 条通过 / {dup_count} 条去重 / {err_count} 条错误")

            # 2c. 写入清洗后数据
            if valid_items:
                curated_path = os.path.join(CURATED_DATA_DIR, f"{src_id}.json")
                # 合并模式：读取已有+追加新数据
                existing = []
                if os.path.exists(curated_path):
                    try:
                        with open(curated_path, "r", encoding="utf-8") as f:
                            existing = json.load(f)
                    except Exception:
                        pass

                all_items = existing + valid_items
                # 最多保留10000条，超出则截取最新的
                if len(all_items) > 10000:
                    all_items = all_items[-10000:]

                with open(curated_path, "w", encoding="utf-8") as f:
                    json.dump(all_items, f, ensure_ascii=False, indent=2)

                curation_files.append(curated_path)
                logger.info(f"    💾 写入 {curated_path} ({len(all_items)} 条累积)")

        curation_stats = curator.get_stats()
        curation_stats["items_cleaned"] = cleaned_count
        curation_stats["duplicates_removed"] = dup_removed
        curation_stats["curated_files"] = curation_files

        self._phase_times["curation"] = time.time() - t1
        logger.info(f"  → 清洗完成: {cleaned_count} 条保留, {dup_removed} 条去重")

        # ─── Phase 3: 模型训练 ───
        t2 = time.time()
        logger.info("🧠 Phase 3: 模型训练...")
        from model_feeder import ModelFeeder
        feeder = ModelFeeder()
        train_results = feeder.feed_all_due()
        self._phase_times["training"] = time.time() - t2

        # 汇总
        elapsed = time.time() - start
        training_ok = sum(1 for r in train_results if r["status"] in ("success", "online_model"))
        training_fail = sum(1 for r in train_results if r["status"] in ("failed", "timeout", "exception"))

        # ─── Phase 4: 质量监控 ───
        t3 = time.time()
        logger.info("📊 Phase 4: 质量监控...")
        from pipeline_quality_monitor import QualityMonitor, PipelineQualityState
        qstate = PipelineQualityState()

        # 记录采集结果到质量状态
        for r in crawl_results:
            qstate.record_collection(
                r.get("source_id", "unknown"),
                r.get("items_count", 0),
                r.get("status", "unknown")
            )
        # 记录训练结果
        for r in train_results:
            qstate.record_training(
                r.get("model_id", r.get("model", "unknown")),
                r.get("status", "unknown"),
                r.get("error", "")
            )
        # 执行质量检查
        qm = QualityMonitor()
        quality_report = qm.run_all_checks()
        self._phase_times["quality"] = time.time() - t3
        logger.info(f"  → 质量状态: {quality_report.get('overall_status', 'unknown')}")

        # ─── Phase 5: 智能调度 ───
        t4 = time.time()
        logger.info("⚡ Phase 5: 智能调度分析...")
        from pipeline_scheduler import SmartScheduler
        scheduler = SmartScheduler()
        schedule_analysis = scheduler.analyze()
        scheduler.apply(dry_run=True)
        self._phase_times["scheduler"] = time.time() - t4
        logger.info(f"  → 建议调整: {schedule_analysis.get('total_adjustments', 0)} 项")

        # ─── Phase 6: 数据清理 ───
        t5 = time.time()
        logger.info("🧹 Phase 6: 数据清理（旋转旧raw文件）...")
        cleaned_bytes = 0
        if os.path.exists(RAW_DATA_DIR):
            for f in os.listdir(RAW_DATA_DIR):
                fpath = os.path.join(RAW_DATA_DIR, f)
                if not f.endswith(".json"):
                    continue
                age = time.time() - os.path.getmtime(fpath)
                if age > 72 * 3600:
                    cleaned_bytes += os.path.getsize(fpath)
                    os.remove(fpath)
        self._phase_times["cleanup"] = time.time() - t5
        if cleaned_bytes > 0:
            logger.info(f"  → 清理 {cleaned_bytes/1024:.0f}KB 旧raw文件")

        report = {
            "timestamp": datetime.datetime.utcnow().isoformat(),
            "total_elapsed_seconds": round(elapsed, 2),
            "phases": self._phase_times,
            "phase1_collect": {
                "sources": len(crawl_results),
                "items_raw": total_crawled,
                "errors": sum(1 for r in crawl_results if r["status"] == "error"),
            },
            "phase2_clean": {
                "items_in": total_crawled,
                "items_cleaned": cleaned_count,
                "duplicates_removed": dup_removed,
                "curated_files": curation_files,
            },
            "phase3_train": {
                "models_checked": len(train_results),
                "success": training_ok,
                "failed": training_fail,
            },
            "phase4_quality": {
                "status": quality_report.get("overall_status", ""),
                "issues_total": quality_report.get("summary", {}).get("issues_total", 0),
                "critical": quality_report.get("summary", {}).get("critical", 0),
                "warnings": quality_report.get("summary", {}).get("warnings", 0),
            },
            "phase5_scheduler": {
                "total_adjustments": schedule_analysis.get("total_adjustments", 0),
                "accelerated": schedule_analysis.get("changes", {}).get("accelerated", 0),
                "decelerated": schedule_analysis.get("changes", {}).get("decelerated", 0),
                "mode": "dry_run",
            },
            "crawler_status": crawler.get_status_report(),
            "feeder_status": feeder.get_status_report(),
        }

        logger.info("=" * 60)
        logger.info(f"🏁 全周期完成: {round(elapsed, 1)}s | "
                     f"采集{total_crawled}条→清洗{cleaned_count}条→训练{training_ok}个模型")
        logger.info("=" * 60)

        return report

    def run_collect_only(self) -> dict:
        """仅采集"""
        from crawler_orchestrator import CrawlerOrchestrator
        crawler = CrawlerOrchestrator()
        results = crawler.collect_all_due()
        return {
            "timestamp": datetime.datetime.utcnow().isoformat(),
            "sources_collected": len(results),
            "crawler_status": crawler.get_status_report(),
        }

    def run_train_only(self) -> dict:
        """仅训练"""
        from model_feeder import ModelFeeder
        feeder = ModelFeeder()
        results = feeder.feed_all_due()
        return {
            "timestamp": datetime.datetime.utcnow().isoformat(),
            "models_checked": len(results),
            "feeder_status": feeder.get_status_report(),
        }

    def _detect_source_type(self, source_id: str) -> str:
        """根据source_id判断数据类型"""
        mapping = {
            "enterprise_websites": "enterprise",
            "url_batch_crawler": "enterprise",
            "qichacha": "enterprise",
            "crm_matching_data": "user_behavior",
            "user_behavior_feedback": "feedback_loop",
            "xiaohongshu": "web_content",
            "baidu_search": "web_content",
            "web_pages_rag": "web_content",
            "knowledge_base": "enterprise",
        }
        return mapping.get(source_id, "enterprise")


def main():
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
        from crawler_orchestrator import CrawlerOrchestrator
        from model_feeder import ModelFeeder
        report = {
            "crawler": CrawlerOrchestrator().get_status_report(),
            "feeder": ModelFeeder().get_status_report(),
        }

    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    else:
        p1 = report.get("phase1_collect", {})
        p2 = report.get("phase2_clean", {})
        p3 = report.get("phase3_train", {})
        print(f"📊 数据管道状态")
        print(f"  📡 采集: {p1.get('sources', 0)} 数据源, {p1.get('items_raw', 0)} 条")
        print(f"  🧹 清洗: {p2.get('items_cleaned', 0)} 条保留, {p2.get('duplicates_removed', 0)} 条去重")
        print(f"  🧠 训练: {p3.get('models_checked', 0)} 模型检查, {p3.get('success', 0)} 成功")
        print(f"  ⏱️  总耗时: {report.get('total_elapsed_seconds', 0)}s")

    failed = p3.get("failed", 0) if not args.json else report.get("phase3_train", {}).get("failed", 0)
    if failed > 0:
        logger.warning(f"⚠️ {failed} 个模型训练失败，请检查日志")
        sys.exit(1)


if __name__ == "__main__":
    main()
