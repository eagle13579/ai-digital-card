"""
渲染 AI数智名片 宣传墙 HTML → 高分辨率 PNG
输出: 宣传墙+5竖幅_最终画面.png (与HTML同目录)
"""
import asyncio
import os
from playwright.async_api import async_playwright

HTML_PATH = r"D:\AI数智名片\docs\宣传墙\宣传墙+5竖幅_实际画面.html"
OUTPUT_PATH = r"D:\AI数智名片\docs\宣传墙\宣传墙+5竖幅_最终画面.png"
OUTPUT_PATH_MAIN = r"D:\AI数智名片\docs\宣传墙\宣传墙_主画面.png"
OUTPUT_PATH_BANNERS = r"D:\AI数智名片\docs\宣传墙\5竖幅画面.png"

async def main():
    file_url = "file:///" + HTML_PATH.replace("\\", "/").replace(":", "|").replace("|", ":")
    print(f"打开: {file_url}")
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            viewport={"width": 1920, "height": 1080},
            device_scale_factor=2,  # Retina 清晰度
            locale="zh-CN",
        )
        
        page = await context.new_page()
        await page.goto(file_url, wait_until="networkidle", timeout=30000)
        
        # 等待字体加载
        await page.wait_for_timeout(2000)
        
        # 获取全页尺寸
        dimensions = await page.evaluate("""
            () => {
                const body = document.body;
                const html = document.documentElement;
                return {
                    width: Math.max(
                        body.scrollWidth, body.offsetWidth,
                        html.scrollWidth, html.offsetWidth,
                        html.clientWidth
                    ),
                    height: Math.max(
                        body.scrollHeight, body.offsetHeight,
                        html.scrollHeight, html.offsetHeight,
                        html.clientHeight
                    )
                };
            }
        """)
        print(f"页面尺寸: {dimensions['width']}×{dimensions['height']}")
        
        # 设置viewport适应全页
        await page.set_viewport_size({
            "width": min(int(dimensions["width"]), 3840),
            "height": min(int(dimensions["height"]), 3000)
        })
        await page.wait_for_timeout(500)
        
        # 全页截图
        await page.screenshot(
            path=OUTPUT_PATH,
            full_page=True,
            type="png"
        )
        file_size = os.path.getsize(OUTPUT_PATH)
        print(f"✅ 全页截图完成: {OUTPUT_PATH}")
        print(f"   文件大小: {file_size/1024/1024:.1f}MB")
        
        # 只截主墙部分 (上面的大图)
        wall_element = await page.query_selector(".wall-wrapper")
        if wall_element:
            await wall_element.screenshot(path=OUTPUT_PATH_MAIN, type="png")
            print(f"✅ 主墙截图完成: {OUTPUT_PATH_MAIN}")
        
        # 截5竖幅部分
        banners_element = await page.query_selector(".banners-row")
        if banners_element:
            await banners_element.screenshot(path=OUTPUT_PATH_BANNERS, type="png")
            print(f"✅ 5竖幅截图完成: {OUTPUT_PATH_BANNERS}")
        
        await browser.close()
        print("\n🎉 全部渲染完成！")

if __name__ == "__main__":
    asyncio.run(main())
