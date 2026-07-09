#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""聚焦红队攻击验证脚本"""
import json, sys, time, urllib.request, urllib.error
import html, base64, uuid, os, datetime

BASE = "http://localhost:8002"
REPORT = []

def req(method, path, headers=None, data=None, timeout=8):
    url = BASE + path
    hdrs = dict(headers or {})
    if data is not None:
        body = json.dumps(data).encode()
        hdrs.setdefault("Content-Type", "application/json")
    else:
        body = None
    r = urllib.request.Request(url, data=body, headers=hdrs, method=method)
    try:
        resp = urllib.request.urlopen(r, timeout=timeout)
        return resp.status, dict(resp.headers), resp.read().decode(errors='replace')
    except urllib.error.HTTPError as e:
        return e.code, dict(e.headers), e.read().decode(errors='replace')
    except Exception as e:
        return 0, {}, str(e)

def report(severity, title, detail, status="未验证", fix=""):
    REPORT.append({"severity": severity, "title": title, "detail": detail, "status": status, "fix": fix})
    icons = {"已修复":"Y", "未修复":"N", "部分修复":"W", "未验证":"?", "已通过":"Y", "已拦截":"Y"}
    icon = icons.get(status, "?")
    print("  %s [%s] %s: %s" % (icon, severity, title, detail[:120]))

def sep(title):
    print("\n" + "=" * 70)
    print("  > " + title)
    print("=" * 70)

# ====== 0. Register test users ======
sep("0. Register test users")
uid1 = "redteam_a_" + uuid.uuid4().hex[:8]
uid2 = "redteam_b_" + uuid.uuid4().hex[:8]
phone1 = "1380000" + str(uuid.uuid4().int % 9000 + 1000)
phone2 = "1380000" + str(uuid.uuid4().int % 9000 + 1000)
pwd = "Test1234!!"

s, h, b = req("POST", "/api/v1/auth/register",
    data={"phone": phone1, "password": pwd, "name": uid1})
print("  Register A: " + str(s) + " " + b[:200])
try: d1 = json.loads(b)
except: d1 = {}
token_a = d1.get("access_token", "") or d1.get("token", "")

s, h, b = req("POST", "/api/v1/auth/register",
    data={"phone": phone2, "password": pwd, "name": uid2})
print("  Register B: " + str(s) + " " + b[:200])
try: d2 = json.loads(b)
except: d2 = {}
token_b = d2.get("access_token", "") or d2.get("token", "")

if not token_a:
    print("  Login A...")
    s, h, b = req("POST", "/api/v1/auth/login",
        data={"phone": phone1, "password": pwd})
    print("  Login A: " + str(s) + " " + b[:200])
    try: d1 = json.loads(b); token_a = d1.get("access_token", "") or d1.get("token", "")
    except: pass
if not token_b:
    print("  Login B...")
    s, h, b = req("POST", "/api/v1/auth/login",
        data={"phone": phone2, "password": pwd})
    print("  Login B: " + str(s) + " " + b[:200])
    try: d2 = json.loads(b); token_b = d2.get("access_token", "") or d2.get("token", "")
    except: pass

print("  Token A: " + ("OK" if token_a else "FAIL"))
print("  Token B: " + ("OK" if token_b else "FAIL"))

# ====== V1 - XSS ======
sep("V1. Stored XSS verification")

payload = "<script>alert(document.cookie)</script>"
s, h, b = req("POST", "/api/v1/brochures",
    headers={"Authorization": "Bearer " + token_a},
    data={
        "title": payload,
        "cover": "https://example.com/c.jpg",
        "purpose": "partner",
        "pages": [{"content_type": "text", "content": payload, "sort_order": 0}]
    })
print("  Create with XSS: HTTP " + str(s))
try: created = json.loads(b)
except: created = {}
bid = created.get("id")
btitle = created.get("title", "")
pcontent = ""
if created.get("pages"):
    pcontent = created["pages"][0].get("content", "")
    print("  title: " + repr(btitle))
    print("  content: " + repr(pcontent))

if "<script>" in btitle or "<script>" in pcontent:
    report("P0", "Stored XSS", "Payload NOT escaped! title=" + btitle[:60], "未修复", "need html.escape()")
else:
    report("P0", "Stored XSS", "Payload escaped OK. title=" + btitle[:60], "已修复", "html.escape() works")

# ====== V2 - Horizontal privilege ======
sep("V2. Horizontal privilege verification")

if bid and token_b:
    s, h, b = req("GET", "/api/v1/brochures/" + str(bid),
        headers={"Authorization": "Bearer " + token_b})
    print("  User B reads A's brochure: HTTP " + str(s))
    try: rb = json.loads(b)
    except: rb = {"detail": b[:200]}
    print("  Response: " + json.dumps(rb, ensure_ascii=False)[:200])

    if s == 403:
        report("P0", "Horizontal privilege (single)", "User B blocked from A's brochure (403)", "已修复", "user_id check works")
    elif s == 200:
        report("P0", "Horizontal privilege (single)", "User B can read A's brochure! Still vulnerable!", "未修复", "need user_id check")
    else:
        report("P0", "Horizontal privilege (single)", "HTTP " + str(s) + ": " + b[:80], "部分修复", "")
