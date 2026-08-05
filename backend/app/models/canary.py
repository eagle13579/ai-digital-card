"""
canary.py — 灰度发布数据模型 (F17 彩虹部署)

定义 CanaryDeployment（灰度部署）、CanaryGroup（用户分组）、
CanaryRule（放量规则）、CanaryEvent（生命周期事件）等核心模型。
"""
from __future__ import annotations
import time
import uuid
from enum import Enum
from typing import Any


class CanaryStatus(str, Enum):
    """灰度部署状态枚举"""
    PENDING = "pending"            # 待部署
    DEPLOYING = "deploying"        # 部署进行中
    CANARY = "canary"              # 灰度中
    PROMOTED = "promoted"          # 全量发布完成
    ROLLED_BACK = "rolled_back"    # 已回滚
    FAILED = "failed"              # 部署失败
    CANCELLED = "cancelled"        # 已取消


class CanaryStrategy(str, Enum):
    """灰度放量策略"""
    MANUAL = "manual"              # 手动确认放量
    AUTO_TIMED = "auto_timed"      # 定时自动放量
    AUTO_METRIC = "auto_metric"    # 按指标自动放量
    STEPPED = "stepped"            # 阶梯式放量


class TrafficAllocationMode(str, Enum):
    """流量分配模式"""
    PERCENTAGE = "percentage"      # 按流量比例
    USER_GROUP = "user_group"      # 按用户分组
    HYBRID = "hybrid"              # 混合模式


class CanaryGroup:
    """
    用户分组定义。

    Attributes:
        group_id: 分组唯一标识
        name: 分组名称（如 "internal_test", "beta_users", "whitelist"）
        description: 分组描述
        user_ids: 用户 ID 白名单
        user_tags: 用户标签过滤条件（如 {"vip_level": ">=3"}）
        traffic_weight: 该分组在灰度中的流量权重（百分比 0-100）
        created_at: 创建时间戳
        enabled: 是否启用
    """

    def __init__(
        self,
        group_id: str,
        name: str,
        description: str = "",
        user_ids: list[int] | None = None,
        user_tags: dict[str, str] | None = None,
        traffic_weight: float = 100.0,
        enabled: bool = True,
    ):
        self.group_id: str = group_id
        self.name: str = name
        self.description: str = description
        self.user_ids: list[int] = user_ids or []
        self.user_tags: dict[str, str] = user_tags or {}
        self.traffic_weight: float = max(0.0, min(100.0, traffic_weight))
        self.created_at: float = time.time()
        self.enabled: bool = enabled

    def to_dict(self) -> dict[str, Any]:
        return {
            "group_id": self.group_id,
            "name": self.name,
            "description": self.description,
            "user_ids": self.user_ids,
            "user_tags": self.user_tags,
            "traffic_weight": self.traffic_weight,
            "created_at": self.created_at,
            "enabled": self.enabled,
        }

    @staticmethod
    def from_dict(data: dict[str, Any]) -> CanaryGroup:
        obj = CanaryGroup(
            group_id=data["group_id"],
            name=data.get("name", ""),
            description=data.get("description", ""),
            user_ids=data.get("user_ids", []),
            user_tags=data.get("user_tags", {}),
            traffic_weight=data.get("traffic_weight", 100.0),
            enabled=data.get("enabled", True),
        )
        obj.created_at = data.get("created_at", time.time())
        return obj

    def __repr__(self) -> str:
        return f"<CanaryGroup '{self.name}' ({self.group_id}) weight={self.traffic_weight}%>"


