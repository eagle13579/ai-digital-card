"""精确API匹配：正确处理APIRouter prefix + 空字符串路由"""
import os, re, glob

BASE = 'D:\\AI数智名片'

def extract_routes_precise(filepath):
    """Extract FULL route paths accounting for APIRouter prefix"""
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Find the router prefix
    prefix = ''
    for m in re.finditer(r'(?:router|bp|_bp)\s*=\s*APIRouter\([^)]*prefix\s*=\s*[\\\'\"]([^\\\'\")]+)[\\\'"]', content):
        prefix = m.group(1).rstrip('/')
    
    # Find all @router.get/post/put/delete
    routes = set()
    for m in re.finditer(r'@\w+\.(get|post|put|delete|patch)\([\\\'\"]([^\\\'\"?<>{}=:)]*)[\\\'"]', content):
        subpath = m.group(2)
        if subpath == '':
            full = prefix
        elif subpath.startswith('/'):
            full = prefix + subpath
        else:
            full = prefix + '/' + subpath
        # Normalize
        full = full.rstrip('/')
        routes.add(full)
    
    return prefix, routes

# Process ALL router files except .bak
routers_dir = os.path.join(BASE, 'backend', 'app', 'routers')
all_routes = {}  # full_path -> source_files
all_prefixes = {}

for f in sorted(glob.glob(os.path.join(routers_dir, '*.py'))):
    if f.endswith('.bak') or '__' in f:
        continue
    fname = os.path.basename(f)
    prefix, routes = extract_routes_precise(f)
    all_prefixes[fname] = prefix
    for r in routes:
        if r not in all_routes:
            all_routes[r] = []
        all_routes[r].append(fname)

# Also check __init__.py for inline routes
with open(os.path.join(BASE, 'backend', 'app', '__init__.py'), 'r', encoding='utf-8') as f:
    init_content = f.read()
for m in re.finditer(r'@(?:app|router)\.(get|post|put|delete)\([\\\'\"]([^\\\'\"?<>{}=:)]*)[\\\'"]', init_content):
    subpath = m.group(2)
    if subpath:
        all_routes.setdefault(subpath, []).append('__init__.py')

# Also check miniapp_router.py
miniapp_router_path = os.path.join(routers_dir, 'miniapp_router.py')
if os.path.exists(miniapp_router_path):
    prefix, routes = extract_routes_precise(miniapp_router_path)
    all_prefixes['miniapp_router.py'] = prefix
    for r in routes:
        all_routes.setdefault(r, []).append('miniapp_router.py')

# Load miniapp API calls
api_js_path = os.path.join(BASE, 'miniapp', 'utils', 'api.js')
with open(api_js_path, 'r', encoding='utf-8') as f:
    api_js = f.read()

api_paths = set()
for m in re.finditer(r"['\"](/api/[^'\"${}]+)['\"]", api_js):
    api_paths.add(m.group(1))
for m in re.finditer(r"`(/api/[^`]+)`", api_js):
    path = m.group(1)
    path = re.sub(r'\$\{[^}]+\}', '{id}', path)
    path = path.split('?')[0]
    api_paths.add(path)
api_paths = {p.rstrip('/') for p in api_paths if p.startswith('/api/')}

# Match
print(f'小程序API: {len(api_paths)} | 后端路由(含prefix): {len(all_routes)}')
print()
print(f'{"#":<3} {"小程序API":<50} {"状态":<10} {"后端文件"}')
print('='*80)

missing = []
matched = 0

for i, path in enumerate(sorted(api_paths), 1):
    found = False
    source = ''
    
    # Exact match
    if path in all_routes:
        found = True
        source = f'✅ {",".join(all_routes[path])}'
    else:
        # Check if path matches a route template (e.g., /api/brochures/{brochure_id})
        for route, files in sorted(all_routes.items(), key=lambda x: -len(x[0])):
            if '{' in route:
                # Check if the path matches the pattern before {param}
                pattern_prefix = route.split('{')[0].rstrip('/')
                if path.startswith(pattern_prefix):
                    found = True
                    source = f'⚠️ {route} ({",".join(files)})'
                    break
    
    if found:
        matched += 1
        print(f'{i:<3} {path:<50} {"✅ FOUND":<10} {source}')
    else:
        missing.append(path)
        print(f'{i:<3} {path:<50} {"❌ MISSING":<10} 后端无此路由')

print()
print(f'匹配: {matched}/{len(api_paths)} | 缺失: {len(missing)}')
print()
if missing:
    print('=== 关键缺失API ===')
    for m in missing:
        print(f'  ❌ {m}')
