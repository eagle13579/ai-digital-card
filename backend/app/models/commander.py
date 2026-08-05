"""
commander.py — Commander-Worker 调度层数据模型

定义 WorkerAgent（工人）、TaskNode（DAG节点）、DAGDefinition（任务有向图）、
CommanderTask（顶层任务）等核心模型。
"""

from __future__ import annotations
import time
import uuid
from enum import Enum
from typing import Any


# ── 枚举类型 ──────────────────────────────────────────


class WorkerStatus(str, Enum):
    """Worker 状态"""
    IDLE = "idle"              # 空闲，可分配任务
    BUSY = "busy"              # 工作中
    ERROR = "error"            # 异常
    OFFLINE = "offline"        # 离线


class TaskNodeStatus(str, Enum):
    """DAG 节点状态"""
    PENDING = "pending"        # 等待被调度
    RUNNING = "running"        # 正在执行
    COMPLETED = "completed"    # 执行成功
    FAILED = "failed"          # 执行失败
    BLOCKED = "blocked"        # 因依赖未完成而阻塞
    SKIPPED = "skipped"        # 已跳过（条件不满足）
    CANCELLED = "cancelled"    # 已取消


class DAGMode(str, Enum):
    """DAG 构建模式"""
    AUTO = "auto"              # 由 Commander 根据切片自动构建
    MANUAL = "manual"          # 用户/外部显式指定 DAG
    FLAT = "flat"              # 扁平（无依赖，并行执行）


class CommanderTaskStatus(str, Enum):
    """顶层任务状态"""
    QUEUED = "queued"          # 已入队
    SCHEDULING = "scheduling"  # 正在解析/构建 DAG
    RUNNING = "running"        # DAG 执行中
    COMPLETED = "completed"    # 所有节点完成（成功或部分跳过）
    FAILED = "failed"          # 存在不可恢复的失败
    CANCELLED = "cancelled"    # 被用户取消
    PARTIAL = "partial"        # 部分完成（部分失败但可接受）


# ── Worker Agent 模型 ────────────────────────────────


class WorkerAgent:
    """
    单个 Worker Agent。

    Attributes:
        worker_id:  唯一标识
        name:       人类可读名称
        status:     当前状态
        capability: 能力标签（如 ["extract", "summarize", "translate"]）
        current_task_node_id: 当前正在执行的节点 ID
        last_heartbeat: 最近一次心跳时间
        metadata:   扩展元数据
    """

    def __init__(
        self,
        worker_id: str | None = None,
        name: str = "",
        capability: list[str] | None = None,
        metadata: dict | None = None,
    ):
        self.worker_id: str = worker_id or f"worker_{uuid.uuid4().hex[:8]}"
        self.name: str = name or self.worker_id
        self.status: WorkerStatus = WorkerStatus.IDLE
        self.capability: list[str] = capability or []
        self.current_task_node_id: str | None = None
        self.last_heartbeat: float = time.time()
        self.metadata: dict[str, Any] = metadata or {}

    def to_dict(self) -> dict[str, Any]:
        return {
            "worker_id": self.worker_id,
            "name": self.name,
            "status": self.status.value,
            "capability": self.capability,
            "current_task_node_id": self.current_task_node_id,
            "last_heartbeat": self.last_heartbeat,
            "metadata": self.metadata,
        }

    def assign(self, task_node_id: str) -> None:
        """分配任务节点给此 Worker"""
        self.status = WorkerStatus.BUSY
        self.current_task_node_id = task_node_id

    def release(self) -> None:
        """释放 Worker"""
        self.status = WorkerStatus.IDLE
        self.current_task_node_id = None

    def heartbeat(self) -> None:
        """心跳更新"""
        self.last_heartbeat = time.time()

    def __repr__(self) -> str:
        return (
            f"<WorkerAgent {self.worker_id} "
            f"status={self.status.value} cap={self.capability}>"
        )


# ── DAG 节点模型 ─────────────────────────────────────


