"""综合测试: brochure create + match recommend"""
import sys, json, os
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
from app.auth_jwt import create_access_token
import urllib.request

BASE = 'http://127.0.0.1:8201'
TOKEN = create_access_token({'sub': '51'})

def api(path, method='GET', data=None):
    req = urllib.request.Request(
        f'{BASE}{path}',
        data=json.dumps(data).encode() if data else None,
        headers={'Content-Type': 'application/json', 'Authorization': f'Bearer {TOKEN}'},
        method=method
    )
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            body = resp.read().decode()
            print(f'  ✅ {method} {path} -> HTTP {resp.status}')
            return json.loads(body) if body else {}
    except urllib.request.HTTPError as e:
        body = e.read().decode()[:200]
        print(f'  ❌ {method} {path} -> HTTP {e.code}: {body}')
        return None

# 1. Create brochure
print('1. Create Brochure')
result = api('/api/brochures', 'POST', {
    'title': '测试名片',
    'cover': '',
    'purpose': 'partner,client',
    'album_meta': None,
    'pages': [{
        'content_type': 'profile',
        'content': json.dumps({'name': '测试'}),
        'sort_order': 0, 'image_url': '', 'media_url': '', 'ai_summary': ''
    }]
})

if result and result.get('id'):
    bid = result['id']
    print(f'   Brochure ID: {bid}')
    
    # 2. Get it
    print('\\n2. Get Brochure')
    api(f'/api/brochures/{bid}')

# 3. Match recommend
print('\\n3. Match Recommend')
api('/api/match/recommend?min_score=0.3')

# 4. Match records
print('\\n4. Match Records')
api('/api/match/records')

print('\\n=== All tests done ===')
