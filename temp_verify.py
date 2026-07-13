#!/usr/bin/env python3
"""AI数字名片 API 端到端验证脚本"""
import urllib.request, json, sys

BASE = "http://127.0.0.1:8201"
results = {"ok": 0, "fail": 0}

def test(name, method="GET", path="/", headers=None, data=None):
    global results
    url = BASE + path
    hdrs = {"Content-Type": "application/json"}
    if headers: hdrs.update(headers)
    try:
        body = json.dumps(data).encode() if data else None
        req = urllib.request.Request(url, data=body, headers=hdrs, method=method)
        resp = urllib.request.urlopen(req, timeout=5)
        result = json.loads(resp.read().decode())
        if isinstance(result, dict) and "code" in result:
            ok = result.get("code") == 0
            if ok:
                d = result.get("data", result)
                if isinstance(d, list):
                    print(f"  ✅ {path} → {len(d)} items")
                elif isinstance(d, dict):
                    print(f"  ✅ {path} → OK ({len(d)} keys)")
                else:
                    print(f"  ✅ {path} → OK")
            else:
                print(f"  ❌ {path} → code={result['code']}: {result.get('message','')}")
                results["fail"] += 1
                return
        elif isinstance(result, list):
            print(f"  ✅ {path} → {len(result)} items")
        elif isinstance(result, dict):
            print(f"  ✅ {path} → OK")
        else:
            print(f"  ✅ {path} → {str(result)[:60]}")
        results["ok"] += 1
    except urllib.error.HTTPError as e:
        body = e.read().decode()[:80]
        print(f"  ❌ {path} → HTTP {e.code}")
        results["fail"] += 1
    except Exception as e:
        print(f"  ❌ {path} → {str(e)[:60]}")
        results["fail"] += 1

print("=" * 50)
print("AI数字名片 · API端到端验证")
print("=" * 50)

# Public endpoints
test("Health", "GET", "/health")
test("API Health", "GET", "/api/health")
test("Brochures", "GET", "/api/brochures")
test("Brochure 1", "GET", "/api/brochures/1")
test("Brochure 5", "GET", "/api/brochures/5")
test("Tags", "GET", "/api/tags")
test("Platforms", "GET", "/api/business-card/platforms")
test("Organizations", "GET", "/api/business-card/organizations")
test("OpenAPI", "GET", "/openapi.json")

# Register a test user (for auth testing)
test("Register", "POST", "/api/auth/register",
     data={"phone":"13800009999","password":"Test123!@#","name":"测试用户","company":"测","title":"测"})
test("Login", "POST", "/api/auth/login",
     data={"phone":"13800009999","password":"Test123!@#"})

print()
print(f"结果: ✅ {results['ok']} 通过, ❌ {results['fail']} 失败")
print("=" * 50)