class TaskNode:
    """
    DAG 中的一个任务节点。

    Attributes:
        node_id:       节点唯一标识
        label:         节点标签（如 "步骤一：数据清洗"）
        content:       节点执行内容（指令、提示词、代码片段等）
        status:        执行状态
        worker_id:     负责执行的 Worker ID
        dependencies:  前置节点 ID 列表（入边）
        dependents:    后置节点 ID 列表（出边）— 可选，用于快速正向遍历
        result:        执行结果（任意结构化数据）
        error:         错误信息
        retry_count:   已重试次数
        max_retries:   最大重试次数
        metadata:      扩展元数据
        created_at:    创建时间
        started_at:    开始执行时间
        completed_at:  完成时间
        token_estimate: 预估 Token 消耗（来自 TaskSlicer）
    """

    def __init__(
        self,
        content: str,
        label: str = "",
        node_id: str | None = None,
        dependencies: list[str] | None = None,
        metadata: dict | None = None,
        max_retries: int = 3,
        token_estimate: int = 0,
    ):
        self.node_id: str = node_id or f"node_{uuid.uuid4().hex[:12]}"
        self.label: str = label or self.node_id
        self.content: str = content
        self.status: TaskNodeStatus = TaskNodeStatus.PENDING
        self.worker_id: str | None = None
        self.dependencies: list[str] = dependencies or []
        self.dependents: list[str] = []
        self.result: Any = None
        self.error: str | None = None
        self.retry_count: int = 0
        self.max_retries: int = max_retries
        self.metadata: dict[str, Any] = metadata or {}
        self.created_at: float = time.time()
        self.started_at: float | None = None
        self.completed_at: float | None = None
        self.token_estimate: int = token_estimate

    @property
    def is_ready(self) -> bool:
        """所有前置依赖是否已完成"""
        return all(dep_status == TaskNodeStatus.COMPLETED
                   for dep_status in self.dependencies)  # NOTE: 实际应在 DAG 中对比状态
        # 真正实现在 DAGDefinition.can_execute()

    def to_dict(self) -> dict[str, Any]:
        return {
            "node_id": self.node_id,
            "label": self.label,
            "content": self.content,
            "status": self.status.value,
            "worker_id": self.worker_id,
            "dependencies": self.dependencies,
            "dependents": self.dependents,
            "result": self.result,
            "error": self.error,
            "retry_count": self.retry_count,
            "max_retries": self.max_retries,
            "metadata": self.metadata,
            "created_at": self.created_at,
            "started_at": self.started_at,
            "completed_at": self.completed_at,
            "token_estimate": self.token_estimate,
        }

    @staticmethod
    def from_dict(data: dict[str, Any]) -> TaskNode:
        node = TaskNode(
            content=data.get("content", ""),
            label=data.get("label", ""),
            node_id=data.get("node_id"),
            dependencies=data.get("dependencies", []),
            metadata=data.get("metadata", {}),
            max_retries=data.get("max_retries", 3),
            token_estimate=data.get("token_estimate", 0),
        )
        node.status = TaskNodeStatus(data.get("status", "pending"))
        node.worker_id = data.get("worker_id")
        node.dependents = data.get("dependents", [])
        node.result = data.get("result")
        node.error = data.get("error")
        node.retry_count = data.get("retry_count", 0)
        node.created_at = data.get("created_at", time.time())
        node.started_at = data.get("started_at")
        node.completed_at = data.get("completed_at")
        return node

    def __repr__(self) -> str:
        return (
            f"<TaskNode {self.node_id} label={self.label!r} "
            f"status={self.status.value} deps={len(self.dependencies)}>"
        )


# ── DAG 定义 ─────────────────────────────────────────


