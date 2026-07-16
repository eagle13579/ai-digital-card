"""Watchdog system for AI Employee agents — event-driven monitoring.

Injected from BrowserUse's watchdog architecture (BaseWatchdog → CrashWatchdog,
popups_watchdog, etc.). Provides three specialized watchdogs:

    - CrashWatchdog:     Monitors agent health, detects crashes/hangs, triggers recovery
    - ProgressWatchdog:  Tracks task execution progress, detects stalls and deadlocks
    - OutputWatchdog:    Validates agent outputs for quality, structure, and completeness

Architecture:
    Each watchdog inherits from BaseWatchdog and uses the content factory's existing
    EventBusProtocol (Event → EventHandler) for event-driven communication. No polling.
    Watchdogs register themselves on agent init() via attach_to_agent().

Usage:
    class MyAgent(BaseAgent):
        async def init(self):
            # Create and attach watchdogs
            self.crash_wd = CrashWatchdog(agent=self)
            self.progress_wd = ProgressWatchdog(agent=self)
            self.output_wd = OutputWatchdog(agent=self)
            await self.crash_wd.attach_to_agent()
            await self.progress_wd.attach_to_agent()
            await self.output_wd.attach_to_agent()
"""

from __future__ import annotations

import asyncio
import logging
import time
import uuid
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import TYPE_CHECKING, Any, Callable, Coroutine

if TYPE_CHECKING:
    from app.agents.base_agent import BaseAgent

logger = logging.getLogger(__name__)


# ======================================================================
# Event Models (lightweight, no external dependency)
# ======================================================================


@dataclass
class WatchdogEvent:
    """Base event for all watchdog-emitted signals.

    Follows the BrowserUse BaseEvent pattern but adapted to run on
    the content factory's existing EventBusProtocol (Event dataclass).
    """

    event_type: str
    source: str  # watchdog class name
    agent_id: str
    payload: dict[str, Any] = field(default_factory=dict)
    timestamp: float = field(default_factory=time.time)
    event_id: str = field(default_factory=lambda: uuid.uuid4().hex[:12])


# ======================================================================
# Event type constants
# ======================================================================


class AgentWatchdogEventType(str, Enum):
    """Canonical event type strings used by watchdogs.

    Agents subscribe to these via runtime.event_bus or direct handler registration.
    """

    # CrashWatchdog events
    AGENT_CRASH_DETECTED = "agent.watchdog.crash.detected"
    AGENT_CRASH_RECOVERED = "agent.watchdog.crash.recovered"
    AGENT_HANG_DETECTED = "agent.watchdog.crash.hang"

    # ProgressWatchdog events
    PROGRESS_UPDATE = "agent.watchdog.progress.update"
    PROGRESS_STALL_DETECTED = "agent.watchdog.progress.stall"
    PROGRESS_DEADLOCK_DETECTED = "agent.watchdog.progress.deadlock"
    TASK_COMPLETED = "agent.watchdog.progress.completed"

    # OutputWatchdog events
    OUTPUT_VALIDATED = "agent.watchdog.output.validated"
    OUTPUT_VALIDATION_FAILED = "agent.watchdog.output.failure"
    OUTPUT_TIMEOUT = "agent.watchdog.output.timeout"


# ======================================================================
# BaseWatchdog
# ======================================================================


