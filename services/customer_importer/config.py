"""
config.py — 目标系统配置定义

定义各 ERP/CRM 系统的 UI 坐标、操作步骤和字段映射。
配置以字典形式组织，支持通过 YAML/JSON 文件扩展。
"""

from __future__ import annotations

import json
import logging
import os
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

# ── 系统配置结构 ──────────────────────────────────────────────────────────

# 标准配置模板（用户可按需修改）
DEFAULT_CONFIG: dict[str, Any] = {
    # ══════════════════════════════════════════════════════════════════════
    # 示例：某 ERP 系统
    # ══════════════════════════════════════════════════════════════════════
    "erp_demo": {
        "display_name": "ERP 演示系统",
        "description": "示例 ERP 系统的 UI 配置",
        # ── 窗口匹配 ──
        "window": {
            "title": "ERP客户管理系统",
            "class_name": "",
        },
        # ── 登录步骤 ──
        "login": {
            "enabled": False,
            "steps": [
                {"action": "type", "target": "username", "x": 400, "y": 300, "value": "${username}"},
                {"action": "type", "target": "password", "x": 400, "y": 350, "value": "${password}"},
                {"action": "click", "x": 400, "y": 400},
            ],
        },
        # ── 导航步骤（进入导入页面前的操作） ──
        "navigation": [
            {"action": "click", "x": 100, "y": 80, "desc": "点击「客户管理」菜单"},
            {"action": "click", "x": 100, "y": 120, "desc": "点击「新增客户」按钮"},
            {"action": "wait", "seconds": 1.0},
        ],
        # ── 表单字段 ──
        # 每个字段定义在屏幕上的坐标、Tab键跳转顺序、或模板图像路径
        "fields": {
            "name": {
                "label": "客户名称",
                "x": 200,
                "y": 250,
                "tab_index": 1,
                "required": True,
                "clear_first": True,
            },
            "phone": {
                "label": "联系电话",
                "x": 200,
                "y": 290,
                "tab_index": 2,
                "required": False,
                "clear_first": True,
            },
            "email": {
                "label": "电子邮箱",
                "x": 200,
                "y": 330,
                "tab_index": 3,
                "required": False,
                "clear_first": True,
            },
            "company": {
                "label": "所属公司",
                "x": 500,
                "y": 250,
                "tab_index": 4,
                "required": False,
                "clear_first": True,
            },
            "title": {
                "label": "职位",
                "x": 500,
                "y": 290,
                "tab_index": 5,
                "required": False,
                "clear_first": True,
            },
            "address": {
                "label": "地址",
                "x": 500,
                "y": 330,
                "tab_index": 6,
                "required": False,
                "clear_first": True,
            },
            "notes": {
                "label": "备注",
                "x": 200,
                "y": 370,
                "tab_index": 7,
                "required": False,
                "clear_first": True,
            },
        },
        # ── 提交按钮 ──
        "submit": {
            "x": 350,
            "y": 450,
            "label": "保存",
            "confirm": False,  # 是否需要确认弹窗
        },
        # ── 提交后等待 ──
        "post_submit_wait": 1.5,
        # ── 失败重试 ──
        "field_input_retries": 2,
        "submission_retries": 1,
    },
    # ══════════════════════════════════════════════════════════════════════
    # 示例：某 CRM Web 系统
    # ══════════════════════════════════════════════════════════════════════
    "crm_web_demo": {
        "display_name": "CRM Web 演示系统",
        "description": "示例 CRM Web 系统的 UI 配置（基于 Alt+Tab 切换窗口）",
        "window": {
            "title": "CRM - 客户关系管理",
            "class_name": "Chrome_WidgetWin_1",
        },
        "login": {
            "enabled": True,
            "steps": [
                {"action": "click", "x": 300, "y": 250, "desc": "点击用户名输入框"},
                {"action": "type", "x": 300, "y": 250, "value": "${username}", "desc": "输入用户名"},
                {"action": "click", "x": 300, "y": 300, "desc": "点击密码输入框"},
                {"action": "type", "x": 300, "y": 300, "value": "${password}", "desc": "输入密码"},
                {"action": "click", "x": 300, "y": 350, "desc": "点击登录按钮"},
                {"action": "wait", "seconds": 3.0, "desc": "等待登录完成"},
            ],
        },
        "navigation": [
            {"action": "click", "x": 50, "y": 100, "desc": "点击侧边栏「客户」"},
            {"action": "click", "x": 50, "y": 50, "desc": "点击「新建客户」"},
            {"action": "wait", "seconds": 2.0},
        ],
        "fields": {
            "name": {"x": 200, "y": 200, "clear_first": True},
            "phone": {"x": 200, "y": 240, "clear_first": True},
            "email": {"x": 200, "y": 280, "clear_first": True},
            "company": {"x": 500, "y": 200, "clear_first": True},
            "title": {"x": 500, "y": 240, "clear_first": True},
            "address": {"x": 500, "y": 280, "clear_first": True},
            "wechat": {"x": 200, "y": 320, "clear_first": True},
            "industry": {"x": 500, "y": 320, "clear_first": True},
            "notes": {"x": 200, "y": 360, "clear_first": True},
        },
        "submit": {
            "x": 350,
            "y": 480,
            "label": "保存",
            "confirm": True,
            "confirm_x": 400,
            "confirm_y": 350,
        },
        "post_submit_wait": 2.0,
        "field_input_retries": 2,
        "submission_retries": 2,
    },
}


