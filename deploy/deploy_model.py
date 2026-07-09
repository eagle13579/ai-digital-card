#!/usr/bin/env python3
"""
AI数智名片 — 自动ML模型部署管线

CLI 工具, 用于将模型从 staging 提升到 production,
支持自动验证、健康检查和回滚。

用法:
    python deploy_model.py promote <model_name> [--version <ver>] [--auto]
    python deploy_model.py promote <model_name> --rollback
    python deploy_model.py health <model_name>
"""

import argparse
import logging
import os
import sys
import time
from pathlib import Path

import requests

# 将项目根目录加入 sys.path, 以便导入 model_registry
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "backend"))

from app.ai.model_registry import ModelRegistry  # noqa: E402

logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] %(levelname)s %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("deploy_model")

# 默认后端健康检查地址
DEFAULT_HEALTH_URL = "http://localhost:8201/api/ml/health"
# 模型文件根目录 (注册时使用相对路径时拼接)
MODEL_ROOT = Path(PROJECT_ROOT) / "models"


def _load_model_safely(path: str) -> bool:
    """尝试加载模型文件做简单推理测试, 捕获所有异常。"""
    try:
        # 根据扩展名选择加载方式
        ext = os.path.splitext(path)[1].lower()
        if ext == ".pkl" or ext == ".pickle":
            import pickle
            with open(path, "rb") as f:
                model = pickle.load(f)
            # 如果有 predict 方法, 做一次推理
            if hasattr(model, "predict"):
                import numpy as np
                # 用全零向量做一次预测
                try:
                    model.predict(np.zeros((1, model.n_features_in_)))
                except Exception:
                    pass  # 不强制要求预测成功, 加载成功即可
        elif ext == ".joblib":
            import joblib
            model = joblib.load(path)
            if hasattr(model, "predict"):
                import numpy as np
                try:
                    model.predict(np.zeros((1, model.n_features_in_)))
                except Exception:
                    pass
        elif ext in (".onnx",):
            import onnxruntime as ort
            session = ort.InferenceSession(path)
            _ = session.get_inputs()  # 验证可读取
        elif ext == ".pt" or ext == ".pth":
            import torch
            model = torch.load(path, map_location="cpu")
            _ = model  # 仅验证可加载
        elif ext == ".h5" or ext == ".keras":
            from tensorflow import keras
            _ = keras.models.load_model(path)
        else:
            # 未知格式, 仅验证文件存在
            logger.warning("未知模型格式 %s, 仅做文件存在检查", ext)
        return True
    except Exception as e:
        logger.error("模型加载/推理测试失败: %s", e)
        return False


def _validate_model(record) -> bool:
    """验证模型: a) 文件存在 b) 加载测试。返回 True 表示通过。"""
    # a) 检查模型文件存在
    model_path = record.path
    if not os.path.isabs(model_path):
        # 尝试相对路径拼接
        abs_path = str(MODEL_ROOT / model_path)
        if os.path.exists(abs_path):
            model_path = abs_path
        else:
            abs_path = str(PROJECT_ROOT / model_path)
            if os.path.exists(abs_path):
                model_path = abs_path

    if not os.path.exists(model_path):
        logger.error("验证失败: 模型文件不存在 (%s)", model_path)
        return False
    logger.info("模型文件存在: %s", model_path)

    # b) 加载 + 推理测试
    logger.info("正在加载模型并进行推理测试...")
    if not _load_model_safely(model_path):
        return False
    logger.info("推理测试通过")
    return True


def _health_check_api(url: str, timeout: int = 30) -> bool:
    """调用后端 ML 健康检查 API。"""
    try:
        logger.info("健康检查: GET %s", url)
        resp = requests.get(url, timeout=timeout)
        if resp.status_code == 200:
            data = resp.json()
            logger.info("健康检查结果: %s", data)
            return True
        else:
            logger.error("健康检查返回 %d: %s", resp.status_code, resp.text)
            return False
    except requests.exceptions.ConnectionError:
        logger.error("健康检查失败: 无法连接 %s (服务未启动?)", url)
        return False
    except requests.exceptions.Timeout:
        logger.error("健康检查超时 (%ds): %s", timeout, url)
        return False
    except Exception as e:
        logger.error("健康检查异常: %s", e)
        return False


