#!/usr/bin/env python3
"""
Mac Mini 数据管道训练器 — 7×24 模型训练守护
============================================
架构: Windows采集数据 → Mac Mini训练模型

职责:
1. 定期从 Windows 同步最新数据 (rsync/SMB)
2. 运行所有模型训练 (优先 MPS/MLX)
3. 记录训练日志
4. 保持 7×24 运行 (launchd)

用法:
  python3 mac_pipeline_trainer.py              # 完整周期 (同步+训练)
  python3 mac_pipeline_trainer.py --train-only # 仅训练 (已有数据)
  python3 mac_pipeline_trainer.py --dry-run    # 模拟运行
  python3 mac_pipeline_trainer.py --status     # 查看状态
"""
import os
import sys
import json
import time
import datetime
import logging
import subprocess
from pathlib import Path

# ── 路径 ──────────────────────────────────────────────────────
HOME = Path.home()
PIPELINE_DIR = HOME / "pipeline"
DATA_DIR = HOME / "pipeline_data"
MODELS_DIR = DATA_DIR / "models"
RAW_DIR = DATA_DIR / "raw"
CURATED_DIR = DATA_DIR / "curated"
LOG_DIR = PIPELINE_DIR / "logs"

# Windows 配置 — 自动发现
WIN_HOST = None       # 自动检测
WIN_USER = "56867"
WIN_PIPELINE = "/d/AI数智名片/backend/data_pipeline"
WIN_DATA = "/d/AI数智名片/backend/data"
WIN_SSH_PORT = 22
CONFIG_FILE = PIPELINE_DIR / "windows_ip.conf"


def _discover_windows_ip() -> str:
    """自动发现Windows主机的IP地址"""
    config_path = CONFIG_FILE

    # 1. 从配置文件读取
    if config_path.exists():
        ip = config_path.read_text().strip()
        result = subprocess.run(["ping", "-c", "1", "-W", "1", ip],
                                capture_output=True, text=True, timeout=3)
        if result.returncode == 0:
            logger.info(f"  ✅ 从配置读取Windows IP: {ip}")
            return ip
        logger.warning(f"  ⚠️ 配置中的IP {ip} 不可达，尝试自动发现")

    # 2. 扫描 ARP 表找 Windows 主机（SSH端口22）
    try:
        result = subprocess.run(["arp", "-a"], capture_output=True, text=True, timeout=5)
        for line in result.stdout.split("\n"):
            if "192.168." in line and ("dynamic" in line.lower() or "ether" in line.lower()):
                parts = line.strip().split()
                ip = parts[0] if "192.168." in parts[0] else parts[1] if len(parts) > 1 and "192.168." in parts[1] else None
                if ip:
                    # 快速ping测试
                    ping = subprocess.run(["ping", "-c", "1", "-W", "1", ip],
                                          capture_output=True, text=True, timeout=3)
                    if ping.returncode == 0:
                        logger.info(f"  ✅ ARP发现Windows: {ip}")
                        config_path.write_text(ip)
                        return ip
        return None
    except Exception as e:
        logger.warning(f"  ⚠️ ARP扫描失败: {e}")
        return None

