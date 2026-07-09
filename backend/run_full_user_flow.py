#!/usr/bin/env python3
"""AI数字名片 — 完整用户流程测试 (19个端点)"""
import json, urllib.request, urllib.error, sys, random, time

BASE = "http://localhost:8002"
AI_BASE = "http://localhost:8202"

results = []

def api(method, path, data=None, token=None, base=BASE, timeout=30, raw_text=False):
    url = base + path
    body = json.dumps(data).encode() if data else None
    req = urllib.request.Request(url, data=body, method=method)
    req.add_header("Content-Type", "application/json")
    if token:
        req.add_header("Authorization", "Bearer " + token)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            raw = resp.read()
            if raw_text:
                return {"status": resp.status, "data": raw.decode("utf-8", errors="replace")[:500]}
            out = json.loads(raw) if raw else {}
            return {"status": resp.status, "data": out}
    except urllib.error.HTTPError as e:
        raw = e.read()
        try:
            return {"status": e.code, "error": json.loads(raw)}
        except json.JSONDecodeError:
            return {"status": e.code, "error": raw.decode("utf-8", errors="replace")[:500]}
    except Exception as e:
        return {"status": -1, "error": str(e)}

def record(num, name, result, severity="P3", problem=""):
    status = result.get("status", -1)
    ok = status == 200 or status == 201
    data = result.get("data", result.get("error", ""))
    summary = str(data)[:200] if not ok else str(data)[:150]
    results.append({
        "num": num, "name": name, "status": status,
        "ok": ok, "summary": summary, "severity": severity, "problem": problem
    })
    icon = "✅" if ok else "❌"
    print(f"  {icon} [{status}] {summary[:120]}")

def print_header(title):
    print(f"\n{'='*60}")
    print(f" {title}")
    print(f"{'='*60}")

# ====================================================================
print("=" * 60)
print(" AI数字名片 — 完整用户流程测试")
print("=" * 60)

# ====================================================================
# 1. Health Check
# ====================================================================
print_header("1. Health Check: GET /health")
r = api("GET", "/health")
record(1, "Health Check", r, "P0")

# ====================================================================
# 2. Register new user
# ====================================================================
print_header("2. 注册新用户: POST /api/v1/auth/register")
rand_suffix = random.randint(10000000, 99999999)
phone = f"138{random.randint(10000000, 99999999)}"
reg_data = {
    "phone": phone,
    "password": "Test123!@#",
    "name": f"测试用户_{rand_suffix}",
    "company": "测试科技",
    "title": "产品经理"
}
r = api("POST", "/api/v1/auth/register", reg_data)
record(2, "Register", r, "P0")

TOKEN = ""
USER_ID = 0
if r["status"] == 200:
    data = r["data"]
    TOKEN = data.get("access_token", "")
    user = data.get("user", {})
    USER_ID = user.get("id", 0)
    print(f"    TOKEN: {TOKEN[:30]}...")
    print(f"    USER_ID: {USER_ID}")

# ====================================================================
# 3. Login
# ====================================================================
print_header("3. 登录: POST /api/v1/auth/login")
if not TOKEN:
    # Try default test user
    r = api("POST", "/api/v1/auth/login", {"phone": "13900001111", "password": "Test123!@#"})
    record(3, "Login (default user)", r, "P0")
    if r["status"] == 200:
        TOKEN = r["data"].get("access_token", "")
        USER_ID = r["data"].get("user", {}).get("id", 0)
else:
    r = api("POST", "/api/v1/auth/login", {"phone": phone, "password": "Test123!@#"})
    record(3, "Login", r, "P0")

print(f"    TOKEN: {TOKEN[:30] if TOKEN else 'N/A'}...")
print(f"    USER_ID: {USER_ID}")

if not TOKEN:
    print("\n[FATAL] 无法获取Token，终止测试")
    sys.exit(1)

# ====================================================================
# 4. Get user info
# ====================================================================
print_header("4. 获取用户信息: GET /api/v1/users/me")
r = api("GET", "/api/v1/users/me", token=TOKEN)
record(4, "User Info", r, "P0")

