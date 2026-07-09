#!/usr/bin/env python
"""
===========================================================
  战狼红队 — AI数智名片 全量安全攻击测试
  场景覆盖: WR-004, WR-009, WR-010, WR-011, WR-012 + JWT
===========================================================
"""
import json, base64, sys, os, time, datetime, hashlib, hmac
import urllib.request
import urllib.error

BASE = "http://localhost:8002"
REPORT = []
TIMESTAMP = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

def req(method, path, headers=None, data=None, timeout=8):
    url = f"{BASE}{path}"
    hdrs = dict(headers or {})
    if data is not None:
        body = json.dumps(data).encode()
        hdrs.setdefault("Content-Type", "application/json")
    else:
        body = None
    r = urllib.request.Request(url, data=body, headers=hdrs, method=method)
    try:
        resp = urllib.request.urlopen(r, timeout=timeout)
        return resp.status, dict(resp.headers), resp.read().decode(errors='replace')
    except urllib.error.HTTPError as e:
        return e.code, dict(e.headers), e.read().decode(errors='replace')
    except Exception as e:
        return 0, {}, str(e)

def b64url(data):
    return base64.urlsafe_b64encode(json.dumps(data).encode()).decode().rstrip('=')

def report(severity, title, detail, fix=""):
    REPORT.append({"severity": severity, "title": title, "detail": detail, "fix": fix})
    print(f"  [{severity}] {title}: {detail[:100]}...")

def print_sep(title):
    print(f"\n{'='*70}")
    print(f"  ▸ {title}")
    print(f"{'='*70}")

# ╔═══════════════════════════════════════════════════════════════════╗
# ║  0. 注册/登录测试用户                                           ║
# ╚═══════════════════════════════════════════════════════════════════╝
print_sep("0. 注册测试用户")

s, h, b = req("POST", "/api/v1/auth/register", data={
    "phone": "13900009999", "password": "Test@1234x",
    "name": "RedTeam", "username": "redteam_main"
})
TOKEN_A = None; USER_A_ID = None
if s == 200:
    data = json.loads(b)
    TOKEN_A = data["access_token"]
    USER_A_ID = data["user"]["id"]
    print(f"  注册成功: UserA ID={USER_A_ID}")
else:
    s2, h2, b2 = req("POST", "/api/v1/auth/login", data={
        "phone": "13900009999", "password": "Test@1234x"
    })
    if s2 == 200:
        data = json.loads(b2)
        TOKEN_A = data["access_token"]
        USER_A_ID = data["user"]["id"]
        print(f"  登录已有用户: UserA ID={USER_A_ID}")
    else:
        print(f"  登录失败: {s2} {b2[:100]}")

s, h, b = req("POST", "/api/v1/auth/register", data={
    "phone": "13900008888", "password": "Test@1234y",
    "name": "UserB", "username": "userb_test"
})
TOKEN_B = None; USER_B_ID = None
if s == 200:
    data = json.loads(b)
    TOKEN_B = data["access_token"]
    USER_B_ID = data["user"]["id"]
    print(f"  注册成功: UserB ID={USER_B_ID}")
else:
    s2, h2, b2 = req("POST", "/api/v1/auth/login", data={
        "phone": "13900008888", "password": "Test@1234y"
    })
    if s2 == 200:
        data = json.loads(b2)
        TOKEN_B = data["access_token"]
        USER_B_ID = data["user"]["id"]
        print(f"  登录已有用户: UserB ID={USER_B_ID}")
    else:
        print(f"  登录失败: {s2} {b2[:100]}")

# ╔═══════════════════════════════════════════════════════════════════╗
# ║  WR-004: 安全基础攻击                                           ║
# ║  ─ SQL注入, XSS, 敏感路径扫描                                   ║
# ╚═══════════════════════════════════════════════════════════════════╝
print_sep("WR-004: 安全基础攻击")