class CanaryRule:
    """
    灰度发布规则配置。

    Attributes:
        rule_id: 规则唯一标识
        deployment_id: 所属部署 ID
        strategy: 放量策略（manual / auto_timed / auto_metric / stepped）
        allocation_mode: 流量分配模式
        initial_traffic: 初始灰度流量比例（百分比 0-100）
        target_traffic: 目标全量流量比例（百分比，通常 100）
        current_traffic: 当前灰度流量比例
        steps: 阶梯放量步骤 [{"traffic": 10, "duration": 300}, ...]
        user_groups: 关联的用户分组 ID 列表
        metric_tolerance: 指标容忍度（用于 auto_metric，如错误率 < 1%）
        auto_promote: 是否自动全量发布
        created_at: 创建时间
        updated_at: 最后更新时间
    """

    def __init__(
        self,
        rule_id: str,
        deployment_id: str,
        strategy: CanaryStrategy = CanaryStrategy.MANUAL,
        allocation_mode: TrafficAllocationMode = TrafficAllocationMode.PERCENTAGE,
        initial_traffic: float = 10.0,
        target_traffic: float = 100.0,
        current_traffic: float = 0.0,
        steps: list[dict[str, Any]] | None = None,
        user_groups: list[str] | None = None,
        metric_tolerance: dict[str, float] | None = None,
        auto_promote: bool = False,
    ):
        if initial_traffic < 0 or initial_traffic > 100:
            raise ValueError("initial_traffic 必须在 0-100 之间")
        if target_traffic < 0 or target_traffic > 100:
            raise ValueError("target_traffic 必须在 0-100 之间")

        self.rule_id: str = rule_id
        self.deployment_id: str = deployment_id
        self.strategy: CanaryStrategy = strategy
        self.allocation_mode: TrafficAllocationMode = allocation_mode
        self.initial_traffic: float = initial_traffic
        self.target_traffic: float = target_traffic
        self.current_traffic: float = current_traffic
        self.steps: list[dict[str, Any]] = steps or []
        self.user_groups: list[str] = user_groups or []
        self.metric_tolerance: dict[str, float] = metric_tolerance or {
            "error_rate": 1.0,       # 错误率上限 %
            "latency_p99": 5000,     # p99 延迟上限 ms
            "success_rate": 99.0,    # 成功率下限 %
        }
        self.auto_promote: bool = auto_promote
        self.created_at: float = time.time()
        self.updated_at: float = time.time()

    def to_dict(self) -> dict[str, Any]:
        return {
            "rule_id": self.rule_id,
            "deployment_id": self.deployment_id,
            "strategy": self.strategy.value,
            "allocation_mode": self.allocation_mode.value,
            "initial_traffic": self.initial_traffic,
            "target_traffic": self.target_traffic,
            "current_traffic": self.current_traffic,
            "steps": self.steps,
            "user_groups": self.user_groups,
            "metric_tolerance": self.metric_tolerance,
            "auto_promote": self.auto_promote,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }

    @staticmethod
    def from_dict(data: dict[str, Any]) -> CanaryRule:
        obj = CanaryRule(
            rule_id=data["rule_id"],
            deployment_id=data["deployment_id"],
            strategy=CanaryStrategy(data.get("strategy", "manual")),
            allocation_mode=TrafficAllocationMode(data.get("allocation_mode", "percentage")),
            initial_traffic=data.get("initial_traffic", 10.0),
            target_traffic=data.get("target_traffic", 100.0),
            current_traffic=data.get("current_traffic", 0.0),
            steps=data.get("steps", []),
            user_groups=data.get("user_groups", []),
            metric_tolerance=data.get("metric_tolerance"),
            auto_promote=data.get("auto_promote", False),
        )
        obj.created_at = data.get("created_at", time.time())
        obj.updated_at = data.get("updated_at", time.time())
        return obj

    def __repr__(self) -> str:
        return (
            f"<CanaryRule '{self.rule_id}' "
            f"strategy={self.strategy.value} "
            f"traffic={self.current_traffic}%/{self.target_traffic}%>"
        )


class CanaryEvent:
    """
    灰度部署生命周期事件记录。

    Attributes:
        event_id: 事件唯一标识
        deployment_id: 所属部署 ID
        event_type: 事件类型（deploy, traffic_change, promote, rollback, error, step）
        message: 事件描述
        metadata: 附加元数据
        timestamp: 事件发生时间
    """

    def __init__(
        self,
        deployment_id: str,
        event_type: str,
        message: str = "",
        metadata: dict[str, Any] | None = None,
    ):
        self.event_id: str = f"ce_{uuid.uuid4().hex[:12]}"
        self.deployment_id: str = deployment_id
        self.event_type: str = event_type
        self.message: str = message
        self.metadata: dict[str, Any] = metadata or {}
        self.timestamp: float = time.time()

    def to_dict(self) -> dict[str, Any]:
        return {
            "event_id": self.event_id,
            "deployment_id": self.deployment_id,
            "event_type": self.event_type,
            "message": self.message,
            "metadata": self.metadata,
            "timestamp": self.timestamp,
        }

    def __repr__(self) -> str:
        return (
            f"<CanaryEvent {self.event_type} "
            f"deploy={self.deployment_id} "
            f"at={self.timestamp:.3f}>"
        )


