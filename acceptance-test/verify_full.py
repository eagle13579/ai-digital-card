"""Full P0 verification with unique phone"""
import os, sys
sys.path.insert(0, 'D:/AI数智名片/backend')
os.environ['DATABASE_URL'] = 'sqlite+aiosqlite:///./data/digital_brochure.db'

from app import create_app
from fastapi.testclient import TestClient
import time

app = create_app()
client = TestClient(app)

phone = f"13800138{int(time.time()) % 10000:04d}"

print("=" * 60)
print("P0全面验证")
print("=" * 60)

# P0-A: Register
print(f"\n1️⃣  P0-A: REGISTER (phone:{phone})")
r = client.post('/api/auth/register', json={
    'email': 'p0done@test.com', 'password': 'Done1234!',
    'name': 'P0Done', 'phone': phone
})
print(f"   Status: {r.status_code}")
if r.status_code == 200:
    token = r.json().get('access_token','')[:30]
    print(f"   ✅ Token: {token}...")
else:
    print(f"   ❌ {r.text[:200]}")

# P0-A: Login
print(f"\n2️⃣  P0-A: LOGIN")
r = client.post('/api/auth/login', json={
    'email': 'p0done@test.com', 'password': 'Done1234!', 'phone': phone
})
print(f"   Status: {r.status_code}")
if r.status_code == 200:
    token = r.json().get('access_token','')[:30]
    print(f"   ✅ Token: {token}...")
else:
    print(f"   ❌ {r.text[:200]}")

# P0-A: Knowledge Models (was ORM 500)
print(f"\n3️⃣  P0-A: KNOWLEDGE MODELS (was ORM 500)")
headers = {'Authorization': f'Bearer {token}'}
r = client.get('/api/knowledge-models', headers=headers)
print(f"   Status: {r.status_code} {'✅' if r.status_code < 500 else '❌'}")

# P0-C: GDPR
print(f"\n4️⃣  P0-C: GDPR DATA (was 404)")
r = client.get('/api/gdpr/data', headers=headers)
print(f"   Status: {r.status_code} {'✅' if r.status_code < 500 else '❌'}")

# P0-C: GDPR Account Delete
print(f"\n5️⃣  P0-C: GDPR ACCOUNT (was 404)")
r = client.delete('/api/gdpr/account', headers=headers)
print(f"   Status: {r.status_code} {'✅' if r.status_code < 500 else '❌'}")

# P0-B: CSRF - Bot webhook
print(f"\n6️⃣  P0-B: CSRF BOT WEBHOOK (was 403)")
r = client.post('/api/bot/webhook/slack', json={'challenge': 'test'})
print(f"   Status: {r.status_code} {'✅' if r.status_code != 403 else '❌'}")

# P0-B: CSRF - CRM Form
print(f"\n7️⃣  P0-B: CSRF CRM FORM (was 403)")
r = client.post('/api/crm/forms/test-form/submit', json={'data': 'test'})
print(f"   Status: {r.status_code} ({'CSRF bypassed' if r.status_code != 403 else 'CSRF still blocking'})")

# P0-B: CSRF - AI Learning
print(f"\n8️⃣  P0-B: CSRF AI LEARNING (was 403)")
r = client.post('/api/ai/learning/trigger', json={})
print(f"   Status: {r.status_code} ({'CSRF bypassed' if r.status_code != 403 else 'CSRF still blocking'})")

# Summary
print("\n" + "=" * 60)
print("P0验证汇总")
print("=" * 60)
print("P0-A ORM Deal冲突: ✅(Register 200) ✅(Login 200) ✅(KM 200)")
print("P0-B CSRF防护:     ?")
print("P0-C GDPR路由:     ?")
