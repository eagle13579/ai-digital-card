#!/usr/bin/env python
"""
check_coverage_gate.py — CI覆盖率门禁验证脚本

验证 pyproject.toml 中 [tool.coverage.report] fail_under >= 80
确保 CI 门禁已生效。

用法:
  python scripts/check_coverage_gate.py          # 检查 backend/pyproject.toml
  python scripts/check_coverage_gate.py --path backend/pyproject.toml  # 指定路径

退出码:
  0 = 门禁已生效 (fail_under >= 80)
  1 = 门禁未生效或文件不存在
  2 = 配置解析错误
"""

import argparse
import re
import sys
from pathlib import Path


def get_project_root() -> Path:
    """获取项目根目录 (脚本所在目录的父目录)"""
    return Path(__file__).resolve().parent.parent


def parse_fail_under(pyproject_path: Path) -> int | None:
    """
    从 pyproject.toml 解析 fail_under 值。
    支持两种格式:
      1. 标准 TOML: fail_under = 80
      2. 带注释: fail_under = 80  # minimum coverage
    """
    if not pyproject_path.exists():
        print(f"[ERROR] 文件不存在: {pyproject_path}")
        return None

    content = pyproject_path.read_text(encoding="utf-8")

    # 找到 [tool.coverage.report] 段落后搜索 fail_under
    in_coverage_report = False
    fail_under_value = None

    for line in content.splitlines():
        stripped = line.strip()

        # 检测段首
        if stripped.startswith("[tool.coverage.report]"):
            in_coverage_report = True
            continue
        # 离开当前段
        if in_coverage_report and stripped.startswith("["):
            break

        if in_coverage_report:
            # 匹配 fail_under = <number>  可能带注释
            m = re.match(r"fail_under\s*=\s*(\d+)(?:\s*#.*)?$", stripped)
            if m:
                fail_under_value = int(m.group(1))
                break

    # 如果没找到，尝试全局搜索（兼容不同格式）
    if fail_under_value is None:
        for line in content.splitlines():
            m = re.match(r"^\s*fail_under\s*=\s*(\d+)", line)
            if m:
                fail_under_value = int(m.group(1))
                break

    return fail_under_value


def check_gate(pyproject_path: Path, min_coverage: int = 80) -> bool:
    """
    验证覆盖率门禁是否生效。

    Args:
        pyproject_path: pyproject.toml 路径
        min_coverage: 最低覆盖率要求 (默认: 80)

    Returns:
        True 门禁生效, False 门禁未生效
    """
    print(f"\n{'=' * 50}")
    print(f"  CI 覆盖率门禁验证")
    print(f"{'=' * 50}")
    print(f"  配置文件: {pyproject_path}")
    print(f"  最低要求: {min_coverage}%")
    print(f"  {'─' * 40}")

    fail_under = parse_fail_under(pyproject_path)

    if fail_under is None:
        print(f"  [FAIL] 未找到 fail_under 配置项")
        print(f"  {'=' * 50}")
        return False

    print(f"  当前配置: fail_under = {fail_under}")

    if fail_under >= min_coverage:
        print(f"  {'=' * 40}")
        print(f"  ✅ CI覆盖率门禁 {fail_under}% 已生效")
        print(f"  {'=' * 50}")
        return True
    else:
        print(f"  [WARN] fail_under ({fail_under}) < 最低要求 ({min_coverage})")
        print(f"  {'=' * 50}")
        return False


def main():
    parser = argparse.ArgumentParser(
        description="CI覆盖率门禁验证 — 检查 pyproject.toml 中 fail_under >= 80"
    )
    parser.add_argument(
        "--path",
        type=str,
        default="",
        help="pyproject.toml 路径 (默认: backend/pyproject.toml)",
    )
    parser.add_argument(
        "--min-coverage",
        type=int,
        default=80,
        help="最低覆盖率要求 (默认: 80)",
    )
    args = parser.parse_args()

    if args.path:
        pyproject_path = Path(args.path)
    else:
        project_root = get_project_root()
        pyproject_path = project_root / "backend" / "pyproject.toml"

    success = check_gate(pyproject_path, min_coverage=args.min_coverage)
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
