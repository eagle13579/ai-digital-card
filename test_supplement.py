#!/usr/bin/env python
"""
Supplemental tests for failed scenarios.
"""
import json, urllib.request, urllib.error, sys, random

BASE = "http://localhost:8002"

def api(method, path, data=None, token=None, base=BASE, timeout=30, raw_text=False):
    url = base + path
    body = json.dumps(data).encode() if data else None
    req = urllib.request.Request(url, data=body, method=method)
    req.add_header("Content-Type", "application/json")
    if token:
        req.add_header("Authorization", "Bearer " + token)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            raw = resp.read()
            if raw_text:
                return {"status": resp.status, "data": raw.decode("utf-8", errors="replace")[:800]}
            out = json.loads(raw) if raw else {}
            return {"status": resp.status, "data": out}
    except urllib.error.HTTPError as e:
        raw = e.read()
        try:
            return {"status": e.code, "error": json.loads(raw)}
        except json.JSONDecodeError:
            return {"status": e.code, "error": raw.decode("utf-8", errors="replace")[:500]}
    except Exception as e:
        return {"status": -1, "error": str(e)}

# Step 1: Register a new user
su = random.randint(10000000, 99999999)
phone = "139" + str(random.randint(10000000, 99999999))
reg = {"phone": phone, "password": "Test123!", "name": "supplement_user_" + str(su), "company": "TestCorp", "title": "CTO"}
r1 = api("POST", "/api/v1/auth/register", reg)
print("1. Register: HTTP " + str(r1['status']))
token_val = ""
uid = 0
if r1['status'] == 200:
    d = r1['data']
    token_val = d.get("access_token", "")
    uid = d.get("user", {}).get("id", 0)
    print("   Token: " + token_val[:30] + "..., UID: " + str(uid))

if not token_val:
    print("FATAL: no token")
    sys.exit(1)

# Step 2: Create our own brochure
br = {"title": "My Smart Card " + str(su), "description": "Personal brand", "template": "modern", "tags": ["AI", "Tech"],
      "pages": [{"title": "About", "content": "AI expert"}, {"title": "Skills", "content": "Product, Tech"}]}
r2 = api("POST", "/api/v1/brochures", br, token=token_val)
print("2. Create brochure: HTTP " + str(r2['status']))
bid = 0
if r2['status'] == 200:
    bid = r2['data'].get('id', 0)
    print("   Brochure ID: " + str(bid))

# Step 3: Publish our brochure
if bid:
    r3 = api("POST", "/api/v1/brochures/" + str(bid) + "/publish", token=token_val)
    print("3. Publish brochure: HTTP " + str(r3['status']))
    st = ""
    if r3['status'] == 200:
        st = r3['data'].get("share_token", "")
        print("   Share Token: " + str(st))
        if st:
            r4 = api("GET", "/view/" + st, raw_text=True, timeout=10)
            print("4. Share page: HTTP " + str(r4['status']) + ", len=" + str(len(r4.get('data',''))))
            preview = r4.get('data','')[:300]
            print("   Preview: " + preview)

# Step 5: Root page (returns HTML)
r5 = api("GET", "/", raw_text=True)
print("\n5. Root page: HTTP " + str(r5['status']))
if r5['status'] == 200:
    content = r5.get('data','')
    if '<html' in content.lower() or '<!doctype' in content.lower():
        print("   HTML page, length: " + str(len(content)) + " chars")
        print("   First 200: " + content[:200])
    elif 'service' in content:
        print("   JSON: " + content[:200])

# Step 6: Supply-demand match via GET
paths_to_try = ["/api/v1/match/search?q=AI&top_k=5", "/api/match/search?q=AI",
                "/api/v1/supply-demand/search?q=AI", "/api/v1/match/supply-demand?q=AI"]
for path in paths_to_try:
    r6 = api("GET", path, token=token_val)
    print("6. Supply-demand GET " + path + ": HTTP " + str(r6['status']))
    if r6['status'] == 200:
        break

# Step 7: Share link generation via GET
for path in ["/api/v1/brochures/" + str(bid) + "/share-link",
             "/api/v1/brochures/share-link?brochure_id=" + str(bid),
             "/api/v1/brochures/" + str(bid) + "/share"]:
    r7 = api("GET", path, token=token_val)
    print("7. Share link GET " + path + ": HTTP " + str(r7['status']))
    if r7['status'] == 200:
        break

# Step 8: Recommend via GET
r8 = api("GET", "/api/v1/recommend/personal?top_k=5&strategy=hybrid", token=token_val)
print("8. Recommend GET: HTTP " + str(r8['status']))
if r8['status'] != 200:
    print("   Details: " + str(r8.get('error', r8.get('data', ''))))

# Step 9: Membership plans via different paths
for p in ["/api/v1/membership/plans", "/api/membership/plans"]:
    r9 = api("GET", p, token=token_val)
    print("9. Membership " + p + ": HTTP " + str(r9['status']))

# Step 10: Logout
for m in ["POST", "GET"]:
    r10 = api(m, "/api/v1/auth/logout", token=token_val)
    print("10. Logout " + m + ": HTTP " + str(r10['status']))
    if r10['status'] in (200, 204):
        break

print("\nSupplemental tests done.")