# ── WR-004.1 SQL注入测试 ──
print("\n  [WR-004.1] SQL注入测试:")
sqli_payloads = [
    ("' OR 1=1--", "any"),
    ("' OR '1'='1", "any"),
    ("admin'--", "any"),
    ("' UNION SELECT * FROM users--", "any"),
    ("' OR 1=1 LIMIT 1--", "any"),
]
for phone, pw in sqli_payloads:
    s, h, b = req("POST", "/api/v1/auth/login", data={"phone": phone, "password": pw})
    if s == 200:
        report("P0", f"SQL注入成功(登录接口)", f"phone={phone} 返回HTTP 200, 绕过了认证",
               "使用参数化查询(已使用SQLAlchemy ORM, 确认ORM配置正确)")
    else:
        print(f"    [安全] 登录注入被拦截: phone={phone} -> {s}")

# SQL注入 - URL参数
sqli_urls = [
    "/api/v1/brochure?id=1 OR 1=1",
    "/api/v1/brochures/1' OR '1'='1",
    "/api/v1/brochures/1 UNION SELECT * FROM users",
]
for path in sqli_urls:
    s, h, b = req("GET", path, headers={"Authorization": f"Bearer {TOKEN_A}" if TOKEN_A else {}})
    note = "[!!!] 可能注入!" if s == 200 and "error" not in b.lower() else f"[安全]({s})"
    print(f"    {note}: GET {path[:50]}... -> {s}")

# ── WR-004.2 XSS测试 ──
print("\n  [WR-004.2] XSS测试:")
xss_payload = '<script>alert(document.cookie)</script>'
s, h, b = req("POST", "/api/v1/auth/register", data={
    "phone": "13900006666", "password": "Test@1234z",
    "name": xss_payload, "username": "xsstest1"
})
if s == 200:
    data = json.loads(b)
    user = data.get("user", {})
    returned_name = user.get("name", "")
    if xss_payload in returned_name:
        report("P0", "存储型XSS漏洞(注册name字段)", 
               f"XSS payload被原样存储并返回: {returned_name[:80]}",
               "已使用html.escape()但需确认前端渲染时是否做二次转义")
    else:
        print(f"    [安全] XSS payload被转义: {returned_name[:80]}")

# XSS - 登录接口
s, h, b = req("POST", "/api/v1/auth/login", data={
    "phone": "13900006666", "password": "' OR 1=1--"
})
print(f"    XSS/SQLi登录: {s}")

# ── WR-004.3 敏感路径扫描 ──
print("\n  [WR-004.3] 敏感路径扫描:")
sensitive_paths = [
    "/docs", "/redoc", "/openapi.json", "/metrics",
    "/debug", "/admin", "/.env", "/.git/config",
    "/api/v1/admin/users", "/api/v1/admin",
    "/graphql", "/api/v1/graphql",
    "/health", "/api/health",
    "/robots.txt", "/sitemap.xml",
    "/swagger.json", "/swagger",
]
for p in sensitive_paths:
    s, h, b = req("GET", p)
    size = len(b)
    status_note = "⚠️ 暴露!" if s == 200 else f"安全({s})"
    if s == 200 and size > 10:
        if p not in ["/health", "/api/health"]:
            report("P1", f"敏感路径暴露: {p}", 
                   f"HTTP {s}, 返回{size}字节", 
                   "生产环境禁用开发文档/调试端点")
    print(f"    {status_note:20s} GET {p:30s} -> {s} ({size}B)")

# 带Token的敏感路径
if TOKEN_A:
    admin_paths = [
        ("GET", "/api/v1/admin/users"),
        ("GET", "/api/v1/admin/settings"),
        ("POST", "/api/v1/admin/users", {"phone": "13900000001", "password": "Admin@1234", "name": "Hacked"}),
    ]
    for method, path, *rest in admin_paths:
        data = rest[0] if rest else None
        s, h, b = req(method, path, headers={"Authorization": f"Bearer {TOKEN_A}"}, data=data)
        if s not in [401, 403, 404]:
            print(f"    ⚠️  Admin端点可达: {method} {path} -> {s} {b[:60]}")

# ╔═══════════════════════════════════════════════════════════════════╗
# ║  WR-009: 敏感信息泄露                                           ║
# ╚═══════════════════════════════════════════════════════════════════╝
print_sep("WR-009: 敏感信息泄露")

