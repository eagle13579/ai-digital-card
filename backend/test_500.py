"""Test the two 500 endpoints and capture full error responses."""
import urllib.request
import json

BASE = "http://localhost:8002"

# 1. Register a test user
reg_data = json.dumps({
    "phone": "13800138006",
    "password": "Test1234!",
    "name": "testuser6"
}).encode()
req = urllib.request.Request(f"{BASE}/api/v1/auth/register", data=reg_data,
                              headers={"Content-Type": "application/json"})
try:
    resp = urllib.request.urlopen(req, timeout=10)
    body = json.loads(resp.read())
    TOKEN = body["access_token"]
    USER_ID = body["user"]["id"]
    print(f"Registered user {USER_ID}, token len={len(TOKEN)}")
except urllib.error.HTTPError as e:
    # User might already exist, try login
    login_data = json.dumps({"phone": "13800138006", "password": "Test1234!"}).encode()
    req = urllib.request.Request(f"{BASE}/api/v1/auth/login", data=login_data,
                                  headers={"Content-Type": "application/json"})
    resp = urllib.request.urlopen(req, timeout=10)
    body = json.loads(resp.read())
    TOKEN = body["access_token"]
    USER_ID = body["user"]["id"]
    print(f"Logged in user {USER_ID}, token len={len(TOKEN)}")

HEADERS = {
    "Content-Type": "application/json",
    "Authorization": f"Bearer {TOKEN}"
}

# 2. Test POST /api/v1/business-card/cards (create_card)
print("\n=== Test 1: POST /api/v1/business-card/cards ===")
card_data = json.dumps({
    "title": "测试名片",
    "pages": [
        {"content_type": "text", "content": "Hello World", "sort_order": 0}
    ]
}).encode()
req = urllib.request.Request(f"{BASE}/api/v1/business-card/cards",
                              data=card_data, headers=HEADERS, method="POST")
try:
    resp = urllib.request.urlopen(req, timeout=15)
    result = json.loads(resp.read())
    print(f"SUCCESS! Status={resp.status}")
    print(f"Result: id={result.get('id')}, title={result.get('title')}, pages={len(result.get('pages', []))}")
    CARD_ID = result["id"]
except urllib.error.HTTPError as e:
    print(f"FAILED! Status={e.code}")
    error_body = e.read().decode()
    print(f"Response body: {error_body}")
    CARD_ID = None

# 3. Test POST /api/v1/brochures/{id}/publish (publish_brochure)
if CARD_ID:
    print(f"\n=== Test 2: POST /api/v1/brochures/{CARD_ID}/publish ===")
    req = urllib.request.Request(f"{BASE}/api/v1/brochures/{CARD_ID}/publish",
                                  data=b"{}", headers=HEADERS, method="POST")
    try:
        resp = urllib.request.urlopen(req, timeout=15)
        result = json.loads(resp.read())
        print(f"SUCCESS! Status={resp.status}")
        print(f"Result: id={result.get('id')}, status={result.get('status')}, pages={len(result.get('pages', []))}")
    except urllib.error.HTTPError as e:
        print(f"FAILED! Status={e.code}")
        error_body = e.read().decode()
        print(f"Response body: {error_body}")
else:
    print("\n=== Test 2: SKIP (need valid card_id) ===")
