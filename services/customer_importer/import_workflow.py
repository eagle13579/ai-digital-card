"""
import_workflow.py — 导入工作流抽象基类与具体实现

定义 ImportWorkflow（抽象基类）和两个内置实现：
  - ERPWebImport  — 面向传统桌面 ERP 系统
  - CRMWebImport  — 面向 Web CRM 系统（WPF / Electron / 浏览器）

每个子类实现导入循环：打开窗口 → 导航 → 逐条填写表单 → 提交 → 记录进度。
"""

from __future__ import annotations

import logging
import time
from abc import ABC, abstractmethod
from typing import Any

from checkpoint import Checkpoint, CheckpointManager, ImportStatus, format_progress_bar
from config import ImportConfig
from rpa_client import RpaClient

logger = logging.getLogger(__name__)


# ══════════════════════════════════════════════════════════════════════════
# 抽象基类
# ══════════════════════════════════════════════════════════════════════════


class ImportWorkflow(ABC):
    """导入工作流抽象基类

    子类需实现：
      - _open_target_system()  — 打开/切换到目标系统
      - _navigate_to_form()    — 导航到新增客户表单
      - _fill_field()          — 填写单个表单字段
      - _submit_form()         — 提交当前表单
      - _handle_error()        — 错误处理

    run() 方法驱动完整的导入循环（含 checkpoint 恢复逻辑）。
    """

    def __init__(
        self,
        rpa_client: RpaClient,
        checkpoint_mgr: CheckpointManager,
        config: dict[str, Any],
        system_name: str,
        field_mapping: dict[str, str] | None = None,
    ):
        """
        Args:
            rpa_client: RPA 微服务客户端
            checkpoint_mgr: 检查点管理器
            config: 目标系统的 UI 配置字典
            system_name: 系统名称（用于日志/检查点元数据）
            field_mapping: 数据字段→表单字段映射 {数据字段名: 表单字段名}
                           None 表示使用同名映射
        """
        self._rpa = rpa_client
        self._checkpoint = checkpoint_mgr
        self._config = config
        self._system_name = system_name
        self._field_mapping = field_mapping or {}
        self._stats = {"success": 0, "failed": 0, "skipped": 0}

    # ── 子类必须实现的抽象方法 ───────────────────────────────────────────

    @abstractmethod
    def _open_target_system(self) -> None:
        """打开或切换到目标系统窗口"""
        ...

    @abstractmethod
    def _navigate_to_form(self) -> None:
        """导航到新增客户表单页面"""
        ...

    @abstractmethod
    def _fill_field(self, field_name: str, field_config: dict[str, Any], value: str) -> None:
        """填写单个表单字段

        Args:
            field_name: 字段名（如 'name', 'phone'）
            field_config: 字段配置（含坐标等）
            value: 要填写的文本值
        """
        ...

    @abstractmethod
    def _submit_form(self) -> bool:
        """提交当前表单

        Returns:
            True 表示提交成功，False 表示失败
        """
        ...

    @abstractmethod
    def _handle_error(self, record_index: int, error: Exception) -> str:
        """处理导入错误，返回错误描述字符串"""
        ...

    # ── 可选覆盖的方法 ──────────────────────────────────────────────────

    def _login_if_needed(self) -> None:
        """如果配置需要登录，执行登录步骤"""
        login_cfg = self._config.get("login", {})
        if not login_cfg.get("enabled", False):
            return
        logger.info("执行系统登录...")
        self._execute_steps(login_cfg.get("steps", []))

    def _post_submit(self) -> None:
        """提交后的处理（等待、确认弹窗等）"""
        wait_time = self._config.get("post_submit_wait", 1.0)
        if wait_time > 0:
            time.sleep(wait_time)

        submit_cfg = self._config.get("submit", {})
        if submit_cfg.get("confirm", False):
            confirm_x = submit_cfg.get("confirm_x")
            confirm_y = submit_cfg.get("confirm_y")
            if confirm_x is not None and confirm_y is not None:
                logger.debug("点击确认弹窗 (%d, %d)", confirm_x, confirm_y)
                self._rpa.click(confirm_x, confirm_y)
                time.sleep(0.5)

    def _execute_steps(self, steps: list[dict[str, Any]]) -> None:
        """执行一组操作步骤"""
        for step in steps:
            action = step.get("action", "")
            desc = step.get("desc", action)

            logger.debug("执行步骤: %s", desc)

            if action == "click":
                self._rpa.click(step["x"], step["y"])
                time.sleep(0.3)
            elif action == "type":
                self._rpa.click_and_type(
                    step["x"], step["y"],
                    step.get("value", ""),
                    clear_first=step.get("clear_first", True),
                )
                time.sleep(0.2)
            elif action == "press":
                self._rpa.press(step.get("keys", "tab"))
                time.sleep(0.2)
            elif action == "wait":
                time.sleep(step.get("seconds", 1.0))
            elif action == "screenshot":
                self._rpa.screenshot(step.get("path"))
            else:
                logger.warning("未知操作: %s", action)

    # ── 核心导入循环 ────────────────────────────────────────────────────

    def run(
        self,
        records: list[dict[str, str]],
        session_id: str,
        source_file: str,
        resume: bool = False,
        dry_run: bool = False,
    ) -> Checkpoint:
        """执行完整导入流程

        Args:
            records: 客户数据列表（每个元素是一个 dict）
            session_id: 导入会话ID
            source_file: 源文件路径
            resume: 是否从中断恢复
            dry_run: 仅验证不实际操作

        Returns:
            最终的 Checkpoint 对象
        """
        total = len(records)
        logger.info(
            "开始导入 %d 条客户记录到「%s」%s",
            total, self._system_name,
            "(DRY RUN)" if dry_run else "",
        )

        # ── 初始化检查点 ──
        if resume:
            cp = self._checkpoint.load_session(session_id)
            if cp is None:
                logger.warning("未找到会话 %s，从头开始", session_id)
                cp = self._checkpoint.create_session(
                    session_id, source_file, total,
                    metadata={"system": self._system_name, "dry_run": dry_run},
                )
            else:
                logger.info("从检查点恢复会话 %s", session_id)
                # 用最新数据更新 records
                for i, record in enumerate(cp.records):
                    if i < len(records):
                        record.raw_data = records[i]
        else:
            cp = self._checkpoint.create_session(
                session_id, source_file, total,
                metadata={"system": self._system_name, "dry_run": dry_run},
            )
            # 写入原始数据
            for i, record in enumerate(cp.records):
                if i < len(records):
                    record.raw_data = records[i]

        # ── 查找恢复起始点 ──
        start_index = self._checkpoint.get_resume_index(cp)
        if start_index >= total:
            logger.info("所有记录已完成导入 (进度: %.1f%%)", cp.progress * 100)
            return cp

        if start_index > 0:
            logger.info("从第 %d 条记录恢复 (跳过 %d 条已完成)", start_index, start_index)

        # ── 非 DRY RUN：打开目标系统 ──
        if not dry_run:
            try:
                self._open_target_system()
                self._login_if_needed()
            except Exception as e:
                logger.error("打开目标系统失败: %s", e)
                raise

        # ── 逐条导入 ──
        for i in range(start_index, total):
            record_data = records[i] if i < len(records) else {}
            raw_data = cp.records[i].raw_data if i < len(cp.records) else record_data

            if dry_run:
                # 干跑模式：仅验证数据
                missing = self._validate_record(record_data)
                status = ImportStatus.SUCCESS if not missing else ImportStatus.FAILED
                msg = f"验证通过" if not missing else f"缺少必填字段: {', '.join(missing)}"
                self._checkpoint.update_record(cp, i, status, msg, raw_data=raw_data)
                logger.info("[%d/%d] %s — %s", i + 1, total, record_data.get("name", "?"), msg)
                continue

            # ── 导航到表单（每条记录前导航一次） ──
            try:
                self._navigate_to_form()
            except Exception as e:
                logger.error("导航到表单失败 (记录 %d): %s", i, e)
                self._checkpoint.update_record(
                    cp, i, ImportStatus.FAILED, f"导航失败: {e}", raw_data=raw_data,
                )
                self._stats["failed"] += 1
                continue

            # ── 填写表单 ──
            success = True
            error_msg = ""

            try:
                self._fill_form_fields(record_data)
            except Exception as e:
                success = False
                error_msg = self._handle_error(i, e)
                logger.error("填写表单失败 (记录 %d): %s", i, error_msg)

            # ── 提交 ──
            if success:
                try:
                    submitted = self._submit_form()
                    if submitted:
                        self._post_submit()
                        self._checkpoint.update_record(
                            cp, i, ImportStatus.SUCCESS, "导入成功", raw_data=raw_data,
                        )
                        self._stats["success"] += 1
                    else:
                        self._checkpoint.update_record(
                            cp, i, ImportStatus.FAILED, "提交失败（空响应）", raw_data=raw_data,
                        )
                        self._stats["failed"] += 1
                except Exception as e:
                    error_msg = self._handle_error(i, e)
                    self._checkpoint.update_record(
                        cp, i, ImportStatus.FAILED, error_msg, raw_data=raw_data,
                    )
                    self._stats["failed"] += 1

            # ── 打印进度 ──
            if (i + 1) % 5 == 0 or i == total - 1 or i == start_index:
                bar = format_progress_bar(
                    cp.completed_count, total,
                )
                logger.info(
                    "进度: %s | 成功: %d | 失败: %d",
                    bar, self._stats["success"], self._stats["failed"],
                )

        # ── 最终摘要 ──
        summary = self._checkpoint.summary(cp)
        logger.info(
            "导入完成！总计: %d, 成功: %d, 失败: %d, 耗时: %.1fs",
            summary["total"], summary["completed"],
            summary["failed"], summary["elapsed_seconds"],
        )

        return cp

    # ── 表单填写辅助方法 ────────────────────────────────────────────────

    def _fill_form_fields(self, record_data: dict[str, str]) -> None:
        """按配置顺序填写所有表单字段

        使用 field_mapping（如果设置了）将数据字段名映射到表单字段名。
        """
        fields_config = self._config.get("fields", {})

        for field_name, field_config in fields_config.items():
            # 确定从数据中取什么字段名
            data_key = field_name
            for data_field, form_field in self._field_mapping.items():
                if form_field == field_name:
                    data_key = data_field
                    break

            value = record_data.get(data_key, "")
            if not value:
                # 尝试直接匹配
                value = record_data.get(field_name, "")

            if not value and field_config.get("required", False):
                logger.warning("必填字段「%s」值为空，跳过", field_name)
                continue

            if value:
                self._fill_field(field_name, field_config, value)

    def _validate_record(self, record_data: dict[str, str]) -> list[str]:
        """验证单条记录，返回缺失的必填字段列表"""
        missing: list[str] = []
        fields_config = self._config.get("fields", {})
        for field_name, field_config in fields_config.items():
            if field_config.get("required", False):
                value = record_data.get(field_name, "")
                if not value:
                    missing.append(field_name)
        return missing


