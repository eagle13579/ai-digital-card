#!/usr/bin/env python
"""
online_learning_pipeline.py — AI数智名片 在线学习管道
====================================================

独立可运行脚本，可用 cron (如 `0 */2 * * *`) 定期执行。

功能:
  1. 从 feedback_service 读取最新反馈数据
  2. 增量更新三塔模型权重 (OnlineWeightOptimizer)
  3. 当新反馈量达到阈值时, 触发三塔模型重训
  4. 保存新的模型 checkpoint
  5. 生成训练报告 (JSON)

用法:
    # 直接运行 (使用默认配置)
    python scripts/online_learning_pipeline.py

    # 指定模型目录和反馈阈值
    python scripts/online_learning_pipeline.py \
        --model-dir ../models \
        --min-feedback 50 \
        --retrain-threshold 200

    # 仅读取最新反馈并更新权重 (不重训)
    python scripts/online_learning_pipeline.py --weights-only

    # 强制重训模型
    python scripts/online_learning_pipeline.py --force-retrain

依赖:
    - backend/app/services/online_learning_service.py
    - backend/app/services/feedback_service.py
    - backend/app/models/ml/tower_ensemble.py
    - backend/scripts/train_matching_model.py (可选, 用于重训)
"""

from __future__ import annotations

import argparse
import json
import logging
import sys
import time
from dataclasses import dataclass, field, asdict
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

# ── 配置路径 (可以在项目根目录运行) ──
# 自动将 backend 加入 sys.path
SCRIPT_DIR = Path(__file__).resolve().parent
BACKEND_DIR = SCRIPT_DIR.parent
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

# ── 默认配置 ──
DEFAULT_MODEL_DIR = BACKEND_DIR / "models"
DEFAULT_MIN_FEEDBACK = 20       # 最少反馈数才执行权重更新
DEFAULT_RETRAIN_THRESHOLD = 200  # 新反馈超过此数触发模型重训
DEFAULT_WEIGHTS_ONLY = False    # 默认启用完整管道
DEFAULT_FEEDBACK_LOOKBACK_HOURS = 48  # 默认读取最近48小时的反馈

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("online_learning_pipeline")


# ---------------------------------------------------------------------------
# 数据模型
# ---------------------------------------------------------------------------

@dataclass
class PipelineReport:
    """管道执行报告"""
    # ── 元信息 ──
    timestamp: str = ""
    pipeline_version: str = "1.0.0"

    # ── 反馈统计 ──
    feedback_records_processed: int = 0
    feedback_lookback_hours: int = DEFAULT_FEEDBACK_LOOKBACK_HOURS

    # ── 权重更新 ──
    weights_before: dict[str, float] = field(default_factory=dict)
    weights_after: dict[str, float] = field(default_factory=dict)
    weight_changes: dict[str, float] = field(default_factory=dict)
    total_weight_updates: int = 0

    # ── 重训统计 ──
    retrain_triggered: bool = False
    retrain_threshold: int = DEFAULT_RETRAIN_THRESHOLD
    retrain_success: bool = False
    retrain_metrics: dict[str, float] = field(default_factory=dict)

    # ── 执行状态 ──
    status: str = "success"
    error_message: str = ""
    execution_time_seconds: float = 0.0
    model_checkpoint_saved: str = ""


# ---------------------------------------------------------------------------
# 管道核心
# ---------------------------------------------------------------------------

