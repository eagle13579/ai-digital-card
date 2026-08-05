"""
P0级 · 在线学习管道包装器 (online_learning_pipe)
==================================================
包装 app/ai/online_learning.py 的在线学习接口为受控管道调用。

职责:
  - 直接读取 data/online_weights.json 和 data/learning_log.jsonl 确认就绪
  - 调用 app/ai/online_learning.py 的 trigger_learning() 接口
  - 输出学习结果报告
"""

import os
import sys
import json
import time
import datetime
import logging

logger = logging.getLogger("OnlineLearningPipe")

# ── 路径常量 ──────────────────────────────────────────────────────
BACKEND_DIR = os.path.normpath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
DATA_DIR = os.path.join(BACKEND_DIR, "data")

ONLINE_WEIGHTS_PATH = os.path.join(DATA_DIR, "online_weights.json")
LEARNING_LOG_PATH = os.path.join(DATA_DIR, "learning_log.jsonl")

# 记忆文件 — 记录上次学习时间/结果
PIPE_STATE_PATH = os.path.join(os.path.dirname(__file__), ".online_learning_pipe_state.json")


# ======================================================================
# 就绪检查
# ======================================================================

def check_ready() -> bool:
    """检查数据和依赖是否就绪

    检查项:
      1. 在线权重文件 (online_weights.json) 存在且可解析
      2. 学习日志文件存在（可选，新建也可）
      3. data/ 目录可写
      4. app/ai/online_learning.py 模块可导入

    Returns:
        bool: 是否就绪
    """
    checks = []

    # 1. 权重文件就绪
    weights_ok = os.path.isfile(ONLINE_WEIGHTS_PATH)
    if weights_ok:
        try:
            with open(ONLINE_WEIGHTS_PATH, "r", encoding="utf-8") as f:
                data = json.load(f)
            weights_ok = bool(data)
            logger.info("在线权重已加载: %d 个键", len(data))
        except (json.JSONDecodeError, Exception) as e:
            weights_ok = False
            logger.warning("在线权重文件解析失败: %s", e)
    checks.append(("online_weights_ready", weights_ok))
    if not weights_ok:
        logger.warning("在线权重文件缺失或无效: %s", ONLINE_WEIGHTS_PATH)

    # 2. 日志文件（可选就绪）
    log_ok = os.path.isfile(LEARNING_LOG_PATH)
    if log_ok:
        try:
            log_size = os.path.getsize(LEARNING_LOG_PATH)
            logger.info("学习日志文件存在: %s (%d bytes)", LEARNING_LOG_PATH, log_size)
        except Exception:
            pass
    else:
        logger.info("学习日志文件暂不存在 (%s), 首次运行将创建", LEARNING_LOG_PATH)
    checks.append(("learning_log_available", True))  # 非阻塞

    # 3. data/ 目录可写
    data_writable = os.access(DATA_DIR, os.W_OK) if os.path.exists(DATA_DIR) else False
    checks.append(("data_dir_writable", data_writable))

    # 4. 在线学习模块可导入
    module_ok = False
    try:
        # 仅验证导入路径，不实际实例化（避免副作用）
        import importlib.util
        online_learning_path = os.path.join(BACKEND_DIR, "app", "ai", "online_learning.py")
        if os.path.isfile(online_learning_path):
            spec = importlib.util.spec_from_file_location("app.ai.online_learning", online_learning_path)
            module_ok = spec is not None
        checks.append(("online_learning_module_importable", module_ok))
    except Exception as e:
        logger.warning("在线学习模块导入检查异常: %s", e)
        checks.append(("online_learning_module_importable", False))

    all_ok = all(ok for name, ok in checks if name != "learning_log_available")

    if all_ok:
        logger.info("✅ online_learning_pipe 就绪检查通过 (%d/4)", len(checks))
    else:
        failed = [name for name, ok in checks if not ok and name != "learning_log_available"]
        logger.warning("⚠️ online_learning_pipe 就绪检查未通过: %s", failed)

    return all_ok


# ======================================================================
# 管道执行
# ======================================================================

