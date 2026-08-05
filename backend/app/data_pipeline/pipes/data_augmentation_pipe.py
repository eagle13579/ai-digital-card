"""
P0级 · 数据增强管道包装器 (data_augmentation_pipe)
====================================================
包装 scripts/data_augmentation.py 为受控管道调用。

职责:
  - 检查 data/training_data.json 和爬虫新数据是否就绪
  - 调用 scripts/data_augmentation.py 执行数据增强
  - 输出增强后的数据集路径
"""

import os
import sys
import json
import time
import datetime
import logging
import subprocess

logger = logging.getLogger("DataAugmentationPipe")

# ── 路径常量 ──────────────────────────────────────────────────────
BACKEND_DIR = os.path.normpath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
DATA_DIR = os.path.join(BACKEND_DIR, "data")
SCRIPTS_DIR = os.path.join(BACKEND_DIR, "scripts")

TRAINING_DATA_PATH = os.path.join(DATA_DIR, "training_data.json")
AUGMENT_SCRIPT_PATH = os.path.join(SCRIPTS_DIR, "data_augmentation.py")
AUGMENTED_OUTPUT_PATH = os.path.join(DATA_DIR, "augmented_dataset.json")

# 执行超时 (秒)
AUGMENT_TIMEOUT = 600


# ======================================================================
# 就绪检查
# ======================================================================

def check_ready() -> bool:
    """检查数据和依赖是否就绪

    检查项:
      1. 增强脚本是否存在
      2. training_data.json 是否存在且非空
      3. 爬虫新数据目录是否有新文件 (data/raw_crawled/ 下的最新文件)
      4. data/ 目录可写

    Returns:
        bool: 是否就绪
    """
    checks = []

    # 1. 脚本就绪
    script_ok = os.path.isfile(AUGMENT_SCRIPT_PATH)
    checks.append(("augment_script_exists", script_ok))
    if not script_ok:
        logger.warning("数据增强脚本不存在: %s", AUGMENT_SCRIPT_PATH)

    # 2. 训练数据就绪
    data_ok = os.path.isfile(TRAINING_DATA_PATH)
    if data_ok:
        try:
            with open(TRAINING_DATA_PATH, "r", encoding="utf-8") as f:
                content = json.load(f)
            data_ok = bool(content)  # 非空
            if data_ok:
                logger.info("training_data.json 有 %d 条记录", len(content) if isinstance(content, list) else 1)
        except (json.JSONDecodeError, Exception):
            data_ok = False
    checks.append(("training_data_ready", data_ok))
    if not data_ok:
        logger.warning("训练数据缺失或为空: %s", TRAINING_DATA_PATH)

    # 3. 爬虫新数据检查 — 检测 data/raw_crawled/ 目录下是否有新文件
    raw_dir = os.path.join(DATA_DIR, "raw_crawled")
    new_crawl_data = False
    if os.path.isdir(raw_dir):
        try:
            files = [
                os.path.join(raw_dir, f)
                for f in os.listdir(raw_dir)
                if f.endswith(".json") or f.endswith(".jsonl")
            ]
            if files:
                # 取最新文件
                newest = max(files, key=os.path.getmtime)
                age_hours = (time.time() - os.path.getmtime(newest)) / 3600
                if age_hours < 48:  # 48小时内算新鲜
                    new_crawl_data = True
                    logger.info("爬虫有新数据: %s (%.1fh 前)", newest, age_hours)
                else:
                    logger.info("爬虫数据已过期 (>48h), 使用已有训练数据")
        except Exception as e:
            logger.debug("爬虫数据目录检查异常: %s", e)
    else:
        logger.info("爬虫原始数据目录不存在 (%s), 跳过爬虫数据检查", raw_dir)
    checks.append(("new_crawl_data_available", new_crawl_data or data_ok))

    # 4. 数据目录可写
    data_writable = os.access(DATA_DIR, os.W_OK) if os.path.exists(DATA_DIR) else False
    checks.append(("data_dir_writable", data_writable))

    all_ok = all(ok for name, ok in checks)

    if all_ok:
        logger.info("✅ data_augmentation_pipe 就绪检查通过 (%d/4)", len(checks))
    else:
        failed = [name for name, ok in checks if not ok]
        logger.warning("⚠️ data_augmentation_pipe 就绪检查未通过: %s", failed)

    return all_ok


