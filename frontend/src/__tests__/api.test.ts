import { describe, it, expect, beforeEach, vi } from 'vitest';
import { api, type ApiResponse } from '../api/client';

// ============================================================
// API 客户端基础测试
// ============================================================

const MOCK_TOKEN = 'test-jwt-token-12345';

beforeEach(() => {
  // 每次测试前清除 localStorage
  localStorage.clear();
  // 重置所有 mock
  vi.restoreAllMocks();
});

describe('api.get()', () => {
  it('应返回标准的 ApiResponse 格式（含 code / message / data）', async () => {
    // 模拟 fetch 返回成功响应
    const mockData = { id: 1, name: '测试名片' };
    vi.spyOn(globalThis, 'fetch').mockResolvedValueOnce(
      new Response(JSON.stringify({ code: 200, message: 'ok', data: mockData }), {
        status: 200,
        headers: { 'Content-Type': 'application/json' },
      }),
    );

    const res: ApiResponse<typeof mockData> = await api.get('/api/brochures/1');

    expect(res).toHaveProperty('code', 200);
    expect(res).toHaveProperty('message', 'ok');
    expect(res).toHaveProperty('data');
    expect(res.data).toEqual(mockData);
  });

  it('应正确处理 HTTP 错误状态', async () => {
    vi.spyOn(globalThis, 'fetch').mockResolvedValueOnce(
      new Response(null, { status: 404, statusText: 'Not Found' }),
    );

    const res = await api.get('/api/brochures/999');

    expect(res.code).toBe(404);
    expect(res.message).toContain('404');
  });
});

describe('api.post()', () => {
  it('应发送 Content-Type: application/json 和 JSON 序列化的请求体', async () => {
    vi.spyOn(globalThis, 'fetch').mockResolvedValueOnce(
      new Response(JSON.stringify({ code: 200, message: 'ok', data: null }), {
        status: 200,
        headers: { 'Content-Type': 'application/json' },
      }),
    );

    const body = { phone: '13800138000', password: 'test123' };
    await api.post('/api/auth/login', body);

    // 验证 fetch 被正确调用
    expect(fetch).toHaveBeenCalledTimes(1);
    const [url, options] = (fetch as ReturnType<typeof vi.fn>).mock.calls[0];

    expect(url).toBe('/api/auth/login');
    expect(options.method).toBe('POST');
    expect(options.headers).toHaveProperty('Content-Type', 'application/json');
    expect(options.body).toBe(JSON.stringify(body));
  });

  it('应携带 Authorization header（当 token 存在时）', async () => {
    // 先设置 token
    api.saveToken(MOCK_TOKEN);

    vi.spyOn(globalThis, 'fetch').mockResolvedValueOnce(
      new Response(JSON.stringify({ code: 200, message: 'ok', data: null }), {
        status: 200,
        headers: { 'Content-Type': 'application/json' },
      }),
    );

    await api.post('/api/auth/refresh', {});

    const [, options] = (fetch as ReturnType<typeof vi.fn>).mock.calls[0];
    expect(options.headers).toHaveProperty('Authorization', `Bearer ${MOCK_TOKEN}`);
  });

  it('不应携带 Authorization header（当 token 不存在时）', async () => {
    vi.spyOn(globalThis, 'fetch').mockResolvedValueOnce(
      new Response(JSON.stringify({ code: 200, message: 'ok', data: null }), {
        status: 200,
        headers: { 'Content-Type': 'application/json' },
      }),
    );

    await api.post('/api/auth/refresh', {});

    const [, options] = (fetch as ReturnType<typeof vi.fn>).mock.calls[0];
    expect(options.headers).not.toHaveProperty('Authorization');
  });
});