# ── WR-009.1 响应头信息泄露 ──
print("\n  [WR-009.1] 响应头检查:")
endpoints_to_check = ["/health", "/api/health", "/api/v1/auth/login", "/"]
for ep in endpoints_to_check:
    s, h, b = req("GET" if ep != "/api/v1/auth/login" else "POST", ep, 
                   data={"phone": "test", "password": "test"} if ep == "/api/v1/auth/login" else None)
    print(f"    {ep}:")
    leaky_headers = []
    for header, value in h.items():
        if header.lower() in ["server", "x-powered-by", "x-aspnet-version", "x-frame-options"]:
            print(f"      {header}: {value}")
            leaky_headers.append(f"{header}={value}")
        if header.lower() == "server":
            report("P1", "响应头信息泄露(Server)", 
                   f"暴露Server头: {value}",
                   "SecurityHeadersMiddleware第60行重新添加了'uvicorn'头，应移除")
    if not leaky_headers:
        print(f"      (无敏感头信息泄露)")

# ── WR-009.2 错误页信息泄露 ──
print("\n  [WR-009.2] 错误页信息泄露:")
s, h, b = req("GET", "/nonexistent_path_xyz_123")
print(f"    404页: {s} {b[:120]}")
if "uvicorn" in b.lower() or "fastapi" in b.lower() or "traceback" in b.lower():
    report("P1", "错误页信息泄露", 
           "404错误页包含框架版本信息",
           "自定义错误页面, 隐藏框架版本号")
if s == 200:
    print(f"    ⚠️ 注意: 404路径返回200状态码(Mock降级)")
    report("P2", "HTTP语义违反: 404返回200", 
           "不存在的路径返回HTTP 200而非404 (Mock降级行为)",
           "移除Mock降级逻辑, 让未知路径正确返回404")

# ── WR-009.3 OpenAPI文档泄露 ──
print("\n  [WR-009.3] API文档暴露:")
for doc_path in ["/openapi.json", "/docs", "/redoc"]:
    s, h, b = req("GET", doc_path)
    if s == 200:
        report("P1", f"API文档暴露: {doc_path}", 
               f"HTTP 200, 返回{len(b)}字节",
               "生产环境应彻底禁用, 当前ENV检查可能未生效")

# ╔═══════════════════════════════════════════════════════════════════╗
# ║  WR-010: nginx安全基线+限流                                    ║
# ╚═══════════════════════════════════════════════════════════════════╝
print_sep("WR-010: 安全基线 + 限流测试")

# ── WR-010.1 安全响应头检查 ──
print("\n  [WR-010.1] 安全响应头检查:")
s, h, b = req("GET", "/api/health")
required_headers = {
    "Content-Security-Policy": "default-src 'self'",
    "Strict-Transport-Security": "max-age=31536000; includeSubDomains",
    "X-Content-Type-Options": "nosniff",
    "X-Frame-Options": "DENY",
    "X-XSS-Protection": "1; mode=block",
    "Referrer-Policy": "strict-origin-when-cross-origin",
    "Permissions-Policy": "camera=(), microphone=(), geolocation=()",
}
missing_headers = []
for name, expected in required_headers.items():
    actual = h.get(name.lower(), "")
    if actual:
        print(f"    ✓ {name}: {actual}")
    else:
        print(f"    ✗ {name}: 缺失!")
        missing_headers.append(name)

if missing_headers:
    report("P1", f"安全响应头缺失: {', '.join(missing_headers)}",
           f"缺少{len(missing_headers)}个安全响应头",
           "SecurityHeadersMiddleware未正确注册或未生效")

# CSP安全检查 - 当前CSP太严格可能影响功能
csp = h.get("content-security-policy", "")
print(f"    CSP策略: {csp}")

# ── WR-010.2 限流测试 ──
print("\n  [WR-010.2] 限流测试(连续请求):")
rate_limit_results = []
for i in range(10):
    s, h, b = req("GET", "/api/health")
    remaining = h.get("ratelimit-remaining", "N/A")
    retry_after = h.get("retry-after", "N/A")
    rate_limit_results.append((s, remaining))
    if i < 5 or i == 9:
        print(f"    请求 {i+1}: status={s}, remaining={remaining}, retry-after={retry_after}")

