"""Canary模型部署 — 安全滚动发布AI模型

架构:
  CanaryDeployManager
  ├── register_model(name, version, gateway)  注册新模型版本
  ├── set_traffic_split(model_name, old%, new%)  设置流量分配
  ├── route_request(model_name, context)  按流量分配路由到具体版本
  ├── collect_metrics(model_name)  收集性能指标
  ├── auto_promote(model_name, threshold)  指标达标则自动提升
  └── rollback(model_name)  一键回滚

流量分配算法:
  - 基于一致性hash: 同一用户始终路由到同一版本(避免体验不一致)
  - 支持百分比: 5%→10%→25%→50%→100% 渐进式
  - 自动回滚: 新版本错误率>5%或延迟>2x基线,自动回滚

指标收集:
  - 请求延迟P50/P95/P99
  - 错误率
  - Token消耗
  - 用户满意度(如果有反馈)
"""

from __future__ import annotations

import dataclasses
import hashlib
import logging
import time
import uuid
from collections import defaultdict
from typing import Any

from app.ai.gateway.interfaces import (
    AIRequest,
    AIResponse,
    AIGatewayProtocol,
)
from app.ai.gateway.model_registry import ModelRegistry

logger = logging.getLogger(__name__)

# ======================================================================
# Data Models
# ======================================================================


@dataclasses.dataclass
class VersionEntry:
    """A registered model version for canary deployment.

    Attributes:
        version: Version string (e.g. "v1.0", "v2.0-beta").
        gateway: The AIGatewayProtocol instance serving this version.
        traffic_weight: Traffic weight (0.0 = no traffic, 1.0 = 100%).
        deployed_at: Unix timestamp of deployment.
        status: One of "staging", "canary", "active", "rolled_back", "promoted".
    """
    version: str
    gateway: AIGatewayProtocol
    traffic_weight: float = 0.0
    deployed_at: float = dataclasses.field(default_factory=time.time)
    status: str = "staging"  # staging / canary / active / rolled_back / promoted


@dataclasses.dataclass
class TrafficSplit:
    """Traffic split configuration between old and new model versions.

    Attributes:
        model_name: Name of the model (e.g. "business-card-lora").
        old_version: The currently active (baseline) version.
        new_version: The canary version being rolled out.
        new_percent: Percentage of traffic to route to new_version (0-100).
        baseline_percent: Percentage for old_version (100 - new_percent).
    """
    model_name: str
    old_version: str
    new_version: str
    new_percent: int = 5  # Start at 5%, increase gradually
    baseline_percent: int = 95  # 100 - new_percent


@dataclasses.dataclass
class VersionMetrics:
    """Performance metrics for a single model version.

    Attributes:
        version: The version identifier.
        total_requests: Total number of requests routed to this version.
        total_errors: Total number of errors.
        latencies_ms: List of recent latencies for P50/P95/P99 calculation.
        total_tokens: Total token consumption.
        error_rate: Computed error rate (errors / total_requests).
        p50_latency: 50th percentile latency (ms).
        p95_latency: 95th percentile latency (ms).
        p99_latency: 99th percentile latency (ms).
    """
    version: str
    total_requests: int = 0
    total_errors: int = 0
    latencies_ms: list[float] = dataclasses.field(default_factory=list)
    total_tokens: int = 0
    error_rate: float = 0.0
    p50_latency: float = 0.0
    p95_latency: float = 0.0
    p99_latency: float = 0.0
    # 用户满意度 (如果有反馈)
    user_satisfaction: float = 0.0
    satisfaction_count: int = 0

    def update(self, latency_ms: float, is_error: bool, tokens: int = 0) -> None:
        """Update metrics with a single request observation.

        Args:
            latency_ms: Request latency in milliseconds.
            is_error: Whether the request resulted in an error.
            tokens: Token count used by the request.
        """
        self.total_requests += 1
        if is_error:
            self.total_errors += 1
        self.total_tokens += tokens
        self.latencies_ms.append(latency_ms)

        # Keep only last 1000 latencies for percentile computation
        if len(self.latencies_ms) > 1000:
            self.latencies_ms = self.latencies_ms[-1000:]

        # Update computed metrics
        self.error_rate = self.total_errors / max(self.total_requests, 1)
        self._compute_percentiles()

    def _compute_percentiles(self) -> None:
        """Compute P50, P95, P99 from recorded latencies."""
        if not self.latencies_ms:
            return
        sorted_lats = sorted(self.latencies_ms)
        n = len(sorted_lats)
        self.p50_latency = sorted_lats[int(n * 0.50)]
        self.p95_latency = sorted_lats[int(n * 0.95)]
        self.p99_latency = sorted_lats[int(n * 0.99)]

    def record_satisfaction(self, score: float) -> None:
        """Record user satisfaction score (0.0 to 1.0).

        Args:
            score: User satisfaction score.
        """
        total = (self.satisfaction_count * self.user_satisfaction) + score
        self.satisfaction_count += 1
        self.user_satisfaction = total / max(self.satisfaction_count, 1)

    @property
    def snapshot(self) -> dict[str, Any]:
        """Return a snapshot dict of current metrics."""
        return {
            "version": self.version,
            "total_requests": self.total_requests,
            "total_errors": self.total_errors,
            "error_rate": round(self.error_rate, 4),
            "p50_latency_ms": round(self.p50_latency, 2),
            "p95_latency_ms": round(self.p95_latency, 2),
            "p99_latency_ms": round(self.p99_latency, 2),
            "total_tokens": self.total_tokens,
            "user_satisfaction": round(self.user_satisfaction, 4),
            "satisfaction_count": self.satisfaction_count,
        }


