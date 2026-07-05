"""AI 客服配置 API — 基于JSON文件持久化（按用户隔离）"""
import json
import logging
import os
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from app.database import get_db
from app.models.user import User
from app.routers.auth import get_current_user

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/ai/config", tags=["AI 配置"])

# ── JSON文件存储路径 ──────────────────────────────────────────────
CONFIG_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "data", "ai_configs")
os.makedirs(CONFIG_DIR, exist_ok=True)


def _config_path(user_id: int) -> str:
    return os.path.join(CONFIG_DIR, f"user_{user_id}.json")


def _load_config(user_id: int) -> dict:
    path = _config_path(user_id)
    if not os.path.exists(path):
        return {}
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError) as e:
        logger.warning("读取AI配置失败 (user=%s): %s", user_id, e)
        return {}


def _save_config(user_id: int, config: dict) -> None:
    path = _config_path(user_id)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(config, f, ensure_ascii=False, indent=2)


# ── 请求/响应模型 ──────────────────────────────────────────────────


class AIConfigResponse(BaseModel):
    autoReply: bool = True
    smartRecommend: bool = True
    dataAnalysis: bool = False
    filterSensitive: bool = True
    timeout: int = 30
    welcomeMessage: str = "您好！我是AI智能客服，请问有什么可以帮您的？"

    model_config = {"from_attributes": True}


class AIConfigUpdate(BaseModel):
    autoReply: bool | None = None
    smartRecommend: bool | None = None
    dataAnalysis: bool | None = None
    filterSensitive: bool | None = None
    timeout: int | None = None
    welcomeMessage: str | None = None


# ── API 端点 ──────────────────────────────────────────────────────


@router.get("", response_model=AIConfigResponse)
async def get_ai_config(
    current_user: User = Depends(get_current_user),
    db: Any = Depends(get_db),
):
    """获取当前用户的AI客服配置（不存在则返回默认值）"""
    raw = _load_config(current_user.id)
    if not raw:
        return AIConfigResponse()
    # 只返回有效字段
    defaults = AIConfigResponse().model_dump()
    merged = {**defaults, **raw}
    return AIConfigResponse(**merged)


@router.post("", response_model=AIConfigResponse)
async def save_ai_config(
    data: AIConfigUpdate,
    current_user: User = Depends(get_current_user),
    db: Any = Depends(get_db),
):
    """保存当前用户的AI客服配置（增量更新）"""
    existing = _load_config(current_user.id)
    # 只写入非 None 字段
    update_dict = data.model_dump(exclude_none=True)
    merged = {**existing, **update_dict}

    # 校验 timeout 范围
    if "timeout" in merged and (merged["timeout"] < 5 or merged["timeout"] > 300):
        raise HTTPException(status_code=422, detail="timeout 必须在 5~300 秒之间")

    _save_config(current_user.id, merged)
    logger.info("AI配置已保存 (user=%s): %s", current_user.id, update_dict)

    defaults = AIConfigResponse().model_dump()
    final = {**defaults, **merged}
    return AIConfigResponse(**final)