# 检查限流是否工作
if all(r[0] == 200 for r in rate_limit_results):
    print("    ⚠️ 限流测试: 10次请求均返回200, 未触发限流")
    report("P2", "限流可能未生效", 
           "10次连续请求未触发限流(可能阈值较高或限流中间件未生效)",
           "检查RateLimiterMiddleware配置和IPRateLimitMiddleware")

# ╔═══════════════════════════════════════════════════════════════════╗
# ║  WR-011: 前后端字段不匹配                                      ║
# ╚═══════════════════════════════════════════════════════════════════╝
print_sep("WR-011: 前后端字段不匹配检查")

# 检查/openapi.json中的API定义
s, h, b = req("GET", "/openapi.json")
if s == 200:
    try:
        spec = json.loads(b)
        paths = list(spec.get("paths", {}).keys())
        print(f"  OpenAPI规范: {len(paths)} 个端点定义")
        print(f"  端点示例: {paths[:5]}")
        
        # 检查实际响应是否匹配规范
        # 取一个端点做实际测试
        test_endpoints = [
            "/api/health",
            "/api/v1/auth/me" if TOKEN_A else None,
        ]
        for ep in test_endpoints:
            if not ep:
                continue
            hdrs = {"Authorization": f"Bearer {TOKEN_A}"} if "/auth/me" in ep else {}
            s2, h2, b2 = req("GET", ep, headers=hdrs)
            print(f"    GET {ep}: {s2} ({len(b2)}B)")
        
        # 检查是否有v1前缀不匹配
        print("\n  前后端路径一致性检查:")
        api_paths_v1 = [p for p in paths if "/api/v1/" in p]
        api_paths_no_v1 = [p for p in paths if "/api/" in p and "/api/v1/" not in p]
        if api_paths_v1:
            print(f"    /api/v1/ 端点: {len(api_paths_v1)}个")
        if api_paths_no_v1:
            print(f"    /api/ 端点(无v1): {len(api_paths_no_v1)}个")
        
    except json.JSONDecodeError as e:
        print(f"  OpenAPI解析失败: {e}")
else:
    print(f"  OpenAPI不可用: HTTP {s} (生产环境已禁用)")

# ╔═══════════════════════════════════════════════════════════════════╗
# ║  WR-012: CORS通配符+Credentials                                ║
# ╚═══════════════════════════════════════════════════════════════════╝
print_sep("WR-012: CORS配置检查")

# ── WR-012.1 CORS预检请求 ──
print("\n  [WR-012.1] CORS OPTIONS预检:")
evil_origins = [
    "https://evil.com",
    "https://attacker.com",
    "null",
    "https://liankebao.top.evil.com",
    "http://localhost:9999",
]
for origin in evil_origins:
    s, h, b = req("OPTIONS", "/api/v1/auth/login", headers={
        "Origin": origin,
        "Access-Control-Request-Method": "POST",
        "Access-Control-Request-Headers": "Authorization, Content-Type"
    })
    acao = h.get("access-control-allow-origin", "N/A")
    acac = h.get("access-control-allow-credentials", "N/A")
    if acao != "N/A" and acao != origin and acao != "null":
        print(f"    Origin={origin}: allow-origin={acao}, credentials={acac}")
        # 如果allow-origin和origin不完全匹配（但不是通配符）
        if acao == "*":
            report("P0", "CORS通配符+Credentials漏洞",
                   f"CORS配置为allow_origins='*'且allow_credentials=True",
                   "不允许通配符+Credentials组合, 应使用白名单")
    elif acao == origin:
        print(f"    ⚠️ Origin={origin}: allow-origin={acao}, credentials={acac}")
        # 检查credentials+非通配符来源
    else:
        print(f"    ✓ Origin={origin}: 被拒绝(acao={acao})")

# ── WR-012.2 CORS反射攻击测试 ──
print("\n  [WR-012.2] CORS反射/Origin反射测试:")
s, h, b = req("OPTIONS", "/api/v1/auth/login", headers={
    "Origin": "https://evil.com",
    "Access-Control-Request-Method": "POST",
})
acao = h.get("access-control-allow-origin", "N/A")
if acao == "https://evil.com":
    report("P0", "CORS Origin反射漏洞",
           "服务器原样返回Origin头, 允许任意跨域请求",
           "使用白名单验证而非反射Origin")

