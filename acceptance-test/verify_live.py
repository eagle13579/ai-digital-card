"""Verify P0 fixes on live server"""
import requests, json

BASE = "http://localhost:8201"

print("=" * 60)
print("P0验证: 实时测试")
print("=" * 60)

# 1. Health
r = requests.get(f"{BASE}/health")
print(f"\n1. HEALTH: {r.status_code} {r.text}")

# 2. Register
r = requests.post(f"{BASE}/api/auth/register", json={
    "email": "p0v@test.com", "password": "P0Verify123!",
    "name": "P0Verify", "phone": "13800138099"
}, timeout=10)
print(f"\n2. REGISTER: {r.status_code}")
if r.status_code == 200:
    d = r.json()
    token = d.get("access_token", "")[:30]
    print(f"   Token: {token}...")
    uid = d.get("user", {}).get("id")
    print(f"   UserID: {uid}")
    
    # 3. Login
    r2 = requests.post(f"{BASE}/api/auth/login", json={
        "email": "p0v@test.com", "password": "P0Verify123!",
        "phone": "13800138099"
    }, timeout=10)
    print(f"\n3. LOGIN: {r2.status_code}")
    
    # 4. Knowledge Models (was ORM 500)
    headers = {"Authorization": f"Bearer {token}"}
    r3 = requests.get(f"{BASE}/api/knowledge-models", headers=headers, timeout=10)
    print(f"\n4. KNOWLEDGE MODELS: {r3.status_code} (was ORM 500)")
    
    # 5. CRM (was ORM 500)
    r4 = requests.get(f"{BASE}/api/crm/contacts", headers=headers, timeout=10)
    print(f"\n5. CRM CONTACTS: {r4.status_code} (was ORM 500)")
    
    # 6. GDPR
    r5 = requests.get(f"{BASE}/api/gdpr/data", headers=headers, timeout=10)
    print(f"\n6. GDPR DATA: {r5.status_code} (was 404)")
else:
    print(f"   Body: {r.text[:300]}")

# 7. CSRF - Bot webhook (was 403)
r6 = requests.post(f"{BASE}/api/bot/webhook/slack", json={"challenge": "test"}, timeout=10)
print(f"\n7. BOT WEBHOOK: {r6.status_code} (was CSRF 403)")

# 8. Public (no auth needed)
r7 = requests.get(f"{BASE}/api/payment/products", timeout=10)
print(f"\n8. PAYMENT PRODUCTS: {r7.status_code}")

print("\n" + "=" * 60)
print("验证完成")
