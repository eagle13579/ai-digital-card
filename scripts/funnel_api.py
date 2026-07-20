"""增长看板API — 建联漏斗分析"""
from fastapi import APIRouter, Depends
from app.dependencies import get_current_user
from app.database import get_db
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter(prefix="/api/growth", tags=["growth"])

@router.get("/funnel")
async def get_funnel(user=Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    """建联漏斗: 注册→名片→匹配→连接"""
    async with db.begin():
        result = await db.execute(text("""
            SELECT
                (SELECT COUNT(*) FROM users) AS registered,
                (SELECT COUNT(*) FROM brochures WHERE is_published=true) AS card_created,
                (SELECT COUNT(DISTINCT user_id) FROM match_records) AS matched,
                (SELECT COUNT(*) FROM connections) AS connected,
                (SELECT COUNT(*) FROM users WHERE last_active_at > NOW() - INTERVAL '7 days') AS active_7d
        """))
        row = result.fetchone()
    return {
        "funnel": {
            "registered": row[0],
            "card_created": row[1],
            "matched": row[2],
            "connected": row[3],
            "active_7d": row[4]
        },
        "conversion_rates": {
            "register_to_card": f"{row[1]/max(row[0],1)*100:.1f}%",
            "card_to_match": f"{row[2]/max(row[1],1)*100:.1f}%",
            "match_to_connect": f"{row[3]/max(row[2],1)*100:.1f}%"
        }
    }
