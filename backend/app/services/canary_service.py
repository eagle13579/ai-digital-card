"""
canary_service.py — 灰度发布引擎 (F17 彩虹部署)

核心能力：
  1. 流量比例分配（百分比/用户分组/混合模式）
  2. 用户分组管理与路由判断
  3. 放量策略（手动/定时/阶梯/按指标自动放量）
  4. 一键回滚（基于部署前快照）
  5. 部署生命周期管理

依赖:
  - F10 Commander（通过 Commander 调度多服务部署任务）
  - 本服务模型: CanaryDeployment, CanaryRule, CanaryGroup, CanaryEvent, CanaryStatus
"""
from __future__ import annotations
import asyncio
import logging
import math
import random
import time
import uuid
from typing import Any

from app.models.canary import (
    CanaryDeployment,
    CanaryEvent,
    CanaryGroup,
    CanaryRule,
    CanaryStatus,
    CanaryStrategy,
    TrafficAllocationMode,
)

logger = logging.getLogger(__name__)


# ──────────────────────────────────────────────
# 默认配置常量
# ──────────────────────────────────────────────
DEFAULT_CANARY_TRAFFIC = 10.0         # 默认初始灰度比例 10%
DEFAULT_MAX_TRAFFIC_STEP = 20.0       # 单次最大放量步长 20%
DEFAULT_STEP_WAIT_SECONDS = 300       # 阶梯放量默认等待 5 分钟
DEFAULT_AUTO_PROMOTE_WAIT = 600       # 自动放量默认等待 10 分钟
MAX_EVENTS_PER_DEPLOYMENT = 500       # 每个部署最大事件数


# ──────────────────────────────────────────────
# 异常类
# ──────────────────────────────────────────────

class CanaryError(Exception):
    """灰度发布通用异常"""
    pass


class DeploymentNotFoundError(CanaryError):
    """部署不存在"""
    pass


class DeploymentStateError(CanaryError):
    """部署状态不允许操作"""
    pass


class InvalidTrafficError(CanaryError):
    """流量分配无效"""
    pass


# ──────────────────────────────────────────────
# 灰度发布引擎
# ──────────────────────────────────────────────

