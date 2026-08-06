#!/usr/bin/env python3
"""全面验证所有修复"""
import json, urllib.request, urllib.error

BASE = "http://localhost:8002"

def api(method, path, data=None, token=None):
    url = f"{BASE}{path}"
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

# Login
s, d = api("POST", "/api/v1/auth/login", {"phone": "13900001111", "password": "Test123!@#"})
print(f"[LOGIN] {s}")
token = d.get("access_token", "")
print(f"[TOKEN] {token[:30]}...")
print()

# 1. 名片创建
s, d = api("POST", "/api/v1/business-card/cards", {
    "title": "验证修复",
    "purpose": "personal",
    "pages": [{"sort_order": 0, "content_type": "text", "content": "测试通过"}]
}, token=token)
print(f"[1] 创建名片: {s} | {'✅' if s==201 else '❌'} | {json.dumps(d, ensure_ascii=False)[:100]}")

# 2. 推荐系统
s, d = api("POST", "/api/v1/recommend/personal", {"limit": 3}, token=token)
print(f"[2] 推荐系统: {s} | {'✅' if s==200 else '❌'} | {json.dumps(d, ensure_ascii=False)[:100]}")

# 3. 订阅计划
s, d = api("GET", "/api/v1/subscription/plans", token=token)
if s == 200 and isinstance(d, list):
    ok = all(p.get("name") and p.get("name") != "?" for p in d)
    print(f"[3] 订阅计划: {s} {len(d)}条 | {'✅' if ok else '❌'} | {[(p.get('name'),p.get('price')) for p in d]}")
else:
    print(f"[3] 订阅计划: {s} | ❌ | {str(d)[:100]}")

# 4. 分享页
s, d = api("GET", "/view/test123")
print(f"[4] 分享页: {s} | {'✅' if s!=404 else '❌'} | {str(d)[:80]}")

# 5. AI聊天 (messages格式)
s, d = api("POST", "/api/v1/ai/deepseek/chat", {
    "messages": [{"role": "user", "content": "你好"}],
    "session_id": "test"
}, token=token)
print(f"[5] AI聊天: {s} | {'✅' if s==200 else '❌'} | {str(d.get('reply',''))[:60]}")

# 6. AI写作
s, d = api("POST", "/api/v1/ai/assist/write", {
    "prompt": "写公司简介",
    "brochure_id": 10,
    "purpose": "company_intro"
}, token=token)
print(f"[6] AI写作: {s} | {'✅' if s<400 else '❌'} | {str(d)[:80]}")

# 7. 根路径
s, d = api("GET", "/")
print(f"[7] 根路径: {s} | {'✅' if s==200 else '❌'}")

# 8. Sunset头检查
import http.client
conn = http.client.HTTPConnection("localhost", 8002)
conn.request("GET", "/api/v1/users/me", headers={"Authorization": f"Bearer {token}"})
resp = conn.getresponse()
sunset = resp.getheader("sunset", "NONE")
print(f"[8] Sunset头: {sunset} | {'✅ 已移除' if 'NONE' in sunset else '❌ 还在'}")

print()
print("===== 验证完毕 =====")
