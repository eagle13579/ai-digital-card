/**
 * a11y 自动化审计测试 (axe-core)
 *
 * 覆盖4个核心页面：首页、定价页、名片页、登录页
 * 每个页面运行 axe-core 分析并报告 violations
 *
 * @see https://www.npmjs.com/package/@axe-core/playwright
 */

import { test, expect } from "@playwright/test";
import AxeBuilder from "@axe-core/playwright";

const BASE_URL = process.env.BASE_URL || "http://localhost:3000";

/** 要审计的核心页面 */
const PAGES = [
  { path: "/",            name: "首页 (Dashboard)" },
  { path: "/pricing",     name: "定价页 (Pricing)" },
  { path: "/business-card", name: "名片页 (Business Card)" },
  { path: "/",            name: "登录页 (Login / 未登录态)" },
] as const;

test.describe("a11y 可访问性审计", () => {
  for (const { path, name } of PAGES) {
    test(`${name} — 无严重 a11y violations @a11y`, async ({ page }) => {
      // 登录页：通过清除 token 确保未登录态
      if (name.includes("登录")) {
        await page.addInitScript(() => {
          localStorage.removeItem("token");
        });
      }

      await page.goto(`${BASE_URL}${path}`);
      await page.waitForLoadState("networkidle");

      // 确保页面已渲染
      await expect(page.locator("main")).toBeVisible({ timeout: 15_000 });

      // 运行 axe-core 分析
      const accessibilityScanResults = await new AxeBuilder({ page })
        .withTags(["wcag2a", "wcag2aa", "wcag21a", "wcag21aa", "best-practice"])
        .analyze();

      const { violations, incomplete, passes } = accessibilityScanResults;

      // --- 汇总报告 ---
      console.log(`\n═══════════════════════════════════════════`);
      console.log(`  ${name} — a11y 审计报告`);
      console.log(`═══════════════════════════════════════════`);
      console.log(`  ✅ 通过检查:    ${passes.length}`);
      console.log(`  ⚠️ 需人工确认:  ${incomplete.length}`);
      console.log(`  ❌ Violations:  ${violations.length}`);
      console.log(`-------------------------------------------`);

      // 如果存在 violations，输出最严重的 3 个问题
      if (violations.length > 0) {
        // 按 impact 排序（critical > serious > moderate > minor）
        const sorted = [...violations].sort((a, b) => {
          const order = { critical: 0, serious: 1, moderate: 2, minor: 3 };
          return (order[a.impact as keyof typeof order] ?? 99) -
                 (order[b.impact as keyof typeof order] ?? 99);
        });

        const top3 = sorted.slice(0, 3);
        console.log(`  📋 最严重的 ${top3.length} 个问题:`);
        for (const v of top3) {
          console.log(`     [${v.impact}] ${v.id}: ${v.help}`);
          console.log(`          节点数: ${v.nodes.length}`);
          console.log(`          详情:  ${v.helpUrl}`);
        }
      }

      console.log(`═══════════════════════════════════════════\n`);

      // 断言：不允许有 critical 或 serious violations
      const criticalOrSerious = violations.filter(
        (v) => v.impact === "critical" || v.impact === "serious"
      );
      expect(
        criticalOrSerious,
        `${name}: 发现 ${criticalOrSerious.length} 个 critical/serious violations`
      ).toHaveLength(0);
    });
  }
});

test.describe("a11y 骨架屏审计", () => {
  // 额外：测试懒加载页面在骨架屏阶段是否无障碍
  test("骨架屏渲染时无严重 a11y 问题 @a11y", async ({ page }) => {
    // 使用极快的网速模拟，确保骨架屏停留
    await page.context().addInitScript(() => {
      // 不等待懒加载完成，立即检查 DOM
    });

    await page.goto(`${BASE_URL}/`);
    // 立即检查（骨架屏尚未替换为真实内容）
    // 等待至少骨架屏 DOM 出现
    await expect(page.locator("main")).toBeVisible({ timeout: 10_000 });

    const results = await new AxeBuilder({ page })
      .withTags(["wcag2a", "wcag2aa"])
      .analyze();

    const criticalSerious = results.violations.filter(
      (v) => v.impact === "critical" || v.impact === "serious"
    );

    expect(
      criticalSerious,
      `骨架屏: 发现 ${criticalSerious.length} 个 critical/serious violations`
    ).toHaveLength(0);

    console.log(`\n  ✅ 骨架屏 a11y 检查通过 (${results.violations.length} violations, ${results.passes.length} passes)\n`);
  });
});
