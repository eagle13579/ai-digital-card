/**
 * k6 压力测试 — AI 数字名片 API
 *
 * 场景: 100 并发用户 × 60 秒
 * 测试接口: 健康检查、注册/登录、名片 CRUD、分享访问
 *
 * 运行:
 *   k6 run tests/stress/k6-script.js
 *
 * 前置条件:
 *   - 后端运行在 http://localhost:8201
 *   - 测试数据库已初始化（SQLite 即可）
 *
 * 环境变量:
 *   API_BASE       - 后端地址 (默认 http://localhost:8201)
 *   VUS            - 虚拟用户数 (默认 100)
 *   DURATION       - 持续时间 (默认 60s)
 */

import http from 'k6/http';
import { check, sleep, group } from 'k6';
import { Rate, Trend, Counter } from 'k6/metrics';

// ─── 自定义指标 ──────────────────────────────────────

const errorRate = new Rate('errors');
const loginDuration = new Trend('login_duration');
const brochureCreateDuration = new Trend('brochure_create_duration');
const shareAccessDuration = new Trend('share_access_duration');
const healthCheckDuration = new Trend('health_check_duration');

// ─── 配置 ──────────────────────────────────────────────

const API_BASE = __ENV.API_BASE || 'http://localhost:8201';
const VUS = parseInt(__ENV.VUS || '100', 10);
const DURATION = __ENV.DURATION || '60s';

export const options = {
  stages: [
    // 渐变启动: 10秒内从 0 到目标并发
    { target: VUS, duration: '10s' },
    // 稳定期: 保持目标并发
    { target: VUS, duration: DURATION },
    // 渐降: 10秒内归零
    { target: 0, duration: '10s' },
  ],
  thresholds: {
    http_req_duration: ['p(95)<2000'], // 95% 请求应在 2 秒内
    http_req_failed: ['rate<0.05'],    // 错误率 < 5%
    errors: ['rate<0.1'],              // 自定义错误率 < 10%
  },
};

// ─── 测试用户池 ──────────────────────────────────────

const USER_POOL_SIZE = 50;
const userPool = Array.from({ length: USER_POOL_SIZE }, (_, i) => ({
  phone: `138${String(100000000 + i).slice(0, 8)}`,
  password: 'StressTest123!',
  name: `压力测试用户_${i}`,
}));

// ─── 全局缓存 ────────────────────────────────────────

// 每个 VU 独立缓存，不共享（避免竞态）
const vuCache = new Map();

// ============================================================
// 设置阶段: 初始化测试用户
// ============================================================

export function setup() {
  // 预注册测试用户，避免压力测试阶段注册冲突
  const preRegistered = [];
  for (const user of userPool.slice(0, 10)) {
    try {
      const res = http.post(`${API_BASE}/api/auth/register`, JSON.stringify(user), {
        headers: { 'Content-Type': 'application/json' },
      });
      if (res.status === 200) {
        const body = JSON.parse(res.body);
        preRegistered.push({ ...user, token: body.access_token });
      }
    } catch {
      // 忽略预注册失败（可能已存在）
    }
  }
  return { preRegistered };
}

// ============================================================
// 主测试函数 (每个 VU 反复执行)
// ============================================================

