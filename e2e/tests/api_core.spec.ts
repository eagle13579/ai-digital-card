import { test, expect } from '@playwright/test';

const BASE = process.env.BASE_URL || 'http://localhost:8002';

test.describe('核心API冒烟测试', () => {
  test('GET /health 返回200', async ({ request }) => {
    const res = await request.get(`${BASE}/health`);
    expect(res.status()).toBe(200);
  });

  test('GET /api/health 返回200', async ({ request }) => {
    const res = await request.get(`${BASE}/api/health`);
    expect(res.status()).toBe(200);
  });

  test('未认证请求 /api/v1/users 返回401', async ({ request }) => {
    const res = await request.get(`${BASE}/api/v1/users`);
    expect(res.status()).toBe(401);
  });

  test('GET /docs 在生产环境禁用', async ({ request }) => {
    // /docs 在生产环境应为 404
    const res = await request.get(`${BASE}/docs`);
    expect([404, 405]).toContain(res.status());
  });
});
