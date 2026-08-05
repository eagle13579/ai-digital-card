"""生产验证脚本"""
import sqlite3, os

DB = os.path.join(os.path.dirname(__file__), '..', 'data', 'digital_brochure.db')
db = sqlite3.connect(DB)

print("=== 数据库验证 ===")
print(f"匹配记录: {db.execute('SELECT COUNT(*) FROM match_records').fetchone()[0]}")
garbage = db.execute("SELECT COUNT(*) FROM match_records WHERE common_tags='[]' OR common_tags=''").fetchone()[0]
print(f"空标签垃圾: {garbage}")

c = db.execute("SELECT COUNT(*) FROM connections WHERE status='accepted'").fetchone()[0]
print(f"已接受连接: {c}")
c2 = db.execute("SELECT COUNT(*) FROM connections").fetchone()[0]
print(f"总连接数: {c2}")

print("\n=== 匹配来源分布 ===")
for r in db.execute("SELECT source, status, COUNT(*) FROM match_records GROUP BY source, status"):
    print(f"  {r[0]}/{r[1]}: {r[2]}")

print("\n=== 连接详情 ===")
for r in db.execute("""
    SELECT c.id, u1.name, u2.name, c.status, c.strength
    FROM connections c
    JOIN users u1 ON c.user_id = u1.id
    JOIN users u2 ON c.contact_id = u2.id
    ORDER BY c.id LIMIT 10
"""):
    print(f"  #{r[0]} {r[1]} ↔ {r[2]} | {r[3]} | {r[4]:.2f}")

db.close()
print("\n=== 验证完成 ===")
