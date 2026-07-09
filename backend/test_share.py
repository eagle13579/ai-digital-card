import json, urllib.request, urllib.error

BASE = 'http://localhost:8002'

# Login
req = urllib.request.Request(BASE + '/api/v1/auth/login',
    json.dumps({'phone':'13900001111','password':'Test123!@#'}).encode(),
    {'Content-Type':'application/json'})
with urllib.request.urlopen(req) as r:
    token = json.loads(r.read())['access_token']

# Get brochures
req2 = urllib.request.Request(BASE + '/api/v1/brochures',
    headers={'Authorization': 'Bearer ' + token})
with urllib.request.urlopen(req2) as r:
    data = json.loads(r.read())

if isinstance(data, dict):
    items = data.get('items', data.get('data', []))
elif isinstance(data, list):
    items = data
else:
    items = []

if items:
    br = items[0]
    share_token = br.get('share_token', '') or br.get('shareToken', '')
    print('Found brochure: id=' + str(br.get('id')) + ' share_token=' + share_token)
    
    if share_token:
        req3 = urllib.request.Request(BASE + '/view/' + share_token)
        try:
            with urllib.request.urlopen(req3, timeout=5) as r:
                html = r.read().decode()
                print('Share page: HTTP ' + str(r.getcode()) + ', len=' + str(len(html)))
                has_flip = 'flip' in html.lower() or 'page' in html.lower()
                print('Has flip viewer: ' + str(has_flip))
        except urllib.error.HTTPError as e:
            body = e.read().decode()[:200]
            print('Share page: HTTP ' + str(e.code))
            print('  ' + body)
else:
    print('No brochures found')