class BaseWatchdog(ABC):
    """Abstract base for all agent watchdogs.

    Inspired by BrowserUse's BaseWatchdog (watchdog_base.py), which provides:
        - Event-driven handler registration via method naming convention
        - Circuit-breaker for CDP connection state
        - Automatic lifecycle task management via __del__
        - Handler uniqueness enforcement

    This adaptation maps the same pattern to the content factory's
    EventBusProtocol + BaseAgent architecture.
    """

    def __init__(self, agent: BaseAgent) -> None:
        self.agent = agent
        self._monitoring_task: asyncio.Task | None = None
        self._active: bool = False
        self._logger = logger.getChild(self.__class__.__name__)
        self._event_handlers: dict[str, list[Callable[[WatchdogEvent], Coroutine[Any, Any, None]]]] = {}

    @property
    def log(self) -> logging.Logger:
        return self._logger

    # ── Event subscription helpers (mirror BrowserUse's attach_handler_to_session) ──

    def on(self, event_type: str, handler: Callable[[WatchdogEvent], Coroutine[Any, Any, None]]) -> None:
        """Register an event handler for a specific watchdog event type."""
        if event_type not in self._event_handlers:
            self._event_handlers[event_type] = []
        self._event_handlers[event_type].append(handler)

    async def _emit(self, event_type: str, **payload: Any) -> None:
        """Emit a watchdog event to all registered handlers.

        Also publishes to the agent's event_bus if available.
        """
        event = WatchdogEvent(
            event_type=event_type,
            source=self.__class__.__name__,
            agent_id=self.agent.agent_id,
            payload=payload,
        )

        # 1. Notify direct subscribers
        handlers = self._event_handlers.get(event_type, [])
        for handler in handlers:
            try:
                await handler(event)
            except Exception:
                self.log.exception("Handler failed for event %s", event_type)

        # 2. Publish to the agent's event_bus (if available)
        agent_event_bus = getattr(self.agent, 'runtime', None)
        if agent_event_bus and hasattr(agent_event_bus, 'event_bus'):
            bus = agent_event_bus.event_bus
            if bus is not None:
                try:
                    from app.events.interfaces import Event as BusEvent
                    from app.events.interfaces import EventPriority

                    await bus.publish(
                        BusEvent(
                            type=event_type,
                            source=f"watchdog.{self.__class__.__name__}",
                            payload={
                                "agent_id": self.agent.agent_id,
                                "agent_name": self.agent.agent_name,
                                **payload,
                            },
                            priority=EventPriority.HIGH,
                        )
                    )
                except Exception:
                    pass  # bus publishing is best-effort

        self.log.debug("Emitted %s: %s", event_type, {k: v for k, v in payload.items() if k != 'traceback'})

    # ── Lifecycle ──

    async def attach_to_agent(self) -> None:
        """Start monitoring. Called from agent.init()."""
        if self._active:
            return
        self._active = True
        self.log.info("Watchdog %s attached to agent %s", self.__class__.__name__, self.agent.agent_name)
        await self._on_attach()

    async def detach_from_agent(self) -> None:
        """Stop monitoring. Called from agent.stop()."""
        self._active = False
        if self._monitoring_task and not self._monitoring_task.done():
            self._monitoring_task.cancel()
            try:
                await self._monitoring_task
            except asyncio.CancelledError:
                pass
            self._monitoring_task = None
        await self._on_detach()
        self.log.info("Watchdog %s detached from agent %s", self.__class__.__name__, self.agent.agent_name)

    async def _on_attach(self) -> None:
        """Subclasses override for attach-time setup."""

    async def _on_detach(self) -> None:
        """Subclasses override for detach-time cleanup."""

    def __del__(self) -> None:
        """Clean up running tasks on garbage collection (mirrors BrowserUse BaseWatchdog)."""
        if self._monitoring_task and not self._monitoring_task.done():
            self._monitoring_task.cancel()


# ======================================================================
# CrashWatchdog
# ======================================================================


