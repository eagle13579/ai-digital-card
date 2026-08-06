#!/usr/bin/env python3
"""
windows_rpa_importer.py — Windows RPA 客户数据批量导入管道主入口

通过 Windows RPA 微服务 (:8667) 模拟人工操作，将 Excel/CSV 客户数据
批量导入目标 ERP/CRM 系统。支持中断恢复、进度追踪。

用法:
    # 查看帮助
    python windows_rpa_importer.py --help

    # 导入客户数据到 ERP 系统
    python windows_rpa_importer.py import customers.xlsx --system erp_demo

    # 导入到 CRM Web 系统，带中断恢复
    python windows_rpa_importer.py import customers.csv --system crm_web_demo --resume

    # 干跑模式（仅验证数据）
    python windows_rpa_importer.py import customers.csv --system erp_demo --dry-run

    # 列出可用系统和检查点
    python windows_rpa_importer.py list-systems
    python windows_rpa_importer.py list-sessions

    # 查看导入进度
    python windows_rpa_importer.py status <session_id>
"""

from __future__ import annotations

import argparse
import json
import logging
import os
import sys
import time
from pathlib import Path
from typing import Any

# ── 确保直接执行时路径可达 ─────────────────────────────────────────────
_SCRIPT_DIR = Path(__file__).parent.resolve()
if str(_SCRIPT_DIR.parent) not in sys.path:
    sys.path.insert(0, str(_SCRIPT_DIR.parent))

from checkpoint import CheckpointManager, format_progress_bar  # noqa: E402
from config import ImportConfig  # noqa: E402
from data_reader import read_customers, summarize_columns  # noqa: E402
from import_workflow import CRMWebImport, ERPWebImport  # noqa: E402
from rpa_client import RpaClient  # noqa: E402

# ── 日志配置 ──────────────────────────────────────────────────────────────

LOG_FORMAT = "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
DATE_FORMAT = "%H:%M:%S"


def setup_logging(verbose: bool = False) -> None:
    """配置日志输出"""
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format=LOG_FORMAT,
        datefmt=DATE_FORMAT,
        handlers=[
            logging.StreamHandler(sys.stdout),
        ],
    )


# ── 默认路径 ──────────────────────────────────────────────────────────────

DEFAULT_CHECKPOINT_DIR = Path(_SCRIPT_DIR) / "checkpoints"
DEFAULT_CONFIG_PATH = Path(_SCRIPT_DIR) / "systems_config.json"


# ══════════════════════════════════════════════════════════════════════════
# 子命令实现
# ══════════════════════════════════════════════════════════════════════════


