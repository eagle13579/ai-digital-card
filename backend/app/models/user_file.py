"""资料文件上传记录 — 用于免费配额检查（每用户 N 个免费文件）。

upload-file 接口每次成功保存文件后写入一条记录；
配额检查按 user_id 统计记录条数，实现"每用户 N 个免费文件"限制。
"""

from datetime import datetime

from sqlalchemy import DateTime, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class UserFileRecord(Base):
    """用户上传的资料文件记录（配额统计用）"""

    __tablename__ = "user_file_records"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        Integer, nullable=False, index=True, comment="上传用户ID"
    )
    original_name: Mapped[str] = mapped_column(
        String(255), default="", comment="原始文件名"
    )
    saved_path: Mapped[str] = mapped_column(
        String(512), default="", comment="存储相对路径"
    )
    size: Mapped[int] = mapped_column(Integer, default=0, comment="文件大小（字节）")
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), comment="上传时间"
    )
