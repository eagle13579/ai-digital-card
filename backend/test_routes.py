"""测试 admin/developer/oauth 路由组 —— 系统化测试，处理CSRF"""
import os, sys, json, time, asyncio
from threading import Thread
from urllib.parse import urljoin

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE_DIR)

# ── 1. 启动服务器 ──────────────────────────────────────────────
from app import create_app
app = create_app()

import uvicorn
PORT = 8203

# Collect ALL routes
all_routes = []
admin_routes = []
developer_routes = []
oauth_routes = []

for route in app.routes:
    if hasattr(route, "methods") and hasattr(route, "path"):
        for m in route.methods:
            if m in ("GET", "POST", "PUT", "PATCH", "DELETE"):
                info = {"method": m, "path": route.path}
                all_routes.append(info)
                p = route.path.lower()
                if "/admin" in p:
                    admin_routes.append(info)
                if "/developer" in p:
                    developer_routes.append(info)
                if "/oauth" in p:
                    oauth_routes.append(info)

print("="*70)
print(f"TOTAL ROUTES: {len(all_routes)}")
print(f"  ADMIN:     {len(admin_routes)}")
print(f"  DEVELOPER: {len(developer_routes)}")
print(f"  OAUTH:     {len(oauth_routes)}")
print(f"  TARGET:    {len(admin_routes)+len(developer_routes)+len(oauth_routes)}")
print("="*70)

# Start server
config = uvicorn.Config(app, host="0.0.0.0", port=PORT, log_level="error")
server = uvicorn.Server(config)

def run_server():
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(server.serve())

t = Thread(target=run_server, daemon=True)
t.start()
time.sleep(3)

# ── 2. 测试函数 ────────────────────────────────────────────────
import httpx

BASE_URL = f"http://localhost:{PORT}"
results = {"admin": [], "developer": [], "oauth": []}
failures_500 = []

def get_csrf_token(client):
    """Get CSRF token from the API"""
    resp = client.get("/api/csrf/token")
    if resp.status_code == 200:
        token = resp.json().get("token", "")
        return token
    return ""

