import sys, json, urllib.request
sys.path.insert(0, "/var/www/ai-digital-card/backend")
from app.auth_jwt import create_access_token

token = create_access_token({"sub": "1"})
print(f"Token: {token[:50]}...")

req = urllib.request.Request("https://card.liankebao.top/api/auth/me")
req.add_header("Authorization", f"Bearer {token}")
try:
    resp = urllib.request.urlopen(req, timeout=10)
    data = json.loads(resp.read())
    name = data.get("name", "?")
    print(f"Auth/me: {resp.status} - User: {name}")
except urllib.error.HTTPError as e:
    print(f"Auth/me FAILED: {e.code}")
    print(e.read().decode()[:300])
