"""
渲染 AI数智名片 宣传墙 → 超高分辨率 PNG（适合印刷）
"""
import asyncio
import os
from playwright.async_api import async_playwright

HTML_PATH = r"D:\AI数智名片\docs\宣传墙\宣传墙+5竖幅_深蓝科技版.html"
OUTPUT_FULL = r"D:\AI数智名片\docs\宣传墙\宣传墙+5竖幅_深蓝科技版_全画面.png"
OUTPUT_WALL = r"D:\AI数智名片\docs\宣传墙\宣传墙_主画面_深蓝科技版.png"
OUTPUT_BANNERS = r"D:\AI数智名片\docs\宣传墙\5竖幅_深蓝科技版.png"

async def main():
    file_url = "file:///" + HTML_PATH.replace("\\", "/")
    print(f"打开: {file_url}")
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        
        # 用超宽视口 + 2x scale = 高清输出
        context = await browser.new_context(
            viewport={"width": 5600, "height": 3000},
            device_scale_factor=2,
            locale="zh-CN",
        )
        
        page = await context.new_page()
        await page.goto(file_url, wait_until="networkidle", timeout=30000)
        await page.wait_for_timeout(3000)  # 等字体
        
        # 检查实际渲染尺寸
        dim = await page.evaluate("""
            () => {
                const w = document.querySelector('.wall-wrapper');
                const b = document.querySelector('.banners-row');
                const s = document.querySelector('.wall-specs');
                return {
                    wallW: w ? w.offsetWidth : 0,
                    wallH: w ? w.offsetHeight : 0,
                    bannerW: b ? b.offsetWidth : 0,
                    bannerH: b ? b.offsetHeight : 0,
                    fullH: document.body.scrollHeight
                };
            }
        """)
        print(f"主墙: {dim['wallW']}×{dim['wallH']}")
        print(f"竖幅: {dim['bannerW']}×{dim['bannerH']}")
        print(f"全页高度: {dim['fullH']}")
        
        # 1) 全页截图（整张画面）
        await page.screenshot(path=OUTPUT_FULL, full_page=True, type="png")
        fs1 = os.path.getsize(OUTPUT_FULL)
        print(f"✅ 全页印刷版: {OUTPUT_FULL} ({fs1/1024/1024:.1f}MB)")
        
        # 2) 主墙单独
        wall = await page.query_selector(".wall-wrapper")
        if wall:
            await wall.screenshot(path=OUTPUT_WALL, type="png")
            fs2 = os.path.getsize(OUTPUT_WALL)
            print(f"✅ 主墙印刷版: {OUTPUT_WALL} ({fs2/1024/1024:.1f}MB)")
        
        # 3) 竖幅单独
        banners = await page.query_selector(".banners-row")
        if banners:
            await banners.screenshot(path=OUTPUT_BANNERS, type="png")
            fs3 = os.path.getsize(OUTPUT_BANNERS)
            print(f"✅ 5竖幅印刷版: {OUTPUT_BANNERS} ({fs3/1024/1024:.1f}MB)")
        
        await browser.close()
        print("\n🎉 全部高清渲染完成！")

if __name__ == "__main__":
    asyncio.run(main())