# ╔═══════════════════════════════════════════════════════════════════╗
# ║  JWT认证绕过测试                                                ║
# ╚═══════════════════════════════════════════════════════════════════╝
print_sep("JWT认证绕过测试")

# ── JWT-1: alg=none攻击 ──
print("\n  [JWT-1] alg=none攻击:")
header_none = b64url({"alg": "none", "typ": "JWT"})
payload_fake = b64url({"sub": "1", "exp": 9999999999, "iat": 0})
token_none = f"{header_none}.{payload_fake}."
s, h, b = req("GET", "/api/v1/auth/me", headers={"Authorization": f"Bearer {token_none}"})
if s == 200:
    report("P0", "JWT alg=none攻击成功",
           "使用alg=none的JWT token绕过了认证",
           "在jose/pyjwt中禁用none算法, 强制要求签名验证")
else:
    print(f"    [安全] alg=none被拒绝: {s}")

# ── JWT-2: 空token/无token ──
print("\n  [JWT-2] 空Token/无Token测试:")
s1, _, _ = req("GET", "/api/v1/auth/me", headers={"Authorization": "Bearer "})
s2, _, _ = req("GET", "/api/v1/auth/me")
print(f"    空token: {s1}, 无token: {s2}")
if s2 == 200:
    report("P0", "认证绕过(无token)", "无token访问受保护端点返回200", "添加认证依赖")

# ── JWT-3: 弱密钥暴力破解 ──
print("\n  [JWT-3] 弱密钥暴力破解:")
# 尝试从.env猜测密钥
weak_secrets = [
    "secret", "123456", "password", "changeme", "change...card",
    "JWT_SECRET", "your-256-bit-random-hex-key-here", "test",
    "key", "admin", "token", "jwt_secret", "my_secret",
]
found_key = None
for weak_secret in weak_secrets:
    try:
        import jwt as pyjwt
        fake = pyjwt.encode({"sub": "1", "exp": 9999999999}, weak_secret, algorithm="HS256")
        s, h, b = req("GET", "/api/v1/auth/me", headers={"Authorization": f"Bearer {fake}"})
        if s == 200:
            found_key = weak_secret
            report("P0", f"JWT弱密钥破解: '{weak_secret}'",
                   f"使用弱密钥伪造token成功登录",
                   "使用openssl rand -hex 32生成强随机密钥, 优先使用RS256")
            break
        else:
            print(f"    [安全] 密钥'{weak_secret[:12]}...'被拒绝: {s}")
    except ImportError:
        print("    pyjwt未安装")
        break
    except Exception as e:
        print(f"    密钥'{weak_secret[:12]}...'错误: {e}")

if not found_key:
    print("    ✓ 所有弱密钥均被拒绝")

# ── JWT-4: Token过期检查 ──
print("\n  [JWT-4] Token过期时间检查:")
if TOKEN_A:
    try:
        parts = TOKEN_A.split(".")
        payload_b64 = parts[1]
        payload_b64 += "=" * (4 - len(payload_b64) % 4)
        payload = json.loads(base64.urlsafe_b64decode(payload_b64))
        exp = payload.get("exp", 0)
        iat = payload.get("iat", 0)
        exp_time = datetime.datetime.fromtimestamp(exp)
        now = datetime.datetime.utcnow()
        remaining = exp_time - now
        print(f"    过期时间: {exp_time}")
        print(f"    剩余有效: {remaining}")
        if remaining.days >= 1:
            report("P1", "JWT过期时间过长",
                   f"Token有效期{remaining.days}天, 增加泄露风险",
                   "建议ACCESS_TOKEN_EXPIRE_MINUTES不超过60分钟")
    except Exception as e:
        print(f"    Token解析失败: {e}")

