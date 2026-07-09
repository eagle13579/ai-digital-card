import json, urllib.request, urllib.error, sys

BASE = "http://localhost:8002"

def api(method, path, data=None, token=None, timeout=10):
    url = BASE + path
    body = json.dumps(data).encode() if data else None
    req = urllib.request.Request(url, data=body, method=method)
    req.add_header("Content-Type", "application/json")
    if token:
        req.add_header("Authorization", "Bearer " + token)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return resp.status, json.loads(resp.read())
    except urllib.error.HTTPError as e:
        raw = e.read()
        try: return e.code, json.loads(raw)
        except: return e.code, raw.decode()[:300]
    except Exception as e:
        return -1, str(e)

# Login
s, d = api("POST", "/api/v1/auth/login", {"phone": "13900001111", "password": "Test123!@#"})
if s != 200:
    print("LOGIN FAILED"); sys.exit(1)
token = d["access_token"]
print(f"✅ 登录成功")

# 1. 名片创建
s, d = api("POST", "/api/v1/business-card/cards", {
    "title": "修复验证", "purpose": "personal",
    "pages": [{"sort_order": 0, "content_type": "text", "content": "通过"}]
}, token=token)
print(f"✅ 创建名片: {s}" if s < 300 else f"❌ 创建名片: {s} {json.dumps(d,ensure_ascii=False)[:80]}")

# 2. 推荐
s, d = api("POST", "/api/v1/recommend/personal", {"limit": 1}, token=token)
print(f"✅ 推荐系统: {s}" if s < 300 else f"❌ 推荐系统: {s} {str(d)[:80]}")

# 3. 订阅计划
s, d = api("GET", "/api/v1/subscription/plans", token=token)
if s == 200 and isinstance(d, list):
    ok = any(p.get("name") and p["name"] != "?" for p in d)
    print(f"{'✅' if ok else '❌'} 订阅计划: {s} {len(d)}条 name={[p.get('name') for p in d]}")
else:
    print(f"❌ 订阅计划: {s}")

# 4. AI写作
s, d = api("POST", "/api/v1/ai/assist/write", {
    "prompt": "写公司简介", "brochure_id": 10, "purpose": "company_intro"
}, token=token)
print(f"✅ AI写作: {s}" if s < 400 else f"❌ AI写作: {s} {json.dumps(d,ensure_ascii=False)[:80]}")

# 5. 根路径
s, d = api("GET", "/")
print(f"✅ 根路径: {s}" if s == 200 else f"❌ 根路径: {s}")

# 6. 分享页
s, d = api("GET", "/view/test123")
print(f"{'✅' if s == 200 else '❌'} 分享页: {s}")

# 7. Sunset头
import http.client
conn = http.client.HTTPConnection("localhost", 8002)
conn.request("GET", "/api/v1/users/me", headers={"Authorization": "Bearer " + token})
resp = conn.getresponse()
resp.read()
sunset = resp.getheader("sunset", "")
print(f"{'❌' if sunset else '✅'} Sunset头: {'还在' if sunset else '已移除'}")

print("\n=== 验证完成 ===")