export default function (data) {
  const vuId = __VU; // k6 内置 VU 编号 (1-based)

  // 限制频率: 每个迭代之间稍作停顿
  sleep(Math.random() * 2 + 0.5);

  group('健康检查', function () {
    const res = http.get(`${API_BASE}/health`);
    const ok = check(res, {
      'health status is 200': (r) => r.status === 200,
    });
    errorRate.add(!ok);
    healthCheckDuration.add(res.timings.duration);
  });

  group('认证流程', function () {
    // 从用户池中选取一个用户
    const userIndex = vuId % USER_POOL_SIZE;
    const user = userPool[userIndex];

    // ── 注册（部分用户） ──
    if (vuId % 3 === 0) {
      const regRes = http.post(`${API_BASE}/api/auth/register`, JSON.stringify(user), {
        headers: { 'Content-Type': 'application/json' },
      });
      // 200=新注册, 400=已存在（正常）
      const ok = check(regRes, {
        'register OK or already exists': (r) => r.status === 200 || r.status === 400,
      });
      errorRate.add(!ok);
      if (regRes.status === 200) {
        const body = JSON.parse(regRes.body);
        vuCache.set('token', body.access_token);
      }
    }

    // ── 登录 ──
    const loginStart = Date.now();
    const loginRes = http.post(`${API_BASE}/api/auth/login`, JSON.stringify({
      phone: user.phone,
      password: user.password,
    }), {
      headers: { 'Content-Type': 'application/json' },
    });
    loginDuration.add(Date.now() - loginStart);

    const loginOk = check(loginRes, {
      'login status is 200': (r) => r.status === 200,
      'login has access_token': (r) => {
        try {
          return JSON.parse(r.body).access_token !== undefined;
        } catch { return false; }
      },
    });
    errorRate.add(!loginOk);

    let token = '';
    if (loginOk) {
      const body = JSON.parse(loginRes.body);
      token = body.access_token;
      vuCache.set('token', token);
    } else {
      // 如果登录失败，返回（避免后续接口雪崩）
      return;
    }

    const authHeaders = {
      'Content-Type': 'application/json',
      Authorization: `Bearer ${token}`,
    };

    // ── 创建名片 ──
    group('名片创建', function () {
      const createStart = Date.now();
      const createRes = http.post(`${API_BASE}/api/brochures`, JSON.stringify({
        title: `压力测试名片_${vuId}_${Date.now()}`,
        purpose: 'partner',
        pages: [
          {
            sort_order: 0,
            content_type: 'cover',
            content: JSON.stringify({
              name: user.name,
              position: '测试工程师',
              company: '压力测试公司',
              phone: user.phone,
            }),
          },
          {
            sort_order: 1,
            content_type: 'text',
            content: JSON.stringify({
              title: '简介',
              body: '这是一张在压力测试中创建的名片。',
            }),
          },
        ],
      }), {
        headers: authHeaders,
      });
      brochureCreateDuration.add(Date.now() - createStart);

      const createOk = check(createRes, {
        'create brochure status is 200': (r) => r.status === 200,
        'create brochure has id': (r) => {
          try { return JSON.parse(r.body).id !== undefined; } catch { return false; }
        },
      });
      errorRate.add(!createOk);

      if (createOk) {
        const brochure = JSON.parse(createRes.body);
        const brochureId = brochure.id;
        vuCache.set('brochureId', brochureId);
        vuCache.set('shareToken', brochure.share_token);

        // ── 发布名片 ──
        const publishRes = http.post(
          `${API_BASE}/api/brochures/${brochureId}/publish`,
          null,
          { headers: authHeaders }
        );
        const publishOk = check(publishRes, {
          'publish status is 200': (r) => r.status === 200,
          'publish changes status to published': (r) => {
            try { return JSON.parse(r.body).status === 'published'; } catch { return false; }
          },
        });
        errorRate.add(!publishOk);

        if (publishOk) {
          const published = JSON.parse(publishRes.body);
          vuCache.set('shareToken', published.share_token);
        }

        // ── 获取名片列表 ──
        const listRes = http.get(`${API_BASE}/api/brochures`, {
          headers: authHeaders,
        });
        check(listRes, {
          'list brochures status is 200': (r) => r.status === 200,
        });

        // ── 更新名片 ──
        const updateRes = http.put(
          `${API_BASE}/api/brochures/${brochureId}`,
          JSON.stringify({
            title: `更新_压力测试名片_${vuId}_${Date.now()}`,
          }),
          { headers: authHeaders }
        );
        check(updateRes, {
          'update brochure status is 200': (r) => r.status === 200,
        });
      }
    });

    // ── 通过分享 token 访问 ──
    group('分享访问', function () {
      const st = vuCache.get('shareToken');
      if (st) {
        const accessStart = Date.now();
        const shareRes = http.get(`${API_BASE}/api/brochures/share/${st}`);
        shareAccessDuration.add(Date.now() - accessStart);

        const shareOk = check(shareRes, {
          'share access status is 200': (r) => r.status === 200,
          'share access returns brochure': (r) => {
            try { return JSON.parse(r.body).share_token === st; } catch { return false; }
          },
        });
        errorRate.add(!shareOk);
      }
    });

    // ── 获取模板配置 ──
    group('模板查询', function () {
      const purposes = ['partner', 'client', 'investor', 'supplier'];
      const purpose = purposes[vuId % purposes.length];
      const tplRes = http.get(`${API_BASE}/api/brochures/template/${purpose}`);
      check(tplRes, {
        'template query status is 200': (r) => r.status === 200,
        'template has pages': (r) => {
          try { return JSON.parse(r.body).pages.length > 0; } catch { return false; }
        },
      });
    });

    // ── 删除名片（30% 概率） ──
    if (vuId % 3 === 1) {
      const brochureId = vuCache.get('brochureId');
      if (brochureId) {
        const delRes = http.del(`${API_BASE}/api/brochures/${brochureId}`, null, {
          headers: authHeaders,
        });
        check(delRes, {
          'delete brochure status is 200': (r) => r.status === 200,
        });
      }
    }
  });
}

// ============================================================
// 清理阶段
// ============================================================

export function teardown(data) {
  // 可选: 清理测试数据
  console.log(`[Teardown] 压力测试完成. 预注册用户数: ${data.preRegistered.length}`);
}