class CrashWatchdog(BaseWatchdog):
    """Monitors agent health and triggers recovery on crash/hang.

    Inspired by BrowserUse's CrashWatchdog (crash_watchdog.py) which uses CDP
    to detect target crashes. This adaptation monitors the agent's lifecycle
    (status, task timeouts, execution errors) instead of CDP targets.

    Detection mechanisms:
        1. Status watch: Agent stuck in BUSY past timeout → hang detected
        2. Execution watch: Agent throws consecutive errors → crash detected
        3. Heartbeat: Agent must call heartbeat() periodically → stale if silent

    Recovery strategies (configurable):
        - restart: Reinvoke agent.init() and continue
        - escalate: Delegate to another agent
        - report_only: Log and emit event, let runtime decide
    """

    def __init__(
        self,
        agent: BaseAgent,
        hang_timeout_seconds: float = 60.0,
        max_consecutive_errors: int = 3,
        heartbeat_interval_seconds: float = 15.0,
        recovery_strategy: str = "report_only",
        check_interval_seconds: float = 5.0,
    ) -> None:
        super().__init__(agent)
        self.hang_timeout_seconds = hang_timeout_seconds
        self.max_consecutive_errors = max_consecutive_errors
        self.heartbeat_interval_seconds = heartbeat_interval_seconds
        self.recovery_strategy = recovery_strategy
        self.check_interval_seconds = check_interval_seconds

        # Private state
        self._last_heartbeat: float = time.time()
        self._consecutive_errors: int = 0
        self._last_status: str = ""
        self._recovery_in_progress: bool = False
        self._crash_count: int = 0
        self._recovery_count: int = 0

    async def heartbeat(self) -> None:
        """Called by the agent to signal it's alive.

        The agent should call this inside long-running tasks.
        """
        self._last_heartbeat = time.time()
        self._consecutive_errors = 0

    async def report_error(self, error: Exception) -> None:
        """Called by the agent when it encounters an execution error."""
        self._consecutive_errors += 1
        self._last_heartbeat = time.time()  # still a sign of life

        if self._consecutive_errors >= self.max_consecutive_errors:
            await self._detect_crash(
                reason=f"Consecutive errors ({self._consecutive_errors} >= {self.max_consecutive_errors})",
                details={"consecutive_errors": self._consecutive_errors, "last_error": str(error)},
            )

    async def _on_attach(self) -> None:
        """Start monitoring loop on attach."""
        self._monitoring_task = asyncio.create_task(self._monitoring_loop())
        self.log.info(
            "CrashWatchdog monitoring %s (hang=%ss, max_errors=%d, strategy=%s)",
            self.agent.agent_name,
            self.hang_timeout_seconds,
            self.max_consecutive_errors,
            self.recovery_strategy,
        )

    async def _monitoring_loop(self) -> None:
        """Main monitoring loop — polls agent status at intervals."""
        # Initial stabilization period
        await asyncio.sleep(3.0)

        while self._active:
            try:
                await self._check_health()
                await asyncio.sleep(self.check_interval_seconds)
            except asyncio.CancelledError:
                break
            except Exception:
                self.log.exception("Error in CrashWatchdog monitoring loop")
                await asyncio.sleep(self.check_interval_seconds)

    async def _check_health(self) -> None:
        """Check if the agent is alive and responsive."""
        from app.agents.base_agent import AgentStatus

        current_status = self.agent.status.value if hasattr(self.agent, 'status') else "unknown"
        self._last_status = current_status

        # Skip checks during recovery
        if self._recovery_in_progress:
            return
        if current_status == AgentStatus.STOPPED.value:
            return

        # Check 1: Heartbeat stale?
        elapsed_since_heartbeat = time.time() - self._last_heartbeat
        if elapsed_since_heartbeat > self.hang_timeout_seconds:
            await self._detect_hang(
                reason=f"No heartbeat for {elapsed_since_heartbeat:.1f}s (timeout={self.hang_timeout_seconds}s)",
                details={"elapsed": round(elapsed_since_heartbeat, 1), "timeout": self.hang_timeout_seconds},
            )

    async def _detect_crash(self, reason: str, details: dict[str, Any] | None = None) -> None:
        """Handle a detected crash."""
        self._crash_count += 1
        self.log.error("💥 CrashWatchdog detected crash: %s (details=%s)", reason, details or {})

        await self._emit(
            AgentWatchdogEventType.AGENT_CRASH_DETECTED,
            reason=reason,
            details=details or {},
            crash_count=self._crash_count,
        )

        await self._execute_recovery(reason, details)

    async def _detect_hang(self, reason: str, details: dict[str, Any] | None = None) -> None:
        """Handle a detected hang."""
        self.log.warning("⏰ CrashWatchdog detected hang: %s", reason)

        await self._emit(
            AgentWatchdogEventType.AGENT_HANG_DETECTED,
            reason=reason,
            details=details or {},
        )

        await self._execute_recovery(reason, details)

    async def _execute_recovery(self, reason: str, details: dict[str, Any] | None = None) -> None:
        """Execute the configured recovery strategy."""
        self._recovery_in_progress = True
        try:
            if self.recovery_strategy == "restart":
                self.log.info("🔄 CrashWatchdog restarting agent %s", self.agent.agent_name)
                try:
                    self.agent._status = type(self.agent.status).INITIALIZING  # type: ignore[union-attr]
                    await self.agent.init()
                    self._consecutive_errors = 0
                    self._last_heartbeat = time.time()
                    self._recovery_count += 1
                    await self._emit(
                        AgentWatchdogEventType.AGENT_CRASH_RECOVERED,
                        reason=reason,
                        recovery_strategy="restart",
                        recovery_count=self._recovery_count,
                    )
                    self.log.info("✅ CrashWatchdog recovery succeeded for %s", self.agent.agent_name)
                except Exception as e:
                    self.log.exception("CrashWatchdog recovery (restart) failed for %s", self.agent.agent_name)
                    # Try escalating on restart failure
                    if self.recovery_strategy != "escalate":
                        await self._execute_recovery(reason, {"original_details": details, "restart_failed": str(e)})

            elif self.recovery_strategy == "escalate":
                self.log.info("🚨 CrashWatchdog escalating from %s", self.agent.agent_name)
                runtime = getattr(self.agent, 'runtime', None)
                if runtime and hasattr(runtime, 'agents'):
                    # Find another agent to delegate the task
                    available = [
                        a for name, a in runtime.agents.items()
                        if name != self.agent.agent_name and getattr(a, 'is_available', False)
                    ]
                    if available:
                        await available[0].handle_event(
                            type("EscalatedEvent", (), {
                                "type": "agent.escalated",
                                "event_type": "agent.escalated",
                                "payload": {
                                    "from_agent": self.agent.agent_name,
                                    "reason": reason,
                                    "details": details or {},
                                },
                            })()
                        )
                        self._recovery_count += 1
                        await self._emit(
                            AgentWatchdogEventType.AGENT_CRASH_RECOVERED,
                            reason=reason,
                            recovery_strategy="escalate",
                            escalated_to=available[0].agent_name,
                        )
            # "report_only" — do nothing, just emit event
        except Exception:
            self.log.exception("CrashWatchdog recovery failed")
        finally:
            self._recovery_in_progress = False


