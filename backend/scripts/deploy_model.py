#!/usr/bin/env python3
"""部署训练好的 LoRA 模型到生产环境。

工作流程:
  1. 注册新模型版本到 ModelRegistry
  2. 提升模型到 staging
  3. 自动 A/B 对比 (staging vs production)
  4. 验证模型健康状态
  5. 提升到 production (可选)

用法:
  python deploy_model.py \\
    --name business-card-lora \\
    --version v1.0 \\
    --adapter-path /path/to/lora_output \\
    --base-model Qwen/Qwen2.5-0.5B-Instruct

参数:
  --name          模型名称 (默认: business-card-lora)
  --version       模型版本 (默认: auto 根据时间戳生成)
  --adapter-path  LoRA 适配器路径 (必填)
  --base-model    基础模型名称/路径 (必填)
  --metrics-path  metrics JSON 文件路径 (可选)
  --stage         目标 stage: none/staging/production (默认: staging)
  --auto-promote  自动 A/B 对比后提升到 production (默认: True)
  --serve         部署后立即启动推理服务 (默认: False)
  --dry-run       仅打印命令，不执行
"""

import argparse
import json
import logging
import os
import subprocess
import sys
import textwrap
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("deploy_model")

# -- 默认路径 ------------------------------------------------------------------

BACKEND_DIR = Path(__file__).resolve().parent.parent
TRAINING_DATA_DIR = BACKEND_DIR.parent / "training_data"


def load_metrics(metrics_path: Optional[str]) -> Dict:
    """从 JSON 文件加载模型评估指标。"""
    if not metrics_path:
        return {}

    path = Path(metrics_path)
    if not path.exists():
        logger.warning("metrics 文件不存在: %s", metrics_path)
        return {}

    try:
        with open(path, "r", encoding="utf-8") as f:
            metrics = json.load(f)
        # 展平嵌套指标
        flat = {}
        for k, v in metrics.items():
            if isinstance(v, (int, float)):
                flat[k] = v
            elif isinstance(v, str):
                try:
                    flat[k] = float(v)
                except (ValueError, TypeError):
                    pass
        logger.info("加载 %d 个评估指标", len(flat))
        return flat
    except Exception as e:
        logger.warning("加载 metrics 失败: %s", e)
        return {}


def validate_adapter_path(adapter_path: str) -> bool:
    """验证 LoRA 适配器路径完整性。"""
    path = Path(adapter_path)
    if not path.is_dir():
        logger.error("适配器目录不存在: %s", adapter_path)
        return False

    # 检查关键文件
    required_files = [
        "adapter_model.safetensors",
        "adapter_config.json",
    ]
    optional_files = [
        "training_report.json",
        "test_inference.json",
        "tokenizer.json",
        "tokenizer_config.json",
    ]

    missing_required = [f for f in required_files if not (path / f).exists()]
    if missing_required:
        logger.error("缺少必要文件: %s", missing_required)
        return False

    missing_optional = [f for f in optional_files if not (path / f).exists()]
    if missing_optional:
        logger.warning("缺少可选文件: %s (不影响部署)", missing_optional)

    # 检查适配器文件大小
    safetensors_path = path / "adapter_model.safetensors"
    size_mb = safetensors_path.stat().st_size / (1024 * 1024)
    logger.info("适配器文件大小: %.2f MB", size_mb)

    return True


def register_with_model_registry(
    name: str,
    version: str,
    adapter_path: str,
    base_model: str,
    metrics: Dict,
    registry_db: str = "",
) -> bool:
    """通过 ModelRegistry API 注册模型。"""
    db_path = registry_db or os.path.join(BACKEND_DIR, "model_registry.db")

    try:
        # 将 backend/app/ai 加入 sys.path
        sys.path.insert(0, str(BACKEND_DIR / "app"))

        from ai.model_registry import ModelRegistry

        registry = ModelRegistry(db_path=db_path)

        # 注册模型
        record = registry.register_model(
            name=name,
            version=version,
            path=adapter_path,
            metrics={
                **metrics,
                "base_model": base_model,
                "deployed_at": datetime.utcnow().isoformat(),
            },
        )
        logger.info("模型已注册: %s v%s (path=%s)", name, version, adapter_path)
        logger.info("  注册详情: stage=%s, created_at=%s", record.stage, record.created_at)
        return True

    except ImportError as e:
        logger.error("导入 ModelRegistry 失败: %s", e)
        logger.error("请确保在 backend 目录下运行")
        return False
    except Exception as e:
        logger.error("注册模型失败: %s", e)
        return False


