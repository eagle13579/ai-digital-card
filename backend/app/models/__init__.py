from app.models.user import User
from app.models.brochure import Brochure, Page
from app.models.tag import UserTag, MatchRecord
from app.models.visitor import VisitorLog
from app.models.trust import TrustNetwork
from app.models.payment import PaymentOrder, EnterpriseSubscription, TrialRecord
from app.models.webhook import WebhookSubscription
from app.models.integration import Integration
from app.models.ab_test import ABTest, ABTestVariant, ABTestEvent
from app.models.audit import AuditLog
from app.models.api_key import ApiKey, ApiKeyUsage
from app.models.message import Message
from app.models.invoice import Invoice
from app.models.platform import Platform, PlatformMember
from app.models.connection import Connection
from app.models.gaia import (
    GaiaKnowledge,
    GaiaEvolutionEvent,
    GaiaTrainingRun,
    GaiaModelWeights,
    KnowledgeModel,
)
# Lazy import to avoid circular chain:
# models.__init__ → crm.crm_models → crm.__init__ → crm_router → routers.auth → services → ai → vector_search → models.tag (loop!)
# Import directly from the module when needed: from app.crm.crm_models import CrmContact

# ── 链客宝合并模型 (27个新文件) ─────────────────
# 注意: CrmContact 等 CRM 类由 app.crm.crm_models 已有实现提供，此处不重复导入
from app.models.activity import Activity, Contact
from app.models.api_usage_log import ApiUsageLog
from app.models.business_card import BusinessCard
from app.models.business_need import BusinessNeed
from app.models.circuit_breaker import CircuitBreakerState
from app.models.contract import Contract, PaymentTransaction
from app.models.deal import BusinessDeal, DealActivity
from app.models.enterprise import Enterprise, EnterpriseRelation
from app.models.escrow import Deal as EscrowDeal, Milestone, Dispute
from app.models.import_history import ImportHistory
from app.models.match_credit_log import MatchCreditLog
from app.models.membership_order import MembershipOrder
from app.models.metrics_snapshot import MetricsSnapshot
from app.models.online_matching_feedback import OnlineMatchingFeedback, OnlineMatchingEvent, OnlineMatchingRegistration
from app.models.order import Order
from app.models.organization import Organization, OrganizationMember, Invite
from app.models.private_board_order import PrivateBoardOrder
from app.models.product import Product
from app.models.rate_limit import RateLimitRecord
from app.models.review import Review
from app.models.revoked_token import RevokedToken
from app.models.six_degrees import UserRelation, RelationEvent, SixDegreePathCache, ReferralLink
from app.models.subscription import Subscription
from app.models.token_budget import (
    DegradeStrategy,
    TokenBudgetRule,
    TokenBudgetEvent,
    TokenBudgetStatus,
)
from app.models.user_event import UserEvent
from app.models.wallet import Wallet, WalletTransaction
from app.models.withdrawal import Withdrawal
# ── F11 分制-压缩流水线 ──
from app.models.compression import (
    CompressionMode,
    CompressionConfig,
    CompressionResult,
    CompressionStats,
)
# ── F12 Prompt分治模板库 ──
from app.models.prompt import PromptCategory, PromptTemplate
# ── F14 工具规则装饰器 ──
from app.models.tool_rules import (
    BoundaryAction,
    BoundaryHandler,
    ConditionOperator,
    ConditionSeverity,
    CostDeclaration,
    CostUnit,
    PostCondition,
    PreCondition,
    ToolRuleDef,
    ToolRuleStats,
    ValidationResult,
)
# ── F17 灰度发布平台 (彩虹部署) ──
from app.models.canary import (
    CanaryDeployment,
    CanaryEvent,
    CanaryGroup,
    CanaryRule,
    CanaryStatus,
    CanaryStrategy,
    TrafficAllocationMode,
)
# ── F21 Agent化任务决策矩阵 ──
from app.models.decision_matrix import (
    DecisionQuadrant,
    ComplexityFactors,
    RepetitionFactors,
    TaskEvaluationResult,
    EvaluationRequest,
    BatchEvaluationRequest,
    BatchEvaluationResult,
    MatrixStats,
    AgentReadinessCategory,
)
# ── F19 Token 消耗分析仪表盘 ──
from app.models.token_analytics import (
    TokenConsumptionRecord,
    TokenBudgetAlert,
    TokenSummaryStats,
    AgentTokenSummary,
)
# ── F18 Agent质量评估看板 ──
from app.models.quality import (
    QualityDimension,
    QualitySample,
    QualityBaseline,
    QualityEvalJob,
    EvalMethod,
    EvalStatus,
)

