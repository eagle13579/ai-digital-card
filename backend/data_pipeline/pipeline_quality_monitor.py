"""
P3: 数据管道质量监控 — 训练结果 + 数据新鲜度 + 告警
============================================
检查维度：
1. 训练成功率 → 近24h/7d趋势，连续失败告警
2. 数据新鲜度 → 每个数据源距上次采集时间，超阈值告警
3. 数据清洗质量 → 去重率/数据量变化
4. 模型训练结果 → 最近一次训练是否成功
5. 告警推送 → 通过AlertChannel推送降级
"""
import os
import sys
import json
import time
import datetime
import logging
from typing import Dict, List, Optional
from collections import defaultdict

BACKEND_DIR = os.path.normpath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, BACKEND_DIR)

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(name)s] %(levelname)s: %(message)s")
logger = logging.getLogger("QualityMonitor")

STATE_FILE = os.path.join(os.path.dirname(__file__), ".pipeline_quality.json")
ALERT_HISTORY_FILE = os.path.join(os.path.dirname(__file__), ".quality_alerts.json")

# 阈值
THRESHOLDS = {
    "max_source_stale_minutes": 180,       # 数据源超过180分钟未采集 → WARN
    "max_source_dead_minutes": 1440,       # 超过24h未采集 → CRITICAL
    "min_items_per_source": 1,             # 每次采集至少1条
    "training_fail_threshold": 3,          # 连续3次失败 → 告警
    "dedup_rate_warn": 0.8,               # 去重率>80% → 可能数据源枯竭
    "data_volume_drop_warn": 0.5,         # 数据量比上次下降50% → 告警
    "max_staleness_model_hours": 72,       # 模型超过72h未训练→告警
}


def _now_ts() -> float:
    return datetime.datetime.utcnow().timestamp()


