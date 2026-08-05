"""
token_analytics.py — F19 Token消耗分析数据模型

定义 TokenConsumptionRecord（Token 消费记录）、TokenBudgetAlert（预算预警记录）。
"""
from __future__ import annotations

import uuid
from datetime import datetime
from enum import Enum
from typing import Any

from sqlalchemy import Column, Integer, String, Float, DateTime, Text, Boolean, Enum as SAEnum
from app.database import Base


class AlertLevel(str, Enum):
    """预警级别"""
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"


# ── SQLAlchemy ORM 模型 ──────────────────────────


class TokenConsumptionRecord(Base):
    """Token 消费记录表——记录每次 Token 消耗的明细"""
    __tablename__ = "token_consumption_record"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    record_id = Column(String(64), unique=True, nullable=False, index=True,
                       comment="全局唯一记录标识")
    agent_name = Column(String(128), nullable=False, index=True,
                        comment="Agent 名称（如 openai_gpt4, deepseek_chat）")
    user_id = Column(Integer, nullable=True, index=True,
                     comment="用户 ID（空表示系统级消耗）")
    session_id = Column(String(64), nullable=True, index=True,
                        comment="会话 ID，用于关联同一次对话")
    rule_name = Column(String(128), nullable=True, index=True,
                       comment="关联的 TokenBudgetRule 名称")

    # Token 数量
    prompt_tokens = Column(Integer, default=0, comment="Prompt Token 数")
    completion_tokens = Column(Integer, default=0, comment="Completion Token 数")
    total_tokens = Column(Integer, default=0, comment="总 Token 数")

    # 预算控制信息
    is_truncated = Column(Boolean, default=False, comment="是否被截断")
    is_downgraded = Column(Boolean, default=False, comment="是否被降级")
    degrade_strategy = Column(String(32), nullable=True, comment="降级策略")

    # 成本
    estimated_cost = Column(Float, default=0.0, comment="估算成本（元）")
    cost_per_token = Column(Float, default=0.0, comment="每 Token 单价（元）")

    # 元数据
    model_name = Column(String(64), nullable=True, comment="模型名称")
    operation = Column(String(64), nullable=True, comment="操作类型（chat, embedding, summary 等）")
    status = Column(String(32), default="success", comment="状态: success / rejected / error")
    metadata_json = Column(Text, nullable=True, comment="附加元数据（JSON）")

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True,
                        comment="记录创建时间")

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "record_id": self.record_id,
            "agent_name": self.agent_name,
            "user_id": self.user_id,
            "session_id": self.session_id,
            "rule_name": self.rule_name,
            "prompt_tokens": self.prompt_tokens,
            "completion_tokens": self.completion_tokens,
            "total_tokens": self.total_tokens,
            "is_truncated": self.is_truncated,
            "is_downgraded": self.is_downgraded,
            "degrade_strategy": self.degrade_strategy,
            "estimated_cost": self.estimated_cost,
            "cost_per_token": self.cost_per_token,
            "model_name": self.model_name,
            "operation": self.operation,
            "status": self.status,
            "metadata_json": self.metadata_json,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class TokenBudgetAlert(Base):
    """Token 预算预警记录表——记录预算超限/接近阈值等预警事件"""
    __tablename__ = "token_budget_alert"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    alert_id = Column(String(64), unique=True, nullable=False, index=True,
                      comment="预警唯一标识")
    rule_name = Column(String(128), nullable=False, index=True,
                       comment="关联的预算规则名称")
    alert_level = Column(String(16), default="warning", nullable=False,
                         comment="预警级别: info / warning / critical")

    # 触发条件
    current_usage = Column(Integer, default=0, comment="当前用量")
    token_limit = Column(Integer, default=0, comment="预算上限")
    usage_ratio = Column(Float, default=0.0, comment="用量占比 (0.0~1.0)")
    threshold = Column(Float, default=0.8, comment="触发阈值")

    # 上下文
    agent_name = Column(String(128), nullable=True, comment="触发预警的 Agent 名称")
    user_id = Column(Integer, nullable=True, comment="触发预警的用户 ID")
    message = Column(Text, nullable=True, comment="预警描述消息")
    detail = Column(Text, nullable=True, comment="详细上下文（JSON）")

    is_resolved = Column(Boolean, default=False, comment="是否已解决")
    resolved_at = Column(DateTime, nullable=True, comment="解决时间")

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True,
                        comment="预警创建时间")

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "alert_id": self.alert_id,
            "rule_name": self.rule_name,
            "alert_level": self.alert_level,
            "current_usage": self.current_usage,
            "token_limit": self.token_limit,
            "usage_ratio": self.usage_ratio,
            "threshold": self.threshold,
            "agent_name": self.agent_name,
            "user_id": self.user_id,
            "message": self.message,
            "detail": self.detail,
            "is_resolved": self.is_resolved,
            "resolved_at": self.resolved_at.isoformat() if self.resolved_at else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