# ── F16 异步任务 Checkpoint 恢复 ──
from app.models.checkpoint import (
    CheckpointStatus,
    StepRecord,
    StepStatus,
    TaskCheckpoint,
)

# ── F20 名片Agent准确率门禁 ──
from app.models.accuracy_gate import (
    AccuracyBaseline,
    AccuracyCheckRecord,
    AccuracyCalibrationRecord,
    AccuracyGateConfig,
    GateDecision,
    CalibrationType,
    CalibrationStatus,
    GateCheckSource,
)

__all__ = [
    "User", "Brochure", "Page", "UserTag", "MatchRecord",
    "VisitorLog", "TrustNetwork", "PaymentOrder", "EnterpriseSubscription", "Integration",
    "WebhookSubscription",
    "ABTest", "ABTestVariant", "ABTestEvent",
    "AuditLog",
    "ApiKey", "ApiKeyUsage",
    "Message",
    "Invoice",
    "GaiaKnowledge", "GaiaEvolutionEvent", "GaiaTrainingRun", "GaiaModelWeights",
    "KnowledgeModel",
    "Platform", "PlatformMember",
    "Connection",
    # CRM
    "CrmContact", "CrmDeal", "CrmPipelineStage", "CrmActivity", "CrmNote",
    # 链客宝合并模型
    "Activity", "Contact",
    "ApiUsageLog",
    "BusinessCard",
    "BusinessNeed",
    "CircuitBreakerState",
    "Contract", "PaymentTransaction",
    "BusinessDeal", "DealActivity",
    "Enterprise", "EnterpriseRelation",
    "EscrowDeal", "Milestone", "Dispute",
    "ImportHistory",
    "MatchCreditLog",
    "MembershipOrder",
    "MetricsSnapshot",
    "OnlineMatchingFeedback", "OnlineMatchingEvent", "OnlineMatchingRegistration",
    "Order",
    "Organization", "OrganizationMember", "Invite",
    "PrivateBoardOrder",
    "Product",
    "RateLimitRecord",
    "Review",
    "RevokedToken",
    "UserRelation", "RelationEvent", "SixDegreePathCache", "ReferralLink",
    "Subscription",
    "DegradeStrategy", "TokenBudgetRule", "TokenBudgetEvent", "TokenBudgetStatus",
    "UserEvent",
    "Wallet", "WalletTransaction",
    "Withdrawal",
    # F11 压缩流水线
    "CompressionMode",
    "CompressionConfig",
    "CompressionResult",
    "CompressionStats",
    # F12 Prompt分治模板库
    "PromptCategory",
    "PromptTemplate",
    # F14 工具规则装饰器
    "BoundaryAction",
    "BoundaryHandler",
    "ConditionOperator",
    "ConditionSeverity",
    "CostDeclaration",
    "CostUnit",
    "PostCondition",
    "PreCondition",
    "ToolRuleDef",
    "ToolRuleStats",
    "ValidationResult",
    # F21 Agent化任务决策矩阵
    "DecisionQuadrant",
    "ComplexityFactors",
    "RepetitionFactors",
    "TaskEvaluationResult",
    "EvaluationRequest",
    "BatchEvaluationRequest",
    "BatchEvaluationResult",
    "MatrixStats",
    "AgentReadinessCategory",
    # F17 灰度发布平台 (彩虹部署)
    "CanaryDeployment",
    "CanaryEvent",
    "CanaryGroup",
    "CanaryRule",
    "CanaryStatus",
    "CanaryStrategy",
    "TrafficAllocationMode",
    # F19 Token 消耗分析仪表盘
    "TokenConsumptionRecord",
    "TokenBudgetAlert",
    "TokenSummaryStats",
    "AgentTokenSummary",
    # F16 异步任务 Checkpoint 恢复
    "CheckpointStatus",
    "StepRecord",
    "StepStatus",
    "TaskCheckpoint",
    # F18 Agent质量评估看板
    "QualityDimension",
    "QualitySample",
    "QualityBaseline",
    "QualityEvalJob",
    "EvalMethod",
    "EvalStatus",
    # F20 名片Agent准确率门禁
    "AccuracyBaseline",
    "AccuracyCheckRecord",
    "AccuracyCalibrationRecord",
    "AccuracyGateConfig",
    "GateDecision",
    "CalibrationType",
    "CalibrationStatus",
    "GateCheckSource",
]
