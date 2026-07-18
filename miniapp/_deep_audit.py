"""深度API匹配：精确检查每个路由的prefix+route组合"""
import os, re, glob

BASE = 'D:\\AI数智名片'

# Read all router files and extract prefix + route pairs
def extract_routes_from_file(filepath):
    """Extract (method, path) from a router file, considering Blueprint prefixes"""
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Find the Blueprint prefix
    prefix = ''
    for m in re.finditer(r'(?:router|bp|_bp)\s*=\s*(?:APIRouter|Blueprint)\([^)]*prefix\s*=\s*[\\\'\"]([^\\\'\")]+)[\\\'"]', content):
        prefix = m.group(1).rstrip('/')
    
    # Also find prefix in include_router
    # Find all @router.get/@router.post etc.
    routes = []
    for m in re.finditer(r'@\w+\.(?:get|post|put|delete|patch)\([\\\'\"]([^\\\'\"?<>{}=]+)[\\\'"]', content):
        route = m.group(1)
        full = prefix + route if route.startswith('/') else prefix + '/' + route
        routes.append(full)
    
    return prefix, routes

# Process all router files
all_routes = {}  # path -> [files]
all_prefixes = {}  # file -> prefix

for f in sorted(glob.glob(os.path.join(BASE, 'backend', 'app', 'routers', '*.py'), recursive=False)):
    if f.endswith('.bak'):
        continue
    fname = os.path.basename(f)
    prefix, routes = extract_routes_from_file(f)
    all_prefixes[fname] = prefix
    
    for route in routes:
        if route not in all_routes:
            all_routes[route] = []
        all_routes[route].append(fname)

# Also check __init__.py include_router calls to understand prefix mapping
with open(os.path.join(BASE, 'backend', 'app', '__init__.py'), 'r', encoding='utf-8') as f:
    init_content = f.read()

# Find include_router calls with prefix
for m in re.finditer(r'app\.include_router\((\w+)(?:\s*,\s*prefix\s*=\s*[\\\'\"]([^\\\'\"?<>]+)[\\\'"])?\)', init_content):
    pass  # Used for reference

# Now check the miniapp API calls against specific routes
api_js_path = os.path.join(BASE, 'miniapp', 'utils', 'api.js')
with open(api_js_path, 'r', encoding='utf-8') as f:
    api_js = f.read()

api_paths = set()
for m in re.finditer(r"['\"](/api/[^'\"${}]+)['\"]", api_js):
    api_paths.add(m.group(1))

# Also find template literal paths
for m in re.finditer(r"`(/api/[^`]+)`", api_js):
    # Simplify templates: ${xxx} -> {id}
    path = m.group(1)
    path = re.sub(r'\$\{[^}]+\}', '{id}', path)
    path = path.split('?')[0]
    api_paths.add(path)

api_paths = {p.rstrip('/') for p in api_paths if p.startswith('/api/')}

print(f'小程序API总数: {len(api_paths)}')
print(f'后端路由文件总数: {len([f for f in glob.glob(os.path.join(BASE, "backend", "app", "routers", "*.py")) if not f.endswith(".bak")])}')
print(f'后端解析路由总数: {len(all_routes)}')
print()

# Match API paths against actual routes with proper prefix consideration
missing = []
print('=== 小程序API vs 后端实际路由（含prefix前缀）===')
print(f'{"#":<3} {"小程序API":<50} {"状态":<8} {"后端路由源"}')
print('-'*100)

for i, path in enumerate(sorted(api_paths), 1):
    found_in = []
    for route, files in sorted(all_routes.items(), key=lambda x: -len(x[0])):
        # Exact match
        if path == route:
            found_in.append(f'✅精确:{"/".join(files)}')
            break
        # Path matches route pattern (path has path param)
        if '{' in route:
            pattern_parts = route.split('{')[0].rstrip('/')
            if path.startswith(pattern_parts):
                found_in.append(f'⚠️前缀:{route} ({",".join(files)})')
                break
    
    if found_in:
        print(f'{i:<3} {path:<50} {"✅ FOUND":<8} {found_in[0]}')
    else:
        print(f'{i:<3} {path:<50} {"❌ MISSING":<8} 后端无此路由')
        missing.append(path)

print()
print(f'缺失API: {len(missing)}')
for m in missing:
    print(f'  ❌ {m}')
