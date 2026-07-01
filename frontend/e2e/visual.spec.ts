/**
 * 视觉回归测试 — AI数字名片前端
 *
 * 对4个核心页面截图并与基线对比。
 * 首次运行自动生成基线截图，后续运行与基线比较。
 * 像素差异阈值: 0.01（>1%差异视为失败）
 *
 * @see https://playwright.dev/docs/api/class-page#page-screenshot
 */
import { test, expect } from "@playwright/test";

const PAGES = [
  { name: "dashboard", path: "/" },
  { name: "cards", path: "/cards/new" },
  { name: "crm", path: "/crm" },
  { name: "pricing", path: "/pricing" },
];

test.describe("视觉回归测试", () => {
  for (const { name, path } of PAGES) {
    test(`截图对比: ${name} (${path})`, async ({ page }) => {
      // 导航到目标页面
      await page.goto(path);

      // 等待页面完全加载（网络空闲 + 关键元素可见）
      await page.waitForLoadState("networkidle");

      // 等待布局渲染完成（确保骨架屏已替换为实际内容）
      await page.waitForTimeout(2000);

      // 截图并对比基线
      await expect(page).toHaveScreenshot(`${name}.png`, {
        maxDiffPixelRatio: 0.01, // 像素差异 < 1%
        fullPage: true,           // 截取完整页面（含滚动区域）
        animations: "disabled",   // 禁用动画避免 flakiness
      });
    });
  }
});