def cmd_import(args: argparse.Namespace) -> int:
    """执行导入流程"""
    logger = logging.getLogger("importer")

    # ── 初始化各组件 ──
    rpa = RpaClient(base_url=args.rpa_url)

    # 检查 RPA 服务是否存活
    if not args.dry_run:
        try:
            health = rpa.health()
            logger.info("RPA 服务状态: %s", health)
        except Exception as e:
            logger.error("RPA 服务不可用 (%s) — 请确认 :8667 已启动", e)
            return 1

    # 加载配置
    config_mgr = ImportConfig(config_path=args.config)
    try:
        system_config = config_mgr.get(args.system)
    except KeyError as e:
        logger.error("%s", e)
        return 1

    # 验证配置
    errors = config_mgr.validate_config(args.system)
    if errors:
        logger.warning("系统配置验证发现以下问题:")
        for err in errors:
            logger.warning("  - %s", err)
        if not args.force:
            logger.warning("使用 --force 强制继续")
            return 1

    # 检查点
    checkpoint_dir = Path(args.checkpoint_dir) if args.checkpoint_dir else DEFAULT_CHECKPOINT_DIR
    cp_mgr = CheckpointManager(checkpoint_dir)

    # ── 读取客户数据 ──
    file_path = args.file
    if not os.path.exists(file_path):
        logger.error("文件不存在: %s", file_path)
        return 1

    logger.info("读取客户数据: %s", file_path)
    all_records: list[dict[str, str]] = []
    summary: dict[str, Any] = {"total": 0}
    gen = read_customers(file_path, chunk_size=500)
    try:
        while True:
            batch = next(gen)
            all_records.extend(batch)
    except StopIteration as e:
        summary = e.value if e.value else {"total": len(all_records)}
    except Exception as e:
        logger.error("读取文件失败: %s", e)
        return 1

    total = len(all_records)
    if total == 0:
        logger.error("文件中没有客户数据")
        return 1

    logger.info("共读取 %d 条客户记录", total)
    columns = set()
    for rec in all_records:
        columns.update(rec.keys())
    col_info = summarize_columns(list(columns))
    logger.info("检测到字段: %s", ", ".join(f"{k}({v})" for k, v in col_info.items()))

    # ── 创建导入工作流 ──
    system_type = system_config.get("type", "erp").lower()
    field_mapping_raw = args.field_mapping
    field_mapping: dict[str, str] = {}
    if field_mapping_raw:
        for pair in field_mapping_raw:
            if "=" in pair:
                data_field, form_field = pair.split("=", 1)
                field_mapping[data_field.strip()] = form_field.strip()

    if system_type == "crm":
        workflow = CRMWebImport(
            rpa_client=rpa,
            checkpoint_mgr=cp_mgr,
            config=system_config,
            system_name=args.system,
            field_mapping=field_mapping or None,
        )
    else:
        workflow = ERPWebImport(
            rpa_client=rpa,
            checkpoint_mgr=cp_mgr,
            config=system_config,
            system_name=args.system,
            field_mapping=field_mapping or None,
        )

    # ── 生成会话 ID ──
    timestamp = time.strftime("%Y%m%d_%H%M%S")
    session_id = f"{args.system}_{Path(file_path).stem}_{timestamp}"

    # ── 执行导入 ──
    logger.info("=" * 60)
    logger.info("  导入会话: %s", session_id)
    logger.info("  目标系统: %s (%s)", system_config.get("display_name", args.system), system_type)
    logger.info("  源文件:   %s", file_path)
    logger.info("  记录数:   %d", total)
    if args.dry_run:
        logger.info("  模式:     DRY RUN (仅验证)")
    if args.resume:
        logger.info("  模式:     从中断恢复")
    logger.info("=" * 60)

    try:
        cp = workflow.run(
            records=all_records,
            session_id=session_id,
            source_file=file_path,
            resume=args.resume,
            dry_run=args.dry_run,
        )
    except KeyboardInterrupt:
        logger.warning("用户中断导入")
        return 130
    except Exception as e:
        logger.error("导入异常终止: %s", e, exc_info=True)
        return 1

    # ── 最终摘要 ──
    s = cp_mgr.summary(cp)
    print()
    print("=" * 60)
    print("  导入完成摘要")
    print("=" * 60)
    print(f"  会话 ID:    {s['session_id']}")
    print(f"  总计:       {s['total']}")
    print(f"  已完成:     {s['completed']}")
    print(f"  失败:       {s['failed']}")
    print(f"  进度:       {s['progress_pct']}%")
    print(f"  耗时:       {s['elapsed_seconds']:.1f}s")
    print(f"  可恢复索引: {s['resume_index']}")
    print("=" * 60)

    return 0


def cmd_list_systems(args: argparse.Namespace) -> int:
    """列出可用的目标系统配置"""
    config_mgr = ImportConfig(config_path=args.config)
    systems = config_mgr.list_systems()

    print(f"{'系统名':<20} {'显示名称':<25} {'描述':<30}")
    print("-" * 75)
    for sys_info in systems:
        print(f"{sys_info['name']:<20} {sys_info['display_name']:<25} {sys_info['description']:<30}")
    return 0


def cmd_list_sessions(args: argparse.Namespace) -> int:
    """列出所有导入会话"""
    checkpoint_dir = Path(args.checkpoint_dir) if args.checkpoint_dir else DEFAULT_CHECKPOINT_DIR
    cp_mgr = CheckpointManager(checkpoint_dir)
    sessions = cp_mgr.list_sessions()

    if not sessions:
        print(f"没有找到导入会话（检查点目录: {checkpoint_dir}）")
        return 0

    print(f"{'会话ID':<35} {'源文件':<30} {'进度':<10} {'成功/总计':<12}")
    print("-" * 90)
    for s in sessions:
        progress = f"{s['progress'] * 100:.0f}%"
        ratio = f"{s['completed_count']}/{s['total_records']}"
        print(f"{s['session_id']:<35} {Path(s['source_file']).name:<30} {progress:<10} {ratio:<12}")
    return 0


