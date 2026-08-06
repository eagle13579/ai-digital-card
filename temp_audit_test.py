"""AI数字名片 全量审计测试"""
import subprocess, json, re, sys

BASE = "http://localhost:8002"

def t(name, cmd, timeout=20):
    try:
        r = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=timeout)
        out = r.stdout
        code = "?"
        for c in ["200","201","400","401","403","404","422","500","502"]:
            if f"HTTP_{c}" in out:
                code = c
                break
        print(f"[{code}] {name}")
        return out, code
    except subprocess.TimeoutExpired:
        print(f"[TIMEOUT] {name}")
        return "", "TIMEOUT"

# Step 1: Register
out, _ = t("Register", """curl -s -w ' HTTP_%{http_code}' -X POST http://localhost:8002/api/v1/auth/register -H "Content-Type: application/json" -d '{"phone":"13911112222","password":"TestPass2024!","name":"审计测试"}' 2>/dev/null""")

# Step 2: Login
out2, _ = t("Login", """curl -s -w ' HTTP_%{http_code}' -X POST http://localhost:8002/api/v1/auth/login -H "Content-Type: application/json" -d '{"phone":"13911112222","password":"TestPass2024!"}' 2>/dev/null""")

# Extract token
token = None
if '"access_token"' in out2:
    m = re.search(r'"access_token"\s*:\s*"([^"]+)"', out2)
    if m:
        token = m.group(1)

if not token:
    print(f"No token: {out2[:200]}")
    sys.exit(0)

AUTH = f"Authorization: Bearer {token}"
print(f"Token OK: {token[:30]}...")

# === USER FLOW TESTS ===
bug_list = []

tests = [
    ("Auth Me", f"curl -s -w ' HTTP_%{{http_code}}' {BASE}/api/v1/auth/me -H \"{AUTH}\" 2>/dev/null"),
    ("Create Card", f"""curl -s -w ' HTTP_%{{http_code}}' -X POST {BASE}/api/v1/business-card/cards -H \"{AUTH}\" -H "Content-Type: application/json" -d '{{"name":"测试名片","company":"红队","title":"CEO"}}' 2>/dev/null"""),
    ("List Cards", f"curl -s -w ' HTTP_%{{http_code}}' {BASE}/api/v1/business-card/cards -H \"{AUTH}\" 2>/dev/null"),
    ("Create Brochure", f"""curl -s -w ' HTTP_%{{http_code}}' -X POST {BASE}/api/v1/brochures -H \"{AUTH}\" -H "Content-Type: application/json" -d '{{"title":"测试画册"}}' 2>/dev/null"""),
    ("AI Chat", f"""curl -s -w ' HTTP_%{{http_code}}' -X POST {BASE}/api/v1/ai/deepseek/chat -H \"{AUTH}\" -H "Content-Type: application/json" -d '{{"messages":[{{"role":"user","content":"你好"}}]}}' 2>/dev/null"""),
    ("AI Writing", f"""curl -s -w ' HTTP_%{{http_code}}' -X POST {BASE}/api/v1/ai/assist/write -H \"{AUTH}\" -H "Content-Type: application/json" -d '{{"purpose":"bio","name":"测试"}}' 2>/dev/null"""),
    ("Recommend", f"curl -s -w ' HTTP_%{{http_code}}' {BASE}/api/v1/recommend/personal -H \"{AUTH}\" 2>/dev/null"),
    ("Subscription", f"curl -s -w ' HTTP_%{{http_code}}' {BASE}/api/v1/subscription/plans -H \"{AUTH}\" 2>/dev/null"),
    ("KG Network", f"curl -s -w ' HTTP_%{{http_code}}' {BASE}/api/v1/knowledge-graph/network/1 -H \"{AUTH}\" 2>/dev/null"),
    ("SAG Analyze", f"""curl -s -w ' HTTP_%{{http_code}}' -X POST {BASE}/api/v1/ai/sag/analyze -H \"{AUTH}\" -H "Content-Type: application/json" -d '{{"query":"测试","context":"test"}}' 2>/dev/null"""),
    ("Match Search", f"""curl -s -w ' HTTP_%{{http_code}}' -X POST {BASE}/api/v1/match/semantic-search -H \"{AUTH}\" -H "Content-Type: application/json" -d '{{"query":"技术合伙人"}}' 2>/dev/null"""),
]

