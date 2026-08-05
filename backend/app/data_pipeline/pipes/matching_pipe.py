"""
P0级 · 名片匹配模型训练管道包装器 (matching_pipe)
==================================================
包装 scripts/train_matching_model_v2.py 为受控管道调用。

职责:
  - 检查 data/online_weights.json 和 data/v2_training_data.json 是否有新数据
  - 调用 scripts/train_matching_model_v2.py 训练
  - 输出训练结果和模型文件路径
  - 包装成 subprocess.run 安全调用（含超时、输出截断、错误捕获）
"""

import os
import sys
import json
import time
import datetime
import logging
import subprocess

logger = logging.getLogger("MatchingPipe")

# ── 路径常量 ──────────────────────────────────────────────────────
BACKEND_DIR = os.path.normpath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
DATA_DIR = os.path.join(BACKEND_DIR, "data")
SCRIPTS_DIR = os.path.join(BACKEND_DIR, "scripts")

ONLINE_WEIGHTS_PATH = os.path.join(DATA_DIR, "online_weights.json")
V2_TRAINING_DATA_PATH = os.path.join(DATA_DIR, "v2_training_data.json")
TRAIN_SCRIPT_PATH = os.path.join(SCRIPTS_DIR, "train_matching_model_v2.py")
MODEL_OUTPUT_PATH = os.path.join(BACKEND_DIR, "models", "matching_model_v2.pt")

# 执行超时 (秒)
TRAIN_TIMEOUT = 600


# ======================================================================
# 就绪检查
# ======================================================================

def check_ready() -> bool:
    """检查数据和依赖是否就绪

    检查项:
      1. 训练脚本是否存在
      2. v2_training_data.json 是否存在且非空
      3. online_weights.json 是否存在（可选依赖，非阻塞）
      4. data/ 目录可写

    Returns:
        bool: 是否就绪
    """
    checks = []

    # 1. 脚本就绪
    script_ok = os.path.isfile(TRAIN_SCRIPT_PATH)
    checks.append(("train_script_exists", script_ok))
    if not script_ok:
        logger.warning("训练脚本不存在: %s", TRAIN_SCRIPT_PATH)

    # 2. 训练数据就绪
    data_ok = os.path.isfile(V2_TRAINING_DATA_PATH)
    if data_ok:
        try:
            with open(V2_TRAINING_DATA_PATH, "r", encoding="utf-8") as f:
                content = json.load(f)
            data_ok = bool(content)  # 非空
        except (json.JSONDecodeError, Exception):
            data_ok = False
    checks.append(("v2_training_data_ready", data_ok))
    if not data_ok:
        logger.warning("V2训练数据缺失或为空: %s", V2_TRAINING_DATA_PATH)

    # 3. 在线权重（可选）
    weights_ok = os.path.isfile(ONLINE_WEIGHTS_PATH)
    if weights_ok:
        logger.info("在线权重文件存在, 将作为训练参考: %s", ONLINE_WEIGHTS_PATH)
    checks.append(("online_weights_optional", weights_ok))

    # 4. 数据目录可写
    data_writable = os.access(DATA_DIR, os.W_OK) if os.path.exists(DATA_DIR) else False
    checks.append(("data_dir_writable", data_writable))

    all_ok = all(ok for name, ok in checks if name != "online_weights_optional")

    if all_ok:
        logger.info("✅ matching_pipe 就绪检查通过 (%d/4)", len(checks))
    else:
        failed = [name for name, ok in checks if not ok and name != "online_weights_optional"]
        logger.warning("⚠️ matching_pipe 就绪检查未通过: %s", failed)

    return all_ok


# ======================================================================
# 管道执行
# ======================================================================

