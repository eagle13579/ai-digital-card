from app.models.user import User
from app.models.brochure import Brochure, Page
from app.models.tag import UserTag, MatchRecord
from app.models.visitor import VisitorLog
from app.models.trust import TrustNetwork
from app.models.payment import PaymentOrder, EnterpriseSubscription, TrialRecord  # noqa: F401
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
# from app.crm.crm_models import (
#     CrmContact,
#     CrmDeal,
#     CrmPipelineStage, 
#     CrmActivity,
#     CrmNote,
# )

# ── 链客宝合并模型 (27个新文件) ─────────────────
# 注意: CrmContact 等 CRM 类由 app.crm.crm_models 已有实现提供，此处不重复导入
from app.models.activity import Activity, Contact
from app.models.api_usage_log import ApiUsageLog
from app.models.business_card import BusinessCard
from app.models.business_need import BusinessNeed
from app.models.circuit_breaker import CircuitBreakerState
from app.models.contract import Contract, PaymentTransaction
from app.models.deal import Deal as BusinessDeal, DealActivity
from app.models.enterprise import Enterprise, EnterpriseRelation
from app.models.escrow import EscrowDeal, Milestone, Dispute
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
from app.models.user_event import UserEvent
from app.models.wallet import Wallet, WalletTransaction
from app.models.withdrawal import Withdrawal
from app.models.consent import UserConsent
from app.models.sdk import SdkApp

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
    "UserEvent",
    "Wallet", "WalletTransaction",
    "Withdrawal",
    "UserConsent",
    "SdkApp",
]