class PipelineQualityState:
    """持久化的质量状态"""

    def __init__(self):
        self._state = self._load()

    def _load(self) -> dict:
        if os.path.exists(STATE_FILE):
            try:
                with open(STATE_FILE, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                pass
        return {
            "training_history": [],       # [{model_id, status, timestamp, error}]
            "collection_history": [],      # [{source_id, items, timestamp, status}]
            "cleaning_history": [],        # [{source_id, input_count, kept, dedup, timestamp}]
            "quality_scores": {},          # {source_id: {score, last_updated, trend}}
            "alerts_sent": [],             # [{message, level, timestamp}]
            "last_check": ""
        }

    def save(self):
        os.makedirs(os.path.dirname(STATE_FILE), exist_ok=True)
        with open(STATE_FILE, "w", encoding="utf-8") as f:
            json.dump(self._state, f, ensure_ascii=False, indent=2)

    def record_training(self, model_id: str, status: str, error: str = ""):
        self._state["training_history"].append({
            "model_id": model_id, "status": status,
            "error": error[:200] if error else "",
            "timestamp": datetime.datetime.utcnow().isoformat()
        })
        # 仅保留最近1000条
        if len(self._state["training_history"]) > 1000:
            self._state["training_history"] = self._state["training_history"][-1000:]
        self.save()

    def record_collection(self, source_id: str, items: int, status: str):
        self._state["collection_history"].append({
            "source_id": source_id, "items": items,
            "status": status,
            "timestamp": datetime.datetime.utcnow().isoformat()
        })
        if len(self._state["collection_history"]) > 2000:
            self._state["collection_history"] = self._state["collection_history"][-2000:]
        self.save()

    def record_cleaning(self, source_id: str, input_count: int,
                        kept: int, dedup: int):
        self._state["cleaning_history"].append({
            "source_id": source_id, "input_count": input_count,
            "kept": kept, "dedup": dedup,
            "timestamp": datetime.datetime.utcnow().isoformat()
        })
        if len(self._state["cleaning_history"]) > 2000:
            self._state["cleaning_history"] = self._state["cleaning_history"][-2000:]
        self.save()


class QualityMonitor:
    """质量监控器 — 检查5个维度+告警"""

    def __init__(self):
        self._state = PipelineQualityState()
        self._alerts: List[dict] = []
        self._has_alert_channel = self._check_alert_channel()

    def _check_alert_channel(self) -> bool:
        """检查告警通道是否可用"""
        try:
            sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "..", "scripts"))
            from alert_channel import AlertChannel  # noqa
            return True
        except Exception:
            return False

    def _send_alert(self, title: str, message: str, level: str = "WARN"):
        """发送告警"""
        try:
            alert_path = os.path.join(BACKEND_DIR, "..", "..", "..",
                                      "..", "scripts", "alert_channel.py")
            alert_abs = os.path.normpath(alert_path)
            if os.path.exists(alert_abs):
                import subprocess
                priority = "P1" if level == "WARN" else "P0"
                subprocess.run(
                    [sys.executable, alert_abs, "--send",
                     f"--title={title}", f"--message={message}",
                     f"--priority={priority}"],
                    capture_output=True, text=True, timeout=10
                )
        except Exception as e:
            logger.warning(f"告警发送失败: {e}")

        self._alerts.append({
            "title": title, "message": message[:200],
            "level": level,
            "timestamp": datetime.datetime.utcnow().isoformat()
        })

    # ─── 检查1: 模型训练成功率 ───

    def check_training_health(self) -> List[dict]:
        """检查训练失败检测：连续失败→告警"""
        issues = []
        history = self._state._state["training_history"]
        model_fails = defaultdict(int)

        for h in reversed(history[-200:]):
            if h["status"] in ("failed", "timeout", "exception"):
                model_fails[h["model_id"]] += 1
            else:
                model_fails[h["model_id"]] = 0

        for model_id, fails in model_fails.items():
            if fails >= THRESHOLDS["training_fail_threshold"]:
                msg = f"模型{model_id}连续{fails}次训练失败"
                issues.append({
                    "type": "training_failure",
                    "severity": "CRITICAL",
                    "target": model_id,
                    "message": msg,
                    "count": fails
                })
                self._send_alert("⚠️ 模型训练告警", msg, level="CRITICAL")

        # 整体成功率
        recent = [h for h in history[-100:] if h["status"] != "online_model"]
        if recent:
            success = sum(1 for h in recent if h["status"] == "success")
            rate = success / len(recent)
            if rate < 0.6:
                issues.append({
                    "type": "training_success_rate",
                    "severity": "WARN",
                    "target": "all",
                    "message": f"近100次训练成功率{rate:.0%}",
                    "rate": rate
                })
                self._send_alert("⚠️ 训练成功率下降", f"成功率{rate:.0%}", level="WARN")

        return issues

    # ─── 检查2: 数据新鲜度 ───

    def check_data_freshness(self) -> List[dict]:
        """检查数据源采集新鲜度"""
        issues = []
        now = _now_ts()

        registry_path = os.path.join(os.path.dirname(__file__), "data_source_registry.json")
        if not os.path.exists(registry_path):
            return []

        with open(registry_path, "r", encoding="utf-8") as f:
            registry = json.load(f)

        for source_id, source in registry.get("sources", {}).items():
            if not source.get("enabled", False):
                continue

            freq_min = source.get("frequency_min", 60)
            max_stale = max(freq_min * 3, THRESHOLDS["max_source_stale_minutes"])

            # 从collection_history中找最后一次
            last = None
            for h in reversed(self._state._state["collection_history"]):
                if h["source_id"] == source_id:
                    last = h
                    break

            if not last:
                issues.append({
                    "type": "freshness",
                    "severity": "CRITICAL",
                    "target": source_id,
                    "message": f"数据源{source_id}从未采集过"
                })
                continue

            try:
                last_ts = datetime.datetime.fromisoformat(last["timestamp"]).timestamp()
                age_min = (now - last_ts) / 60
            except Exception:
                continue

            if age_min > THRESHOLDS["max_source_dead_minutes"]:
                issues.append({
                    "type": "freshness",
                    "severity": "CRITICAL",
                    "target": source_id,
                    "message": f"{source_id}已{age_min:.0f}分钟未采集(阈值{max_stale}min)"
                })
                self._send_alert("🔴 数据源失联", f"{source_id} {age_min:.0f}分钟无数据",
                                 level="CRITICAL")
            elif age_min > max_stale:
                issues.append({
                    "type": "freshness",
                    "severity": "WARN",
                    "target": source_id,
                    "message": f"{source_id}已{age_min:.0f}分钟未采集(应≤{max_stale}min)"
                })

        return issues

    # ─── 检查3: 清洗质量 ───

    def check_cleaning_quality(self) -> List[dict]:
        """检查数据清洗质量：去重率异常/数据量骤降"""
        issues = []
        history = self._state._state["cleaning_history"]

        # 按source_id分组检查最近2次
        source_records = defaultdict(list)
        for h in history:
            source_records[h["source_id"]].append(h)

        for source_id, records in source_records.items():
            if len(records) < 2:
                continue

            last = records[-1]
            prev = records[-2]

            # 去重率检查
            if last["input_count"] > 0:
                dedup_rate = last["dedup"] / last["input_count"]
                if dedup_rate > THRESHOLDS["dedup_rate_warn"]:
                    issues.append({
                        "type": "cleaning_dedup",
                        "severity": "WARN",
                        "target": source_id,
                        "message": f"{source_id}去重率{dedup_rate:.0%}，数据源可能枯竭",
                        "dedup_rate": dedup_rate
                    })

            # 数据量骤降
            if prev["kept"] > 0 and last["kept"] < prev["kept"] * THRESHOLDS["data_volume_drop_warn"]:
                issues.append({
                    "type": "cleaning_volume_drop",
                    "severity": "WARN",
                    "target": source_id,
                    "message": f"{source_id}数据量从{prev['kept']}骤降至{last['kept']}",
                    "drop_ratio": last["kept"] / prev["kept"] if prev["kept"] else 0
                })

        return issues

    # ─── 检查4: 模型过时检查 ───

    def check_model_staleness(self) -> List[dict]:
        """检查模型是否过时"""
        issues = []
        from .model_registry import ModelRegistry
        reg = ModelRegistry()

        for model in reg.all():
            if not model.enabled:
                continue
            if model.training_type == "online":
                continue

            last = None
            for h in reversed(self._state._state["training_history"]):
                if h["model_id"] == model.model_id:
                    last = h
                    break

            if not last:
                issues.append({
                    "type": "model_staleness",
                    "severity": "WARN",
                    "target": model.model_id,
                    "message": f"模型{model.model_id}从未训练过"
                })
                continue

            try:
                last_ts = datetime.datetime.fromisoformat(last["timestamp"]).timestamp()
                age_hours = (_now_ts() - last_ts) / 3600
            except Exception:
                continue

            if age_hours > THRESHOLDS["max_staleness_model_hours"]:
                issues.append({
                    "type": "model_staleness",
                    "severity": "WARN",
                    "target": model.model_id,
                    "message": f"{model.model_id}已{age_hours:.0f}h未训练(阈值{THRESHOLDS['max_staleness_model_hours']}h)",
                    "age_hours": age_hours
                })

        return issues

    # ─── 全量检查 ───

    def run_all_checks(self) -> dict:
        """执行全部5项质量检查"""
        logger.info("🔍 P3质量监控: 5维检查...")

        checks = {
            "training_health": self.check_training_health(),
            "data_freshness": self.check_data_freshness(),
            "cleaning_quality": self.check_cleaning_quality(),
            "model_staleness": self.check_model_staleness(),
        }

        all_issues = []
        for check_name, issues in checks.items():
            for i in issues:
                i["check"] = check_name
                all_issues.append(i)

        # 统计
        criticals = [i for i in all_issues if i["severity"] == "CRITICAL"]
        warnings = [i for i in all_issues if i["severity"] == "WARN"]
        info = [i for i in all_issues if i["severity"] == "INFO"]

        self._state._state["last_check"] = datetime.datetime.utcnow().isoformat()
        self._state.save()

        result = {
            "timestamp": datetime.datetime.utcnow().isoformat(),
            "overall_status": "healthy" if not criticals else "degraded" if not [c for c in criticals if c["severity"]=="CRITICAL"] else "critical",
            "summary": {
                "total_checks": 4,
                "issues_total": len(all_issues),
                "critical": len(criticals),
                "warnings": len(warnings),
                "info": len(info),
            },
            "issues": all_issues,
            "alerts_sent": self._alerts,
            "state": {
                "training_records": len(self._state._state["training_history"]),
                "collection_records": len(self._state._state["collection_history"]),
                "cleaning_records": len(self._state._state["cleaning_history"]),
            }
        }

        # 打印摘要
        logger.info(f"  状态: {result['overall_status']}")
        logger.info(f"  问题: {len(all_issues)}总 ({len(criticals)}个严重, {len(warnings)}个警告)")
        for i in all_issues[:5]:
            logger.info(f"    [{i['severity']}] {i['message']}")

        return result


def run_once():
    """单次执行入口（用于cron）"""
    monitor = QualityMonitor()
    result = monitor.run_all_checks()
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 1 if result.get("summary", {}).get("critical", 0) > 0 else 0


if __name__ == "__main__":
    sys.exit(run_once())
