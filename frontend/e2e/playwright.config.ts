import { defineConfig, devices } from "@playwright/test";

/**
 * Playwright E2E 配置 — AI数智名片前端
 * 指向 Vite 开发服务器 (port 3000)
 * @see https://playwright.dev/docs/api/class-testconfig
 */
export default defineConfig({
  testDir: "./",
  testMatch: "*.spec.ts",
  fullyParallel: false,
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 2 : 0,
  workers: process.env.CI ? 1 : undefined,
  reporter: process.env.CI
    ? [["html", { outputFolder: "playwright-report" }], ["list"]]
    : "list",
  // 视觉回归快照目录（相对于 testDir）
  snapshotDir: "./__snapshots__",
  // 首次运行时自动生成基线截图（无基线不报错）
  ignoreSnapshots: false,

  use: {
    // 指向前端 dev server
    baseURL: process.env.BASE_URL || "http://localhost:3000",
    // 追踪：首次失败时记录
    trace: "on-first-retry",
    // 截图：仅失败时
    screenshot: "only-on-failure",
    // 视口：桌面 1280×720
    viewport: { width: 1280, height: 720 },
    // 操作超时
    actionTimeout: 10_000,
  },

  projects: [
    {
      name: "chromium",
      use: { ...devices["Desktop Chrome"] },
    },
  ],

  // 每个测试超时 30s
  timeout: 30_000,

  // 测试前启动 dev server
  webServer: process.env.CI
    ? {
        command: "npm run dev",
        port: 3000,
        reuseExistingServer: true,
        timeout: 60_000,
      }
    : undefined,
});
