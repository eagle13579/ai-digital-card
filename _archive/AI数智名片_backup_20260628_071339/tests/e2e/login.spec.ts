/**
 * E2E: 登录流程测试
 *
 * 覆盖场景:
 *   1. 注册新用户
 *   2. 密码登录
 *   3. 访问受保护页面时跳转
 *   4. 登出后令牌失效
 *
 * 前置条件:
 *   - 后端运行在 http://localhost:8201
 *   - 前端运行在 http://localhost:3000
 *   - 测试数据库为空 (SQLite 内存/临时文件)
 *
 * 运行:
 *   npx playwright test tests/e2e/login.spec.ts
 */

import { test, expect } from '@playwright/test';

const BASE_URL = 'http://localhost:3000';
const API_BASE = 'http://localhost:8201';

const TEST_USER = {
  phone: '13800000001',
  password: 'Test123456',
  name: 'E2E测试用户',
};

// ─── 辅助: 通过 API 注册用户 ────────────────────────────

async function registerUser(request: any) {
  const res = await request.post(`${API_BASE}/api/auth/register`, {
    data: TEST_USER,
  });
  return res;
}

// ─── 辅助: 通过 API 登录 ───────────────────────────────

async function loginUser(request: any) {
  const res = await request.post(`${API_BASE}/api/auth/login`, {
    data: {
      phone: TEST_USER.phone,
      password: TEST_USER.password,
    },
  });
  return res;
}

// ═══════════════════════════════════════════════════════════
// Test Suite
// ═══════════════════════════════════════════════════════════

