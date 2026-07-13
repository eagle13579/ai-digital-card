"""
探索用户数据 — 查看数据库中所有用户及其公司/职位信息
"""
import sqlite3

DB_PATH = "data/digital_brochure.db"

conn = sqlite3.connect(DB_PATH)
cur = conn.cursor()

# Check users
cur.execute("SELECT id, name, company, title, intro FROM users")
users = cur.fetchall()
print(f"=== 用户数: {len(users)} ===")
for u in users:
    print(f"ID={u[0]}, 姓名={u[1]}, 公司={u[2]}, 职位={u[3]}")
    if u[4]:
        print(f"  简介: {u[4][:100]}")
    print()

# Check existing tags
cur.execute("SELECT COUNT(*) FROM user_tags")
cnt = cur.fetchone()[0]
print(f"=== 现有标签数: {cnt} ===")

cur.execute("SELECT * FROM user_tags LIMIT 20")
tags = cur.fetchall()
for t in tags:
    print(f"  ID={t[0]}, user_id={t[1]}, type={t[2]}, tag={t[3]}, weight={t[4]}, source={t[5]}")

# Check brochures
cur.execute("SELECT id, user_id, title, purpose, status FROM brochures")
brochures = cur.fetchall()
print(f"\n=== 画册数: {len(brochures)} ===")
for b in brochures:
    print(f"  ID={b[0]}, user_id={b[1]}, title={b[2]}, purpose={b[3]}, status={b[4]}")

conn.close()
