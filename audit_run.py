#!/usr/bin/env python3
"""AI数字名片 - 审计测试脚本（纯Python HTTP，不用curl）"""
import json
import http.client
import sys
import re
import urllib.request

BASE_HOST = "localhost"
BASE_PORT = 8002

def api(method, path, data=None, token=None, timeout=20):
    """直接用Python http.client调用API"""
    conn = http.client.HTTPConnection(BASE_HOST, BASE_PORT, timeout=timeout)
    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = "Bearer " + token
    body = json.dumps(data, ensure_ascii=False) if data else None
    try:
        conn.request(method, path, body=body, headers=headers)
        resp = conn.getresponse()
        raw = resp.read().decode('utf-8', errors='replace')
        status = resp.status
        conn.close()
        return status, raw
    except Exception as e:
        return 0, str(e)

def response_ok(status, raw):
    return 200 <= status < 300

def resp_json(raw):
    try:
        return json.loads(raw)
    except:
        return None

# ===== STEP 1: Health Check =====
status, raw = api("GET", "/health")
print(f"[Health] {status} | {raw[:100]}")

# ===== STEP 2: Register =====
reg_data = {"phone": "13911112222", "password": "TestPass2024!", "name": "audit_test"}
status, raw = api("POST", "/api/v1/auth/register", reg_data)
print(f"[Register] {status} | {raw[:200]}")

if status == 422:
    # User may already exist, just try login
    pass

# ===== STEP 3: Login =====
login_data = {"phone": "13911112222", "password": "TestPass2024!"}
status, raw = api("POST", "/api/v1/auth/login", login_data)
print(f"[Login] {status}")

token = None
j = resp_json(raw)
if j and isinstance(j, dict) and j.get("access_token"):
    token = j["access_token"]
    print(f"[Token] {token[:40]}...")
else:
    print(f"[FAIL] {raw[:200]}")
    sys.exit(1)

# ===== STEP 4: Full User Flow =====
bugs = []
sec_bugs = []

tests = [
    ("Auth Me", "GET", "/api/v1/auth/me"),
    ("Create Card", "POST", "/api/v1/business-card/cards", {"name":"测试名片","company":"红队科技","title":"安全工程师"}),
    ("List Cards", "GET", "/api/v1/business-card/cards"),
    ("Create Brochure", "POST", "/api/v1/brochures", {"title":"测试画册"}),
    ("AI Chat", "POST", "/api/v1/ai/deepseek/chat", {"messages":[{"role":"user","content":"你好呀"}]}),
    ("AI Writing", "POST", "/api/v1/ai/assist/write", {"purpose":"bio","name":"测试用户"}),
    ("Recommend", "GET", "/api/v1/recommend/personal"),
    ("Subscription", "GET", "/api/v1/subscription/plans"),
    ("KG Network", "GET", "/api/v1/knowledge-graph/network/1"),
    ("SAG Analyze", "POST", "/api/v1/ai/sag/analyze", {"query":"测试SAG","context":"测试端到端"}),
    ("Match Search", "POST", "/api/v1/match/semantic-search", {"query":"寻找技术合伙人"}),
]

print("\n=== USER FLOW ===")
for t in tests:
    name = t[0]
    method = t[1]
    path = t[2]
    data = t[3] if len(t) > 3 else None
    
    timeout = 60 if "chat" in path or "write" in path or "analyze" in path else 20
    status, raw = api(method, path, data, token, timeout)
    
    ok = response_ok(status, raw)
    if ok:
        j = resp_json(raw)
        if j and isinstance(j, dict) and j.get("detail"):
            print(f"  [WARN/{status}] {name}: {str(j['detail'])[:100]}")
            bugs.append((name, str(j['detail'])[:100]))
        else:
            print(f"  [OK/{status}] {name}")
    else:
        j = resp_json(raw)
        detail = str(j.get("detail", raw[:150])) if j else raw[:150]
        print(f"  [BUG/{status}] {name}: {detail}")
        bugs.append((name, detail))

# ===== STEP 5: RED TEAM =====
print("\n=== RED TEAM ===")

# 5a. SQL Injection on login
sqli_data = {"phone": "' OR 1=1--", "password": "x"}
status, raw = api("POST", "/api/v1/auth/login", sqli_data)
if response_ok(status, raw) and '"access_token"' in raw:
    sec_bugs.append(("CRITICAL SQLi Bypass: Login injection", raw[:100]))
    print(f"  [LEAK] SQLi Login: {raw[:100]}")
