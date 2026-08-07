#!/usr/bin/env python3
"""seed_all_souls.py — 为军团全员（158 员工）生成灵魂目录

把 roster.json 全部员工（general/compliance/research/acquisition/ai_assistant）
按部门映射到模板池灵魂，生成:
    LEGION_PATH/emp-{name}-{suffix}/employee.yaml
    LEGION_PATH/emp-{name}-{suffix}/soul-injection.yaml
    LEGION_PATH/emp-{name}-{suffix}/memory/memory.db

用法:
    python3 seed_all_souls.py           # 生成/更新全部员工灵魂
    python3 seed_all_souls.py --dry     # 预览不写入
    python3 seed_all_souls.py --dept research  # 只生成某部门
    python3 seed_all_souls.py --limit 20       # 只生成前 20 个（测试）
"""
from __future__ import annotations

import argparse
import json
import os
import shutil
import sys
from pathlib import Path

LEGION_PATH = Path("/app/gaia-commercial/apps/services/ai_legion/employees")
ROSTER = LEGION_PATH / "roster.json"
TEMPLATE_POOL = Path("/var/www/ai-shuzhi-com/template_pool/_base_templates")

# 部门 → 模板映射（roster 的 department key → 模板池目录）
DEPT_TEMPLATE_MAP: dict[str, str] = {
    "compliance": "compliance",
    "research": "research",
    "acquisition": "acquisition",
    "ai_assistant": "ai_assistant",
    "general": "research",  # 通用员工用研究型灵魂（含持续学习人格）
}

# 已存在的 9 核心员工（跳过，保持现有灵魂不被覆盖）
CORE_EMPLOYEES = {
    "烛龙", "狴犴", "獬豸", "乘黄", "文鳐", "开明兽", "计然", "䑏疏", "白泽",
}


def load_roster() -> dict:
    with open(ROSTER, encoding="utf-8") as f:
        return json.load(f)


def build_employee_yaml(emp: dict, template_dept: str) -> str:
    """构造 employee.yaml（合并 roster 档案 + 模板角色）。"""
    name = emp.get("name", "") or ""
    role = emp.get("title", "") or ""
    dept = emp.get("department", "") or ""
    capabilities = emp.get("capabilities", []) or []
    caps_lines = "\n".join(f'    - "{c}"' for c in capabilities[:12]) or '    - "通用能力"'
    emp_id = emp.get("emp_id", "") or f"emp-{name}"

    return f"""# ============================================================
# 员工配置 (全员版 — 由 seed_all_souls.py 生成)
# 灵魂模板: {template_dept}
# roster: {emp_id}
# ============================================================

employee:
  id: "{emp_id}"
  name: "{name}"
  role: "{role or template_dept}"
  department: "{dept}"
  description: "AI数字军团 {template_dept} 方向员工 — 全员共享学习激活"
  soul_source: "{template_dept}-template"

  # --- 能力配置 ---
  capabilities:
{caps_lines}

  # --- 人格设定 ---
  personality: "专业、尽责、持续学习、乐于分享"

  # --- 共享学习协议 (全员三件套) ---
  shared_learning:
    enabled: true
    sync_cron: "*/30 * * * *"
    share_tool: "share_knowledge"
    sync_tool: "sync_knowledge"

  # --- 母体引用: 服务器版不依赖本地 ---
  mother_references: []

  # --- 初始化参数 ---
  init_params:
    max_concurrent_tasks: 5
    learning_enabled: true
    gaia_backfeed_enabled: true
"""


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry", action="store_true", help="预览不写入")
    ap.add_argument("--dept", type=str, default="", help="只生成某部门 (compliance/research/acquisition/ai_assistant/general)")
    ap.add_argument("--limit", type=int, default=0, help="只生成前 N 个（测试）")
    ap.add_argument("--force", action="store_true", help="覆盖已存在的员工目录")
    args = ap.parse_args()

    if not TEMPLATE_POOL.is_dir():
        print(f"❌ 模板池不存在: {TEMPLATE_POOL}")
        return 1
    if not ROSTER.exists():
        print(f"❌ roster 不存在: {ROSTER}")
        return 1

    roster = load_roster()
    created, skipped = 0, 0

    for dept_key, members in roster.items():
        if dept_key == "_meta" or not isinstance(members, list):
            continue
        if args.dept and dept_key != args.dept:
            continue

        template_dept = DEPT_TEMPLATE_MAP.get(dept_key, "research")
        tmpl = TEMPLATE_POOL / template_dept
        tmpl_employee = tmpl / "employee.yaml"
        tmpl_soul = tmpl / "soul-injection.yaml"
        tmpl_mem = tmpl / "memory" / "memory.db"
        if not (tmpl_employee.exists() and tmpl_soul.exists()):
            print(f"  [SKIP] 部门 {dept_key}: 模板 {template_dept} 不完整")
            skipped += 1
            continue

        for emp in members:
            name = emp.get("name", "") or ""
            emp_id = emp.get("emp_id", "") or ""
            # 跳过 9 核心（已有专属灵魂）
            if name in CORE_EMPLOYEES:
                skipped += 1
                continue

            # 目录名：用 emp_id（含后缀唯一），若为空用 emp-{name}
            dir_name = emp_id if emp_id else f"emp-{name}"
            emp_dir = LEGION_PATH / dir_name

            if emp_dir.exists() and not args.force:
                skipped += 1
                continue

            if args.dry:
                print(f"  [DRY] {dir_name} ← {template_dept} 模板")
                created += 1
                continue

            try:
                emp_dir.mkdir(parents=True, exist_ok=True)
                (emp_dir / "memory").mkdir(parents=True, exist_ok=True)

                # 1. employee.yaml — 用 roster 档案增强
                (emp_dir / "employee.yaml").write_text(
                    build_employee_yaml(emp, template_dept), encoding="utf-8"
                )

                # 2. soul-injection.yaml — 复制模板
                shutil.copy2(tmpl_soul, emp_dir / "soul-injection.yaml")

                # 3. memory.db — 复制模板记忆（空库或初始记忆）
                if tmpl_mem.exists():
                    shutil.copy2(tmpl_mem, emp_dir / "memory" / "memory.db")

                created += 1
                if created % 20 == 0:
                    print(f"  ... 已生成 {created} 个 ({dir_name})")
            except Exception as exc:  # noqa: BLE001
                print(f"  [ERR] {dir_name}: {exc}")
                skipped += 1

            if args.limit and created >= args.limit:
                break
        if args.limit and created >= args.limit:
            break

    print(f"\n✅ 完成: 生成 {created} / 跳过 {skipped} → {LEGION_PATH}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
