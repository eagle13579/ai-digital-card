"""CRM 抽象层 — 定义统一的 CRM 集成接口、桥接注册中心与同步调度函数。

提供三种使用模式:
  1. CRMBridge (async class-based) — 配合 Provider 类实例注册使用
  2. dispatch (sync function) — 根据 integration 类型直接路由到对应的 sync 函数
  3. SyncScheduler / ConflictDetector — 双向同步调度与冲突检测能力
"""
import asyncio
import json
import logging
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from threading import Thread
from typing import Any, Callable

from app.database import SessionLocal

logger = logging.getLogger(__name__)


# ══════════════════════════════════════════════════════════════════════════
# 抽象基类（供 async class 模式使用）
# ══════════════════════════════════════════════════════════════════════════


class CRMProvider(ABC):
    """CRM 提供商抽象基类。所有具体集成（HubSpot / Salesforce）需实现此接口。"""

    @abstractmethod
    async def export_contact(self, contact_data: dict[str, Any]) -> dict[str, Any]:
        """导出联系人到 CRM。返回 CRM 侧联系人 ID / URL 等信息。"""
        ...

    @abstractmethod
    async def update_contact(
        self, contact_id: str, contact_data: dict[str, Any]
    ) -> dict[str, Any]:
        """更新 CRM 中已有联系人。"""
        ...

    @abstractmethod
    async def delete_contact(self, contact_id: str) -> bool:
        """从 CRM 删除联系人。"""
        ...

    @abstractmethod
    async def get_contact(self, contact_id: str) -> dict[str, Any] | None:
        """查询 CRM 联系人详情。"""
        ...

    @abstractmethod
    async def test_connection(self) -> bool:
        """测试与 CRM 的连接是否有效（校验 Token / API Key）。"""
        ...

    @abstractmethod
    async def get_provider_name(self) -> str:
        """返回提供商名称标识（如 'hubspot' / 'salesforce'）。"""
        ...


class CRMBridge:
    """CRM 桥接注册中心 — 管理所有已注册的 CRM Provider。"""

    def __init__(self) -> None:
        self._providers: dict[str, CRMProvider] = {}
        # 注入同步调度器（按需初始化）
        self._sync_scheduler: "SyncScheduler | None" = None

    def register(self, provider: CRMProvider) -> None:
        """注册一个 CRM Provider 实例。"""
        name = provider.get_provider_name()
        self._providers[name] = provider

    def get(self, name: str) -> CRMProvider | None:
        """按名称获取已注册的 CRM Provider。"""
        return self._providers.get(name)

    def list_providers(self) -> list[str]:
        """列出所有已注册的提供商名称。"""
        return list(self._providers.keys())

    async def export_to_all(
        self, contact_data: dict[str, Any]
    ) -> dict[str, dict[str, Any]]:
        """将联系人批量导出到所有已注册且可用的 CRM。返回 {provider_name: result}。"""
        results: dict[str, dict[str, Any]] = {}
        for name, provider in self._providers.items():
            try:
                result = await provider.export_contact(contact_data)
                results[name] = {"success": True, "data": result}
            except Exception as e:
                results[name] = {"success": False, "error": str(e)}
        return results

    async def health_check_all(self) -> dict[str, bool]:
        """检测所有注册 CRM 的连接状态。"""
        status: dict[str, bool] = {}
        for name, provider in self._providers.items():
            try:
                status[name] = await provider.test_connection()
            except Exception:
                status[name] = False
        return status

    # ── 同步调度接口 ──────────────────────────────────────────────────────

    @property
    def sync_scheduler(self) -> "SyncScheduler":
        """获取或创建 SyncScheduler 实例（懒初始化）。"""
        if self._sync_scheduler is None:
            self._sync_scheduler = SyncScheduler(bridge=self)
        return self._sync_scheduler

    def init_sync_scheduler(
        self,
        cron_expression: str = "0 */6 * * *",
        conflict_resolver: (
            Callable[[dict[str, Any], dict[str, Any]], dict[str, Any]] | None
        ) = None,
    ) -> "SyncScheduler":
        """初始化并返回同步调度器。

        Args:
            cron_expression: 标准 cron 表达式, 默认每6小时同步一次
            conflict_resolver: 可选冲突自动裁决函数
                              接收 (local_data, crm_data) 返回合并后的数据
        """
        scheduler = SyncScheduler(
            bridge=self, cron_expression=cron_expression, conflict_resolver=conflict_resolver
        )
        self._sync_scheduler = scheduler
        return scheduler


