"""agent 永久记忆 API — OptMem 能力的产品化封装

提供 wake/note/recall/zoom/nap/forget/stats 端点，让任何 Agent
（或 AI数智名片内的智能体）拥有跨会话、跨模型、纯文本的永久记忆。

设计哲学（源自 OptMem / VictorTaelin）：
  - 文件系统就是数据库：append-only 纯文本 LOG，固定宽度记录，位置即身份
  - 正则搜索就是检索引擎：无需向量库、无需嵌入模型
  - 280 字节一行记忆：最可靠的记忆格式，换模型/厂商不丢失

生产注意：
  - 记忆库目录由 AGENT_MEMORY_DIR 环境变量控制（默认 backend/data/agent_memory）
  - wake 返回的 nap_prompt 需由调用方（LLM）产出一行摘要后调 /nap 提交
"""

from __future__ import annotations

import logging
from typing import Optional

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from services.optmem_service import (
    forget as svc_forget,
    nap as svc_nap,
    note as svc_note,
    recall as svc_recall,
    stats as svc_stats,
    wake as svc_wake,
    zoom as svc_zoom,
)
from services.optmem_core import OptMemError

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/memory", tags=["Agent永久记忆"])


# ======================================================================
# Schemas
# ======================================================================

class NoteRequest(BaseModel):
    text: str = Field(..., min_length=1, max_length=280,
                      description="一行记忆，≤280 字节")


class NapRequest(BaseModel):
    block: str = Field(..., description="块 id，形如 '0-1'（来自 wake/nap_prompt）")
    summary: str = Field(..., min_length=1, max_length=280,
                         description="LLM 产出的压缩摘要，≤280 字节")


class ForgetRequest(BaseModel):
    block: str = Field(..., description="要删除的块 id，形如 '0-1'")


# ======================================================================
# Endpoints
# ======================================================================

@router.get("/stats", summary="记忆库状态")
def get_stats():
    """返回记忆库统计：记忆数、待压缩数、配置。"""
    return svc_stats()


@router.get("/wake", summary="唤醒：读取记忆上下文")
def get_wake(limit: Optional[int] = Query(None, ge=1, le=1000,
                                          description="阅读行数预算")):
    """读取当前全部记忆（树渲染：近期详细、远期摘要）。

    返回 lines 为渲染文本；若 blocked=True，需先 nap 补摘要再 wake。
    """
    try:
        return svc_wake(limit=limit)
    except OptMemError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/note", summary="记录一条记忆")
def post_note(req: NoteRequest):
    """记录一行记忆（≤280 字节）。若触发压缩阈值，返回 nap_prompt。"""
    try:
        return svc_note(req.text)
    except OptMemError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/nap", summary="提交压缩摘要")
def post_nap(req: NapRequest):
    """提交某块的压缩摘要（由 LLM 根据 nap_prompt 产出）。"""
    try:
        return svc_nap(req.block, req.summary)
    except OptMemError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/recall", summary="正则搜索记忆")
def get_recall(q: str = Query(..., description="正则表达式，逐字匹配"),
               newest: int = Query(20000, ge=100, le=100000,
                                   description="最多返回字节数")):
    """搜索全部历史记忆（正则，不区分大小写）。"""
    try:
        return svc_recall(q, newest=newest)
    except OptMemError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/zoom", summary="展开树节点")
def get_zoom(block: str = Query(..., description="块 id，形如 '0-1'")):
    """把摘要块展开为其两半（直到原始记忆）。"""
    try:
        return svc_zoom(block)
    except OptMemError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/forget", summary="删除坏摘要")
def delete_forget(req: ForgetRequest):
    """删除错误的摘要（及上层），LOG 不动，下次 nap 自动重建。"""
    try:
        return svc_forget(req.block)
    except OptMemError as e:
        raise HTTPException(status_code=400, detail=str(e))
