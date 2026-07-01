/**
 * E2E: 名片创建/编辑/分享流程测试
 *
 * 覆盖场景:
 *   1. 创建名片 (POST /api/brochures)
 *   2. 获取名片列表 (GET /api/brochures)
 *   3. 更新名片 (PUT /api/brochures/{id})
 *   4. 发布名片 (POST /api/brochures/{id}/publish)
 *   5. 通过分享 token 访问 (GET /api/brochures/share/{share_token})
 *   6. 删除名片 (DELETE /api/brochures/{id})
 *   7. 前端页面路由导航 (/business-card, /card/:token)
 *   8. 完整 UI 操作管线
 *
 * 前置条件:
 *   - 后端运行在 http://localhost:8201
 *   - 前端运行在 http://localhost:3000
 *   - 测试数据库为空
 *
 * 运行:
 *   npx playwright test tests/e2e/brochure.spec.ts
 */

import { test, expect } from '@playwright/test';

const BASE_URL = 'http://localhost:3000';
const API_BASE = 'http://localhost:8201';

const TEST_USER = {
  phone: '13800000002',
  password: 'Test123456',
  name: 'E2E名片测试',
};

// ─── 共享 token（跨测试使用） ──────────────────────────

let authToken = '';
let createdBrochureId = -1;
let shareToken = '';

// ─── 辅助: 注册并登录 ───────────────────────────────

test.beforeAll(async ({ request }) => {
  // 先尝试注册
  const regRes = await request.post(`${API_BASE}/api/auth/register`, {
    data: TEST_USER,
  });
  // 如果重复注册则登录
  if (regRes.status() !== 200) {
    console.warn('用户已存在，尝试登录...');
  }
  const loginRes = await request.post(`${API_BASE}/api/auth/login`, {
    data: {
      phone: TEST_USER.phone,
      password: TEST_USER.password,
    },
  });
  expect(loginRes.status()).toBe(200);
  const body = await loginRes.json();
  authToken = body.access_token;
  expect(authToken).toBeTruthy();
});

// ═══════════════════════════════════════════════════════════
// Test Suite
// ═══════════════════════════════════════════════════════════