# ── 全局单例（供 async class 模式使用） ──────────────────────────────────
crm_bridge = CRMBridge()


# ══════════════════════════════════════════════════════════════════════════
# 冲突检测 — 比较本地与 CRM 侧联系人的字段级差异
# ══════════════════════════════════════════════════════════════════════════


class ConflictField(str, Enum):
    """标识哪个数据源在冲突字段上拥有更新的版本。"""

    LOCAL = "local"
    CRM = "crm"
    BOTH = "both"


@dataclass
class FieldDiff:
    """单个字段的差异描述。"""

    field_name: str
    local_value: Any = None
    crm_value: Any = None
    newer_side: ConflictField = ConflictField.BOTH

    def to_dict(self) -> dict[str, Any]:
        return {
            "field": self.field_name,
            "local_value": self.local_value,
            "crm_value": self.crm_value,
            "newer_side": self.newer_side.value,
        }


@dataclass
class ConflictResult:
    """一次冲突检测的结果。"""

    is_conflict: bool = False
    """是否为真正的冲突（两边都被修改）。"""
    local_contact_id: str = ""
    """本地系统联系人标识。"""
    crm_contact_id: str = ""
    """CRM 侧联系人标识。"""
    local_updated_at: float = 0.0
    """本地最后修改时间戳。"""
    crm_updated_at: float = 0.0
    """CRM 侧最后修改时间戳。"""
    field_diffs: list[FieldDiff] = field(default_factory=list)
    """差异字段列表。"""
    local_data: dict[str, Any] = field(default_factory=dict)
    """冲突时的本地数据快照。"""
    crm_data: dict[str, Any] = field(default_factory=dict)
    """冲突时的 CRM 数据快照。"""

    @property
    def conflicted_fields(self) -> list[str]:
        return [d.field_name for d in self.field_diffs]

    def to_dict(self) -> dict[str, Any]:
        return {
            "is_conflict": self.is_conflict,
            "local_contact_id": self.local_contact_id,
            "crm_contact_id": self.crm_contact_id,
            "local_updated_at": self.local_updated_at,
            "crm_updated_at": self.crm_updated_at,
            "field_diffs": [d.to_dict() for d in self.field_diffs],
            "conflicted_fields": self.conflicted_fields,
        }


# 比较时忽略的元字段（不参与冲突判断）
_SKIP_FIELDS = frozenset({"external_id", "raw", "updated_at", "created_at"})


