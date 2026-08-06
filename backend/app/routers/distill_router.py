"""企业知识蒸馏服务 — F-CARD-01 MVP

B端企业客户上传资料 → 一键蒸馏 → 企业知识库（结构化条目 + 检索）。

API:
  POST /api/v1/distill/upload    上传素材（title/content）→ 保存并触发蒸馏
  GET  /api/v1/distill/run       触发蒸馏（处理待蒸馏素材目录）
  GET  /api/v1/distill/kb        企业知识库列表
  GET  /api/v1/distill/kb/search 企业知识库检索

复用: backend/scripts/gaia_distill.py 一键蒸馏管线（A8一键/A9安全/A10分级）
"""
from __future__ import annotations

import asyncio
import logging
import subprocess
from datetime import datetime, timezone
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy import select, or_
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.gaia import GaiaKnowledge

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/distill", tags=["企业知识蒸馏"])

BACKEND = Path("/var/www/ai-digital-card/backend")
RAW_DIR = BACKEND / "data" / "enterprise_kb" / "raw"
DISTILL_SCRIPT = BACKEND / "scripts" / "gaia_distill.py"
VENV_PY = BACKEND / "venv" / "bin" / "python3"
KB_SOURCE = "distill_enterprise"


# ======================================================================
# Schemas
# ======================================================================

class DistillUploadRequest(BaseModel):
    """素材上传请求"""
    title: str = Field(..., description="素材标题")
    content: str = Field(..., description="素材内容（文本）")
    tenant: str = Field("default", description="租户标识")


class DistillRunResponse(BaseModel):
    ok: bool
    message: str
    pid: int | None = None


# ======================================================================
# 素材上传
# ======================================================================

@router.post("/upload")
async def upload_material(req: DistillUploadRequest):
    """上传企业素材 → 保存到待蒸馏目录"""
    if len(req.content.strip()) < 100:
        raise HTTPException(status_code=422, detail="素材内容过短（至少100字）")
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    safe = "".join(c for c in req.title if c.isalnum() or c in "_- ")[:60].strip()
    fname = f"{ts}_{req.tenant}_{safe or 'material'}.md"
    fpath = RAW_DIR / fname
    fpath.write_text(
        f"# {req.title}\n\n{req.content}\n\n---\n[tenant: {req.tenant}]\n",
        encoding="utf-8",
    )
    # 立即后台触发蒸馏
    asyncio.create_task(_run_distill_bg())
    return {"ok": True, "file": fname, "message": "素材已保存，蒸馏已触发"}


# ======================================================================
# 蒸馏触发
# ======================================================================

async def _run_distill_bg() -> None:
    """后台运行 gaia_distill.py 处理待蒸馏素材"""
    try:
        proc = await asyncio.create_subprocess_exec(
            str(VENV_PY), str(DISTILL_SCRIPT),
            "--file", str(RAW_DIR),
            "--source-tag", KB_SOURCE,
            "--max", "20",
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.STDOUT,
        )
        await asyncio.wait_for(proc.communicate(), timeout=420)
    except Exception as e:  # noqa: BLE001
        logger.error("企业蒸馏后台任务失败: %s", e)


@router.get("/run")
async def trigger_distill():
    """手动触发蒸馏（同步等待，适合调试/小批量）"""
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    proc = subprocess.run(
        [str(VENV_PY), str(DISTILL_SCRIPT), "--file", str(RAW_DIR),
         "--source-tag", KB_SOURCE, "--max", "20"],
        capture_output=True, text=True, timeout=430,
    )
    tail = (proc.stdout or "")[-1500:]
    return {"ok": proc.returncode == 0, "returncode": proc.returncode, "output": tail}


# ======================================================================
# 企业知识库
# ======================================================================

@router.get("/kb")
async def list_kb(
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
):
    """企业知识库列表（最新在前）"""
    stmt = (
        select(GaiaKnowledge)
        .where(GaiaKnowledge.source == KB_SOURCE)
        .order_by(GaiaKnowledge.id.desc())
        .limit(limit)
        .offset(offset)
    )
    rows = (await db.execute(stmt)).scalars().all()
    total = (await db.execute(
        select(GaiaKnowledge.id).where(GaiaKnowledge.source == KB_SOURCE)
    )).all()
    return {
        "total": len(total),
        "items": [
            {
                "id": k.id,
                "knowledge_type": k.knowledge_type,
                "title": k.title,
                "content": (k.content or "")[:500],
                "tags": k.tags or [],
                "confidence": k.confidence,
                "created_at": k.created_at.isoformat() if k.created_at else None,
            }
            for k in rows
        ],
    }


@router.get("/kb/search")
async def search_kb(
    q: str = Query(..., min_length=1, max_length=100),
    limit: int = Query(10, ge=1, le=50),
    db: AsyncSession = Depends(get_db),
):
    """企业知识库检索（标题/内容模糊匹配）"""
    like = f"%{q}%"
    stmt = (
        select(GaiaKnowledge)
        .where(
            GaiaKnowledge.source == KB_SOURCE,
            or_(GaiaKnowledge.title.ilike(like), GaiaKnowledge.content.ilike(like)),
        )
        .order_by(GaiaKnowledge.id.desc())
        .limit(limit)
    )
    rows = (await db.execute(stmt)).scalars().all()
    return {
        "query": q,
        "count": len(rows),
        "items": [
            {
                "id": k.id,
                "knowledge_type": k.knowledge_type,
                "title": k.title,
                "content": (k.content or "")[:500],
                "tags": k.tags or [],
            }
            for k in rows
        ],
    }
