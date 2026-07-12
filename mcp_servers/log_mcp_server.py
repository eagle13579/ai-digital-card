"""
日志收集 MCP 工具 — AI数智名片
采集和分析后端服务日志（JSON 结构化日志）
"""
import os
import json
import subprocess
import re
from datetime import datetime
from collections import Counter, defaultdict
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("AI 数智名片 - 日志收集工具")

BACKEND_DIR = os.path.normpath(os.path.join(os.path.dirname(__file__), '..', 'backend'))
LOG_FILE = os.path.join(BACKEND_DIR, 'logs', 'app.log')


@mcp.tool()
def get_recent_logs(lines: int = 100) -> list[dict]:
    """
    获取最近 N 条日志

    参数:
        lines: 行数（默认100，最大500）
    """
    logs = []
    # 尝试读取日志文件
    log_sources = [
        LOG_FILE,
        os.path.join(BACKEND_DIR, 'app.log'),
        os.path.join(BACKEND_DIR, 'data', 'learning_log.jsonl'),
    ]

    for path in log_sources:
        if os.path.exists(path):
            with open(path, 'r', encoding='utf-8', errors='replace') as f:
                all_lines = f.readlines()
                for line in all_lines[-lines:]:
                    line = line.strip()
                    if line:
                        try:
                            logs.append(json.loads(line))
                        except json.JSONDecodeError:
                            logs.append({"raw": line, "timestamp": datetime.now().isoformat()})
            break

    if logs:
        return logs

    return [{"message": "未找到日志文件，后端可能未生成日志文件（日志输出到 stderr）"}]


@mcp.tool()
def check_service_health() -> dict:
    """
    健康检查：检测后端服务是否运行
    """
    import socket

    host = "127.0.0.1"
    port = 8201

    result = {
        "service": "AI数智名片后端 (port 8201)",
        "timestamp": datetime.now().isoformat(),
    }

    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(3)
        code = sock.connect_ex((host, port))
        sock.close()
        if code == 0:
            result["status"] = "running"
            result["message"] = "服务运行中"
        else:
            result["status"] = "stopped"
            result["message"] = f"端口 {port} 未监听，服务未启动"
    except Exception as e:
        result["status"] = "error"
        result["message"] = str(e)

    return result


@mcp.tool()
def analyze_logs(lines: int = 500) -> dict:
    """
    分析日志统计：错误率、常用路径、响应时间分布

    参数:
        lines: 分析的日志行数（默认500）
    """
    log_entries = []

    for path in [LOG_FILE, os.path.join(BACKEND_DIR, 'app.log')]:
        if os.path.exists(path):
            with open(path, 'r', encoding='utf-8', errors='replace') as f:
                all_lines = f.readlines()
                for line in all_lines[-lines:]:
                    if line.strip():
                        try:
                            entry = json.loads(line)
                            log_entries.append(entry)
                        except json.JSONDecodeError:
                            pass
            break

    if not log_entries:
        return {
            "source": "无日志文件",
            "total_entries": 0,
            "error": "未找到可分析的日志。后端日志输出到 stderr，需要配置日志文件输出。",
            "setup_hint": (
                "配置方法: 在 backend/app/middleware/logging_middleware.py 中添加 FileHandler，\n"
                "或在 .env 中添加 LOG_FILE=logs/app.log"
            )
        }

    # 统计级别
    level_counts = Counter(e.get("level", "UNKNOWN") for e in log_entries)

    # 错误日志
    errors = [e for e in log_entries if e.get("level") in ("ERROR", "CRITICAL", "WARNING")]

    # 请求路径统计
    path_counts = Counter(e.get("path", "") for e in log_entries if e.get("path"))

    # 慢请求
    slow_requests = [
        {"path": e.get("path"), "duration_ms": e.get("duration_ms"), "method": e.get("method")}
        for e in log_entries
        if e.get("duration_ms") and e["duration_ms"] > 1000
    ]
    slow_requests.sort(key=lambda x: x["duration_ms"], reverse=True)

    # 响应码统计
    status_counts = Counter(str(e.get("status")) for e in log_entries if e.get("status"))

    # 平均响应时间
    durations = [e["duration_ms"] for e in log_entries if e.get("duration_ms")]
    avg_duration = round(sum(durations) / len(durations), 2) if durations else 0

    return {
        "source": "日志文件",
        "total_entries": len(log_entries),
        "level_distribution": dict(level_counts),
        "status_code_distribution": dict(status_counts),
        "avg_response_ms": avg_duration,
        "slow_requests_count": len(slow_requests),
        "slow_requests_top5": slow_requests[:5],
        "error_count": len(errors),
        "error_details": errors[-10:] if errors else [],
        "top_paths": path_counts.most_common(10),
    }


@mcp.tool()
def tail_service_logs(timeout_seconds: int = 5) -> str:
    """
    实时获取后端服务最近日志输出
    尝试从 stderr 捕获日志

    参数:
        timeout_seconds: 等待时间（秒）
    """
    try:
        # 尝试使用系统命令获取服务日志
        if os.name == 'nt':
            # Windows: 尝试查找 python 进程
            result = subprocess.run(
                ['wmic', 'process', 'where', 'name="python.exe"', 'get', 'commandline,processid',
                 '/format:csv'],
                capture_output=True, text=True, timeout=timeout_seconds
            )
            lines = result.stdout.strip().split('\n')
            procs = [l for l in lines if 'main:app' in l or 'uvicorn' in l]
            if procs:
                return f"后端服务进程:\n" + "\n".join(procs[:5])
            else:
                return "未找到运行中的 uvicorn 进程"
        else:
            result = subprocess.run(
                ['ps', 'aux'], capture_output=True, text=True, timeout=timeout_seconds
            )
            lines = result.stdout.strip().split('\n')
            procs = [l for l in lines if 'uvicorn' in l or 'main:app' in l]
            if procs:
                return f"后端服务进程:\n" + "\n".join(procs[:5])
            else:
                return "未找到运行中的 uvicorn 进程"
    except subprocess.TimeoutExpired:
        return "查询超时"
    except Exception as e:
        return f"查询出错: {e}"


if __name__ == "__main__":
    mcp.run(transport="stdio")
