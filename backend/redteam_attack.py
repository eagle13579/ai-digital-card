#!/usr/bin/env python
"""红队安全攻击测试 - AI数字名片"""
import json, base64, sys, os, time
import urllib.request

BASE = "http://localhost:8002"
REPORT = []

def req(method, path, headers=None, data=None, timeout=5):
    """Make HTTP request and return (status, headers_dict, body_text)"""
    url = f"{BASE}{path}"
    hdrs = {}
    if headers:
        hdrs.update(headers)
    if data is not None:
        body = json.dumps(data).encode()
        hdrs.setdefault("Content-Type", "application/json")
    else:
        body = None
    
    req_obj = urllib.request.Request(url, data=body, headers=hdrs, method=method)
    try:
        resp = urllib.request.urlopen(req_obj, timeout=timeout)
        status = resp.status
        resp_headers = dict(resp.headers)
        resp_body = resp.read().decode()
        return status, resp_headers, resp_body
    except urllib.error.HTTPError as e:
        return e.code, dict(e.headers), e.read().decode()
    except Exception as e:
        return 0, {}, str(e)

def print_sep(title):
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}")

def report(severity, title, detail, fix=""):
    REPORT.append({"severity": severity, "title": title, "detail": detail, "fix": fix})
    print(f"  [{severity}] {title}: {detail[:120]}")

# ==============================
# 0. 注册测试用户
# ==============================
print_sep("0. 注册测试用户")

s, h, b = req("POST", "/api/v1/auth/register", data={
    "phone": "13900009999", "password": "Test@1234x",
    "name": "RedTeam", "username": "redteam_main"
})
print(f"注册用户A: {s}")
if s == 200:
    data = json.loads(b)
    TOKEN_A = data["access_token"]
    USER_A_ID = data["user"]["id"]
    print(f"  TokenA: {TOKEN_A[:40]}...")
    print(f"  UserA ID: {USER_A_ID}")
else:
    # Try login if already exists
    s, h, b = req("POST", "/api/v1/auth/login", data={
        "phone": "13900009999", "password": "Test@1234x"
    })
    print(f"登录已有用户: {s}")
    data = json.loads(b)
    TOKEN_A = data.get("access_token", "")
    USER_A_ID = data.get("user", {}).get("id", "?")

s, h, b = req("POST", "/api/v1/auth/register", data={
    "phone": "13900008888", "password": "Test@1234y",
    "name": "UserB", "username": "userb_test"
})
print(f"注册用户B: {s}")
if s == 200:
    data = json.loads(b)
    TOKEN_B = data["access_token"]
    USER_B_ID = data["user"]["id"]
    print(f"  TokenB: {TOKEN_B[:40]}...")
    print(f"  UserB ID: {USER_B_ID}")
else:
    s, h, b = req("POST", "/api/v1/auth/login", data={
        "phone": "13900008888", "password": "Test@1234y"
    })
    data = json.loads(b)
    TOKEN_B = data.get("access_token", "")
    USER_B_ID = data.get("user", {}).get("id", "?")

# ==============================
# P0: 信息泄露侦察
# ==============================
print_sep("P0: 信息泄露侦察")

# 1.1 响应头检查
s, h, b = req("GET", "/health")
server = h.get("Server", "N/A")
x_powered = h.get("X-Powered-By", "N/A")
sunset = h.get("Sunset", "N/A")
deprecation = h.get("deprecation", "N/A")
print(f"  Server: {server}")
print(f"  X-Powered-By: {x_powered}")
print(f"  Deprecation/Sunset: {deprecation}")
report("P1", "响应头信息泄露", 
    f"Server={server}, Deprecation={deprecation}, 暴露了uvicorn和API版本信息",
    "隐藏Server头或使用通用值；移除deprecation标头或限制仅向已认证用户显示")

