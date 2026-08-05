#!/usr/bin/env python3
"""gaia_orchestra_daemon.py — A Orchestra 编排器守护进程

作为PM2后台服务运行，将A Orchestra的吸收成果真正挂载到运行环境。
每小时轮询一次，自动压缩worker输出、收集基准数据。

启动: pm2 start gaia_orchestra_daemon.py --name gaia-orchestra
"""

from __future__ import annotations

import asyncio
import json
import logging
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("gaia-orchestra")

CACHE_DIR = Path("D:/AI数智名片/backend/cache/orchestra")
CACHE_DIR.mkdir(parents=True, exist_ok=True)


class OrchestraDaemon:
    """编排器守护进程 — 每小时执行一次闭环"""

    def __init__(self):
        self._benchmark_path = Path(
            "D:/向海容的知识库/wiki/wiki/记忆宫殿/scripts/gaia_benchmark.py"
        )

    async def tick(self) -> dict:
        """单次心跳：执行全部闭环"""
        results = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "compression_applied": 0,
            "benchmark_score": None,
            "errors": [],
        }

        # 1. 上下文提纯 — 子进程隔离
        try:
            pure_code = r"""
import sys, json, os
sys.path.insert(0, 'D:/AI数智名片/backend')
from app.agents.compression_protocol import context_distillation

log_dir = 'D:/AI数智名片/backend/logs'
result = {"compressed": 0}
if os.path.isdir(log_dir):
    logs = sorted(os.listdir(log_dir), key=lambda f: os.path.getmtime(os.path.join(log_dir, f)), reverse=True)[:3]
    for name in logs:
        path = os.path.join(log_dir, name)
        if os.path.isfile(path):
            try:
                content = open(path, encoding='utf-8', errors='replace').read()[:5000]
                context_distillation(content, 'agent error warning')
                result['compressed'] += 1
            except Exception:
                pass
print(json.dumps(result))
"""
            proc = await asyncio.create_subprocess_exec(
                sys.executable, "-c", pure_code,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=15)
            if stdout:
                data = json.loads(stdout.decode("utf-8"))
                results["compression_applied"] = data.get("compressed", 0)
            if stderr:
                err_text = stderr.decode("utf-8", errors="replace")[:200]
                if err_text.strip():
                    results["errors"].append(f"compression: {err_text}")
        except Exception as e:
            results["errors"].append(f"compression err: {e}")

        # 2. 基准测试 — 子进程
        if self._benchmark_path.exists():
            try:
                proc = await asyncio.create_subprocess_exec(
                    sys.executable, str(self._benchmark_path), "--format", "json",
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE,
                    cwd=str(self._benchmark_path.parent),
                )
                stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=30)
                if proc.returncode == 0 and stdout:
                    report = json.loads(stdout.decode("utf-8"))
                    results["benchmark_score"] = report.get("scores", {}).get("overall")
                if stderr:
                    err_text = stderr.decode("utf-8", errors="replace")[:200]
                    if err_text.strip():
                        results["errors"].append(f"benchmark: {err_text}")
            except Exception as e:
                results["errors"].append(f"benchmark err: {e}")

        return results

    async def loop(self, interval_seconds: int = 3600):
        """主循环"""
        logger.info("Orchestra 守护进程启动，间隔=%ds", interval_seconds)
        while True:
            try:
                results = await self.tick()
                logger.info(
                    "心跳: compression=%d score=%s errors=%d",
                    results["compression_applied"],
                    f"{results['benchmark_score']:.4f}" if results["benchmark_score"] else "N/A",
                    len(results["errors"]),
                )
            except Exception as e:
                logger.error("心跳异常: %s", e)
            await asyncio.sleep(interval_seconds)


if __name__ == "__main__":
    daemon = OrchestraDaemon()
    interval = int(os.environ.get("ORCHESTRA_INTERVAL", "3600"))
    try:
        asyncio.run(daemon.loop(interval))
    except KeyboardInterrupt:
        logger.info("守护进程停止")
