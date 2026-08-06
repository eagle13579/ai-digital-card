import sys, os
sys.path.insert(0, 'D:/AI数智名片/backend')
os.chdir('D:/AI数智名片/backend')

import asyncio
from app.database import AsyncSessionLocal
from app.models.brochure import Brochure, Page
from sqlalchemy import select
from sqlalchemy.orm import selectinload

async def test():
    async with AsyncSessionLocal() as db:
        # 先用正确的schema尝试创建
        try:
            br = Brochure(
                user_id=56,
                title="测试名片",
                cover="",
                purpose="personal",
                pages_count=1,
            )
            db.add(br)
            await db.flush()
            
            page = Page(
                brochure_id=br.id,
                sort_order=0,
                content_type="text",
                content="测试内容",
                image_url="",
                media_url="",
                ai_summary=""
            )
            db.add(page)
            await db.commit()
            await db.refresh(br)
            
            print(f"创建成功: brochure_id={br.id}")
            print(f"pages属性类型: {type(br.pages)}")
            print(f"pages内容: {br.pages}")
            
            # 也测试publish逻辑
            from datetime import datetime
            br.status = "published"
            br.share_token = "test" + str(br.id)
            await db.commit()
            await db.refresh(br)
            print(f"发布成功: status={br.status}, share_token={br.share_token}")
            
        except Exception as e:
            import traceback
            print(f"错误: {e}")
            traceback.print_exc()
        finally:
            await db.rollback()

asyncio.run(test())