@dataclasses.dataclass
class ModelMetrics:
    """Aggregated metrics for an entire model (all versions).

    Attributes:
        model_name: Name of the model.
        versions: Dict of version -> VersionMetrics.
        baseline_version: The version designated as the baseline.
        canary_version: The canary version under evaluation.
    """
    model_name: str
    versions: dict[str, VersionMetrics] = dataclasses.field(default_factory=dict)
    baseline_version: str = ""
    canary_version: str = ""

    def get_or_create(self, version: str) -> VersionMetrics:
        """Get or create metrics for a specific version.

        Args:
            version: Version identifier.

        Returns:
            VersionMetrics instance.
        """
        if version not in self.versions:
            self.versions[version] = VersionMetrics(version=version)
        return self.versions[version]

    @property
    def baseline(self) -> VersionMetrics | None:
        """Get baseline version metrics."""
        if self.baseline_version and self.baseline_version in self.versions:
            return self.versions[self.baseline_version]
        return None

    @property
    def canary(self) -> VersionMetrics | None:
        """Get canary version metrics."""
        if self.canary_version and self.canary_version in self.versions:
            return self.versions[self.canary_version]
        return None

    @property
    def snapshot(self) -> dict[str, Any]:
        """Return a snapshot dict of all metrics."""
        return {
            "model_name": self.model_name,
            "baseline_version": self.baseline_version,
            "canary_version": self.canary_version,
            "versions": {
                v: metrics.snapshot
                for v, metrics in self.versions.items()
            },
        }


# ======================================================================
# Canary Deploy Manager
# ======================================================================


