from app.services.brochure import BrochureService
from app.services.tag_service import TagService
# These imports trigger a circular chain through:
# matching_engine → vector_search → models.tag → crm.crm_models → crm_router → routers.auth → services.chainke_bridge → services (loop!)
# They are imported lazily in the modules that actually need them.
# from app.services.matching_engine import MatchEngine
from app.services.trust_service import TrustService
from app.services.brochure_render import BrochureRenderer
from app.services.media_service import MediaService
from app.services.team_service import TeamService
from app.services.invoice_service import InvoiceService
from app.services.subscription_service import (
    PLANS,
    PlanConfig,
    TRIAL_DAYS,
    can_downgrade,
    can_upgrade,
    downgrade_subscription,
    get_current_subscription,
    get_plan,
    get_trial_status,
    has_used_trial,
    start_trial,
    upgrade_subscription,
)
from app.services.feedback_service import FeedbackService, FeedbackAction, FeedbackResult, FeedbackSummary, get_feedback_service
from app.services.recommend_service import (
    FeedbackRecommendation,
    RecommendService,
)
from app.services.bot_service import BotBase, BotMessage, BotCard, BotCommand, register_bot, get_bot, get_enabled_bots, list_bots
from app.services.bot_slack import SlackBot, slack_bot
from app.services.bot_feishu import FeishuBot, feishu_bot
from app.services.bot_dingtalk import DingTalkBot, dingtalk_bot
from app.services.email_service import EmailService, email_service
from app.services.email_templates import (
    welcome_html,
    trial_expiring_3d_html,
    trial_expiring_1d_html,
    trial_expired_html,
    crm_new_contact_html,
    campaign_broadcast_html,
    unsubscribe_confirmed_html,
)
from app.services.email_campaign import EmailCampaignService, get_tracking_pixel_bytes
from app.services.calendar_service import (
    CalendarBase,
    CalendarEvent,
    CalendarResult,
    register_calendar,
    get_calendar,
    get_enabled_calendars,
    list_calendars,
)
from app.services.calendar_zoom import ZoomCalendar, zoom_calendar
from app.services.calendar_tencent import TencentCalendar, tencent_calendar

# ── 链客宝合并服务 (17个新文件) ─────────────────
from app.services.action_recommender import ActionRecommender, get_action_recommender
from app.services.ai_chatbot import AIChatbotEngine, get_chatbot_engine
from app.services.contract_templates import ContractTemplateManager, get_template_manager
from app.services.crm_pipeline import create_lead, get_lead, update_lead, get_pipeline, get_pipeline_summary_for_user
from app.services.data_enrichment import BaseEnricher, QichachaEnricher, create_enricher
from app.services.dedup import DuplicateGroup, detect_duplicates, group_duplicates
from app.services.enrichment_providers import TianyanchaEnricher, AiqichaEnricher, CompositeEnricher
from app.services.escrow_service import create_deal, update_deal_status, release_payment, create_dispute, calculate_trust_score
from app.services.esign_client import EsignClient, EsignError, verify_callback_signature
from app.services.importer import ImportEngine
from app.services.llm_service import get_llm_client, get_llm_client_async, generate_matching_reason, summarize_lead
from app.services.matching_client import MatchingClient
from app.services.organization_service import create_organization, get_organization, get_user_orgs, add_member, create_invite, accept_invite
from app.services.qichacha_client import QichachaClient
from app.services.scoring_ab_test import ScoreABTest
from app.services.six_degrees import RelationGraph, PathCacheManager, find_shortest_path, find_network, compute_trust_score
from app.services.training_data_generator import generate_training_data, save_augmented_data

__all__ = [
    "BrochureService",
    "TagService",
    "MatchEngine",
    "TrustService",
    "BrochureRenderer",
    "MediaService",
    "TeamService",
    "InvoiceService",
    "PLANS",
    "PlanConfig",
    "TRIAL_DAYS",
    "can_downgrade",
    "can_upgrade",
    "downgrade_subscription",
    "get_current_subscription",
    "get_plan",
    "get_trial_status",
    "has_used_trial",
    "start_trial",
    "upgrade_subscription",
    "FeedbackService",
    "FeedbackAction",
    "FeedbackResult",
    "FeedbackSummary",
    "get_feedback_service",
    "FeedbackRecommendation",
    "RecommendService",
    # IM 机器人
    "BotBase",
    "BotMessage",
    "BotCard",
    "BotCommand",
    "register_bot",
    "get_bot",
    "get_enabled_bots",
    "list_bots",
    "SlackBot",
    "slack_bot",
    "FeishuBot",
    "feishu_bot",
    "DingTalkBot",
    "dingtalk_bot",
    # 邮件服务
    "EmailService",
    "email_service",
    "welcome_html",
    "trial_expiring_3d_html",
    "trial_expiring_1d_html",
    "trial_expired_html",
    "crm_new_contact_html",
    "campaign_broadcast_html",
    "unsubscribe_confirmed_html",
    "EmailCampaignService",
    "get_tracking_pixel_bytes",
    # 日历集成
    "CalendarBase",
    "CalendarEvent",
    "CalendarResult",
    "register_calendar",
    "get_calendar",
    "get_enabled_calendars",
    "list_calendars",
    "ZoomCalendar",
    "zoom_calendar",
    "TencentCalendar",
    "tencent_calendar",
    # 链客宝合并服务
    "ActionRecommender", "get_action_recommender",
    "AIChatbotEngine", "get_chatbot_engine",
    "ContractTemplateManager", "get_template_manager",
    "create_lead", "get_lead", "update_lead", "get_pipeline", "get_pipeline_summary_for_user",
    "BaseEnricher", "QichachaEnricher", "create_enricher",
    "DuplicateGroup", "detect_duplicates", "group_duplicates",
    "TianyanchaEnricher", "AiqichaEnricher", "CompositeEnricher",
    "create_deal", "update_deal_status", "release_payment", "create_dispute", "calculate_trust_score",
    "EsignClient", "EsignError", "verify_callback_signature",
    "ImportEngine",
    "get_llm_client", "get_llm_client_async", "generate_matching_reason", "summarize_lead",
    "MatchingClient",
    "create_organization", "get_organization", "get_user_orgs", "add_member", "create_invite", "accept_invite",
    "QichachaClient",
    "ScoreABTest",
    "RelationGraph", "PathCacheManager", "find_shortest_path", "find_network", "compute_trust_score",
    "generate_training_data", "save_augmented_data",
]
