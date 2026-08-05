"""
commander.py — Commander-Worker 调度核心

核心职责：
  1. 任务 DAG 解析与构建（支持与 TaskSlicer 协作）
  2. Worker Agent 调度与派发（6 个预置 Worker）
  3. 状态追踪（节点级 + 任务级）
  4. 结果聚合（所有节点完成后合并结果）
  5. 取消/暂停/重试支持

架构：
  Commander 持有 Worker 池和任务注册表。
  每 tick 扫描所有 RUNNING 任务的 DAG，将 READY 节点派发给空闲 Worker。
  Worker 以异步回调/轮询方式返回结果。
"""

from __future__ import annotations
import asyncio
import logging
import time
import uuid
from typing import Any, Callable

from app.models.commander import (
    CommanderTask,
    CommanderTaskStatus,
    DAGDefinition,
    DAGMode,
    TaskNode,
    TaskNodeStatus,
    WorkerAgent,
    WorkerStatus,
)

logger = logging.getLogger(__name__)


# ── Worker 执行器基类 ────────────────────────────────────


class WorkerExecutor:
    """
    Worker 执行器抽象基类。
    子类实现 _execute 方法以提供具体执行逻辑。

    预置 6 个 Worker：
      - extractor:   信息提取
      - summarizer:  摘要生成
      - analyzer:    分析推理
      - writer:      文本生成/改写
      - translator:  翻译
      - validator:   校验/审核
    """

    CAPABILITY: str = "generic"

    async def execute(
        self, node: TaskNode, worker: WorkerAgent
    ) -> tuple[Any, str | None]:
        """
        执行节点任务。

        Returns:
            (result, error) — 成功时 error 为 None, result 为执行结果;
                              失败时 error 为错误描述, result 可为 None.
        """
        try:
            result = await self._execute(node, worker)
            return result, None
        except Exception as e:
            logger.exception(
                "Worker %s 执行节点 %s 失败: %s",
                worker.worker_id, node.node_id, e,
            )
            return None, str(e)

    async def _execute(self, node: TaskNode, worker: WorkerAgent) -> Any:
        """子类实现此方法"""
        raise NotImplementedError


class ExtractorWorker(WorkerExecutor):
    """信息提取 Worker"""
    CAPABILITY = "extract"

    async def _execute(self, node: TaskNode, worker: WorkerAgent) -> dict:
        content = node.content
        logger.info("[Extractor] 提取信息: %s...", content[:80])
        # 模拟提取逻辑 — 实际项目可对接 LLM / NLP 服务
        return {
            "extracted": True,
            "source_length": len(content),
            "summary": content[:200] if len(content) > 200 else content,
        }


class SummarizerWorker(WorkerExecutor):
    """摘要生成 Worker"""
    CAPABILITY = "summarize"

    async def _execute(self, node: TaskNode, worker: WorkerAgent) -> dict:
        content = node.content
        logger.info("[Summarizer] 生成摘要: %s...", content[:80])
        return {
            "summarized": True,
            "original_length": len(content),
            "summary": content[:100] if len(content) > 100 else content,
        }


class AnalyzerWorker(WorkerExecutor):
    """分析推理 Worker"""
    CAPABILITY = "analyze"

    async def _execute(self, node: TaskNode, worker: WorkerAgent) -> dict:
        content = node.content
        logger.info("[Analyzer] 分析推理: %s...", content[:80])
        return {
            "analyzed": True,
            "analysis": f"分析完成: 内容长度 {len(content)} 字符",
            "keywords": ["AI", "digital", "card"] if "AI" in content else [],
        }


class WriterWorker(WorkerExecutor):
    """文本生成/改写 Worker"""
    CAPABILITY = "write"

    async def _execute(self, node: TaskNode, worker: WorkerAgent) -> dict:
        content = node.content
        logger.info("[Writer] 文本生成: %s...", content[:80])
        return {
            "written": True,
            "output": f"基于输入生成的文本: {content[:100]}...",
        }


class TranslatorWorker(WorkerExecutor):
    """翻译 Worker"""
    CAPABILITY = "translate"

    async def _execute(self, node: TaskNode, worker: WorkerAgent) -> dict:
        content = node.content
        logger.info("[Translator] 翻译处理: %s...", content[:80])
        return {
            "translated": True,
            "source_lang": "auto",
            "target_lang": "en",
            "translation": f"[Translation of {len(content)} chars]",
        }


