#!/usr/bin/env python3
"""完整用户测试脚本 v2"""
import json, urllib.request, urllib.error

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
        with urllib.request.urlopen(req, timeout=15) as resp:
            return {"status": resp.status, "data": json.loads(resp.read())}
    except urllib.error.HTTPError as e:
        raw = e.read()
        try:
            return {"status": e.code, "error": json.loads(raw)}
        except json.JSONDecodeError:
            return {"status": e.code, "error": raw.decode()[:500]}
    except Exception as e:
        return {"status": -1, "error": str(e)}

# Login
login = api("POST", "/api/v1/auth/login", {"phone": "13900001111", "password": "Test123!@#"})
if login["status"] != 200:
    print(f"FAIL login: {login}")
    exit(1)
TOKEN=*** en", "")
for k in ["access_token", "token", "auth_token"]:
    if k in login["data"]:
        TOKEN=login.....n"]
        break
if not TOKEN:
    print(f"KEYS: {list(login['data'].keys())}")
    exit(1)
print(f"LOGIN OK token: {TOKEN[:30]}...")

# 1. User info
me = api("GET", "/api/v1/users/me", token=TOKEN)
print(f"[1] USER INFO: {me['status']} name={me.get('data',{}).get('name','?')} tier={me.get('data',{}).get('membership_tier','?')}")

# 2. Create card
print("[2] CREATE CARD")
card = api("POST", "/api/v1/business-card/cards", {
    "name": "测试用户", "company": "测试科技", "title": "产品经理",
    "phone": "13900001111", "email": "test@test.com"
}, token=TOKEN)
print(f"    → {card['status']}: {str(card.get('data', card.get('error', '')))[:200]}")

# 3. Create brochure
print("[3] CREATE BROCHURE")
br = api("POST", "/api/v1/brochures", {
    "title": "测试产品画册", "description": "产品介绍", "template": "modern",
    "pages": [{"title": "封面", "content": "测试科技"}]
}, token=TOKEN)
print(f"    → {br['status']}: {str(br.get('data', br.get('error', '')))[:200]}")
br_id = br.get("data", {}).get("id") if br["status"] == 200 else None
if br_id:
    pub = api("POST", f"/api/v1/brochures/{br_id}/publish", token=TOKEN)
    print(f"    PUBLISH → {pub['status']}: {str(pub.get('data', pub.get('error', '')))[:200]}")

# 4. AI chat
print("[4] AI CHAT")
chat = api("POST", "/api/v1/ai/deepseek/chat", {
    "message": "你好", "session_id": "test_001"
}, token=TOKEN)
print(f"    → {chat['status']}: {str(chat.get('data', chat.get('error', '')))[:300]}")

# Also try assist write
write = api("POST", "/api/v1/ai/assist/write", {
    "prompt": "写一段公司简介", "brochure_id": 1
}, token=TOKEN)
print(f"    AI WRITE → {write['status']}: {str(write.get('data', write.get('error', '')))[:200]}")

# 5. Match
print("[5] MATCH")
match = api("POST", "/api/v1/match/engine", {
    "demand": "AI产品设计", "tags": ["AI"], "max_results": 5
}, token=TOKEN)
print(f"    → {match['status']}: {str(match.get('data', match.get('error', '')))[:200]}")

# 6. Recommend
print("[6] RECOMMEND")
rec = api("POST", "/api/v1/recommend/personal", {"limit": 3}, token=TOKEN)
print(f"    → {rec['status']}: {str(rec.get('data', rec.get('error', '')))[:200]}")

# 7. Membership
print("[7] MEMBERSHIP")
p = api("GET", "/api/v1/membership/pricing", token=TOKEN)
print(f"    PRICING → {p['status']}")
sp = api("GET", "/api/v1/subscription/plans", token=TOKEN)
print(f"    PLANS → {sp['status']}: type={type(sp.get('data',sp.get('error',[]))).__name__}")

# 8. Knowledge graph
print("[8] KNOWLEDGE GRAPH")
kg = api("GET", "/api/v1/knowledge-graph/network/56", token=TOKEN)
print(f"    → {kg['status']}: {str(kg.get('data', kg.get('error', '')))[:200]}")

# 9. Share page
print("[9] SHARE PAGE")
share = api("GET", "/view/test_token")
print(f"    → {share['status']}")

# 10. Health
h = api("GET", "/health")
print(f"[10] HEALTH: {json.dumps(h.get('data',{}))[:100]}")

print("\n===== DONE =====")