# ====================================================================
# 5. Create business card
# ====================================================================
print_header("5. 创建名片: POST /api/v1/business-card/cards")
card_data = {
    "name": "测试用户",
    "company": "测试科技",
    "title": "产品经理",
    "phone": phone,
    "email": "test@test.com",
    "intro": "专注于AI产品设计",
    "tags": ["AI", "产品设计"]
}
r = api("POST", "/api/v1/business-card/cards", card_data, token=TOKEN)
record(5, "Create Card", r, "P1")

# ====================================================================
# 6. Get card list
# ====================================================================
print_header("6. 获取名片列表: GET /api/v1/business-card/cards")
r = api("GET", "/api/v1/business-card/cards", token=TOKEN)
record(6, "Card List", r, "P1")
# Also try brochures (which is the canonical endpoint)
r2 = api("GET", "/api/v1/brochures", token=TOKEN)
if r2["status"] == 200:
    record(6, "Card List (brochures)", r2, "P1")

# ====================================================================
# 7. Create brochure
# ====================================================================
print_header("7. 创建画册: POST /api/v1/brochures")
brochure_data = {
    "title": "测试产品画册",
    "description": "产品介绍",
    "template": "modern",
    "pages": [{"title": "封面", "content": "测试科技公司简介"}]
}
r = api("POST", "/api/v1/brochures", brochure_data, token=TOKEN)
record(7, "Create Brochure", r, "P1")
BR_ID = 0
if r["status"] == 200:
    data = r["data"]
    BR_ID = data.get("id", 0) or data.get("brochure", {}).get("id", 0)
    print(f"    Brochure ID: {BR_ID}")

# ====================================================================
# 8. Get brochure list
# ====================================================================
print_header("8. 获取画册列表: GET /api/v1/brochures")
r = api("GET", "/api/v1/brochures", token=TOKEN)
record(8, "Brochure List", r, "P1")

# ====================================================================
# 9. Publish brochure
# ====================================================================
print_header("9. 发布画册: POST /api/v1/brochures/{id}/publish")
if BR_ID:
    r = api("POST", f"/api/v1/brochures/{BR_ID}/publish", token=TOKEN)
else:
    r = api("POST", "/api/v1/brochures/1/publish", token=TOKEN)
record(9, "Publish Brochure", r, "P1")
SHARE_TOKEN = ""
if r["status"] == 200:
    SHARE_TOKEN = r["data"].get("share_token", "")
    print(f"    Share Token: {SHARE_TOKEN}")

# ====================================================================
# 10. Get public share page
# ====================================================================
print_header("10. 获取公开分享页: GET /view/{share_token}")
if SHARE_TOKEN:
    r = api("GET", f"/view/{SHARE_TOKEN}", raw_text=True)
else:
    r = api("GET", "/view/test123", raw_text=True)
record(10, "Share Page", r, "P1")

# ====================================================================
# 11. AI DeepSeek Chat
# ====================================================================
print_header("11. AI DeepSeek聊天: POST /api/v1/ai/deepseek/chat")
r = api("POST", "/api/v1/ai/deepseek/chat", {
    "messages": [{"role": "user", "content": "你好"}],
    "temperature": 0.7,
    "max_tokens": 512
}, token=TOKEN)
record(11, "AI DeepSeek Chat", r, "P2",
       "需配置DEEPSEEK_API_KEY，否则返回401/5xx")

# ====================================================================
# 12. AI Writing Assistant
# ====================================================================
print_header("12. AI写作助手: POST /api/v1/ai/assist/write")
r = api("POST", "/api/v1/ai/assist/write", {
    "purpose": "bio",
    "name": "测试用户",
    "position": "产品经理",
    "company": "测试科技",
    "keywords": "AI,产品设计"
}, token=TOKEN)
record(12, "AI Writing Assist", r, "P2",
       "需要配置AI API Key")