def run_pipeline() -> dict:
    """执行名片匹配模型训练管道

    流程:
      1. check_ready()
      2. 如果就绪, subprocess.run(训练脚本, cwd=BACKEND_DIR)
      3. 捕获输出、超时、错误
      4. 验证模型文件产出

    Returns:
        dict: {
            "status": "success" | "skipped" | "failed" | "exception",
            "model_id": "matching_model_v2",
            "pipeline": "matching_pipe",
            "timestamp": "...",
            ...
        }
    """
    start_time = time.time()
    logger.info("=" * 50)
    logger.info("🚀 matching_pipe 启动")
    logger.info("=" * 50)

    # 1. 就绪检查
    if not check_ready():
        return {
            "status": "skipped",
            "model_id": "matching_model_v2",
            "pipeline": "matching_pipe",
            "timestamp": datetime.datetime.utcnow().isoformat(),
            "elapsed_seconds": 0,
            "reason": "先决条件不满足 (训练脚本/v2训练数据缺失)",
        }

    # 2. 获取训练数据信息
    data_info = {}
    try:
        data_mtime = os.path.getmtime(V2_TRAINING_DATA_PATH)
        data_info["v2_data_mtime"] = datetime.datetime.fromtimestamp(data_mtime).isoformat()
        data_info["v2_data_size_kb"] = round(os.path.getsize(V2_TRAINING_DATA_PATH) / 1024, 1)
    except Exception:
        data_info["v2_data_mtime"] = "unknown"

    # 3. 执行训练脚本
    logger.info("▶ 执行训练脚本: %s", TRAIN_SCRIPT_PATH)
    try:
        result = subprocess.run(
            [sys.executable, TRAIN_SCRIPT_PATH],
            capture_output=True,
            text=True,
            timeout=TRAIN_TIMEOUT,
            cwd=BACKEND_DIR,
            env={**os.environ, "PYTHONUNBUFFERED": "1"},
        )
        exit_code = result.returncode
        stdout_preview = result.stdout[-2000:] if result.stdout else ""
        stderr_preview = result.stderr[-2000:] if result.stderr else ""

    except subprocess.TimeoutExpired:
        logger.error("⏰ 训练超时 (%ds)", TRAIN_TIMEOUT)
        return {
            "status": "timeout",
            "model_id": "matching_model_v2",
            "pipeline": "matching_pipe",
            "timestamp": datetime.datetime.utcnow().isoformat(),
            "elapsed_seconds": round(time.time() - start_time, 2),
            "error": f"训练脚本执行超时 ({TRAIN_TIMEOUT}s)",
            "train_script": TRAIN_SCRIPT_PATH,
        }
    except Exception as e:
        logger.error("💥 训练异常: %s", e)
        return {
            "status": "exception",
            "model_id": "matching_model_v2",
            "pipeline": "matching_pipe",
            "timestamp": datetime.datetime.utcnow().isoformat(),
            "elapsed_seconds": round(time.time() - start_time, 2),
            "error": str(e),
            "train_script": TRAIN_SCRIPT_PATH,
        }

    # 4. 验证模型文件产出
    model_ok = os.path.isfile(MODEL_OUTPUT_PATH)
    if model_ok:
        model_size_kb = round(os.path.getsize(MODEL_OUTPUT_PATH) / 1024, 1)
        logger.info("✅ 模型文件已产出: %s (%s KB)", MODEL_OUTPUT_PATH, model_size_kb)
    else:
        logger.warning("⚠️ 模型文件未找到: %s", MODEL_OUTPUT_PATH)

    # 5. 构建结果
    elapsed = round(time.time() - start_time, 2)

    if exit_code == 0:
        status = "success"
        logger.info("✅ matching_pipe 训练完成, 耗时=%.1fs", elapsed)
    else:
        status = "failed"
        logger.error("❌ matching_pipe 训练失败, exit=%d", exit_code)

    result_dict = {
        "status": status,
        "model_id": "matching_model_v2",
        "pipeline": "matching_pipe",
        "timestamp": datetime.datetime.utcnow().isoformat(),
        "elapsed_seconds": elapsed,
        "exit_code": exit_code,
        "data_info": data_info,
        "model_output": {
            "path": MODEL_OUTPUT_PATH,
            "exists": model_ok,
            "size_kb": model_size_kb if model_ok else 0,
        },
        "train_script": TRAIN_SCRIPT_PATH,
    }

    if result.stdout:
        result_dict["stdout_preview"] = stdout_preview
    if result.stderr:
        result_dict["stderr_preview"] = stderr_preview

    return result_dict


# ======================================================================
# 运行报告
# ======================================================================

