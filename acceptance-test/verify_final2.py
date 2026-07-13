"""Final full verification"""
import os, sys
os.environ['DATABASE_URL'] = 'sqlite+aiosqlite:///./data/digital_brochure.db'
sys.path.insert(0, 'D:/AI数智名片/backend')
from app import create_app
from fastapi.testclient import TestClient

app = create_app()
c = TestClient(app)

r = c.post('/api/auth/register', json={'email':'final2@t.com','password':'Fin1234!','name':'Final','phone':'13800138555'})
if r.status_code != 200:
    r = c.post('/api/auth/login', json={'email':'done@test.com','password':'Done1234!','phone':'13800138008'})
token = r.json()['access_token']
h = {'Authorization': f'Bearer {token}'}

tests = [
    ('Auth Login', c.post('/api/auth/login', json={'email':'done@test.com','password':'Done1234!','phone':'13800138008'}).status_code, 200),
    ('CRM Contacts', c.get('/api/crm/contacts', headers=h).status_code, 200),
    ('GDPR Data', c.get('/api/gdpr/data', headers=h).status_code, 200),
    ('Knowledge Models', c.get('/api/knowledge-models', headers=h).status_code, 200),
    ('Payment Products', c.get('/api/payment/products').status_code, 200),
    ('Privacy /privacy', c.get('/privacy').status_code, 200),
    ('Terms /terms', c.get('/terms').status_code, 200),
    ('Cookies /cookies', c.get('/cookies').status_code, 200),
    ('Bot webhook (CSRF)', c.post('/api/bot/webhook/slack', json={'challenge':'test'}).status_code, 200),
]

print('=== FULL VERIFICATION ===')
all_pass = True
for name, actual, expected in tests:
    status = '✅' if actual == expected else '❌'
    all_pass = all_pass and (actual == expected)
    print(f'  {status} {name}: {actual}')

print(f'\nRoutes: {len(app.routes)}')
print(f'All pass: {"✅ YES" if all_pass else "❌ NO"}')