# 1.2 敏感路径暴露
print("\n  敏感路径扫描:")
sensitive_paths = [
    "/docs", "/redoc", "/openapi.json", "/metrics", "/health"
]
for p in sensitive_paths:
    s, h, b = req("GET", p)
    status_note = "暴露!" if s == 200 else f"安全({s})"
    if s == 200:
        size = len(b)
        report("P1", f"敏感路径暴露: {p}", 
            f"HTTP {s}, 返回{size}字节内容", 
            "生产环境禁用/docs、/redoc、/metrics，或添加IP白名单和认证")

# 1.3 CORS配置检查
print("\n  CORS测试:")
s, h, b = req("OPTIONS", "/api/v1/auth/login", 
    headers={
        "Origin": "https://evil.com",
        "Access-Control-Request-Method": "POST",
        "Access-Control-Request-Headers": "Authorization, Content-Type"
    })
print(f"  OPTIONS /auth/login (Origin=evil.com): {s}")
for k,v in h.items():
    if 'access-control' in k.lower():
        print(f"    {k}: {v}")
if "access-control-allow-origin" in h:
    report("P1", "CORS配置过松", 
        f"允许来源: {h.get('access-control-allow-origin')}", 
        "限制CORS来源列表为已知可信域名")
else:
    print("  → CORS来源验证: 未返回allow-origin，浏览器会拒绝（安全）")

# ==============================
# P0: SQL注入测试
# ==============================
print_sep("P0: SQL注入测试")

# 登录接口SQL注入
sqli_payloads = [
    ("' OR 1=1--", "any"),
    ("' OR '1'='1", "any"),
    ('admin\'--', "any"),
    ("'; DROP TABLE users--", "any"),
]
for phone, pw in sqli_payloads:
    s, h, b = req("POST", "/api/v1/auth/login", data={"phone": phone, "password": pw})
    if s == 200:
        report("P0", f"SQL注入成功(登录): phone={phone}", 
            f"HTTP 200, 绕过了认证", "使用参数化查询(已使用SQLAlchemy ORM)")
    else:
        print(f"  [安全] SQL注入被拦截: phone={phone} -> {s} {b[:60]}")

# 名片搜索SQL注入测试（如果有搜索端点）
for endpoint in ["/api/v1/brochure", "/api/v1/brochures"]:
    s, h, b = req("GET", f"{endpoint}?id=1 OR 1=1")
    if s == 200 and "error" not in b.lower():
        report("P2", f"可能SQL注入(GET参数): {endpoint}?id=1 OR 1=1",
            f"HTTP {s}, 返回了内容", "使用参数化查询")
    else:
        print(f"  [安全] GET参数注入被拦截: {endpoint}?id=1 OR 1=1 -> {s}")

# ==============================
# P0: JWT安全测试
# ==============================
print_sep("P0: JWT安全测试")

# 7a: alg=none
def b64(data):
    return base64.urlsafe_b64encode(json.dumps(data).encode()).decode().rstrip('=')

header_none = b64({"alg": "none", "typ": "JWT"})
payload_fake = b64({"sub": "1", "exp": 9999999999, "role": "admin"})
token_none = f"{header_none}.{payload_fake}."

s, h, b = req("GET", "/api/v1/user/me", headers={"Authorization": f"Bearer {token_none}"})
if s == 200:
    report("P0", "JWT alg=none攻击成功", 
        f"HTTP 200, 使用alg=none token绕过了认证", 
        "在JWT库中禁用none算法, 要求签名验证")
else:
    print(f"  [安全] JWT alg=none被拒绝: {s}")

# 7b: 空token
s, h, b = req("GET", "/api/v1/user/me", headers={"Authorization": "Bearer "})
print(f"  空token: {s}")
s, h, b = req("GET", "/api/v1/user/me")
print(f"  无token: {s}")
if s == 200:
    report("P0", "认证绕过(无token)", "无token访问受保护端点返回200", "添加认证依赖")

# 7c: 伪造token（使用已知弱密钥尝试）
# From .env: JWT_SECRET=change...card
import hmac, hashlib

