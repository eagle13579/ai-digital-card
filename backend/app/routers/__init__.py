from app.routers.ai_assist import router as ai_assist_router
from app.routers.auth import router as auth_router
from app.routers.user import router as user_router
from app.routers.brochure import router as brochure_router
from app.routers.tag import router as tag_router
from app.routers.match import router as match_router
from app.routers.match import brochure_alias_router
from app.routers.visitor import router as visitor_router
from app.routers.trust import router as trust_router
from app.routers.i18n import router as i18n_router
from app.routers.share import router as share_router
from app.routers.public import router as public_router
from app.routers.team import router as team_router
from app.routers.integrations import router as integration_router
from app.routers.export import router as export_router
from app.routers.webhooks import router as webhook_router
from app.routers.ab_test import router as ab_test_router
from app.routers.gdpr import router as gdpr_router

from app.routers.payment import router as payment_router
from app.routers.recommend import router as recommend_router
from app.routers.sso import router as sso_router
from app.routers.api_keys import router as api_keys_router
from app.routers.docs import router as docs_router
from app.routers.web_vitals import router as web_vitals_router
from app.routers.graphql_route import graphql_router
from app.routers.oauth import router as oauth_router
from app.routers.admin import router as admin_router
from app.routers.tenant_api import router as tenant_router
from app.routers.developer import router as developer_router
from app.routers.messages import router as message_router
from app.routers.invoice import router as invoice_router
from app.routers.knowledge_graph import router as knowledge_graph_router
from app.routers.subscription_router import router as subscription_router
from app.routers.gaia_router import router as gaia_router
from app.crm.crm_router import router as crm_router
from app.routers.bot_router import router as bot_router
from app.routers.document import router as document_router
from app.routers.analytics import router as analytics_router
from app.routers.social_connect_router import router as social_connect_router
from app.routers.resource_platform_router import router as resource_platform_router
from app.routers.nfc import router as nfc_router
from app.routers.token_pricing_router import router as token_pricing_router
from app.routers.membership import router as membership_router
from app.routers.health import router as health_router
from app.routers.metrics_dashboard import router as metrics_dashboard_router

__all__ = [
    "ai_assist_router",
    "auth_router",
    "user_router",
    "brochure_router",
    "tag_router",
    "match_router",
    "brochure_alias_router",
    "visitor_router",
    "trust_router",
    "i18n_router",
    "share_router",
    "public_router",
    "team_router",
    "integration_router",
    "export_router",
    "webhook_router",
    "ab_test_router",
    "gdpr_router",
    "payment_router",
    "recommend_router",
    "sso_router",
    "api_keys_router",
    "docs_router",
    "web_vitals_router",
    "graphql_router",
    "oauth_router",
    "admin_router",
    "tenant_router",
    "developer_router",
    "message_router",
    "invoice_router",
    "knowledge_graph_router",
    "subscription_router",
    "gaia_router",
    "crm_router",
    "bot_router",
    "document_router",
    "analytics_router",
    "social_connect_router",
    "resource_platform_router",
    "nfc_router",
    "token_pricing_router",
    "membership_router",
    "health_router",
    "metrics_dashboard_router",

]
