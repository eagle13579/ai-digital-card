"""反馈闭环路由 — 用户反馈触发完整数据飞轮"""
import logging

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.ai.feedback_loop import get_feedback_loop
from app.ai.online_learning import get_online_learning_engine, get_learning_status

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["feedback"])


# ======================================================================
# 请求/响应模型
# ======================================================================


class FeedbackRequest(BaseModel):
    """反馈请求体"""
    user_id: int = Field(..., description="当前用户 ID")
    item_id: int = Field(..., description="被推荐用户 ID")
    rating: int = Field(..., description="评分: 1=👍, -1=👎, 或 1-5 星级")
    source: str = Field("recommend", description="来源: recommend/discover/similar")


class FeedbackResponse(BaseModel):
    """反馈响应体"""
    status: str = "ok"
    feedback_id: int = 0
    online_adjustment: float = 1.0
    current_weights: dict = {}


# ======================================================================
# 路由
# ======================================================================


@router.post("/feedback", response_model=FeedbackResponse)
async def post_feedback(body: FeedbackRequest):
    """提交反馈 — 触发完整数据飞轮闭环

    用户点击 👍/👎/⭐ → feedback_loop.record() → online_learning.on_feedback()
    → recommendation 权重立即可用

    请求示例:
        POST /api/feedback
        {"user_id": 1, "item_id": 42, "rating": 1, "source": "recommend"}
    """
    try:
        loop = get_feedback_loop()
        record = loop.record_feedback(
            user_id=body.user_id,
            item_id=body.item_id,
            rating=body.rating,
            source=body.source,
        )

        # 读取实时学习后的权重状态
        status = get_learning_status()
        current_weights = status.get("current_weights", {})
        global_adj = current_weights.get("global_adjustment", 1.0)

        return FeedbackResponse(
            status="ok",
            feedback_id=record.id,
            online_adjustment=global_adj,
            current_weights=current_weights,
        )
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        logger.error("反馈提交失败: %s", e, exc_info=True)
        raise HTTPException(status_code=500, detail=f"反馈提交失败: {e}")