# ── JWT-5: 算法混淆攻击 ──
print("\n  [JWT-5] 算法混淆攻击(RS256→HS256):")
# 尝试用HS256签一个RS256 alg的token来测试算法混淆
# auth_jwt.py中先尝试RS256, 失败后回退到HS256
# 如果攻击者获得了公钥, 可以用公钥当HS256密钥签名
try:
    _, pub_key = None, None
    # Check if public key is exposed
    s, h, b = req("GET", "/.well-known/jwks.json")
    if s == 200:
        print(f"    ⚠️ JWKS端点暴露! {b[:100]}")
        report("P1", "JWKS公钥端点暴露",
               "/.well-known/jwks.json可访问, 暴露RSA公钥",
               "移除或保护JWKS端点")
    else:
        print(f"    JWKS端点: {s} (安全)")
    
    s, h, b = req("GET", "/api/v1/auth/jwks")
    if s == 200:
        print(f"    ⚠️ JWKS端点(/api/v1/auth/jwks)暴露!")
        report("P1", "JWKS端点暴露", 
               "/api/v1/auth/jwks可访问",
               "限制JWKS端点访问")
except Exception as e:
    print(f"    JWKS检查错误: {e}")

# ── JWT-6: 越权测试 ──
print("\n  [JWT-6] 水平越权测试:")
if TOKEN_A and TOKEN_B and USER_B_ID:
    # UserA尝试访问UserB的资料
    s, h, b = req("GET", "/api/v1/auth/me", headers={"Authorization": f"Bearer {TOKEN_A}"})
    if s == 200:
        user_a_info = json.loads(b)
        print(f"    用户A信息: id={user_a_info.get('id')}, name={user_a_info.get('name')}")
    
    # UserA访问UserB的ID信息
    s, h, b = req("GET", f"/api/v1/user/{USER_B_ID}", 
                   headers={"Authorization": f"Bearer {TOKEN_A}"})
    if s == 200:
        report("P0", "水平越权: 用户A可读取用户B信息",
               f"用用户A的token访问/api/v1/user/{USER_B_ID}返回200",
               "所有用户数据访问需验证user_id与当前登录用户匹配")
    else:
        print(f"    [安全] 越权访问被拒绝: {s}")
    
    # UserA访问UserB的名片
    for bid in [1, 2, 3]:
        s, h, b = req("GET", f"/api/v1/brochures/{bid}", 
                       headers={"Authorization": f"Bearer {TOKEN_A}"})
        if s == 200:
            try:
                d2 = json.loads(b)
                owner_id = d2.get("user_id")
                if owner_id and owner_id != USER_A_ID:
                    report("P0", "水平越权: 名片数据可被其他用户读取",
                           f"用户A(id={USER_A_ID})可读取user_id={owner_id}的名片{bid}",
                           "brochure查询需添加WHERE user_id = current_user.id")
                print(f"    ⚠️ 名片{bid}: owner={owner_id}, 越权读取成功")
            except Exception as e:
                print(f"    名片{bid}: {s} {b[:60]}")
        else:
            print(f"    名片{bid}: [安全] {s}")

# ╔═══════════════════════════════════════════════════════════════════╗
# ║  代码安全反模式扫描                                             ║
# ╚═══════════════════════════════════════════════════════════════════╝
print_sep("代码安全反模式扫描")
import re

backend_dir = "D:/AI数智名片/backend"
danger_patterns = [
    (r"__import__\(", "__import__()动态导入"),
    (r"\beval\s*\(", "eval()执行"),
    (r"\bexec\s*\(", "exec()执行"),
    (r"\bos\.system\b", "os.system()"),
    (r"\bsubprocess\.", "subprocess调用"),
    (r"debug\s*=\s*True", "debug=True"),
    (r"reload\s*=\s*True", "reload=True"),
    (r"HARDCODED_KEY\s*=", "硬编码密钥"),
    (r"pickle\.loads?", "pickle反序列化"),
    (r"yaml\.load\s*\(", "不安全的yaml.load"),
    (r"sqlite3\.execute\s*\(\s*f[\"']", "f-string SQL注入"),
    (r"\.execute\s*\(\s*[\"'].*\{", "format字符串SQL"),
]

for root, dirs, files in os.walk(backend_dir):
    dirs[:] = [d for d in dirs if d not in ('__pycache__', '.git', 'venv', 'node_modules')]
    for f in files:
        if f.endswith('.py'):
            fpath = os.path.join(root, f)
            try:
                with open(fpath, 'r', encoding='utf-8', errors='ignore') as fh:
                    content = fh.read()
                for pattern, desc in danger_patterns:
                    if re.search(pattern, content, re.IGNORECASE):
                        relpath = os.path.relpath(fpath, backend_dir)
                        print(f"    ⚠️  [{desc}] 发现于 {relpath}")
                        # debug=True may be in run.py, that's OK
                        if "debug" not in pattern.lower() or "run.py" not in relpath:
                            report("P2", f"代码反模式: {desc}",
                                   f"文件 {relpath} {desc}",
                                   "移除或审查")
            except Exception as e:
                pass

