"""agent_safety.py — 智能体运行时安全与渐进式警告

TurnProgressiveWarnings 提供基于轮次的渐进式安全警告机制，
用于在 Agent 执行循环中逐步增强约束，防止无效重试和失控行为。

Usage:
    from baize_libs.generic_agent.agent_safety import TurnProgressiveWarnings

    signal = TurnProgressiveWarnings.get_signal(turn=7, in_plan_mode=False)
    if signal.level == "warning":
        # 注入警告到 next_prompt
        pass
    elif signal.level == "danger":
        # 强制 ask_user 或 break
        pass
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional


@dataclass
class ProgressiveSignal:
    """渐进式安全信号。

    Attributes:
        turn: 触发该信号的轮次。
        level: 信号级别 — "info" | "warning" | "danger".
        message: 信号消息内容。
        action: 建议的动作 — "continue" | "inject_warning" | "ask_user" | "break".
    """

    turn: int
    level: str  # "info" | "warning" | "danger"
    message: str
    action: str = "continue"


class TurnProgressiveWarnings:
    """基于轮次的渐进式安全警告。

    随着 Agent 执行轮次增加，逐步施加更强的约束信号：

        Turn 7:     warning  → "禁止无效重试"
        Turn 10:    warning  → 注入上下文
        Turn 35:    danger   → "必须ask_user"
        Turn 70:    danger   → 软上限警告（plan 模式下触发）

    每轮只触发最高匹配的信号。更高的轮次覆盖更低的轮次。
    """

    # 预定义的渐进式信号规则 — 按 turn 升序排列
    _SIGNAL_RULES: list[tuple[int, str, str, str]] = [
        # (turn_threshold, level, message, action)
        (7, "warning", "禁止无效重试 — Agent 多次执行同一动作，请检查逻辑", "inject_warning"),
        (10, "warning", "注入上下文 — 轮次较高，建议检查上下文完整性", "inject_warning"),
        (35, "danger", "必须 ask_user — 长时间未与用户交互，需暂停确认", "ask_user"),
        (70, "danger", "软上限警告 — 已达执行轮次上限，请终止或进入 fallback", "break"),
    ]

    _IN_PLAN_SIGNAL_RULES: list[tuple[int, str, str, str]] = [
        # Plan 模式下的额外规则（覆盖/补充通用规则）
        (7, "warning", "禁止无效重试 — Plan 模式下请勿重复执行已完成步骤", "inject_warning"),
        (10, "warning", "注入上下文 — Plan 模式下检查 plan.md 进度一致性", "inject_warning"),
        (35, "danger", "必须 ask_user — Plan 模式长时间执行，需用户确认方向", "ask_user"),
        (70, "danger", "软上限警告 — Plan 模式已达执行上限，建议重新规划", "break"),
    ]

    def __init__(self, turn: int = 0) -> None:
        """初始化渐进式警告跟踪器。

        Args:
            turn: 起始轮次（可用于恢复状态，默认 0）。
        """
        self._turn = turn
        self._last_signal: Optional[ProgressiveSignal] = None

    @property
    def turn(self) -> int:
        """当前轮次。"""
        return self._turn

    def advance(self) -> int:
        """推进一轮，返回更新后的轮次号。

        Returns:
            增加后的轮次号。
        """
        self._turn += 1
        return self._turn

    def check(self, in_plan_mode: bool = False) -> Optional[ProgressiveSignal]:
        """检查当前轮次是否触发渐进式警告。

        Args:
            in_plan_mode: 是否处于 Plan 模式。

        Returns:
            若当前轮次触发警告，返回 ProgressiveSignal；否则返回 None。
        """
        rules = self._IN_PLAN_SIGNAL_RULES if in_plan_mode else self._SIGNAL_RULES
        best_signal: Optional[ProgressiveSignal] = None

        for threshold, level, message, action in rules:
            if self._turn >= threshold:
                best_signal = ProgressiveSignal(
                    turn=threshold,
                    level=level,
                    message=message,
                    action=action,
                )

        self._last_signal = best_signal
        return best_signal

    @staticmethod
    def get_signal(turn: int, in_plan_mode: bool = False) -> Optional[ProgressiveSignal]:
        """根据轮次获取渐进式安全信号（纯静态方法）。

        这是最简洁的调用方式，不依赖实例状态。

        Args:
            turn: 当前执行轮次。
            in_plan_mode: 是否处于 Plan 模式。

        Returns:
            该轮次匹配的 ProgressiveSignal，若无匹配则返回 None。
        """
        rules = TurnProgressiveWarnings._IN_PLAN_SIGNAL_RULES if in_plan_mode else TurnProgressiveWarnings._SIGNAL_RULES
        best_signal: Optional[ProgressiveSignal] = None

        for threshold, level, message, action in rules:
            if turn >= threshold:
                best_signal = ProgressiveSignal(
                    turn=threshold,
                    level=level,
                    message=message,
                    action=action,
                )

        return best_signal

    def get_last_signal(self) -> Optional[ProgressiveSignal]:
        """获取最近一次检查产生的信号。"""
        return self._last_signal

    def reset(self) -> None:
        """重置轮次计数和信号状态。"""
        self._turn = 0
        self._last_signal = None

    def __repr__(self) -> str:
        return (
            f"<TurnProgressiveWarnings turn={self._turn} "
            f"last_signal={self._last_signal}>"
        )
