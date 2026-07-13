"""Debug GDPR 500"""
import os, sys
sys.path.insert(0, 'D:/AI数智名片/backend')
os.environ['DATABASE_URL'] = 'sqlite+aiosqlite:///./data/digital_brochure.db'
from app import create_app
from fastapi.testclient import TestClient

app = create_app()
client = TestClient(app)

# Login
r = client.post('/api/auth/login', json={
    'email': 'done@test.com', 'password': 'Done1234!',
    'phone': '13800138008'
})
token = r.json()['access_token']
headers = {'Authorization': f'Bearer {token}'}

print("=== GDPR DATA ===")
r = client.get('/api/gdpr/data', headers=headers)
print(f"Status: {r.status_code}")
print(f"Body: {r.text[:500]}")

print("\n=== GDPR LOGS ===")
r = client.get('/api/gdpr/logs', headers=headers)
print(f"Status: {r.status_code}")
print(f"Body: {r.text[:500]}")

print("\n=== CRM ===")
r = client.get('/api/crm/contacts', headers=headers)
print(f"Status: {r.status_code}")
print(f"Body: {r.text[:200]}")
