"""Test the platform query to find the 500 error cause"""
import sys
sys.path.insert(0, 'D:\\AI数智名片\\backend')

import asyncio
from sqlalchemy import func, select, text
from app.database import engine
from app.models.platform import Platform, PlatformMember
from app.api_standards import raise_http_error, ErrorCode

# Define the success function from platform_router.py for testing
def success(data: any = None, message: str = "操作成功") -> dict:
    return {"code": 0, "message": message, "data": data}

async def test():
    async with engine.connect() as conn:
        query = (
            select(
                Platform,
                func.count(PlatformMember.id).over(partition_by=Platform.id).label("member_count"),
            )
            .outerjoin(PlatformMember, PlatformMember.platform_id == Platform.id)
            .distinct()
            .order_by(text("member_count DESC"))
            .limit(5)
        )
        try:
            result = await conn.execute(query)
            rows = result.all()
            print(f"Query success! {len(rows)} rows")
            if rows:
                print(f"First row: id={rows[0][0].id}, name={rows[0][0].name}")
        except Exception as e:
            print(f"Query error: {type(e).__name__}: {e}")

# Run in existing event loop
try:
    loop = asyncio.get_running_loop()
    loop.create_task(test())
except RuntimeError:
    asyncio.run(test())