print("\n=== USER FLOW ===")
for name, cmd in tests:
    out, code = t(name, cmd)
    if code in ("500","404","422"):
        bug_list.append((name, code, out[:200]))
        print(f"  *** BUG [{code}]")
        print(f"      {out[:200]}")

# === RED TEAM ATTACKS ===
print("\n=== RED TEAM SECURITY ===")
rt_bugs = []

# SQLi
out, code = t("SQLi-Login", """curl -s -w ' HTTP_%{http_code}' -X POST http://localhost:8002/api/v1/auth/login -H "Content-Type: application/json" -d '{"phone":"'"'"' OR 1=1--","password":"x"}' 2>/dev/null""")
if code == "200":
    rt_bugs.append(("SQLi-Login Bypass!", code))

# Auth bypass
for name, cmd in [
    ("NoAuth Me", f"curl -s -w ' HTTP_%{{http_code}}' {BASE}/api/v1/auth/me 2>/dev/null"),
    ("FakeToken", f"""curl -s -w ' HTTP_%{{http_code}}' {BASE}/api/v1/auth/me -H "Authorization: Bearer eyJhbG.fake.5c" 2>/dev/null"""),
]:
    out, code = t(name, cmd)
    if code not in ("401","403"):
        rt_bugs.append((f"Auth bypass: {name}={code}", code))

# Info leak
for name, path in [
    (".env leak", "/.env"),
    ("Docs leak", "/docs"),
    ("OpenAPI", "/openapi.json"),
    ("Metrics", "/metrics"),
    ("Admin", "/admin"),
]:
    out, code = t(name, f"curl -s -w ' HTTP_%{{http_code}}' {BASE}{path} 2>/dev/null")
    if code == "200":
        rt_bugs.append((f"Info leak: {name}", code))

# CORS
cors_raw = subprocess.run(
    f"""curl -s -D - -o /dev/null -H 'Origin: https://evil.com' {BASE}/health 2>/dev/null""",
    shell=True, capture_output=True, text=True, timeout=8
).stdout
print(f"[CORS HEADERS]")
for line in cors_raw.split('\n'):
    if 'access-control' in line.lower():
        print(f"  {line.strip()}")
        if 'allow-origin: *' in line.lower() or 'allow-origin: https://evil' in line.lower():
            rt_bugs.append(("CORS wildcard/mirror", f"Origin: {line.strip()}"))

# Rate limit
rl_raw = subprocess.run(
    f"for i in 1 2 3 4 5 6 7 8 9 10; do curl -s -o /dev/null -w '%{{http_code}} ' {BASE}/api/v1/auth/me -H \"{AUTH}\" 2>/dev/null; done; echo",
    shell=True, capture_output=True, text=True, timeout=15
).stdout.strip()
print(f"[RATE] {rl_raw}")
codes = rl_raw.split()
if len(set(codes)) == 1 and all(c == "200" for c in codes):
    rt_bugs.append(("No rate limiting - 10/10 all 200", rl_raw))

# Security headers
hdrs = subprocess.run(
    f"curl -s -D - -o /dev/null {BASE}/health 2>/dev/null",
    shell=True, capture_output=True, text=True, timeout=8
).stdout
print(f"[HEADERS]")
has_csp = False
has_hsts = False
has_xss = False
for line in hdrs.split('\n'):
    l = line.strip().lower()
    if l.startswith('content-security-policy'): has_csp = True
    if l.startswith('strict-transport-security'): has_hsts = True
    if l.startswith('x-content-type-options') or l.startswith('x-xss-protection'): has_xss = True
    if l:
        print(f"  {line.strip()}")
if not has_csp: rt_bugs.append(("Missing CSP header", ""))
if not has_hsts: rt_bugs.append(("Missing HSTS header", ""))
if not has_xss: rt_bugs.append(("Missing XSS protection header", ""))

print(f"\n=== SUMMARY ===")
print(f"User Flow Bugs: {len(bug_list)}")
for n, c, d in bug_list:
    print(f"  [{c}] {n}")
print(f"Security Issues: {len(rt_bugs)}")
for n, d in rt_bugs:
    print(f"  [!] {n}")
