#!/usr/bin/env python
"""
全自动cron任务注册脚本 — 7×24数据管道定时任务

注册以下 cron 任务:
  ┌──────────────────────────────────────────────┬──────────┬──────────────────────────────────────┐
  │ 任务名                                       │ 频率     │ 命令                                 │
  ├──────────────────────────────────────────────┼──────────┼──────────────────────────────────────┤
  │ data-pipeline-full-cycle                     │ 每1小时  │ pipeline_controller --mode full      │
  │ data-pipeline-collect                        │ 每30分钟 │ pipeline_controller --mode collect   │
  │ data-pipeline-train                          │ 每30分钟 │ pipeline_controller --mode train      │
  │ data-pipeline-health                         │ 每5分钟  │ pipeline_health_check                │
  │ data-online-learning                         │ 每15分钟 │ pipeline_controller --mode train      │
  └──────────────────────────────────────────────┴──────────┴──────────────────────────────────────┘

用法:
  python -m app.data_pipeline.register_cron                     # 注册到crontab
  python -m app.data_pipeline.register_cron --dry-run           # 仅打印不安装
  python -m app.data_pipeline.register_cron --print-cron-file   # 生成cron文件路径
  python -m app.data_pipeline.register_cron --remove            # 移除本脚本注册的任务
"""
import argparse
import json
import os
import subprocess
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path

# ── 路径配置 ──────────────────────────────────────────────
HERE = Path(__file__).parent.resolve()
BACKEND_DIR = HERE.parent.parent.resolve()
PROJECT_ROOT = BACKEND_DIR.parent.resolve()

CRON_CONFIG_DIR = HERE / ".cron_configs"
CRON_CONFIG_FILE = CRON_CONFIG_DIR / "registered_crons.json"

# 日志目录
LOG_DIR = PROJECT_ROOT / "logs"
os.makedirs(LOG_DIR, exist_ok=True)

# ── cron 任务定义 ─────────────────────────────────────────
# 格式: (任务ID, cron表达式, 命令, 描述)
CRON_DEFINITIONS = [
    {
        "id": "data-pipeline-full-cycle",
        "schedule": "0 * * * *",                          # 每整点 (每1小时)
        "description": "完整数据管道 — 采集+治理+训练全周期",
        "command": (
            f'cd {BACKEND_DIR} && '
            f'{sys.executable} -m app.data_pipeline.pipeline_controller '
            f'--mode full --json'
            f' >> {LOG_DIR / "cron_full_cycle.log"} 2>&1'
        ),
    },
    {
        "id": "data-pipeline-collect",
        "schedule": "*/30 * * * *",                       # 每30分钟
        "description": "仅数据采集 — 运行所有到期爬虫",
        "command": (
            f'cd {BACKEND_DIR} && '
            f'{sys.executable} -m app.data_pipeline.pipeline_controller '
            f'--mode collect --json'
            f' >> {LOG_DIR / "cron_collect.log"} 2>&1'
        ),
    },
    {
        "id": "data-pipeline-train",
        "schedule": "*/30 * * * *",                       # 每30分钟
        "description": "仅模型训练 — 训练所有到期模型",
        "command": (
            f'cd {BACKEND_DIR} && '
            f'{sys.executable} -m app.data_pipeline.pipeline_controller '
            f'--mode train --json'
            f' >> {LOG_DIR / "cron_train.log"} 2>&1'
        ),
    },
    {
        "id": "data-pipeline-health",
        "schedule": "*/5 * * * *",                        # 每5分钟
        "description": "数据管道健康检查 — 自动监控管道状态",
        "command": (
            f'cd {BACKEND_DIR} && '
            f'{sys.executable} -m app.data_pipeline.pipeline_health_check'
            f' >> {LOG_DIR / "cron_health.log"} 2>&1'
        ),
    },
    {
        "id": "data-online-learning",
        "schedule": "*/15 * * * *",                       # 每15分钟
        "description": "在线学习 — 增量模型权重调整 (train_only模式)",
        "command": (
            f'cd {BACKEND_DIR} && '
            f'{sys.executable} -m app.data_pipeline.pipeline_controller '
            f'--mode train --json'
            f' >> {LOG_DIR / "cron_online_learning.log"} 2>&1'
        ),
    },
]