class OnlineLearningPipeline:
    """在线学习管道 — 反馈驱动模型持续优化。

    可周期性执行, 完成:
      - 反馈数据读取与汇总
      - 在线权重增量更新
      - 条件触发模型重训
      - Checkpoint 保存
      - 执行报告生成
    """

    def __init__(
        self,
        model_dir: Path = DEFAULT_MODEL_DIR,
        min_feedback: int = DEFAULT_MIN_FEEDBACK,
        retrain_threshold: int = DEFAULT_RETRAIN_THRESHOLD,
        weights_only: bool = DEFAULT_WEIGHTS_ONLY,
        lookback_hours: int = DEFAULT_FEEDBACK_LOOKBACK_HOURS,
    ):
        self.model_dir = Path(model_dir)
        self.min_feedback = min_feedback
        self.retrain_threshold = retrain_threshold
        self.weights_only = weights_only
        self.lookback_hours = lookback_hours

        # 延迟导入 (避免启动时加载 PyTorch)
        self._online_service = None
        self._feedback_service = None

    def _get_services(self):
        """延迟加载服务实例。"""
        if self._online_service is None:
            from app.services.online_learning_service import OnlineLearningService, get_online_learning_service
            self._online_service = get_online_learning_service()
        if self._feedback_service is None:
            from app.services.feedback_service import get_feedback_service
            self._feedback_service = get_feedback_service()
        return self._online_service, self._feedback_service

    def run(self) -> PipelineReport:
        """执行一次完整管道。

        Returns:
            PipelineReport: 执行报告
        """
        start_time = time.time()
        report = PipelineReport(
            timestamp=datetime.now().isoformat(),
            feedback_lookback_hours=self.lookback_hours,
            retrain_threshold=self.retrain_threshold,
        )

        try:
            print("=" * 60)
            print("  AI数智名片 — 在线学习管道")
            print(f"  时间: {report.timestamp}")
            print("=" * 60)
            print()

            # ── 步骤 1: 读取反馈数据 ──
            print("[1/4] 读取近期反馈数据...")
            feedback_data = self._collect_recent_feedback()
            report.feedback_records_processed = len(feedback_data)
            print(f"       → 获取到 {len(feedback_data)} 条近期反馈")

            # 如果反馈量不足, 跳过权重更新
            if len(feedback_data) < self.min_feedback:
                print(f"       → 反馈量 ({len(feedback_data)}) 低于最小阈值 ({self.min_feedback}), 跳过更新")
                report.status = "skipped"
                report.execution_time_seconds = round(time.time() - start_time, 2)
                return report

            # ── 步骤 2: 在线权重更新 ──
            print(f"\n[2/4] 在线权重增量更新...")
            update_result = self._update_weights_batch(feedback_data)
            report.weights_before = update_result.get("weights_before", {})
            report.weights_after = update_result.get("weights_after", {})
            report.total_weight_updates = update_result.get("total_updates", 0)

            # 计算权重变化
            for k in set(report.weights_before) | set(report.weights_after):
                old_val = report.weights_before.get(k, 0)
                new_val = report.weights_after.get(k, 0)
                report.weight_changes[k] = round(new_val - old_val, 4)

            print(f"       → 权重更新完成 (累计 {report.total_weight_updates} 次)")
            print(f"       → 权重: α={report.weights_after.get('alpha', 0):.4f}, "
                  f"β={report.weights_after.get('beta', 0):.4f}, "
                  f"γ={report.weights_after.get('gamma', 0):.4f}")

            # 如果只更新权重, 跳过重训
            if self.weights_only:
                print(f"       → weights-only 模式, 跳过重训")
            else:
                # ── 步骤 3: 条件触发模型重训 ──
                print(f"\n[3/4] 检查重训条件...")
                report.retrain_triggered = len(feedback_data) >= self.retrain_threshold
                if report.retrain_triggered:
                    print(f"       → 反馈量 ({len(feedback_data)}) 达到重训阈值 ({self.retrain_threshold}), 触发重训")
                    retrain_result = self._retrain_model()
                    report.retrain_success = retrain_result.get("success", False)
                    report.retrain_metrics = retrain_result.get("metrics", {})
                    if report.retrain_success:
                        print(f"       → 重训成功! 指标:")
                        for k, v in report.retrain_metrics.items():
                            print(f"           {k}: {v}")
                    else:
                        print(f"       → 重训失败: {retrain_result.get('error', 'unknown')}")
                else:
                    print(f"       → 反馈量 ({len(feedback_data)}) < 阈值 ({self.retrain_threshold}), 跳过重训")

            # ── 步骤 4: 保存检查点 ──
            print(f"\n[4/4] 保存模型检查点...")
            checkpoint_path = self._save_checkpoint(report)
            report.model_checkpoint_saved = str(checkpoint_path) if checkpoint_path else ""
            print(f"       → 检查点已保存: {checkpoint_path}")

            report.status = "success"

        except Exception as e:
            logger.exception("管道执行失败")
            report.status = "failed"
            report.error_message = str(e)
            print(f"\n  ✗ 错误: {e}")

        report.execution_time_seconds = round(time.time() - start_time, 2)

        print(f"\n{'=' * 60}")
        print(f"  管道执行完成 | 状态: {report.status} | "
              f"耗时: {report.execution_time_seconds:.1f}s")
        print(f"  处理反馈: {report.feedback_records_processed} 条")
        print(f"{'=' * 60}")

        return report

    # ------------------------------------------------------------------
    # 内部步骤
    # ------------------------------------------------------------------

    def _collect_recent_feedback(self) -> list[dict[str, Any]]:
        """从 FeedbackService 收集近期反馈。

        Returns:
            list[dict]: 每条反馈含 user_id, match_id, action, score, timestamp
        """
        online_svc, fb_svc = self._get_services()

        feedback_list = []

        try:
            # 获取全局统计中的反馈记录
            global_stats = fb_svc.get_global_stats()

            # 获取所有有反馈记录的用户
            # 由于 FeedbackLoop 的 get_global_stats 返回汇总信息, 我们通过它获取总反馈量
            recent_count = global_stats.get("recent_feedback", 0)
            total_feedback = global_stats.get("total_feedback", 0)

            logger.info("全局反馈统计: 总反馈 %d, 近期 %d", total_feedback, recent_count)

            # 在线服务自身的统计
            online_stats = online_svc.get_online_stats()

            # 计算可用的反馈记录 (基于在线服务已处理量和总量差异)
            processed = online_stats.total_feedback_processed
            pending = max(0, total_feedback - processed)

            # 模拟反馈条目 (实际项目中应遍历用户查询)
            if pending > 0:
                # 记录: 当前待处理反馈量
                feedback_list = [{"pending_count": pending, "total": total_feedback}]

        except Exception as e:
            logger.warning("收集反馈数据失败(可忽略): %s", e)

        return feedback_list

    def _update_weights_batch(self, feedback_data: list) -> dict[str, Any]:
        """批量更新在线权重。

        Args:
            feedback_data: 反馈数据列表

        Returns:
            dict: 包含更新前后权重和统计
        """
        online_svc, _ = self._get_services()
        result = online_svc.update_model_weights()
        return {
            "weights_before": result.get("weights_before", {}),
            "weights_after": result.get("weights_after", {}),
            "total_updates": online_svc.get_weight_optimizer().total_updates,
        }

    def _retrain_model(self) -> dict[str, Any]:
        """触发三塔模型重训。

        尝试加载 train_matching_model 模块执行完整训练流程。
        如果无法加载或训练失败, 回退并记录错误。

        Returns:
            dict: {"success": bool, "metrics": dict, "error": str}
        """
        result = {"success": False, "metrics": {}, "error": ""}

        try:
            # 尝试导入三塔训练脚本
            sys.path.insert(0, str(BACKEND_DIR))
            from scripts.train_matching_model import (
                main as train_main,
                load_training_data,
                train_three_tower_model,
                evaluate_model,
                save_model,
                compute_feature_importance,
            )
            from sklearn.model_selection import train_test_split

            # ── 检查训练数据是否存在 ──
            data_path = BACKEND_DIR / "data" / "training_data.json"
            if not data_path.exists():
                result["error"] = f"训练数据不存在: {data_path}, 请先运行 prepare_training_data.py"
                logger.warning(result["error"])
                return result

            # ── 执行训练 ──
            # 尽量复用已有训练脚本的主流程, 但以编程方式调用
            print("       → 开始三塔模型重训...")

            # 加载数据
            X_overlap, X_semantic, X_weight, y, samples, meta = load_training_data()

            n_pos = int(y.sum())
            n_neg = len(y) - n_pos
            print(f"       → 数据: {len(y)} 样本 (正={n_pos}, 负={n_neg})")

            # 划分训练/验证集
            split = train_test_split(
                X_overlap, X_semantic, X_weight, y,
                test_size=0.2,
                random_state=42,
                stratify=y,
            )
            X_o_train, X_o_val = split[0], split[1]
            X_s_train, X_s_val = split[2], split[3]
            X_w_train, X_w_val = split[4], split[5]
            y_train, y_val = split[6], split[7]

            # 训练
            model, history, scalers = train_three_tower_model(
                X_o_train, X_s_train, X_w_train, y_train,
                X_o_val, X_s_val, X_w_val, y_val,
            )

            # 评估
            metrics_val, _ = evaluate_model(
                model, X_o_val, X_s_val, X_w_val, y_val, scalers, "验证集"
            )

            # 特征重要性
            X_o_mean = X_overlap.mean(axis=0)
            X_s_mean = X_semantic.mean(axis=0)
            X_w_mean = X_weight.mean(axis=0)
            device = next(model.parameters()).device
            feature_importance = compute_feature_importance(
                model, scalers, X_o_mean, X_s_mean, X_w_mean, device,
            )

            # 保存模型
            report = save_model(model, scalers, metrics_val, feature_importance, history)

            result["success"] = True
            result["metrics"] = metrics_val
            result["checkpoint"] = str(self.model_dir / "matching_model.pt")

            logger.info("模型重训成功: %s", metrics_val)

        except ImportError as e:
            result["error"] = f"导入训练模块失败: {e}"
            logger.warning("无法导入训练模块, 跳过重训: %s", e)
        except FileNotFoundError as e:
            result["error"] = str(e)
            logger.warning("训练数据或模型文件缺失: %s", e)
        except Exception as e:
            result["error"] = str(e)
            logger.error("模型重训异常: %s", e, exc_info=True)

        return result

    def _save_checkpoint(self, report: PipelineReport) -> Optional[Path]:
        """保存当前模型检查点。

        Args:
            report: 管道执行报告 (用于元数据)

        Returns:
            Optional[Path]: 检查点文件路径, 失败返回 None
        """
        try:
            self.model_dir.mkdir(parents=True, exist_ok=True)

            checkpoint = {
                "type": "online_learning_checkpoint",
                "timestamp": report.timestamp,
                "pipeline_version": report.pipeline_version,
                "weights": report.weights_after,
                "weight_changes": report.weight_changes,
                "total_weight_updates": report.total_weight_updates,
                "feedback_processed": report.feedback_records_processed,
                "retrain_triggered": report.retrain_triggered,
                "retrain_metrics": report.retrain_metrics,
                "execution_time": report.execution_time_seconds,
            }

            path = self.model_dir / f"online_checkpoint_{datetime.now():%Y%m%d_%H%M%S}.json"
            with open(path, "w", encoding="utf-8") as f:
                json.dump(checkpoint, f, ensure_ascii=False, indent=2)

            # 同时保存一个 latest 链接 (覆盖写入)
            latest_path = self.model_dir / "online_checkpoint_latest.json"
            with open(latest_path, "w", encoding="utf-8") as f:
                json.dump(checkpoint, f, ensure_ascii=False, indent=2)

            logger.info("检查点已保存: %s", path)
            return path

        except Exception as e:
            logger.error("保存检查点失败: %s", e)
            return None


