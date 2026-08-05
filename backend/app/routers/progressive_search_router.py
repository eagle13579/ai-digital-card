"""
F15 渐进式人脉搜索 — 路由层 (Progressive Search Router)

设计理念 (F15):
────────────────────────────────────────────────────────
渐进式人脉搜索颠覆传统"一刀切"的搜索模式，采用两阶段渐进策略：

  Phase 1 — 广度撒网 (Broad Tag Matching):
    基于用户标签体系，从三个维度综合评分：
    - 语义相似度 (40%) — 通过M3E兼容的标签向量余弦相似度计算
    - 社交信任度 (35%) — 基于六度关系图的直接信任分
    - 供需互补度 (25%) — 双方 provide/need 标签的供需耦合度
    输出前 N 个高潜力候选用户，用于下一阶段深度探索。

  Phase 2 — 深度挖掘 (Deep Social Graph Exploration):
    对 Phase 1 的 Top K 候选，通过双向BFS算法
    在六度人脉关系图中逐一寻找与搜索发起方之间的最短连接路径。
    返回每位的连接路径、路径信任度、中间节点信息。

API 设计原则:
  - 拆分两个独立端点 (/phase1, /phase2) 和一站式端点 (/full)
  - 前端可灵活选择：仅标签匹配 / 完整渐进式搜索
  - 所有端点响应遵循统一格式 {code, message, data}

路径前缀: /api/business-card/progressive-search
标签: 渐进式人脉搜索

依赖:
  - app.services.progressive_search_service 的 phase1_tag_matching,
    phase2_social_exploration, full_progressive_search
  - app.models.user.User 用户模型
  - app.models.tag.UserTag 标签模型
  - app.services.six_degrees.RelationGraph / bidirectional_bfs (Phase 2)
"""

import logging
import time
from typing import Optional

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.user import User
from app.routers.auth import get_current_user
from app.api_standards import raise_http_error, ErrorCode
from app.services import progressive_search_service as pss

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/business-card/progressive-search",
    tags=["渐进式人脉搜索"],
)


# ── Pydantic 请求/响应模型 ──────────────────────────────────


class Phase1Request(BaseModel):
    """Phase 1: 广度标签匹配请求"""
    query_tags: Optional[list[str]] = Field(
        None,
        description="搜索标签列表（不传则从用户自身标签自动推导搜索意图）",
    )
    limit: int = Field(
        50, ge=1, le=200,
        description="返回候选用户数上限（1~200）",
    )
    min_score: float = Field(
        0.0, ge=0.0, le=1.0,
        description="最低综合评分阈值（0.0~1.0）",
    )
    tag_type: Optional[str] = Field(
        None,
        description="标签类型过滤: provide / need / 不传则为全部",
    )


class Phase2Request(BaseModel):
    """Phase 2: 深度社交图谱探索请求"""
    candidates: list[dict] = Field(
        ...,
        description="Phase 1 输出的候选列表（直接从 /phase1 响应传入即可）",
    )
    max_depth: int = Field(
        6, ge=1, le=6,
        description="BFS最大搜索深度（1~6，六度人脉上限）",
    )
    top_k: int = Field(
        20, ge=1, le=50,
        description="最多对 top_k 个候选执行深度探索",
    )


class FullSearchRequest(BaseModel):
    """全流程渐进式搜索请求"""
    query_tags: Optional[list[str]] = Field(
        None,
        description="搜索标签列表",
    )
    phase1_limit: int = Field(
        50, ge=1, le=200,
        description="Phase 1 候选数上限",
    )
    phase2_top_k: int = Field(
        20, ge=1, le=50,
        description="Phase 2 深度探索的 Top K",
    )
    max_depth: int = Field(
        6, ge=1, le=6,
        description="BFS最大搜索深度",
    )
    min_score: float = Field(
        0.0, ge=0.0, le=1.0,
        description="最低综合评分阈值",
    )
    tag_type: Optional[str] = Field(
        None,
        description="标签类型过滤",
    )


# ── 辅助函数 ────────────────────────────────────────────────


def success(data: any = None, message: str = "操作成功") -> dict:
    """统一成功响应"""
    return {"code": 0, "message": message, "data": data}


# ── API 端点 — Phase 1: 广度标签匹配 ────────────────────────


