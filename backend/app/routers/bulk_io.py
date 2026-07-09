"""批量 IO 路由 — CSV 导入/导出/模板/任务状态。

端点前缀: /api/admin/bulk

  POST   /api/admin/bulk/import           — 上传 CSV 导入（multipart/form-data）
  GET    /api/admin/bulk/export            — 导出 CSV（query params: entity_type, format=csv）
  GET    /api/admin/bulk/template          — 下载导入模板（query params: entity_type）
  GET    /api/admin/bulk/import/{job_id}/status  — 查询导入任务状态

支持的实体类型: contacts, brochures, users
"""

from __future__ import annotations

import logging
import time
from typing import Any
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File
from fastapi.responses import PlainTextResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.user import User
from app.routers.admin import require_admin
from app.services.bulk_io_service import (
    BulkIOService,
    _import_jobs,
    get_bulk_io_service,
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/admin/bulk", tags=["Admin Bulk I/O"])

AdminDep = Depends(require_admin)


# ── 依赖：获取当前用户 ID ──────────────────────────────────────────────────


async def _get_current_user_id(
    _admin: bool = AdminDep,
    db: AsyncSession = Depends(get_db),
) -> int:
    """为了权限暂时仅传回 admin 标记。实际可扩展为真实 user 注入。"""
    # 管理员操作的 user_id 暂设为 0（全局操作）
    return 0


async def _get_service(
    db: AsyncSession = Depends(get_db),
    user_id: int = Depends(_get_current_user_id),
) -> BulkIOService:
    return BulkIOService(db=db, user_id=user_id)


# ── 工具函数 ────────────────────────────────────────────────────────────────


_VALID_ENTITY_TYPES = {"contacts", "brochures", "users"}


def _validate_entity_type(entity_type: str) -> None:
    if entity_type not in _VALID_ENTITY_TYPES:
        raise HTTPException(
            status_code=400,
            detail=f"不支持的实体类型 '{entity_type}'，允许: {', '.join(sorted(_VALID_ENTITY_TYPES))}",
        )


# ── 导入 ────────────────────────────────────────────────────────────────────


@router.post("/import", status_code=201)
async def bulk_import(
    file: UploadFile = File(...),
    entity_type: str = Query(..., description="实体类型: contacts/brochures/users"),
    svc: BulkIOService = Depends(_get_service),
):
    """上传 CSV 文件批量导入数据。

    接收 multipart/form-data:
      - file: CSV 文件（UTF-8 with BOM）
      - entity_type: 实体类型
    """
    _validate_entity_type(entity_type)

    content = await file.read()
    try:
        csv_text = content.decode("utf-8-sig")  # 自动处理 BOM
    except UnicodeDecodeError:
        raise HTTPException(status_code=400, detail="文件编码错误，请使用 UTF-8 编码")

    # 启动导入任务
    result = await svc.import_csv(csv_text, entity_type)

    # 记录到任务状态
    job_id = uuid4().hex[:12]
    _import_jobs[job_id] = {
        "id": job_id,
        "entity_type": entity_type,
        "status": "completed",
        "total_rows": result.total_rows,
        "success_rows": result.success_rows,
        "error_rows": result.error_rows,
        "errors_detail": [
            {"row": e.row, "message": e.message, "raw_data": e.raw_data}
            for e in result.errors_detail
        ],
        "created_at": time.time(),
        "file_name": file.filename,
    }

    return {
        "job_id": job_id,
        "status": "completed",
        "total_rows": result.total_rows,
        "success_rows": result.success_rows,
        "error_rows": result.error_rows,
        "errors_detail": [
            {"row": e.row, "message": e.message, "raw_data": e.raw_data}
            for e in result.errors_detail
        ],
    }


# ── 导出 ────────────────────────────────────────────────────────────────────


@router.get("/export")
async def bulk_export(
    entity_type: str = Query(..., description="实体类型: contacts/brochures/users"),
    format: str = Query("csv", description="导出格式（当前仅支持 csv）"),
    svc: BulkIOService = Depends(_get_service),
):
    """导出指定实体类型为 CSV 文件。"""
    _validate_entity_type(entity_type)

    if format != "csv":
        raise HTTPException(
            status_code=400,
            detail=f"不支持的导出格式 '{format}'，当前仅支持 'csv'",
        )

    result = await svc.export_csv(entity_type)

    return PlainTextResponse(
        content=result.csv_content,
        media_type="text/csv; charset=utf-8",
        headers={
            "Content-Disposition": f'attachment; filename="{result.file_name}"',
            "X-Total-Count": str(result.row_count),
        },
    )


# ── 模板 ────────────────────────────────────────────────────────────────────


@router.get("/template")
async def bulk_template(
    entity_type: str = Query(..., description="实体类型: contacts/brochures/users"),
    db: AsyncSession = Depends(get_db),
):
    """下载带示例数据的 CSV 导入模板。"""
    _validate_entity_type(entity_type)

    svc = BulkIOService(db=db)
    csv_content = svc.get_import_template(entity_type)

    file_name = f"{entity_type}_import_template.csv"

    return PlainTextResponse(
        content=csv_content,
        media_type="text/csv; charset=utf-8",
        headers={
            "Content-Disposition": f'attachment; filename="{file_name}"',
        },
    )


# ── 导入任务状态查询 ─────────────────────────────────────────────────────────


@router.get("/import/{job_id}/status")
async def bulk_import_status(
    job_id: str,
):
    """查询批量导入任务的执行状态和结果。

    Args:
        job_id: 导入任务 ID（从 POST /import 返回的 job_id）。
    """
    job = _import_jobs.get(job_id)
    if not job:
        raise HTTPException(
            status_code=404,
            detail=f"导入任务 {job_id} 不存在或已过期",
        )

    return {
        "job_id": job["id"],
        "status": job["status"],
        "entity_type": job["entity_type"],
        "total_rows": job["total_rows"],
        "success_rows": job["success_rows"],
        "error_rows": job["error_rows"],
        "errors_detail": job["errors_detail"],
        "created_at": job["created_at"],
        "file_name": job["file_name"],
    }
