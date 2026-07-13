"""
查看所有用户的标签分布情况
"""
import sqlite3

DB_PATH = "data/digital_brochure.db"

conn = sqlite3.connect(DB_PATH)
cur = conn.cursor()

print("=== 用户标签分布 ===")
cur.execute("""
    SELECT u.id, u.name, u.company, u.title,
           (SELECT COUNT(*) FROM user_tags WHERE user_id = u.id AND tag_type = 'provide') as provide_cnt,
           (SELECT COUNT(*) FROM user_tags WHERE user_id = u.id AND tag_type = 'need') as need_cnt
    FROM users u
    ORDER BY u.id
""")
for row in cur.fetchall():
    print(f"ID={row[0]:2d} | {row[1]:8s} | {row[2]:20s} | {row[3]:20s} | provide={row[4]} need={row[5]}")

print("\n=== 用户1-15的所有标签 ===")
cur.execute("SELECT user_id, tag_type, tag, weight, source FROM user_tags WHERE user_id BETWEEN 1 AND 15 ORDER BY user_id, tag_type")
for t in cur.fetchall():
    print(f"  user_id={t[0]:2d} | {t[1]:8s} | {t[2]:20s} | weight={t[3]:.2f} | source={t[4]}")

conn.close()