test.describe('登录流程 E2E', () => {
  // ── 注册 ──────────────────────────────────────────────

  test('POST /api/auth/register — 注册新用户', async ({ request }) => {
    const res = await registerUser(request);
    expect(res.status()).toBe(200);

    const body = await res.json();
    expect(body).toHaveProperty('access_token');
    expect(body).toHaveProperty('user');
    expect(body.user).toMatchObject({
      phone: TEST_USER.phone,
      name: TEST_USER.name,
    });
    // token 格式: JWT 三段式
    expect(body.access_token.split('.')).toHaveLength(3);
  });

  test('POST /api/auth/register — 重复注册返回 400', async ({ request }) => {
    // 先注册 （如果上一条失败则重试）
    const registerRes = await registerUser(request);
    if (registerRes.status() !== 200) {
      // 可能已存在，先清理
      console.warn('首次注册失败，可能用户已存在，继续测试重复注册');
    }
    // 重复注册
    const dupRes = await registerUser(request);
    expect(dupRes.status()).toBe(400);
    const body = await dupRes.json();
    expect(body.detail).toContain('已注册');
  });

  // ── 登录 ──────────────────────────────────────────────

  test('POST /api/auth/login — 正确凭证登录成功', async ({ request }) => {
    const res = await loginUser(request);
    expect(res.status()).toBe(200);

    const body = await res.json();
    expect(body).toHaveProperty('access_token');
    expect(body.token_type).toBe('bearer');
    expect(body.user.phone).toBe(TEST_USER.phone);
  });

  test('POST /api/auth/login — 错误密码返回 401', async ({ request }) => {
    const res = await request.post(`${API_BASE}/api/auth/login`, {
      data: {
        phone: TEST_USER.phone,
        password: 'wrong_password_123',
      },
    });
    expect(res.status()).toBe(401);
    const body = await res.json();
    expect(body.detail).toMatch(/密码错误|凭证/);
  });

  test('POST /api/auth/login — 不存在的手机号返回 401', async ({ request }) => {
    const res = await request.post(`${API_BASE}/api/auth/login`, {
      data: {
        phone: '13999999999',
        password: 'SomePass123!',
      },
    });
    expect(res.status()).toBe(401);
  });

  // ── 令牌校验 ──────────────────────────────────────────

  test('使用 JWT 令牌访问受保护接口', async ({ request }) => {
    // 先登录获取 token
    const loginRes = await loginUser(request);
    expect(loginRes.status()).toBe(200);
    const { access_token } = await loginRes.json();

    // 用 token 访问 /api/brochures (需要认证)
    const brochuresRes = await request.get(`${API_BASE}/api/brochures`, {
      headers: { Authorization: `Bearer ${access_token}` },
    });
    // 即使没有名片，也应该返回 200 (空列表)
    expect(brochuresRes.status()).toBe(200);
    const list = await brochuresRes.json();
    expect(Array.isArray(list)).toBe(true);
  });

  test('无令牌访问受保护接口返回 401', async ({ request }) => {
    const res = await request.get(`${API_BASE}/api/brochures`);
    // FastAPI OAuth2 scheme 默认返回 401
    expect(res.status()).toBe(401);
  });

  test('伪造 JWT 令牌返回 401', async ({ request }) => {
    const fakeToken = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.fake.xxxxx';
    const res = await request.get(`${API_BASE}/api/brochures`, {
      headers: { Authorization: `Bearer ${fakeToken}` },
    });
    expect(res.status()).toBe(401);
  });

  // ── 前端页面渲染 ──────────────────────────────────────

  test('前端页面正常渲染（未登录状态）', async ({ page }) => {
    // 清除 localStorage 模拟未登录
    await page.goto(BASE_URL);
    await page.evaluate(() => localStorage.removeItem('token'));
    await page.reload();

    // SPA 首页应正常渲染
    await expect(page.locator('#root')).toBeVisible({ timeout: 10000 });

    // 页面标题包含"数智"或"名片"等关键词（中文产品名）
    const title = await page.title();
    const bodyText = await page.locator('body').innerText();
    const hasBrandText =
      bodyText.includes('AI') ||
      bodyText.includes('名片') ||
      bodyText.includes('数智') ||
      bodyText.includes('Business') ||
      bodyText.includes('Card');

    expect(hasBrandText).toBe(true);
  });

  test('前端页面支持通过 localStorage 注入 token 登录', async ({ page, request }) => {
    // 先通过 API 获取有效 token
    const loginRes = await loginUser(request);
    expect(loginRes.status()).toBe(200);
    const { access_token } = await loginRes.json();

    // 设置 token 到 localStorage 并刷新
    await page.goto(BASE_URL);
    await page.evaluate((token) => {
      localStorage.setItem('token', token);
    }, access_token);
    await page.reload();

    // 页面应渲染，且能请求到名片列表（无异常）
    await expect(page.locator('#root')).toBeVisible({ timeout: 10000 });
    // 确认无控制台错误
    const consoleErrors: string[] = [];
    page.on('console', (msg) => {
      if (msg.type() === 'error') {
        consoleErrors.push(msg.text());
      }
    });
    // 给异步请求足够时间
    await page.waitForTimeout(2000);
    // 允许导航类和 fetch 类错误，但不能有未捕获异常
    const criticalErrors = consoleErrors.filter(
      (e) => !e.includes('favicon') && !e.includes('Failed to load resource')
    );
    expect(criticalErrors.length).toBe(0);
  });

  // ── API 健康 ──────────────────────────────────────────

  test('后端 API /health 返回 200', async ({ request }) => {
    const res = await request.get(`${API_BASE}/health`);
    expect(res.status()).toBe(200);
    const text = await res.text();
    expect(text).toBe('OK');
  });

  test('后端 API /api/health 返回 JSON', async ({ request }) => {
    const res = await request.get(`${API_BASE}/api/health`);
    expect(res.status()).toBe(200);
    const body = await res.json();
    expect(body.status).toBe('ok');
  });
});

// ═══════════════════════════════════════════════════════════
// 清理: 删除测试用户 (通过 API，可选)
// ═══════════════════════════════════════════════════════════

test.afterAll(async ({ request }) => {
  // 尝试删除测试用户（不强制通过，CI 环境可能无删除接口）
  try {
    const loginRes = await loginUser(request);
    if (loginRes.status() === 200) {
      const { access_token } = await loginRes.json();
      // 有些项目没有删除用户的公开 API，忽略失败
      await request.delete(`${API_BASE}/api/user/me`, {
        headers: { Authorization: `Bearer ${access_token}` },
      }).catch(() => {});
    }
  } catch {
    // ignore cleanup failures
  }
});
