#!/usr/bin/env python
"""
统一数据管道健康检查脚本

检查项:
  1. data_pipeline/ 所有 .py 文件语法正确性 (compile 检查)
  2. data_source_registry.json 是否存在且 JSON 有效
  3. model_registry.json 是否需要初始化
  4. data/ 目录下关键文件是否存在 (training_data.json, online_weights.json 等)
  5. data_curator_state.json 状态是否正常

输出: JSON 格式报告到 stdout
退出码: 0 = 健康, 1 = 存在至少一个问题
"""
import ast
import json
import os
import sys
from pathlib import Path

# ── 路径配置 ──────────────────────────────────────────────
HERE = Path(__file__).parent.resolve()                      # app/data_pipeline/
APP_DIR = HERE.parent.resolve()                              # app/
BACKEND_DIR = APP_DIR.parent.resolve()                      # backend/
DATA_DIR = BACKEND_DIR / "data"                              # backend/data/
APP_DATA_DIR = APP_DIR / "data"                              # app/data/


def check_py_files_syntax() -> dict:
    """检查 data_pipeline/ 下所有 .py 文件语法是否正确"""
    issues = []
    files_checked = 0

    for pyfile in sorted(HERE.glob("*.py")):
        files_checked += 1
        try:
            with open(pyfile, "r", encoding="utf-8") as f:
                source = f.read()
            ast.parse(source, filename=str(pyfile))
        except SyntaxError as e:
            issues.append({
                "file": str(pyfile.name),
                "error": f"SyntaxError: {e.msg} (line {e.lineno}, col {e.offset})",
            })

    status = "ok" if not issues else "error"
    return {
        "check": "py_files_syntax",
        "status": status,
        "detail": {
            "files_checked": files_checked,
            "errors": len(issues),
        },
        "issues": issues,
    }