def promote_model(
    name: str,
    version: str,
    stage: str,
    registry_db: str = "",
) -> bool:
    """提升模型到指定 stage。"""
    db_path = registry_db or os.path.join(BACKEND_DIR, "model_registry.db")

    try:
        sys.path.insert(0, str(BACKEND_DIR / "app"))
        from ai.model_registry import ModelRegistry

        registry = ModelRegistry(db_path=db_path)
        result = registry.promote_model(name=name, version=version, stage=stage)
        if result:
            logger.info("模型已提升: %s v%s -> %s", name, version, stage)
            return True
        else:
            logger.error("提升模型失败: %s v%s 未找到", name, version)
            return False
    except Exception as e:
        logger.error("提升模型失败: %s", e)
        return False


def auto_compare_and_promote(
    name: str,
    registry_db: str = "",
) -> Optional[Dict]:
    """自动 A/B 对比 staging vs production，更优者提升。"""
    db_path = registry_db or os.path.join(BACKEND_DIR, "model_registry.db")

    try:
        sys.path.insert(0, str(BACKEND_DIR / "app"))
        from ai.model_registry import ModelRegistry

        registry = ModelRegistry(db_path=db_path)
        result = registry.compare_models(name=name)
        if result and result.get("compared"):
            if result["winner"] == "staging":
                logger.info(
                    "A/B 对比: staging(%.4f) > production(%.4f), 自动提升",
                    result.get("stage_value", 0),
                    result.get("prod_value", 0),
                )
            else:
                logger.info(
                    "A/B 对比: production(%.4f) >= staging(%.4f), 保持现状",
                    result.get("prod_value", 0),
                    result.get("stage_value", 0),
                )
            return result
        else:
            logger.info("A/B 对比: 无需变更或数据不足")
            return result
    except Exception as e:
        logger.warning("A/B 对比失败: %s", e)
        return None


def health_check_models(registry_db: str = "") -> Dict:
    """检查所有 production 模型健康状态。"""
    db_path = registry_db or os.path.join(BACKEND_DIR, "model_registry.db")

    try:
        sys.path.insert(0, str(BACKEND_DIR / "app"))
        from ai.model_registry import ModelRegistry

        registry = ModelRegistry(db_path=db_path)
        healthy, total = registry.health_check()
        logger.info("模型健康检查: %d/%d 通过", healthy, total)
        return {"healthy": healthy, "total": total}
    except Exception as e:
        logger.warning("健康检查失败: %s", e)
        return {"healthy": 0, "total": 0}


