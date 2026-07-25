"""
统一爬虫调度器 — 管理所有数据源采集任务
"""
import os
import sys
import json
import time
import datetime
import logging
from typing import Dict, List, Optional

# 路径修复
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(name)s] %(levelname)s: %(message)s")
logger = logging.getLogger("CrawlerOrchestrator")

REGISTRY_PATH = os.path.join(os.path.dirname(__file__), "data_source_registry.json")
STATE_PATH = os.path.join(os.path.dirname(__file__), ".crawler_state.json")


class CrawlerOrchestrator:
    """
    爬虫调度器 — 按数据源注册表调度所有采集任务
    支持：
    - 按频率调度（避免过频采集）
    - 按数据源依赖排序
    - 失败重试 + 告警
    - 记录采集统计
    """

    def __init__(self):
        self._registry = self._load_registry()
        self._state: Dict[str, dict] = self._load_state()
        self._results: List[dict] = []

    def _load_registry(self) -> dict:
        with open(REGISTRY_PATH, "r", encoding="utf-8") as f:
            return json.load(f)

    def _load_state(self) -> dict:
        if os.path.exists(STATE_PATH):
            with open(STATE_PATH, "r", encoding="utf-8") as f:
                return json.load(f)
        return {"last_collected": {}, "total_items": 0, "last_run": ""}

    def _save_state(self):
        with open(STATE_PATH, "w", encoding="utf-8") as f:
            json.dump(self._state, f, ensure_ascii=False, indent=2)

    def should_collect(self, source_id: str) -> bool:
        """检查是否该采集了（基于频率）"""
        sources = self._registry.get("sources", {})
        source = sources.get(source_id)
        if not source or not source.get("enabled", False):
            return False

        freq_min = source.get("frequency_min", 60)
        last = self._state["last_collected"].get(source_id, 0)
        now = time.time()

        return (now - last) >= freq_min * 60

    def collect_all_due(self) -> List[dict]:
        """采集所有到期的数据源"""
        results = []
        sources = self._registry.get("sources", {})

        for source_id, source in sources.items():
            if not source.get("enabled", False):
                continue
            if not self.should_collect(source_id):
                logger.info(f"⏭️ {source_id} 未到期，跳过")
                continue

            logger.info(f"🔄 开始采集: {source_id} ({source.get('name', '')})")
            try:
                result = self._collect_single(source_id, source)
                results.append(result)
                self._state["last_collected"][source_id] = time.time()
                self._state["total_items"] += result.get("items_count", 0)
                logger.info(f"✅ {source_id} 采集完成: {result.get('items_count', 0)} 条")
            except Exception as e:
                logger.error(f"❌ {source_id} 采集失败: {e}")
                results.append({
                    "source_id": source_id,
                    "status": "error",
                    "error": str(e),
                    "items_count": 0,
                    "timestamp": datetime.datetime.utcnow().isoformat()
                })

        self._state["last_run"] = datetime.datetime.utcnow().isoformat()
        self._save_state()
        self._results = results
        return results

    def _collect_single(self, source_id: str, source: dict) -> dict:
        """采集单个数据源（桩实现 — 真实场景调对应引擎）"""
        engine = source.get("engine", "")

        items_count = 0
        if engine == "web_search":
            # 模拟web search采集
            items_count = self._simulate_web_search(source)
        elif engine == "qichacha_client":
            items_count = self._simulate_qichacha(source)
        else:
            # 通用：记录已注册但暂未实现真实调用的数据源
            items_count = self._log_unimplemented(source_id, source)

        return {
            "source_id": source_id,
            "status": "success",
            "items_count": items_count,
            "collected_files": [f"data/raw/{source_id}_{int(time.time())}.json"],
            "timestamp": datetime.datetime.utcnow().isoformat()
        }

    def _simulate_web_search(self, source: dict) -> int:
        """（桩）执行web_search — 实际该调Hermes web_search工具"""
        logger.info(f"  [桩] web_search 采集: {source.get('name', '')}")
        # TODO: 接入真实 web_search 工具
        return 0

    def _simulate_qichacha(self, source: dict) -> int:
        """（桩）企查查采集"""
        logger.info(f"  [桩] qichacha 采集: {source.get('name', '')}")
        return 0

    def _log_unimplemented(self, source_id: str, source: dict) -> int:
        """记录未实现的采集器"""
        logger.info(f"  [未实现] {source_id}: {source.get('engine', '')} 采集器待接入")
        return 0

    def get_status_report(self) -> dict:
        """生成状态报告"""
        sources = self._registry.get("sources", {})
        now = time.time()

        source_status = {}
        for sid, src in sources.items():
            last = self._state["last_collected"].get(sid, 0)
            freq = src.get("frequency_min", 60)
            age = (now - last) / 60 if last > 0 else float("inf")
            due = age >= freq

            source_status[sid] = {
                "name": src.get("name", ""),
                "enabled": src.get("enabled", False),
                "last_collected_min_ago": round(age, 1),
                "frequency_min": freq,
                "due": due,
                "models_fed": src.get("models_fed", []),
            }

        return {
            "total_sources": len(sources),
            "enabled": sum(1 for s in sources.values() if s.get("enabled")),
            "source_status": source_status,
            "total_items_collected": self._state.get("total_items", 0),
            "last_run": self._state.get("last_run", "never"),
        }


def run_once():
    """单次执行入口（用于cron）"""
    orchestrator = CrawlerOrchestrator()
    results = orchestrator.collect_all_due()
    report = orchestrator.get_status_report()

    # 输出报告
    active = sum(1 for r in results if r["status"] == "success")
    errors = sum(1 for r in results if r["status"] == "error")
    items = sum(r.get("items_count", 0) for r in results)

    output = {
        "timestamp": datetime.datetime.utcnow().isoformat(),
        "sources_collected": len(results),
        "success": active,
        "errors": errors,
        "total_items": items,
        "report": report,
    }
    print(json.dumps(output, ensure_ascii=False, indent=2))
    return 0 if errors == 0 else 1


if __name__ == "__main__":
    sys.exit(run_once())
