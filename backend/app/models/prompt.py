"""F12 Prompt分治模板库 — 数据库模型。

职责单一模板类型:
  - input_parser:       输入解析
  - info_extractor:     信息提取
  - analysis_reasoning: 分析推理
  - formatter:          格式化
  - quality_control:    质量控制
"""

from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import String, Text, DateTime, JSON, Enum as SAEnum, Index
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base

import enum


class PromptCategory(str, enum.Enum):
    """F12 分治模板类别枚举"""

    INPUT_PARSER = "input_parser"          # 输入解析
    INFO_EXTRACTOR = "info_extractor"      # 信息提取
    ANALYSIS_REASONING = "analysis_reasoning"  # 分析推理
    FORMATTER = "formatter"                # 格式化
    QUALITY_CONTROL = "quality_control"    # 质量控制


class PromptTemplate(Base):
    """Prompt 模板 — 单一职责、版本化管理。"""

    __tablename__ = "prompt_templates"

    id: Mapped[str] = mapped_column(
        String(64), primary_key=True, comment="模板唯一标识（如 'input_parser/v1'）"
    )
    name: Mapped[str] = mapped_column(
        String(128), nullable=False, comment="模板名称"
    )
    category: Mapped[PromptCategory] = mapped_column(
        SAEnum(PromptCategory, name="prompt_category", create_constraint=True),
        nullable=False,
        comment="模板类别（F12 分治职责）",
    )
    version: Mapped[str] = mapped_column(
        String(32), nullable=False, default="v1", comment="语义版本号"
    )
    description: Mapped[str] = mapped_column(
        String(512), default="", comment="模板用途描述"
    )
    system_prompt: Mapped[str] = mapped_column(
        Text, nullable=False, comment="System prompt 模板内容（支持 {placeholder} 插值）"
    )
    user_prompt_template: Mapped[str] = mapped_column(
        Text, default="", comment="User prompt 模板内容（可选）"
    )
    parameters_schema: Mapped[Optional[dict]] = mapped_column(
        JSON, default=None, comment="期望入参的 JSON Schema（用于校验）"
    )
    output_schema: Mapped[Optional[dict]] = mapped_column(
        JSON, default=None, comment="期望输出的 JSON Schema（用于质量控制）"
    )
    tags: Mapped[Optional[list]] = mapped_column(
        JSON, default=list, comment="标签数组（如 ['f12', '分治', '提取']）"
    )
    is_active: Mapped[bool] = mapped_column(
        default=True, comment="是否启用"
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        comment="创建时间",
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        comment="更新时间",
    )

    __table_args__ = (
        Index("idx_prompt_category", "category"),
        Index("idx_prompt_active", "is_active"),
    )

    def to_dict(self) -> dict:
        """序列化为字典（用于 API 响应）。"""
        return {
            "id": self.id,
            "name": self.name,
            "category": self.category.value,
            "version": self.version,
            "description": self.description,
            "system_prompt": self.system_prompt,
            "user_prompt_template": self.user_prompt_template,
            "parameters_schema": self.parameters_schema,
            "output_schema": self.output_schema,
            "tags": self.tags or [],
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