class ConflictDetector:
    """双向同步冲突检测器。

    比较同一联系人在本地和 CRM 侧的数据，判断是否存在双向修改。
    只有当两边自上次同步后都有修改时才视为冲突。
    """

    # 参与比较的 ContactData 字段（排除元字段）
    COMPARISON_FIELDS = (
        "name",
        "email",
        "phone",
        "company",
        "title",
        "department",
        "tags",
    )

    def __init__(
        self,
        tolerance_seconds: float = 1.0,
    ):
        """初始化冲突检测器。

        Args:
            tolerance_seconds: 时间戳比较容差（秒），防止时钟偏差导致误判。
        """
        self.tolerance = tolerance_seconds

    def compare(
        self,
        local_data: dict[str, Any],
        crm_data: dict[str, Any],
        local_updated_at: float = 0.0,
        crm_updated_at: float = 0.0,
        local_contact_id: str = "",
        crm_contact_id: str = "",
    ) -> ConflictResult:
        """比较本地与 CRM 联系人数据，检测冲突。

        Args:
            local_data: 本地联系人数据字典
            crm_data: CRM 侧联系人数据字典
            local_updated_at: 本地最后修改时间戳（秒）
            crm_updated_at: CRM 侧最后修改时间戳（秒）
            local_contact_id: 本地联系人标识
            crm_contact_id: CRM 侧联系人标识

        Returns:
            ConflictResult 对象，is_conflict=True 表示需要人工/自动裁决
        """
        result = ConflictResult(
            local_contact_id=local_contact_id or local_data.get("external_id", ""),
            crm_contact_id=crm_contact_id or crm_data.get("external_id", ""),
            local_data=local_data,
            crm_data=crm_data,
            local_updated_at=local_updated_at,
            crm_updated_at=crm_updated_at,
        )

        # 逐字段比较
        has_diffs = False
        for field in self.COMPARISON_FIELDS:
            lv = local_data.get(field)
            cv = crm_data.get(field)

            # 序列化为可比较形式（处理 list 等不可哈希类型）
            lv_str = json.dumps(lv, sort_keys=True, ensure_ascii=False) if not isinstance(lv, (str, type(None))) else lv
            cv_str = json.dumps(cv, sort_keys=True, ensure_ascii=False) if not isinstance(cv, (str, type(None))) else cv

            if lv_str != cv_str:
                has_diffs = True
                # 尝试判断哪一边更新
                newer = self._determine_newer_side(
                    field, lv, cv, local_updated_at, crm_updated_at
                )
                result.field_diffs.append(
                    FieldDiff(
                        field_name=field,
                        local_value=lv,
                        crm_value=cv,
                        newer_side=newer,
                    )
                )

        # 冲突判定: 必须有差异且两边都有修改时间戳
        if has_diffs and local_updated_at > 0 and crm_updated_at > 0:
            # 两边都在上次同步之后被修改过 => 冲突
            lv_changed = local_updated_at > 0
            cv_changed = crm_updated_at > 0
            if lv_changed and cv_changed:
                result.is_conflict = True
            elif lv_changed:
                # 仅本地修改 — 应以本地为准（非冲突，只是本地领先）
                result.is_conflict = False
            else:
                # 仅 CRM 修改 — 应以 CRM 为准（非冲突）
                result.is_conflict = False
        elif has_diffs:
            # 只有一方有数据，或者缺少时间戳 — 保守视为非冲突
            result.is_conflict = False

        return result

    def _determine_newer_side(
        self,
        field: str,
        local_val: Any,
        crm_val: Any,
        local_updated_at: float,
        crm_updated_at: float,
    ) -> ConflictField:
        """根据修改时间戳判断哪一边对该字段的修改更新。"""
        if local_updated_at <= 0 and crm_updated_at <= 0:
            return ConflictField.BOTH
        if local_updated_at <= 0:
            return ConflictField.CRM
        if crm_updated_at <= 0:
            return ConflictField.LOCAL

        diff = local_updated_at - crm_updated_at
        if abs(diff) <= self.tolerance:
            return ConflictField.BOTH
        return ConflictField.LOCAL if diff > 0 else ConflictField.CRM


# ══════════════════════════════════════════════════════════════════════════
# 同步调度器 — cron 式定期同步 + 单次手动同步
# ══════════════════════════════════════════════════════════════════════════


def _cron_field_match(value: int, pattern: str) -> bool:
    """匹配 cron 表达式中的单个字段值。

    支持: * (任意), 具体数字, 1-5 (范围), */5 (步长), 1,3,5 (列表)
    """
    pattern = pattern.strip()

    # * 匹配任意值
    if pattern == "*":
        return True

    # 逗号分隔列表
    if "," in pattern:
        return any(_cron_field_match(value, p) for p in pattern.split(","))

    # 步长: */5 或 1-30/5
    if "/" in pattern:
        base, step = pattern.split("/", 1)
        step = int(step)
        if base == "*":
            return value % step == 0
        if "-" in base:
            start_s, end_s = base.split("-", 1)
            start, end = int(start_s), int(end_s)
            return start <= value <= end and (value - start) % step == 0
        return value % step == 0

    # 范围: 1-5
    if "-" in pattern:
        start, end = pattern.split("-", 1)
        return int(start) <= value <= int(end)

    # 具体数字
    return int(pattern) == value


def cron_match(cron_expression: str, timestamp: float | None = None) -> bool:
    """检查给定时间戳是否匹配 cron 表达式。

    Args:
        cron_expression: 标准 cron 表达式 "分 时 日 月 周"
                         (minute hour day-of-month month day-of-week)
        timestamp: UNIX 时间戳（秒），默认当前时间

    Returns:
        是否匹配
    """
    parts = cron_expression.strip().split()
    if len(parts) != 5:
        raise ValueError(
            f"cron 表达式必须包含 5 个字段 (minute hour day month weekday), 当前: {cron_expression!r}"
        )

    now = time.localtime(timestamp or time.time())
    minute, hour, day, month, weekday = now.tm_min, now.tm_hour, now.tm_mday, now.tm_mon, now.tm_wday

    fields = [
        (minute, parts[0]),
        (hour, parts[1]),
        (day, parts[2]),
        (month, parts[3]),
        (weekday, parts[4]),
    ]

    return all(_cron_field_match(v, p) for v, p in fields)


