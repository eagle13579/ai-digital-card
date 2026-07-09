#!/usr/bin/env python3
"""完整用户测试脚本 v3"""
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
    print("[FAIL] Login:", json.dumps(login, ensure_ascii=False))
    exit(1)
TOKEN = ""
for k in ["access_token", "token", "auth_token"]:
    if k in login["data"]:
        TOKEN = login["data"][k]
        break
if not TOKEN:
    print("[FAIL] No token key found, keys:", list(login["data"].keys()))
    exit(1)
print("[OK] Login, token:", TOKEN[:30]+"...")
print("")

# 1. User info
r = api("GET", "/api/v1/users/me", token=TOKEN)
d = r.get("data", r.get("error", {}))
print(f"[1] User Info: {r['status']} | name={d.get('name','?')} tier={d.get('membership_tier','?')}")

# 2. Create card
r = api("POST", "/api/v1/business-card/cards", {
    "name": "测试用户", "company": "测试科技", "title": "产品经理",
    "phone": "13900001111", "email": "test@test.com"
}, token=TOKEN)
print(f"[2] Create Card: {r['status']} | {json.dumps(r.get('data',r.get('error',{})), ensure_ascii=False)[:150]}")

# 3. Card list
r = api("GET", "/api/v1/business-card/cards", token=TOKEN)
print(f"[3] Card List: {r['status']} | {str(r.get('data',r.get('error','')))[:150]}")

# 4. Create brochure
r = api("POST", "/api/v1/brochures", {
    "title": "测试产品画册", "description": "产品介绍",
    "template": "modern",
    "pages": [{"title": "封面", "content": "测试科技"}]
}, token=TOKEN)
print(f"[4] Create Brochure: {r['status']}", end="")
br_id = 0
if r["status"] == 200:
    br_id = r["data"].get("id", 0)
    print(f" | id={br_id}")
    # Publish
    r2 = api("POST", f"/api/v1/brochures/{br_id}/publish", token=TOKEN)
    print(f"    Publish: {r2['status']} | {json.dumps(r2.get('data',r2.get('error',{})), ensure_ascii=False)[:150]}")
else:
    print(f" | {json.dumps(r.get('error',{}), ensure_ascii=False)[:150]}")

# 5. Brochure list
r = api("GET", "/api/v1/brochures", token=TOKEN)
print(f"[5] Brochure List: {r['status']} | count={len(r.get('data',[])) if r['status']==200 else '?'}")

# 6. AI Chat
r = api("POST", "/api/v1/ai/deepseek/chat", {
    "message": "你好", "session_id": "test_001"
}, token=TOKEN)
print(f"[6] AI Chat: {r['status']} | {json.dumps(r.get('data',r.get('error',{})), ensure_ascii=False)[:200]}")

# 7. AI Assist Write
r = api("POST", "/api/v1/ai/assist/write", {
    "prompt": "帮我写一段公司简介", "brochure_id": br_id or 1
}, token=TOKEN)
print(f"[7] AI Write: {r['status']} | {json.dumps(r.get('data',r.get('error',{})), ensure_ascii=False)[:200]}")

# 8. AI Config
r = api("GET", "/api/v1/ai/config", token=TOKEN)
print(f"[8] AI Config: {r['status']}")

# 9. Match engine
r = api("POST", "/api/v1/match/engine", {
    "demand": "AI产品设计服务", "tags": ["AI"], "max_results": 5
}, token=TOKEN)
print(f"[9] Match: {r['status']} | {json.dumps(r.get('data',r.get('error',{})), ensure_ascii=False)[:200]}")

# 10. Recommend
r = api("POST", "/api/v1/recommend/personal", {"limit": 3}, token=TOKEN)
print(f"[10] Recommend: {r['status']} | {json.dumps(r.get('data',r.get('error',{})), ensure_ascii=False)[:200]}")

# 11. Membership pricing
r = api("GET", "/api/v1/membership/pricing", token=TOKEN)
print(f"[11] Pricing: {r['status']}")

# 12. Subscription plans
r = api("GET", "/api/v1/subscription/plans", token=TOKEN)
if r["status"] == 200:
    data = r["data"]
    if isinstance(data, list):
        print(f"[12] Plans: OK, {len(data)} plans")
        for plan in data[:3]:
            print(f"     - {plan.get('name','?')}: {plan.get('price',plan.get('amount','?'))}")
    else:
        print(f"[12] Plans: OK, type={type(data).__name__}: {json.dumps(data, ensure_ascii=False)[:200]}")
else:
    print(f"[12] Plans: {r['status']} | {json.dumps(r.get('error',{}), ensure_ascii=False)[:200]}")

# 13. Payment products
r = api("GET", "/api/v1/payment/products", token=TOKEN)
print(f"[13] Products: {r['status']}")

# 14. Knowledge graph
r = api("GET", "/api/v1/knowledge-graph/network/56", token=TOKEN)
print(f"[14] KG Network: {r['status']} | {str(r.get('data',r.get('error','')))[:150]}")


# 15. Public pages
print("")
print("=== Public Pages ===")
for path in ["/health", "/", "/api/health"]:
    r = api("GET", path)
    print(f"  GET {path}: {r['status']}")

# 16. Card-editor page
r = api("GET", "/card-editor")
print(f"  GET /card-editor: {r['status']}")

# 17. Share page
r = api("GET", "/view/test_share_token")
print(f"  GET /view/test_share_token: {r['status']}")

print("")
print("===== DONE =====")
