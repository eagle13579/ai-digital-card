#!/usr/bin/env python3
"""验证500错误：用正确的参数重测"""
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

# 登录
_, data = api("POST", "/api/v1/auth/login", {"phone": "13900001111", "password": "Test123!@#"})
TOKEN = data.get("access_token", "")
print(f"TOKEN: {TOKEN[:30]}...")

# ===== 用正确参数重测 500 API =====

# 1. 创建名片/画册 - 用 BrochureCreate 的正确 schema
print("\n[1] POST /api/v1/business-card/cards (正确参数)")
status, data = api("POST", "/api/v1/business-card/cards", {
    "title": "测试用户名片",  # 正确: title 而非 name
    "cover": "",
    "purpose": "personal",
    "pages": [
        {
            "sort_order": 0,
            "content_type": "text",
            "content": "测试用户\n测试科技\n产品经理",
            "image_url": "",
            "media_url": "",
            "ai_summary": ""
        }
    ]
}, token=TOKEN)
print(f"  → {status}: {json.dumps(data, ensure_ascii=False)[:200]}")

if status == 200:
    card_id = data.get("id", "?")
    print(f"  ✅ 创建成功, id={card_id}")
    
    # 测试发布
    print(f"\n[2] POST /api/v1/brochures/{card_id}/publish")
    status2, data2 = api("POST", f"/api/v1/brochures/{card_id}/publish", token=TOKEN)
    print(f"  → {status2}: {json.dumps(data2, ensure_ascii=False)[:200]}")

# 3. 推荐系统
print("\n[3] POST /api/v1/recommend/personal")
status, data = api("POST", "/api/v1/recommend/personal", {"limit": 3}, token=TOKEN)
print(f"  → {status}: {json.dumps(data, ensure_ascii=False)[:200]}")

# 4. AI聊天（正确参数）
print("\n[4] POST /api/v1/ai/deepseek/chat (messages 格式)")
status, data = api("POST", "/api/v1/ai/deepseek/chat", {
    "messages": [{"role": "user", "content": "你好"}],
    "session_id": "test_001"
}, token=TOKEN)
print(f"  → {status}: {json.dumps(data, ensure_ascii=False)[:200]}")

# 5. AI写作（加 purpose）
print("\n[5] POST /api/v1/ai/assist/write (加 purpose)")
status, data = api("POST", "/api/v1/ai/assist/write", {
    "prompt": "帮我写一段公司简介",
    "brochure_id": 10,
    "purpose": "company_intro"
}, token=TOKEN)
print(f"  → {status}: {json.dumps(data, ensure_ascii=False)[:200]}")

# 6. 订阅计划数据结构
print("\n[6] GET /api/v1/subscription/plans")
status, data = api("GET", "/api/v1/subscription/plans", token=TOKEN)
if status == 200:
    if isinstance(data, list):
        print(f"  → 列表, 共{len(data)}条")
        for plan in data:
            print(f"     name={plan.get('name','?')} price={plan.get('price','?')} amount={plan.get('amount','?')}")
    else:
        print(f"  → {json.dumps(data, ensure_ascii=False)[:200]}")
else:
    print(f"  → {status}: {json.dumps(data, ensure_ascii=False)[:200]}")

# 7. 分享页
print("\n[7] GET /view/test")
status, data = api("GET", "/view/test")
print(f"  → {status}: {str(data)[:200]}")

# 8. 健康页
print("\n[8] GET /")
status, data = api("GET", "/")
print(f"  → {status}: {str(data)[:200]}")

print("\n===== 验证完成 =====")