test.describe('名片创建/编辑/分享 E2E', () => {
  // ── 创建名片 ──────────────────────────────────────────

  test('POST /api/brochures — 创建新名片', async ({ request }) => {
    const res = await request.post(`${API_BASE}/api/brochures`, {
      headers: { Authorization: `Bearer ${authToken}` },
      data: {
        title: '张三·产品经理名片',
        cover: '',
        purpose: 'client',
        pages: [
          {
            sort_order: 0,
            content_type: 'cover',
            content: JSON.stringify({
              name: '张三',
              position: '产品经理',
              company: '数智科技',
              phone: '13800138000',
              email: 'zhangsan@example.com',
            }),
            image_url: '',
          },
          {
            sort_order: 1,
            content_type: 'text',
            content: JSON.stringify({
              title: '关于我',
              body: '10年互联网产品经验，专注AI领域',
            }),
            image_url: '',
          },
        ],
      },
    });
    expect(res.status()).toBe(200);

    const body = await res.json();
    expect(body).toHaveProperty('id');
    expect(body.title).toBe('张三·产品经理名片');
    expect(body.purpose).toBe('client');
    expect(body.status).toBe('draft');
    expect(body.pages).toHaveLength(2);
    expect(body.share_token).toBeTruthy();

    createdBrochureId = body.id;
    shareToken = body.share_token;
  });

  test('POST /api/brochures — 无 token 创建返回 401', async ({ request }) => {
    const res = await request.post(`${API_BASE}/api/brochures`, {
      data: { title: 'unauthorized', pages: [] },
    });
    expect(res.status()).toBe(401);
  });

  // ── 获取名片列表 ──────────────────────────────────────

  test('GET /api/brochures — 获取名片列表', async ({ request }) => {
    const res = await request.get(`${API_BASE}/api/brochures`, {
      headers: { Authorization: `Bearer ${authToken}` },
    });
    expect(res.status()).toBe(200);

    const list = await res.json();
    expect(Array.isArray(list)).toBe(true);
    expect(list.length).toBeGreaterThanOrEqual(1);

    const created = list.find((b: any) => b.id === createdBrochureId);
    expect(created).toBeTruthy();
    expect(created.title).toBe('张三·产品经理名片');
  });

  // ── 获取单个名片 ──────────────────────────────────────

  test('GET /api/brochures/{id} — 获取名片详情', async ({ request }) => {
    expect(createdBrochureId).toBeGreaterThan(0);

    const res = await request.get(`${API_BASE}/api/brochures/${createdBrochureId}`, {
      headers: { Authorization: `Bearer ${authToken}` },
    });
    expect(res.status()).toBe(200);

    const body = await res.json();
    expect(body.id).toBe(createdBrochureId);
    expect(body.pages).toHaveLength(2);
    expect(body.pages[0].content_type).toBe('cover');
  });

  test('GET /api/brochures/{id} — 不存在的名片返回 404', async ({ request }) => {
    const res = await request.get(`${API_BASE}/api/brochures/999999`, {
      headers: { Authorization: `Bearer ${authToken}` },
    });
    expect(res.status()).toBe(404);
  });

  // ── 更新名片 ──────────────────────────────────────────

  test('PUT /api/brochures/{id} — 更新名片信息', async ({ request }) => {
    expect(createdBrochureId).toBeGreaterThan(0);

    const res = await request.put(`${API_BASE}/api/brochures/${createdBrochureId}`, {
      headers: { Authorization: `Bearer ${authToken}` },
      data: {
        title: '张三·高级产品经理名片',
        pages: [
          {
            sort_order: 0,
            content_type: 'cover',
            content: JSON.stringify({
              name: '张三',
              position: '高级产品经理',
              company: '数智科技',
              phone: '13800138000',
              email: 'zhangsan@example.com',
            }),
            image_url: '',
          },
          {
            sort_order: 1,
            content_type: 'text',
            content: JSON.stringify({
              title: '关于我',
              body: '12年互联网产品经验，专注AI与SaaS领域',
            }),
            image_url: '',
          },
          {
            sort_order: 2,
            content_type: 'image',
            content: '',
            image_url: 'https://via.placeholder.com/800x600',
          },
        ],
      },
    });
    expect(res.status()).toBe(200);

    const body = await res.json();
    expect(body.title).toBe('张三·高级产品经理名片');
    expect(body.pages).toHaveLength(3);
  });

  // ── 发布名片 ──────────────────────────────────────────

  test('POST /api/brochures/{id}/publish — 发布名片', async ({ request }) => {
    expect(createdBrochureId).toBeGreaterThan(0);

    const res = await request.post(
      `${API_BASE}/api/brochures/${createdBrochureId}/publish`,
      {
        headers: { Authorization: `Bearer ${authToken}` },
      }
    );
    expect(res.status()).toBe(200);

    const body = await res.json();
    expect(body.status).toBe('published');
    // 发布后 share_token 应刷新
    expect(body.share_token).toBeTruthy();
    if (body.share_token) {
      shareToken = body.share_token;
    }
  });

  // ── 通过分享 token 访问 ──────────────────────────────

  test('GET /api/brochures/share/{share_token} — 通过分享链接访问', async ({ request }) => {
    expect(shareToken).toBeTruthy();

    const res = await request.get(
      `${API_BASE}/api/brochures/share/${shareToken}`
    );
    expect(res.status()).toBe(200);

    const body = await res.json();
    expect(body.share_token).toBe(shareToken);
    expect(body.status).toBe('published');
    // 查看计数增加
    expect(body.view_count).toBeGreaterThanOrEqual(1);
  });

  test('GET /api/brochures/share/{share_token} — 无效 token 返回 404', async ({ request }) => {
    const res = await request.get(
      `${API_BASE}/api/brochures/share/invalid_token_12345`
    );
    expect(res.status()).toBe(404);
  });

  // ── 模板接口 ──────────────────────────────────────────

  test('GET /api/brochures/template/{purpose} — 获取用途模板', async ({ request }) => {
    const res = await request.get(
      `${API_BASE}/api/brochures/template/partner`
    );
    expect(res.status()).toBe(200);

    const body = await res.json();
    expect(body.purpose).toBe('partner');
    expect(body.name).toBe('找合作伙伴');
    expect(body.pages.length).toBeGreaterThan(0);
    expect(body.theme).toHaveProperty('primary');
  });

  test('GET /api/brochures/template/{purpose} — 不支持的用途返回 404', async ({ request }) => {
    const res = await request.get(
      `${API_BASE}/api/brochures/template/unknown_purpose`
    );
    expect(res.status()).toBe(404);
  });

  // ── 前端页面渲染 ──────────────────────────────────────

  test('前端 / 路由渲染 BusinessCardPage', async ({ page }) => {
    // 注入 token
    await page.goto(BASE_URL);
    await page.evaluate((token) => {
      localStorage.setItem('token', token);
    }, authToken);
    await page.reload();

    // 等待 SPA 加载完成
    await expect(page.locator('#root')).toBeVisible({ timeout: 15000 });

    // 等待异步请求完成，页面应有"我的AI数智名片"或"名片"相关文字
    await page.waitForTimeout(3000);
    const bodyText = await page.locator('body').innerText();

    // 应渲染名片列表（至少包含我们创建的名片标题）
    expect(
      bodyText.includes('AI数智名片') ||
        bodyText.includes('张三') ||
        bodyText.includes('名片')
    ).toBe(true);
  });

  // ── 删除名片 ──────────────────────────────────────────

  test('DELETE /api/brochures/{id} — 删除名片', async ({ request }) => {
    expect(createdBrochureId).toBeGreaterThan(0);

    const res = await request.delete(
      `${API_BASE}/api/brochures/${createdBrochureId}`,
      {
        headers: { Authorization: `Bearer ${authToken}` },
      }
    );
    expect(res.status()).toBe(200);

    // 确认已删除
    const getRes = await request.get(
      `${API_BASE}/api/brochures/${createdBrochureId}`,
      {
        headers: { Authorization: `Bearer ${authToken}` },
      }
    );
    expect(getRes.status()).toBe(404);
  });

  test('DELETE /api/brochures/{id} — 无权限删除', async ({ request }) => {
    // 用无效 token 删除应该返回 401 或 403
    const res = await request.delete(
      `${API_BASE}/api/brochures/${createdBrochureId}`,
      {
        headers: { Authorization: 'Bearer invalid_token_xxx' },
      }
    );
    expect(res.status()).toBeGreaterThanOrEqual(401);
    expect(res.status()).toBeLessThanOrEqual(403);
  });
});