# ── 配置管理器 ────────────────────────────────────────────────────────────


class ImportConfig:
    """导入配置管理器

    提供系统配置的加载、查询和验证功能。
    支持从内置 DEFAULT_CONFIG 和外部 YAML/JSON 文件加载。
    """

    def __init__(self, config_path: str | Path | None = None):
        self._configs: dict[str, Any] = dict(DEFAULT_CONFIG)

        if config_path:
            self.load(config_path)

    def load(self, config_path: str | Path) -> None:
        """从 JSON/YAML 文件加载外部配置

        外部配置会与内置配置合并（外部同名系统会覆盖内置配置）。
        """
        path = Path(config_path)
        if not path.exists():
            logger.warning("配置文件不存在: %s，使用内置默认配置", path)
            return

        ext = path.suffix.lower()
        try:
            if ext == ".json":
                with open(path, encoding="utf-8") as f:
                    external = json.load(f)
            elif ext in (".yaml", ".yml"):
                try:
                    import yaml
                except ImportError:
                    raise ImportError("加载 YAML 配置需要 PyYAML: pip install pyyaml")
                with open(path, encoding="utf-8") as f:
                    external = yaml.safe_load(f)
            else:
                raise ValueError(f"不支持的配置文件格式: {ext}（支持 .json / .yaml / .yml）")
        except Exception as e:
            logger.error("加载配置文件失败 %s: %s", path, e)
            return

        if not isinstance(external, dict):
            logger.error("配置内容必须是一个字典（系统名→配置）")
            return

        # 合并配置
        for system_name, system_config in external.items():
            if system_name in self._configs and isinstance(system_config, dict):
                # 深度合并
                self._deep_merge(self._configs[system_name], system_config)
            else:
                self._configs[system_name] = system_config

        logger.info("已加载 %d 个外部系统配置", len(external))

    def get(self, system_name: str) -> dict[str, Any]:
        """获取指定系统的配置"""
        config = self._configs.get(system_name)
        if config is None:
            available = list(self._configs.keys())
            raise KeyError(
                f"未知系统「{system_name}」。可用系统: {available}"
            )
        return config

    def list_systems(self) -> list[dict[str, str]]:
        """列出所有可用的系统配置"""
        return [
            {
                "name": name,
                "display_name": cfg.get("display_name", name),
                "description": cfg.get("description", ""),
            }
            for name, cfg in self._configs.items()
        ]

    def validate_config(self, system_name: str) -> list[str]:
        """验证系统配置的完整性，返回缺失项列表"""
        errors: list[str] = []
        try:
            cfg = self.get(system_name)
        except KeyError as e:
            return [str(e)]

        if "window" not in cfg or "title" not in cfg.get("window", {}):
            errors.append("缺少 window.title（窗口标题）")

        if "fields" not in cfg or not cfg["fields"]:
            errors.append("缺少 fields（表单字段定义）")
        else:
            for fname, fcfg in cfg["fields"].items():
                if "x" not in fcfg or "y" not in fcfg:
                    errors.append(f"字段「{fname}」缺少坐标 (x/y)")

        if "submit" not in cfg or "x" not in cfg.get("submit", {}) or "y" not in cfg.get("submit", {}):
            errors.append("缺少 submit 按钮坐标")

        return errors

    # ── 内部方法 ──────────────────────────────────────────────────────────

    @staticmethod
    def _deep_merge(base: dict[str, Any], override: dict[str, Any]) -> None:
        """深度合并两个字典（override 覆盖 base）"""
        for key, value in override.items():
            if key in base and isinstance(base[key], dict) and isinstance(value, dict):
                ImportConfig._deep_merge(base[key], value)
            else:
                base[key] = value