class ValidatorWorker(WorkerExecutor):
    """校验/审核 Worker"""
    CAPABILITY = "validate"

    async def _execute(self, node: TaskNode, worker: WorkerAgent) -> dict:
        content = node.content
        logger.info("[Validator] 校验审核: %s...", content[:80])
        return {
            "validated": True,
            "passed": len(content) > 0,
            "issues": [],
            "score": 1.0 if content else 0.0,
        }


# ── Worker 执行器注册表 ────────────────────────────────

_BUILTIN_WORKERS: dict[str, type[WorkerExecutor]] = {
    "extract": ExtractorWorker,
    "summarize": SummarizerWorker,
    "analyze": AnalyzerWorker,
    "write": WriterWorker,
    "translate": TranslatorWorker,
    "validate": ValidatorWorker,
}


def get_worker_executor(capability: str) -> WorkerExecutor:
    """根据能力标签获取对应的 Worker 执行器实例"""
    cls = _BUILTIN_WORKERS.get(capability)
    if cls is None:
        # 保底使用通用执行器（直接返回内容）
        return _GenericWorker()
    return cls()


class _GenericWorker(WorkerExecutor):
    """通用保底 Worker"""
    CAPABILITY = "generic"

    async def _execute(self, node: TaskNode, worker: WorkerAgent) -> dict:
        return {
            "executed": True,
            "content_length": len(node.content),
            "note": "Executed by generic worker",
        }


# ── Commander 核心 ──────────────────────────────────────