# ══════════════════════════════════════════════════════════════════════════
# 具体实现：ERP 系统导入
# ══════════════════════════════════════════════════════════════════════════


class ERPWebImport(ImportWorkflow):
    """面向传统桌面 ERP 系统的导入工作流

    操作模式：
      1. find-window 按标题查找 ERP 窗口
      2. 直接使用 x/y 坐标点击、输入
      3. Tab 键切换输入框焦点
    """

    def _open_target_system(self) -> None:
        window_cfg = self._config.get("window", {})
        title = window_cfg.get("title", "")
        class_name = window_cfg.get("class_name")

        logger.info("查找ERP窗口: title=%s", title)
        result = self._rpa.find_window(title, class_name=class_name)
        logger.debug("find-window 结果: %s", result)
        time.sleep(1.0)

    def _navigate_to_form(self) -> None:
        nav_steps = self._config.get("navigation", [])
        if nav_steps:
            logger.debug("执行导航步骤...")
            self._execute_steps(nav_steps)

    def _fill_field(self, field_name: str, field_config: dict[str, Any], value: str) -> None:
        clear = field_config.get("clear_first", True)
        retries = self._config.get("field_input_retries", 2)

        for attempt in range(retries + 1):
            try:
                self._rpa.click_and_type(
                    field_config["x"],
                    field_config["y"],
                    value,
                    clear_first=clear and attempt == 0,
                )
                time.sleep(0.2)
                break  # 成功则跳出重试循环
            except Exception as e:
                if attempt < retries:
                    logger.warning("字段「%s」输入失败 (尝试 %d/%d): %s",
                                   field_name, attempt + 1, retries + 1, e)
                    time.sleep(0.5)
                else:
                    raise

    def _submit_form(self) -> bool:
        submit_cfg = self._config.get("submit", {})
        retries = self._config.get("submission_retries", 1)

        for attempt in range(retries + 1):
            try:
                self._rpa.click(submit_cfg["x"], submit_cfg["y"])
                time.sleep(0.5)
                return True
            except Exception as e:
                if attempt < retries:
                    logger.warning("提交失败 (尝试 %d/%d): %s", attempt + 1, retries + 1, e)
                    time.sleep(1.0)
                else:
                    raise

        return False

    def _handle_error(self, record_index: int, error: Exception) -> str:
        return f"ERP 导入错误 (记录 {record_index}): {error}"


