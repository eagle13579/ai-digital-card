import json, urllib.request, urllib.error

BASE = "http://localhost:8002"

def api(method, path, data=None, token=None):
    url = BASE + path
    body = json.dumps(data).encode() if data else None
    req = urllib.request.Request(url, data=body, method=method)
    req.add_header("Content-Type", "application/json")
    req.add_header("Accept", "application/json")
    if token:
        req.add_header("Authorization", "Bearer " + token)
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            return resp.status, json.loads(resp.read())
    except urllib.error.HTTPError as e:
        raw = e.read()
        try:
            return e.code, json.loads(raw)
        except:
            return e.code, raw.decode()[:500]
    except Exception as e:
        return -1, str(e)

results = []

# 1. Login
s, d = api("POST", "/api/v1/auth/login", {"phone": "13900001111", "password": "Test123!@#"})
token = d.get("access_token", "")
results.append(("登录", s, s == 200))

# 2. 创建名片
s, d = api("POST", "/api/v1/business-card/cards", {
    "title": "test", "purpose": "personal",
    "pages": [{"sort_order": 0, "content_type": "text", "content": "hello"}]
}, token=token)
results.append(("创建名片", s, s in (200, 201), str(d)[:80]))

# 3. 推荐系统
s, d = api("POST", "/api/v1/recommend/personal", {"limit": 3}, token=token)
results.append(("推荐系统", s, s == 200, str(d)[:80]))

# 4. 订阅计划
s, d = api("GET", "/api/v1/subscription/plans", token=token)
if s == 200 and isinstance(d, list):
    ok = any(p.get("name") for p in d if p.get("name") and p["name"] != "?")
    results.append(("订阅计划", s, ok, f"{len(d)}条"))
else:
    results.append(("订阅计划", s, False, str(d)[:60]))

# 5. 分享页
s, d = api("GET", "/view/test123")
results.append(("分享页", s, s != 404, str(d)[:60]))

# 6. AI聊天
s, d = api("POST", "/api/v1/ai/deepseek/chat", {
    "messages": [{"role": "user", "content": "你好"}], "session_id": "test"
}, token=token)
results.append(("AI聊天", s, s == 200))

# 7. AI写作
s, d = api("POST", "/api/v1/ai/assist/write", {
    "prompt": "写公司简介", "brochure_id": 10, "purpose": "company_intro"
}, token=token)
results.append(("AI写作", s, s < 400, str(d)[:60]))

# 8. 根路径
s, d = api("GET", "/")
results.append(("根路径", s, s == 200))

# 9. Sunset头
import http.client
conn = http.client.HTTPConnection("localhost", 8002)
conn.request("GET", "/api/v1/users/me", headers={"Authorization": "Bearer " + token})
resp = conn.getresponse()
resp.read()
sunset = resp.getheader("sunset", "")
results.append(("Sunset头", "有" if sunset else "无", not sunset, sunset[:30] if sunset else ""))

print("=" * 70)
print(f"{'项目':<16} {'状态码':<8} {'结果':<8} 详情")
print("=" * 70)
for r in results:
    name, code, ok, *detail = r
    icon = "✅" if ok else "❌"
    det = detail[0] if detail else ""
    print(f"{name:<16} {str(code):<8} {icon:<8} {det}")