# ── 领域模型（非 ORM）───────────────────────────


class TokenSummaryStats:
    """Token 汇总统计——聚合查询的结果封装"""
    def __init__(
        self,
        total_tokens: int = 0,
        total_prompt_tokens: int = 0,
        total_completion_tokens: int = 0,
        total_cost: float = 0.0,
        total_requests: int = 0,
        truncated_count: int = 0,
        downgraded_count: int = 0,
        rejected_count: int = 0,
        unique_agents: int = 0,
        unique_users: int = 0,
        avg_tokens_per_request: float = 0.0,
        period_start: str | None = None,
        period_end: str | None = None,
    ):
        self.total_tokens = total_tokens
        self.total_prompt_tokens = total_prompt_tokens
        self.total_completion_tokens = total_completion_tokens
        self.total_cost = total_cost
        self.total_requests = total_requests
        self.truncated_count = truncated_count
        self.downgraded_count = downgraded_count
        self.rejected_count = rejected_count
        self.unique_agents = unique_agents
        self.unique_users = unique_users
        self.avg_tokens_per_request = avg_tokens_per_request
        self.period_start = period_start
        self.period_end = period_end

    def to_dict(self) -> dict[str, Any]:
        budget_status = {}  # 由调用方注入
        return {
            "total_tokens": self.total_tokens,
            "total_prompt_tokens": self.total_prompt_tokens,
            "total_completion_tokens": self.total_completion_tokens,
            "total_cost": round(self.total_cost, 4),
            "total_requests": self.total_requests,
            "truncated_count": self.truncated_count,
            "downgraded_count": self.downgraded_count,
            "rejected_count": self.rejected_count,
            "unique_agents": self.unique_agents,
            "unique_users": self.unique_users,
            "avg_tokens_per_request": round(self.avg_tokens_per_request, 2),
            "period_start": self.period_start,
            "period_end": self.period_end,
        }


class AgentTokenSummary:
    """按 Agent 维度的 Token 消耗汇总"""
    def __init__(
        self,
        agent_name: str,
        total_tokens: int = 0,
        total_cost: float = 0.0,
        total_requests: int = 0,
        truncated_count: int = 0,
        downgraded_count: int = 0,
        unique_users: int = 0,
        token_limit: int = 0,
        usage_ratio: float = 0.0,
    ):
        self.agent_name = agent_name
        self.total_tokens = total_tokens
        self.total_cost = total_cost
        self.total_requests = total_requests
        self.truncated_count = truncated_count
        self.downgraded_count = downgraded_count
        self.unique_users = unique_users
        self.token_limit = token_limit
        self.usage_ratio = usage_ratio

    def to_dict(self) -> dict[str, Any]:
        return {
            "agent_name": self.agent_name,
            "total_tokens": self.total_tokens,
            "total_cost": round(self.total_cost, 4),
            "total_requests": self.total_requests,
            "truncated_count": self.truncated_count,
            "downgraded_count": self.downgraded_count,
            "unique_users": self.unique_users,
            "token_limit": self.token_limit,
            "usage_ratio": round(self.usage_ratio, 4),
            "avg_tokens_per_request": round(self.total_tokens / max(self.total_requests, 1), 2),
        }
