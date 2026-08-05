"""小程序api.js vs 后端路由 — 全量API匹配审计"""
import json, os, re, glob

BASE = 'D:\\AI数智名片'

# 1. Extract ALL API endpoints from api.js
api_js_path = os.path.join(BASE, 'miniapp', 'utils', 'api.js')
with open(api_js_path, 'r', encoding='utf-8') as f:
    api_js = f.read()

# Find all API paths (e.g., '/api/auth/wx-mini-login', `/api/users/${userId}`)
api_paths = set()
for m in re.finditer(r"['\"](/api/[^'\"${}]+)['\"]", api_js):
    api_paths.add(m.group(1))

# Also find ones with template literals 
for m in re.finditer(r"`(/api/[^`${]+)\${[^}]+}([^`]*)`", api_js):
    path = m.group(1) + '{id}' + m.group(2)
    api_paths.add(path)
for m in re.finditer(r"`(/api/[^`?]+)\?[^`]*`", api_js):
    api_paths.add(m.group(1))

# Clean up duplicate patterns
api_paths = {p.rstrip('/') for p in api_paths if p.startswith('/api/')}

print(f'小程序定义API总数: {len(api_paths)}')
print()

# 2. Extract backend routes
backend_files = []
for f in glob.glob(os.path.join(BASE, 'backend', 'app', 'routers', '*.py'), recursive=False):
    if f.endswith('.bak'):
        continue
    backend_files.append(f)

# Also check main init
backend_files.append(os.path.join(BASE, 'backend', 'app', '__init__.py'))

backends = {}  # backend_path -> source_file
for f in sorted(backend_files):
    with open(f, 'r', encoding='utf-8') as fh:
        content = fh.read()
    
    # Find route definitions
    for m in re.finditer(r'@\w+\.(?:route|get|post|put|delete|patch)\([\\\'\"]([^\\\'\"?<>{}=:]+)[\\\'"\)]', content):
        route = m.group(1)
        if not route.startswith('/'):
            route = '/' + route
        backends[route] = os.path.basename(f)
    
    # Also check prefix + route combinations
    for m in re.finditer(r'prefix\s*=\s*[\\\'\"]([^\\\'\"?<>{}=]+)[\\\'"]', content):
        prefix = m.group(1).rstrip('/')
        for m2 in re.finditer(r'@\w+\.(?:route|get|post|put|delete|patch)\([\\\'\"]([^\\\'\"?<>{}=:]+)[\\\'"\)]', content):
            route = m2.group(1)
            if not route.startswith('/'):
                route = '/' + route
            backends[prefix + route] = os.path.basename(f)

# 3. Match: which API calls exist?
print('='*100)
print(f'{"#":<3} {"小程序 API 路径":<55} {"后端路由前缀匹配":<12} {"状态":<8} {"说明"}')
print('='*100)

matched = 0
unmatched = []
unmatched_details = []

for i, path in enumerate(sorted(api_paths), 1):
    # Check against backend routes
    found = False
    match_detail = ''
    for br in sorted(backends.keys()):
        # Check exact match or prefix match
        if path == br:
            found = True
            match_detail = f'✅ 精确匹配: {backends[br]}'
            break
        # Check if path starts with br (e.g., /api/brochures matches /api/brochures/{id})
        br_prefix = br.split('{')[0].rstrip('/') if '{' in br else br
        if br_prefix and path.startswith(br_prefix):
            if not found:
                found = True
                match_detail = f'⚠️ 前缀匹配: {backends[br]} ({br})'
            else:
                match_detail += f' | {backends[br]} ({br})'
    
    if found:
        matched += 1
        print(f'{i:<3} {path:<55} {"✅":<12} {"FOUND":<8} {match_detail}')
    else:
        unmatched.append(path)
        unmatched_details.append((i, path))
        print(f'{i:<3} {path:<55} {"❌":<12} {"MISSING":<8} 后端无此路由')

# 4. Summary
print()
print('='*100)
print(f'总API: {len(api_paths)} | 匹配到: {matched} | 缺失: {len(unmatched)}')
print(f'缺失率: {len(unmatched)/len(api_paths)*100:.1f}%' if api_paths else 'N/A')

print()
print('=== 缺失API列表（小程序调用但后端无路由）===')
for i, path in unmatched_details:
    print(f'  {i}. {path}')

# 5. Show backend route prefixes
print()
print('=== 后端路由前缀归类 ===')
prefixes = set()
for br in sorted(backends.keys()):
    parts = br.split('/')
    if len(parts) >= 4:
        prefix = '/'.join(parts[:4])
    elif len(parts) == 3:
        prefix = '/'.join(parts[:3])
    else:
        prefix = br
    prefixes.add(prefix)
for p in sorted(prefixes):
    print(f'  {p}')