# ======================================================================
# ProgressWatchdog
# ======================================================================


@dataclass
class TaskProgress:
    """Tracks progress of a single task execution."""

    task_id: str
    description: str
    started_at: float = field(default_factory=time.time)
    last_update: float = field(default_factory=time.time)
    steps_completed: int = 0
    total_steps: int = 0
    status: str = "running"  # running, stalled, deadlocked, completed, failed
    error: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def progress_pct(self) -> float:
        if self.total_steps == 0:
            return 0.0
        return min(100.0, (self.steps_completed / self.total_steps) * 100.0)

    @property
    def elapsed(self) -> float:
        return time.time() - self.started_at


class ProgressWatchdog(BaseWatchdog):
    """Monitors task execution progress and detects stalls/deadlocks.

    Tracks active tasks and their step-by-step progress. If a task
    makes no progress for stall_timeout_seconds, emits a stall event.
    If the total execution exceeds deadline_seconds, emits a deadlock event.

    Usage:
        # In agent code:
        await self.progress_wd.start_task("generate_report", total_steps=5)
        # ... do step 1 ...
        await self.progress_wd.advance_task("generate_report", detail="Fetching data")
        # ... do step 2 ...
        await self.progress_wd.advance_task("generate_report", detail="Analyzing")
        # ... on done ...
        await self.progress_wd.complete_task("generate_report", result={...})
    """

    def __init__(
        self,
        agent: BaseAgent,
        stall_timeout_seconds: float = 30.0,
        deadline_seconds: float = 300.0,
        check_interval_seconds: float = 5.0,
        max_concurrent_tasks: int = 20,
    ) -> None:
        super().__init__(agent)
        self.stall_timeout_seconds = stall_timeout_seconds
        self.deadline_seconds = deadline_seconds
        self.check_interval_seconds = check_interval_seconds
        self.max_concurrent_tasks = max_concurrent_tasks

        self._tasks: dict[str, TaskProgress] = {}
        self._completed_tasks: list[TaskProgress] = []
        self._max_completed_history: int = 100

    async def start_task(self, task_id: str, description: str = "", total_steps: int = 0, **metadata: Any) -> None:
        """Start tracking a new task."""
        if len(self._tasks) >= self.max_concurrent_tasks:
            self.log.warning("ProgressWatchdog at max concurrent tasks (%d), dropping %s", self.max_concurrent_tasks, task_id)
            return
        self._tasks[task_id] = TaskProgress(
            task_id=task_id,
            description=description or task_id,
            total_steps=total_steps,
            metadata=metadata,
        )
        self.log.debug("📊 ProgressWatchdog started task: %s (steps=%d)", task_id, total_steps)
        await self._emit(AgentWatchdogEventType.PROGRESS_UPDATE, task_id=task_id, action="started", **metadata)

    async def advance_task(self, task_id: str, steps: int = 1, detail: str = "") -> None:
        """Advance a task by N steps."""
        task = self._tasks.get(task_id)
        if task is None:
            self.log.warning("ProgressWatchdog: task %s not found for advance", task_id)
            return
        task.steps_completed += steps
        task.last_update = time.time()
        self.log.debug("📊 ProgressWatchdog advance %s: %d/%d (%.0f%%)", task_id, task.steps_completed, task.total_steps, task.progress_pct)
        await self._emit(
            AgentWatchdogEventType.PROGRESS_UPDATE,
            task_id=task_id,
            action="advance",
            steps_completed=task.steps_completed,
            total_steps=task.total_steps,
            progress_pct=task.progress_pct,
            detail=detail,
        )

    async def complete_task(self, task_id: str, result: dict[str, Any] | None = None) -> None:
        """Mark a task as completed."""
        task = self._tasks.pop(task_id, None)
        if task is None:
            return
        task.status = "completed"
        task.last_update = time.time()
        if result:
            task.metadata["result"] = result
        self._completed_tasks.append(task)
        if len(self._completed_tasks) > self._max_completed_history:
            self._completed_tasks.pop(0)
        self.log.info("📊 ProgressWatchdog task completed: %s (%.1fs)", task_id, task.elapsed)
        await self._emit(
            AgentWatchdogEventType.TASK_COMPLETED,
            task_id=task_id,
            elapsed=round(task.elapsed, 1),
            steps_completed=task.steps_completed,
            **result if result else {},
        )

    async def fail_task(self, task_id: str, error: str) -> None:
        """Mark a task as failed."""
        task = self._tasks.pop(task_id, None)
        if task is None:
            return
        task.status = "failed"
        task.error = error
        self._completed_tasks.append(task)
        self.log.warning("📊 ProgressWatchdog task failed: %s: %s", task_id, error)
        await self._emit(
            AgentWatchdogEventType.PROGRESS_DEADLOCK_DETECTED,
            task_id=task_id,
            error=error,
            elapsed=round(task.elapsed, 1),
        )

    def get_progress(self, task_id: str) -> TaskProgress | None:
        """Get current progress of a task (non-async, safe for logging)."""
        return self._tasks.get(task_id)

    async def _on_attach(self) -> None:
        """Start progress monitoring loop."""
        self._monitoring_task = asyncio.create_task(self._monitoring_loop())

    async def _monitoring_loop(self) -> None:
        """Periodically check all active tasks for stalls/deadlocks."""
        await asyncio.sleep(2.0)
        while self._active:
            try:
                await self._check_tasks()
                await asyncio.sleep(self.check_interval_seconds)
            except asyncio.CancelledError:
                break
            except Exception:
                self.log.exception("Error in ProgressWatchdog monitoring loop")
                await asyncio.sleep(self.check_interval_seconds)

    async def _check_tasks(self) -> None:
        """Check all active tasks for stalls and deadlines."""
        now = time.time()
        for task_id, task in list(self._tasks.items()):
            # Check deadline exceeded
            if now - task.started_at > self.deadline_seconds:
                task.status = "deadlocked"
                self.log.warning("⏰ ProgressWatchdog deadlock: %s exceeded deadline %.0fs", task_id, self.deadline_seconds)
                await self._emit(
                    AgentWatchdogEventType.PROGRESS_DEADLOCK_DETECTED,
                    task_id=task_id,
                    elapsed=round(now - task.started_at, 1),
                    deadline=self.deadline_seconds,
                    steps_completed=task.steps_completed,
                    total_steps=task.total_steps,
                )
                continue

            # Check stall
            if now - task.last_update > self.stall_timeout_seconds:
                self.log.warning(
                    "⏰ ProgressWatchdog stall: %s idle for %.1fs (progress: %d/%d)",
                    task_id,
                    now - task.last_update,
                    task.steps_completed,
                    task.total_steps,
                )
                await self._emit(
                    AgentWatchdogEventType.PROGRESS_STALL_DETECTED,
                    task_id=task_id,
                    idle_seconds=round(now - task.last_update, 1),
                    stall_timeout=self.stall_timeout_seconds,
                    steps_completed=task.steps_completed,
                    total_steps=task.total_steps,
                )


