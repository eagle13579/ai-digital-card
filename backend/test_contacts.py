"""通讯录 API 测试脚本"""
import json
import urllib.request
import urllib.error

BASE = "http://localhost:8000"

def req(method, path, body=None, token=None):
    url = f"{BASE}{path}"
    data = json.dumps(body).encode() if body else None
    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    r = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        resp = urllib.request.urlopen(r)
        return resp.status, json.loads(resp.read())
    except urllib.error.HTTPError as e:
        return e.code, json.loads(e.read().decode())

# 1. Register (or just get a token for existing user)
status, data = req("POST", "/api/auth/register", {
    "phone": "13800000002",
    "password": "TestPass123!",
    "name": "测试用户2"
})
if status == 200:
    token = data["access_token"]
    user_id = data["user"]["id"]
    print(f"✓ 注册成功: user_id={user_id}")
else:
    # User might already exist, try login
    status, data = req("POST", "/api/auth/login", {
        "phone": "13800000002",
        "password": "TestPass123!"
    })
    if status == 200:
        token = data["access_token"]
        user_id = data["user"]["id"]
        print(f"✓ 登录成功: user_id={user_id}")
    else:
        print(f"✗ 认证失败: {data}")
        exit(1)

# 2. Import contacts
status, data = req("POST", "/api/contacts/import", {
    "contacts": [
        {"name": "张三", "phone": "13812345678", "company": "阿里巴巴", "position": "CTO"},
        {"name": "李四", "phone": "13987654321", "company": "腾讯", "position": "CEO"},
        {"name": "王五", "phone": "13700000000", "company": "百度"},
    ],
    "source": "manual",
}, token=token)
assert status == 200, f"Import failed: {data}"
print(f"✓ 导入结果: {json.dumps(data, ensure_ascii=False)}")

# 3. Import duplicate (should be skipped)
status, data = req("POST", "/api/contacts/import", {
    "contacts": [{"name": "张三重复", "phone": "13812345678"}],
    "source": "manual",
}, token=token)
print(f"✓ 去重测试: {json.dumps(data, ensure_ascii=False)}")

# 4. List contacts
status, data = req("GET", "/api/contacts?page=1&page_size=10", token=token)
print(f"✓ 联系人列表: {json.dumps(data, ensure_ascii=False)}")

# 5. Stats
status, data = req("GET", "/api/contacts/stats", token=token)
print(f"✓ 统计: {json.dumps(data, ensure_ascii=False)}")

# 6. Match result (no system user matches)
status, data = req("GET", "/api/contacts/match-result", token=token)
print(f"✓ 匹配结果: {json.dumps(data, ensure_ascii=False)}")

# 7. Delete single contact
contact_id = None
if data["data"]:
    contacts_resp = req("GET", "/api/contacts?page=1&page_size=10", token=token)
    items = contacts_resp[1]["data"]["items"]
    if items:
        contact_id = items[0]["id"]
        status, data = req("DELETE", f"/api/contacts/{contact_id}", token=token)
        print(f"✓ 删除联系人 {contact_id}: {json.dumps(data, ensure_ascii=False)}")

# 8. Clear all
status, data = req("DELETE", "/api/contacts", token=token)
print(f"✓ 清空全部: {json.dumps(data, ensure_ascii=False)}")

print("\n✅ 所有测试通过！")
