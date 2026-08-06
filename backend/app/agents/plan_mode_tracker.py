"""plan_mode_tracker.py — Agent Plan Mode Tracker

为 Commander Layer 提供 Plan 模式支持。
Plan 模式让 AI 智能体在处理复杂、多步任务时自动：
    1. 创建 plan.md 文件记录任务分解和进度
    2. 每步执行后检查 plan.md 中 [ ] 剩余数量
    3. 0个 [ ] 时自动退出 plan 模式

Usage:
    tracker = PlanModeTracker()
    tracker.enter_plan_mode("./plans/task_01.md")
    # ... execute steps ...
    remaining = tracker._check_plan_completion()
    if remaining == 0:
        tracker._exit_plan_mode()
"""

from __future__ import annotations

import os
import re
import time
from typing import Optional


# ── Plan Mode Tracker ────────────────────────────────────────────────────────


class PlanModeTracker:
    """Plan 模式跟踪器。

    为 Agent 提供 Plan 模式的进入、退出和进度检查能力。
    可以混入 (mixin) 到任意 Agent 类中使用。

    Attributes:
        _plan_active: 是否处于 Plan 模式。
        _plan_path: 当前 plan.md 文件路径。
        _plan_created_at: Plan 创建时间戳。
        _original_max_turns: 进入 Plan 模式前的原始 max_turns 值。
        _plan_max_turns_bonus: Plan 模式下额外增加的 max_turns 步数。
        _plan_task_count: Plan 中包含的任务总数。
    """

    def __init__(self, plan_max_turns_bonus: int = 10) -> None:
        """初始化 PlanModeTracker。

        Args:
            plan_max_turns_bonus: 进入 Plan 模式时额外增加的 max_turns 步数，
                                   默认 10 步。
        """
        self._plan_active: bool = False
        self._plan_path: Optional[str] = None
        self._plan_created_at: float = 0.0
        self._original_max_turns: int = 0
        self._plan_max_turns_bonus: int = plan_max_turns_bonus
        self._plan_task_count: int = 0

    # ── 公共 API ──────────────────────────────────────────────────────────

    def enter_plan_mode(self, plan_path: str, max_turns: int = 0) -> None:
        """进入 Plan 模式。

        创建一个 plan.md 文件（如果尚不存在），
        并调整 Agent 的 max_turns 以留出 Plan 模式的执行步数。

        Args:
            plan_path: plan.md 文件的路径。
            max_turns: 原始的 max_turns 值（用于增加步数）。
        """
        self._plan_active = True
        self._plan_path = plan_path
        self._plan_created_at = time.time()
        self._original_max_turns = max_turns

        # 确保 plan 文件所在目录存在
        plan_dir = os.path.dirname(plan_path)
        if plan_dir and not os.path.exists(plan_dir):
            os.makedirs(plan_dir, exist_ok=True)

        self._log("[Plan] 进入 Plan 模式", f"plan_path={plan_path}")

    def _in_plan_mode(self) -> bool:
        """检查当前是否处于 Plan 模式。

        Returns:
            True 表示处于 Plan 模式，False 表示未处于。
        """
        return self._plan_active

    def _exit_plan_mode(self) -> None:
        """退出 Plan 模式。

        重置 Plan 模式相关状态，清理资源。
        """
        if not self._plan_active:
            return

        self._log("[Plan] 退出 Plan 模式")

        self._plan_active = False
        self._plan_path = None
        self._plan_created_at = 0.0
        self._original_max_turns = 0
        self._plan_task_count = 0

    def _check_plan_completion(self) -> int:
        """检查 plan.md 中未完成的任务数量。

        读取 plan.md 文件，统计其中形式为 "[ ]" 的未完成项的数量。

        Returns:
            plan.md 中剩余的 [ ] 数量。如果文件不存在或无法读取，返回 -1。
        """
        if not self._plan_active or not self._plan_path:
            return -1

        if not os.path.exists(self._plan_path):
            self._log("[Plan] 警告", f"plan.md 不存在: {self._plan_path}")
            return -1

        try:
            with open(self._plan_path, "r", encoding="utf-8") as f:
                content = f.read()

            # 统计所有未完成的 [ ] 项（但不统计已完成的 [x]）
            unchecked = len(re.findall(r"\[ \]", content))
            checked = len(re.findall(r"\[x\]", content))
            total = unchecked + checked

            self._log(
                "[Plan] 进度检查",
                f"总任务={total}, 已完成={checked}, 剩余={unchecked}",
            )

            return unchecked

        except (OSError, IOError) as exc:
            self._log("[Plan] 错误", f"读取 plan.md 失败: {exc}")
            return -1

    # ── Plan 文件操作 ─────────────────────────────────────────────────────

    def _create_plan_from_tasks(
        self,
        tasks: list[dict],
        goal: str,
        plan_dir: Optional[str] = None,
    ) -> str:
        """根据任务列表创建 plan.md 文件。

        将 Commander.decompose() 输出的子任务列表转换为标准 plan.md 格式。

        Args:
            tasks: 子任务列表，每个元素应包含 'task_id' 和 'goal' 字段。
            goal: 原始目标描述。
            plan_dir: plan 文件存放目录。若为 None，使用当前目录下的 plans/。

        Returns:
            创建的 plan.md 文件的绝对路径。
        """
        # 确定 plan 路径
        if plan_dir is None:
            plan_dir = os.path.join(os.getcwd(), "plans")

        timestamp = time.strftime("%Y%m%d_%H%M%S")
        safe_goal = re.sub(r"[^a-zA-Z0-9\u4e00-\u9fff_]", "_", goal[:30])
        plan_filename = f"plan_{safe_goal}_{timestamp}.md"
        plan_path = os.path.join(plan_dir, plan_filename)

        # 确保目录存在
        os.makedirs(plan_dir, exist_ok=True)

        # 生成 plan.md 内容
        lines: list[str] = []
        lines.append(f"# Plan: {goal}")
        lines.append("")
        lines.append(f"- **创建时间**: {time.strftime('%Y-%m-%d %H:%M:%S')}")
        lines.append(f"- **目标**: {goal}")
        lines.append(f"- **子任务数**: {len(tasks)}")
        lines.append("")
        lines.append("## 任务列表")
        lines.append("")

        for i, task in enumerate(tasks, 1):
            task_id = task.get("task_id", f"task_{i}")
            task_goal = task.get("goal", f"子任务 {i}")
            lines.append(f"- [ ] **{task_id}**: {task_goal}")

        lines.append("")
        lines.append("---")
        lines.append("*自动由 PlanModeTracker 生成*")

        # 写入文件
        with open(plan_path, "w", encoding="utf-8") as f:
            f.write("\n".join(lines) + "\n")

        self._plan_path = plan_path
        self._plan_task_count = len(tasks)
        self._plan_active = True

        self._log("[Plan] 已创建 plan.md", f"path={plan_path}, tasks={len(tasks)}")

        return plan_path

    def _mark_step_completed(self, task_id: str) -> bool:
        """将 plan.md 中指定 task_id 的任务标记为已完成。

        将 "[ ]" 替换为 "[x]"。

        Args:
            task_id: 要标记的任务 ID。

        Returns:
            标记成功返回 True，否则返回 False。
        """
        if not self._plan_active or not self._plan_path:
            return False

        if not os.path.exists(self._plan_path):
            return False

        try:
            with open(self._plan_path, "r", encoding="utf-8") as f:
                content = f.read()

            # 查找并标记对应的任务行
            # 匹配模式: "- [ ] **task_id**: ..."
            pattern = rf"(\- \[ \] \*\*{re.escape(task_id)}\*\*)"
            replacement = pattern.replace("[ ]", "[x]")

            new_content = re.sub(
                rf"\- \[ \] \*\*{re.escape(task_id)}\*\*",
                f"- [x] **{task_id}**",
                content,
                count=1,
            )

            if new_content == content:
                self._log(
                    "[Plan] 警告",
                    f"未找到 task_id={task_id} 的未完成任务",
                )
                return False

            with open(self._plan_path, "w", encoding="utf-8") as f:
                f.write(new_content)

            self._log("[Plan] 标记完成", f"task_id={task_id}")
            return True

        except (OSError, IOError) as exc:
            self._log("[Plan] 错误", f"更新 plan.md 失败: {exc}")
            return False

    # ── 辅助方法 ──────────────────────────────────────────────────────────

    def _log(self, tag: str, message: str = "") -> None:
        """内部日志记录。"""
        msg = f"{tag}: {message}" if message else tag
        # 使用 print 作为轻量日志（不影响外部 logger 配置）
        print(f"[PlanModeTracker] {msg}")

    @property
    def plan_active(self) -> bool:
        """是否处于 Plan 模式（只读属性）。"""
        return self._plan_active

    @property
    def plan_path(self) -> Optional[str]:
        """当前 plan.md 路径（只读属性）。"""
        return self._plan_path

    @property
    def plan_task_count(self) -> int:
        """Plan 中的任务总数（只读属性）。"""
        return self._plan_task_count