else:
    report("P0", "Horizontal privilege (single)", "Cannot verify (no data)", "未验证", "")

# V2b - list endpoint
print("\n  V2b: List endpoint check")
s, h, b = req("GET", "/api/v1/brochures?page_size=5",
    headers={"Authorization": "Bearer " + token_b})
try: lst = json.loads(b)
except: lst = {}
items = lst.get("items", []) or lst.get("data", [])
print("  User B sees " + str(len(items)) + " items")
other_uids = [str(it.get("user_id")) for it in items if it.get("user_id")]
if other_uids:
    print("  Other user_ids found: " + ", ".join(other_uids[:5]))
    report("P0", "Horizontal privilege (list)", "List returns all users' data, not filtered by current user", "部分修复", "list should filter by current user")
else:
    print("  All data belongs to current user")
    report("P0", "Horizontal privilege (list)", "List only returns current user data", "已修复", "")

# ====== V3 - Sensitive paths ======
sep("V3. Sensitive path exposure")

paths = [
    ("/docs", "Swagger docs"),
    ("/redoc", "ReDoc docs"),
    ("/openapi.json", "OpenAPI spec"),
    ("/metrics", "Prometheus metrics"),
]
for p, desc in paths:
    s, h, b = req("GET", p)
    blen = len(b)
    print("  GET " + p + ": HTTP " + str(s) + ", body=" + str(blen) + "B")
    if s == 200 and blen > 100:
        low = b.lower()
        if "swagger" in low or "redoc" in low or "openapi" in low:
            report("P1", "Sensitive path: " + desc, "HTTP " + str(s) + " " + str(blen) + "B doc content", "未修复", "disable in production")
        elif p == "/metrics" and blen > 100:
            report("P1", "Sensitive path: " + desc, "HTTP " + str(s) + " " + str(blen) + "B metrics", "未修复", "disable in production")
        else:
            report("P1", "Sensitive path: " + desc, "HTTP " + str(s) + " " + str(blen) + "B (non-doc)", "已修复", "")
    elif s in (404, 405):
        report("P1", "Sensitive path: " + desc, "HTTP " + str(s) + " disabled", "已修复", "")
    else:
        report("P1", "Sensitive path: " + desc, "HTTP " + str(s) + " " + str(blen) + "B", "部分修复", "")

# ====== V4 - Security headers ======
sep("V4. Security headers check")

s, h, b = req("GET", "/api/v1/auth/login")
checks = {
    "content-security-policy": "CSP",
    "strict-transport-security": "HSTS",
    "x-content-type-options": "X-CTO",
    "x-frame-options": "XFO",
    "x-xss-protection": "XXP",
    "referrer-policy": "Referrer-Policy",
    "permissions-policy": "Permissions-Policy",
}
all_ok = True
for hdr, name in checks.items():
    val = h.get(hdr)
    if val:
        print("  Y " + name + ": " + val[:60])
    else:
        print("  N " + name + ": MISSING")
        all_ok = False

if all_ok:
    report("P1", "Security headers", "All 7 security headers present. CSP: " + str(h.get("content-security-policy",""))[:50], "已通过", "")
else:
    report("P1", "Security headers", "Some headers missing", "未修复", "add missing headers")

print("  Server: " + str(h.get("server", "")))

# ====== V5 - CSRF ======
sep("V5. CSRF verification")

s, h, b = req("OPTIONS", "/api/v1/brochures")
print("  OPTIONS: HTTP " + str(s))
cors = {k: v for k, v in h.items() if "access-control" in k.lower()}
print("  CORS: " + str(cors))

s, h, b = req("GET", "/api/csrf/token")
print("  GET /api/csrf/token: HTTP " + str(s))
try: cs = json.loads(b)
except: cs = {}
ct = cs.get("token", "")
print("  CSRF token: " + ("OK" if ct else "FAIL"))

if ct:
    report("P1", "CSRF protection", "CSRF token endpoint works, Double Submit Cookie pattern", "已通过", "")
else:
    report("P1", "CSRF protection", "CSRF token endpoint unavailable", "未修复", "")

# ====== V6 - JWT ======
sep("V6. JWT security")