# ====================================================================
# 13. Recommend system
# ====================================================================
print_header("13. 推荐系统: POST /api/v1/recommend/personal")
r = api("POST", "/api/v1/recommend/personal", {"top_k": 5, "strategy": "hybrid"}, token=TOKEN)
record(13, "Recommend Personal", r, "P1")

# ====================================================================
# 14. Knowledge Graph
# ====================================================================
print_header("14. 知识图谱: GET /api/v1/knowledge-graph/network/{id}")
target_id = USER_ID if USER_ID else 1
r = api("GET", f"/api/v1/knowledge-graph/network/{target_id}", token=TOKEN)
record(14, "Knowledge Graph", r, "P2")

# ====================================================================
# 15. Subscription Plans
# ====================================================================
print_header("15. 会员定价: GET /api/v1/subscription/plans")
r = api("GET", "/api/v1/subscription/plans", token=TOKEN)
record(15, "Subscription Plans", r, "P0")

# ====================================================================
# 16. OCR Scan (ai_service on port 8202)
# ====================================================================
print_header("16. OCR扫描: POST /ai/ocr (ai_service:8202)")
r = api("POST", "/ai/ocr", {
    "image_path": "",
    "use_external_ocr": False,
    "extract_contacts": True,
    "extract_business": False
}, base=AI_BASE, timeout=10)
record(16, "OCR Scan", r, "P2",
       "OCR服务在ai_service(8202)，需要有效文件路径")

# ====================================================================
# 17. Match semantic search
# ====================================================================
print_header("17. 语义搜索: POST /api/v1/match/semantic-search")
r = api("POST", "/api/v1/match/semantic-search", {
    "query": "AI产品设计",
    "top_k": 5,
    "min_score": 0.0
}, token=TOKEN)
record(17, "Semantic Search", r, "P1")

# ====================================================================
# 18. A/B Test
# ====================================================================
print_header("18. A/B测试: GET /api/v1/ab-test/experiments")
r = api("GET", "/api/v1/ab-test/experiments", token=TOKEN)
record(18, "AB Test Experiments", r, "P2")

# ====================================================================
# 19. SAG Pipeline
# ====================================================================
print_header("19. SAG管道: POST /api/v1/ai/sag/analyze")
r = api("POST", "/api/v1/ai/sag/analyze", {
    "mode": "quality_review",
    "content": {"text": "测试内容"},
    "depth": "fast",
    "temperature": 0.5
}, token=TOKEN)
record(19, "SAG Analyze", r, "P2",
       "需要AI API Key和SAG引擎支持")

# ====================================================================
# Summary
# ====================================================================
print("\n" + "=" * 60)
print(" 📊 测试结果汇总")
print("=" * 60)

p0 = [r for r in results if r["severity"] == "P0"]
p1 = [r for r in results if r["severity"] == "P1"]
p2 = [r for r in results if r["severity"] == "P2"]
p3 = [r for r in results if r["severity"] == "P3"]
ok_count = sum(1 for r in results if r["ok"])
fail_count = len(results) - ok_count

print(f"\n总端点: {len(results)}")
print(f"通过: {ok_count}/{len(results)} ({100*ok_count//len(results)}%)")
print(f"失败: {fail_count}")
print(f"  P0 (阻塞): {len(p0)}")
print(f"  P1 (严重): {len(p1)}")
print(f"  P2 (一般): {len(p2)}")
print(f"  P3 (轻微): {len(p3)}")

print("\n详细结果:")
for r in sorted(results, key=lambda x: x["num"]):
    icon = "✅" if r["ok"] else "❌"
    sev = f"[{r['severity']}]" if not r["ok"] else ""
    print(f"  {icon} #{r['num']:2d} {r['name']:35s} HTTP {r['status']:3d} {sev}")
    if not r["ok"]:
        snippet = r['summary'][:100]
        print(f"        ↳ {snippet}")
        if r["problem"]:
            print(f"        ↳ 问题: {r['problem']}")

with open("full_flow_results.json", "w") as f:
    json.dump(results, f, ensure_ascii=False, indent=2)
print(f"\n结果已保存到 full_flow_results.json")