class CanaryService:
    """
    灰度发布引擎 — 管理一次灰度发布的完整生命周期。

    职责：
      - 创建/启动/放量/回滚/完成 灰度部署
      - 管理用户分组
      - 判断用户是否命中灰度
      - 执行放量策略（手动/定时/阶梯/按指标）
    """

    def __init__(self, deployment: CanaryDeployment):
        self._deployment: CanaryDeployment = deployment
        self._active: bool = True
        logger.info(
            "灰度引擎初始化: '%s' v%s on %s (策略=%s, 模式=%s)",
            deployment.name, deployment.version, deployment.service,
            deployment.rule.strategy.value, deployment.rule.allocation_mode.value,
        )

    # ── 属性 ────────────────────────────────

    @property
    def deployment(self) -> CanaryDeployment:
        return self._deployment

    @property
    def status(self) -> CanaryStatus:
        return self._deployment.status

    @property
    def current_traffic(self) -> float:
        return self._deployment.rule.current_traffic

    @property
    def is_active(self) -> bool:
        return self._active

    # ── 部署生命周期 ──────────────────────

    def start(self) -> CanaryDeployment:
        """启动灰度部署"""
        dep = self._deployment
        if dep.status not in (CanaryStatus.PENDING, CanaryStatus.CANCELLED):
            raise DeploymentStateError(
                f"部署 '{dep.deployment_id}' 当前状态为 {dep.status.value}，无法启动"
            )

        dep.status = CanaryStatus.DEPLOYING
        dep.started_at = time.time()

        # 设置初始流量
        dep.rule.current_traffic = dep.rule.initial_traffic

        dep.add_event("deploy", f"灰度部署启动: 初始流量 {dep.rule.initial_traffic}%", {
            "version": dep.version,
            "service": dep.service,
            "initial_traffic": dep.rule.initial_traffic,
            "strategy": dep.rule.strategy.value,
            "allocation_mode": dep.rule.allocation_mode.value,
        })

        # 如果初始流量 > 0，进入灰度状态
        if dep.rule.initial_traffic > 0:
            dep.status = CanaryStatus.CANARY

        logger.info(
            "灰度部署已启动: '%s' v%s 初始流量=%.1f%%",
            dep.name, dep.version, dep.rule.initial_traffic,
        )
        return dep

    def promote(self) -> CanaryDeployment:
        """全量发布 — 将流量提升到 target_traffic"""
        dep = self._deployment
        if dep.status != CanaryStatus.CANARY:
            raise DeploymentStateError(
                f"部署 '{dep.deployment_id}' 当前状态为 {dep.status.value}，无法全量发布"
            )

        old_traffic = dep.rule.current_traffic
        dep.rule.current_traffic = dep.rule.target_traffic
        dep.status = CanaryStatus.PROMOTED
        dep.completed_at = time.time()

        dep.add_event("promote",
            f"全量发布: {old_traffic}% → {dep.rule.target_traffic}%",
            {"old_traffic": old_traffic, "new_traffic": dep.rule.target_traffic},
        )

        logger.info(
            "灰度部署已全量发布: '%s' v%s %.1f%% → %.1f%%",
            dep.name, dep.version, old_traffic, dep.rule.target_traffic,
        )
        return dep

    def rollback(self, reason: str = "管理员手动回滚") -> CanaryDeployment:
        """
        一键回滚 — 恢复到部署前的快照状态。

        回滚会：
          1. 将流量重置为 0%
          2. 将状态设为 ROLLED_BACK
          3. 记录回滚事件（附带快照信息）
        """
        dep = self._deployment
        if dep.status in (CanaryStatus.PENDING, CanaryStatus.ROLLED_BACK, CanaryStatus.CANCELLED):
            raise DeploymentStateError(
                f"部署 '{dep.deployment_id}' 当前状态为 {dep.status.value}，无法回滚"
            )

        old_traffic = dep.rule.current_traffic
        dep.rule.current_traffic = 0.0
        dep.status = CanaryStatus.ROLLED_BACK
        dep.completed_at = time.time()

        dep.add_event("rollback", reason, {
            "old_traffic": old_traffic,
            "snapshot": dep.snapshot_before,
            "reason": reason,
        })

        logger.warning(
            "灰度部署已回滚: '%s' v%s (原因: %s)",
            dep.name, dep.version, reason,
        )
        return dep

    def cancel(self, reason: str = "管理员取消") -> CanaryDeployment:
        """取消灰度部署"""
        dep = self._deployment
        if dep.status in (CanaryStatus.PROMOTED, CanaryStatus.ROLLED_BACK, CanaryStatus.CANCELLED):
            raise DeploymentStateError(
                f"部署 '{dep.deployment_id}' 当前状态为 {dep.status.value}，无法取消"
            )

        dep.rule.current_traffic = 0.0
        dep.status = CanaryStatus.CANCELLED
        dep.completed_at = time.time()

        dep.add_event("cancel", reason)
        logger.info("灰度部署已取消: '%s' v%s", dep.name, dep.version)
        return dep

    # ── 流量管理 ──────────────────────────

    def set_traffic(self, percentage: float) -> CanaryDeployment:
        """
        手动设置灰度流量比例。

        Args:
            percentage: 目标流量比例 (0-100)

        Raises:
            InvalidTrafficError: 比例超出范围
            DeploymentStateError: 部署状态不允许
        """
        dep = self._deployment
        if dep.status != CanaryStatus.CANARY:
            raise DeploymentStateError(
                f"部署 '{dep.deployment_id}' 状态为 {dep.status.value}，不可调整流量"
            )
        if percentage < 0 or percentage > 100:
            raise InvalidTrafficError("流量比例必须在 0-100 之间")
        if percentage > dep.rule.target_traffic:
            raise InvalidTrafficError(
                f"流量比例 {percentage}% 超过目标 {dep.rule.target_traffic}%"
            )

        old_traffic = dep.rule.current_traffic
        dep.rule.current_traffic = percentage
        dep.rule.updated_at = time.time()

        dep.add_event("traffic_change",
            f"流量调整: {old_traffic}% → {percentage}%",
            {"old_traffic": old_traffic, "new_traffic": percentage},
        )

        logger.info("灰度流量调整: '%s' %.1f%% → %.1f%%", dep.name, old_traffic, percentage)

        # 如果达到目标流量，自动全量
        if percentage >= dep.rule.target_traffic and dep.rule.auto_promote:
            return self.promote()

        return dep

    def adjust_traffic_step(self, delta: float) -> CanaryDeployment:
        """
        按步长调整流量（用于阶梯放量）。

        Args:
            delta: 要增加的流量百分比（正数放量，负数缩量）
        """
        new_traffic = max(0.0, min(
            self._deployment.rule.target_traffic,
            self._deployment.rule.current_traffic + delta,
        ))
        return self.set_traffic(new_traffic)

    # ── 用户分组管理 ──────────────────────

    def add_group(self, group: CanaryGroup) -> list[CanaryGroup]:
        """添加用户分组"""
        # 去重：如果 group_id 已存在则替换
        existing = [g for g in self._deployment.groups if g.group_id == group.group_id]
        if existing:
            self._deployment.groups.remove(existing[0])
        self._deployment.groups.append(group)
        self._deployment.add_event("group_add", f"添加用户分组 '{group.name}'", {
            "group_id": group.group_id,
            "user_count": len(group.user_ids),
        })
        return self._deployment.groups

    def remove_group(self, group_id: str) -> list[CanaryGroup]:
        """移除用户分组"""
        group = next((g for g in self._deployment.groups if g.group_id == group_id), None)
        if group:
            self._deployment.groups.remove(group)
            self._deployment.add_event("group_remove", f"移除用户分组 '{group.name}'")
        return self._deployment.groups

    def get_groups(self) -> list[CanaryGroup]:
        """获取所有用户分组"""
        return list(self._deployment.groups)

    def is_user_in_canary(self, user_id: int) -> bool:
        """
        判断用户是否在灰度范围内。

        根据分配模式判断：
          - PERCENTAGE: 基于 user_id hash 一致性判断
          - USER_GROUP: 检查用户是否在任一分组中
          - HYBRID: 同时在分组中且命中流量比例
        """
        dep = self._deployment
        if dep.status != CanaryStatus.CANARY:
            return False
        if dep.rule.current_traffic <= 0:
            return False

        mode = dep.rule.allocation_mode

        if mode == TrafficAllocationMode.PERCENTAGE:
            return self._match_by_percentage(user_id, dep.rule.current_traffic)

        if mode == TrafficAllocationMode.USER_GROUP:
            return self._match_by_user_group(user_id)

        # HYBRID: 在分组中 且 命中流量比例
        if mode == TrafficAllocationMode.HYBRID:
            if not self._match_by_user_group(user_id):
                return False
            return self._match_by_percentage(user_id, dep.rule.current_traffic)

        return False

    def get_canary_user_ids(self) -> set[int]:
        """
        获取当前灰度覆盖的所有用户 ID。
        仅对 USER_GROUP / HYBRID 模式有效。
        """
        if self._deployment.rule.allocation_mode == TrafficAllocationMode.PERCENTAGE:
            return set()
        user_ids: set[int] = set()
        for group in self._deployment.groups:
            user_ids.update(group.user_ids)
        return user_ids

    def _match_by_percentage(self, user_id: int, percentage: float) -> bool:
        """
        基于一致性哈希的用户流量匹配。

        使用 user_id 的确定性 hash 来判断是否落在灰度范围内。
        保证同一用户始终落在同一组，避免灰度"闪烁"。
        """
        # 确定性 hash
        hash_val = (hash(f"canary:{user_id}") & 0x7FFFFFFF) % 10000
        threshold = int(percentage * 100)  # 百分比转为万分数
        return hash_val < threshold

    def _match_by_user_group(self, user_id: int) -> bool:
        """检查用户是否在任意启用的用户分组中"""
        for group in self._deployment.groups:
            if not group.enabled:
                continue
            if user_id in group.user_ids:
                return True
            # 如果定义了标签过滤条件，则通过标签匹配
            if group.user_tags:
                # 这里简化处理：如果分组有标签条件且用户ID匹配（实际应从标签服务查询）
                # 真实实现中应调用 tags_service.get_user_tags(user_id) 进行比对
                pass
        return False

    # ── 放量策略 ──────────────────────────

    async def execute_auto_strategy(self) -> None:
        """
        按配置的放量策略自动执行灰度放量。

        根据 strategy 类型：
          - AUTO_TIMED: 定时递增流量直到全量
          - STEPPED: 按配置的阶梯逐步放量
          - AUTO_METRIC: 监控指标，达标后自动放量（需要外部注入指标）
          - MANUAL: 不做自动操作，等待手动触发
        """
        dep = self._deployment
        if dep.status != CanaryStatus.CANARY:
            return

        strategy = dep.rule.strategy

        if strategy == CanaryStrategy.MANUAL:
            logger.info("手动策略: '%s' 等待管理员操作", dep.name)
            return

        if strategy == CanaryStrategy.AUTO_TIMED:
            await self._execute_auto_timed()

        elif strategy == CanaryStrategy.STEPPED:
            await self._execute_stepped()

        elif strategy == CanaryStrategy.AUTO_METRIC:
            logger.info("按指标放量: '%s' 等待指标回调", dep.name)
            # auto_metric 需要外部调用 check_metrics_and_promote()

    async def _execute_auto_timed(self) -> None:
        """
        定时自动放量策略：
          每隔 DEFAULT_AUTO_PROMOTE_WAIT 秒增加 DEFAULT_MAX_TRAFFIC_STEP%，
          直到达到 target_traffic。
        """
        dep = self._deployment
        target = dep.rule.target_traffic
        step = DEFAULT_MAX_TRAFFIC_STEP
        wait = DEFAULT_AUTO_PROMOTE_WAIT

        logger.info(
            "定时放量启动: '%s' 当前=%.1f%% 目标=%.1f%% 步长=%.1f%% 间隔=%ds",
            dep.name, dep.rule.current_traffic, target, step, wait,
        )

        while dep.status == CanaryStatus.CANARY and dep.rule.current_traffic < target:
            await asyncio.sleep(wait)
            if dep.status != CanaryStatus.CANARY:
                break

            new_traffic = min(target, dep.rule.current_traffic + step)
            self.set_traffic(new_traffic)
            logger.info(
                "定时放量: '%s' %.1f%% → %.1f%% (目标 %.1f%%)",
                dep.name, dep.rule.current_traffic - step, new_traffic, target,
            )

    async def _execute_stepped(self) -> None:
        """
        阶梯放量策略：
          按 rule.steps 中定义的步骤依次放量。
          每步格式: {"traffic": 20, "duration": 300} — 30% 流量持续 5 分钟
        """
        dep = self._deployment
        steps = dep.rule.steps

        if not steps:
            logger.warning("阶梯策略但未配置步骤: '%s'", dep.name)
            return

        logger.info(
            "阶梯放量启动: '%s' %d 步",
            dep.name, len(steps),
        )

        for i, step in enumerate(steps):
            traffic = float(step.get("traffic", 0))
            duration = int(step.get("duration", DEFAULT_STEP_WAIT_SECONDS))

            if traffic > dep.rule.target_traffic:
                traffic = dep.rule.target_traffic

            self.set_traffic(traffic)
            dep.add_event("step",
                f"阶梯放量 第{i+1}/{len(steps)}步: 流量={traffic}% 持续={duration}s",
                {"step": i + 1, "total_steps": len(steps), "traffic": traffic, "duration": duration},
            )

            if traffic >= dep.rule.target_traffic:
                if dep.rule.auto_promote:
                    self.promote()
                return

            await asyncio.sleep(duration)

            if dep.status != CanaryStatus.CANARY:
                logger.info("阶梯放量中断: '%s' 状态已变更为 %s", dep.name, dep.status.value)
                return

    def check_metrics_and_promote(
        self,
        error_rate: float | None = None,
        success_rate: float | None = None,
        latency_p99: float | None = None,
    ) -> dict[str, Any]:
        """
        检查指标并自动放量（AUTO_METRIC 策略使用）。

        Args:
            error_rate: 当前错误率（%）
            success_rate: 当前成功率（%）
            latency_p99: 当前 p99 延迟（ms）

        Returns:
            {"should_promote": bool, "reason": str, "traffic": float}

        如果所有指标在容忍范围内，自动递增流量。
        """
        dep = self._deployment
        tolerance = dep.rule.metric_tolerance
        result: dict[str, Any] = {"should_promote": False, "reason": "", "traffic": dep.rule.current_traffic}

        violations: list[str] = []

        if error_rate is not None and error_rate > tolerance.get("error_rate", 1.0):
            violations.append(f"错误率 {error_rate}% > 阈值 {tolerance['error_rate']}%")

        if success_rate is not None and success_rate < tolerance.get("success_rate", 99.0):
            violations.append(f"成功率 {success_rate}% < 阈值 {tolerance['success_rate']}%")

        if latency_p99 is not None and latency_p99 > tolerance.get("latency_p99", 5000):
            violations.append(f"p99延迟 {latency_p99}ms > 阈值 {tolerance['latency_p99']}ms")

        if violations:
            result["reason"] = "指标未达标: " + "; ".join(violations)
            dep.add_event("metric_block", result["reason"], {
                "error_rate": error_rate,
                "success_rate": success_rate,
                "latency_p99": latency_p99,
                "tolerance": tolerance,
            })
            return result

        # 指标达标，自动递增流量
        new_traffic = min(
            dep.rule.target_traffic,
            dep.rule.current_traffic + DEFAULT_MAX_TRAFFIC_STEP,
        )
        self.set_traffic(new_traffic)

        if new_traffic >= dep.rule.target_traffic and dep.rule.auto_promote:
            self.promote()
            result["should_promote"] = True
            result["reason"] = "指标达标，自动全量发布"

        result["traffic"] = new_traffic
        result["reason"] = result.get("reason") or f"指标达标，流量递增至 {new_traffic}%"

        dep.add_event("metric_promote", f"指标达标自动放量: {new_traffic}%", {
            "error_rate": error_rate,
            "success_rate": success_rate,
            "latency_p99": latency_p99,
        })

        return result

    # ── 快照管理 ──────────────────────────

    def take_snapshot(self) -> dict[str, Any]:
        """
        拍摄当前部署配置快照，用于回滚恢复。

        快照包含：服务当前版本、配置、路由规则等。
        """
        dep = self._deployment
        snapshot = {
            "service": dep.service,
            "version": dep.version,
            "traffic": dep.rule.current_traffic,
            "strategy": dep.rule.strategy.value,
            "target_traffic": dep.rule.target_traffic,
            "groups": [g.to_dict() for g in dep.groups],
            "timestamp": time.time(),
        }
        dep.snapshot_before = snapshot
        dep.add_event("snapshot", "已拍摄部署快照", snapshot)
        return snapshot

    # ── 状态查询 ──────────────────────────

    def get_status(self) -> dict[str, Any]:
        """获取当前部署状态摘要"""
        dep = self._deployment
        return dep.to_status_dict()

    def get_full_status(self) -> dict[str, Any]:
        """获取完整部署详情"""
        dep = self._deployment
        data = dep.to_dict()
        data["is_active"] = self._active
        return data


