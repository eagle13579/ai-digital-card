"""精确API匹配 v3 — 修复regex允许{param}"""
import os, re, glob

BASE = 'D:\\AI数智名片'

def extract_routes_fixed(filepath):
    """Extract FULL route paths with correct regex"""
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Find the router prefix
    prefix = ''
    for m in re.finditer(r'(?:router|bp|_bp)\s*=\s*APIRouter\([^)]*prefix\s*=\s*[\\\'\"]([^\\\'\")]+)[\\\'"]', content):
        prefix = m.group(1).rstrip('/')
    
    routes = set()
    for m in re.finditer(r'@\w+\.(?:get|post|put|delete|patch)\(\s*[\"\']([^\"\']+)[\"\']', content):
        subpath = m.group(1).split('?')[0]
        if subpath == '':
            full = prefix
        elif subpath.startswith('/'):
            full = prefix + subpath
        else:
            full = prefix + '/' + subpath
        routes.add(full.rstrip('/'))
    
    return prefix, routes

# Process ALL router files
routers_dir = os.path.join(BASE, 'backend', 'app', 'routers')
all_routes = {}  # full_path -> source_files

for f in sorted(glob.glob(os.path.join(routers_dir, '*.py'))):
    if f.endswith('.bak') or '__' in f or os.path.basename(f) == '__init__.py':
        continue
    fname = os.path.basename(f)
    prefix, routes = extract_routes_fixed(f)
    for r in routes:
        if r not in all_routes:
            all_routes[r] = []
        all_routes[r].append(fname)

# Also check __init__.py inline routes
with open(os.path.join(BASE, 'backend', 'app', '__init__.py'), 'r', encoding='utf-8') as f:
    init_content = f.read()
for m in re.finditer(r'@(?:app|router)\.(?:get|post|put|delete)\(\s*[\"\']([^\"\']+)[\"\']', init_content):
    subpath = m.group(1)
    if subpath:
        all_routes.setdefault(subpath, []).append('__init__.py')

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

# Build lookup: for each backend route, get its "prefix without param" 
route_lookup = []
for route, files in sorted(all_routes.items(), key=lambda x: -len(x[0])):
    # The "static" prefix (part before first {param})
    static_prefix = route.split('{')[0].rstrip('/') if '{' in route else route
    route_lookup.append((route, static_prefix, files))

# Match
missing = []
matched = 0

print(f'小程序API: {len(api_paths)} | 后端具体路由: {len(all_routes)}')
print()
print(f'{"#":<4} {"小程序API":<50} {"状态":<8} {"后端"}')
print('='*85)

for i, path in enumerate(sorted(api_paths), 1):
    found = False
    source = ''
    
    # Exact match first
    if path in all_routes:
        found = True
        source = f'✅ {"|".join(all_routes[path])}'
    else:
        # Match against route patterns
        for route, static_prefix, files in route_lookup:
            if '{' in route:
                # Check if path's static part matches route's static part
                if static_prefix and path.startswith(static_prefix):
                    found = True
                    source = f'⚠️ {route} ({"|".join(files)})'
                    break
            elif route.split('?')[0] == path:
                found = True
                source = f'✅ {"|".join(files)}'
                break
    
    if found:
        matched += 1
        print(f'{i:<4} {path:<50} {"✅ FOUND":<8} {source}')
    else:
        missing.append(path)
        print(f'{i:<4} {path:<50} {"❌ MISS":<8} 后端无此路由')

print()
print(f'匹配: {matched}/{len(api_paths)} | 缺失: {len(missing)}')
print()

# Group missing APIs by module for analysis
if missing:
    print('=== 缺失API分组 ===')
    groups = {}
    for m in missing:
        key = m.split('/')[1] + '/' + m.split('/')[2] if len(m.split('/')) > 2 else m
        if key not in groups:
            groups[key] = []
        groups[key].append(m)
    
    for key in sorted(groups.keys()):
        print(f'\n  📦 {key}/ ({len(groups[key])} missing)')
        for m in groups[key]:
            print(f'    ❌ {m}')
