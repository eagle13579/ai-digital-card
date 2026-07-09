#!/usr/bin/env python3
"""AI数智名片 用户视角测试脚本"""
import json, sys, time
import urllib.request

BASE = "http://localhost:8002"

def api(method, path, data=None, token=None):
    url = f"{BASE}{path}"
    body = json.dumps(data).encode() if data else None
    req = urllib.request.Request(url, data=body, method=method)
    req.add_header("Content-Type", "application/json")
    req.add_header("Accept", "application/json")
    if token:
        req.add_header("Authorization", f"Bearer {token}")
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            raw = resp.read()
            return json.loads(raw)
    except urllib.error.HTTPError as e:
        raw = e.read()
        try:
            return {"_error": e.code, "_body": json.loads(raw)}
        except json.JSONDecodeError:
            return {"_error": e.code, "_raw": raw.decode("utf-8", errors="replace")[:500]}

# ===== 1. 用户注册 =====
print("=" * 60)
print("1️⃣  用户注册")
print("=" * 60)

# 手机号注册
reg = api("POST", "/api/v1/auth/register", {
    "phone": "13900001111",
    "password": "Test123!@#",
    "name": "测试用户",
    "company": "测试科技",
    "title": "产品经理"
})
if reg.get("_error"):
    print(f"❌ 注册失败: {reg}")
    # 可能已存在，尝试登录
    login = api("POST", "/api/v1/auth/login", {
        "phone": "13900001111",
        "password": "Test123!@#"
    })
    print(f"登录结果: {login.get('_error', 'ok')}")
    TOKEN = login.get("access_token", "")
else:
    TOKEN = reg.get("access_token", "")
    print(f"✅ 注册成功: user_id={reg.get('user',{}).get('id')}")

if not TOKEN:
    print("❌ 无法获取token")
    sys.exit(1)

print(f"✅ Token获取成功: {TOKEN[:30]}...")

# ===== 2. 获取用户信息 =====
print("\n" + "=" * 60)
print("2️⃣  用户信息")
print("=" * 60)
me = api("GET", "/api/v1/users/me", token=TOKEN)
if me.get("_error"):
    print(f"❌ 获取用户信息失败: {me}")
else:
    print(f"✅ 用户: {me.get('name')} / {me.get('phone')} / tier={me.get('membership_tier')}")

# ===== 3. 创建名片 =====
print("\n" + "=" * 60)
print("3️⃣  创建名片")
print("=" * 60)
card = api("POST", "/api/v1/business-card/cards", {
    "name": "测试用户",
    "company": "测试科技",
    "title": "产品经理",
    "phone": "13900001111",
    "email": "test@test.com",
    "website": "https://test.com",
    "intro": "专注于AI产品设计",
    "tags": ["AI", "产品设计", "数字化转型"]
}, token=TOKEN)
print(f"创建名片: code={card.get('_error', 'ok')}")
if card.get("_error"):
    print(f"  ❌ 响应: {json.dumps(card, ensure_ascii=False)[:300]}")

cards = api("GET", "/api/v1/business-card/cards", token=TOKEN)
if isinstance(cards, list):
    print(f"名片列表: ✅ {len(cards)} 张")
elif isinstance(cards, dict):
    print(f"名片列表: code={cards.get('_error', 'ok')}")

# ===== 4. 创建画册 =====
print("\n" + "=" * 60)
print("4️⃣  创建画册")
print("=" * 60)
brochure = api("POST", "/api/v1/brochures", {
    "title": "测试公司产品画册",
    "description": "这是我公司的产品介绍",
    "template": "modern",
    "pages": [
        {"title": "封面", "content": "测试科技 - 创新驱动未来"},
        {"title": "关于我们", "content": "我们是一家专注于AI的科技公司"}
    ]
}, token=TOKEN)
print(f"创建画册: code={brochure.get('_error', 'ok')}")
if brochure.get("_error"):
    print(f"  ❌ 响应: {json.dumps(brochure, ensure_ascii=False)[:300]}")
else:
    br_id = brochure.get("id") or ""
    print(f"  ✅ 画册ID: {br_id}")

# ===== 5. AI功能 =====
print("\n" + "=" * 60)
print("5️⃣  AI功能")
print("=" * 60)
chat = api("POST", "/api/v1/ai/deepseek/chat", {
    "message": "你好，请介绍一下你自己",
    "session_id": "test_001"
}, token=TOKEN)
print(f"AI聊天: code={chat.get('_error', 'ok')}")
if not chat.get("_error"):
    reply = chat.get("reply") or chat.get("response") or chat.get("content", "")
    print(f"  ✅ 回复: {str(reply)[:150]}")

write = api("POST", "/api/v1/ai/assist/write", {
    "prompt": "帮我写一段公司简介，AI科技公司",
    "brochure_id": 1
}, token=TOKEN)
print(f"AI写作: code={write.get('_error', 'ok')}")

# ===== 6. 供需匹配 =====
print("\n" + "=" * 60)
print("6️⃣  供需匹配")
print("=" * 60)
match = api("POST", "/api/v1/match/engine", {
    "demand": "需要AI产品设计服务",
    "tags": ["AI", "产品设计"],
    "max_results": 5
}, token=TOKEN)
print(f"匹配引擎: code={match.get('_error', 'ok')}")

rec = api("POST", "/api/v1/recommend/personal", {"limit": 5}, token=TOKEN)
print(f"个性化推荐: code={rec.get('_error', 'ok')}")

# ===== 7. 会员体系 =====
print("\n" + "=" * 60)
print("7️⃣  会员体系")
print("=" * 60)
pricing = api("GET", "/api/v1/membership/pricing", token=TOKEN)
print(f"定价: code={pricing.get('_error', 'ok')}")

plans = api("GET", "/api/v1/subscription/plans", token=TOKEN)
print(f"订阅计划: code={plans.get('_error', 'ok')}")

prods = api("GET", "/api/v1/payment/products", token=TOKEN)
print(f"支付产品: code={prods.get('_error', 'ok')}")

# ===== 8. 公开页面 =====
print("\n" + "=" * 60)
print("8️⃣  公开页面")
print("=" * 60)
h = api("GET", "/health")
print(f"健康检查: {json.dumps(h, ensure_ascii=False)[:100]}")

print("\n" + "=" * 60)
print("✅ 测试完成")
print("=" * 60)