def report() -> dict:
    """生成当前管道状态报告（不执行训练）

    Returns:
        dict: 包含模型文件状态、数据新鲜度、脚本状态等
    """
    now = time.time()
    report_data = {
        "pipeline": "matching_pipe",
        "model_id": "matching_model_v2",
        "display_name": "名片匹配模型v2",
        "priority": "P0",
        "timestamp": datetime.datetime.utcnow().isoformat(),
        "assets": {
            "train_script": {
                "path": TRAIN_SCRIPT_PATH,
                "exists": os.path.isfile(TRAIN_SCRIPT_PATH),
            },
            "model_file": {
                "path": MODEL_OUTPUT_PATH,
                "exists": os.path.isfile(MODEL_OUTPUT_PATH),
            },
            "v2_training_data": {
                "path": V2_TRAINING_DATA_PATH,
                "exists": os.path.isfile(V2_TRAINING_DATA_PATH),
            },
            "online_weights": {
                "path": ONLINE_WEIGHTS_PATH,
                "exists": os.path.isfile(ONLINE_WEIGHTS_PATH),
            },
        },
        "readiness": check_ready(),
    }

    # 补充文件时间信息
    for key, info in report_data["assets"].items():
        if info["exists"]:
            try:
                mtime = os.path.getmtime(info["path"])
                info["last_modified"] = datetime.datetime.fromtimestamp(mtime).isoformat()
                info["age_hours"] = round((now - mtime) / 3600, 2)
                info["size_kb"] = round(os.path.getsize(info["path"]) / 1024, 1)
            except Exception:
                pass

    return report_data


# ======================================================================
# main 入口
# ======================================================================

def main():
    """独立入口（可用于cron调用）

    用法:
        python -m app.data_pipeline.pipes.matching_pipe
        python -m app.data_pipeline.pipes.matching_pipe --mode check
        python -m app.data_pipeline.pipes.matching_pipe --mode run
        python -m app.data_pipeline.pipes.matching_pipe --mode report --json
    """
    import argparse

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
        handlers=[logging.StreamHandler()],
    )

    parser = argparse.ArgumentParser(description="名片匹配模型训练管道包装器")
    parser.add_argument("--mode", choices=["check", "run", "report"],
                        default="run", help="运行模式")
    parser.add_argument("--json", action="store_true", help="JSON格式输出")
    args = parser.parse_args()

    if args.mode == "check":
        ready = check_ready()
        result = {
            "mode": "check",
            "pipeline": "matching_pipe",
            "ready": ready,
            "timestamp": datetime.datetime.utcnow().isoformat(),
        }
        if args.json:
            print(json.dumps(result, ensure_ascii=False, indent=2))
        else:
            print(f"{'✅' if ready else '❌'} matching_pipe {'就绪' if ready else '未就绪'}")

    elif args.mode == "run":
        result = run_pipeline()
        if args.json:
            print(json.dumps(result, ensure_ascii=False, indent=2))
        else:
            status_icon = {"success": "✅", "failed": "❌", "skipped": "⏭️", "timeout": "⏰", "exception": "💥"}
            icon = status_icon.get(result["status"], "❓")
            print(f"{icon} matching_pipe: {result['status']}")
            print(f"   耗时: {result.get('elapsed_seconds', 0)}s")
            if result.get("model_output", {}).get("exists"):
                print(f"   模型: {result['model_output']['path']} ({result['model_output']['size_kb']} KB)")
            if result.get("error"):
                print(f"   错误: {result['error']}")

    elif args.mode == "report":
        result = report()
        if args.json:
            print(json.dumps(result, ensure_ascii=False, indent=2))
        else:
            print("📊 matching_pipe 状态报告")
            print(f"   就绪: {'✅' if result['readiness'] else '❌'}")
            for key, info in result["assets"].items():
                ok = "✅" if info["exists"] else "❌"
                extra = ""
                if info.get("size_kb"):
                    extra += f", {info['size_kb']} KB"
                if info.get("age_hours") is not None:
                    extra += f", {info['age_hours']}h 前更新"
                print(f"   {ok} {key}: {info['path']}{extra}")
    else:
        print(f"未知模式: {args.mode}")
        sys.exit(1)


if __name__ == "__main__":
    main()
