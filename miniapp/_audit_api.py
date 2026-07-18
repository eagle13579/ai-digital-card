"""全量API依赖审计：小程序前端调用的API vs 后端实际注册的路由"""
import json, os, re, glob

BASE = 'D:\\AI数智名片'
MINIAPP = os.path.join(BASE, 'miniapp')
BACKEND = os.path.join(BASE, 'backend')

# 1. Extract all API calls from miniapp JS files
mini_api_calls = {}  # page_path -> set of API calls

for f in sorted(glob.glob(os.path.join(MINIAPP, 'pages', '**', '*.js'), recursive=True)):
    rel = os.path.relpath(f, MINIAPP)
    with open(f, 'r', encoding='utf-8') as fh:
        content = fh.read()
    
    # Find all API URLs called
    # Pattern: /api/xxx or https://xxx/api/
    apis = set()
    # wx.request urls
    for m in re.finditer(r'[\\\'"`](/api/[^\\\'"`? )]+)', content):
        apis.add(m.group(1))
    # fetch/axios urls
    for m in re.finditer(r'[\\\'"`](/api/[^\\\'"`? )]+)', content):
        apis.add(m.group(1))
    # Template strings like `url`
    for m in re.finditer(r'`[^`]*/api/[^`? )]+`', content):
        url = m.group(0).replace('`','').split('?')[0]
        # Remove template variables like ${xxx}
        url = re.sub(r'\$\{[^}]+\}', '{var}', url)
        apis.add(url)
    
    if '/' in rel and rel.endswith('.js'):
        page_name = rel.replace('.js','')
    else:
        page_name = rel.replace('.js','')
    
    if apis:
        mini_api_calls[page_name] = sorted(apis)

# 2. Extract all backend route registrations
backend_routes = set()
for f in glob.glob(os.path.join(BACKEND, 'app', 'routers', '*.py'), recursive=False):
    with open(f, 'r', encoding='utf-8') as fh:
        content = fh.read()
    for m in re.finditer(r'@\w+\.(?:route|get|post|put|delete|patch)\([\\\'\"]([^\\\'\"?<>{}=]+)[\\\'"]', content):
        route = m.group(1)
        if not route.startswith('/'):
            route = '/' + route
        backend_routes.add(route)
    
    # Also check @router.api_route or app.get patterns
    for m in re.finditer(r'@\w+\.api_route\([\\\'\"]([^\\\'\"?<>{}=]+)[\\\'"]', content):
        route = m.group(1)
        if not route.startswith('/'):
            route = '/' + route
        backend_routes.add(route)

# Also check main app.__init__.py for inline routes
with open(os.path.join(BACKEND, 'app', '__init__.py'), 'r', encoding='utf-8') as fh:
    init_content = fh.read()
for m in re.finditer(r'@\w+\.(?:route|get|post|put|delete|patch)\([\\\'\"]([^\\\'\"?<>{}=]+)[\\\'"]', init_content):
    route = m.group(1)
    if not route.startswith('/'):
        route = '/' + route
    backend_routes.add(route)

# 3. Compare: which API calls from miniapp DON'T exist in backend?
print('='*80)
print('API调用完整性审计：小程序调用的API vs 后端注册路由')
print('='*80)

total_found = 0
total_missing = 0
all_mini_apis = set()

for page, apis in sorted(mini_api_calls.items()):
    print(f'\n--- {page} ---')
    for api in apis:
        all_mini_apis.add(api)
        # Check if this API exists in backend routes
        # Remove {var} parts for comparison
        api_pattern = api.split('?')[0].split('{')[0] if '{' in api else api.split('?')[0]
        exists = False
        for br in backend_routes:
            # Check prefix match
            if api_pattern.startswith(br) or (api_pattern != api and api.startswith(br)):
                exists = True
                break
            # Check if backend route pattern matches (e.g., /api/users/{id})
            br_prefix = br.split('{')[0] if '{' in br else br
            if api_pattern.startswith(br_prefix):
                exists = True
                break
        
        status = '✅' if exists else '❌ MISSING'
        if not exists:
            total_missing += 1
        total_found += 1
        print(f'  {status} {api}')

print()
print('='*80)
print(f'总计: 小程序调用 {total_found} 个API, 后端缺失 {total_missing} 个')
print(f'后端注册路由总数: {len(backend_routes)}')

# 4. List backend routes for reference
print()
print('=== 后端已注册路由（部分） ===')
for route in sorted(backend_routes):
    print(f'  {route}')