# ══════════════════════════════════════════════════════════════════════════
# 具体实现：CRM Web 系统导入
# ══════════════════════════════════════════════════════════════════════════


class CRMWebImport(ImportWorkflow):
    """面向 Web CRM / SPA 系统的导入工作流

    与 ERP 导入的区别：
      - 窗口可能为浏览器（Chrome/Edge）
      - 导航步骤更复杂（可能含下拉菜单、弹窗）
      - 提交后可能需要确认弹窗
      - 每页可能需要等待元素加载
    """

    def _open_target_system(self) -> None:
        window_cfg = self._config.get("window", {})
        title = window_cfg.get("title", "")
        class_name = window_cfg.get("class_name", "Chrome_WidgetWin_1")

        logger.info("查找CRM窗口: title=%s", title)
        try:
            result = self._rpa.find_window(title, class_name=class_name)
            logger.debug("find-window 结果: %s", result)
        except Exception:
            logger.warning("精确查找失败，尝试模糊匹配 title=%s", title)
            result = self._rpa.find_window(title)
        time.sleep(1.0)

    def _navigate_to_form(self) -> None:
        nav_steps = self._config.get("navigation", [])
        if nav_steps:
            logger.info("执行CRM导航步骤...")
            self._execute_steps(nav_steps)
            # Web 系统额外等待
            time.sleep(1.0)

    def _fill_field(self, field_name: str, field_config: dict[str, Any], value: str) -> None:
        clear = field_config.get("clear_first", True)
        retries = self._config.get("field_input_retries", 2)

        for attempt in range(retries + 1):
            try:
                # 先点击聚焦
                self._rpa.click(field_config["x"], field_config["y"])
                time.sleep(0.3)

                if clear:
                    self._rpa.press("ctrl+a")
                    time.sleep(0.1)
                    self._rpa.press("delete")
                    time.sleep(0.1)

                self._rpa.type(value, interval=0.05)
                time.sleep(0.2)
                break
            except Exception as e:
                if attempt < retries:
                    logger.warning("CRM字段「%s」输入失败 (尝试 %d/%d): %s",
                                   field_name, attempt + 1, retries + 1, e)
                    time.sleep(1.0)
                else:
                    raise

    def _submit_form(self) -> bool:
        submit_cfg = self._config.get("submit", {})
        retries = self._config.get("submission_retries", 2)

        for attempt in range(retries + 1):
            try:
                self._rpa.click(submit_cfg["x"], submit_cfg["y"])
                time.sleep(1.0)
                return True
            except Exception as e:
                if attempt < retries:
                    logger.warning("CRM提交失败 (尝试 %d/%d): %s",
                                   attempt + 1, retries + 1, e)
                    time.sleep(2.0)
                else:
                    raise

        return False

    def _handle_error(self, record_index: int, error: Exception) -> str:
        return f"CRM 导入错误 (记录 {record_index}): {error}"