# ╔═══════════════════════════════════════════════════════════════════╗
# ║  .env配置安全检查                                              ║
# ╚═══════════════════════════════════════════════════════════════════╝
print_sep(".env配置安全检查")

env_example = """JWT_SECRET=your-256-bit-random-hex-key-here
CORS_ORIGINS=https://liankebao.top,https://api.liankebao.top,http://localhost:5173,http://localhost:8200
"""
print(f"  .env.example中JWT_SECRET为默认值: your-256-bit-random-hex-key-here")
report("P2", "JWT_SECRET默认值风险",
       ".env.example中JWT_SECRET为'your-256-bit-random-hex-key-here'",
       "确保生产环境使用openssl rand -hex 32生成强密钥")

# ╔═══════════════════════════════════════════════════════════════════╗
# ║  端口扫描(发现所有运行中的服务)                                 ║
# ╚═══════════════════════════════════════════════════════════════════╝
print_sep("端口扫描: 运行中的服务")

import socket
common_ports = [8000, 8002, 8200, 8201, 5173, 5170, 6379, 5432, 3306, 27017, 3000, 5000, 8080, 8443, 9090]
print("  扫描本地常见端口...")
for port in common_ports:
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.settimeout(1)
    result = s.connect_ex(('127.0.0.1', port))
    if result == 0:
        try:
            s2 = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s2.settimeout(2)
            s2.connect(('127.0.0.1', port))
            s2.send(b"GET / HTTP/1.0\r\n\r\n")
            banner = s2.recv(200).decode(errors='replace')[:80]
            s2.close()
        except:
            banner = "(no banner)"
        print(f"   端口 {port}: 开放 ({banner})")
    s.close()

# ╔═══════════════════════════════════════════════════════════════════╗
# ║  生成综合红队报告                                              ║
# ╚═══════════════════════════════════════════════════════════════════╝
print_sep("=" * 30 + " 战狼红队报告 " + "=" * 30)

severity_order = {"P0": 0, "P1": 1, "P2": 2, "P3": 3}
REPORT.sort(key=lambda r: severity_order.get(r["severity"], 9))

# 计算安全评分
total = len(REPORT)
p0 = sum(1 for r in REPORT if r["severity"] == "P0")
p1 = sum(1 for r in REPORT if r["severity"] == "P1")
p2 = sum(1 for r in REPORT if r["severity"] == "P2")
score = max(1, 10 - p0 * 3 - p1 * 1 - p2 * 0.5)
score = min(10, max(1, score))

print(f"\n  🛡️  安全评分: {score:.1f}/10")
print(f"  📊 漏洞总数: {total}")
print(f"     🔴 P0(严重): {p0}")
print(f"     🟠 P1(高危): {p1}")
print(f"     🟡 P2(中危): {p2}")
print()

# 按严重性输出
for i, r in enumerate(REPORT, 1):
    icon = {"P0": "🔴", "P1": "🟠", "P2": "🟡", "P3": "⚪"}.get(r["severity"], "⚪")
    print(f"  {icon} [{r['severity']}] {r['title']}")
    print(f"     问题: {r['detail'][:150]}")
    print(f"     修复: {r['fix'][:150]}")
    print()

# 保存报告
final_report = {
    "report_title": "战狼红队 AI数智名片 全量安全攻击测试报告",
    "timestamp": TIMESTAMP,
    "target": BASE,
    "security_score": round(score, 1),
    "summary": {
        "total_findings": total,
        "p0_critical": p0,
        "p1_high": p1,
        "p2_medium": p2,
    },
    "findings": REPORT,
}

report_path = "D:/AI数智名片/backend/redteam_full_report.json"
with open(report_path, "w", encoding="utf-8") as f:
    json.dump(final_report, f, ensure_ascii=False, indent=2)
print(f"\n  📝 完整报告已保存: {report_path}")
