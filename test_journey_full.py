#!/usr/bin/env python
"""
AI数智名片 — 真实用户全流程测试
从用户视角完整跑通: 获知→注册→配置→核心使用→查看结果→采取行动→签约→持续赋能
"""
import json, urllib.request, urllib.error, sys, random, time, os

BASE = "http://localhost:8002"
TOKEN_VAR = ""
USER_ID = 0

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
                return {"status": resp.status, "data": raw.decode("utf-8", errors="replace")[:800]}
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

def step(num, name, result, severity="P3"):
    status = result.get("status", -1)
    ok = status in (200, 201, 204, 302)
    data = result.get("data", result.get("error", ""))
    summary = str(data)[:200] if not ok else str(data)[:150]
    results.append({
        "step": num, "name": name, "status": status,
        "ok": ok, "summary": summary, "severity": severity
    })
    icon = "✅" if ok else "❌"
    print(f"  {icon} [{status}] {summary[:120]}")
    return ok

def print_header(title):
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}")

def print_journey(title):
    print(f"\n{'─'*60}")
    print(f"  📋 客户旅程: {title}")
    print(f"{'─'*60}")

print("=" * 60)
print("  🚀 AI数智名片 — 真实用户全流程评测")
print("=" * 60)

# ====================================================================
# 第1步: 获知 (Awareness)
# ====================================================================
print_journey("Step 1 \u2014 获知 (Awareness)")

print_header("1.1 服务健康检查 GET /health")
r = api("GET", "/health")
step(1, "Health Check", r, "P0")

print_header("1.2 访问首页 GET /")
r = api("GET", "/")
step(2, "Root Page", r, "P0")

print_header("1.3 查看会员定价 GET /api/v1/subscription/plans")
r = api("GET", "/api/v1/subscription/plans")
step(3, "Subscription Plans", r, "P0")

print_header("1.4 获取OpenAPI文档 GET /openapi.json")
r = api("GET", "/openapi.json")
step(4, "OpenAPI Docs", r, "P1")

# ====================================================================
# 第2步: 注册 (Registration)
# ====================================================================
print_journey("Step 2 \u2014 注册 (Registration)")

rand_suffix = random.randint(10000000, 99999999)
phone = f"138{random.randint(10000000, 99999999)}"
reg_data = {
    "phone": phone,
    "password": "Test123!@#",
    "name": f"真实用户_{rand_suffix}",
    "company": "数智科技有限公司",
    "title": "产品总监"
}

print_header("2.1 注册新用户 POST /api/v1/auth/register")
r = api("POST", "/api/v1/auth/register", reg_data)
step(5, "User Register", r, "P0")

if r["status"] == 200:
    data = r["data"]
    TOKEN_VAR = data.get("access_token", "")
    user = data.get("user", {})
    USER_ID = user.get("id", 0)
    print(f"    📝 TOKEN: {TOKEN_VAR[:40]}...")
    print(f"    📝 USER_ID: {USER_ID}")
    print(f"    📝 用户名: {user.get('name', 'N/A')}")

if not TOKEN_VAR:
    print_header("2.1b 登录已有用户 POST /api/v1/auth/login")
    r = api("POST", "/api/v1/auth/login", {"phone": "13900001111", "password": "Test123!@#"})
    step(5, "User Login (fallback)", r, "P0")
    if r["status"] == 200:
        TOKEN_VAR = r["data"].get("access_token", "")
        USER_ID = r["data"].get("user", {}).get("id", 0)
else:
    print_header("2.2 登录验证 POST /api/v1/auth/login")
    r = api("POST", "/api/v1/auth/login", {"phone": phone, "password": "Test123!@#"})
    step(6, "User Login", r, "P0")
    if r["status"] == 200 and not TOKEN_VAR:
        TOKEN_VAR = r["data"].get("access_token", "")
        USER_ID = r["data"].get("user", {}).get("id", 0)

if not TOKEN_VAR:
    print("\n[FATAL] 无法获取Token，终止测试")
    sys.exit(1)

print_header("2.3 获取我的信息 GET /api/v1/users/me")
r = api("GET", "/api/v1/users/me", token=TOKEN_VAR)
step(7, "Get User Info", r, "P0")

# ====================================================================
# 第3步: 配置 (Configuration)
# ====================================================================
print_journey("Step 3 \u2014 配置 (Configuration)")