# 默认冲突自动裁决策略: 本地数据优先
def _default_conflict_resolver(
    local_data: dict[str, Any], crm_data: dict[str, Any]
) -> dict[str, Any]:
    """默认冲突解决策略 — 本地优先，用 CRM 数据补充本地缺失字段。"""
    merged = dict(local_data)
    for key in ("name", "email", "phone", "company", "title", "department"):
        if not merged.get(key) and crm_data.get(key):
            merged[key] = crm_data[key]
    # 合并 tags（去重）
    local_tags = set(local_data.get("tags", []) or [])
    crm_tags = set(crm_data.get("tags", []) or [])
    merged["tags"] = sorted(local_tags | crm_tags)
    return merged


class SyncScheduler:
    """CRM 双向同步调度器。

    提供:
      - cron 表达式定期同步
      - 手动触发单次同步
      - 冲突检测与记录
      - 持久化同步状态到 SQLite (SyncState / SyncConflict)
      - 可选自动冲突裁决回调

    用法:
        scheduler = SyncScheduler(bridge=crm_bridge, cron_expression="0 */2 * * *")
        scheduler.start()   # 后台线程启动
        ...
        scheduler.stop()
    """

    def __init__(
        self,
        bridge: CRMBridge,
        cron_expression: str = "0 */6 * * *",
        conflict_detector: ConflictDetector | None = None,
        conflict_resolver: Callable | None = None,
        sync_fn: Callable | None = None,
    ):
        """初始化同步调度器。

        Args:
            bridge: CRMBridge 实例（提供已注册的 provider）
            cron_expression: cron 表达式，默认每6小时整点同步
            conflict_detector: 冲突检测器实例，如为 None 则自动创建
            conflict_resolver: 冲突自动裁决函数，接收 (local_data, crm_data) 返回合并后数据
                               None 表示仅记录冲突但不自动裁决
            sync_fn: 可选的同步执行函数。默认使用 bridge.export_to_all
                     自定义签名: async sync_fn(bridge, provider_name) -> SyncResult-like dict
        """
        self.bridge = bridge
        self.cron_expression = cron_expression
        self.conflict_detector = conflict_detector or ConflictDetector()
        self.conflict_resolver = conflict_resolver  # None = 仅记录不自动解决
        self.sync_fn = sync_fn

        # 调度状态
        self._running = False
        self._thread: Thread | None = None
        self._last_check_time: float = 0.0
        self._stop_event = asyncio.Event()

        # 最近一次同步结果缓存
        self.last_sync_result: dict[str, Any] = {}

    # ── 生命周期 ──────────────────────────────────────────────────────────

    def start(self) -> None:
        """在后台线程启动调度器。

        调度器每隔60秒检查一次当前时间是否匹配 cron 表达式。
        """
        if self._running:
            logger.warning("SyncScheduler is already running")
            return

        self._running = True
        self._thread = Thread(target=self._scheduler_loop, daemon=True, name="crm-sync-scheduler")
        self._thread.start()
        logger.info(
            "SyncScheduler started with cron expression: %s (check interval: 60s)",
            self.cron_expression,
        )

    def stop(self) -> None:
        """停止后台调度线程。"""
        self._running = False
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=5)
            logger.info("SyncScheduler stopped")
        self._thread = None

    @property
    def is_running(self) -> bool:
        return self._running and (self._thread is not None and self._thread.is_alive())

    # ── 调度主循环 ────────────────────────────────────────────────────────

    def _scheduler_loop(self) -> None:
        """后台调度线程主循环。

        每60秒检查一次 cron 匹配。匹配时触发同步。
        使用 asyncio.run() 在后台线程中执行异步同步函数。
        """
        while self._running:
            try:
                now = time.time()
                # Cron 匹配检查（每分钟检查一次）
                if self._should_sync(now):
                    logger.info(
                        "Cron trigger matched at %s, starting sync...",
                        datetime.fromtimestamp(now).isoformat(),
                    )
                    try:
                        asyncio.run(self._run_sync_cycle(trigger="schedule"))
                    except Exception as e:
                        logger.error("Sync cycle failed: %s", str(e), exc_info=True)

                    # 防止同一分钟重复触发
                    time.sleep(61)
                else:
                    time.sleep(60)
            except Exception as e:
                logger.error("Scheduler loop error: %s", str(e), exc_info=True)
                time.sleep(60)

    def _should_sync(self, now: float) -> bool:
        """判断当前时间点是否应触发同步。"""
        # 避免同一分钟重复触发
        if now - self._last_check_time < 60:
            return False
        if cron_match(self.cron_expression, now):
            self._last_check_time = now
            return True
        return False

    # ── 手动触发同步 ──────────────────────────────────────────────────────

    async def sync_now(self, provider_name: str | None = None) -> dict[str, Any]:
        """手动触发立即同步。

        Args:
            provider_name: 指定要同步的提供商，None 表示同步所有已注册提供商

        Returns:
            同步结果字典: {
                "success": bool,
                "provider": str,
                "created": int,
                "updated": int,
                "deleted": int,
                "conflicts": int,
                "sync_state_id": int,
                "error": str (optional),
                ...
            }
        """
        return await self._run_sync_cycle(trigger="manual", provider_filter=provider_name)

    # ── 核心同步周期 ──────────────────────────────────────────────────────

    async def _run_sync_cycle(
        self, trigger: str = "manual", provider_filter: str | None = None
    ) -> dict[str, Any]:
        """执行一次完整的同步周期。

        步骤:
          1. 遍历已注册的 provider
          2. 对每个 provider 执行同步
          3. 检测冲突（如果 provider 支持 get_contact）
          4. 持久化 SyncState + SyncConflict
          5. 返回汇总结果

        Args:
            trigger: 触发方式, "schedule" 或 "manual"
            provider_filter: 仅同步指定 provider
        """
        all_results: dict[str, Any] = {"success": True, "providers": {}}
        providers = self.bridge.list_providers()

        if provider_filter:
            if provider_filter in providers:
                providers = [provider_filter]
            else:
                return {"success": False, "error": f"Provider {provider_filter!r} not registered"}

        for pname in providers:
            provider = self.bridge.get(pname)
            if provider is None:
                continue

            # 创建同步状态记录
            state_id = self._create_sync_state(pname, trigger)
            logger.info("Sync cycle started for provider: %s (trigger=%s)", pname, trigger)

            try:
                # ── 执行同步 ──────────────────────────────────────────
                if self.sync_fn:
                    # 自定义同步函数
                    result = await self.sync_fn(self.bridge, pname)
                else:
                    # 默认: 导出测试 — 实际需替换为真正的双向同步逻辑
                    test_ok = await provider.test_connection()
                    if not test_ok:
                        raise ConnectionError(f"Connection test failed for {pname}")
                    result = {"success": True, "created": 0, "updated": 0, "deleted": 0}

                # ── 冲突检测 ──────────────────────────────────────────
                conflicts = await self._detect_conflicts(provider, pname, state_id)

                # ── 持久化状态 ────────────────────────────────────────
                created = result.get("created", 0)
                updated = result.get("updated", 0)
                deleted = result.get("deleted", 0)
                self._finish_sync_state(
                    state_id,
                    status="success",
                    created=created,
                    updated=updated,
                    deleted=deleted,
                    conflicted=len(conflicts),
                    details=json.dumps(result, ensure_ascii=False),
                )

                provider_result = {
                    "success": True,
                    "created": created,
                    "updated": updated,
                    "deleted": deleted,
                    "conflicts": len(conflicts),
                    "conflict_ids": [c.get("id") for c in conflicts],
                    "sync_state_id": state_id,
                }
                logger.info(
                    "Sync completed for %s: created=%d updated=%d deleted=%d conflicts=%d",
                    pname, created, updated, deleted, len(conflicts),
                )

            except Exception as e:
                error_msg = str(e)
                logger.error("Sync failed for %s: %s", pname, error_msg, exc_info=True)
                self._finish_sync_state(
                    state_id, status="failed", error=error_msg
                )
                provider_result = {
                    "success": False,
                    "error": error_msg,
                    "sync_state_id": state_id,
                }

            all_results["providers"][pname] = provider_result
            if not provider_result.get("success", False):
                all_results["success"] = False

        self.last_sync_result = all_results
        return all_results

    # ── 冲突检测与持久化 ──────────────────────────────────────────────────

    async def _detect_conflicts(
        self, provider: CRMProvider, pname: str, state_id: int
    ) -> list[dict[str, Any]]:
        """通过对比联系人数据检测双向冲突。

        遍历本地联系人列表并与 CRM 侧对比，发现两边都被修改的冲突。

        Args:
            provider: CRM provider 实例
            pname: 提供商名称
            state_id: 关联的 SyncState ID

        Returns:
            已持久化的冲突记录列表
        """
        saved_conflicts: list[dict[str, Any]] = []
        # 注意: 此处需要外部提供本地数据源
        # 子类或使用者应覆写 _get_local_contacts 方法
        local_contacts = await self._get_local_contacts(pname)

        for local_contact in local_contacts:
            ext_id = local_contact.get("external_id", "")
            if not ext_id:
                continue

            try:
                crm_raw = await provider.get_contact(ext_id)
            except Exception:
                logger.warning("Failed to fetch CRM contact %s from %s", ext_id, pname)
                continue

            if crm_raw is None:
                # CRM 侧不存在 — 不是冲突，只是本地新增
                continue

            # 提取冲突检测所需元数据
            local_updated = local_contact.get("updated_at", 0)
            crm_updated = crm_raw.get("updated_at", 0)

            # 转换为时间戳（支持多种格式）
            local_ts = self._to_timestamp(local_updated)
            crm_ts = self._to_timestamp(crm_updated)

            # 执行冲突检测
            conflict = self.conflict_detector.compare(
                local_data=local_contact,
                crm_data=crm_raw,
                local_updated_at=local_ts,
                crm_updated_at=crm_ts,
                local_contact_id=str(local_contact.get("id", ext_id)),
                crm_contact_id=ext_id,
            )

            if conflict.is_conflict:
                # 冲突记录
                conflict_record = self._save_conflict(
                    state_id=state_id,
                    provider=pname,
                    local_contact_id=conflict.local_contact_id,
                    crm_contact_id=conflict.crm_contact_id,
                    local_data=conflict.local_data,
                    crm_data=conflict.crm_data,
                    conflicted_fields=",".join(conflict.conflicted_fields),
                )

                # 自动裁决（如果配置了 resolver）
                if self.conflict_resolver is not None:
                    merged = self.conflict_resolver(local_contact, crm_raw)
                    logger.info(
                        "Auto-resolved conflict for %s (local=%s crm=%s) -> merged",
                        pname, conflict.local_contact_id, conflict.crm_contact_id,
                    )
                    # 注意: 自动裁决后需要更新本地/CRM数据
                    # 此处仅记录裁决结果，实际写入需外部实现
                    conflict_record["auto_resolved"] = True
                else:
                    logger.info(
                        "Conflict detected for %s local=%s crm=%s fields=%s",
                        pname, conflict.local_contact_id, conflict.crm_contact_id,
                        conflict.conflicted_fields,
                    )

                saved_conflicts.append(conflict_record)

        return saved_conflicts

    async def _get_local_contacts(self, pname: str) -> list[dict[str, Any]]:
        """获取本地联系人列表用于冲突检测。

        默认实现返回空列表，子类或调用者应覆写此方法以提供真实数据。
        可从 CrmContact 表或其他本地存储查询。

        Args:
            pname: 提供商名称

        Returns:
            ContactData 格式的字典列表
        """
        # TODO: 从本地数据库读取联系人列表
        # 例如: from app.crm.crm_models import CrmContact
        #       contacts = db.query(CrmContact).filter(...).all()
        logger.debug("_get_local_contacts not overridden — returning empty list for %s", pname)
        return []

    # ── SQLite 持久化 ─────────────────────────────────────────────────────

    def _create_sync_state(self, provider: str, trigger: str = "manual") -> int:
        """在 SQLite 中创建同步状态记录并返回 ID。"""
        from app.models.sync_state import SyncState

        db = SessionLocal()
        try:
            record = SyncState(
                provider=provider,
                status="running",
                trigger=trigger,
            )
            db.add(record)
            db.commit()
            db.refresh(record)
            return record.id
        except Exception as e:
            db.rollback()
            logger.error("Failed to create SyncState: %s", str(e))
            return -1
        finally:
            db.close()

    def _finish_sync_state(
        self,
        state_id: int,
        status: str = "success",
        created: int = 0,
        updated: int = 0,
        deleted: int = 0,
        conflicted: int = 0,
        error: str = "",
        details: str = "",
    ) -> None:
        """更新 SyncState 记录为完成状态。"""
        from app.models.sync_state import SyncState

        if state_id < 0:
            return

        db = SessionLocal()
        try:
            record = db.query(SyncState).filter(SyncState.id == state_id).first()
            if record:
                record.mark_finished(
                    status=status,
                    created=created,
                    updated=updated,
                    deleted=deleted,
                    conflicted=conflicted,
                    error=error,
                    details=details,
                )
                db.commit()
        except Exception as e:
            db.rollback()
            logger.error("Failed to update SyncState %d: %s", state_id, str(e))
        finally:
            db.close()

    def _save_conflict(
        self,
        state_id: int,
        provider: str,
        local_contact_id: str,
        crm_contact_id: str,
        local_data: dict[str, Any],
        crm_data: dict[str, Any],
        conflicted_fields: str = "",
    ) -> dict[str, Any]:
        """将冲突记录持久化到 SQLite，并返回记录字典。"""
        from app.models.sync_state import SyncConflict

        db = SessionLocal()
        try:
            record = SyncConflict(
                sync_state_id=state_id,
                provider=provider,
                local_contact_id=local_contact_id,
                crm_contact_id=crm_contact_id,
                local_data=json.dumps(local_data, ensure_ascii=False),
                crm_data=json.dumps(crm_data, ensure_ascii=False),
                conflicted_fields=conflicted_fields,
            )
            db.add(record)
            db.commit()
            db.refresh(record)

            return {
                "id": record.id,
                "provider": record.provider,
                "local_contact_id": record.local_contact_id,
                "crm_contact_id": record.crm_contact_id,
                "conflicted_fields": record.conflicted_fields,
                "detected_at": record.detected_at.isoformat() if record.detected_at else "",
            }
        except Exception as e:
            db.rollback()
            logger.error("Failed to save SyncConflict: %s", str(e))
            return {"id": -1, "error": str(e)}
        finally:
            db.close()

    # ── 查询接口 ──────────────────────────────────────────────────────────

    def get_sync_history(
        self,
        provider: str | None = None,
        limit: int = 20,
    ) -> list[dict[str, Any]]:
        """查询最近的同步历史记录。

        Args:
            provider: 提供商标识过滤，None 表示全部
            limit: 返回条数上限

        Returns:
            SyncState 字典列表
        """
        from app.models.sync_state import SyncState

        db = SessionLocal()
        try:
            query = db.query(SyncState)
            if provider:
                query = query.filter(SyncState.provider == provider)
            records = query.order_by(SyncState.id.desc()).limit(limit).all()

            return [
                {
                    "id": r.id,
                    "provider": r.provider,
                    "status": r.status,
                    "trigger": r.trigger,
                    "started_at": r.started_at.isoformat() if r.started_at else "",
                    "finished_at": r.finished_at.isoformat() if r.finished_at else "",
                    "created": r.contacts_created,
                    "updated": r.contacts_updated,
                    "deleted": r.contacts_deleted,
                    "conflicted": r.contacts_conflicted,
                    "error": r.error_message,
                }
                for r in records
            ]
        finally:
            db.close()

    def get_unresolved_conflicts(
        self, provider: str | None = None, limit: int = 50
    ) -> list[dict[str, Any]]:
        """查询未解决的冲突记录。

        Args:
            provider: 提供商标识过滤
            limit: 返回条数上限

        Returns:
            未解决的 SyncConflict 字典列表
        """
        from app.models.sync_state import SyncConflict

        db = SessionLocal()
        try:
            query = db.query(SyncConflict).filter(SyncConflict.resolved == False)  # noqa: E712
            if provider:
                query = query.filter(SyncConflict.provider == provider)
            records = query.order_by(SyncConflict.id.desc()).limit(limit).all()

            return [
                {
                    "id": r.id,
                    "sync_state_id": r.sync_state_id,
                    "provider": r.provider,
                    "local_contact_id": r.local_contact_id,
                    "crm_contact_id": r.crm_contact_id,
                    "conflicted_fields": r.conflicted_fields.split(",") if r.conflicted_fields else [],
                    "detected_at": r.detected_at.isoformat() if r.detected_at else "",
                    "local_data": json.loads(r.local_data or "{}"),
                    "crm_data": json.loads(r.crm_data or "{}"),
                }
                for r in records
            ]
        finally:
            db.close()

    def resolve_conflict(
        self,
        conflict_id: int,
        method: str = "local_wins",
    ) -> dict[str, Any]:
        """手动标记冲突为已解决。

        Args:
            conflict_id: SyncConflict 记录 ID
            method: 解决方法: local_wins / crm_wins / manual_merge / ignored

        Returns:
            操作结果字典
        """
        from app.models.sync_state import SyncConflict

        db = SessionLocal()
        try:
            record = db.query(SyncConflict).filter(SyncConflict.id == conflict_id).first()
            if not record:
                return {"success": False, "error": f"Conflict {conflict_id} not found"}

            record.resolve(method=method)
            db.commit()
            return {
                "success": True,
                "id": conflict_id,
                "method": method,
                "resolved_at": record.resolved_at.isoformat() if record.resolved_at else "",
            }
        except Exception as e:
            db.rollback()
            return {"success": False, "error": str(e)}
        finally:
            db.close()

    # ── 工具方法 ──────────────────────────────────────────────────────────

    @staticmethod
    def _to_timestamp(value: Any) -> float:
        """将多种时间格式统一转换为 UNIX 时间戳（秒）。"""
        if value is None:
            return 0.0
        if isinstance(value, (int, float)):
            # 假设是秒级时间戳；如果是毫秒级则转换
            if value > 1e12:  # 毫秒级
                return value / 1000.0
            return float(value)
        if isinstance(value, str):
            try:
                dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
                return dt.timestamp()
            except (ValueError, TypeError):
                return 0.0
        if hasattr(value, "timestamp"):
            return value.timestamp()
        return 0.0


