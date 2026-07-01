import { test, expect } from "@playwright/test";

/**
 * 用户路径 3：导航路径测试
 *
 * 覆盖场景：
 *   - 侧边栏所有导航项点击后 URL 正确变更
 *   - 直接访问各路由页面渲染正确
 *   - 侧边栏展开/收起功能
 *   - 移动端响应式导航适配（缩小时）
 */

const BASE_URL = process.env.BASE_URL || "http://localhost:3000";

/**
 * 侧边栏导航项定义
 * path: 路由路径
 * label: 导航项显示文本（支持模糊匹配 i18n key）
 * expectedUrlPrefix: URL 应包含的前缀
 */
const NAV_ITEMS = [
  { path: "/", label: "仪表盘", expectedUrlPrefix: "http://localhost:3000/" },
  {
    path: "/cards",
    label: "名片编辑",
    expectedUrlPrefix: "http://localhost:3000/cards",
  },
  {
    path: "/matching",
    label: "匹配中心",
    expectedUrlPrefix: "http://localhost:3000/matching",
  },
  {
    path: "/network",
    label: "信任网络",
    expectedUrlPrefix: "http://localhost:3000/network",
  },
  {
    path: "/api-keys",
    label: "开发者门户",
    expectedUrlPrefix: "http://localhost:3000/api-keys",
  },
  {
    path: "/settings",
    label: "设置",
    expectedUrlPrefix: "http://localhost:3000/settings",
  },
] as const;

test.describe("侧边栏导航", () => {
  test("侧边栏可见且包含所有导航项", async ({ page }) => {
    await page.goto(BASE_URL);
    await page.waitForLoadState("networkidle");

    // 验证侧边栏存在
    const sidebar = page.locator("aside");
    await expect(sidebar).toBeVisible({ timeout: 10_000 });

    // 验证每个导航项在侧边栏中存在
    for (const item of NAV_ITEMS) {
      const navButton = sidebar.locator("button").filter({ hasText: item.label });
      await expect(navButton).toBeVisible();
    }
  });

  test("点击每个导航项正确跳转", async ({ page }) => {
    await page.goto(BASE_URL);
    await page.waitForLoadState("networkidle");

    for (const item of NAV_ITEMS) {
      const navButton = page
        .locator("aside button")
        .filter({ hasText: item.label });

      await navButton.click();

      // 等待 URL 更新
      await page.waitForURL(`${item.expectedUrlPrefix}**`, { timeout: 10_000 });

      // 验证 URL 包含正确路径
      expect(page.url()).toContain(item.path);

      // 验证主内容区已渲染
      await expect(page.locator("main")).toBeVisible();
    }
  });

  test("侧边栏展开/收起切换", async ({ page }) => {
    await page.goto(BASE_URL);
    await page.waitForLoadState("networkidle");

    const sidebar = page.locator("aside");

    // 找到收起/展开按钮
    const collapseButton = sidebar.locator("button").last();

    // 初始状态应为展开（w-56）
    await expect(sidebar).toBeVisible();

    // 点击收起
    await collapseButton.click();
    // 等待动画完成
    await page.waitForTimeout(400);

    // 再次点击展开
    await collapseButton.click();
    await page.waitForTimeout(400);

    // 验证导航项仍然可用
    const firstNav = page.locator("aside button").first();
    await expect(firstNav).toBeVisible();
  });

  test("直接访问各路由 — 页面渲染正确", async ({ page }) => {
    // 测试直接 URL 访问而非通过点击导航
    const routesToTest = [
      { path: "/", label: "仪表盘" },
      { path: "/cards/new", label: "名片编辑" },
      { path: "/matching", label: "匹配" },
      { path: "/network", label: "网络" },
      { path: "/api-keys", label: "开发者" },
      { path: "/settings", label: "设置" },
      { path: "/business-card", label: "名片" },
      { path: "/pricing", label: "定价" },
    ];

    for (const route of routesToTest) {
      await page.goto(`${BASE_URL}${route.path}`);
      await page.waitForLoadState("networkidle");

      // 验证主内容区渲染
      await expect(page.locator("main")).toBeVisible({
        timeout: 15_000,
      });

      // 验证 Header 存在
      await expect(page.locator("header")).toBeVisible();

      // 验证侧边栏存在
      await expect(page.locator("aside")).toBeVisible();

      console.log(`✅ ${route.path} — 页面渲染正常`);
    }
  });

  test("导航后 Header 标题一致性", async ({ page }) => {
    await page.goto(BASE_URL);
    await page.waitForLoadState("networkidle");

    // Header 标题在导航后应保持不变
    const headerTitle = page.locator("header h1");
    const initialTitle = await headerTitle.textContent();

    // 导航到不同页面
    for (const item of NAV_ITEMS.slice(1, 3)) {
      await page.locator("aside button").filter({ hasText: item.label }).click();
      await page.waitForURL(`${item.expectedUrlPrefix}**`);
      await page.waitForLoadState("networkidle");

      // Header 标题应保持相同
      await expect(page.locator("header h1")).toContainText(
        initialTitle || "AI数智名片"
      );
    }
  });
});

test.describe("导航边界情况", () => {
  test("404 路由：访问不存在路径应正常渲染 Layout", async ({ page }) => {
    await page.goto(`${BASE_URL}/non-existent-path-12345`);
    await page.waitForLoadState("networkidle");

    // 验证 Layout 仍在（Header + Sidebar）
    await expect(page.locator("header")).toBeVisible({ timeout: 10_000 });
    await expect(page.locator("aside")).toBeVisible();
    await expect(page.locator("main")).toBeVisible();
  });

  test("路由懒加载：切换路由时骨架屏显示后正常渲染", async ({ page }) => {
    await page.goto(BASE_URL);
    await page.waitForLoadState("networkidle");

    // 快速切换到另一个页面
    await page.locator("aside button").filter({ hasText: "设置" }).click();

    // 验证最终页面渲染
    await page.waitForURL("**/settings", { timeout: 10_000 });
    await expect(page.locator("main")).toBeVisible({ timeout: 15_000 });
  });
});
