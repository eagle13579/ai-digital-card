"""Personalization routes — interact, recommend, trending."""
from fastapi import APIRouter, Depends
from app.ai.online_learning import OnlineLearningPipeline
from app.ai.bandit_engine import BanditService
from app.middleware.rbac import require_permission
from app.models.user import User
from app.routers.auth import get_current_user

router = APIRouter(prefix="/api/v1/personalization", tags=["personalization"])
pipeline = OnlineLearningPipeline()
bandit = BanditService({})

@router.post("/interact")
async def record_interaction(user_id: str, item_id: str, action: str = "view",
                             current_user: User = Depends(get_current_user)):
    # BUG-021 修复: user_id 强制绑定当前用户，防交叉读取
    if user_id != str(current_user.id):
        user_id = str(current_user.id)
    pipeline.record_interaction(user_id, item_id, action)
    return {"status": "ok"}

@router.get("/recommend")
async def recommend(user_id: str, top_k: int = 10,
                    current_user: User = Depends(get_current_user)):
    # BUG-021 修复: 绑定当前用户
    if user_id != str(current_user.id):
        user_id = str(current_user.id)
    candidates = pipeline.get_trending(hours=72, limit=50)
    items = [{"id": i} for i in candidates]
    return bandit.recommend(items, user_id, top_k=top_k, id_key="id")

@router.get("/trending")
async def trending(hours: int = 24, limit: int = 20,
                   current_user: User = Depends(get_current_user)):
    return {"items": pipeline.get_trending(hours=hours, limit=limit)}

@router.get("/history")
async def history(user_id: str, limit: int = 50,
                  current_user: User = Depends(get_current_user)):
    # BUG-021 修复: 绑定当前用户
    if user_id != str(current_user.id):
        user_id = str(current_user.id)
    return {"items": pipeline.get_user_history(user_id, limit=limit)}
