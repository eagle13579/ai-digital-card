"""同步状态持久化模型 — 记录 CRM 同步运行历史与冲突记录。

使用 SQLAlchemy ORM，与现有 database.py 中的 Base 和 SessionLocal 兼容。
支持两种同步状态表:
  - SyncState:  每次同步运行的状态（成功/失败/冲突数等）
  - SyncConflict: 双向同步中检测到的数据冲突
"""

from datetime import datetime

from sqlalchemy import Integer, String, Text, DateTime, Boolean, func
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class SyncState(Base):
    """CRM 同步运行状态记录表。

    每次同步周期（无论手动触发还是调度触发）写入一条记录。
    """

    __tablename__ = "crm_sync_states"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    # 提供商标识，如 "hubspot" / "salesforce" / "all"
    provider: Mapped[str] = mapped_column(
        String(32), nullable=False, index=True, comment="CRM 提供商标识"
    )
    # 同步状态: running / success / failed / partial
    status: Mapped[str] = mapped_column(
        String(16), nullable=False, default="running", comment="同步状态"
    )
    # 同步开始时间
    started_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), comment="同步开始时间"
    )
    # 同步结束时间（nullable 表示尚未完成）
    finished_at: Mapped[datetime | None] = mapped_column(
        DateTime, nullable=True, comment="同步完成时间"
    )
    # 统计: 创建数
    contacts_created: Mapped[int] = mapped_column(
        Integer, default=0, comment="新建联系人数量"
    )
    # 统计: 更新数
    contacts_updated: Mapped[int] = mapped_column(
        Integer, default=0, comment="更新联系人数量"
    )
    # 统计: 删除数
    contacts_deleted: Mapped[int] = mapped_column(
        Integer, default=0, comment="删除联系人数量"
    )
    # 统计: 冲突数
    contacts_conflicted: Mapped[int] = mapped_column(
        Integer, default=0, comment="冲突联系人数量"
    )
    # 错误信息（多个错误用 ; 分隔）
    error_message: Mapped[str] = mapped_column(
        Text, default="", comment="错误信息摘要"
    )
    # 详细描述（JSON 格式，可存储完整日志）
    details: Mapped[str] = mapped_column(
        Text, default="", comment="同步详情（JSON）"
    )
    # 触发方式: manual / schedule
    trigger: Mapped[str] = mapped_column(
        String(16), default="manual", comment="触发方式"
    )

    def mark_finished(
        self,
        status: str = "success",
        created: int = 0,
        updated: int = 0,
        deleted: int = 0,
        conflicted: int = 0,
        error: str = "",
        details: str = "",
    ) -> None:
        """标记同步运行为已完成状态。"""
        self.status = status
        self.finished_at = datetime.utcnow()
        self.contacts_created = created
        self.contacts_updated = updated
        self.contacts_deleted = deleted
        self.contacts_conflicted = conflicted
        self.error_message = error
        self.details = details

    def __repr__(self) -> str:
        return (
            f"<SyncState id={self.id} provider={self.provider} "
            f"status={self.status} trigger={self.trigger}>"
        )


class SyncConflict(Base):
    """CRM 双向同步数据冲突记录表。

    当本地和 CRM 侧的同一条联系人都在最近同步周期中被修改时，
    记录冲突详情供人工或自动裁决。
    """

    __tablename__ = "crm_sync_conflicts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    # 关联的同步运行 ID
    sync_state_id: Mapped[int] = mapped_column(
        Integer, nullable=False, index=True, comment="关联 SyncState ID"
    )
    # 提供商标识
    provider: Mapped[str] = mapped_column(
        String(32), nullable=False, index=True, comment="CRM 提供商"
    )
    # 本地联系人 ID（系统中该联系人的主键）
    local_contact_id: Mapped[str] = mapped_column(
        String(64), nullable=False, comment="本地联系人 ID"
    )
    # CRM 侧联系人 ID
    crm_contact_id: Mapped[str] = mapped_column(
        String(64), nullable=False, comment="CRM 侧联系人 ID"
    )
    # 冲突时的本地数据快照（JSON 格式 ContactData 字典）
    local_data: Mapped[str] = mapped_column(
        Text, default="{}", comment="本地数据快照（JSON）"
    )
    # 冲突时的 CRM 侧数据快照（JSON 格式 ContactData 字典）
    crm_data: Mapped[str] = mapped_column(
        Text, default="{}", comment="CRM 侧数据快照（JSON）"
    )
    # 冲突的字段列表（逗号分隔）
    conflicted_fields: Mapped[str] = mapped_column(
        String(256), default="", comment="冲突字段列表"
    )
    # 检测时间
    detected_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), comment="冲突检测时间"
    )
    # 是否已解决
    resolved: Mapped[bool] = mapped_column(
        Boolean, default=False, comment="是否已解决"
    )
    # 解决方法: local_wins / crm_wins / manual_merge / ignored
    resolution: Mapped[str] = mapped_column(
        String(32), default="", comment="解决方法"
    )
    # 解决时间
    resolved_at: Mapped[datetime | None] = mapped_column(
        DateTime, nullable=True, comment="解决时间"
    )

    def resolve(self, method: str = "local_wins") -> None:
        """标记冲突为已解决。"""
        self.resolved = True
        self.resolution = method
        self.resolved_at = datetime.utcnow()

    def __repr__(self) -> str:
        return (
            f"<SyncConflict id={self.id} provider={self.provider} "
            f"local={self.local_contact_id} crm={self.crm_contact_id} "
            f"resolved={self.resolved}>"
        )
