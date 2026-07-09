"""验证 Token定价路由注册"""
import sys, os
sys.path.insert(0, "D:/AI数智名片/backend")
os.environ.setdefault("ENV", "production")

from app import create_app
app = create_app()

# 查找 token 相关路由
found = False
for route in app.routes:
    if hasattr(route, "path") and "token" in route.path.lower():
        print(f"  {route.methods} {route.path}")
        found = True

if not found:
    print("NO /token/ routes registered!")
else:
    print(f"Total /token/ routes found")

print(f"Total routes: {len(app.routes)}")