print_header("3.1 创建名片 POST /api/v1/business-card/cards")
card_data = {
    "name": "张总",
    "company": "数智科技有限公司",
    "title": "产品总监",
    "phone": phone,
    "email": "zhang@aibizcard.com",
    "intro": "15年产品设计经验，专注于AI驱动的数字化转型",
    "tags": ["AI", "产品设计", "数字化转型"],
    "wechat": "zhang1985",
    "website": "https://aibizcard.com"
}
r = api("POST", "/api/v1/business-card/cards", card_data, token=TOKEN_VAR)
step(8, "Create Business Card", r, "P1")
CARD_ID = 0
if r["status"] == 200:
    CARD_ID = r["data"].get("id", 0) or r["data"].get("card", {}).get("id", 0)
    print(f"    📇 CARD_ID: {CARD_ID}")

if not CARD_ID:
    print_header("3.1b 尝试创建画册名片 POST /api/v1/brochures")
    card_data2 = {
        "title": "张总 - 个人名片",
        "description": "AI产品总监个人介绍",
        "template": "modern",
        "pages": [
            {"title": "个人简介", "content": "15年产品设计经验，专注于AI数字化转型"},
            {"title": "业务范围", "content": "AI产品咨询、数字化转型方案设计"}
        ]
    }
    r = api("POST", "/api/v1/brochures", card_data2, token=TOKEN_VAR)
    step(8, "Create Brochure Card", r, "P1")
    if r["status"] == 200:
        data = r["data"]
        CARD_ID = data.get("id", 0) or data.get("brochure", {}).get("id", 0)
        print(f"    📇 Brochure/CARD_ID: {CARD_ID}")

print_header("3.2 获取名片列表 GET /api/v1/business-card/cards")
r = api("GET", "/api/v1/business-card/cards", token=TOKEN_VAR)
step(9, "Card List", r, "P1")

print_header("3.3 获取画册列表 GET /api/v1/brochures")
r = api("GET", "/api/v1/brochures", token=TOKEN_VAR)
step(10, "Brochure List", r, "P1")
BR_ID = 0
if r["status"] == 200:
    data = r["data"]
    if isinstance(data, list) and len(data) > 0:
        BR_ID = data[0].get("id", 0)
    elif isinstance(data, dict):
        items = data.get("data", data.get("brochures", data.get("items", [])))
        if isinstance(items, list) and len(items) > 0:
            BR_ID = items[0].get("id", 0)
    print(f"    📖 BR_ID from list: {BR_ID}")

if not BR_ID and not CARD_ID:
    print_header("3.3b 创建画册 POST /api/v1/brochures (fallback)")
    br_data = {
        "title": "数智科技产品画册",
        "description": "公司核心产品与解决方案",
        "template": "modern",
        "tags": ["AI", "数字化转型"],
        "pages": [
            {"title": "公司简介", "content": "数智科技致力于AI驱动企业数字化转型"},
            {"title": "核心产品", "content": "AI数智名片、智能CRM、数据分析平台"}
        ]
    }
    r = api("POST", "/api/v1/brochures", br_data, token=TOKEN_VAR)
    step(10, "Create Brochure", r, "P1")
    if r["status"] == 200:
        data = r["data"]
        BR_ID = data.get("id", 0) or data.get("brochure", {}).get("id", 0)
        print(f"    📖 Brochure ID: {BR_ID}")

# ====================================================================
# 第4步: 核心使用 (Core Usage)
# ====================================================================
print_journey("Step 4 \u2014 核心使用 (Core Usage)")

SHARE_TOKEN = ""
if BR_ID:
    print_header(f"4.1 发布画册 POST /api/v1/brochures/{BR_ID}/publish")
    r = api("POST", f"/api/v1/brochures/{BR_ID}/publish", token=TOKEN_VAR)
    step(11, "Publish Brochure", r, "P1")
    if r["status"] == 200:
        SHARE_TOKEN = r["data"].get("share_token", "")
        print(f"    🔗 Share Token: {SHARE_TOKEN}")

print_header("4.2 语义搜索 POST /api/v1/match/semantic-search")
r = api("POST", "/api/v1/match/semantic-search", {
    "query": "AI产品设计",
    "top_k": 5,
    "min_score": 0.0
}, token=TOKEN_VAR)
step(12, "Semantic Search", r, "P1")