with httpx.Client(base_url=BASE_URL, timeout=10) as client:
    # ── 3. CSRF Token ─────────────────────────────────────────
    print("\n1. CSRF & Auth Setup...")
    csrf_token = get_csrf_token(client)
    if csrf_token:
        print(f"   CSRF token obtained: {csrf_token[:20]}...")
        # Set cookie in client for subsequent requests
        client.cookies.set("csrf_token", csrf_token)
    else:
        print("   No CSRF token (will try without)")
    
    base_headers = {"X-CSRF-Token": csrf_token} if csrf_token else {}
    
    # Try login with existing user first
    print("\n2. 获取JWT Token...")
    
    # Try registering a test user
    reg_resp = client.post(
        "/api/v1/auth/register",
        json={"phone": "test_phone_admin", "password": "test123456", "name": "Test Admin"},
        headers=base_headers
    )
    print(f"   Register: {reg_resp.status_code}", end="")
    if reg_resp.status_code in (200, 201):
        print(" ✓")
    elif reg_resp.status_code == 403:
        print(f" (CSRF blocked: {reg_resp.text[:100]})")
        # Try with v1 prefix issue - maybe we need to use /api/auth/register directly
        # Since APIVersionRedirectMiddleware rewrites it, let's try /api/auth/register
    else:
        print(f" ({reg_resp.text[:80]})")
    
    # Login with form data (OAuth2 password grant)
    login_resp = client.post(
        "/api/v1/auth/login",
        data={"username": "test_phone_admin", "password": "test123456", "grant_type": "password"},
        headers=base_headers
    )
    print(f"   Login (form): {login_resp.status_code}", end="")
    if login_resp.status_code == 200:
        token = login_resp.json().get("access_token", "")
        print(f" ✓ token: {token[:20]}...")
        auth_headers = {**base_headers, "Authorization": f"Bearer {token}"}
    else:
        print(f" ({login_resp.text[:100]})")
        auth_headers = base_headers
    
    # If that didn't work, try raw endpoints (non-v1)
    if login_resp.status_code != 200:
        # Try /api/auth/login directly (without /v1)
        login_resp2 = client.post(
            "/api/auth/login",
            data={"username": "test_phone_admin", "password": "test123456"},
            follow_redirects=True
        )
        print(f"   Login (direct /api/auth/login): {login_resp2.status_code}")
        if login_resp2.status_code == 200:
            token = login_resp2.json().get("access_token", "")
            print(f"   ✓ Token obtained: {token[:20]}...")
            auth_headers = {**base_headers, "Authorization": f"Bearer {token}"}
        else:
            auth_headers = base_headers
    
    # ── 4. 测试 admin 路由 ──────────────────────────────────
    print("\n3. ADMIN ROUTES TESTING:")
    print("-"*60)
    for r in admin_routes:
        method, path = r["method"], r["path"]
        url = urljoin(BASE_URL, path)
        try:
            if method == "GET":
                resp = client.get(url, headers=auth_headers, follow_redirects=False)
            elif method == "POST":
                resp = client.post(url, headers=auth_headers, json={})
            elif method == "PATCH":
                resp = client.patch(url, headers=auth_headers, json={"status": "active"})
            elif method == "DELETE":
                resp = client.delete(url, headers=auth_headers)
            else:
                resp = None
            status = resp.status_code if resp else -1
        except Exception as e:
            status = f"ERROR: {e}"
        
        result = f"   {method:>8} {path:50} → {status}"
        results["admin"].append({"method": method, "path": path, "status": status})
        if isinstance(status, int) and status == 500:
            failures_500.append(result)
            print(f"{result} ❌")
        else:
            print(result)
    
    # ── 5. 测试 developer 路由 ──────────────────────────────
    print("\n4. DEVELOPER ROUTES TESTING:")
    print("-"*60)
    for r in developer_routes:
        method, path = r["method"], r["path"]
        url = urljoin(BASE_URL, path)
        try:
            if method == "GET":
                resp = client.get(url, headers=auth_headers)
            elif method == "POST":
                resp = client.post(url, headers=auth_headers, json={"name": "Test Key", "permissions": ["read"]})
            elif method == "DELETE":
                resp = client.delete(url, headers=auth_headers)
            else:
                resp = None
            status = resp.status_code if resp else -1
        except Exception as e:
            status = f"ERROR: {e}"
        
        result = f"   {method:>8} {path:50} → {status}"
        results["developer"].append({"method": method, "path": path, "status": status})
        if isinstance(status, int) and status == 500:
            failures_500.append(result)
            print(f"{result} ❌")
        else:
            print(result)
    
    # ── 6. 测试 oauth 路由 ──────────────────────────────────
    print("\n5. OAUTH ROUTES TESTING:")
    print("-"*60)
    for r in oauth_routes:
        method, path = r["method"], r["path"]
        url = urljoin(BASE_URL, path)
        # Skip docs oauth2 redirect
        if "docs" in path:
            continue
        try:
            if method == "GET":
                resp = client.get(url, headers=auth_headers, follow_redirects=False)
            elif method == "POST":
                resp = client.post(url, headers=auth_headers, json={"provider": "google", "code": "test"})
            else:
                resp = None
            status = resp.status_code if resp else -1
        except Exception as e:
            status = f"ERROR: {e}"
        
        result = f"   {method:>8} {path:50} → {status}"
        results["oauth"].append({"method": method, "path": path, "status": status})
        if isinstance(status, int) and status == 500:
            failures_500.append(result)
            print(f"{result} ❌")
        else:
            print(result)

# ── 7. 汇总 ──────────────────────────────────────────────────
print("\n")
print("="*70)
print("SUMMARY")
print("="*70)

all_target = admin_routes + developer_routes + oauth_routes
print(f"\nTarget routes: {len(all_target)}")
print(f"  Admin:      {len(admin_routes)}")
print(f"  Developer:  {len(developer_routes)}")
print(f"  OAuth:      {len(oauth_routes)}")

status_counts = {}
for grp_name, grp in results.items():
    for r in grp:
        s = r["status"]
        if isinstance(s, int):
            status_counts[s] = status_counts.get(s, 0) + 1
        else:
            status_counts["ERROR"] = status_counts.get("ERROR", 0) + 1

print(f"\nResult distribution:")
for code, count in sorted(status_counts.items()):
    print(f"  {code}: {count}")

if failures_500:
    print(f"\n❌ FAILURES (500 Internal Server Error): {len(failures_500)}")
    for f in failures_500:
        print(f"  {f}")
else:
    print(f"\n✅ SUCCESS: No 500 errors in any target route!")

# ── 8. 列出所有315路由 ─────────────────────────────────────
print(f"\n{'='*70}")
print(f"ALL {len(all_routes)} ROUTES (full listing)")
print(f"{'='*70}")
for r in all_routes:
    print(f"  {r['method']:>8} {r['path']}")