@router.post("/phase1", summary="Phase 1 — 广度标签匹配")
async def search_phase1(
    req: Phase1Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Phase 1 — 广度撒网式标签匹配

    基于用户的标签体系进行多维综合评分搜索：
      - 语义相似度 (40%) : 标签向量余弦相似度
      - 社交信任度 (35%) : 基于六度关系图的信任分
      - 供需互补度 (25%) : 双方标签的供需耦合程度

    返回按综合评分降序排列的候选用户列表，
    供前端预览或传入 Phase 2 进行深度社交探索。
    """
    t_start = time.time()

    results = await pss.phase1_tag_matching(
        db=db,
        user_id=current_user.id,
        query_tags=req.query_tags,
        limit=req.limit,
        min_score=req.min_score,
        tag_type=req.tag_type,
    )

    elapsed_ms = round((time.time() - t_start) * 1000, 2)

    logger.info(
        "Phase1搜索 user=%d, candidates=%d, time=%dms",
        current_user.id, len(results), elapsed_ms,
    )

    return success({
        "candidates": results,
        "total": len(results),
        "time_ms": elapsed_ms,
    })


# ── API 端点 — Phase 2: 深度社交图谱探索 ────────────────────


@router.post("/phase2", summary="Phase 2 — 深度社交图谱探索")
async def search_phase2(
    req: Phase2Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Phase 2 — 深度社交图谱探索

    对 Phase 1 输出的候选列表，通过双向BFS算法
    在六度人脉关系图中，逐一查找候选人与搜索发起方之间的
    最短连接路径。

    返回每位候选人的：
      - 人脉连接路径（节点ID列表）
      - 路径信任度（信任衰减后）
      - 路径中各跳节点详情（姓名、公司、职位）
      - 是否为直接连接（一度人脉）
    """
    if not req.candidates:
        raise_http_error(
            400, ErrorCode.VALIDATION_ERROR,
            "candidates 列表不能为空，请先调用 Phase 1 获取候选列表",
        )

    if req.top_k > len(req.candidates):
        req.top_k = len(req.candidates)

    t_start = time.time()

    results = await pss.phase2_social_exploration(
        db=db,
        user_id=current_user.id,
        candidates=req.candidates,
        max_depth=req.max_depth,
        top_k=req.top_k,
    )

    elapsed_ms = round((time.time() - t_start) * 1000, 2)

    # 统计
    connected = sum(1 for r in results if r["social_path"]["length"] >= 0)
    direct = sum(1 for r in results if r["social_path"].get("direct_connection"))

    logger.info(
        "Phase2探索 user=%d, explored=%d, connected=%d, direct=%d, time=%dms",
        current_user.id, len(results), connected, direct, elapsed_ms,
    )

    return success({
        "results": results,
        "stats": {
            "explored": len(results),
            "connected": connected,
            "direct_connections": direct,
            "time_ms": elapsed_ms,
        },
    })


# ── API 端点 — 全流程渐进式搜索 ─────────────────────────────


@router.post("/full", summary="全流程渐进式搜索（Phase 1 + Phase 2）")
async def search_full(
    req: FullSearchRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    全流程渐进式人脉搜索

    一站式执行两阶段渐进式搜索：
      1. 广度撒网 — 标签多维匹配获得候选列表
      2. 深度挖掘 — 为 Top K 候选在社交图谱中寻找连接路径

    返回包含 phase1 和 phase2 两部分结果的完整响应，
    以及两阶段各自的耗时统计。

    适用场景：
      - 前端希望一次请求完成全流程搜索
      - 需要同时获取标签匹配结果和社交路径信息
    """
    t_start = time.time()

    full_result = await pss.full_progressive_search(
        db=db,
        user_id=current_user.id,
        query_tags=req.query_tags,
        phase1_limit=req.phase1_limit,
        phase2_top_k=req.phase2_top_k,
        max_depth=req.max_depth,
        min_score=req.min_score,
        tag_type=req.tag_type,
    )

    elapsed_ms = round((time.time() - t_start) * 1000, 2)

    logger.info(
        "全流程渐进式搜索 user=%d, complete, total_time=%dms",
        current_user.id, elapsed_ms,
    )

    full_result["stats"]["total_time_ms"] = elapsed_ms
    return success(full_result)