else:
    print(f"  [OK/blocked] SQLi Login: {status}")

# 5b. No auth
status, raw = api("GET", "/api/v1/auth/me")
if response_ok(status, raw):
    sec_bugs.append(("Auth Bypass: /auth/me without token returned 200", ""))
    print(f"  [LEAK] NoAuth Me: {status}")
else:
    print(f"  [OK/blocked] NoAuth Me: {status}")

# 5c. Fake token
status, raw = api("GET", "/api/v1/auth/me", token="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIn0.dozjgN18PkL4v0p0v0p0v0")
if response_ok(status, raw):
    sec_bugs.append(("Auth Bypass: Fake JWT accepted", raw[:100]))
    print(f"  [LEAK] FakeToken: {status}")
else:
    print(f"  [OK/blocked] FakeToken: {status}")

# 5d. Info leaks
info_paths = ["/.env", "/docs", "/openapi.json", "/metrics", "/admin", "/debug", "/swagger", "/redoc", "/.git/config"]
for path in info_paths:
    status, raw = api("GET", path)
    if status == 200 and len(raw) > 20:
        sec_bugs.append((f"Info Leak: {path} returns 200", raw[:80]))
        print(f"  [LEAK/{status}] {path}: {raw[:80]}")
    else:
        print(f"  [OK/blocked/{status}] {path}")

# 5e. CORS check
conn = http.client.HTTPConnection(BASE_HOST, BASE_PORT, timeout=10)
conn.request("OPTIONS", "/health", headers={
    "Origin": "https://evil.com",
    "Access-Control-Request-Method": "GET"
})
resp = conn.getresponse()
raw = resp.read().decode()
cors_hdrs = dict(resp.getheaders())
conn.close()

if cors_hdrs.get("access-control-allow-origin", "") == "*":
    sec_bugs.append(("CORS: Wildcard allow-origin", ""))
    print(f"  [LEAK] CORS wildcard")
elif cors_hdrs.get("access-control-allow-origin", "") == "https://evil.com":
    sec_bugs.append(("CORS: Mirror origin", cors_hdrs.get("access-control-allow-origin", "")))
    print(f"  [LEAK] CORS mirror origin")
else:
    acao = cors_hdrs.get("access-control-allow-origin", "not set")
    print(f"  [OK] CORS: {acao}")

# 5f. Rate limiting check
codes = []
for i in range(10):
    status, raw = api("GET", "/api/v1/auth/me", token=token)
    codes.append(str(status))
unique = set(codes)
if len(unique) == 1:
    sec_bugs.append(("No Rate Limiting: 10/10 same status", str(codes)))
    print(f"  [LEAK] No rate limiting: {''.join(codes)}")
else:
    print(f"  [rate OK] Codes: {''.join(codes)}")

# 5g. Security headers check
conn = http.client.HTTPConnection(BASE_HOST, BASE_PORT, timeout=10)
conn.request("GET", "/health")
resp = conn.getresponse()
raw = resp.read().decode()
h = dict(resp.getheaders())
conn.close()

missing = []
if 'content-security-policy' not in h: missing.append("CSP")
if 'strict-transport-security' not in h: missing.append("HSTS")
if 'x-content-type-options' not in h: missing.append("X-Content-Type-Options")
if 'x-frame-options' not in h: missing.append("X-Frame-Options")
for m in missing:
    sec_bugs.append((f"Missing Security Header: {m}", ""))
print(f"  [Headers] Missing: {missing if missing else 'None'}")

# ===== SUMMARY =====
print("\n" + "="*60)
print("  AI数字名片 审计结果汇总")
print("="*60)
print(f"\n用户流程问题: {len(bugs)}")
for n, d in bugs:
    print(f"  [{n}] {d[:120]}")
print(f"\n安全问题: {len(sec_bugs)}")
for n, d in sec_bugs:
    print(f"  [!] {n}")
    if d:
        print(f"      {d[:120]}")

# Save report
report = {
    "user_flow_bugs": [{"name": n, "detail": d[:200]} for n, d in bugs],
    "security_bugs": [{"name": n, "detail": d[:200]} for n, d in sec_bugs],
    "total_bugs": len(bugs) + len(sec_bugs)
}
with open(r"D:\AI数智名片\audit_results.json", "w") as f:
    json.dump(report, f, ensure_ascii=False, indent=2)
print(f"\n报告已保存: audit_results.json")