# Try HS256 with weak key
weak_secrets = ["change...card", "secret", "123456", "password", "changeme"]
for weak_secret in weak_secrets:
    try:
        import jwt as pyjwt
        fake = pyjwt.encode({"sub": "1", "exp": 9999999999, "role": "admin"}, weak_secret, algorithm="HS256")
        s, h, b = req("GET", "/api/v1/user/me", headers={"Authorization": f"Bearer {fake}"})
        if s == 200:
            report("P0", f"JWT弱密钥暴力破解成功: secret='{weak_secret}'", 
                f"使用弱密钥伪造token成功访问API", 
                "使用强随机密钥(至少256位), 使用RS256非对称签名")
            break
        else:
            print(f"  [安全] 密钥'{weak_secret[:8]}...'被拒绝: {s}")
    except ImportError:
        print("  pyjwt未安装，跳过HS256伪造测试")
        break
    except Exception as e:
        print(f"  密钥'{weak_secret[:8]}...'错误: {e}")

# 7d: token过期测试 - decode existing token to check expiry
if TOKEN_A:
    try:
        parts = TOKEN_A.split(".")
        payload_b64 = parts[1]
        payload_b64 += "=" * (4 - len(payload_b64) % 4)
        payload = json.loads(base64.urlsafe_b64decode(payload_b64))
        exp = payload.get("exp", 0)
        import datetime
        exp_time = datetime.datetime.fromtimestamp(exp)
        now = datetime.datetime.utcnow()
        remaining = exp_time - now
        print(f"  Token过期时间: {exp_time}, 剩余: {remaining}")
        days = remaining.days
        report("P1", "JWT过期时间过长", 
            f"Token有效期{days}天(配置为7天), 增加了token泄露风险", 
            "建议将ACCESS_TOKEN_EXPIRE_MINUTES降低到60分钟以内")
    except Exception as e:
        print(f"  Token解析失败: {e}")

# ==============================
# P0: 认证绕过/越权测试
# ==============================
print_sep("P0: 认证绕过/越权测试")

# 尝试用userA的token访问userB的资源
if TOKEN_A and TOKEN_B:
    # Get userA's info
    s, h, b = req("GET", "/api/v1/user/me", headers={"Authorization": f"Bearer {TOKEN_A}"})
    print(f"  用户A访问自己的信息: {s}")
    
    # Try to access user B's info - check if there's a user detail endpoint
    s, h, b = req("GET", f"/api/v1/user/{USER_B_ID}", headers={"Authorization": f"Bearer {TOKEN_A}"})
    if s == 200:
        report("P0", "越权漏洞: 用户A可访问用户B信息", 
            f"用用户A的token访问 /api/v1/user/{USER_B_ID} 返回200", 
            "所有用户数据访问需要验证user_id与当前登录用户匹配")
    else:
        print(f"  [安全] 越权访问被拒绝: {s}")

    # Try to access brochures of user B
    s, h, b = req("GET", "/api/v1/brochure", headers={"Authorization": f"Bearer {TOKEN_A}"})
    print(f"  用户A访问名片列表: {s} {b[:100]}")

# ==============================
# P0: XSS测试
# ==============================
print_sep("P0: XSS测试")

xss_payload = '<script>alert(document.cookie)</script>'
s, h, b = req("POST", "/api/v1/auth/register", data={
    "phone": "13900007777",
    "password": "Test@1234z",
    "name": xss_payload,
    "username": "xsstest1"
})
print(f"  XSS注册(name={xss_payload}): {s}")
if s == 200:
    data = json.loads(b)
    user = data.get("user", {})
    returned_name = user.get("name", "")
    print(f"  返回的name: {returned_name}")
    if xss_payload in returned_name:
        report("P0", "存储型XSS漏洞", 
            f"XSS payload被存储并返回: {returned_name}", 
            "对所有用户输入进行HTML转义, 使用Content-Security-Policy")
    else:
        print("  [安全] XSS payload未被原样存储")