def cmd_session_status(args: argparse.Namespace) -> int:
    """查看单个会话的状态详情"""
    checkpoint_dir = Path(args.checkpoint_dir) if args.checkpoint_dir else DEFAULT_CHECKPOINT_DIR
    cp_mgr = CheckpointManager(checkpoint_dir)
    cp = cp_mgr.load_session(args.session_id)

    if cp is None:
        print(f"会话不存在: {args.session_id}")
        return 1

    s = cp_mgr.summary(cp)
    print(json.dumps(s, ensure_ascii=False, indent=2))
    print()
    print("各记录状态:")
    print(f"{'索引':<8} {'状态':<15} {'名称':<25} {'消息':<30}")
    print("-" * 80)
    for i, record in enumerate(cp.records):
        name = record.raw_data.get("name", record.raw_data.get("company", f"记录#{i}"))
        print(f"{i:<8} {record.status:<15} {name[:24]:<25} {record.message[:29]:<30}")
    return 0


# ══════════════════════════════════════════════════════════════════════════
# CLI 入口
# ══════════════════════════════════════════════════════════════════════════


def build_parser() -> argparse.ArgumentParser:
    """构建命令行参数解析器"""
    parser = argparse.ArgumentParser(
        prog="windows_rpa_importer.py",
        description="Windows RPA 客户数据批量导入管道 — 通过RPA微服务(:8667)模拟人工操作导入客户数据",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  python windows_rpa_importer.py import customers.xlsx --system erp_demo
  python windows_rpa_importer.py import customers.csv --system crm_web_demo --resume
  python windows_rpa_importer.py import customers.xlsx --system erp_demo --dry-run
  python windows_rpa_importer.py list-systems
  python windows_rpa_importer.py list-sessions
  python windows_rpa_importer.py status erp_demo_customers_20260729_120000
        """,
    )
    parser.add_argument("--verbose", "-v", action="store_true", help="详细日志输出")
    parser.add_argument(
        "--rpa-url",
        default="http://localhost:8667",
        help="RPA 微服务地址 (默认: http://localhost:8667)",
    )
    parser.add_argument(
        "--checkpoint-dir",
        default=None,
        help="检查点存储目录 (默认: ./checkpoints)",
    )
    parser.add_argument(
        "--config",
        default=None,
        help="外部系统配置文件路径 (.json / .yaml)",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="即使配置验证有警告也强制继续",
    )

    subparsers = parser.add_subparsers(dest="command", help="子命令")

    # ── import ──
    import_parser = subparsers.add_parser("import", help="导入客户数据到目标系统")
    import_parser.add_argument("file", help="客户数据文件路径 (.csv / .xlsx)")
    import_parser.add_argument(
        "--system", "-s",
        required=True,
        help="目标系统名称（使用 list-systems 查看可用系统）",
    )
    import_parser.add_argument(
        "--resume", "-r",
        action="store_true",
        help="从中断点恢复导入",
    )
    import_parser.add_argument(
        "--dry-run",
        action="store_true",
        help="干跑模式 — 仅验证数据，不进行实际 RPA 操作",
    )
    import_parser.add_argument(
        "--field-mapping", "-m",
        action="append",
        help="字段映射: 数据字段=表单字段 (可多次使用，如 -m name=姓名 -m phone=电话)",
    )

    # ── list-systems ──
    subparsers.add_parser("list-systems", help="列出所有可用的目标系统配置")

    # ── list-sessions ──
    subparsers.add_parser("list-sessions", help="列出所有导入会话")

    # ── status ──
    status_parser = subparsers.add_parser("status", help="查看导入会话状态详情")
    status_parser.add_argument("session_id", help="会话 ID")

    return parser


def main(argv: list[str] | None = None) -> int:
    """主入口"""
    parser = build_parser()
    args = parser.parse_args(argv)

    setup_logging(verbose=args.verbose)

    if args.command == "import":
        return cmd_import(args)
    elif args.command == "list-systems":
        return cmd_list_systems(args)
    elif args.command == "list-sessions":
        return cmd_list_sessions(args)
    elif args.command == "status":
        return cmd_session_status(args)
    else:
        parser.print_help()
        return 0


if __name__ == "__main__":
    sys.exit(main())
