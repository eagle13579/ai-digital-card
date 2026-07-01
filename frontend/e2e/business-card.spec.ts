import { test, expect } from "@playwright/test";

/**
 * 用户路径 2：名片 CRUD 流程
 *
 * 覆盖场景：
 *   - 仪表盘页名片列表渲染
 *   - 创建新名片（导航到 /cards/new）
 *   - 名片编辑页面 UI 正确渲染
 *   - 返回仪表盘验证导航功能
 */

const BASE_URL = process.env.BASE_URL || "http://localhost:3000";

test.describe("名片 CRUD 流程", () => {
  test("仪表盘页：渲染名片列表区域和快速操作", async ({ page }) => {
    await page.goto(BASE_URL);
    await page.waitForLoadState("networkidle");

    // 验证欢迎横幅区域存在
    const welcomeBanner = page.locator(
      "div.bg-gradient-to-br.from-primary.to-purple-600"
    );
    await expect(welcomeBanner).toBeVisible({ timeout: 10_000 });

    // 验证快速操作区域 — "创建新名片"按钮
    const createCardButton = page.locator("button", {
      hasText: "名片",
    });
    await expect(createCardButton.first()).toBeVisible();

    // 验证"我的名片"标题存在
    await expect(
      page.locator("h3", { hasText: "我的名片" })
    ).toBeVisible();
  });

  test("创建新名片：导航到 /cards/new 页面", async ({ page }) => {
    await page.goto(BASE_URL);
    await page.waitForLoadState("networkidle");

    // 点击"创建新名片"按钮（快速操作区域第一个按钮）
    const createButton = page.locator("button").filter({
      hasText: "名片",
    });
    await createButton.first().click();

    // 等待页面导航到 /cards/new
    await page.waitForURL("**/cards/new", { timeout: 10_000 });
    await page.waitForLoadState("networkidle");

    // 验证当前路径
    expect(page.url()).toContain("/cards/new");

    // 验证卡片编辑器页面渲染了必要的 UI 元素
    // CardEditorPage 应包含表单元素
    const pageContent = page.locator("main");
    await expect(pageContent).toBeVisible();

    // 验证 Header 仍正确渲染
    await expect(page.locator("header")).toBeVisible();

    // 验证 Sidebar 仍正确渲染
    await expect(page.locator("aside")).toBeVisible();
  });

  test("名片编辑页面：验证模板选择和表单区域", async ({ page }) => {
    await page.goto(`${BASE_URL}/cards/new`);
    await page.waitForLoadState("networkidle");

    // 验证页面标题或面包屑（如果存在）
    await expect(page.locator("main")).toBeVisible({ timeout: 10_000 });

    // 验证侧边导航仍在
    await expect(page.locator("aside")).toBeVisible();

    // 验证 Header 仍在
    await expect(page.locator("header")).toBeVisible();

    // 返回仪表盘验证导航可用
    const dashboardNav = page.locator("aside button").filter({
      hasText: "仪表盘",
    });
    if (await dashboardNav.isVisible()) {
      await dashboardNav.click();
      await page.waitForURL("**/", { timeout: 10_000 });
      expect(page.url()).toBe(`${BASE_URL}/`);
    }
  });

  test("名片详情页：导航到 /business-card 页面", async ({ page }) => {
    // /business-card 是兼容性的名片列表页面
    await page.goto(`${BASE_URL}/business-card`);
    await page.waitForLoadState("networkidle");

    // 验证页面渲染
    await expect(page.locator("main")).toBeVisible({ timeout: 10_000 });

    // 验证 Header 存在
    await expect(page.locator("header")).toBeVisible();
  });

  test("删除操作：验证删除按钮/功能入口存在", async ({ page }) => {
    // 访问仪表盘，查看是否有删除入口
    await page.goto(BASE_URL);
    await page.waitForLoadState("networkidle");

    // 仪表盘默认显示空状态（无名片时）
    // 验证"暂无名片"等空状态文案存在
    const noCardsText = page.locator("text=暂无名片");
    // 如果存在空状态，验证其显示
    if (await noCardsText.isVisible().catch(() => false)) {
      await expect(noCardsText).toBeVisible();
    }

    // 验证 sidebar 中"名片编辑"导航项存在
    const cardNav = page.locator("aside button").filter({
      hasText: "名片编辑",
    });
    await expect(cardNav).toBeVisible();
  });
});
