#!/usr/bin/env python3
"""disk_watchdog.py — 磁盘空间监控（v1.0 重建版）

检查 / 、/var/www、/opt 等关键分区的使用率，超过阈值时输出告警。
no_agent cron 包装: 空输出 = 静默正常；非空输出 = 告警推送。
"""
import shutil
import sys

THRESHOLD = 85  # 使用率阈值 %
WARN_PATHS = ["/", "/var", "/opt", "/tmp"]


def main() -> int:
    alerts = []
    checked = set()
    for p in WARN_PATHS:
        try:
            usage = shutil.disk_usage(p)
        except OSError:
            continue
        # 同一文件系统只报一次
        if p in checked:
            continue
        checked.add(p)
        pct = usage.used / usage.total * 100
        if pct >= THRESHOLD:
            alerts.append(
                f"⚠️ 磁盘告警 {p}: 已用 {pct:.1f}% "
                f"({usage.used / 1024**3:.1f}G / {usage.total / 1024**3:.1f}G)"
            )
    if alerts:
        print("\n".join(alerts))
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
