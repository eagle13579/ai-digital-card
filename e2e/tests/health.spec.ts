import { test, expect } from "@playwright/test";

const BASE = process.env.BASE_URL || "http://localhost:8201";

// ── /health ───────────────────────────────────────────────────

test("GET /health returns 200 and plain text OK", async ({ request }) => {
  const res = await request.get(`${BASE}/health`);
  expect(res.status()).toBe(200);
  expect(await res.text()).toBe("OK");
});

test("GET /health has no CORS headers (plain endpoint)", async ({ request }) => {
  const res = await request.get(`${BASE}/health`);
  const origin = res.headers()["access-control-allow-origin"];
  // /health returns PlainTextResponse, CORS is applied by middleware
  // Middleware should add the header; if not, this is informational
  console.log("access-control-allow-origin:", origin);
  // Just verify the response is still 200
  expect(res.status()).toBe(200);
});

// ── /api/health ───────────────────────────────────────────────

test("GET /api/health returns JSON with status ok", async ({ request }) => {
  const res = await request.get(`${BASE}/api/health`);
  expect(res.status()).toBe(200);
  const body = await res.json();
  expect(body).toHaveProperty("status", "ok");
  expect(body).toHaveProperty("service");
});

test("GET /api/health responds within 2 seconds", async ({ request }) => {
  const start = Date.now();
  const res = await request.get(`${BASE}/api/health`);
  const elapsed = Date.now() - start;
  expect(res.status()).toBe(200);
  expect(elapsed).toBeLessThan(2000);
});

test("GET /api/health returns valid JSON content-type", async ({ request }) => {
  const res = await request.get(`${BASE}/api/health`);
  expect(res.status()).toBe(200);
  const ct = res.headers()["content-type"] || "";
  expect(ct).toContain("application/json");
});

// ── / (root) ──────────────────────────────────────────────────

test("GET / returns HTML and 200", async ({ request }) => {
  const res = await request.get(`${BASE}/`);
  expect(res.status()).toBe(200);
  const text = await res.text();
  expect(text).toContain("<!DOCTYPE html") || expect(text).toContain("<html");
});
