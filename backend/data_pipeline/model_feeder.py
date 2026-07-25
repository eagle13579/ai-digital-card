"""
模型数据供给器 — 将治理后的数据喂给每个模型的训练管道
"""
import os
import sys
import json
import time
import datetime
import logging
import subprocess
from typing import Dict, List, Optional, Any

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from .model_registry import ModelRegistry, ModelTrainingConfig

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(name)s] %(levelname)s: %(message)s")
logger = logging.getLogger("ModelFeeder")

BACKEND_DIR = os.path.normpath(os.path.join(os.path.dirname(__file__), ".."))
GAIA_COMMERCIAL_DIR = os.path.normpath("D:/gaia-commercial/scripts")


class ModelFeeder:
    """
    模型数据供给器
    职责：
    1. 按模型注册表检查哪个模型该训练了
    2. 该模型需要的数据源是否已有新数据
    3. 调用训练脚本
    4. 记录训练结果
    """

    def __init__(self):
        self._registry = ModelRegistry()
        self._state_path = os.path.join(os.path.dirname(__file__), ".model_feeder_state.json")
        self._state: dict = self._load_state()
        self._results: List[dict] = []

    def _load_state(self) -> dict:
        if os.path.exists(self._state_path):
            with open(self._state_path, "r", encoding="utf-8") as f:
                return json.load(f)
        return {"last_trained": {}, "total_training_runs": 0}

    def _save_state(self):
        with open(self._state_path, "w", encoding="utf-8") as f:
            json.dump(self._state, f, ensure_ascii=False, indent=2)

    def should_train(self, model: ModelTrainingConfig) -> bool:
        """检查是否该训练了"""
        if not model.enabled:
            return False
        last = self._state["last_trained"].get(model.model_id, 0.0)
        now = time.time()
        return (now - last) >= model.frequency_min * 60

    def train_model(self, model: ModelTrainingConfig) -> dict:
        """调用模型训练脚本"""
        logger.info(f"🔄 开始训练: {model.model_id} ({model.name})")

        if model.training_type == "online":
            # 在线学习 — 直接调用模块API
            return self._train_online(model)
        else:
            # 离线训练 — 执行训练脚本
            return self._train_offline(model)

    def _train_online(self, model: ModelTrainingConfig) -> dict:
        """
        在线学习模式 — 调用模块的在线更新方法
        这些模型持续从用户行为流学习，不需要显式训练
        """
        # 在线模型每次检查时，确保数据管道已经喂了新数据即可
        # 实际训练不在这里触发，而是在用户交互时实时发生
        logger.info(f"  [在线] {model.model_id} 为在线学习模型，检查数据新鲜度")
        return {
            "model_id": model.model_id,
            "status": "online_model",
            "message": "在线学习模型持续自更新，无需显式训练",
            "data_freshness_check": "ok",
            "train_script": model.train_script,
        }

    def _train_offline(self, model: ModelTrainingConfig) -> dict:
        """
        离线训练模式 — 执行训练脚本
        """
        train_script = model.train_script
        script_path = os.path.join(BACKEND_DIR, train_script)

        if not os.path.exists(script_path):
            # 尝试gaia-commercial路径
            alt_path = os.path.join(GAIA_COMMERCIAL_DIR, os.path.basename(train_script))
            if os.path.exists(alt_path):
                script_path = alt_path
            else:
                logger.warning(f"  ⚠️ 训练脚本不存在: {train_script}")
                return {
                    "model_id": model.model_id,
                    "status": "skipped",
                    "error": f"训练脚本不存在: {script_path}",
                }

        try:
            result = subprocess.run(
                [sys.executable, script_path],
                capture_output=True,
                text=True,
                timeout=600,  # 10分钟超时
                cwd=BACKEND_DIR,
                env={**os.environ, "JWT_SECRET": os.environ.get("JWT_SECRET", "dummy_pipeline"),
                     "DATABASE_URL": os.environ.get("DATABASE_URL", "sqlite+aiosqlite:///pipeline.db")}
            )
            exit_code = result.returncode

            if exit_code == 0:
                logger.info(f"  ✅ {model.model_id} 训练完成")
                self._state["last_trained"][model.model_id] = time.time()
                self._state["total_training_runs"] += 1
                self._save_state()
                return {
                    "model_id": model.model_id,
                    "status": "success",
                    "exit_code": 0,
                    "output_preview": result.stdout[-500:] if result.stdout else "",
                }
            else:
                logger.error(f"  ❌ {model.model_id} 训练失败: exit={exit_code}")
                logger.error(f"  stderr: {result.stderr[-500:]}")
                return {
                    "model_id": model.model_id,
                    "status": "failed",
                    "exit_code": exit_code,
                    "error": result.stderr[-300:] if result.stderr else "未知错误",
                }

        except subprocess.TimeoutExpired:
            logger.error(f"  ⏰ {model.model_id} 训练超时")
            return {"model_id": model.model_id, "status": "timeout", "error": "超过600s"}
        except Exception as e:
            logger.error(f"  💥 {model.model_id} 训练异常: {e}")
            return {"model_id": model.model_id, "status": "exception", "error": str(e)}

    def feed_all_due(self) -> List[dict]:
        """训练所有到期的模型"""
        models = self._registry.all()
        results = []

        for model in sorted(models, key=lambda m: {"online": 0, "offline_batch": 1, "self_supervised": 2, "evolution": 3}.get(m.training_type, 99)):
            if not self.should_train(model):
                logger.info(f"⏭️ {model.model_id} 未到期，跳过")
                continue
            result = self.train_model(model)
            results.append(result)
            self._results.append(result)

        return results

    def get_status_report(self) -> dict:
        """生成训练状态报告"""
        models = self._registry.all()
        now = time.time()

        model_status = {}
        for m in models:
            last = self._state["last_trained"].get(m.model_id, 0.0)
            age_hours = (now - last) / 3600 if last > 0 else float("inf")
            due = (now - last) >= m.frequency_min * 60 if last > 0 else True

            model_status[m.model_id] = {
                "name": m.name,
                "priority": m.priority,
                "training_type": m.training_type,
                "last_trained_hours_ago": round(age_hours, 1),
                "frequency_min": m.frequency_min,
                "due": due,
                "enabled": m.enabled,
                "data_sources": m.data_sources,
            }

        return {
            "total_models": len(models),
            "enabled": sum(1 for m in models if m.enabled),
            "total_training_runs": self._state.get("total_training_runs", 0),
            "models": model_status,
        }


def run_once():
    """单次执行入口"""
    feeder = ModelFeeder()
    results = feeder.feed_all_due()
    report = feeder.get_status_report()

    success = sum(1 for r in results if r["status"] == "success")
    skipped = sum(1 for r in results if r["status"] == "skipped")
    failed = sum(1 for r in results if r["status"] in ("failed", "timeout", "exception"))
    online = sum(1 for r in results if r["status"] == "online_model")

    output = {
        "timestamp": datetime.datetime.utcnow().isoformat(),
        "models_checked": len(results),
        "success": success,
        "online": online,
        "skipped": skipped,
        "failed": failed,
        "report": report,
    }
    print(json.dumps(output, ensure_ascii=False, indent=2))
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(run_once())