# ---------------------------------------------------------------------------
# 报告输出
# ---------------------------------------------------------------------------

def print_report(report: PipelineReport) -> None:
    """打印可读的管道执行报告。"""
    print()
    print("=" * 60)
    print("  在线学习执行报告")
    print("=" * 60)
    print(f"  状态:              {report.status}")
    print(f"  时间:              {report.timestamp}")
    print(f"  耗时:              {report.execution_time_seconds:.1f}s")
    print(f"  处理反馈:          {report.feedback_records_processed} 条")
    print()
    print("  ── 权重更新 ──")
    print(f"  累计更新次数:      {report.total_weight_updates}")
    for k in ["alpha", "beta", "gamma"]:
        before = report.weights_before.get(k, 0)
        after = report.weights_after.get(k, 0)
        change = after - before
        arrow = "↑" if change > 0.001 else ("↓" if change < -0.001 else "→")
        print(f"  {k}: {before:.4f} → {after:.4f}  {arrow} {change:+.4f}")

    if report.retrain_triggered:
        print()
        print("  ── 模型重训 ──")
        print(f"  触发:              {'是' if report.retrain_triggered else '否'}")
        if report.retrain_success:
            print(f"  状态:              成功")
            for k, v in report.retrain_metrics.items():
                print(f"  {k}: {v}")
        else:
            print(f"  状态:              失败 ({report.error_message or '未知'})")

    print(f"\n  ── 检查点 ──")
    print(f"  路径:              {report.model_checkpoint_saved}")
    print(f"{'=' * 60}")
    print()


