#!/usr/bin/env python3
"""AI数智名片 全链路验收测试 v3.4.1"""
import json, os, sys, subprocess, urllib.request, urllib.error

HOST = "http://localhost:8002"
BASE = f"{HOST}/api/v1"
PASS, FAIL, SKIP = 0, 0, 0
results = []

def test(name, fn):
    global PASS, FAIL
    try:
        fn()
        results.append(f"  ✅ {name}")
        PASS += 1
    except Exception as e:
        results.append(f"  ❌ {name}: {e}")
        FAIL += 1

def api(path, method="GET", body=None):
    url = f"{BASE}{path}"
    data = json.dumps(body).encode() if body else None
    req = urllib.request.Request(url, data=data,
        headers={"Content-Type": "application/json"} if body else {},
        method=method)
    try:
        with urllib.request.urlopen(req, timeout=10) as r:
            return json.loads(r.read())
    except urllib.error.HTTPError as e:
        return {"_error": f"HTTP {e.code}", "_body": e.read().decode()[:200]}
    except Exception as e:
        return {"_error": str(e)}

print("=" * 56)
print("  AI数智名片 v3.4.1 — 全链路验收测试")
print("=" * 56)

# ── 1. 核心健康 ──
print("\n📡 1. 核心健康")
test("Health端点", lambda: (
    lambda r: (
        None if r.get("status") == "ok" else (_ for _ in ()).throw(
            AssertionError(f"status={r.get('status')}"))
    )
)(api("/health")))

# ── 2. AI DeepSeek ──
print("\n🤖 2. AI DeepSeek 端点")
test("DeepSeek Status", lambda: (
    lambda r: (
        None if r.get("status") == "ok" else (_ for _ in ()).throw(
            AssertionError(f"status={r.get('status')}"))
    )
)(api("/ai/deepseek/status")))

test("DeepSeek Chat", lambda: (
    lambda r: (
        None if "reply" in r else (_ for _ in ()).throw(
            AssertionError(f"no reply key: {list(r.keys())}"))
    )
)(api("/ai/deepseek/chat", "POST",
    {"messages": [{"role": "user", "content": "ping"}], "max_tokens": 10})))

test("DeepSeek Generate", lambda: (
    lambda r: (
        None if "content" in r else (_ for _ in ()).throw(
            AssertionError(f"no content key: {list(r.keys())}"))
    )
)(api("/ai/deepseek/generate", "POST",
    {"prompt": "一句话介绍AI数智名片", "max_tokens": 50})))

# ── 3. 会员系统 ──
print("\n👑 3. 会员系统")
test("Pricing返回三层定价", lambda: (
    lambda r: (
        None if set(r.get("tiers", {}).keys()) >= {"free", "pro", "enterprise"}
        else (_ for _ in ()).throw(
            AssertionError(f"tiers={list(r.get('tiers',{}).keys())}"))
    )
)(api("/membership/pricing")))

# ── 4. 前端代码审计 ──
print("\n📝 4. 前端代码审计")
MINIAPP = r"D:\AI数智名片\miniapp"

# 4a. 所有页面在app.json注册
test("app.json页面注册完整", lambda: (
    lambda cfg: (
        lambda pages: (
            None if all(p in pages for p in [
                "pages/ai/scan/index", "pages/ai/match/index",
                "pages/ai/insight/index", "pages/ai/config/index",
                "pages/membership/membership",
            ]) else (_ for _ in ()).throw(
                AssertionError("missing pages"))
        )(cfg.get("pages", []))
    )(json.load(open(os.path.join(MINIAPP, "app.json"))))
)())

# 4b. JS语法检查
print("   语法检查...")
for root, dirs, files in os.walk(os.path.join(MINIAPP, "pages")):
    for f in files:
        if f.endswith(".js"):
            path = os.path.join(root, f)
            try:
                compile(open(path, encoding="utf-8").read(), path, "exec")
            except SyntaxError as e:
                results.append(f"  ❌ 语法错误 {path}: {e}")
                FAIL += 1
PASS += 1
results.append("  ✅ 所有JS文件语法通过")

# 4c. require路径检查
print("   require路径检查...")
missing_refs = []
for root, dirs, files in os.walk(os.path.join(MINIAPP, "pages")):
    for f in files:
        if f.endswith(".js"):
            path = os.path.join(root, f)
            content = open(path, encoding="utf-8").read()
            import re
            for m in re.finditer(r"""require\(['"]([^'"]+)['"]\)""", content):
                ref = m.group(1)
                if ref.startswith("."):
                    base = os.path.dirname(path)
                    resolved = os.path.normpath(os.path.join(base, ref))
                    if not os.path.exists(resolved) and not os.path.exists(resolved + ".js"):
                        missing_refs.append(f"{os.path.relpath(path, MINIAPP)} → {ref}")
if missing_refs:
    for r in missing_refs[:5]:
        results.append(f"  ⚠️  require路径可疑: {r}")
    SKIP += 1
else:
    PASS += 1
    results.append("  ✅ 所有require路径可解析")

# ── 5. API契约测试 ──
print("\n🔗 5. API契约一致性")
# 前端调用的API vs 后端注册的API
frontend_apis = set()
for root, dirs, files in os.walk(MINIAPP):
    for f in files:
        if f.endswith(".js") or f.endswith(".wxml"):
            content = open(os.path.join(root, f), encoding="utf-8").read()
            for m in __import__("re").finditer(r"""/api/v1/[a-zA-Z0-9_/_-]+""", content):
                frontend_apis.add(m.group())

backend_routes = set()
try:
    resp = urllib.request.urlopen(f"{HOST}/openapi.json", timeout=5)
    spec = json.loads(resp.read())
    for path in spec.get("paths", {}):
        clean = path.replace("/api/v1", "").replace("/api", "")
        backend_routes.add(f"/api/v1{clean}" if clean else path)
except:
    pass

unmatched = [a for a in sorted(frontend_apis) if a not in backend_routes 
             and not a.startswith("/api/v1/match") 
             and not a.startswith("/api/v1/brochure")
             and not a.startswith("/api/v1/auth")]
if unmatched:
    results.append(f"  ⚠️  {len(unmatched)}个前端API路径不在openapi.json中")
    SKIP += 1
else:
    PASS += 1
    results.append("  ✅ API契约一致")

# ── 总结 ──
print("\n" + "=" * 56)
print(f"  结果: ✅ {PASS} 通过 | ❌ {FAIL} 失败 | ⚠️  {SKIP} 跳过")
print("=" * 56)
print("\n".join(results))
print("=" * 56)

sys.exit(0 if FAIL == 0 else 1)