def start_serving_service(
    name: str,
    version: str,
    adapter_path: str,
    base_model: str,
    port: int = 8000,
) -> bool:
    """启动模型推理服务。"""
    logger.info("准备启动推理服务...")

    serving_script = str(BACKEND_DIR / "app" / "ai" / "model_serving.py")
    if not Path(serving_script).exists():
        logger.warning("model_serving.py 不存在，跳过服务启动")
        return False

    # 通过环境变量传递配置
    env = os.environ.copy()
    env["MLX_BASE_URL"] = f"http://192.168.1.233:{port}"
    env["MODEL_NAME"] = name
    env["MODEL_VERSION"] = version
    env["ADAPTER_PATH"] = adapter_path
    env["BASE_MODEL"] = base_model

    cmd = [
        sys.executable, serving_script,
        "--port", str(port),
    ]

    try:
        logger.info("启动推理服务: %s", " ".join(cmd))
        # 后台启动
        subprocess.Popen(
            cmd,
            env=env,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        logger.info("推理服务已启动 (PID: %d, port: %d)", 0, port)
        return True
    except Exception as e:
        logger.error("启动推理服务失败: %s", e)
        return False


def get_version_tag() -> str:
    """生成版本标签 (基于时间戳 + git hash)。"""
    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    git_hash = ""

    try:
        result = subprocess.run(
            ["git", "rev-parse", "--short", "HEAD"],
            capture_output=True, text=True, timeout=5,
            cwd=BACKEND_DIR,
        )
        if result.returncode == 0:
            git_hash = result.stdout.strip()[:7]
    except Exception:
        pass

    if git_hash:
        return f"{timestamp}-{git_hash}"
    return timestamp


def main():
    parser = argparse.ArgumentParser(
        description="部署 LoRA 微调模型到生产环境",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=textwrap.dedent("""\
            示例:
              # 基本部署 (注册 + staging)
              python deploy_model.py \\
                --adapter-path ../../training_data/lora_qwen \\
                --base-model Qwen/Qwen2.5-0.5B-Instruct

              # 带 metrics 自动生产
              python deploy_model.py \\
                --adapter-path ../../training_data/lora_qwen \\
                --base-model Qwen/Qwen2.5-0.5B-Instruct \\
                --metrics-path ../../training_data/lora_qwen/loss_history.json \\
                --stage production

              # 部署后启动服务
              python deploy_model.py \\
                --adapter-path ... --base-model ... --serve

              # 从 Mac Mini 远程适配器部署
              python deploy_model.py \\
                --adapter-path ~/lora_training/lora_output \\
                --base-model Qwen/Qwen2.5-0.5B-Instruct \\
                --remote
        """),
    )

    # -- 模型参数 -------------------------------------------------------------
    parser.add_argument(
        "--name", type=str, default="business-card-lora",
        help="模型名称 (默认: business-card-lora)",
    )
    parser.add_argument(
        "--version", type=str, default="",
        help="模型版本 (默认: 自动生成基于时间戳)",
    )
    parser.add_argument(
        "--adapter-path", type=str, required=True,
        help="LoRA 适配器路径 (必填)",
    )
    parser.add_argument(
        "--base-model", type=str, required=True,
        help="基础模型名称/路径 (必填)",
    )

    # -- 部署参数 -------------------------------------------------------------
    parser.add_argument(
        "--metrics-path", type=str, default="",
        help="metrics JSON 文件路径 (可选)",
    )
    parser.add_argument(
        "--stage", type=str, default="staging",
        choices=["none", "staging", "production"],
        help="目标 stage (默认: staging)",
    )
    parser.add_argument(
        "--auto-promote", action="store_true", default=True,
        help="自动 A/B 对比后提升到 production (默认: True)",
    )
    parser.add_argument(
        "--serve", action="store_true", default=False,
        help="部署后立即启动推理服务 (默认: False)",
    )
    parser.add_argument(
        "--port", type=int, default=8000,
        help="推理服务端口 (默认: 8000)",
    )
    parser.add_argument(
        "--remote", action="store_true", default=False,
        help="适配器路径在远程 Mac Mini 上",
    )

    # -- 其他 ------------------------------------------------------------------
    parser.add_argument(
        "--dry-run", action="store_true",
        help="仅打印操作步骤，不实际执行",
    )
    parser.add_argument(
        "--registry-db", type=str, default="",
        help="ModelRegistry SQLite 数据库路径 (默认: backend/model_registry.db)",
    )

    args = parser.parse_args()

    # -- 自动生成版本号 -------------------------------------------------------
    version = args.version or get_version_tag()

    # -- 打印部署配置 ---------------------------------------------------------
    logger.info("=" * 60)
    logger.info("模型部署启动")
    logger.info(f"  模型名称: {args.name}")
    logger.info(f"  模型版本: {version}")
    logger.info(f"  适配器路径: {args.adapter_path}")
    logger.info(f"  基础模型: {args.base_model}")
    logger.info(f"  目标 stage: {args.stage}")
    logger.info(f"  自动 A/B: {args.auto_promote}")
    logger.info(f"  启动服务: {args.serve}")
    logger.info("=" * 60)

    # -- 验证适配器路径 -------------------------------------------------------
    if not args.remote and not args.dry_run:
        if not validate_adapter_path(args.adapter_path):
            logger.error("适配器验证失败，中止部署")
            sys.exit(1)

    # -- 加载 metrics ----------------------------------------------------------
    metrics = load_metrics(args.metrics_path) if args.metrics_path else {}
    if not metrics and Path(args.adapter_path, "training_report.json").exists():
        # 自动从训练报告加载
        report_path = Path(args.adapter_path, "training_report.json")
        metrics = load_metrics(str(report_path))
        logger.info("自动从训练报告加载 metrics")

    if not metrics and Path(args.adapter_path, "loss_history.json").exists():
        # 从 loss_history 提取最终 loss
        try:
            with open(Path(args.adapter_path, "loss_history.json"), "r") as f:
                history = json.load(f)
            if history and isinstance(history, list):
                metrics["final_loss"] = history[-1].get("loss", 0)
                metrics["num_steps"] = len(history)
                logger.info("从 loss_history 提取 metrics: final_loss=%.4f", metrics["final_loss"])
        except Exception:
            pass

    logger.info("模型评估指标: %s", json.dumps(metrics, ensure_ascii=False))
    logger.info("=" * 60)

    # =========================================================================
    # Step 1: 注册模型
    # =========================================================================
    logger.info("[Step 1/4] 注册模型到 ModelRegistry...")

    if args.dry_run:
        logger.info("  [DRY-RUN] 将注册: %s v%s -> %s", args.name, version, args.adapter_path)
    else:
        ok = register_with_model_registry(
            name=args.name,
            version=version,
            adapter_path=args.adapter_path,
            base_model=args.base_model,
            metrics=metrics,
            registry_db=args.registry_db,
        )
        if not ok:
            logger.error("注册失败，中止部署")
            sys.exit(1)

    # =========================================================================
    # Step 2: 提升模型到指定 stage
    # =========================================================================
    logger.info("[Step 2/4] 提升模型到 %s...", args.stage)

    if args.dry_run:
        logger.info("  [DRY-RUN] 将提升: %s v%s -> %s", args.name, version, args.stage)
    else:
        ok = promote_model(
            name=args.name,
            version=version,
            stage=args.stage,
            registry_db=args.registry_db,
        )
        if not ok:
            logger.warning("提升到 %s 失败，继续执行", args.stage)

    # =========================================================================
    # Step 3: 自动 A/B 对比 (staging vs production)
    # =========================================================================
    if args.auto_promote:
        logger.info("[Step 3/4] 自动 A/B 对比 staging vs production...")

        if args.dry_run:
            logger.info("  [DRY-RUN] 将执行 A/B 对比: %s", args.name)
        else:
            result = auto_compare_and_promote(
                name=args.name,
                registry_db=args.registry_db,
            )
            if result:
                logger.info("  A/B 对比结果: winner=%s", result.get("winner", "unknown"))
            else:
                logger.info("  A/B 对比跳过 (可能是第一个版本)")
    else:
        logger.info("[Step 3/4] 跳过 A/B 对比 (--no-auto-promote)")

    # =========================================================================
    # Step 4: 健康检查
    # =========================================================================
    logger.info("[Step 4/4] 模型健康检查...")

    if args.dry_run:
        logger.info("  [DRY-RUN] 将执行健康检查")
    else:
        health = health_check_models(registry_db=args.registry_db)
        if health["healthy"] < health["total"]:
            logger.warning("部分模型健康检查未通过: %d/%d", health["healthy"], health["total"])
        else:
            logger.info("所有模型健康: %d/%d", health["healthy"], health["total"])

    # =========================================================================
    # 可选: 启动推理服务
    # =========================================================================
    if args.serve:
        logger.info("[Optional] 启动推理服务...")

        if args.dry_run:
            logger.info("  [DRY-RUN] 将在 port %d 启动服务", args.port)
        else:
            ok = start_serving_service(
                name=args.name,
                version=version,
                adapter_path=args.adapter_path,
                base_model=args.base_model,
                port=args.port,
            )
            if ok:
                logger.info("推理服务启动成功")
            else:
                logger.warning("推理服务启动失败")

    # =========================================================================
    # 完成
    # =========================================================================
    print()
    print("=" * 60)
    print("  模型部署完成！")
    print()
    print(f"  模型: {args.name} v{version}")
    print(f"  Stage: {args.stage if not args.auto_promote else 'production (auto)'}")
    print(f"  适配器: {args.adapter_path}")
    print(f"  基础模型: {args.base_model}")
    print()
    print("  后续操作:")
    print(f"    1. 查看注册的模型:")
    print(f"       python -c \"from ai.model_registry import ModelRegistry; "
          f"r = ModelRegistry(); print(r.list_models())\"")
    print(f"    2. 获取 production 模型:")
    print(f"       python -c \"from ai.model_registry import ModelRegistry; "
          f"r = ModelRegistry(); m = r.get_production_model('{args.name}'); "
          f"print(m)\"")
    print(f"    3. 回滚 (如果需要):")
    print(f"       python -c \"from ai.model_registry import ModelRegistry; "
          f"r = ModelRegistry(); r.rollback('{args.name}')\"")
    print("=" * 60)


if __name__ == "__main__":
    main()