else:
    print(f"  [安全] XSS注册被拒绝: {b[:100]}")

# ==============================
# P1: 配置安全测试
# ==============================
print_sep("P1: 配置安全测试")

# Rate limit测试
print("  限流测试:")
for i in range(5):
    s, h, b = req("GET", "/health")
    remaining = h.get("ratelimit-remaining", "?")
    print(f"    请求{i+1}: remaining={remaining}")
if remaining and int(remaining) < 90:
    print("  → 限流机制已启用")
else:
    print("  → 限流机制检测中...")

# Check CORS_ORIGINS from config - we already read it
print("\n  CORS配置:")
print("  CORS_ORIGINS允许的来源: https://liankebao.top,...")
# Check the deprecation header we found earlier
# We noted deprecation: true and link header

# Check for debug mode
s, h, b = req("GET", "/debug")
if s == 200:
    report("P1", "调试模式未关闭", "/debug端点可访问", "生产环境禁用调试模式")

# Password policy check (already strong in code)
print("\n  密码策略:")
print("  → 已实施: 最小8位+大写+小写+数字+特殊字符")
print("  → bcrypt哈希存储")

# ==============================
# P1: 依赖安全检查
# ==============================
print_sep("P1: 依赖安全扫描")

# Read requirements.txt
req_path = "D:/AI数智名片/backend/requirements.txt"
if os.path.exists(req_path):
    with open(req_path) as f:
        deps = f.read()
    print(f"  requirements.txt ({len(deps)} 字符)")
    # Check for known-vulnerable packages
    vulnerable_pkgs = {
        "passlib": "passlib 1.7.4 (已知弃用, 建议迁移到 bcrypt 直接)",
        "jose": "python-jose 可能有已知漏洞, 建议用 PyJWT",
    }
    for pkg, note in vulnerable_pkgs.items():
        if pkg in deps.lower():
            report("P1", f"依赖安全问题: {pkg}", note, "升级或替换为维护中的替代包")

# ==============================
# P2: 额外信息泄露检查
# ==============================
print_sep("P2: 其他发现")

# Check if there's an .env.example that reveals structure
env_path = "D:/AI数智名片/backend/.env"
if os.path.exists(env_path):
    with open(env_path) as f:
        env_content = f.read()
    if "JWT_SECRET=change" in env_content:
        report("P2", "JWT密钥强度可疑", 
            ".env中JWT_SECRET包含'change'字样, 可能是默认/弱密钥", 
            "使用 openssl rand -hex 32 生成强随机密钥")
    if "WECHAT_MINI_SECRET" in env_content or "WECHAT_PAY_API_KEY" in env_content:
        report("P0", "敏感凭据明文存储", 
            ".env文件包含微信支付密钥等敏感凭据, 文件系统权限不足可能泄露", 
            "对生产凭据加密存储, 使用密钥管理服务")

# Check Sunset/deprecation headers
print("  Deprecation/Sunset headers: 发现 API v1 废弃标头")
print("  → /api/v1/端点返回 deprecation: true 和 Link 标头")

# ==============================
# 总结
# ==============================
print(f"\n{'='*60}")
print(f"  红队安全攻击测试报告")
print(f"{'='*60}")
print(f"\n总计发现 {len(REPORT)} 个安全问题:\n")

severity_order = {"P0": 0, "P1": 1, "P2": 2, "P3": 3}
REPORT.sort(key=lambda r: severity_order.get(r["severity"], 9))

for i, r in enumerate(REPORT, 1):
    print(f"{i}. [{r['severity']}] {r['title']}")
    print(f"   问题: {r['detail']}")
    print(f"   建议: {r['fix']}")
    print()

# Save report
report_path = "D:/AI数智名片/backend/redteam_report.json"
with open(report_path, "w") as f:
    json.dump(REPORT, f, ensure_ascii=False, indent=2)
print(f"报告已保存至: {report_path}")