class DAGDefinition:
    """
    有向无环图（DAG）任务定义。

    Attributes:
        dag_id:     DAG 唯一标识
        nodes:      所有节点（按 node_id 索引）
        entry_nodes: 无入边的节点（DAG 入口）
        mode:       构建模式
        metadata:   扩展元数据
        created_at: 创建时间
    """

    def __init__(
        self,
        dag_id: str | None = None,
        nodes: list[TaskNode] | None = None,
        mode: DAGMode = DAGMode.AUTO,
        metadata: dict | None = None,
    ):
        self.dag_id: str = dag_id or f"dag_{uuid.uuid4().hex[:12]}"
        self.nodes: dict[str, TaskNode] = {}
        self.entry_nodes: list[str] = []
        self.mode: DAGMode = mode
        self.metadata: dict[str, Any] = metadata or {}
        self.created_at: float = time.time()

        if nodes:
            for node in nodes:
                self.add_node(node)

    def add_node(self, node: TaskNode) -> str:
        """添加节点到 DAG，自动维护依赖关系"""
        self.nodes[node.node_id] = node
        for dep_id in node.dependencies:
            if dep_id in self.nodes:
                if node.node_id not in self.nodes[dep_id].dependents:
                    self.nodes[dep_id].dependents.append(node.node_id)
        return node.node_id

    def _rebuild_entry_nodes(self) -> None:
        """重新计算入口节点（无入边的节点）"""
        all_nodes = set(self.nodes.keys())
        has_incoming = set()
        for node in self.nodes.values():
            for dep_id in node.dependencies:
                if dep_id in self.nodes:
                    has_incoming.add(node.node_id)
        self.entry_nodes = [nid for nid in all_nodes if nid not in has_incoming]

    def validate(self) -> bool:
        """
        验证 DAG 合法性：
        1. 所有依赖的节点必须存在于图中
        2. 无环
        返回 True 表示合法。
        """
        # 1. 依赖存在性
        for nid, node in self.nodes.items():
            for dep_id in node.dependencies:
                if dep_id not in self.nodes:
                    raise ValueError(
                        f"节点 {nid} 依赖的 {dep_id} 不在 DAG 中"
                    )

        # 2. 环检测：DFS
        WHITE, GRAY, BLACK = 0, 1, 2
        color: dict[str, int] = {nid: WHITE for nid in self.nodes}

        def dfs(nid: str) -> bool:
            color[nid] = GRAY
            for dep_id in self.nodes[nid].dependencies:
                if dep_id not in color:
                    continue
                if color[dep_id] == GRAY:
                    return True  # 发现环
                if color[dep_id] == WHITE:
                    if dfs(dep_id):
                        return True
            color[nid] = BLACK
            return False

        for nid in self.nodes:
            if color[nid] == WHITE:
                if dfs(nid):
                    raise ValueError(f"DAG 中存在环，涉及节点 {nid}")

        self._rebuild_entry_nodes()
        return True

    def get_ready_nodes(self) -> list[TaskNode]:
        """
        获取当前可执行的节点集合（所有前置依赖均已 COMPLETED）。
        返回 Ready 列表（保持确定性排序）。
        """
        ready: list[TaskNode] = []
        for node in self.nodes.values():
            if node.status != TaskNodeStatus.PENDING:
                continue
            deps_completed = all(
                self.nodes[dep_id].status == TaskNodeStatus.COMPLETED
                for dep_id in node.dependencies
                if dep_id in self.nodes
            )
            if deps_completed:
                ready.append(node)
        # 按创建时间排序以保持确定性
        ready.sort(key=lambda n: n.created_at)
        return ready

    def get_blocked_nodes(self) -> list[TaskNode]:
        """获取因依赖未就绪而阻塞的 PENDING 节点"""
        blocked: list[TaskNode] = []
        for node in self.nodes.values():
            if node.status != TaskNodeStatus.PENDING:
                continue
            deps_unfinished = any(
                nid in self.nodes
                and self.nodes[nid].status not in (
                    TaskNodeStatus.COMPLETED, TaskNodeStatus.SKIPPED
                )
                for nid in node.dependencies
            )
            if deps_unfinished:
                blocked.append(node)
        return blocked

    @property
    def total_nodes(self) -> int:
        return len(self.nodes)

    @property
    def completed_count(self) -> int:
        return sum(
            1 for n in self.nodes.values()
            if n.status in (TaskNodeStatus.COMPLETED, TaskNodeStatus.SKIPPED)
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "dag_id": self.dag_id,
            "nodes": [n.to_dict() for n in self.nodes.values()],
            "entry_nodes": self.entry_nodes,
            "mode": self.mode.value,
            "metadata": self.metadata,
            "total_nodes": self.total_nodes,
            "completed_count": self.completed_count,
            "created_at": self.created_at,
        }

    @staticmethod
    def from_dict(data: dict[str, Any]) -> DAGDefinition:
        nodes = [TaskNode.from_dict(n) for n in data.get("nodes", [])]
        dag = DAGDefinition(
            dag_id=data.get("dag_id"),
            nodes=nodes,
            mode=DAGMode(data.get("mode", "auto")),
            metadata=data.get("metadata", {}),
        )
        dag.created_at = data.get("created_at", time.time())
        dag._rebuild_entry_nodes()
        return dag

    @staticmethod
    def from_slice_plan(
        slice_plan_dict: dict[str, Any],
        dag_id: str | None = None,
    ) -> DAGDefinition:
        """
        从 TaskSlicer 的 SlicePlan 构建线性依赖 DAG。
        切片按顺序排列：slice0 → slice1 → slice2 → ...
        """
        slices = slice_plan_dict.get("slices", [])
        nodes: list[TaskNode] = []
        prev_id: str | None = None
        for i, sl in enumerate(slices):
            node_id = sl.get("id", f"node_{uuid.uuid4().hex[:12]}")
            deps = [prev_id] if prev_id is not None else []
            node = TaskNode(
                content=sl.get("content", ""),
                label=f"slice_{i}",
                node_id=node_id,
                dependencies=deps,
                metadata={
                    "slice_index": i,
                    "source_slice_id": sl.get("id"),
                    "token_estimate": sl.get("token_estimate", 0),
                    **(sl.get("metadata", {})),
                },
                token_estimate=sl.get("token_estimate", 0),
            )
            nodes.append(node)
            prev_id = node_id

        return DAGDefinition(
            dag_id=dag_id,
            nodes=nodes,
            mode=DAGMode.AUTO,
            metadata={"source_slice_plan_id": slice_plan_dict.get("task_id")},
        )

    def __repr__(self) -> str:
        return (
            f"<DAGDefinition {self.dag_id} "
            f"nodes={self.total_nodes} entry={len(self.entry_nodes)}>"
        )