def generate_crontab_lines() -> list[str]:
    """生成 crontab 格式的条目列表"""
    lines: list[str] = []
    lines.append("# ════════════════════════════════════════════════════════════")
    lines.append(f"# 数据管道 cron 任务 — 由 register_cron.py 自动生成")
    lines.append(f"# 生成时间: {datetime.now(timezone.utc).isoformat()}")
    lines.append(f"# 项目路径: {BACKEND_DIR}")
    lines.append(f"# Python: {sys.executable}")
    lines.append("# ════════════════════════════════════════════════════════════")
    lines.append("")
    lines.append(f"SHELL=/bin/bash")
    lines.append(f"PATH=/usr/local/bin:/usr/bin:/bin:{os.path.dirname(sys.executable)}")
    lines.append("")

    for cron in CRON_DEFINITIONS:
        comment = (
            f"# {cron['id']} — {cron['description']}"
        )
        lines.append(comment)
        lines.append(f"{cron['schedule']} {cron['command']}")
        lines.append("")

    return lines


def save_config(crontab_lines: list[str]) -> dict:
    """将注册的 cron 配置保存到 JSON 配置文件中以供审计"""
    os.makedirs(CRON_CONFIG_DIR, exist_ok=True)

    registered = []
    for cron in CRON_DEFINITIONS:
        registered.append({
            "id": cron["id"],
            "schedule": cron["schedule"],
            "description": cron["description"],
            "command": cron["command"],
            "registered_at": datetime.now(timezone.utc).isoformat(),
        })

    config = {
        "_meta": {
            "version": "1.0.0",
            "description": "数据管道cron任务注册表",
            "generated_by": "register_cron.py",
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "project_root": str(PROJECT_ROOT),
            "backend_dir": str(BACKEND_DIR),
            "python": sys.executable,
            "total_tasks": len(registered),
        },
        "crontab_file": str(CRON_CONFIG_DIR / "crontab"),
        "registered_tasks": registered,
    }

    with open(CRON_CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(config, f, ensure_ascii=False, indent=2)

    return config


def write_crontab_file(crontab_lines: list[str]) -> Path:
    """将 crontab 内容写出到文件"""
    crontab_path = CRON_CONFIG_DIR / "crontab"
    os.makedirs(CRON_CONFIG_DIR, exist_ok=True)

    with open(crontab_path, "w", encoding="utf-8") as f:
        f.writelines(line + "\n" for line in crontab_lines)

    return crontab_path


def install_crontab(crontab_path: Path) -> dict:
    """尝试将 crontab 文件安装到系统 crontab"""
    result = {
        "method": None,
        "success": False,
        "message": "",
    }

    # 方法 1: crontab 命令 (Linux/Mac/Git Bash)
    try:
        # 先获取现有 crontab (如果有)
        try:
            existing = subprocess.run(
                ["crontab", "-l"],
                capture_output=True, text=True, timeout=10,
            )
            existing_content = existing.stdout if existing.returncode == 0 else ""
        except (FileNotFoundError, subprocess.TimeoutExpired):
            existing_content = ""

        # 将本脚本的条目添加到现有 crontab
        with open(crontab_path, "r") as f:
            new_content = f.read()

        # 合并: 移除旧的 data-pipeline 条目, 保留其他
        merged_lines = []
        skip_block = False
        for line in existing_content.splitlines():
            if line.strip().startswith("# data-pipeline-") or line.strip().startswith("# ═════"):
                skip_block = True
                continue
            if skip_block:
                if line.strip() == "" or line.strip().startswith("#"):
                    # 仍处于注释块中
                    if "# 数据管道" in line or "# 生成时间" in line or "# 项目路径" in line or "# Python" in line:
                        continue
                    if line.strip().startswith("# ") and not line.strip().startswith("# data-pipeline-"):
                        skip_block = False  # 新注释块开始
                    continue
                skip_block = False
            merged_lines.append(line)

        # 追加新内容
        merged = "\n".join(merged_lines).strip()
        if merged:
            merged += "\n\n"
        merged += new_content

        # 安装
        proc = subprocess.run(
            ["crontab", "-"],
            input=merged,
            capture_output=True, text=True, timeout=10,
        )
        if proc.returncode == 0:
            result["method"] = "crontab"
            result["success"] = True
            result["message"] = f"成功安装 {len(CRON_DEFINITIONS)} 个 cron 任务到系统 crontab"
            return result
        else:
            result["message"] = f"crontab 安装失败: {proc.stderr.strip()}"
    except FileNotFoundError:
        result["message"] = "crontab 命令不可用 (非 Linux/Mac 环境)"

    # 方法 2: 仅写出 crontab 文件供用户手动安装
    result["method"] = "manual"
    result["success"] = True
    result["message"] = (
        f"crontab 文件已生成: {crontab_path}\n"
        f"请在 Git Bash 终端执行: crontab {crontab_path}\n"
        f"或手动将上述内容追加到: crontab -e"
    )

    return result


def remove_crons() -> dict:
    """移除本脚本注册的所有 cron 任务"""
    result = {
        "success": False,
        "message": "",
        "removed_count": 0,
    }

    try:
        proc = subprocess.run(
            ["crontab", "-l"],
            capture_output=True, text=True, timeout=10,
        )
        if proc.returncode != 0:
            result["message"] = "当前无 crontab 或 crontab 不可访问"
            result["success"] = True
            return result

        lines = proc.stdout.splitlines()
        filtered = []
        in_pipeline_block = False
        removed = 0

        for line in lines:
            if line.strip().startswith("# ═════") and "数据管道" in proc.stdout[proc.stdout.find(line):proc.stdout.find(line)+100]:
                in_pipeline_block = True
                removed += 1
                continue
            if in_pipeline_block:
                # 跳过空行和注释行直到遇到非 data-pipeline 的条目
                if line.strip() == "" or line.strip().startswith("#"):
                    continue
                # 检查是否是 data-pipeline 命令
                if "data-pipeline" in line or "pipeline_controller" in line or "pipeline_health_check" in line:
                    removed += 1
                    continue
                in_pipeline_block = False

            filtered.append(line)

        new_content = "\n".join(filtered)

        # 写回 crontab
        subprocess.run(
            ["crontab", "-"],
            input=new_content,
            capture_output=True, text=True, timeout=10,
        )

        result["success"] = True
        result["removed_count"] = removed
        result["message"] = f"已从 crontab 移除 {removed} 个条目"

        # 删除配置文件
        if CRON_CONFIG_FILE.exists():
            CRON_CONFIG_FILE.unlink()

    except FileNotFoundError:
        result["message"] = "crontab 命令不可用"

    return result


def main():
    parser = argparse.ArgumentParser(
        description="全自动cron任务注册 — 数据管道7×24定时任务",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument(
        "--dry-run", action="store_true",
        help="仅打印生成的 crontab 内容, 不安装",
    )
    parser.add_argument(
        "--print-cron-file", action="store_true",
        help="仅显示生成的 cron 配置文件路径",
    )
    parser.add_argument(
        "--remove", action="store_true",
        help="移除本脚本注册的所有 cron 任务",
    )
    parser.add_argument(
        "--json", action="store_true",
        help="以 JSON 格式输出结果",
    )

    args = parser.parse_args()

    # ── 移除模式 ──
    if args.remove:
        result = remove_crons()
        if args.json:
            print(json.dumps(result, ensure_ascii=False, indent=2))
        else:
            print("=" * 60)
            print("🗑️  Cron 移除结果")
            print("=" * 60)
            print(f"  状态: {'✅ 成功' if result['success'] else '❌ 失败'}")
            print(f"  移除: {result['removed_count']} 个条目")
            print(f"  消息: {result['message']}")
        sys.exit(0 if result["success"] else 1)

    # ── 生成 crontab 内容 ──
    crontab_lines = generate_crontab_lines()

    # ── 仅打印路径 ──
    if args.print_cron_file:
        crontab_path = write_crontab_file(crontab_lines)
        print(str(crontab_path))
        sys.exit(0)

    # ── Dry-run: 仅打印 ──
    if args.dry_run:
        print("\n".join(crontab_lines))
        sys.exit(0)

    # ── 正常注册模式 ──
    # 1. 写出 crontab 文件
    crontab_path = write_crontab_file(crontab_lines)

    # 2. 保存注册配置
    config = save_config(crontab_lines)

    # 3. 尝试安装到系统 crontab
    install_result = install_crontab(crontab_path)

    # 4. 输出结果
    result = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "status": "ok" if install_result["success"] else "warning",
        "total_tasks": len(CRON_DEFINITIONS),
        "installation": install_result,
        "config_file": str(CRON_CONFIG_FILE),
        "crontab_file": str(crontab_path),
        "tasks": [
            {
                "id": c["id"],
                "schedule": c["schedule"],
                "description": c["description"],
            }
            for c in CRON_DEFINITIONS
        ],
        "log_directory": str(LOG_DIR),
    }

    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print("=" * 60)
        print("📋  数据管道 cron 任务注册结果")
        print("=" * 60)
        print(f"  注册任务: {len(CRON_DEFINITIONS)} 个")
        print(f"  ─────────────────────────────────────────────")
        for c in CRON_DEFINITIONS:
            print(f"  📌 {c['id']}")
            print(f"     调度: {c['schedule']}")
            print(f"     说明: {c['description']}")
        print(f"  ─────────────────────────────────────────────")
        print(f"  配置保存: {CRON_CONFIG_FILE}")
        print(f"  crontab文件: {crontab_path}")
        print(f"  安装方式: {install_result['method']}")
        print(f"  安装结果: {'✅ 成功' if install_result['success'] else '❌ 失败'}")
        print(f"  消息: {install_result['message']}")
        print(f"  日志目录: {LOG_DIR}")
        print("=" * 60)

    sys.exit(0 if install_result["success"] else 1)


if __name__ == "__main__":
    main()
