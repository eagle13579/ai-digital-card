"""通讯录导入 — API 路由。

端点:
  POST   /api/contacts/import       批量导入联系人
  GET    /api/contacts              获取联系人列表（分页）
  GET    /api/contacts/stats        联系人统计
  GET    /api/contacts/match-result 匹配结果
  DELETE /api/contacts/{id}         删除单条联系人
  DELETE /api/contacts              清空全部联系人
"""

from __future__ import annotations

from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.user import User
from app.routers.auth import get_current_user
from app.services.contact_service import ContactService

router = APIRouter(prefix="/api/contacts", tags=["通讯录"])


# ======================================================================
# 请求/响应模型
# ======================================================================


class ContactImportItem(BaseModel):
    """单条待导入联系人"""
    name: str = Field(..., min_length=1, max_length=64, description="联系人姓名")
    phone: str = Field(..., description="手机号")
    company: str = Field("", max_length=128, description="公司")
    position: str = Field("", max_length=128, description="职位")


class ContactImportRequest(BaseModel):
    """批量导入请求"""
    contacts: list[ContactImportItem] = Field(
        ..., min_length=1, max_length=10000, description="联系人列表",
    )
    source: str = Field("manual", pattern=r"^(wechat|csv|manual)$", description="来源")


class ContactImportResponse(BaseModel):
    """导入响应"""
    code: int = 200
    message: str = "导入完成"
    data: dict[str, Any]


class ContactListResponse(BaseModel):
    """列表响应"""
    code: int = 200
    message: str = "ok"
    data: dict[str, Any]


class ContactStatsResponse(BaseModel):
    """统计响应"""
    code: int = 200
    message: str = "ok"
    data: dict[str, Any]


class ContactMatchResponse(BaseModel):
    """匹配结果响应"""
    code: int = 200
    message: str = "匹配完成"
    data: list[dict[str, Any]]


class ContactDeleteResponse(BaseModel):
    """删除响应"""
    code: int = 200
    message: str = "联系人已删除"
    data: dict[str, Any]


class ContactClearResponse(BaseModel):
    """清空响应"""
    code: int = 200
    message: str = "已清空全部联系人"
    data: dict[str, Any]


# ======================================================================
# 端点
# ======================================================================


@router.post("/import", response_model=ContactImportResponse)
async def import_contacts(
    request: ContactImportRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """批量导入联系人（手机号 Fernet 加密存储 + SHA-256 去重）。

    支持来源: wechat / csv / manual。
    同用户同手机号自动去重，返回导入统计。
    """
    raw = [item.model_dump() for item in request.contacts]
    result = await ContactService.import_contacts(
        user_id=current_user.id,
        contacts=raw,
        source=request.source,
        db=db,
    )
    return {
        "code": 200,
        "message": "导入完成",
        "data": {
            "total": result.total,
            "success": result.success,
            "duplicates": result.duplicates,
            "failed": result.failed,
            "failures": result.failures,
        },
    }


@router.get("", response_model=ContactListResponse)
async def list_contacts(
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页条数"),
    source: Optional[str] = Query(None, pattern=r"^(wechat|csv|manual)?$", description="来源筛选"),
    keyword: Optional[str] = Query(None, min_length=1, description="姓名关键词搜索"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """查询已导入的联系人列表（分页，脱敏返回）。"""
    data = await ContactService.get_contacts(
        user_id=current_user.id,
        db=db,
        page=page,
        page_size=page_size,
        source=source,
        keyword=keyword,
    )
    return {
        "code": 200,
        "message": "ok",
        "data": data,
    }


@router.get("/stats", response_model=ContactStatsResponse)
async def contact_stats(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """联系人统计：总数、已匹配数、按来源分布。"""
    stats = await ContactService.get_contact_stats(
        user_id=current_user.id, db=db,
    )
    return {
        "code": 200,
        "message": "ok",
        "data": stats,
    }


@router.get("/match-result", response_model=ContactMatchResponse)
async def match_result(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """运行匹配引擎，通过手机号哈希查找已在平台注册的联系人。

    自动标记联系人匹配状态，仅首次调用执行实际匹配。
    """
    results = await ContactService.match_contacts(
        user_id=current_user.id, db=db,
    )
    return {
        "code": 200,
        "message": "匹配完成",
        "data": results,
    }


@router.delete("/{contact_id}", response_model=ContactDeleteResponse)
async def delete_contact(
    contact_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """软删除单条联系人。

    不会物理删除数据，仅设置 deleted_at 标记。
    """
    ok = await ContactService.delete_contact(
        contact_id=contact_id, user_id=current_user.id, db=db,
    )
    if not ok:
        raise HTTPException(status_code=404, detail="联系人不存在")
    return {
        "code": 200,
        "message": "联系人已删除",
        "data": {"contact_id": contact_id},
    }


@router.delete("", response_model=ContactClearResponse)
async def clear_contacts(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """清空当前用户的所有已导入联系人（软删除）。"""
    count = await ContactService.clear_contacts(
        user_id=current_user.id, db=db,
    )
    return {
        "code": 200,
        "message": "已清空全部联系人",
        "data": {"deleted_count": count},
    }