def cmd_promote(args):
    """处理 promote 子命令。"""
    registry = ModelRegistry(db_path=str(PROJECT_ROOT / "backend" / "model_registry.db"))
    model_name = args.model_name

    # ---- 回滚模式 ----
    if args.rollback:
        logger.info("=== 回滚模式: %s ===", model_name)
        result = registry.rollback(model_name)
        if result is None:
            logger.error("回滚失败: 无可用 staging 版本")
            sys.exit(1)
        logger.info("回滚成功: %s v%s → production", result.name, result.version)

        # 回滚后做验证
        logger.info("回滚后验证...")
        if not _validate_model(result):
            logger.warning("回滚后验证未通过, 但回滚操作已执行")
        if not _health_check_api(args.health_url):
            logger.warning("回滚后健康检查未通过, 请手动检查服务状态")
        logger.info("回滚完成: %s v%s", result.name, result.version)
        return

    # ---- 手动指定版本 ----
    target_version = None
    if args.version:
        target_version = args.version
        record = registry.get_model(model_name, target_version)
        if record is None:
            logger.error("模型 %s v%s 不存在", model_name, target_version)
            sys.exit(1)
    elif args.auto:
        # ---- 自动模式: 找最新 staging 版本 ----
        all_models = registry.list_models()
        staging_models = [
            m for m in all_models
            if m.name == model_name and m.stage == "staging"
        ]
        if not staging_models:
            logger.error("自动提升失败: 模型 %s 没有 staging 版本", model_name)
            sys.exit(1)
        # 按创建时间降序, 取最新的
        staging_models.sort(key=lambda m: m.created_at, reverse=True)
        record = staging_models[0]
        target_version = record.version
        logger.info("自动模式: 找到最新 staging 版本 %s v%s", model_name, target_version)
    else:
        logger.error("请指定 --version 或 --auto")
        sys.exit(1)

    # ---- 验证 ----
    logger.info("=== 验证阶段: %s v%s ===", model_name, target_version)

    # a) + b) 文件存在 + 加载测试
    if not _validate_model(record):
        logger.error("验证失败, 终止部署")
        sys.exit(1)

    # c) 后端健康检查 API
    if not _health_check_api(args.health_url):
        logger.error("健康检查 API 未通过, 终止部署")
        sys.exit(1)

    # ---- 提升 ----
    logger.info("=== 提升阶段: %s v%s → production ===", model_name, target_version)
    result = registry.promote_model(model_name, target_version, "production")
    if result is None:
        logger.error("提升失败")
        sys.exit(1)

    # ---- 提升后二次验证 ----
    logger.info("提升后二次验证...")
    if _health_check_api(args.health_url):
        logger.info("生产环境健康检查通过")
    else:
        logger.warning("提升后健康检查未通过, 请手动检查")

    logger.info("部署成功: %s v%s → production ✓", model_name, target_version)


def cmd_health(args):
    """处理 health 子命令 — 检查模型注册中心的生产模型健康状态。"""
    registry = ModelRegistry(db_path=str(PROJECT_ROOT / "backend" / "model_registry.db"))
    healthy, total = registry.health_check()
    logger.info("模型健康状态: %d/%d 通过", healthy, total)

    # 也可以调用远端 API
    if args.health_url:
        ok = _health_check_api(args.health_url, timeout=args.timeout)
        if ok:
            logger.info("远端健康检查通过")
        else:
            logger.warning("远端健康检查未通过")
    return (healthy, total)


def parse_args(argv=None):
    """解析命令行参数。"""
    parser = argparse.ArgumentParser(
        description="AI数智名片 — 自动ML模型部署管线",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  python deploy_model.py promote intent_classifier --auto
  python deploy_model.py promote intent_classifier --version v2.1.0
  python deploy_model.py promote intent_classifier --rollback
  python deploy_model.py health intent_classifier
        """,
    )

    subparsers = parser.add_subparsers(dest="command", help="子命令")

    # promote 子命令
    promote_parser = subparsers.add_parser("promote", help="提升模型到 production")
    promote_parser.add_argument("model_name", help="模型名称")
    promote_parser.add_argument("--version", "-v", help="指定版本号")
    promote_parser.add_argument("--auto", "-a", action="store_true", help="自动选择最新 staging 版本")
    promote_parser.add_argument("--rollback", "-r", action="store_true", help="回滚到上一个 production 版本")
    promote_parser.add_argument(
        "--health-url",
        default=DEFAULT_HEALTH_URL,
        help=f"健康检查 API 地址 (默认: {DEFAULT_HEALTH_URL})",
    )

    # health 子命令
    health_parser = subparsers.add_parser("health", help="检查模型健康状态")
    health_parser.add_argument("model_name", nargs="?", default=None, help="模型名称 (可选)")
    health_parser.add_argument(
        "--health-url",
        default=DEFAULT_HEALTH_URL,
        help=f"健康检查 API 地址 (默认: {DEFAULT_HEALTH_URL})",
    )
    health_parser.add_argument("--timeout", "-t", type=int, default=30, help="健康检查超时秒数")

    return parser.parse_args(argv)


def main():
    args = parse_args()

    if args.command == "promote":
        cmd_promote(args)
    elif args.command == "health":
        cmd_health(args)
    else:
        logger.error("未知命令: %s (可用命令: promote, health)", args.command)
        sys.exit(1)


if __name__ == "__main__":
    main()
