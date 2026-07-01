// k6 smoke test — AI数字名片
// 验证核心端点可达且响应时间 < 500ms
import http from 'k6/http';
import { check, sleep } from 'k6';
import { Rate, Trend } from 'k6/metrics';

const BASE_URL = __ENV.BASE_URL || 'http://localhost:8200';

const errorRate = new Rate('errors');
const healthTrend = new Trend('health_duration');
const loginTrend = new Trend('login_duration');
const brochuresTrend = new Trend('brochures_duration');
const templatesTrend = new Trend('templates_duration');

export const options = {
  vus: 1,
  iterations: 5,
  thresholds: {
    health_duration: ['p(95)<500'],
    login_duration: ['p(95)<500'],
    brochures_duration: ['p(95)<500'],
    templates_duration: ['p(95)<500'],
    errors: ['rate<0.1'],
  },
};

export default function () {
  // 1. Health check
  {
    const r = http.get(`${BASE_URL}/health`);
    healthTrend.add(r.timings.duration);
    const ok = check(r, { 'health status 200': (res) => res.status === 200 });
    if (!ok) errorRate.add(1);
    sleep(0.5);
  }

  // 2. Login (POST /api/v1/auth/login)
  {
    const r = http.post(`${BASE_URL}/api/v1/auth/login`, JSON.stringify({
      phone: '13800138000',
      password: 'test1234',
    }), { headers: { 'Content-Type': 'application/json' } });
    loginTrend.add(r.timings.duration);
    const ok = check(r, {
      'login status 200': (res) => res.status === 200,
      'login has token': (res) => res.json('access_token') !== undefined,
    });
    if (!ok) errorRate.add(1);
    sleep(0.5);
  }

  // 3. Brochure list (GraphQL)
  {
    const r = http.post(`${BASE_URL}/graphql`, JSON.stringify({
      query: `{ brochures(limit: 5) { id title status } }`,
    }), { headers: { 'Content-Type': 'application/json' } });
    brochuresTrend.add(r.timings.duration);
    const ok = check(r, {
      'brochures status 200': (res) => res.status === 200,
      'brochures returns data': (res) => res.json('data.brochures') !== undefined,
    });
    if (!ok) errorRate.add(1);
    sleep(0.5);
  }

  // 4. Templates (GET /api/v1/templates)
  {
    const r = http.get(`${BASE_URL}/api/v1/templates`);
    templatesTrend.add(r.timings.duration);
    const ok = check(r, {
      'templates status 200': (res) => res.status === 200,
    });
    if (!ok) errorRate.add(1);
    sleep(0.5);
  }
}