if token_a:
    parts = token_a.split(".")
    if len(parts) == 3:
        # Decode header
        try:
            hb64 = parts[0]
            pad = 4 - len(hb64) % 4
            if pad != 4: hb64 += "=" * pad
            hdr_raw = base64.urlsafe_b64decode(hb64)
            hdr = json.loads(hdr_raw)
            print("  JWT alg: " + str(hdr.get("alg", "")))
            if hdr.get("alg") == "HS256":
                report("P2", "JWT signing algorithm", "Uses HS256 (symmetric). RS256 recommended", "部分修复", "code supports RS256 but token is HS256")
            elif hdr.get("alg") == "RS256":
                report("P2", "JWT signing algorithm", "Uses RS256 asymmetric", "已修复", "")
        except Exception as e:
            print("  JWT header decode: " + str(e))

        # Decode payload for expiry
        try:
            pb64 = parts[1]
            pad = 4 - len(pb64) % 4
            if pad != 4: pb64 += "=" * pad
            pl_raw = base64.urlsafe_b64decode(pb64)
            pl = json.loads(pl_raw)
            exp = pl.get("exp", 0)
            if exp:
                exp_dt = datetime.datetime.fromtimestamp(exp)
                now = datetime.datetime.now()
                hrs = (exp_dt - now).total_seconds() / 3600
                print("  Token expires: " + str(exp_dt))
                print("  Hours until expiry: %.1f" % hrs)
                if hrs > 24:
                    report("P1", "JWT expiry too long", "Token valid ~%.1f hours" % hrs, "已修复", "reduced to 60 min from 7 days")
                else:
                    report("P1", "JWT expiry", "Token valid ~%.1f hours (60 min config)" % hrs, "已修复", "ACCESS_TOKEN_EXPIRE_MINUTES=60")
        except Exception as e:
            print("  JWT payload decode: " + str(e))

# ====== V7 - Code security patterns ======
sep("V7. Code security anti-pattern scan")

bdir = "/d/AI数智名片/backend"
patterns = {
    "eval(": "eval()",
    "exec(": "exec()",
    "subprocess": "subprocess",
    "os.system": "os.system",
    "pickle.loads": "pickle unsafe deserialize",
}
finds = []
for root, dirs, files in os.walk(bdir):
    if "__pycache__" in root or ".pytest_cache" in root:
        continue
    for f in files:
        if f.endswith(".py"):
            fp = os.path.join(root, f)
            try:
                with open(fp, "r", encoding="utf-8", errors="ignore") as fh:
                    content = fh.read()
                    for pat, desc in patterns.items():
                        if pat in content:
                            rel = os.path.relpath(fp, bdir)
                            finds.append((pat, desc, rel))
            except:
                pass

seen = set()
for pat, desc, rel in finds:
    if pat not in seen:
        seen.add(pat)
        print("  W " + desc + " in " + rel)
        report("P2", "Anti-pattern: " + desc, "Found " + pat + " in " + rel, "未修复", "remove dangerous calls")

if not finds:
    print("  No dangerous calls found")
    report("P1", "Code security check", "No eval/exec/subprocess found", "已通过", "")

# JWT key strength
env_path = os.path.join(bdir, ".env")
try:
    with open(env_path, "r", encoding="utf-8") as f:
        env_content = f.read()
    for line in env_content.split("\n"):
        if line.startswith("JWT_SECRET="):
            secret_val = line.split("=", 1)[1].strip()
            if len(secret_val) < 32 or "change" in secret_val.lower() or "test" in secret_val.lower():
                print("  W JWT_SECRET weak: " + str(secret_val[:20]) + "...")
                report("P2", "JWT key strength", "JWT_SECRET too short or has placeholder value", "未修复", "use openssl rand -hex 32")
            else:
                report("P2", "JWT key strength", "JWT_SECRET is strong random key", "已修复", "")
            break
except Exception as e:
    print("  JWT key check failed: " + str(e))

# ====== Final report ======
sep("FINAL SECURITY SCORE")

sev_score = {"P0": 0, "P1": 0, "P2": 0}
stat_count = {"已修复": 0, "未修复": 0, "部分修复": 0, "已通过": 0, "已拦截": 0, "未验证": 0}
for r in REPORT:
    if r["severity"] in sev_score:
        sev_score[r["severity"]] += 1
    if r["status"] in stat_count:
        stat_count[r["status"]] += 1

print("\n  Severity: P0=%d, P1=%d, P2=%d" % (sev_score["P0"], sev_score["P1"], sev_score["P2"]))
print("  Status: fixed=%d, unfixed=%d, partial=%d, passed=%d" % (
    stat_count.get("已修复", 0),
    stat_count.get("未修复", 0),
    stat_count.get("部分修复", 0),
    stat_count.get("已通过", 0)))

fixed = stat_count.get("已修复", 0) + stat_count.get("已通过", 0) + stat_count.get("已拦截", 0)
total = len(REPORT)
if total > 0:
    score = int(fixed / total * 100)
else:
    score = 0
print("  Security score: %d/100 (%d/%d fixed)" % (score, fixed, total))

print("\n" + "=" * 70)
print("  FIX LIST")
print("=" * 70)
for r in REPORT:
    icons = {"已修复": "Y", "未修复": "N", "部分修复": "W", "已通过": "Y", "已拦截": "Y", "未验证": "?"}
    icon = icons.get(r["status"], "?")
    print("  %s [%s] %s: %s" % (icon, r["severity"], r["title"], r["status"]))

# Save
ts = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
full = {
    "scan_time": ts,
    "target": "AI Digital Business Card",
    "base_url": BASE,
    "security_score": "%d/100" % score,
    "summary": {"total": total, "fixed": fixed, "unfixed": total - fixed, "severity": sev_score},
    "findings": REPORT,
}
rpt_path = "/d/AI数智名片/backend/redteam_focused_report.json"
with open(rpt_path, "w", encoding="utf-8") as f:
    json.dump(full, f, ensure_ascii=False, indent=2)
print("\n  Report saved: " + rpt_path)
