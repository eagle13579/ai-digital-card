from app.routers.auth import router as auth_router
from app.routers.user import router as user_router
from app.routers.brochure import router as brochure_router
from app.routers.tag import router as tag_router
from app.routers.match import router as match_router
from app.routers.match import brochure_alias_router
from app.routers.visitor import router as visitor_router
from app.routers.trust import router as trust_router
from app.routers.i18n import router as i18n_router

__all__ = [
    "auth_router",
    "user_router",
    "brochure_router",
    "tag_router",
    "match_router",
    "brochure_alias_router",
    "visitor_router",
    "trust_router",
    "i18n_router",
]
