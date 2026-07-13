"""测试auth 500的根因"""
import os, sys
sys.path.insert(0, 'D:/AI数智名片/backend')
os.environ['DATABASE_URL'] = 'sqlite+aiosqlite:///./data/digital_brochure.db'

from app import create_app
from fastapi.testclient import TestClient

app = create_app()
client = TestClient(app)

print("=" * 60)
print("测试1: Register with phone")
r = client.post('/api/auth/register', json={
    'email': 'test_auth@test.com',
    'password': 'Test1234!',
    'name': 'AuthTester',
    'phone': '13800138000'
})
print(f"Status: {r.status_code}")
print(f"Body: {r.text[:1000]}")
print()

print("测试2: Login")
r = client.post('/api/auth/login', json={
    'email': 'test_auth@test.com',
    'password': 'Test1234!'
})
print(f"Status: {r.status_code}")
print(f"Body: {r.text[:1000]}")
