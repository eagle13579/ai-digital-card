/**
 * E2E: 用户完整旅程全流程测试
 * 覆盖: 注册→创建名片→分享→查看→匹配→支付
 * 运行: npx playwright test tests/e2e/full_flow.spec.ts
 */
import { test, expect } from '@playwright/test';

const BASE_URL = 'http://localhost:3000';
const API_BASE = 'http://localhost:8201';

const TEST_USER = {
  phone: '13800000099',
  password: 'FullFlow123!',
  name: '完整旅程用户',
};

let authToken = '';
let shareToken = '';

test.beforeAll(async ({ request }) => {
  await request.post(`${API_BASE}/api/auth/register`, { data: TEST_USER })
    .catch(() => console.warn('用户已存在'));
  const loginRes = await request.post(`${API_BASE}/api/auth/login`, {
    data: { phone: TEST_USER.phone, password: TEST_USER.password },
  });
  expect(loginRes.status()).toBe(200);
  authToken = (await loginRes.json()).access_token;
});

async function loginPage(page: any) {
  await page.goto(BASE_URL);
  await page.evaluate((t: string) => localStorage.setItem('token', t), authToken);
  await page.reload();
  await expect(page.locator('#root')).toBeVisible({ timeout: 15000 });
  await page.waitForTimeout(1500);
}

test.describe('用户完整旅程: 注册→创建名片→分享→查看→匹配→支付', () => {
  test('1. 创建名片', async ({ request }) => {
    const res = await request.post(`${API_BASE}/api/brochures`, {
      headers: { Authorization: `Bearer ${authToken}` },
      data: {
        title: '张三测试名片',
        company: '测试公司',
        purpose: 'client',
        pages: [{ sort_order: 0, content_type: 'cover', content: JSON.stringify({ name: '张三', position: '产品经理', company: '数智科技', phone: '13800138000', email: 'zhangsan@example.com' }), image_url: '' }, { sort_order: 1, content_type: 'text', content: JSON.stringify({ title: '关于我', body: '10年互联网产品经验' }), image_url: '' }],
      },
    });
    expect(res.status()).toBe(200);
    const body = await res.json();
    expect(body.title).toBe('张三测试名片');
    expect(body.status).toBe('draft');
    expect(body.share_token).toBeTruthy();
    shareToken = body.share_token;
  });

  test('2. 发布名片', async ({ request }) => {
    const list = await (await request.get(`${API_BASE}/api/brochures`, {
      headers: { Authorization: `Bearer ${authToken}` },
    })).json();
    const brochure = list.find((b: any) => b.share_token === shareToken);
    expect(brochure).toBeTruthy();

    const pubRes = await request.post(`${API_BASE}/api/brochures/${brochure.id}/publish`, {
      headers: { Authorization: `Bearer ${authToken}` },
    });
    expect(pubRes.status()).toBe(200);
    const pubBody = await pubRes.json();
    expect(pubBody.status).toBe('published');
    if (pubBody.share_token) shareToken = pubBody.share_token;
  });

  test('3. 公开分享链接可访问', async ({ request }) => {
    const res = await request.get(`${API_BASE}/api/brochures/share/${shareToken}`);
    expect(res.status()).toBe(200);
    const body = await res.json();
    expect(body.share_token).toBe(shareToken);
    expect(body.status).toBe('published');
    expect(body.view_count).toBeGreaterThanOrEqual(1);
  });

  test('4. 仪表盘渲染', async ({ page }) => {
    await loginPage(page);
    const text = await page.locator('body').innerText();
    expect(text.includes('AI') || text.includes('名片') || text.includes('数智') || text.includes('Dashboard')).toBe(true);
  });

  test('5. 名片页渲染', async ({ page }) => {
    await loginPage(page);
    await page.goto(`${BASE_URL}/business-card`);
    await page.waitForTimeout(2000);
    await expect(page.locator('#root')).toBeVisible({ timeout: 10000 });
  });

  test('6. 公开名片页面', async ({ page }) => {
    await page.goto(`${BASE_URL}/card/${shareToken}`);
    await expect(page.locator('#root')).toBeVisible({ timeout: 15000 });
    await page.waitForTimeout(2000);
    const text = await page.locator('body').innerText();
    expect(text.includes('张三') || text.includes('数智科技')).toBe(true);
  });

  test('7. 匹配中心', async ({ page }) => {
    await loginPage(page);
    await page.goto(`${BASE_URL}/matching`);
    await page.waitForTimeout(2000);
    await expect(page.locator('#root')).toBeVisible({ timeout: 10000 });
    const text = await page.locator('body').innerText();
    expect(text.includes('匹配') || text.includes('推荐') || text.includes('Matching')).toBe(true);
  });

  test('8. 定价与支付', async ({ page }) => {
    await loginPage(page);
    await page.goto(`${BASE_URL}/pricing`);
    await page.waitForTimeout(2000);
    await expect(page.locator('#root')).toBeVisible({ timeout: 10000 });
    const text = await page.locator('body').innerText();
    expect(text.includes('定价') || text.includes('套餐') || text.includes('立即开通') || text.includes('Pricing')).toBe(true);
  });
});

test.afterAll(async ({ request }) => {
  try {
    const list = await (await request.get(`${API_BASE}/api/brochures`, {
      headers: { Authorization: `Bearer ${authToken}` },
    })).json();
    for (const b of list) {
      await request.delete(`${API_BASE}/api/brochures/${b.id}`, {
        headers: { Authorization: `Bearer ${authToken}` },
      }).catch(() => {});
    }
  } catch { /* ignore */ }
});