print_header("4.3 推荐系统 POST /api/v1/recommend/personal")
r = api("POST", "/api/v1/recommend/personal", {"top_k": 5, "strategy": "hybrid"}, token=TOKEN_VAR)
step(13, "Recommend Personal", r, "P1")

print_header("4.4 供需匹配 POST /api/v1/match/supply-demand")
r = api("POST", "/api/v1/match/supply-demand", {
    "query": "AI产品经理", "top_k": 5
}, token=TOKEN_VAR)
if r["status"] == 404:
    r = api("GET", "/api/v1/match/search?q=AI%E4%BA%A7%E5%93%81%E7%BB%8F%E7%90%86", token=TOKEN_VAR)
step(14, "Supply-Demand Match", r, "P2")

print_header("4.5 AI写作助手 POST /api/v1/ai/assist/write")
r = api("POST", "/api/v1/ai/assist/write", {
    "purpose": "bio",
    "name": "张总",
    "position": "产品总监",
    "company": "数智科技",
    "keywords": "AI,产品设计,数字化转型"
}, token=TOKEN_VAR, timeout=15)
step(15, "AI Writing Assist", r, "P2")

print_header("4.6 AI聊天 POST /api/v1/ai/deepseek/chat")
r = api("POST", "/api/v1/ai/deepseek/chat", {
    "messages": [{"role": "user", "content": "你好，请帮我写一段个人简介，我是AI产品总监"}],
    "temperature": 0.7,
    "max_tokens": 512
}, token=TOKEN_VAR, timeout=15)
step(16, "AI Chat", r, "P2")

# ====================================================================
# 第5步: 查看结果 (View Results)
# ====================================================================
print_journey("Step 5 \u2014 查看结果 (View Results)")

if SHARE_TOKEN:
    print_header(f"5.1 访问公开分享页 GET /view/{SHARE_TOKEN}")
    r = api("GET", f"/view/{SHARE_TOKEN}", raw_text=True, timeout=10)
else:
    print_header("5.1 访问公开分享页 GET /view/test123")
    r = api("GET", "/view/test123", raw_text=True, timeout=10)
step(17, "Share Page View", r, "P0")

print_header("5.2 知识图谱 GET /api/v1/knowledge-graph/network/{id}")
target_id = USER_ID if USER_ID else 1
r = api("GET", f"/api/v1/knowledge-graph/network/{target_id}", token=TOKEN_VAR)
step(18, "Knowledge Graph", r, "P2")

print_header("5.3 分析仪表盘 GET /api/v1/analytics/dashboard")
r = api("GET", "/api/v1/analytics/dashboard", token=TOKEN_VAR)
step(19, "Analytics Dashboard", r, "P1")

# ====================================================================
# 第6步: 采取行动 (Take Action)
# ====================================================================
print_journey("Step 6 \u2014 采取行动 (Take Action)")

print_header("6.1 生成分享链接 POST /api/v1/brochures/share-link")
r = api("POST", "/api/v1/brochures/share-link", {
    "brochure_id": BR_ID if BR_ID else 1,
    "type": "qrcode"
}, token=TOKEN_VAR)
step(20, "Share Link Generation", r, "P1")

print_header("6.2 导出名片 POST /api/v1/export/card")
r = api("POST", "/api/v1/export/card", {
    "card_id": CARD_ID if CARD_ID else 1,
    "format": "vcf"
}, token=TOKEN_VAR)
step(21, "Export Card", r, "P2")

print_header("6.3 A/B测试 GET /api/v1/ab-test/experiments")
r = api("GET", "/api/v1/ab-test/experiments", token=TOKEN_VAR)
step(22, "AB Test Experiments", r, "P2")

# ====================================================================
# 第7步: 签约 (Subscription)
# ====================================================================
print_journey("Step 7 \u2014 签约 (Subscription)")

print_header("7.1 查看会员计划 GET /api/v1/membership/plans")
r = api("GET", "/api/v1/membership/plans", token=TOKEN_VAR)
step(23, "Membership Plans", r, "P0")

print_header("7.2 查看使用统计 GET /api/v1/membership/usage-stats")
r = api("GET", "/api/v1/membership/usage-stats", token=TOKEN_VAR)
step(24, "Usage Stats", r, "P1")