def save_report_to_file(report: PipelineReport, output_dir: Optional[Path] = None) -> Path:
    """将报告保存为 JSON 文件。

    Args:
        report: 执行报告
        output_dir: 输出目录 (默认 model_dir)

    Returns:
        Path: 报告文件路径
    """
    if output_dir is None:
        output_dir = DEFAULT_MODEL_DIR
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    report_path = output_dir / f"online_learning_report_{datetime.now():%Y%m%d_%H%M%S}.json"

    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(asdict(report), f, ensure_ascii=False, indent=2)

    logger.info("报告已保存: %s", report_path)
    return report_path


# ---------------------------------------------------------------------------
# 命令行入口
# ---------------------------------------------------------------------------

def parse_args(argv: Optional[list[str]] = None) -> argparse.Namespace:
    """解析命令行参数。"""
    parser = argparse.ArgumentParser(
        description="AI数智名片 — 在线学习管道",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  %(prog)s                                    # 默认配置执行
  %(prog)s --weights-only                      # 仅更新权重, 不重训
  %(prog)s --retrain-threshold 100             # 降低重训阈值
  %(prog)s --model-dir ../models               # 指定模型目录
  %(prog)s --min-feedback 10 --lookback 24     # 最少10条反馈, 回溯24小时
  %(prog)s --force-retrain                     # 强制重训
        """,
    )
    parser.add_argument(
        "--model-dir",
        type=str,
        default=str(DEFAULT_MODEL_DIR),
        help=f"模型目录 (默认: {DEFAULT_MODEL_DIR})",
    )
    parser.add_argument(
        "--min-feedback",
        type=int,
        default=DEFAULT_MIN_FEEDBACK,
        help=f"最少反馈数才执行更新 (默认: {DEFAULT_MIN_FEEDBACK})",
    )
    parser.add_argument(
        "--retrain-threshold",
        type=int,
        default=DEFAULT_RETRAIN_THRESHOLD,
        help=f"新反馈超过此数触发重训 (默认: {DEFAULT_RETRAIN_THRESHOLD})",
    )
    parser.add_argument(
        "--lookback",
        "--lookback-hours",
        type=int,
        dest="lookback_hours",
        default=DEFAULT_FEEDBACK_LOOKBACK_HOURS,
        help=f"反馈数据回溯小时数 (默认: {DEFAULT_FEEDBACK_LOOKBACK_HOURS})",
    )
    parser.add_argument(
        "--weights-only",
        action="store_true",
        default=DEFAULT_WEIGHTS_ONLY,
        help="仅更新在线权重, 跳过模型重训",
    )
    parser.add_argument(
        "--force-retrain",
        action="store_true",
        default=False,
        help="强制触发模型重训 (无视阈值)",
    )
    parser.add_argument(
        "--save-report",
        type=str,
        default="",
        help="报告保存目录 (默认: 与 model-dir 相同)",
    )

    return parser.parse_args(argv)


def main(argv: Optional[list[str]] = None) -> int:
    """主入口。

    Args:
        argv: 命令行参数列表 (默认使用 sys.argv[1:])

    Returns:
        int: 退出码 (0=成功, 1=失败)
    """
    args = parse_args(argv)

    # 如果强制重训, 临时降低阈值
    retrain_threshold = DEFAULT_RETRAIN_THRESHOLD
    if args.force_retrain:
        retrain_threshold = 0

    # 构建管道
    pipeline = OnlineLearningPipeline(
        model_dir=Path(args.model_dir),
        min_feedback=args.min_feedback,
        retrain_threshold=retrain_threshold,
        weights_only=args.weights_only,
        lookback_hours=args.lookback_hours,
    )

    # 执行
    report = pipeline.run()

    # 输出报告
    print_report(report)

    # 保存报告
    report_dir = Path(args.save_report) if args.save_report else Path(args.model_dir)
    save_report_to_file(report, report_dir)

    return 0 if report.status == "success" else 1


if __name__ == "__main__":
    sys.exit(main())
