#!/usr/bin/env python
"""Test the share page and other endpoints that need deeper investigation."""
import urllib.request, json, ssl

def fetch(url, timeout=30):
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    try:
        req = urllib.request.Request(url)
        with urllib.request.urlopen(req, timeout=timeout, context=ctx) as resp:
            raw = resp.read()
            return {"status": resp.status, "data": raw.decode("utf-8", errors="replace")}
    except Exception as e:
        return {"status": -1, "error": str(e), "data": str(e)}

print("=" * 60)
print("  Deep verification of share page")
print("=" * 60)

# Use the share token from previous test
share_token = "e75bc82c48184a9f"
url = "http://localhost:8002/view/" + share_token
print("Fetching: " + url)
r = fetch(url, timeout=60)
print("Status: " + str(r['status']))
if r['status'] == 200:
    data = r['data']
    print("Length: " + str(len(data)))
    if '<html' in data.lower() or '<!doctype' in data.lower():
        print("✅ Returns HTML page")
        # Extract title
        import re
        titles = re.findall(r'<title>(.*?)</title>', data)
        print("Title: " + str(titles))
        # Show first 500 chars
        print("Preview:")
        print(data[:500])
    else:
        print("Response: " + data[:300])
else:
    print("Error: " + r.get('error', str(r)))
    print("Data: " + r.get('data', '')[:500])

# Also test with non-existent token
print("\n--- Non-existent share token ---")
r2 = fetch("http://localhost:8002/view/nonexistent123", timeout=10)
print("Status: " + str(r2['status']))
print("Preview: " + str(r2.get('data', ''))[:300])

# Test API health
print("\n--- API health ---")
r3 = fetch("http://localhost:8002/health")
print("Health: " + r3.get('data', '')[:200])

# Test API docs JSON
r4 = fetch("http://localhost:8002/openapi.json")
print("\nAPI docs JSON: " + ("✅ loaded, size=" + str(len(r4.get('data','')))) if r4['status']==200 else "❌ failed")
