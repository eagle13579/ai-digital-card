"""名片分享路由 — QR 码图片 & NFC 配置"""

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import Response, JSONResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.brochure import Brochure
from app.services.share_service import generate_qr_code, generate_nfc_ndef_record

router = APIRouter(prefix="/share", tags=["分享"])


@router.get("/qr/{share_token}")
async def get_share_qr(share_token: str, db: AsyncSession = Depends(get_db)):
    """
    获取名片分享 QR 码图片 (PNG)。
    
    验证 share_token 有效后返回 290x290 左右 PNG 图片。
    """
    # 验证 token 是否存在
    result = await db.execute(
        select(Brochure).where(
            Brochure.share_token == share_token,
            Brochure.status.in_(["published"]),
        )
    )
    brochure = result.scalars().first()
    if brochure is None:
        raise HTTPException(status_code=404, detail="名片不存在或链接已失效")

    try:
        png_bytes = generate_qr_code(share_token, box_size=10, border=2)
        return Response(content=png_bytes, media_type="image/png")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"QR 码生成失败: {str(e)}")


@router.get("/nfc/{share_token}")
async def get_share_nfc(share_token: str, db: AsyncSession = Depends(get_db)):
    """
    获取名片 NFC NDEF 配置 (JSON)。
    
    返回 JSON 供移动客户端写入或预览 NFC 标签内容。
    """
    # 验证 token 是否存在
    result = await db.execute(
        select(Brochure).where(
            Brochure.share_token == share_token,
            Brochure.status.in_(["published"]),
        )
    )
    brochure = result.scalars().first()
    if brochure is None:
        raise HTTPException(status_code=404, detail="名片不存在或链接已失效")

    try:
        ndef_config = generate_nfc_ndef_record(share_token)
        return JSONResponse(content=ndef_config)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"NFC 配置生成失败: {str(e)}")