class CanaryDeployment:
    """
    灰度部署实例 — 代表一次完整的灰度发布过程。

    Attributes:
        deployment_id: 部署唯一标识
        name: 部署名称
        version: 部署版本号
        service: 目标服务名称
        status: 当前状态
        rule: 灰度规则配置
        groups: 关联的用户分组列表
        events: 生命周期事件列表
        snapshot_before: 回滚快照（部署前的配置/版本信息）
        created_at: 创建时间
        updated_at: 最后更新时间
        started_at: 部署开始时间
        completed_at: 部署完成/回滚时间
        created_by: 创建者
    """

    def __init__(
        self,
        deployment_id: str,
        name: str,
        version: str,
        service: str,
        rule: CanaryRule,
        groups: list[CanaryGroup] | None = None,
        status: CanaryStatus = CanaryStatus.PENDING,
        snapshot_before: dict[str, Any] | None = None,
        created_by: str = "system",
    ):
        self.deployment_id: str = deployment_id
        self.name: str = name
        self.version: str = version
        self.service: str = service
        self.status: CanaryStatus = status
        self.rule: CanaryRule = rule
        self.groups: list[CanaryGroup] = groups or []
        self.events: list[CanaryEvent] = []
        self.snapshot_before: dict[str, Any] = snapshot_before or {}
        self.created_at: float = time.time()
        self.updated_at: float = time.time()
        self.started_at: float | None = None
        self.completed_at: float | None = None
        self.created_by: str = created_by

    def add_event(
        self,
        event_type: str,
        message: str = "",
        metadata: dict[str, Any] | None = None,
    ) -> CanaryEvent:
        """添加生命周期事件"""
        event = CanaryEvent(
            deployment_id=self.deployment_id,
            event_type=event_type,
            message=message,
            metadata=metadata,
        )
        self.events.append(event)
        self.updated_at = time.time()
        return event

    def to_dict(self) -> dict[str, Any]:
        return {
            "deployment_id": self.deployment_id,
            "name": self.name,
            "version": self.version,
            "service": self.service,
            "status": self.status.value,
            "rule": self.rule.to_dict(),
            "groups": [g.to_dict() for g in self.groups],
            "events": [e.to_dict() for e in self.events[-50:]],  # 最多返回 50 条事件
            "snapshot_before": self.snapshot_before,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "started_at": self.started_at,
            "completed_at": self.completed_at,
            "created_by": self.created_by,
        }

    def to_status_dict(self) -> dict[str, Any]:
        """精简状态摘要"""
        return {
            "deployment_id": self.deployment_id,
            "name": self.name,
            "version": self.version,
            "service": self.service,
            "status": self.status.value,
            "current_traffic": self.rule.current_traffic,
            "target_traffic": self.rule.target_traffic,
            "strategy": self.rule.strategy.value,
            "started_at": self.started_at,
            "completed_at": self.completed_at,
            "created_by": self.created_by,
            "total_events": len(self.events),
        }

    @staticmethod
    def from_dict(data: dict[str, Any]) -> CanaryDeployment:
        rule = CanaryRule.from_dict(data["rule"])
        groups = [CanaryGroup.from_dict(g) for g in data.get("groups", [])]
        obj = CanaryDeployment(
            deployment_id=data["deployment_id"],
            name=data.get("name", ""),
            version=data.get("version", ""),
            service=data.get("service", ""),
            rule=rule,
            groups=groups,
            status=CanaryStatus(data.get("status", "pending")),
            snapshot_before=data.get("snapshot_before", {}),
            created_by=data.get("created_by", "system"),
        )
        obj.events = [CanaryEvent.from_dict(e) for e in data.get("events", [])]
        obj.created_at = data.get("created_at", time.time())
        obj.updated_at = data.get("updated_at", time.time())
        obj.started_at = data.get("started_at")
        obj.completed_at = data.get("completed_at")
        return obj

    def __repr__(self) -> str:
        return (
            f"<CanaryDeployment '{self.name}' "
            f"v{self.version} on {self.service} "
            f"status={self.status.value}>"
        )


# 添加 CanaryEvent.from_dict 静态方法
def _event_from_dict(data: dict[str, Any]) -> CanaryEvent:
    evt = CanaryEvent(
        deployment_id=data.get("deployment_id", ""),
        event_type=data.get("event_type", "unknown"),
        message=data.get("message", ""),
        metadata=data.get("metadata", {}),
    )
    evt.event_id = data.get("event_id", evt.event_id)
    evt.timestamp = data.get("timestamp", evt.timestamp)
    return evt


CanaryEvent.from_dict = staticmethod(_event_from_dict)
