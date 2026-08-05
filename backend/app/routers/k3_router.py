"""
AI数智名片 × K3 匹配增强 — API 端点
====================================
Kimi K3 1M 超长上下文匹配：一次性理解企业全部资料（宣传册/名片/需求文档），
输出企业画像 + 匹配机会 + 跨境合作可能 + 推荐语。

端点:
  POST /api/match/k3/analyze   — 企业资料全文 K3 分析匹配
  GET  /api/match/k3/status    — K3 服务状态（key 是否配置）
"""
import logging
import os
import sys
import time
from typing import Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

# K3 服务库（/var/www/baize_libs）
sys.path.insert(0, "/var/www/baize_libs")
try:
    from kimi_k3_service import KimiK3Client, KimiK3Router, K3APIKeyError
    K3_LIB_OK = True
except Exception as e:  # pragma: no cover
    K3_LIB_OK = False
    logger.error("K3 服务库导入失败: %s", e)

router = APIRouter(prefix="/api/match/k3", tags=["K3匹配"])

PROMPT = """你是一个企业供需匹配专家。
请分析以下企业资料，输出：

## 一、企业画像
- 主营业务、规模、行业地位
- 核心能力/资源
- 当前痛点/需求

## 二、匹配机会
- 适合对接的供应商/客户类型
- 跨境合作可能性（韩国/中国）
- 匹配优先级排序

## 三、一句话推荐语（用于数字名片展示）

企业资料：
---
{content}
---"""


class K3AnalyzeRequest(BaseModel):
    content: str = Field(..., min_length=50, max_length=600000,
                         description="企业资料全文（宣传册/名片/需求文档），K3 可处理 1M 上下文")
    title: str = Field("企业资料", description="资料名称")
    force: bool = Field(False, description="强制走 K3（即使内容较短）")


class K3AnalyzeResponse(BaseModel):
    success: bool
    engine: str = "kimi-k3"
    model: str = ""
    used_k3: bool = True
    routed_to: str = "k3"
    result: str
    latency_ms: float
    note: str = ""


@router.get("/status")
async def k3_status():
    """K3 服务状态检查"""
    if not K3_LIB_OK:
        return {"success": False, "lib": "missing",
                "detail": "kimi_k3_service 库未安装"}
    try:
        client = KimiK3Client()
        return {"success": True, "lib": "ok", "key": "configured",
                "model": client.model, "base_url": client.base_url}
    except K3APIKeyError:
        return {"success": False, "lib": "ok", "key": "missing",
                "detail": "KIMI_K3_API_KEY 未配置（backend/.env 或环境变量）"}


@router.post("/analyze", response_model=K3AnalyzeResponse)
async def k3_analyze(data: K3AnalyzeRequest):
    """企业资料 K3 全量分析匹配"""
    if not K3_LIB_OK:
        raise HTTPException(status_code=503, detail="K3 服务库未安装")

    t0 = time.time()
    try:
        client = KimiK3Client()
    except K3APIKeyError as e:
        raise HTTPException(status_code=503, detail=str(e))

    router = KimiK3Router()
    n = len(data.content)

    # 路由决策：内容足够长或强制时走 K3；短内容提示可走轻量
    use_k3 = data.force or router.should_use_k3("analysis", n)
    if not use_k3:
        return K3AnalyzeResponse(
            success=True,
            model=router.suggest_model(n),
            used_k3=False,
            routed_to="short",
            result="内容较短（{}字），建议用轻量模型处理；如需 K3 1M 全量分析请传 force=true".format(n),
            latency_ms=0,
            note="KimiK3Router 自动路由",
        )

    try:
        prompt = PROMPT.format(content=data.content[:500000])
        result = client.chat_completion(prompt, system="你是一个企业供需匹配专家。")
        latency = (time.time() - t0) * 1000
        return K3AnalyzeResponse(
            success=True,
            model=client.model,
            used_k3=True,
            routed_to="k3",
            result=result,
            latency_ms=round(latency, 1),
        )
    except Exception as e:
        logger.exception("K3 分析失败")
        raise HTTPException(status_code=502, detail=f"K3 调用失败: {e}")
