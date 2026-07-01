// k6 load test — AI数字名片
// 100VU × 2min, 登录→创建名片→获取列表
// 阈值: p95 < 2s, 错误率 < 1%
import http from 'k6/http';
import { check, sleep } from 'k6';
import { Rate, Trend } from 'k6/metrics';

const BASE_URL = __ENV.BASE_URL || 'http://localhost:8200';

const errorRate = new Rate('errors');
const loginTrend = new Trend('login_duration');
const createTrend = new Trend('create_duration');
const listTrend = new Trend('list_duration');

export const options = {
  stages: [
    { duration: '10s', target: 100 },  // ramp-up
    { duration: '2m', target: 100 },   // steady
    { duration: '10s', target: 0 },    // ramp-down
  ],
  thresholds: {
    login_duration: ['p(95)<2000'],
    create_duration: ['p(95)<2000'],
    list_duration: ['p(95)<2000'],
    errors: ['rate<0.01'],
  },
};

export default function () {
  const headers = { 'Content-Type': 'application/json' };
  let token = '';

  // Login
  {
    const r = http.post(`${BASE_URL}/api/v1/auth/login`, JSON.stringify({
      phone: `user_${__VU}@test.com`,
      password: 'test1234',
    }), { headers });
    loginTrend.add(r.timings.duration);
    if (check(r, { 'login ok': (res) => res.status === 200 })) {
      token = r.json('access_token') || '';
    } else {
      errorRate.add(1);
      return;
    }
    sleep(1);
  }

  const authHeaders = { ...headers, Authorization: `Bearer ${token}` };

  // Create brochure
  {
    const r = http.post(`${BASE_URL}/api/v1/brochures`, JSON.stringify({
      title: `名片-${__VU}-${Date.now()}`,
      purpose: 'partner',
      pages_count: 3,
    }), { headers: authHeaders });
    createTrend.add(r.timings.duration);
    const ok = check(r, {
      'create status 201': (res) => res.status === 201,
      'create has id': (res) => res.json('id') !== undefined,
    });
    if (!ok) errorRate.add(1);
    sleep(1);
  }

  // List brochures
  {
    const r = http.get(`${BASE_URL}/api/v1/brochures?limit=10`, { headers: authHeaders });
    listTrend.add(r.timings.duration);
    const ok = check(r, {
      'list status 200': (res) => res.status === 200,
      'list returns array': (res) => Array.isArray(res.json()),
    });
    if (!ok) errorRate.add(1);
    sleep(1);
  }
}
