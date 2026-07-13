"""诊断CRM 500和GDPR 500的真正原因"""
import os, sys
sys.path.insert(0, 'D:/AI数智名片/backend')
os.environ['DATABASE_URL'] = 'sqlite+aiosqlite:///./data/digital_brochure.db'
from app import create_app
from fastapi.testclient import TestClient

app = create_app()
client = TestClient(app)

# Login first (P0-A fixed!)
r = client.post('/api/auth/register', json={
    'email': 'diag@test.com', 'password': 'Diag1234!',
    'name': 'Diag', 'phone': '13800138009'
})
if r.status_code != 200:
    r = client.post('/api/auth/login', json={
        'email': 'diag@test.com', 'password': 'Diag1234!',
        'phone': '13800138009'
    })
token = r.json()['access_token']
headers = {'Authorization': f'Bearer {token}'}

print("=" * 60)
print(f"Token: {token[:30]}...")

# CRM contacts
print("\n1. CRM /contacts:")
r = client.get('/api/crm/contacts', headers=headers)
print(f"   Status: {r.status_code}")
print(f"   {r.text[:300]}")

# CRM stats
print("\n2. CRM /stats:")
r = client.get('/api/crm/stats', headers=headers)
print(f"   Status: {r.status_code}")
if r.status_code >= 500:
    print(f"   {r.text[:300]}")

# GDPR data
print("\n3. GDPR /data:")
r = client.get('/api/gdpr/data', headers=headers)
print(f"   Status: {r.status_code}")
if r.status_code >= 500:
    print(f"   {r.text[:300]}")

# GDPR account delete 
print("\n4. GDPR /account DELETE:")
r = client.delete('/api/gdpr/account', headers=headers)
print(f"   Status: {r.status_code}")
if r.status_code >= 500:
    print(f"   {r.text[:300]}")

# Try brochure (was also 500)
print("\n5. Brochures GET:")
r = client.get('/api/brochures', headers=headers)
print(f"   Status: {r.status_code}")