# ══════════════════════════════════════════════════════════════════════════
# 同步调度函数 — 根据 integration 类型路由到具体 provider 的 sync 函数
# 适用于 FastAPI endpoint 中的简单同步调用
# ══════════════════════════════════════════════════════════════════════════


SUPPORTED_PROVIDERS = frozenset({"hubspot", "salesforce"})


def dispatch(
    integration_type: str,
    config: dict[str, Any],
    contact_data: dict[str, Any] | None = None,
    action: str = "test",
) -> dict[str, Any]:
    """根据集成类型调度到对应的 CRM sync 函数。

    Args:
        integration_type: 集成类型 — "hubspot" 或 "salesforce"
        config: CRM 配置字典
            - HubSpot: {"api_key": "..."} 或 {"access_token": "..."}
            - Salesforce: {"client_id": ..., "client_secret": ..., "username": ..., "password": ...}
                          或 {"access_token": ..., "instance_url": ...}
        contact_data: 联系人数据（仅 action="export" 时需要）
        action: 操作类型 — "test" 连接测试 | "export" 导出联系人

    Returns:
        test 返回: {"connected": True/False, "message": "..."}
        export 返回: {"success": True/False, "contact_id": "...", ...}

    Raises:
        ValueError: 不支持的集成类型或操作
    """
    if integration_type not in SUPPORTED_PROVIDERS:
        return {
            "success": False,
            "error": f"不支持的 CRM 集成类型: '{integration_type}'，支持的: {', '.join(sorted(SUPPORTED_PROVIDERS))}",
        }

    # 延迟导入，避免模块加载时产生循环依赖
    if integration_type == "hubspot":
        from app.services.crm_hubspot import test_connection as hs_test
        from app.services.crm_hubspot import export_contact as hs_export

        api_key = config.get("api_key") or config.get("access_token", "")
        if not api_key:
            return {"success": False, "error": "缺少 HubSpot API Key (api_key/access_token)"}

        if action == "test":
            return hs_test(api_key)
        elif action == "export":
            if contact_data is None:
                return {"success": False, "error": "export 操作需要 contact_data 参数"}
            return hs_export(api_key, contact_data)
        else:
            return {"success": False, "error": f"不支持的操作: '{action}'，仅支持 test/export"}

    elif integration_type == "salesforce":
        from app.services.crm_salesforce import test_connection as sf_test
        from app.services.crm_salesforce import export_contact as sf_export

        if action == "test":
            return sf_test(config)
        elif action == "export":
            if contact_data is None:
                return {"success": False, "error": "export 操作需要 contact_data 参数"}
            return sf_export(config, contact_data)
        else:
            return {"success": False, "error": f"不支持的操作: '{action}'，仅支持 test/export"}

    # 不会执行到这里（SUPPORTED_PROVIDERS 已检查）
    return {"success": False, "error": f"未知集成类型: {integration_type}"}
