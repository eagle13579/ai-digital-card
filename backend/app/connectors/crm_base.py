"""CRM 连接器抽象基类。

所有外部 CRM 集成（Salesforce / HubSpot / 飞书多维表格等）
需继承 CrmBase 并实现其抽象方法。
"""

from __future__ import annotations

import abc
import dataclasses
import logging
from typing import Optional

logger = logging.getLogger(__name__)


# ── 数据模型 ──────────────────────────────────────────────


@dataclasses.dataclass
class ContactData:
    """统一联系人数据模型（CRM 无关）。"""

    external_id: str               # CRM 侧记录 ID
    name: str                      # 姓名
    email: str                     # 邮箱
    phone: str = ""                # 手机号
    company: str = ""              # 公司
    title: str = ""                # 职位
    department: str = ""           # 部门
    tags: list[str] = dataclasses.field(default_factory=list)

    # 扩展字段（各 CRM 特有字段序列化为 JSON）
    raw: dict | None = None

    def to_dict(self) -> dict:
        return dataclasses.asdict(self)

    @classmethod
    def from_dict(cls, d: dict) -> "ContactData":
        return cls(**{k: v for k, v in d.items() if k in cls.__dataclass_fields__})


@dataclasses.dataclass
class SyncResult:
    """一次同步操作的结果。"""

    success: bool
    created: int = 0
    updated: int = 0
    deleted: int = 0
    errors: list[str] = dataclasses.field(default_factory=list)
    details: str = ""


# ── 基类 ─────────────────────────────────────────────────


class CrmBase(abc.ABC):
    """CRM 连接器抽象基类。

    用法:
        class MyCrm(CrmBase):
            def authenticate(self) -> bool:
                ...
            def get_contact(self, external_id: str) -> Optional[ContactData]:
                ...
            ...

    子类需在实例化前设置好凭证（通过 env / config / 构造参数）。
    """

    def __init__(self, config: dict | None = None):
        self.config = config or {}
        self._authenticated = False

    # ── 认证 ──────────────────────────────────────────

    @abc.abstractmethod
    def authenticate(self) -> bool:
        """向 CRM 认证，返回是否成功。"""
        ...

    @property
    def is_authenticated(self) -> bool:
        return self._authenticated

    # ── 联系人 CRUD ───────────────────────────────────

    @abc.abstractmethod
    def get_contact(self, external_id: str) -> Optional[ContactData]:
        """根据 CRM 侧 ID 获取联系人，不存在返回 None。"""
        ...

    @abc.abstractmethod
    def search_contacts(self, query: str, limit: int = 20) -> list[ContactData]:
        """搜索联系人（按姓名/邮箱/公司模糊匹配）。"""
        ...

    @abc.abstractmethod
    def create_contact(self, contact: ContactData) -> SyncResult:
        """创建联系人，返回包含 CRM 侧 ID 的 SyncResult。"""
        ...

    @abc.abstractmethod
    def update_contact(self, contact: ContactData) -> SyncResult:
        """更新联系人（通过 contact.external_id 定位）。"""
        ...

    @abc.abstractmethod
    def delete_contact(self, external_id: str) -> SyncResult:
        """删除联系人。"""
        ...

    # ── 批量 / 同步 ────────────────────────────────────

    @abc.abstractmethod
    def sync_contacts(
        self,
        contacts: list[ContactData],
        strategy: str = "upsert",
    ) -> SyncResult:
        """批量同步联系人。

        Args:
            contacts: 联系人列表
            strategy: 'upsert' | 'replace' | 'append'
               upsert  — 有则更新无则创建
               replace — 用本批数据完全替换 CRM 联系人
               append  — 只创建新记录，不更新已有的
        """
        ...

    # ── 健康检查 ──────────────────────────────────────

    @abc.abstractmethod
    def health_check(self) -> dict:
        """返回 CRM 连接状态，例如 {"status": "ok", "latency_ms": 120}。"""
        ...

    # ── 辅助 ──────────────────────────────────────────

    def _log_sync(self, label: str, result: SyncResult) -> None:
        logger.info(
            "[CRM:%s] %s — 创建=%d 更新=%d 删除=%d 错误=%d | %s",
            self.__class__.__name__,
            label,
            result.created,
            result.updated,
            result.deleted,
            len(result.errors),
            result.details,
        )