def check_data_source_registry() -> dict:
    """检查 data_source_registry.json 是否存在且 JSON 有效"""
    issues = []
    registry_path = HERE / "data_source_registry.json"

    if not registry_path.exists():
        return {
            "check": "data_source_registry",
            "status": "error",
            "detail": {"error": "文件不存在"},
            "issues": [{"file": "data_source_registry.json", "error": "文件不存在"}],
        }

    try:
        with open(registry_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        # 验证基本结构
        if "sources" not in data:
            issues.append({"error": "缺少 'sources' 根键"})
        if "_meta" not in data:
            issues.append({"error": "缺少 '_meta' 元信息"})

        source_count = len(data.get("sources", {}))
        status = "ok" if not issues else "warning"
        return {
            "check": "data_source_registry",
            "status": status,
            "detail": {
                "path": str(registry_path),
                "sources_count": source_count,
                "valid_json": True,
            },
            "issues": issues,
        }
    except json.JSONDecodeError as e:
        return {
            "check": "data_source_registry",
            "status": "error",
            "detail": {"error": f"JSON 解析失败: {e}"},
            "issues": [{"file": "data_source_registry.json", "error": f"JSON 解析失败: {e}"}],
        }


def check_model_registry() -> dict:
    """检查 model_registry.json 是否需要初始化"""
    registry_path = HERE / "model_registry.json"

    if not registry_path.exists():
        return {
            "check": "model_registry",
            "status": "warning",
            "detail": {"message": "model_registry.json 不存在，需要初始化"},
            "issues": [{
                "file": "model_registry.json",
                "error": "文件不存在，请运行 python -m app.data_pipeline.model_registry 初始化",
            }],
        }

    try:
        with open(registry_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        models = data.get("models", {})
        if not models:
            return {
                "check": "model_registry",
                "status": "warning",
                "detail": {"message": "model_registry.json 存在但无模型注册记录"},
                "issues": [{"error": "注册表为空，无模型注册记录"}],
            }

        return {
            "check": "model_registry",
            "status": "ok",
            "detail": {
                "path": str(registry_path),
                "models_count": len(models),
                "model_ids": list(models.keys()),
            },
            "issues": [],
        }
    except json.JSONDecodeError as e:
        return {
            "check": "model_registry",
            "status": "error",
            "detail": {"error": f"JSON 解析失败: {e}"},
            "issues": [{"file": "model_registry.json", "error": f"JSON 解析失败: {e}"}],
        }


def check_data_directory() -> dict:
    """检查 data/ 目录下关键训练数据文件是否存在"""
    issues = []
    found = []
    missing = []

    # 关键文件清单 (从 model_registry.py 中提取的 model_file 路径)
    critical_files = [
        ("training_data.json", DATA_DIR / "training_data.json"),
        ("online_weights.json", DATA_DIR / "online_weights.json"),
        ("v2_training_data.json", DATA_DIR / "v2_training_data.json"),
    ]

    for name, path in critical_files:
        if path.exists():
            found.append({
                "name": name,
                "path": str(path),
                "size_bytes": path.stat().st_size,
            })
        else:
            missing.append({"name": name, "expected_path": str(path)})
            issues.append({"error": f"关键文件缺失: {name} (期望路径: {path})"})

    status = "ok" if not missing else "warning"
    return {
        "check": "data_directory",
        "status": status,
        "detail": {
            "data_dir": str(DATA_DIR),
            "found": len(found),
            "missing": len(missing),
            "files": {
                "found": found,
                "missing": [m["name"] for m in missing],
            },
        },
        "issues": issues,
    }


def check_curator_state() -> dict:
    """检查 data_curator_state.json 状态是否正常

    查找以下路径 (优先第一个存在的):
      1. .data_curator_state.json (隐藏文件, data_curator.py 中定义)
      2. data_curator_state.json (无点前缀)
    """
    issues = []

    # 搜索可能的路径
    candidates = [
        HERE / ".data_curator_state.json",
        HERE / "data_curator_state.json",
    ]

    state_path = None
    for p in candidates:
        if p.exists():
            state_path = p
            break

    if state_path is None:
        issues.append({
            "error": "data_curator_state.json 不存在 (首次运行将自动创建)",
            "hint": "data_curator 模块将在首次数据去重时自动创建该文件",
        })
        return {
            "check": "curator_state",
            "status": "warning",
            "detail": {
                "message": "状态文件不存在 — 首次运行时将自动创建",
                "searched": [str(p) for p in candidates],
            },
            "issues": issues,
        }

    try:
        with open(state_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        # 状态文件应该是一个 dict (seen_hashes)
        if not isinstance(data, dict):
            issues.append({"error": "状态文件格式异常: 期望 JSON 对象 (dict)"})

        total_records = len(data)
        # 检查是否损坏 (所有值应为时间戳)
        corrupted = 0
        for k, v in data.items():
            if not isinstance(v, (int, float)):
                corrupted += 1
        if corrupted > 0:
            issues.append({"error": f"状态文件中 {corrupted} 条记录的值为非时间戳类型"})

        status = "ok" if not issues else "warning"
        return {
            "check": "curator_state",
            "status": status,
            "detail": {
                "path": str(state_path),
                "total_unique_records": total_records,
                "corrupted_entries": corrupted,
                "file_size_bytes": state_path.stat().st_size,
            },
            "issues": issues,
        }
    except json.JSONDecodeError as e:
        return {
            "check": "curator_state",
            "status": "error",
            "detail": {"error": f"JSON 解析失败: {e}"},
            "issues": [{"file": str(state_path), "error": f"JSON 解析失败: {e}"}],
        }


def run_all_checks() -> dict:
    """执行所有健康检查并汇总报告"""
    checks = [
        check_py_files_syntax(),
        check_data_source_registry(),
        check_model_registry(),
        check_data_directory(),
        check_curator_state(),
    ]

    total = len(checks)
    ok_count = sum(1 for c in checks if c["status"] == "ok")
    warning_count = sum(1 for c in checks if c["status"] == "warning")
    error_count = sum(1 for c in checks if c["status"] == "error")

    # 聚合所有 issues
    all_issues = []
    for c in checks:
        for issue in c.get("issues", []):
            issue["check"] = c["check"]
            all_issues.append(issue)

    overall_status = "healthy"
    if error_count > 0:
        overall_status = "unhealthy"
    elif warning_count > 0:
        overall_status = "degraded"

    report = {
        "timestamp": __import__("datetime").datetime.now(__import__("datetime").timezone.utc).isoformat(),
        "pipeline": "data_pipeline",
        "overall_status": overall_status,
        "summary": {
            "total_checks": total,
            "passed": ok_count,
            "warnings": warning_count,
            "errors": error_count,
        },
        "checks": {c["check"]: c for c in checks},
        "issues": all_issues,
    }

    return report


def main():
    report = run_all_checks()

    # 输出 JSON 报告 (stdout)
    print(json.dumps(report, ensure_ascii=False, indent=2))

    # 退出码: 0 = 健康, 1 = 有问题
    if report["summary"]["errors"] > 0:
        sys.exit(1)
    sys.exit(0)


if __name__ == "__main__":
    main()