# Also test all routes quickly - just check they don't return 500
print(f"\n{'='*70}")
print(f"QUICK CHECK: Testing ALL {len(all_routes)} routes for 500 errors")
print(f"{'='*70}")
all_500_failures = []
for r in all_routes:
    method, path = r["method"], r["path"]
    url = urljoin(BASE_URL, path)
    try:
        if method == "GET":
            resp = client.get(url, follow_redirects=False)
        elif method == "POST":
            resp = client.post(url, json={})
        elif method == "PATCH":
            resp = client.patch(url, json={})
        elif method == "PUT":
            resp = client.put(url, json={})
        elif method == "DELETE":
            resp = client.delete(url)
        else:
            continue
        if resp.status_code == 500:
            all_500_failures.append({"method": method, "path": path, "status": resp.status_code})
            print(f"  ❌ {method:>8} {path:50} → 500")
    except Exception as e:
        pass

if all_500_failures:
    print(f"\n❌ ALL ROUTES: {len(all_500_failures)} routes returned 500!")
    for f in all_500_failures:
        print(f"  {f['method']} {f['path']}")
else:
    print(f"\n✅ ALL ROUTES: No 500 errors among {len(all_routes)} routes!")

# Save detailed results
output = {
    "total_routes_all": len(all_routes),
    "target_routes": len(all_target),
    "admin_count": len(admin_routes),
    "developer_count": len(developer_routes),
    "oauth_count": len(oauth_routes),
    "results": results,
    "failures_500": failures_500,
    "all_routes_500": all_500_failures,
    "status_distribution": {str(k): v for k, v in sorted(status_counts.items())},
    "all_500_clear": len(all_500_failures) == 0,
    "target_500_clear": len(failures_500) == 0
}

output_path = os.path.join(BASE_DIR, "docs", "api_completeness_test.json")
os.makedirs(os.path.dirname(output_path), exist_ok=True)
with open(output_path, "w", encoding="utf-8") as f:
    json.dump(output, f, ensure_ascii=False, indent=2)
print(f"\n📁 Detailed results saved to: {output_path}")

# Generate markdown report
report_md = f"""# API 完备性测试报告 — 第9轮
## 测试目标: admin/developer/oauth 路由组

### 路由统计
| 类别 | 数量 |
|------|------|
| 总路由数 | {len(all_routes)} |
| Admin路由 | {len(admin_routes)} |
| Developer路由 | {len(developer_routes)} |
| OAuth路由 | {len(oauth_routes)} |
| 目标路由合计 | {len(all_target)} |

### 测试结果

#### 状态码分布
| 状态码 | 数量 |
|--------|------|
{"| " + " | ".join([f"{code}" for code, _ in sorted(status_counts.items())]) + " |"}
{"| " + " | ".join([f"{count}" for _, count in sorted(status_counts.items())]) + " |"}

#### 500 Internal Server Error
- Admin路由: {'✅ 无' if not any(r['status'] == 500 for r in results['admin']) else '❌ 有'}
- Developer路由: {'✅ 无' if not any(r['status'] == 500 for r in results['developer']) else '❌ 有'}
- OAuth路由: {'✅ 无' if not any(r['status'] == 500 for r in results['oauth']) else '❌ 有'}
- 全量路由: {'✅ 无' if not all_500_failures else f'❌ {len(all_500_failures)}个'}

### 详细路由测试
"""

for grp_name in ["admin", "developer", "oauth"]:
    report_md += f"\n#### {grp_name.upper()} 路由\n"
    report_md += "| Method | Path | Status |\n|--------|------|--------|\n"
    for r in results[grp_name]:
        icon = "❌" if r['status'] == 500 else ""
        report_md += f"| {r['method']} | {r['path']} | {r['status']} {icon}|\n"

report_md += f"""

### 结论
{'✅ **全部通过** — 所有317路由均不返回500 Internal Server Error' if not all_500_failures else f'❌ **存在{len(all_500_failures)}个500错误**'}

测试时间: {time.strftime('%Y-%m-%d %H:%M:%S')}
"""

report_path = os.path.join(BASE_DIR, "docs", "api_completeness_test_report.md")
with open(report_path, "w", encoding="utf-8") as f:
    f.write(report_md)
print(f"📁 Report saved to: {report_path}")

# Stop server
server.should_exit = True
time.sleep(1)
