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
    健康检查：检测后端服务是否运行（本地dev + 生产SSH + 生产公网 三路检查）
    
    三路确认:
    - local_8201: 本地开发环境端口
    - ssh_prod_8201: SSH直连生产服务器 localhost:8201（最准确）
    - card.liankebao.top: 生产公网域名（走Nginx）
    """
    import socket
    import urllib.request
    import urllib.error

    result = {
        "service": "AI数智名片后端 (port 8201)",
        "timestamp": datetime.now().isoformat(),
        "checks": {},
    }

    # 检查1：本地端口
    local_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    local_sock.settimeout(3)
    local_code = local_sock.connect_ex(("127.0.0.1", 8201))
    local_sock.close()
    result["checks"]["local_8201"] = "running" if local_code == 0 else "stopped"

    # 检查2：生产服务器 SSH 直连 (最准确的健康检查)
    try:
        ssh_check = subprocess.run(
            ["ssh", "-o", "ConnectTimeout=5", "-o", "StrictHostKeyChecking=no",
             "root@47.116.116.87",
             "curl -s -o /dev/null -w '%{http_code}' --max-time 5 http://localhost:8201/health"],
            capture_output=True, text=True, timeout=10
        )
        if ssh_check.returncode == 0 and ssh_check.stdout.strip().startswith("2"):
            result["checks"]["ssh_prod_8201"] = f"HTTP_{ssh_check.stdout.strip()}"
        elif ssh_check.returncode == 0 and ssh_check.stdout.strip():
            result["checks"]["ssh_prod_8201"] = f"HTTP_{ssh_check.stdout.strip()}"
        else:
            stderr = ssh_check.stderr.strip()
            result["checks"]["ssh_prod_8201"] = f"ssh_error: {stderr[:80]}" if stderr else "ssh_failed"
    except subprocess.TimeoutExpired:
        result["checks"]["ssh_prod_8201"] = "ssh_timeout"
    except FileNotFoundError:
        result["checks"]["ssh_prod_8201"] = "ssh_not_available"
    except Exception as e:
        result["checks"]["ssh_prod_8201"] = f"error: {str(e)[:60]}"

    # 检查3：生产公网（走Nginx，可能被链客宝劫持）
    try:
        req = urllib.request.Request(
            "https://card.liankebao.top/api/brochures/visible",
            method="GET",
            headers={"User-Agent": "MCP-HealthCheck/1.0"}
        )
        resp = urllib.request.urlopen(req, timeout=5)
        result["checks"]["card.liankebao.top"] = f"HTTP_{resp.status}"
        resp.close()
    except urllib.error.HTTPError as e:
        result["checks"]["card.liankebao.top"] = f"HTTP_{e.code}"
    except Exception as e:
        result["checks"]["card.liankebao.top"] = str(e)
    
    # 综合状态（SSH直连最权威）
    ssh_ok = result["checks"].get("ssh_prod_8201", "").startswith("HTTP_2")
    local_ok = result["checks"]["local_8201"] == "running"
    
    if ssh_ok and local_ok:
        result["status"] = "running"
        result["message"] = "生产+本地均正常"
    elif ssh_ok:
        result["status"] = "running"
        result["message"] = "生产正常，本地dev未运行"
    elif local_ok:
        result["status"] = "degraded"
        result["message"] = "本地dev正常，生产异常"
    else:
        result["status"] = "stopped"
        result["message"] = "生产与本地均不可用"

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
