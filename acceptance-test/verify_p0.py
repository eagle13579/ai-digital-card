"""测试注册API修复"""
import os, sys
sys.path.insert(0, 'D:/AI数智名片/backend')
os.environ['DATABASE_URL'] = 'sqlite+aiosqlite:///./data/digital_brochure.db'

from app import create_app
from fastapi.testclient import TestClient

app = create_app()
client = TestClient(app)

print("=" * 60)
print("测试1: Register")
r = client.post('/api/auth/register', json={
    'email': 'p0test@test.com',
    'password': 'Test1234!',
    'name': 'P0Tester',
    'phone': '13800138000'
})
print(f"Status: {r.status_code}")
print(f"Body: {r.text[:1000]}")
print()

if r.status_code == 200:
    import json
    data = r.json()
    token = data.get('access_token')
    print(f"Token: {token[:30]}..." if token else "NO TOKEN")
    
    print("\n测试2: Login")
    r2 = client.post('/api/auth/login', json={
        'email': 'p0test@test.com',
        'password': 'Test1234!',
        'phone': '13800138000'
    })
    print(f"Status: {r2.status_code}")
    print(f"Body: {r2.text[:500]}")
    
    if r2.status_code == 200:
        data2 = r2.json()
        token2 = data2.get('access_token')
        print(f"\n测试3: 获取心智模型 (需认证)")
        headers = {'Authorization': f'Bearer {token2}'}
        r3 = client.get('/api/knowledge-models', headers=headers)
        print(f"Status: {r3.status_code}")
        print(f"Body: {r3.text[:500]}")
