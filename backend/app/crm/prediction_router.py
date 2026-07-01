"""AI 销售预测 API 路由。

端点:
  GET    /api/crm/prediction/deal/{deal_id}  → 单个 Deal 的赢单率预测
  POST   /api/crm/prediction/retrain         → 重新训练模型
  GET    /api/crm/prediction/status          → 模型状态
"""

from __future__ import annotations

import logging

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.crm.crm_rbac import REPORTS_VIEW, require_permission
from app.services.sales_prediction import get_prediction_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/crm/prediction", tags=["CRM-销售预测"])


# ═══════════════════════════════════════════════════════════════════════════════════
# Pydantic Schemas
# ═══════════════════════════════════════════════════════════════════════════════════


class SinglePredictionResponse(BaseModel):
    """单 Deal 预测响应。"""
    deal_id: int
    title: str = ""
    contact_name: str = ""
    contact_source: str = ""
    stage_name: str | None = None
    deal_value: float = 0.0
    predicted_win_probability: float = Field(
        ..., description="预测赢单率 (0~100%)"
    )
    confidence: str = Field(
        ..., description="置信度: high / medium / low"
    )
    model_trained: bool = False
    features: dict = Field(default_factory=dict)


class RetrainRequest(BaseModel):
    """重新训练请求（无参数，可留空）"""
    pass


class RetrainResponse(BaseModel):
    """重新训练响应。"""
    success: bool
    message: str
    samples: int = 0
    won: int = 0
    lost: int = 0
    accuracy: float | None = None
    final_loss: float | None = None
    features: int = 0


class ModelStatusResponse(BaseModel):
    """模型状态响应。"""
    model_trained: bool
    train_samples: int
    accuracy: float | None = None
    n_features: int = 0
    features_description: list[str] = Field(default_factory=list)


# ═══════════════════════════════════════════════════════════════════════════════════
# API 端点
# ═══════════════════════════════════════════════════════════════════════════════════


@router.get("/deal/{deal_id}", response_model=SinglePredictionResponse)
async def predict_deal(
    deal_id: int,
    db: AsyncSession = Depends(get_db),
    _: None = Depends(require_permission(REPORTS_VIEW)),
):
    """预测单个 Deal 的赢单率。

    基于历史成交数据的逻辑回归模型，输出 0~100% 的赢单概率和置信度。
    """
    svc = get_prediction_service()
    result = await svc.predict_deal(deal_id, db)

    if "error" in result:
        raise HTTPException(status_code=404, detail=result["error"])

    return SinglePredictionResponse(
        deal_id=result["deal_id"],
        title=result.get("title", ""),
        contact_name=result.get("contact_name", ""),
        contact_source=result.get("contact_source", ""),
        stage_name=result.get("stage_name"),
        deal_value=result.get("deal_value", 0.0),
        predicted_win_probability=result["predicted_win_probability"],
        confidence=result["confidence"],
        model_trained=result["model_trained"],
        features=result.get("features", {}),
    )


@router.post("/retrain", response_model=RetrainResponse)
async def retrain_model(
    db: AsyncSession = Depends(get_db),
    _: None = Depends(require_permission(REPORTS_VIEW)),
):
    """使用数据库中所有历史成交/丢失记录重新训练预测模型。"""
    svc = get_prediction_service()
    result = await svc.train(db)

    return RetrainResponse(
        success=result.get("success", False),
        message=result.get("message", ""),
        samples=result.get("samples", 0),
        won=result.get("won", 0),
        lost=result.get("lost", 0),
        accuracy=result.get("accuracy"),
        final_loss=result.get("final_loss"),
        features=result.get("features", 0),
    )


@router.get("/status", response_model=ModelStatusResponse)
async def model_status(
    _: None = Depends(require_permission(REPORTS_VIEW)),
):
    """获取当前预测模型的状态（是否已训练、样本数、准确率等）。"""
    svc = get_prediction_service()
    status = svc.get_status()
    return ModelStatusResponse(
        model_trained=status["model_trained"],
        train_samples=status["train_samples"],
        accuracy=status["accuracy"],
        n_features=status["n_features"],
        features_description=status["features_description"],
    )
