import { describe, it, expect, beforeEach } from 'vitest';

// ============================================================
// 1. Token 存储（localStorage 封装）— 纯逻辑，无 DOM
// ============================================================

describe('Token 存储 (api/client)', () => {
  beforeEach(() => {
    localStorage.clear();
  });

  it('saveToken 应将 token 写入 localStorage', async () => {
    const { api } = await import('../api/client');
    api.saveToken('my-test-token');
    expect(localStorage.getItem('token')).toBe('my-test-token');
  });

  it('loadToken 应读取之前保存的 token', async () => {
    const { api } = await import('../api/client');
    localStorage.setItem('token', 'saved-token-value');
    expect(api.loadToken()).toBe('saved-token-value');
  });

  it('loadToken 应返回 null 当 token 不存在时', async () => {
    const { api } = await import('../api/client');
    expect(api.loadToken()).toBeNull();
  });

  it('removeToken 应清除 localStorage 中的 token', async () => {
    const { api } = await import('../api/client');
    localStorage.setItem('token', 'to-be-removed');
    api.removeToken();
    expect(localStorage.getItem('token')).toBeNull();
  });
});

// ============================================================
// 2. DesignTokens — generateTokens 纯函数
// ============================================================

describe('DesignTokens generateTokens (utils/designTokens)', () => {
  it('generateTokens 应为 landing 类型返回完整结构', async () => {
    const { generateTokens } = await import('../utils/designTokens');
    const tokens = generateTokens('landing');
    expect(tokens).toHaveProperty('colors');
    expect(tokens).toHaveProperty('typography');
    expect(tokens).toHaveProperty('spacing');
    expect(tokens).toHaveProperty('radius');
    expect(tokens).toHaveProperty('shadows');
    expect(tokens).toHaveProperty('animation');
    expect(tokens).toHaveProperty('effects');
    expect(tokens.colors.primary).toMatch(/^#/);
    expect(tokens.colors.accent).toMatch(/^#/);
    expect(tokens.colors.success).toBe('#10B981');
    expect(tokens.colors.error).toBe('#EF4444');
    expect(tokens.typography.sizes.h1).toBe('3.5rem');
    expect(tokens.typography.sizes.body).toBe('1rem');
  });

  it('generateTokens 应为不同文档类型返回不同配色', async () => {
    const { generateTokens } = await import('../utils/designTokens');
    const reportTokens = generateTokens('report');
    const socialTokens = generateTokens('social');
    // report 和 social 应有不同的 primary/accent
    expect(reportTokens.colors.primary).not.toBe(socialTokens.colors.primary);
    expect(reportTokens.colors.accent).not.toBe(socialTokens.colors.accent);
  });

  it('generateTokens 对未知类型应回退到 landing', async () => {
    const { generateTokens } = await import('../utils/designTokens');
    const landingTokens = generateTokens('landing');
    const unknownTokens = generateTokens('unknown' as any);
    expect(unknownTokens.colors.primary).toBe(landingTokens.colors.primary);
    expect(unknownTokens.colors.accent).toBe(landingTokens.colors.accent);
  });
});

// ============================================================
// 3. ApiResponse 类型格式 — 纯逻辑验证
//    确保 api.get/post 返回的对象符合 { code, message, data } 格式
// ============================================================

describe('API 响应格式验证', () => {
  it('api.get 应返回 { code, message, data } 格式', async () => {
    const { api } = await import('../api/client');
    const mockData = { id: 1, name: 'Test' };
    // 使用 vi 做 spy — 但为了保持纯逻辑，这里用简单 mock
    const originalFetch = globalThis.fetch;
    globalThis.fetch = async () =>
      new Response(JSON.stringify({ code: 200, message: 'ok', data: mockData }), {
        status: 200,
        headers: { 'Content-Type': 'application/json' },
      });

    const res = await api.get('/api/test');
    expect(res).toHaveProperty('code', 200);
    expect(res).toHaveProperty('message', 'ok');
    expect(res).toHaveProperty('data');
    expect(res.data).toEqual(mockData);

    globalThis.fetch = originalFetch;
  });
});
