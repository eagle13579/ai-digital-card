// k6 stress test — AI数字名片
// 10→50→100→200 VU 阶梯, 找崩溃点
import http from 'k6/http';
import { check, sleep } from 'k6';
import { Rate } from 'k6/metrics';

const BASE_URL = __ENV.BASE_URL || 'http://localhost:8200';
const errorRate = new Rate('errors');

export const options = {
  stages: [
    { duration: '1m', target: 10 },   // warm-up
    { duration: '1m', target: 50 },   // moderate
    { duration: '1m', target: 100 },  // high
    { duration: '1m', target: 200 },  // peak
    { duration: '30s', target: 0 },   // cooldown
  ],
  thresholds: {
    http_req_failed: ['rate<0.05'],
    http_req_duration: ['p(95)<5000'],
  },
};

export default function () {
  // Health — always safe
  {
    const r = http.get(`${BASE_URL}/health`);
    check(r, { 'health ok': (res) => res.status === 200 });
  }

  // Login
  {
    const r = http.post(`${BASE_URL}/api/v1/auth/login`, JSON.stringify({
      phone: `stress_${__VU}@test.com`,
      password: 'test1234',
    }), { headers: { 'Content-Type': 'application/json' } });
    const ok = check(r, { 'login status 200': (res) => res.status === 200 });
    if (!ok) { errorRate.add(1); return; }
    sleep(0.3);
  }

  // Brochure list
  {
    const r = http.post(`${BASE_URL}/graphql`, JSON.stringify({
      query: `{ brochures(limit: 5) { id title status } }`,
    }), { headers: { 'Content-Type': 'application/json' } });
    const ok = check(r, { 'graphql ok': (res) => res.status === 200 });
    if (!ok) errorRate.add(1);
    sleep(0.3);
  }

  // Templates
  {
    const r = http.get(`${BASE_URL}/api/v1/templates`);
    const ok = check(r, { 'templates ok': (res) => res.status === 200 });
    if (!ok) errorRate.add(1);
    sleep(0.3);
  }
}