class Commander:
    """
    指挥官 — 任务调度中枢。

    用法:
        commander = Commander()
        task = await commander.submit_task(
            title="数据采集",
            slices=[...],       # 可选: 预切片的子任务列表
            dag=dag,             # 可选: 预先定义的 DAG
            content="...",       # 可选: 原始大任务文本（自动切片）
        )
        status = commander.get_task_status(task_id)
        dag = commander.get_dag(task_id)
        workers = commander.list_workers()
    """

    def __init__(
        self,
        worker_count: int = 6,
        poll_interval: float = 0.1,
    ):
        # Worker 池
        self.workers: list[WorkerAgent] = []
        self._init_workers(worker_count)

        # 任务注册表
        self.tasks: dict[str, CommanderTask] = {}

        # 执行器缓存
        self._executors: dict[str, WorkerExecutor] = {}

        # 调度控制
        self._running: bool = False
        self._poll_interval: float = poll_interval
        self._scheduler_task: asyncio.Task | None = None

        # 回调钩子
        self._on_node_complete: list[Callable] = []
        self._on_task_complete: list[Callable] = []

        logger.info(
            "Commander 初始化完成: %d Workers, poll_interval=%.2fs",
            len(self.workers), poll_interval,
        )

    # ── Worker 初始化 ─────────────────────────────

    def _init_workers(self, count: int) -> None:
        """初始化 6 个预置 Worker Agent"""
        capability_names = list(_BUILTIN_WORKERS.keys())
        for i in range(count):
            cap = capability_names[i % len(capability_names)]
            worker = WorkerAgent(
                name=f"Worker-{cap}-{i}",
                capability=[cap],
                metadata={"index": i},
            )
            self.workers.append(worker)

    def add_worker(self, worker: WorkerAgent) -> None:
        """动态添加 Worker"""
        self.workers.append(worker)
        logger.info("Commander 添加 Worker: %s (cap=%s)", worker.name, worker.capability)

    def remove_worker(self, worker_id: str) -> bool:
        """移除 Worker"""
        for i, w in enumerate(self.workers):
            if w.worker_id == worker_id:
                self.workers.pop(i)
                logger.info("Commander 移除 Worker: %s", worker_id)
                return True
        return False

    # ── 任务提交 ─────────────────────────────────

    async def submit_task(
        self,
        title: str = "",
        description: str = "",
        task_id: str | None = None,
        content: str | None = None,
        slices: list[dict] | None = None,
        dag: DAGDefinition | None = None,
        user_id: str | None = None,
        metadata: dict | None = None,
    ) -> CommanderTask:
        """
        提交任务到 Commander。

        构建 DAG 的优先级:
          1. dag 参数 — 直接使用显式 DAG
          2. slices 参数 — 从切片列表构建线性 DAG
          3. content 参数 —  使用 TaskSlicer 自动切片

        Returns:
            CommanderTask 对象
        """
        tid = task_id or f"cmd_{uuid.uuid4().hex[:12]}"

        # 确定 DAG
        if dag is not None:
            # 显式 DAG
            dag.validate()
            final_dag = dag
        elif slices:
            # 从切片构建 DAG
            slice_dag = DAGDefinition(
                dag_id=f"dag_{tid}",
                mode=DAGMode.AUTO,
            )
            prev_id: str | None = None
            for i, sl in enumerate(slices):
                node = TaskNode(
                    content=sl.get("content", ""),
                    label=sl.get("label", f"slice_{i}"),
                    node_id=sl.get("node_id"),
                    dependencies=[prev_id] if prev_id else [],
                    metadata=sl.get("metadata", {}),
                    token_estimate=sl.get("token_estimate", 0),
                )
                slice_dag.add_node(node)
                prev_id = node.node_id
            slice_dag.validate()
            final_dag = slice_dag
        elif content:
            # 使用 TaskSlicer 自动切片
            final_dag = await self._auto_slice_to_dag(content, tid)
        else:
            raise ValueError("必须提供 content、slices 或 dag 之一")

        # 创建任务
        task = CommanderTask(
            title=title or tid,
            description=description,
            task_id=tid,
            dag=final_dag,
            user_id=user_id,
            metadata=metadata or {},
        )
        task.status = CommanderTaskStatus.RUNNING
        task.started_at = time.time()

        self.tasks[tid] = task

        logger.info(
            "任务已提交: %s title=%r nodes=%d",
            tid, title, final_dag.total_nodes,
        )

        # 确保调度循环在运行
        self._ensure_scheduler()

        return task

    async def _auto_slice_to_dag(
        self, content: str, task_id: str
    ) -> DAGDefinition:
        """使用 TaskSlicer 自动切片并构建线性 DAG"""
        try:
            from app.services.task_slicer import TaskSlicer
            slicer = TaskSlicer()
            plan = slicer.auto_slice(content, mode="token_budget", task_id=task_id)
            dag = DAGDefinition.from_slice_plan(plan.to_dict(), dag_id=f"dag_{task_id}")
            logger.info(
                "TaskSlicer 自动切片完成: %d slices -> DAG %s",
                plan.slice_count, dag.dag_id,
            )
            return dag
        except ImportError:
            logger.warning("TaskSlicer 不可用，回退到单节点 DAG")
            node = TaskNode(content=content, label="root")
            dag = DAGDefinition(
                dag_id=f"dag_{task_id}",
                nodes=[node],
                mode=DAGMode.FLAT,
            )
            return dag

    # ── 调度循环 ─────────────────────────────────

    def _ensure_scheduler(self) -> None:
        """确保调度循环在运行"""
        if not self._running or self._scheduler_task is None:
            self._running = True
            self._scheduler_task = asyncio.create_task(self._scheduler_loop())
            logger.debug("Commander 调度循环已启动")

    async def _scheduler_loop(self) -> None:
        """调度主循环：扫描 DAG，派发 Ready 节点"""
        while self._running:
            try:
                await self._tick()
            except Exception as e:
                logger.exception("Commander 调度 tick 异常: %s", e)
            await asyncio.sleep(self._poll_interval)

    async def _tick(self) -> None:
        """一个调度 tick"""
        # 1. 收集所有 RUNNING 任务的 Ready 节点
        ready_nodes: list[tuple[str, TaskNode]] = []
        for tid, task in list(self.tasks.items()):
            if task.status not in (
                CommanderTaskStatus.RUNNING, CommanderTaskStatus.SCHEDULING
            ):
                continue
            if task.dag is None:
                continue
            for node in task.dag.get_ready_nodes():
                ready_nodes.append((tid, node))

        if not ready_nodes:
            # 检查是否有任务需要最终化
            self._finalize_completed_tasks()
            return

        # 2. 找到空闲 Worker
        idle_workers = [w for w in self.workers if w.status == WorkerStatus.IDLE]

        if not idle_workers:
            return  # 无可用 Worker，等待下一 tick

        # 3. 匹配并派发
        dispatched = 0
        for tid, node in ready_nodes:
            if dispatched >= len(idle_workers):
                break
            worker = idle_workers[dispatched]

            # 标记节点为 RUNNING
            node.status = TaskNodeStatus.RUNNING
            node.started_at = time.time()
            node.worker_id = worker.worker_id

            # 分配 Worker
            worker.assign(node.node_id)

            # 异步执行（不阻塞调度循环）
            asyncio.create_task(
                self._execute_node(tid, node.node_id, worker)
            )

            dispatched += 1

        if dispatched:
            logger.debug(
                "Commander tick: 派发了 %d 个节点", dispatched,
            )

    def _finalize_completed_tasks(self) -> None:
        """检查并最终化已完成的任务"""
        for tid, task in list(self.tasks.items()):
            if task.status != CommanderTaskStatus.RUNNING:
                continue
            if task.dag is None:
                continue

            dag = task.dag
            all_terminal = all(
                n.status in (
                    TaskNodeStatus.COMPLETED,
                    TaskNodeStatus.FAILED,
                    TaskNodeStatus.SKIPPED,
                    TaskNodeStatus.CANCELLED,
                )
                for n in dag.nodes.values()
            )

            if not all_terminal:
                continue

            # 聚合结果
            completed = [
                n for n in dag.nodes.values()
                if n.status == TaskNodeStatus.COMPLETED
            ]
            failed = [
                n for n in dag.nodes.values()
                if n.status == TaskNodeStatus.FAILED
            ]

            if failed and not completed:
                task.status = CommanderTaskStatus.FAILED
                task.error = f"{len(failed)} 个节点失败"
            elif failed and completed:
                task.status = CommanderTaskStatus.PARTIAL
                task.error = f"{len(failed)} 个节点失败，{len(completed)} 个成功"
            else:
                task.status = CommanderTaskStatus.COMPLETED

            task.completed_at = time.time()
            task.result = self._aggregate_results(dag)

            logger.info(
                "任务完成: %s status=%s total=%d completed=%d failed=%d",
                tid, task.status.value,
                dag.total_nodes, dag.completed_count, len(failed),
            )

            # 触发回调
            for cb in self._on_task_complete:
                try:
                    cb(task)
                except Exception:
                    logger.exception("任务完成回调异常")

    # ── 节点执行 ─────────────────────────────────

    async def _execute_node(
        self, task_id: str, node_id: str, worker: WorkerAgent
    ) -> None:
        """执行单个节点（在独立协程中运行）"""
        task = self.tasks.get(task_id)
        if task is None or task.dag is None:
            return

        node = task.dag.nodes.get(node_id)
        if node is None:
            return

        # 获取执行器
        cap = worker.capability[0] if worker.capability else "generic"
        executor = self._get_executor(cap)

        # 执行
        result, error = await executor.execute(node, worker)

        # 更新节点状态
        if error:
            node.retry_count += 1
            if node.retry_count >= node.max_retries:
                node.status = TaskNodeStatus.FAILED
                node.error = error
                logger.warning(
                    "节点 %s 执行失败（已达最大重试次数 %d）: %s",
                    node_id, node.max_retries, error,
                )
            else:
                # 重试：重置为 PENDING
                node.status = TaskNodeStatus.PENDING
                node.error = error
                node.worker_id = None
                logger.info(
                    "节点 %s 将重试 (%d/%d): %s",
                    node_id, node.retry_count, node.max_retries, error,
                )
        else:
            node.status = TaskNodeStatus.COMPLETED
            node.result = result
            node.completed_at = time.time()
            logger.info(
                "节点 %s 执行完成 (worker=%s)", node_id, worker.worker_id,
            )

        # 释放 Worker
        worker.release()

        # 触发回调
        for cb in self._on_node_complete:
            try:
                cb(task, node)
            except Exception:
                logger.exception("节点完成回调异常")

    def _get_executor(self, capability: str) -> WorkerExecutor:
        """获取或缓存执行器实例"""
        if capability not in self._executors:
            self._executors[capability] = get_worker_executor(capability)
        return self._executors[capability]

    # ── 结果聚合 ─────────────────────────────────

    def _aggregate_results(self, dag: DAGDefinition) -> dict[str, Any]:
        """聚合 DAG 中所有已完成节点的结果"""
        completed = [
            n for n in dag.nodes.values()
            if n.status == TaskNodeStatus.COMPLETED
        ]
        return {
            "total_nodes": dag.total_nodes,
            "completed_count": dag.completed_count,
            "node_results": {
                n.node_id: {
                    "label": n.label,
                    "result": n.result,
                    "worker_id": n.worker_id,
                    "started_at": n.started_at,
                    "completed_at": n.completed_at,
                }
                for n in completed
            },
            "aggregated_at": time.time(),
        }

    # ── 任务控制 ─────────────────────────────────

    async def stop_task(self, task_id: str) -> bool:
        """
        取消/停止正在运行的任务。

        将 DAG 中所有 PENDING 和 RUNNING 的节点标记为 CANCELLED。
        """
        task = self.tasks.get(task_id)
        if task is None:
            return False

        if task.status not in (
            CommanderTaskStatus.RUNNING,
            CommanderTaskStatus.SCHEDULING,
            CommanderTaskStatus.QUEUED,
        ):
            return False

        if task.dag:
            for node in task.dag.nodes.values():
                if node.status in (
                    TaskNodeStatus.PENDING,
                    TaskNodeStatus.RUNNING,
                    TaskNodeStatus.BLOCKED,
                ):
                    node.status = TaskNodeStatus.CANCELLED
                    node.completed_at = time.time()

        task.status = CommanderTaskStatus.CANCELLED
        task.completed_at = time.time()
        logger.info("任务已停止: %s", task_id)
        return True

    async def retry_task(self, task_id: str) -> bool:
        """
        重试失败的任务：将所有 FAILED 节点重置为 PENDING。
        """
        task = self.tasks.get(task_id)
        if task is None:
            return False

        if task.status != CommanderTaskStatus.FAILED:
            return False

        if task.dag:
            for node in task.dag.nodes.values():
                if node.status == TaskNodeStatus.FAILED:
                    node.status = TaskNodeStatus.PENDING
                    node.retry_count = 0
                    node.error = None
                    node.result = None
                    node.started_at = None
                    node.completed_at = None
                    node.worker_id = None

        task.status = CommanderTaskStatus.RUNNING
        task.error = None
        task.result = None
        task.started_at = time.time()
        task.completed_at = None

        logger.info("任务已重试: %s", task_id)
        return True

    async def pause_task(self, task_id: str) -> bool:
        """
        暂停任务：将 RUNNING 节点保留，PENDING 节点标记为 BLOCKED。
        """
        task = self.tasks.get(task_id)
        if task is None:
            return False
        if task.status != CommanderTaskStatus.RUNNING:
            return False

        if task.dag:
            for node in task.dag.nodes.values():
                if node.status == TaskNodeStatus.PENDING:
                    node.status = TaskNodeStatus.BLOCKED

        task.status = CommanderTaskStatus.SCHEDULING
        logger.info("任务已暂停: %s", task_id)
        return True

    async def resume_task(self, task_id: str) -> bool:
        """恢复暂停的任务"""
        task = self.tasks.get(task_id)
        if task is None:
            return False

        if task.dag:
            for node in task.dag.nodes.values():
                if node.status == TaskNodeStatus.BLOCKED:
                    node.status = TaskNodeStatus.PENDING

        task.status = CommanderTaskStatus.RUNNING
        logger.info("任务已恢复: %s", task_id)
        return True

    # ── 查询接口 ─────────────────────────────────

    def get_task(self, task_id: str) -> CommanderTask | None:
        """获取任务详情"""
        return self.tasks.get(task_id)

    def get_task_status(self, task_id: str) -> dict[str, Any] | None:
        """获取任务状态摘要"""
        task = self.tasks.get(task_id)
        if task is None:
            return None
        dag_stats = {}
        if task.dag:
            nodes = task.dag.nodes.values()
            dag_stats = {
                "total_nodes": task.dag.total_nodes,
                "completed_count": task.dag.completed_count,
                "status_counts": self._count_node_statuses(nodes),
            }
        return {
            "task_id": task.task_id,
            "title": task.title,
            "status": task.status.value,
            "error": task.error,
            "dag": dag_stats,
            "created_at": task.created_at,
            "started_at": task.started_at,
            "completed_at": task.completed_at,
        }

    def get_dag(self, task_id: str) -> DAGDefinition | None:
        """获取任务的 DAG 定义"""
        task = self.tasks.get(task_id)
        if task is None:
            return None
        return task.dag

    def list_tasks(
        self,
        status: CommanderTaskStatus | None = None,
    ) -> list[dict[str, Any]]:
        """列出所有任务（概要）"""
        result = []
        for task in self.tasks.values():
            if status and task.status != status:
                continue
            dag_info = {}
            if task.dag:
                dag_info = {
                    "total_nodes": task.dag.total_nodes,
                    "completed_count": task.dag.completed_count,
                }
            result.append({
                "task_id": task.task_id,
                "title": task.title,
                "status": task.status.value,
                "error": task.error,
                "dag": dag_info,
                "created_at": task.created_at,
                "started_at": task.started_at,
                "completed_at": task.completed_at,
            })
        return result

    def list_workers(self) -> list[dict[str, Any]]:
        """列出所有 Worker（含状态）"""
        return [w.to_dict() for w in self.workers]

    def get_worker(self, worker_id: str) -> WorkerAgent | None:
        """获取单个 Worker 详情"""
        for w in self.workers:
            if w.worker_id == worker_id:
                return w
        return None

    def get_task_node(self, task_id: str, node_id: str) -> TaskNode | None:
        """获取任务中的特定节点"""
        task = self.tasks.get(task_id)
        if task is None or task.dag is None:
            return None
        return task.dag.nodes.get(node_id)

    # ── 统计 ─────────────────────────────────────

    def get_stats(self) -> dict[str, Any]:
        """Commander 全局统计"""
        task_counts: dict[str, int] = {}
        for task in self.tasks.values():
            s = task.status.value
            task_counts[s] = task_counts.get(s, 0) + 1

        worker_counts: dict[str, int] = {}
        for w in self.workers:
            s = w.status.value
            worker_counts[s] = worker_counts.get(s, 0) + 1

        return {
            "total_tasks": len(self.tasks),
            "total_workers": len(self.workers),
            "tasks_by_status": task_counts,
            "workers_by_status": worker_counts,
            "builtin_executors": list(_BUILTIN_WORKERS.keys()),
        }

    @staticmethod
    def _count_node_statuses(nodes: list[TaskNode]) -> dict[str, int]:
        counts: dict[str, int] = {}
        for n in nodes:
            s = n.status.value
            counts[s] = counts.get(s, 0) + 1
        return counts

    # ── 生命周期 ─────────────────────────────────

    async def shutdown(self) -> None:
        """关闭 Commander，停止调度循环"""
        self._running = False
        if self._scheduler_task:
            self._scheduler_task.cancel()
            try:
                await self._scheduler_task
            except asyncio.CancelledError:
                pass
            self._scheduler_task = None
        logger.info("Commander 已关闭")

    # ── 钩子注册 ─────────────────────────────────

    def on_node_complete(self, callback: Callable) -> None:
        """注册节点完成回调"""
        self._on_node_complete.append(callback)

    def on_task_complete(self, callback: Callable) -> None:
        """注册任务完成回调"""
        self._on_task_complete.append(callback)


# ── 全局单例 ──────────────────────────────────────────

_commander_instance: Commander | None = None


def get_commander() -> Commander:
    """获取全局 Commander 单例"""
    global _commander_instance
    if _commander_instance is None:
        _commander_instance = Commander(worker_count=6, poll_interval=0.1)
    return _commander_instance


async def init_commander_on_startup() -> None:
    """应用启动时初始化 Commander"""
    commander = get_commander()
    logger.info(
        "Commander 就绪: %d Workers, %d 个内置执行器",
        len(commander.workers), len(_BUILTIN_WORKERS),
    )


async def shutdown_commander() -> None:
    """应用关闭时停止 Commander"""
    global _commander_instance
    if _commander_instance:
        await _commander_instance.shutdown()
        _commander_instance = None
        logger.info("Commander 已关闭并清理")
