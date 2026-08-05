"""测试 brochure create API"""
import sys, json, os
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))

from app.auth_jwt import create_access_token
import urllib.request

BASE = 'http://127.0.0.1:8201'
token = create_access_token({'sub': '51'})

payload = json.dumps({
    'title': '测试的电子名片',
    'cover': '',
    'purpose': 'partner,client',
    'album_meta': None,
    'pages': [{
        'content_type': 'profile',
        'content': json.dumps({'name': '测试', 'title': 'CEO'}),
        'sort_order': 0,
        'image_url': '',
        'media_url': '',
        'ai_summary': '',
    }]
})

req = urllib.request.Request(
    f'{BASE}/api/brochures',
    data=payload.encode(),
    headers={
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {token}'
    },
    method='POST'
)

try:
    with urllib.request.urlopen(req, timeout=15) as resp:
        result = resp.read().decode()
        print(f'HTTP {resp.status}')
        print(f'Result: {result[:500]}')
except urllib.request.HTTPError as e:
    print(f'HTTP ERROR {e.code}')
    print(f'Body: {e.read().decode()[:1000]}')
except Exception as e:
    print(f'Error: {e}')