# ======================================================================
# 管道执行
# ======================================================================

def run_pipeline() -> dict:
    """执行数据增强管道

    流程:
      1. check_ready()
      2. 如果就绪, subprocess.run(增强脚本, cwd=BACKEND_DIR)
      3. 捕获输出、超时、错误
      4. 验证增强数据集产出

    Returns:
        dict: 执行结果
    """
    start_time = time.time()
    logger.info("=" * 50)
    logger.info("🚀 data_augmentation_pipe 启动")
    logger.info("=" * 50)

    if not check_ready():
        return {
            "status": "skipped",
            "model_id": "data_augmentation",
            "pipeline": "data_augmentation_pipe",
            "timestamp": datetime.datetime.utcnow().isoformat(),
            "elapsed_seconds": 0,
            "reason": "先决条件不满足 (增强脚本/训练数据缺失)",
        }

    # 获取训练数据信息
    data_info = {}
    try:
        data_mtime = os.path.getmtime(TRAINING_DATA_PATH)
        data_info["training_data_mtime"] = datetime.datetime.fromtimestamp(data_mtime).isoformat()
        data_info["training_data_size_kb"] = round(os.path.getsize(TRAINING_DATA_PATH) / 1024, 1)
    except Exception:
        pass

    # 执行增强脚本
    logger.info("▶ 执行数据增强脚本: %s", AUGMENT_SCRIPT_PATH)
    try:
        result = subprocess.run(
            [sys.executable, AUGMENT_SCRIPT_PATH],
            capture_output=True,
            text=True,
            timeout=AUGMENT_TIMEOUT,
            cwd=BACKEND_DIR,
            env={**os.environ, "PYTHONUNBUFFERED": "1"},
        )
        exit_code = result.returncode
        stdout_preview = result.stdout[-2000:] if result.stdout else ""
        stderr_preview = result.stderr[-2000:] if result.stderr else ""

    except subprocess.TimeoutExpired:
        logger.error("⏰ 数据增强超时 (%ds)", AUGMENT_TIMEOUT)
        return {
            "status": "timeout",
            "model_id": "data_augmentation",
            "pipeline": "data_augmentation_pipe",
            "timestamp": datetime.datetime.utcnow().isoformat(),
            "elapsed_seconds": round(time.time() - start_time, 2),
            "error": f"增强脚本执行超时 ({AUGMENT_TIMEOUT}s)",
            "augment_script": AUGMENT_SCRIPT_PATH,
        }
    except Exception as e:
        logger.error("💥 数据增强异常: %s", e)
        return {
            "status": "exception",
            "model_id": "data_augmentation",
            "pipeline": "data_augmentation_pipe",
            "timestamp": datetime.datetime.utcnow().isoformat(),
            "elapsed_seconds": round(time.time() - start_time, 2),
            "error": str(e),
            "augment_script": AUGMENT_SCRIPT_PATH,
        }

    # 验证增强数据集产出
    output_ok = os.path.isfile(AUGMENTED_OUTPUT_PATH)
    output_size_kb = 0
    output_record_count = 0
    if output_ok:
        output_size_kb = round(os.path.getsize(AUGMENTED_OUTPUT_PATH) / 1024, 1)
        try:
            with open(AUGMENTED_OUTPUT_PATH, "r", encoding="utf-8") as f:
                aug_data = json.load(f)
            if isinstance(aug_data, list):
                output_record_count = len(aug_data)
            elif isinstance(aug_data, dict):
                output_record_count = len(aug_data)
        except Exception:
            pass
        logger.info("✅ 增强数据集已产出: %s (%s KB, %d 条)",
                     AUGMENTED_OUTPUT_PATH, output_size_kb, output_record_count)

    elapsed = round(time.time() - start_time, 2)

    if exit_code == 0 and output_ok:
        status = "success"
        logger.info("✅ data_augmentation_pipe 完成, 耗时=%.1fs", elapsed)
    elif exit_code == 0:
        status = "partial"
        logger.warning("⚠️ 脚本正常退出但增强数据集未生成")
    else:
        status = "failed"
        logger.error("❌ data_augmentation_pipe 失败, exit=%d", exit_code)

    result_dict = {
        "status": status,
        "model_id": "data_augmentation",
        "pipeline": "data_augmentation_pipe",
        "timestamp": datetime.datetime.utcnow().isoformat(),
        "elapsed_seconds": elapsed,
        "exit_code": exit_code,
        "data_info": data_info,
        "augmented_output": {
            "path": AUGMENTED_OUTPUT_PATH,
            "exists": output_ok,
            "size_kb": output_size_kb,
            "record_count": output_record_count,
        },
        "augment_script": AUGMENT_SCRIPT_PATH,
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
    """生成当前管道状态报告（不执行增强）

    Returns:
        dict: 包含数据文件状态、脚本状态等
    """
    now = time.time()
    report_data = {
        "pipeline": "data_augmentation_pipe",
        "model_id": "data_augmentation",
        "display_name": "数据增强管道",
        "priority": "P0",
        "timestamp": datetime.datetime.utcnow().isoformat(),
        "assets": {
            "augment_script": {
                "path": AUGMENT_SCRIPT_PATH,
                "exists": os.path.isfile(AUGMENT_SCRIPT_PATH),
            },
            "training_data": {
                "path": TRAINING_DATA_PATH,
                "exists": os.path.isfile(TRAINING_DATA_PATH),
            },
            "augmented_dataset": {
                "path": AUGMENTED_OUTPUT_PATH,
                "exists": os.path.isfile(AUGMENTED_OUTPUT_PATH),
            },
        },
        "readiness": check_ready(),
    }

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
        python -m app.data_pipeline.pipes.data_augmentation_pipe
        python -m app.data_pipeline.pipes.data_augmentation_pipe --mode check
        python -m app.data_pipeline.pipes.data_augmentation_pipe --mode run
        python -m app.data_pipeline.pipes.data_augmentation_pipe --mode report --json
    """
    import argparse

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
        handlers=[logging.StreamHandler()],
    )

    parser = argparse.ArgumentParser(description="数据增强管道包装器")
    parser.add_argument("--mode", choices=["check", "run", "report"],
                        default="run", help="运行模式")
    parser.add_argument("--json", action="store_true", help="JSON格式输出")
    args = parser.parse_args()

    if args.mode == "check":
        ready = check_ready()
        result = {
            "mode": "check",
            "pipeline": "data_augmentation_pipe",
            "ready": ready,
            "timestamp": datetime.datetime.utcnow().isoformat(),
        }
        if args.json:
            print(json.dumps(result, ensure_ascii=False, indent=2))
        else:
            print(f"{'✅' if ready else '❌'} data_augmentation_pipe {'就绪' if ready else '未就绪'}")

    elif args.mode == "run":
        result = run_pipeline()
        if args.json:
            print(json.dumps(result, ensure_ascii=False, indent=2))
        else:
            status_icon = {"success": "✅", "failed": "❌", "skipped": "⏭️", "timeout": "⏰", "exception": "💥", "partial": "⚠️"}
            icon = status_icon.get(result["status"], "❓")
            print(f"{icon} data_augmentation_pipe: {result['status']}")
            print(f"   耗时: {result.get('elapsed_seconds', 0)}s")
            if result.get("augmented_output", {}).get("exists"):
                out = result["augmented_output"]
                print(f"   输出: {out['path']} ({out['size_kb']} KB, {out['record_count']} 条)")
            if result.get("error"):
                print(f"   错误: {result['error']}")

    elif args.mode == "report":
        result = report()
        if args.json:
            print(json.dumps(result, ensure_ascii=False, indent=2))
        else:
            print("📊 data_augmentation_pipe 状态报告")
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