# ======================================================================
# OutputWatchdog
# ======================================================================


@dataclass
class ValidationResult:
    """Result of an output validation check."""

    passed: bool
    checks: list[dict[str, Any]] = field(default_factory=list)
    score: float = 0.0  # 0.0 to 1.0
    summary: str = ""


class OutputWatchdog(BaseWatchdog):
    """Validates agent outputs for quality, structure, and completeness.

    Inspired by BrowserUse's approach of using dedicated watchdogs for
    specific quality concerns (screenshot_watchdog, recording_watchdog, etc.).

    Supports pluggable validators — each validator is an async function
    that receives the output and returns True/False with a reason.
    """

    def __init__(self, agent: BaseAgent, output_timeout_seconds: float = 60.0) -> None:
        super().__init__(agent)
        self.output_timeout_seconds = output_timeout_seconds
        self._validators: dict[str, Callable[[Any], Coroutine[Any, Any, bool]]] = {}

    def register_validator(
        self,
        name: str,
        validator_fn: Callable[[Any], Coroutine[Any, Any, bool]],
    ) -> None:
        """Register a validator function.

        Args:
            name: Unique validator name (e.g. "has_title", "no_empty_fields").
            validator_fn: Async function that takes output and returns bool.
        """
        self._validators[name] = validator_fn
        self.log.debug("OutputWatchdog registered validator: %s", name)

    async def validate_output(self, output: Any, task_id: str = "") -> ValidationResult:
        """Run all registered validators against an output.

        Args:
            output: The agent's output to validate.
            task_id: Optional task identifier for traceability.

        Returns:
            ValidationResult with pass/fail, individual check results, and score.
        """
        if not self._validators:
            self.log.debug("OutputWatchdog: no validators registered, output auto-approved")
            result = ValidationResult(passed=True, score=1.0, summary="No validators configured")
            await self._emit(
                AgentWatchdogEventType.OUTPUT_VALIDATED,
                task_id=task_id,
                passed=True,
                score=1.0,
                summary="No validators configured",
            )
            return result

        checks: list[dict[str, Any]] = []
        passed_count = 0
        total_count = len(self._validators)

        for name, validator_fn in self._validators.items():
            try:
                is_valid = await validator_fn(output)
                checks.append({"validator": name, "passed": is_valid})
                if is_valid:
                    passed_count += 1
            except Exception as e:
                checks.append({"validator": name, "passed": False, "error": str(e)})
                self.log.warning("OutputWatchdog validator %s raised: %s", name, e)

        score = passed_count / total_count if total_count > 0 else 1.0
        passed = score >= 0.5  # majority pass
        summary = f"Validated: {passed_count}/{total_count} checks passed"

        if passed:
            await self._emit(
                AgentWatchdogEventType.OUTPUT_VALIDATED,
                task_id=task_id,
                passed=True,
                score=score,
                summary=summary,
                checks=checks,
            )
        else:
            await self._emit(
                AgentWatchdogEventType.OUTPUT_VALIDATION_FAILED,
                task_id=task_id,
                passed=False,
                score=score,
                summary=summary,
                checks=checks,
            )

        return ValidationResult(passed=passed, checks=checks, score=score, summary=summary)

    async def _on_attach(self) -> None:
        """Register built-in validators on attach."""
        # Register a default validator for dict outputs with 'content' key
        async def _has_content(output: Any) -> bool:
            if isinstance(output, dict):
                return bool(output.get("content") or output.get("text") or output.get("result"))
            if isinstance(output, str):
                return len(output.strip()) > 0
            return output is not None

        self.register_validator("has_content", _has_content)
        self.log.info("OutputWatchdog attached with %d validator(s)", len(self._validators))


# ======================================================================
# WatchdogManager — convenience for attaching all watchdogs at once
# ======================================================================


class WatchdogManager:
    """Convenience manager that creates and attaches all three watchdogs.

    Usage:
        class MyAgent(BaseAgent):
            async def init(self):
                self.watchdogs = WatchdogManager(self)
                await self.watchdogs.attach_all()
    """

    def __init__(self, agent: BaseAgent) -> None:
        self.agent = agent
        self.crash: CrashWatchdog = CrashWatchdog(agent)
        self.progress: ProgressWatchdog = ProgressWatchdog(agent)
        self.output: OutputWatchdog = OutputWatchdog(agent)

    async def attach_all(self) -> None:
        """Attach all watchdogs to the agent."""
        await self.crash.attach_to_agent()
        await self.progress.attach_to_agent()
        await self.output.attach_to_agent()
        logger.info("All watchdogs attached to agent %s", self.agent.agent_name)

    async def detach_all(self) -> None:
        """Detach all watchdogs from the agent."""
        await self.crash.detach_from_agent()
        await self.progress.detach_from_agent()
        await self.output.detach_from_agent()
        logger.info("All watchdogs detached from agent %s", self.agent.agent_name)