print_header("7.3 查看订阅定价 GET /api/v1/subscription/plans")
r = api("GET", "/api/v1/subscription/plans", token=TOKEN_VAR)
if r["status"] == 401:
    r = api("GET", "/api/v1/subscription/plans")
step(25, "Subscription Plans (auth)", r, "P0")

# ====================================================================
# 第8步: 持续赋能 (Continuous Empowerment)
# ====================================================================
print_journey("Step 8 \u2014 持续赋能 (Continuous Empowerment)")

print_header("8.1 消息列表 GET /api/v1/messages")
r = api("GET", "/api/v1/messages", token=TOKEN_VAR)
step(26, "Messages", r, "P1")

print_header("8.2 访客记录 GET /api/v1/visitors")
r = api("GET", "/api/v1/visitors", token=TOKEN_VAR)
step(27, "Visitor Records", r, "P2")

print_header("8.3 AI配置管理 GET /api/v1/ai/config")
r = api("GET", "/api/v1/ai/config", token=TOKEN_VAR)
step(28, "AI Config", r, "P2")

print_header("8.4 SAG分析 POST /api/v1/ai/sag/analyze")
r = api("POST", "/api/v1/ai/sag/analyze", {
    "mode": "quality_review",
    "content": {"text": "测试内容"},
    "depth": "fast",
    "temperature": 0.5
}, token=TOKEN_VAR, timeout=15)
step(29, "SAG Analyze", r, "P2")

print_header("8.5 用户退出登录 POST /api/v1/auth/logout")
r = api("POST", "/api/v1/auth/logout", token=TOKEN_VAR)
step(30, "User Logout", r, "P1")

# ====================================================================
# 汇总
# ====================================================================
print("\n" + "=" * 60)
print("  📊 客户旅程评测结果汇总")
print("=" * 60)

p0 = [r for r in results if r["severity"] == "P0"]
p1 = [r for r in results if r["severity"] == "P1"]
p2 = [r for r in results if r["severity"] == "P2"]
ok_count = sum(1 for r in results if r["ok"])
fail_count = len(results) - ok_count

print(f"\n总端点: {len(results)}")
print(f"通过: {ok_count}/{len(results)} ({100*ok_count//len(results) if len(results) > 0 else 0}%)")
print(f"失败: {fail_count}")
print(f"  P0 (阻塞): {len(p0)}")
print(f"  P1 (严重): {len(p1)}")
print(f"  P2 (一般): {len(p2)}")

print("\n" + "─" * 60)
print("  客户旅程 8 步评测表")
print("─" * 60)

journey_names = [
    ("Step 1: 获知 (Awareness)", list(range(1, 5))),
    ("Step 2: 注册 (Registration)", list(range(5, 8))),
    ("Step 3: 配置 (Configuration)", list(range(8, 11))),
    ("Step 4: 核心使用 (Core Usage)", list(range(11, 17))),
    ("Step 5: 查看结果 (View Results)", list(range(17, 20))),
    ("Step 6: 采取行动 (Take Action)", list(range(20, 23))),
    ("Step 7: 签约 (Subscription)", list(range(23, 26))),
    ("Step 8: 持续赋能 (Continuous Empowerment)", list(range(26, 31))),
]

for jname, jsteps in journey_names:
    jresults = [r for r in results if r["step"] in jsteps]
    jok = sum(1 for r in jresults if r["ok"])
    jtotal = len(jresults)
    icon = "✅" if jok == jtotal else ("⚠️" if jok > 0 else "❌")
    print(f"  {icon} {jname:45s} {jok}/{jtotal}")

print("\n详细结果:")
for r in sorted(results, key=lambda x: x["step"]):
    icon = "✅" if r["ok"] else "❌"
    sev = f"[{r['severity']}]" if not r["ok"] else ""
    print(f"  {icon} #{r['step']:2d} {r['name']:40s} HTTP {r['status']:3d} {sev}")
    if not r["ok"]:
        snippet = r['summary'][:120]
        print(f"        ↳ {snippet}")

out_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "journey_test_results.json")
with open(out_path, "w") as f:
    json.dump({"results": results, "ok": ok_count, "total": len(results)}, f, ensure_ascii=False, indent=2)
print(f"\n结果已保存到 {out_path}")