def run_pipeline(force: bool = False) -> dict:
    """执行在线学习管道

    直接调用 app/ai/online_learning.py 的 trigger_learning() 或
    check_and_learn() 接口，而非通过 subprocess。

    流程:
      1. check_ready()
      2. sys.path 注入 BACKEND_DIR, 导入 trigger_learning / get_learning_status
      3. 执行 trigger_learning() — 运行一轮完整学习周期
      4. 读取 learning_log.jsonl 获取最新日志
      5. 保存管道状态

    Args:
        force: 如果 True, 直接触发 run_learning_cycle() 而非 check_and_learn()

    Returns:
        dict: {
            "status": "success" | "skipped" | "no_new_feedback" | "exception",
            "model_id": "online_learning",
            ...
        }
    """
    start_time = time.time()
    logger.info("=" * 50)
    logger.info("🚀 online_learning_pipe 启动%s", " (强制模式)" if force else "")
    logger.info("=" * 50)

    if not check_ready():
        return {
            "status": "skipped",
            "model_id": "online_learning",
            "pipeline": "online_learning_pipe",
            "timestamp": datetime.datetime.utcnow().isoformat(),
            "elapsed_seconds": 0,
            "reason": "先决条件不满足 (权重文件/模块不可用)",
        }

    # 读取当前权重作为基线
    current_weights = {}
    try:
        with open(ONLINE_WEIGHTS_PATH, "r", encoding="utf-8") as f:
            current_weights = json.load(f)
    except Exception:
        pass

    # ── 导入并调用在线学习模块 ──────────────────────────────────
    try:
        # 确保 BACKEND_DIR 在 sys.path 中
        if BACKEND_DIR not in sys.path:
            sys.path.insert(0, BACKEND_DIR)

        from app.ai.online_learning import (
            trigger_learning,
            get_learning_status,
            get_online_learning_engine,
        )

        engine = get_online_learning_engine()

        if force:
            # 强制运行完整学习周期
            logger.info("▶ 强制触发在线学习 (run_learning_cycle)")
            learn_result = engine.run_learning_cycle()
        else:
            # 检查反馈量是否达到阈值
            logger.info("▶ 检查是否达到学习阈值 (check_and_learn)")
            learn_result = engine.check_and_learn()

    except ImportError as e:
        logger.error("在线学习模块导入失败: %s", e)
        return {
            "status": "exception",
            "model_id": "online_learning",
            "pipeline": "online_learning_pipe",
            "timestamp": datetime.datetime.utcnow().isoformat(),
            "elapsed_seconds": round(time.time() - start_time, 2),
            "error": f"模块导入失败: {e}",
        }
    except Exception as e:
        logger.error("💥 在线学习执行异常: %s", e)
        return {
            "status": "exception",
            "model_id": "online_learning",
            "pipeline": "online_learning_pipe",
            "timestamp": datetime.datetime.utcnow().isoformat(),
            "elapsed_seconds": round(time.time() - start_time, 2),
            "error": str(e),
        }

    # ── 处理返回结果 ────────────────────────────────────────────
    elapsed = round(time.time() - start_time, 2)

    if learn_result is None:
        # check_and_learn 返回 None — 未达阈值
        # 获取当前状态
        status_info = engine.get_learning_status()
        feedback = status_info.get("feedback", {})
        learning = status_info.get("learning", {})

        result = {
            "status": "no_new_feedback",
            "model_id": "online_learning",
            "pipeline": "online_learning_pipe",
            "timestamp": datetime.datetime.utcnow().isoformat(),
            "elapsed_seconds": elapsed,
            "message": "反馈累积未达学习阈值, 跳过本轮学习",
            "details": {
                "total_feedback": feedback.get("total", 0),
                "new_since_last_learn": learning.get("new_since_last_learn", 0),
                "threshold": learning.get("threshold", 100),
                "progress_percent": learning.get("progress_percent", 0),
                "total_cycles": learning.get("total_cycles", 0),
            },
        }
        logger.info("⏭️ 跳过学习: 新增反馈 %d / %d (%.1f%%)",
                     result["details"]["new_since_last_learn"],
                     result["details"]["threshold"],
                     result["details"]["progress_percent"])
    else:
        # 有学习结果
        weight_changes = learn_result.get("weight_changes", {})
        feedback_stats = learn_result.get("feedback_stats", {})

        # 读取最新学习日志
        recent_logs = []
        try:
            recent_logs = engine.get_recent_logs(limit=5)
        except Exception:
            pass

        result = {
            "status": "success",
            "model_id": "online_learning",
            "pipeline": "online_learning_pipe",
            "timestamp": datetime.datetime.utcnow().isoformat(),
            "elapsed_seconds": elapsed,
            "cycle": learn_result.get("cycle", 0),
            "weight_changes": {
                "old_global_adjustment": weight_changes.get("old_global_adjustment"),
                "new_global_adjustment": weight_changes.get("new_global_adjustment"),
                "net_adjust": weight_changes.get("net_adjust"),
                "old_weights": weight_changes.get("old_weights"),
                "new_weights": weight_changes.get("new_weights"),
            },
            "feedback_stats": {
                "total": feedback_stats.get("total", 0),
                "positive": feedback_stats.get("positive", 0),
                "negative": feedback_stats.get("negative", 0),
                "new_since_last": feedback_stats.get("new_since_last", 0),
                "like_ratio": feedback_stats.get("like_ratio", 0),
            },
            "new_weights_file": ONLINE_WEIGHTS_PATH,
            "recent_logs_count": len(recent_logs),
        }

        logger.info("✅ online_learning_pipe 完成, cycle=%d, adjustment=%.4f→%.4f, 耗时=%.1fs",
                     result["cycle"],
                     weight_changes.get("old_global_adjustment", 0),
                     weight_changes.get("new_global_adjustment", 0),
                     elapsed)

    # 持久化管道状态
    _save_state(result)

    return result