# ── Commander 顶层任务 ────────────────────────────────


class CommanderTask:
    """
    指挥官顶层任务，包含完整生命周期。

    Attributes:
        task_id:        唯一标识
        title:          任务标题
        description:    任务描述
        status:         顶层状态
        dag:            DAG 定义
        result:         聚合结果
        error:          顶层错误
        user_id:        提交用户（可选）
        metadata:       扩展元数据
        created_at:     创建时间
        started_at:     开始执行时间
        completed_at:   完成时间
    """

    def __init__(
        self,
        title: str = "",
        description: str = "",
        task_id: str | None = None,
        dag: DAGDefinition | None = None,
        user_id: str | None = None,
        metadata: dict | None = None,
    ):
        self.task_id: str = task_id or f"cmd_{uuid.uuid4().hex[:12]}"
        self.title: str = title or self.task_id
        self.description: str = description
        self.status: CommanderTaskStatus = CommanderTaskStatus.QUEUED
        self.dag: DAGDefinition | None = dag
        self.result: Any = None
        self.error: str | None = None
        self.user_id: str | None = user_id
        self.metadata: dict[str, Any] = metadata or {}
        self.created_at: float = time.time()
        self.started_at: float | None = None
        self.completed_at: float | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "task_id": self.task_id,
            "title": self.title,
            "description": self.description,
            "status": self.status.value,
            "dag": self.dag.to_dict() if self.dag else None,
            "result": self.result,
            "error": self.error,
            "user_id": self.user_id,
            "metadata": self.metadata,
            "created_at": self.created_at,
            "started_at": self.started_at,
            "completed_at": self.completed_at,
        }

    @staticmethod
    def from_dict(data: dict[str, Any]) -> CommanderTask:
        dag = None
        if data.get("dag"):
            dag = DAGDefinition.from_dict(data["dag"])
        task = CommanderTask(
            title=data.get("title", ""),
            description=data.get("description", ""),
            task_id=data.get("task_id"),
            dag=dag,
            user_id=data.get("user_id"),
            metadata=data.get("metadata", {}),
        )
        task.status = CommanderTaskStatus(data.get("status", "queued"))
        task.result = data.get("result")
        task.error = data.get("error")
        task.created_at = data.get("created_at", time.time())
        task.started_at = data.get("started_at")
        task.completed_at = data.get("completed_at")
        return task

    def __repr__(self) -> str:
        return (
            f"<CommanderTask {self.task_id} title={self.title!r} "
            f"status={self.status.value} dag_nodes={self.dag.total_nodes if self.dag else 0}>"
        )
