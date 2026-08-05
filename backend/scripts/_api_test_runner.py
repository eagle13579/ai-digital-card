"""
全模块API测试脚本
循环测试每个feature模块，报告错误
"""
import sys, json, requests
sys.path.insert(0, '.')

from app.auth_jwt import create_access_token

BASE = 'http://127.0.0.1:8201'
PASS = 0
FAIL = 0
BUGS = []

def test(name, fn):
    global PASS, FAIL
    try:
        result = fn()
        if result.get('error'):
            FAIL += 1
            msg = f"  ❌ {name}: {result['error']}"
            print(msg)
            BUGS.append({'module': name.split('-')[0].strip(), 'level': 'P1', 'desc': result['error']})
        else:
            PASS += 1
            print(f"  ✅ {name}")
        return result
    except Exception as e:
        FAIL += 1
        print(f"  ❌ {name}: {e}")
        BUGS.append({'module': name.split('-')[0].strip(), 'level': 'P1', 'desc': str(e)})
        return {'error': str(e)}

def api_get(path, token=None):
    headers = {'Authorization': f'Bearer {token}'} if token else {}
    r = requests.get(f'{BASE}{path}', headers=headers, timeout=10)
    return r.json() if r.status_code < 500 else {'error': f'HTTP {r.status_code}'}

def api_post(path, data, token=None):
    headers = {'Authorization': f'Bearer {token}', 'Content-Type': 'application/json'} if token else {'Content-Type': 'application/json'}
    r = requests.post(f'{BASE}{path}', json=data, headers=headers, timeout=10)
    return r.json() if r.status_code < 500 else {'error': f'HTTP {r.status_code}'}

# Create tokens for multiple test users
tokens = {}
for uid in [51, 52, 53, 54, 55]:
    tokens[uid] = create_access_token({'sub': str(uid)})

print("=" * 60)
print("全模块API测试报告")
print("=" * 60)

print(f"\n--- 模块1: 健康检查 ---")
test('Health', lambda: {'ok' if api_get('/health') == 'OK' else 'error': 'health failed'})
test('API Health', lambda: api_get('/api/health'))

print(f"\n--- 模块2: 用户/认证 ---")
test('Profile API', lambda: api_get('/api/profile', tokens[51]))
test('User Info', lambda: api_get('/api/users/me', tokens[51]))

print(f"\n--- 模块3: 名片画册 ---")
# Test creating a brochure with the correct format
result = test('Create Brochure', lambda: api_post('/api/brochures', {
    'title': '陈明远的电子名片',
    'cover': '',
    'purpose': 'partner,client',
    'pages': [
        {'content_type': 'profile', 'content': json.dumps({'name':'陈明远','title':'CEO','company':'星辰科技'}), 'sort_order': 0},
        {'content_type': 'skills', 'content': json.dumps(['AI技术','产品设计']), 'sort_order': 1},
    ]
}, tokens[51]))

brochure_id = None
if isinstance(result, dict) and result.get('id'):
    brochure_id = result['id']
    print(f"    创建画册 ID: {brochure_id}")

if brochure_id:
    test('Get Brochure', lambda: api_get(f'/api/brochures/{brochure_id}', tokens[51]))
    test('List Brochures', lambda: api_get('/api/brochures?page_size=5', tokens[51]))

print(f"\n--- 模块4: 标签 ---")
test('Get My Tags', lambda: api_get('/api/tags/me', tokens[51]))
test('Add Tags', lambda: api_post('/api/tags/me', {'tags': [{'tag':'区块链','weight':0.8,'tag_type':'provide'}]}, tokens[51]))

print(f"\n--- 模块5: 智能匹配 ---")
test('Match Recommend', lambda: api_get('/api/match/recommend?min_score=0.3', tokens[51]))
test('Match Records', lambda: api_get('/api/match/records', tokens[51]))
test('Match Engine', lambda: api_post('/api/v1/match/engine', {'min_score':0.3}, tokens[51]))

print(f"\n--- 模块6: 建联 ---")
test('Request Connection', lambda: api_post('/api/business-card/connections/request', 
    {'target_user_id': 52, 'message': '你好，想和您交流合作', 'source': 'match'}, tokens[51]))
test('Connection List', lambda: api_get('/api/business-card/connections', tokens[51]))
test('Pending List', lambda: api_get('/api/business-card/connections/pending', tokens[51]))

print(f"\n--- 模块7: 语义搜索 ---")
test('Smart Search', lambda: api_post('/api/v1/semantic-search', {'query': 'AI技术', 'top_k': 5}, tokens[51]))

print(f"\n--- 模块8: 访客统计 ---")
test('Visitor Stats', lambda: api_get('/api/visitors/stats', tokens[51]))
test('Visitor Logs', lambda: api_get('/api/visitors', tokens[51]))

print(f"\n--- 模块9: 信任网络 ---")
test('Trust Network', lambda: api_get('/api/trust/network', tokens[51]))
test('BFS Path', lambda: api_get(f'/api/business-card/connections/path/{55}', tokens[51]))

print(f"\n--- 模块10: 数据统计 ---")
test('Business Snapshot', lambda: api_get('/api/analytics/summary', tokens[51]))
test('Dashboard Stats', lambda: api_get('/api/dashboard/stats', tokens[51]))

print(f"\n{'='*60}")
print(f"测试结果: ✅ {PASS} 通过, ❌ {FAIL} 失败, 🐛 {len(BUGS)} 个Bug")
print(f"{'='*60}")

if BUGS:
    print(f"\n🐛 Bug清单:")
    for i, bug in enumerate(BUGS, 1):
        print(f"  {i}. [{bug['level']}] {bug['module']}: {bug['desc']}")
