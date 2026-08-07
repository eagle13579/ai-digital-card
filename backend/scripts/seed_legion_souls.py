#!/usr/bin/env python3
"""seed_legion_souls.py — 为军团 9 类员工在服务器上生成灵魂目录

把 ai-shuzhi 模板池（4 部门 soul-injection + memory.db）和 roster.json
的员工档案，按 legion_employee.py 期望的结构生成:
    LEGION_PATH/emp-{name}/employee.yaml
    LEGION_PATH/emp-{name}/soul-injection.yaml
    LEGION_PATH/emp-{name}/memory/memory.db

用法:
    python3 seed_legion_souls.py          # 生成/更新全部 9 员工灵魂
    python3 seed_legion_souls.py --dry    # 预览不写入
"""
from __future__ import annotations

import argparse
import json
import os
import shutil
import sys
from pathlib import Path

LEGION_PATH = Path("/app/gaia-commercial/apps/services/ai_legion/employees")
ROSTER = Path("/app/gaia-commercial/apps/services/ai_legion/employees/roster.json")
TEMPLATE_POOL = Path("/var/www/ai-shuzhi-com/template_pool/_base_templates")

# 9 类员工 → 模板部门映射（用最接近的专业方向灵魂）
EMPLOYEE_TEMPLATE_MAP: dict[str, str] = {
    "emp-烛龙": "research",      # Backend — 研发型灵魂
    "emp-狴犴": "compliance",    # QA — 严谨审查型灵魂
    "emp-獬豸": "compliance",    # Security — 合规安全型灵魂
    "emp-乘黄": "acquisition",   # Growth — 增长获客型灵魂
    "emp-文鳐": "research",      # Knowledge — 知识研究型灵魂
    "emp-开明兽": "research",    # Architecture — 架构研究型灵魂
    "emp-计然": "research",      # Data — 数据分析型灵魂
    "emp-䑏疏": "research",      # SRE — 技术运维型灵魂
    "emp-白泽": "ai_assistant",  # Support — 助理型灵魂
}


def load_roster() -> dict:
    with open(ROSTER, encoding="utf-8") as f:
        return json.load(f)


def find_employee_in_roster(roster: dict, emp_name: str) -> dict | None:
    """在 roster.json（按部门分组）中找到对应员工档案。"""
    for dept, members in roster.items():
        if dept == "_meta" or not isinstance(members, list):
            continue
        for m in members:
            if m.get("name") == emp_name or (m.get("emp_id") or "").startswith(f"emp-{emp_name}"):
                return m
    return None


def build_employee_yaml(emp: dict | None, template_dept: str) -> str:
    """构造 employee.yaml（合并 roster 档案 + 模板角色）。"""
    name = emp.get("name", "") if emp else ""
    role = (emp.get("title") or "") if emp else ""
    capabilities = emp.get("capabilities", []) if emp else []
    caps_lines = "\n".join(f'    - "{c}"' for c in capabilities[:8]) or '    - "通用能力"'
    return f"""# ============================================================
# 员工配置 (服务器版 — 由 seed_legion_souls.py 生成)
# 灵魂模板: {template_dept}
# ============================================================

employee:
  id: "emp-{name}"
  name: "{name}"
  role: "{role or template_dept}"
  description: "AI数字军团 {template_dept} 方向员工"
  soul_source: "{template_dept}-template"

  # --- 能力配置 ---
  capabilities:
{caps_lines}

  # --- 人格设定 ---
  personality: "专业、尽责、持续学习"

  # --- 母体引用: 服务器版不依赖本地 ---
  mother_references: []

  # --- 初始化参数 ---
  init_params:
    max_concurrent_tasks: 10
    learning_enabled: true
    gaia_backfeed_enabled: true
"""


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry", action="store_true", help="预览不写入")
    args = ap.parse_args()

    if not TEMPLATE_POOL.is_dir():
        print(f"❌ 模板池不存在: {TEMPLATE_POOL}")
        return 1

    roster = load_roster()
    created, updated, skipped = 0, 0, 0

    for emp_key, template_dept in EMPLOYEE_TEMPLATE_MAP.items():
        # emp_key 形如 "emp-烛龙"，目录名直接用（勿再拼 emp- 前缀）
        emp_dir = LEGION_PATH / emp_key
        emp_name = emp_key[4:]  # 去掉 "emp-" 前缀，得到 "烛龙"
        tmpl = TEMPLATE_POOL / template_dept

        # 检查模板文件
        tmpl_employee = tmpl / "employee.yaml"
        tmpl_soul = tmpl / "soul-injection.yaml"
        tmpl_mem = tmpl / "memory" / "memory.db"
        if not (tmpl_employee.exists() and tmpl_soul.exists()):
            print(f"  [SKIP] {emp_key}: 模板 {template_dept} 不完整")
            skipped += 1
            continue

        if args.dry:
            print(f"  [DRY] {emp_key} ← {template_dept} 模板")
            created += 1
            continue

        emp_dir.mkdir(parents=True, exist_ok=True)
        (emp_dir / "memory").mkdir(parents=True, exist_ok=True)

        # 1. employee.yaml — 用 roster 档案增强
        emp = find_employee_in_roster(roster, emp_name)
        yaml_content = build_employee_yaml(emp, template_dept)
        (emp_dir / "employee.yaml").write_text(yaml_content, encoding="utf-8")

        # 2. soul-injection.yaml — 直接复制模板
        shutil.copy2(tmpl_soul, emp_dir / "soul-injection.yaml")

        # 3. memory.db — 复制模板记忆（空库或初始记忆）
        if tmpl_mem.exists():
            shutil.copy2(tmpl_mem, emp_dir / "memory" / "memory.db")

        created += 1
        print(f"  [✓] {emp_name} ← {template_dept} (employee.yaml + soul + memory.db)")

    print(f"\n✅ 完成: 生成 {created} / 跳过 {skipped} → {LEGION_PATH}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