# ======================================================================
# 运行报告
# ======================================================================

def report() -> dict:
    """生成当前管道状态报告（不执行学习）

    Returns:
        dict: 包含权重文件、学习日志、模块状态等
    """
    now = time.time()

    # 尝试加载在线学习引擎状态
    engine_status = {}
    try:
        if BACKEND_DIR not in sys.path:
            sys.path.insert(0, BACKEND_DIR)
        from app.ai.online_learning import get_learning_status
        engine_status = get_learning_status()
    except Exception as e:
        logger.debug("无法获取在线学习引擎状态: %s", e)

    # 加载管道历史状态
    pipe_state = _load_state()

    report_data = {
        "pipeline": "online_learning_pipe",
        "model_id": "online_learning",
        "display_name": "在线学习引擎",
        "priority": "P1",
        "timestamp": datetime.datetime.utcnow().isoformat(),
        "assets": {
            "online_weights": {
                "path": ONLINE_WEIGHTS_PATH,
                "exists": os.path.isfile(ONLINE_WEIGHTS_PATH),
            },
            "learning_log": {
                "path": LEARNING_LOG_PATH,
                "exists": os.path.isfile(LEARNING_LOG_PATH),
            },
        },
        "engine_status": engine_status,
        "pipe_state": pipe_state,
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
# 管道状态持久化
# ======================================================================

def _load_state() -> dict:
    """加载管道持久化状态"""
    if os.path.exists(PIPE_STATE_PATH):
        try:
            with open(PIPE_STATE_PATH, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {"last_run": None, "total_runs": 0, "last_result": None}


def _save_state(result: dict):
    """持久化管道状态"""
    try:
        state = _load_state()
        state["last_run"] = result.get("timestamp", datetime.datetime.utcnow().isoformat())
        state["total_runs"] = state.get("total_runs", 0) + 1
        state["last_result"] = {
            "status": result.get("status"),
            "timestamp": result.get("timestamp"),
            "elapsed_seconds": result.get("elapsed_seconds"),
        }
        os.makedirs(os.path.dirname(PIPE_STATE_PATH), exist_ok=True)
        with open(PIPE_STATE_PATH, "w", encoding="utf-8") as f:
            json.dump(state, f, ensure_ascii=False, indent=2)
    except Exception as e:
        logger.debug("管道状态持久化失败: %s", e)


# ======================================================================
# main 入口
# ======================================================================

def main():
    """独立入口（可用于cron调用）

    用法:
        python -m app.data_pipeline.pipes.online_learning_pipe
        python -m app.data_pipeline.pipes.online_learning_pipe --mode check
        python -m app.data_pipeline.pipes.online_learning_pipe --mode run
        python -m app.data_pipeline.pipes.online_learning_pipe --mode run --force
        python -m app.data_pipeline.pipes.online_learning_pipe --mode report --json
    """
    import argparse

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
        handlers=[logging.StreamHandler()],
    )

    parser = argparse.ArgumentParser(description="在线学习管道包装器")
    parser.add_argument("--mode", choices=["check", "run", "report"],
                        default="run", help="运行模式")
    parser.add_argument("--force", action="store_true",
                        help="强制触发完整学习周期 (无视阈值)")
    parser.add_argument("--json", action="store_true", help="JSON格式输出")
    args = parser.parse_args()

    if args.mode == "check":
        ready = check_ready()
        result = {
            "mode": "check",
            "pipeline": "online_learning_pipe",
            "ready": ready,
            "timestamp": datetime.datetime.utcnow().isoformat(),
        }
        if args.json:
            print(json.dumps(result, ensure_ascii=False, indent=2))
        else:
            print(f"{'✅' if ready else '❌'} online_learning_pipe {'就绪' if ready else '未就绪'}")

    elif args.mode == "run":
        result = run_pipeline(force=args.force)
        if args.json:
            print(json.dumps(result, ensure_ascii=False, indent=2))
        else:
            status = result["status"]
            status_icon = {"success": "✅", "no_new_feedback": "⏭️", "skipped": "⏭️", "exception": "💥"}
            icon = status_icon.get(status, "❓")
            print(f"{icon} online_learning_pipe: {status}")
            print(f"   耗时: {result.get('elapsed_seconds', 0)}s")
            if status == "success":
                wc = result.get("weight_changes", {})
                print(f"   调整: {wc.get('old_global_adjustment', '?')} → {wc.get('new_global_adjustment', '?')}")
                print(f"   权重: {wc.get('new_weights', {})}")
            elif status == "no_new_feedback":
                d = result.get("details", {})
                print(f"   反馈进度: {d.get('new_since_last_learn', 0)} / {d.get('threshold', 100)} ({d.get('progress_percent', 0)}%)")
            if result.get("error"):
                print(f"   错误: {result['error']}")

    elif args.mode == "report":
        result = report()
        if args.json:
            print(json.dumps(result, ensure_ascii=False, indent=2))
        else:
            print("📊 online_learning_pipe 状态报告")
            print(f"   就绪: {'✅' if result['readiness'] else '❌'}")
            for key, info in result["assets"].items():
                ok = "✅" if info["exists"] else "❌"
                extra = ""
                if info.get("size_kb"):
                    extra += f", {info['size_kb']} KB"
                if info.get("age_hours") is not None:
                    extra += f", {info['age_hours']}h 前更新"
                print(f"   {ok} {key}: {info['path']}{extra}")
            es = result.get("engine_status", {})
            if es:
                feedback = es.get("feedback", {})
                learning = es.get("learning", {})
                weights = es.get("current_weights", {})
                print(f"   反馈: {feedback.get('total', 0)} 条 (👍{feedback.get('positive', 0)}/👎{feedback.get('negative', 0)})")
                print(f"   学习: {learning.get('total_cycles', 0)} 周期, {learning.get('progress_percent', 0)}% 至下次")
                print(f"   权重: global_adj={weights.get('global_adjustment', 1.0)}")
            ps = result.get("pipe_state", {})
            if ps.get("total_runs", 0) > 0:
                print(f"   管道历史: {ps['total_runs']} 次运行, 上次={ps.get('last_run', 'N/A')}")

    else:
        print(f"未知模式: {args.mode}")
        sys.exit(1)


if __name__ == "__main__":
    main()