# ──────────────────────────────────────────────
# 灰度发布注册表（全局管理）
# ──────────────────────────────────────────────

class CanaryRegistry:
    """
    灰度发布注册表 — 全局管理所有 CanaryService 实例。

    用法:
        registry = CanaryRegistry()
        service = registry.create_deployment("v2.1.0", "user-service")
        service.start()
        registry.rollback("deploy_xxx")
    """

    def __init__(self):
        self._services: dict[str, CanaryService] = {}
        self._lock = asyncio.Lock()
        logger.info("灰度发布注册表初始化完成")

    # ── 创建与获取 ────────────────────────

    def create_deployment(
        self,
        name: str,
        version: str,
        service: str,
        strategy: CanaryStrategy = CanaryStrategy.MANUAL,
        allocation_mode: TrafficAllocationMode = TrafficAllocationMode.PERCENTAGE,
        initial_traffic: float = DEFAULT_CANARY_TRAFFIC,
        target_traffic: float = 100.0,
        steps: list[dict[str, Any]] | None = None,
        user_groups: list[CanaryGroup] | None = None,
        auto_promote: bool = False,
        created_by: str = "system",
        snapshot_before: dict[str, Any] | None = None,
    ) -> CanaryService:
        """
        创建新的灰度部署。

        Returns:
            CanaryService 实例（尚未 start）
        """
        deployment_id = f"deploy_{uuid.uuid4().hex[:12]}"

        rule = CanaryRule(
            rule_id=f"rule_{uuid.uuid4().hex[:8]}",
            deployment_id=deployment_id,
            strategy=strategy,
            allocation_mode=allocation_mode,
            initial_traffic=initial_traffic,
            target_traffic=target_traffic,
            steps=steps or [],
            auto_promote=auto_promote,
        )

        # 如果未提供分组，创建一个默认分组
        groups = user_groups or []
        if not groups:
            default_group = CanaryGroup(
                group_id=f"grp_{uuid.uuid4().hex[:8]}",
                name="default",
                description="默认灰度分组",
                traffic_weight=initial_traffic,
            )
            groups = [default_group]

        deployment = CanaryDeployment(
            deployment_id=deployment_id,
            name=name,
            version=version,
            service=service,
            rule=rule,
            groups=groups,
            status=CanaryStatus.PENDING,
            snapshot_before=snapshot_before or {},
            created_by=created_by,
        )

        service_obj = CanaryService(deployment)
        self._services[deployment_id] = service_obj
        logger.info(
            "灰度创建: '%s' v%s on %s (id=%s)",
            name, version, service, deployment_id,
        )
        return service_obj

    def get(self, deployment_id: str) -> CanaryService | None:
        """获取指定部署的服务实例"""
        return self._services.get(deployment_id)

    def get_or_raise(self, deployment_id: str) -> CanaryService:
        """获取指定部署，不存在则抛出异常"""
        svc = self.get(deployment_id)
        if svc is None:
            raise DeploymentNotFoundError(f"部署 '{deployment_id}' 不存在")
        return svc

    # ── 生命周期快捷操作 ──────────────────

    def start_deployment(self, deployment_id: str) -> CanaryDeployment:
        """启动部署的快捷方法"""
        svc = self.get_or_raise(deployment_id)
        return svc.start()

    def rollback(self, deployment_id: str, reason: str = "管理员手动回滚") -> CanaryDeployment:
        """一键回滚的快捷方法"""
        svc = self.get_or_raise(deployment_id)
        return svc.rollback(reason)

    def promote(self, deployment_id: str) -> CanaryDeployment:
        """全量发布的快捷方法"""
        svc = self.get_or_raise(deployment_id)
        return svc.promote()

    def set_traffic(self, deployment_id: str, percentage: float) -> CanaryDeployment:
        """设置流量的快捷方法"""
        svc = self.get_or_raise(deployment_id)
        return svc.set_traffic(percentage)

    # ── 查询 ──────────────────────────────

    def list_deployments(self, service: str | None = None, status: CanaryStatus | None = None) -> list[dict[str, Any]]:
        """列出所有部署（可过滤）"""
        result = []
        for svc in self._services.values():
            dep = svc.deployment
            if service and dep.service != service:
                continue
            if status and dep.status != status:
                continue
            result.append(dep.to_status_dict())
        return result

    def list_active(self) -> list[dict[str, Any]]:
        """列出所有活跃（灰度中）的部署"""
        return [
            svc.deployment.to_status_dict()
            for svc in self._services.values()
            if svc.deployment.status == CanaryStatus.CANARY
        ]

    def count(self) -> int:
        """当前注册的部署数量"""
        return len(self._services)

    def remove(self, deployment_id: str) -> bool:
        """从注册表中移除部署（不删除历史记录）"""
        if deployment_id in self._services:
            del self._services[deployment_id]
            logger.info("灰度注册表: 移除 '%s'", deployment_id)
            return True
        return False

    def get_service_groups(self, service_name: str | None = None) -> list[CanaryGroup]:
        """
        获取所有服务的用户分组。

        Args:
            service_name: 可选，按服务名过滤
        """
        groups: dict[str, CanaryGroup] = {}
        for svc in self._services.values():
            if service_name and svc.deployment.service != service_name:
                continue
            for g in svc.deployment.groups:
                groups[g.group_id] = g
        return list(groups.values())


# 全局单例
canary_registry = CanaryRegistry()