class CanaryDeployManager:
    """Canary model deployment manager — safe rollout of AI models.

    Provides traffic splitting with consistent hashing, metrics collection,
    auto-promotion, and automatic rollback when error rate or latency
    exceeds thresholds.

    Usage:
        manager = CanaryDeployManager(model_registry)
        manager.register_model("my-model", "v2.0", canary_gateway)
        manager.set_traffic_split("my-model", "v1.0", "v2.0", new_percent=10)

        # Route a request (consistent hash by user_id)
        response = await manager.route_request(
            "my-model",
            {"user_id": "user_123", "request": ai_request},
        )

        # Check metrics and auto-promote if healthy
        manager.collect_metrics("my-model")
        decision = manager.auto_promote("my-model", threshold=0.95)

        # Rollback if something goes wrong
        manager.rollback("my-model")
    """

    # Auto-rollback thresholds (class-level constants)
    MAX_ERROR_RATE: float = 0.05       # >5% error rate triggers auto-rollback
    MAX_LATENCY_MULTIPLIER: float = 2.0  # >2x baseline latency triggers auto-rollback
    PROGRESSIVE_STEPS: list[int] = [5, 10, 25, 50, 100]  # Gradual rollout percentages

    def __init__(self, registry: ModelRegistry | None = None) -> None:
        """Initialise the canary deploy manager.

        Args:
            registry: Optional ModelRegistry instance for provider chain integration.
        """
        self._registry = registry
        # model_name -> {version: VersionEntry}
        self._versions: dict[str, dict[str, VersionEntry]] = {}
        # model_name -> TrafficSplit
        self._traffic_splits: dict[str, TrafficSplit] = {}
        # model_name -> model_name ordered list (for version ordering)
        self._version_order: dict[str, list[str]] = {}
        # model_name -> ModelMetrics
        self._metrics: dict[str, ModelMetrics] = {}
        # Deployment history log
        self._deploy_log: list[dict[str, Any]] = []

    # ── Model Version Management ──────────────────────────────────────

    def register_model(
        self,
        name: str,
        version: str,
        gateway: AIGatewayProtocol,
        status: str = "staging",
    ) -> VersionEntry:
        """Register a new model version for deployment.

        Args:
            name: Model name (e.g. "business-card-lora").
            version: Version string (e.g. "v1.0", "v2.0-beta").
            gateway: AIGatewayProtocol instance serving this version.
            status: Initial status (default: "staging").

        Returns:
            The registered VersionEntry.
        """
        if name not in self._versions:
            self._versions[name] = {}
            self._version_order[name] = []

        if version in self._versions[name]:
            logger.warning(
                "Model '%s' version '%s' already registered, replacing",
                name, version,
            )

        entry = VersionEntry(
            version=version,
            gateway=gateway,
            status=status,
        )
        self._versions[name][version] = entry

        # Maintain insertion order
        if version not in self._version_order[name]:
            self._version_order[name].append(version)

        # Ensure metrics tracking exists
        if name not in self._metrics:
            self._metrics[name] = ModelMetrics(model_name=name)

        logger.info(
            "CanaryDeploy: registered model '%s' version '%s' (status=%s)",
            name, version, status,
        )
        self._log_deploy_event(name, version, "register", {"status": status})
        return entry

    def get_version(self, name: str, version: str) -> VersionEntry | None:
        """Get a registered version entry.

        Args:
            name: Model name.
            version: Version string.

        Returns:
            VersionEntry if found, None otherwise.
        """
        return self._versions.get(name, {}).get(version)

    def list_versions(self, name: str) -> list[dict[str, Any]]:
        """List all registered versions for a model.

        Args:
            name: Model name.

        Returns:
            List of version info dicts.
        """
        versions = self._versions.get(name, {})
        return [
            {
                "version": v.version,
                "status": v.status,
                "traffic_weight": v.traffic_weight,
                "deployed_at": v.deployed_at,
            }
            for v in versions.values()
        ]

    # ── Traffic Splitting ─────────────────────────────────────────────

    def set_traffic_split(
        self,
        model_name: str,
        version_old: str,
        version_new: str,
        new_percent: int = 5,
    ) -> TrafficSplit:
        """Set traffic split between old and new model versions.

        Args:
            model_name: Name of the model.
            version_old: Baseline version identifier.
            version_new: Canary version identifier.
            new_percent: Percentage of traffic for the new version (0-100).

        Returns:
            The TrafficSplit configuration.

        Raises:
            ValueError: If new_percent is not in 0-100, or versions aren't registered.
        """
        if not 0 <= new_percent <= 100:
            raise ValueError(f"new_percent must be 0-100, got {new_percent}")

        if model_name not in self._versions:
            raise ValueError(f"Model '{model_name}' has no registered versions")

        if version_old not in self._versions[model_name]:
            raise ValueError(
                f"Version '{version_old}' not registered for model '{model_name}'"
            )
        if version_new not in self._versions[model_name]:
            raise ValueError(
                f"Version '{version_new}' not registered for model '{model_name}'"
            )

        split = TrafficSplit(
            model_name=model_name,
            old_version=version_old,
            new_version=version_new,
            new_percent=new_percent,
            baseline_percent=100 - new_percent,
        )
        self._traffic_splits[model_name] = split

        # Update version traffic weights
        self._versions[model_name][version_old].traffic_weight = split.baseline_percent / 100.0
        self._versions[model_name][version_new].traffic_weight = split.new_percent / 100.0

        # Update statuses
        self._versions[model_name][version_old].status = "active"
        self._versions[model_name][version_new].status = "canary"

        # Set metrics tracking
        if model_name in self._metrics:
            self._metrics[model_name].baseline_version = version_old
            self._metrics[model_name].canary_version = version_new

        logger.info(
            "CanaryDeploy: traffic split for '%s': %s=%d%%, %s=%d%%",
            model_name, version_old, split.baseline_percent,
            version_new, split.new_percent,
        )
        self._log_deploy_event(
            model_name, version_new, "traffic_split",
            {"old_version": version_old, "new_percent": new_percent},
        )
        return split

    def get_traffic_split(self, model_name: str) -> TrafficSplit | None:
        """Get current traffic split for a model.

        Args:
            model_name: Model name.

        Returns:
            TrafficSplit if configured, None otherwise.
        """
        return self._traffic_splits.get(model_name)

    # ── Consistent Hash Routing ───────────────────────────────────────

    def route_request(
        self,
        model_name: str,
        context: dict[str, Any],
    ) -> tuple[str, VersionEntry | None]:
        """Route a request to the appropriate model version using consistent hashing.

        Uses a consistent hash of the user_id (or a random fallback) to ensure
        the same user always gets the same model version, providing a consistent
        experience during canary rollouts.

        Args:
            model_name: Name of the model to route for.
            context: Request context dict. Must contain at least one of:
                - "user_id": User identifier for consistent hashing.
                - "session_id": Session identifier (fallback).
                If neither is provided, a random routing decision is made.

        Returns:
            Tuple of (version_string, VersionEntry_or_None).
            Returns ("", None) if no versions are registered.
        """
        versions = self._versions.get(model_name)
        if not versions:
            logger.warning("CanaryDeploy: no versions for model '%s'", model_name)
            return ("", None)

        # Check if there's a traffic split active
        split = self._traffic_splits.get(model_name)
        if split is None:
            # No split — use the latest registered version
            ordered = self._version_order.get(model_name, [])
            if not ordered:
                return ("", None)
            latest = ordered[-1]
            entry = versions.get(latest)
            if entry and entry.status not in ("rolled_back",):
                return (latest, entry)
            # If latest is rolled back, fall back
            for ver in reversed(ordered):
                e = versions.get(ver)
                if e and e.status not in ("rolled_back",):
                    return (ver, e)
            return ("", None)

        # Traffic split is active — use consistent hashing
        hash_key = (
            context.get("user_id")
            or context.get("session_id")
            or str(uuid.uuid4())
        )
        hash_val = self._consistent_hash(hash_key)
        # hash_val is in [0.0, 1.0)

        # Route to new version if hash falls in the new_percent range
        if hash_val * 100 < split.new_percent:
            entry = versions.get(split.new_version)
            if entry and entry.status not in ("rolled_back",):
                return (split.new_version, entry)

        # Route to baseline version
        entry = versions.get(split.old_version)
        if entry:
            return (split.old_version, entry)

        # Fallback: any active version
        for ver in self._version_order.get(model_name, []):
            e = versions.get(ver)
            if e and e.status not in ("rolled_back",):
                return (ver, e)

        return ("", None)

    @staticmethod
    def _consistent_hash(key: str) -> float:
        """Compute a consistent hash value in [0.0, 1.0) from a string key.

        Uses SHA-256 to produce a stable, uniformly distributed hash
        that ensures the same key always maps to the same value.

        Args:
            key: String key to hash.

        Returns:
            Float in [0.0, 1.0).
        """
        hash_bytes = hashlib.sha256(key.encode("utf-8")).digest()
        # Use first 8 bytes as a 64-bit integer
        hash_int = int.from_bytes(hash_bytes[:8], byteorder="big")
        return hash_int / (2**64)

    # ── Metrics Collection ────────────────────────────────────────────

    def record_request(
        self,
        model_name: str,
        version: str,
        latency_ms: float,
        is_error: bool = False,
        tokens: int = 0,
    ) -> None:
        """Record a single request observation for metrics.

        Args:
            model_name: Model name.
            version: Version identifier.
            latency_ms: Request latency in milliseconds.
            is_error: Whether the request resulted in an error.
            tokens: Token count used by the request.
        """
        if model_name not in self._metrics:
            self._metrics[model_name] = ModelMetrics(model_name=model_name)

        metrics = self._metrics[model_name].get_or_create(version)
        metrics.update(latency_ms, is_error, tokens)

    def record_satisfaction(
        self,
        model_name: str,
        version: str,
        score: float,
    ) -> None:
        """Record user satisfaction score for a model version.

        Args:
            model_name: Model name.
            version: Version identifier.
            score: Satisfaction score (0.0 to 1.0).
        """
        if model_name not in self._metrics:
            self._metrics[model_name] = ModelMetrics(model_name=model_name)
        metrics = self._metrics[model_name].get_or_create(version)
        metrics.record_satisfaction(score)

    def collect_metrics(self, model_name: str) -> dict[str, Any] | None:
        """Collect and return current metrics for a model.

        Args:
            model_name: Model name.

        Returns:
            Metrics snapshot dict, or None if model not tracked.
        """
        metrics = self._metrics.get(model_name)
        if metrics is None:
            return None
        snapshot = metrics.snapshot
        # Add auto-rollback assessment
        snapshot["auto_rollback_risk"] = self._assess_rollback_risk(model_name)
        return snapshot

    def _assess_rollback_risk(self, model_name: str) -> dict[str, Any]:
        """Assess whether the canary version should be auto-rolled back.

        Compares canary metrics against baseline thresholds:
        - Error rate > MAX_ERROR_RATE (5%)
        - P95 latency > MAX_LATENCY_MULTIPLIER * baseline P95 (2x)

        Args:
            model_name: Model name.

        Returns:
            Dict with keys: should_rollback, reasons, canary_error_rate,
            canary_p95, baseline_p95, latency_ratio.
        """
        risk: dict[str, Any] = {
            "should_rollback": False,
            "reasons": [],
            "canary_error_rate": 0.0,
            "canary_p95": 0.0,
            "baseline_p95": 0.0,
            "latency_ratio": 1.0,
        }

        metrics = self._metrics.get(model_name)
        if not metrics or not metrics.canary or not metrics.baseline:
            risk["reasons"].append("insufficient_data")
            return risk

        canary = metrics.canary
        baseline = metrics.baseline

        canary_metrics = canary.snapshot
        baseline_metrics = baseline.snapshot

        risk["canary_error_rate"] = canary_metrics["error_rate"]
        risk["canary_p95"] = canary_metrics["p95_latency_ms"]
        risk["baseline_p95"] = baseline_metrics["p95_latency_ms"]

        # Check error rate threshold
        if canary.error_rate > self.MAX_ERROR_RATE:
            risk["should_rollback"] = True
            risk["reasons"].append(
                f"error_rate={canary.error_rate:.4f} > threshold={self.MAX_ERROR_RATE}"
            )

        # Check latency threshold (only if baseline has data)
        if baseline.p95_latency > 0 and canary.p95_latency > 0:
            ratio = canary.p95_latency / baseline.p95_latency
            risk["latency_ratio"] = round(ratio, 2)
            if ratio > self.MAX_LATENCY_MULTIPLIER:
                risk["should_rollback"] = True
                risk["reasons"].append(
                    f"latency_ratio={ratio:.2f}x > threshold={self.MAX_LATENCY_MULTIPLIER}x"
                )

        return risk

    # ── Auto-Promotion ────────────────────────────────────────────────

    def auto_promote(
        self,
        model_name: str,
        threshold: float = 0.95,
        min_requests: int = 100,
    ) -> dict[str, Any]:
        """Auto-promote the canary version if metrics meet the threshold.

        Conditions for promotion:
        1. Canary version is deployed and has metrics
        2. Canary has at least `min_requests` observations
        3. No auto-rollback conditions are triggered
        4. User satisfaction (if available) >= threshold

        On promotion, sets traffic to 100% new version and marks
        the old version as "active" fallback.

        Args:
            model_name: Model name.
            threshold: Required user satisfaction or metric score (0-1).
            min_requests: Minimum number of requests before auto-promotion.

        Returns:
            Decision dict with keys: promoted, reason, old_version,
            new_version, metrics.
        """
        result: dict[str, Any] = {
            "model_name": model_name,
            "promoted": False,
            "reason": "",
            "old_version": "",
            "new_version": "",
            "metrics": None,
        }

        metrics = self._metrics.get(model_name)
        if not metrics:
            result["reason"] = "no_metrics_tracked"
            return result

        split = self._traffic_splits.get(model_name)
        if not split:
            result["reason"] = "no_traffic_split"
            return result

        canary_metrics = metrics.canary
        if not canary_metrics:
            result["reason"] = "no_canary_metrics"
            return result

        # Check minimum request count
        if canary_metrics.total_requests < min_requests:
            result["reason"] = (
                f"insufficient_requests: {canary_metrics.total_requests} < {min_requests}"
            )
            return result

        # Check auto-rollback risk
        risk = self._assess_rollback_risk(model_name)
        if risk["should_rollback"]:
            # Auto-rollback instead of promote
            self._auto_rollback(model_name, risk)
            result["reason"] = f"auto_rolled_back: {', '.join(risk['reasons'])}"
            result["old_version"] = split.old_version
            result["new_version"] = split.new_version
            result["metrics"] = metrics.snapshot
            return result

        # Check satisfaction threshold (if available)
        if canary_metrics.satisfaction_count > 0:
            if canary_metrics.user_satisfaction < threshold:
                result["reason"] = (
                    f"satisfaction={canary_metrics.user_satisfaction:.4f} < "
                    f"threshold={threshold}"
                )
                result["metrics"] = metrics.snapshot
                return result

        # All conditions met — promote!
        self._promote_canary(model_name, split)
        result["promoted"] = True
        result["reason"] = (
            f"canary healthy after {canary_metrics.total_requests} requests: "
            f"error_rate={canary_metrics.error_rate:.4f}, "
            f"p95_latency={canary_metrics.p95_latency:.2f}ms"
        )
        result["old_version"] = split.old_version
        result["new_version"] = split.new_version
        result["metrics"] = metrics.snapshot

        # Also register in ModelRegistry if available
        if self._registry and split.new_version:
            try:
                self._registry.register_provider(
                    name=f"{model_name}@{split.new_version}",
                    gateway=self._versions.get(model_name, {}).get(
                        split.new_version
                    ).gateway,
                    priority=0,
                )
                logger.info(
                    "CanaryDeploy: registered promoted version in ModelRegistry: %s@%s",
                    model_name, split.new_version,
                )
            except Exception as exc:
                logger.warning(
                    "CanaryDeploy: failed to register promoted version in ModelRegistry: %s",
                    exc,
                )

        self._log_deploy_event(
            model_name, split.new_version, "auto_promote",
            {
                "old_version": split.old_version,
                "total_requests": canary_metrics.total_requests,
                "error_rate": canary_metrics.error_rate,
            },
        )
        return result

    def _promote_canary(
        self,
        model_name: str,
        split: TrafficSplit,
    ) -> None:
        """Internal: promote canary to 100% traffic.

        Args:
            model_name: Model name.
            split: The traffic split configuration.
        """
        versions = self._versions.get(model_name, {})

        # Set canary to 100%
        if split.new_version in versions:
            versions[split.new_version].traffic_weight = 1.0
            versions[split.new_version].status = "promoted"

        # Mark old version as fallback
        if split.old_version in versions:
            versions[split.old_version].traffic_weight = 0.0
            versions[split.old_version].status = "active"  # fallback

        # Remove traffic split (routing goes to new version)
        if model_name in self._traffic_splits:
            del self._traffic_splits[model_name]

        logger.info(
            "CanaryDeploy: PROMOTED '%s' version '%s' to 100%% traffic",
            model_name, split.new_version,
        )

    # ── Rollback ──────────────────────────────────────────────────────

    def rollback(self, model_name: str) -> dict[str, Any]:
        """One-click rollback to the previous stable version.

        Args:
            model_name: Model name.

        Returns:
            Decision dict with keys: rolled_back, reason, rolled_from, rolled_to.
        """
        result: dict[str, Any] = {
            "model_name": model_name,
            "rolled_back": False,
            "reason": "",
            "rolled_from": "",
            "rolled_to": "",
        }

        split = self._traffic_splits.get(model_name)
        if not split:
            # Check if there's a promoted version to rollback from
            versions = self._versions.get(model_name, {})
            promoted = [
                v for v in versions.values()
                if v.status == "promoted"
            ]
            if promoted:
                # Find the last version before promoted
                ordered = self._version_order.get(model_name, [])
                promoted_idx = -1
                for i, v in enumerate(ordered):
                    entry = versions.get(v)
                    if entry and entry.status == "promoted":
                        promoted_idx = i
                        break
                if promoted_idx > 0:
                    rollback_to = ordered[promoted_idx - 1]
                    rollback_entry = versions.get(rollback_to)
                    if rollback_entry:
                        # Rollback the promoted version
                        promoted_ver = ordered[promoted_idx]
                        versions[promoted_ver].traffic_weight = 0.0
                        versions[promoted_ver].status = "rolled_back"
                        rollback_entry.traffic_weight = 1.0
                        rollback_entry.status = "active"

                        result["rolled_back"] = True
                        result["reason"] = "manual_rollback_from_promoted"
                        result["rolled_from"] = promoted_ver
                        result["rolled_to"] = rollback_to

                        self._log_deploy_event(
                            model_name, promoted_ver, "rollback",
                            {"rolled_to": rollback_to, "type": "manual"},
                        )
                        return result

            result["reason"] = "no_active_deployment_to_rollback"
            return result

        # Rollback to old version from canary
        versions = self._versions.get(model_name, {})
        old_entry = versions.get(split.old_version)
        new_entry = versions.get(split.new_version)

        if not old_entry:
            result["reason"] = f"baseline version '{split.old_version}' not found"
            return result

        # Set old version to 100%
        old_entry.traffic_weight = 1.0
        old_entry.status = "active"

        # Mark canary as rolled back
        if new_entry:
            new_entry.traffic_weight = 0.0
            new_entry.status = "rolled_back"

        # Remove traffic split
        if model_name in self._traffic_splits:
            del self._traffic_splits[model_name]

        result["rolled_back"] = True
        result["reason"] = "manual_rollback_from_canary"
        result["rolled_from"] = split.new_version
        result["rolled_to"] = split.old_version

        logger.warning(
            "CanaryDeploy: ROLLED BACK '%s' from '%s' to '%s'",
            model_name, split.new_version, split.old_version,
        )
        self._log_deploy_event(
            model_name, split.new_version, "rollback",
            {"rolled_to": split.old_version, "type": "manual"},
        )
        return result

    def _auto_rollback(
        self,
        model_name: str,
        risk: dict[str, Any],
    ) -> dict[str, Any]:
        """Internal: automatic rollback when metrics exceed thresholds.

        Args:
            model_name: Model name.
            risk: The rollback risk assessment dict.

        Returns:
            The rollback result dict.
        """
        result = self.rollback(model_name)
        result["reason"] = f"auto_rollback: {', '.join(risk.get('reasons', []))}"
        result["rolled_back"] = True

        logger.warning(
            "CanaryDeploy: AUTO-ROLLBACK '%s': %s",
            model_name, ", ".join(risk.get("reasons", [])),
        )

        self._log_deploy_event(
            model_name, result.get("rolled_from", ""), "auto_rollback",
            {
                "rolled_to": result.get("rolled_to", ""),
                "reasons": risk.get("reasons", []),
            },
        )
        return result

    # ── Status & Reporting ────────────────────────────────────────────

    def get_status(self) -> dict[str, Any]:
        """Get status for all models under canary management.

        Returns:
            Dict with model names as keys, status info as values.
        """
        status: dict[str, Any] = {}
        for model_name in self._versions:
            versions = self._versions[model_name]
            split = self._traffic_splits.get(model_name)
            metrics = self._metrics.get(model_name)
            risk = self._assess_rollback_risk(model_name) if metrics else {}

            status[model_name] = {
                "versions": [
                    {
                        "version": v.version,
                        "status": v.status,
                        "traffic_weight": v.traffic_weight,
                        "deployed_at": v.deployed_at,
                    }
                    for v in versions.values()
                ],
                "traffic_split": {
                    "active": split is not None,
                    "old_version": split.old_version if split else "",
                    "new_version": split.new_version if split else "",
                    "new_percent": split.new_percent if split else 0,
                    "baseline_percent": split.baseline_percent if split else 100,
                } if split else {"active": False},
                "metrics": metrics.snapshot if metrics else {},
                "auto_rollback_risk": risk,
            }
        return status

    def get_model_status(self, model_name: str) -> dict[str, Any] | None:
        """Get detailed status for a single model.

        Args:
            model_name: Model name.

        Returns:
            Status dict, or None if model not found.
        """
        if model_name not in self._versions:
            return None
        return self.get_status().get(model_name)

    def get_deploy_log(self, model_name: str | None = None) -> list[dict[str, Any]]:
        """Get deployment history log.

        Args:
            model_name: Optional filter by model name.

        Returns:
            List of deployment event dicts.
        """
        if model_name:
            return [e for e in self._deploy_log if e.get("model_name") == model_name]
        return list(self._deploy_log)

    def _log_deploy_event(
        self,
        model_name: str,
        version: str,
        event_type: str,
        details: dict[str, Any] | None = None,
    ) -> None:
        """Record a deployment event in the log.

        Args:
            model_name: Model name.
            version: Version string.
            event_type: Type of event (register, traffic_split, promote, rollback).
            details: Optional additional details.
        """
        self._deploy_log.append({
            "model_name": model_name,
            "version": version,
            "event_type": event_type,
            "details": details or {},
            "timestamp": time.time(),
        })

    # ── Progressive Rollout Steps ─────────────────────────────────────

    def next_step(self, model_name: str) -> int | None:
        """Get the next progressive rollout percentage for a model.

        Steps: 5% → 10% → 25% → 50% → 100%

        Args:
            model_name: Model name.

        Returns:
            Next percentage value, or None if already at 100% or no split.
        """
        split = self._traffic_splits.get(model_name)
        if not split:
            return None

        current = split.new_percent
        for step in self.PROGRESSIVE_STEPS:
            if step > current:
                return step
        return None  # Already at 100%

    def advance_step(self, model_name: str) -> TrafficSplit | None:
        """Advance the canary rollout to the next progressive step.

        Args:
            model_name: Model name.

        Returns:
            Updated TrafficSplit, or None if unable to advance.

        Raises:
            ValueError: If auto-rollback conditions are triggered.
        """
        next_pct = self.next_step(model_name)
        if next_pct is None:
            logger.info("CanaryDeploy: '%s' already at 100%%", model_name)
            return None

        # Check auto-rollback before advancing
        risk = self._assess_rollback_risk(model_name)
        if risk.get("should_rollback"):
            self._auto_rollback(model_name, risk)
            raise ValueError(
                f"Cannot advance '{model_name}': auto-rollback triggered. "
                f"Reasons: {', '.join(risk.get('reasons', []))}"
            )

        split = self._traffic_splits.get(model_name)
        if not split:
            return None

        split.new_percent = next_pct
        split.baseline_percent = 100 - next_pct

        # Update version weights
        versions = self._versions.get(model_name, {})
        if split.old_version in versions:
            versions[split.old_version].traffic_weight = split.baseline_percent / 100.0
        if split.new_version in versions:
            versions[split.new_version].traffic_weight = split.new_percent / 100.0

        logger.info(
            "CanaryDeploy: advanced '%s' to %d%% (baseline=%d%%)",
            model_name, next_pct, split.baseline_percent,
        )
        self._log_deploy_event(
            model_name, split.new_version, "advance_step",
            {"new_percent": next_pct, "old_percent": split.baseline_percent},
        )
        return split


# ======================================================================
# Module-level singleton support
# ======================================================================

_canary_manager: CanaryDeployManager | None = None


def get_canary_manager() -> CanaryDeployManager:
    """Get or create the global CanaryDeployManager singleton.

    Returns:
        The shared CanaryDeployManager instance.
    """
    global _canary_manager
    if _canary_manager is None:
        _canary_manager = CanaryDeployManager()
        logger.info("CanaryDeployManager singleton created")
    return _canary_manager


def reset_canary_manager() -> None:
    """Reset the singleton (useful for testing)."""
    global _canary_manager
    _canary_manager = None
    logger.debug("CanaryDeployManager singleton reset")