# ── 日志 ──────────────────────────────────────────────────────
LOG_DIR.mkdir(parents=True, exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
    handlers=[
        logging.FileHandler(LOG_DIR / "trainer.log", encoding="utf-8"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("MacTrainer")


class MacPipelineTrainer:
    """Mac Mini 训练调度器"""

    def __init__(self):
        self._start_time = time.time()

    def sync_from_windows(self) -> bool:
        """从 Windows rsync 最新数据 (自动发现IP)"""
        global WIN_HOST
        logger.info("📡 从 Windows 同步数据...")

        # 自动发现 Windows IP
        if WIN_HOST is None:
            WIN_HOST = _discover_windows_ip()

        if WIN_HOST is None:
            logger.warning("  ⚠️ Windows 离线，使用上次同步的数据")
            return False

        logger.info(f"  ✅ Windows 在线 ({WIN_HOST})，开始 rsync...")

        # 同步管道代码 (增量)
        try:
            subprocess.run([
                "rsync", "-avz",
                f"{WIN_USER}@{WIN_HOST}:{WIN_PIPELINE}/",
                f"{PIPELINE_DIR}/"
            ], capture_output=True, text=True, timeout=120)
            logger.info("  ✅ 管道代码已同步")
        except Exception as e:
            logger.warning(f"  ⚠️ 代码同步失败: {e}")

        # 同步训练数据 (增量)
        try:
            subprocess.run([
                "rsync", "-avz",
                "--include=training_data.json", "--include=v2_training_data.json",
                "--include=online_weights.json", "--include=learning_log.jsonl",
                "--include=*.pt", "--include=raw/", "--include=curated/",
                "--exclude=*",
                f"{WIN_USER}@{WIN_HOST}:{WIN_DATA}/",
                f"{DATA_DIR}/"
            ], capture_output=True, text=True, timeout=120)
            logger.info("  ✅ 训练数据已同步")
        except Exception as e:
            logger.warning(f"  ⚠️ 数据同步失败: {e}")

        # 同步模型权重回 Windows (Mac训练产的 .pt 权重回流)
        try:
            model_files = list(MODELS_DIR.glob("*.pt")) + list(MODELS_DIR.glob("*.json"))
            if model_files:
                result = subprocess.run([
                    "rsync", "-avz",
                    f"{MODELS_DIR}/",
                    f"{WIN_USER}@{WIN_HOST}:{WIN_DATA}/models/"
                ], capture_output=True, text=True, timeout=60)
                logger.info(f"  ✅ 模型权重已回流 ({len(model_files)} 文件)")
        except Exception as e:
            logger.warning(f"  ⚠️ 模型回流失败: {e}")

        return True

    def train_all_models(self) -> dict:
        """通过subprocess运行训练（避免相对导入问题）"""
        logger.info("🧠 开始训练所有模型...")

        try:
            result = subprocess.run(
                [sys.executable, "-m", "pipeline_controller", "--mode", "train", "--json"],
                capture_output=True, text=True, timeout=600,
                cwd=str(PIPELINE_DIR),
                env={**os.environ, "JWT_SECRET": "mac_mini_pipeline", "PYTHONPATH": str(PIPELINE_DIR)}
            )

            if result.stdout:
                try:
                    report = json.loads(result.stdout)
                    success = report.get("feeder_status", {}).get("success", 0)
                    total = report.get("feeder_status", {}).get("total_models", 0)
                    logger.info(f"  ✅ {report.get('models_checked', 0)} 模型检查")
                    return {"status": "ok", "models_checked": report.get("models_checked", 0), "report": report}
                except json.JSONDecodeError:
                    logger.info(f"  输出: {result.stdout[:500]}")
                    return {"status": "parsed", "raw": result.stdout[:500]}

            return {"status": "no_output"}

        except subprocess.TimeoutExpired:
            logger.error("  ⏰ 训练超时")
            return {"status": "timeout"}
        except Exception as e:
            logger.error(f"  错误: {e}")
            return {"status": "error", "error": str(e)}

    def run_quality_check(self) -> dict:
        """运行质量检查"""
        logger.info("📊 运行质量检查...")
        sys.path.insert(0, str(PIPELINE_DIR))

        try:
            from pipeline_quality_monitor import QualityMonitor
            qm = QualityMonitor()
            return qm.run_all_checks()
        except ImportError as e:
            logger.warning(f"  质量检查跳过: {e}")
            return {"status": "skipped"}

    def run_full_cycle(self) -> dict:
        """完整周期: 同步+训练+质量"""
        logger.info("=" * 50)
        logger.info("🚀 Mac Mini 训练管道启动")
        logger.info("=" * 50)

        # Phase 1: 数据同步
        t0 = time.time()
        synced = self.sync_from_windows()
        sync_time = time.time() - t0

        # Phase 2: 模型训练
        t1 = time.time()
        train_result = self.train_all_models()
        train_time = time.time() - t1

        # Phase 3: 质量检查
        t2 = time.time()
        quality_result = self.run_quality_check()
        quality_time = time.time() - t2

        total_time = time.time() - self._start_time

        report = {
            "timestamp": datetime.datetime.now(datetime.UTC).isoformat(),
            "host": "Mac Mini",
            "total_elapsed_seconds": round(total_time, 1),
            "phases": {
                "sync": round(sync_time, 1),
                "train": round(train_time, 1),
                "quality": round(quality_time, 1),
            },
            "data_synced": synced,
            "training": train_result,
            "quality": quality_result,
        }

        logger.info(f"🏁 完成: {round(total_time, 1)}s")
        return report


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Mac Mini 训练管道")
    parser.add_argument("--train-only", action="store_true", help="仅训练（不同步）")
    parser.add_argument("--dry-run", action="store_true", help="模拟运行")
    parser.add_argument("--status", action="store_true", help="查看状态")
    args = parser.parse_args()

    trainer = MacPipelineTrainer()

    if args.status:
        # 显示最近运行状态
        log_file = LOG_DIR / "trainer.log"
        if log_file.exists():
            lines = log_file.read_text().splitlines()[-20:]
            for line in lines:
                print(line)
        else:
            print("⏳ 还没有运行记录")
        return

    if args.dry_run:
        print("🧪 Dry-run 模式: 检查环境和依赖")
        print(f"  PIPELINE_DIR: {PIPELINE_DIR}")
        print(f"  DATA_DIR: {DATA_DIR}")
        print(f"  Python: {sys.version}")
        print(f"  目录就绪: ✅" if PIPELINE_DIR.exists() else f"  目录就绪: ❌")
        if PIPELINE_DIR.exists():
            files = list(PIPELINE_DIR.glob("*.py"))
            print(f"  管道文件: {len(files)} 个 .py")
        return

    if args.train_only:
        report = trainer.train_all_models()
    else:
        report = trainer.run_full_cycle()

    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
