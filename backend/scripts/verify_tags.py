"""
验证 — 最终标签分布
"""
import sqlite3

DB_PATH = "data/digital_brochure.db"

conn = sqlite3.connect(DB_PATH)
cur = conn.cursor()

print("=== 最终标签分布（用户1-15）===")
cur.execute("""
    SELECT u.id, u.name, u.company, u.title,
           (SELECT COUNT(*) FROM user_tags WHERE user_id = u.id AND tag_type = 'provide' AND source = 'ai') as ai_provide,
           (SELECT COUNT(*) FROM user_tags WHERE user_id = u.id AND tag_type = 'need' AND source = 'ai') as ai_need,
           (SELECT COUNT(*) FROM user_tags WHERE user_id = u.id AND tag_type = 'provide' AND source = 'manual') as manual_provide,
           (SELECT COUNT(*) FROM user_tags WHERE user_id = u.id AND tag_type = 'need' AND source = 'manual') as manual_need
    FROM users u WHERE u.id BETWEEN 1 AND 15 ORDER BY u.id
""")
for row in cur.fetchall():
    print(f"ID={row[0]:2d} | {row[1]:8s} | {row[2]:20s} | "
          f"AI提供={row[3]} AI需求={row[4]} | "
          f"手工提供={row[5]} 手工需求={row[6]}")

cur.execute("SELECT COUNT(*) FROM user_tags")
total = cur.fetchone()[0]
cur.execute("SELECT COUNT(*), source FROM user_tags GROUP BY source")
print(f"\n=== 标签汇总: 共 {total} 条 ===")
for r in cur.fetchall():
    print(f"  source={r[1]}: {r[0]} 条")

print("\n=== 行业标签分布 ===")
cur.execute("""
    SELECT u.name, u.company, ut.tag as industry_tag
    FROM user_tags ut
    JOIN users u ON u.id = ut.user_id
    WHERE ut.source = 'ai' AND ut.tag_type = 'provide' AND ut.tag IN (
        'AI/大数据/软件', '新能源/储能', '物流/供应链', '智能制造/精密制造',
        '品牌设计/创意', '投资/金融', '电商/跨境电商', '传媒/营销',
        '法律/合规服务', '财税/审计服务', '管理咨询/战略', '软件开发/IT服务', '纺织制造'
    )
    ORDER BY u.id
""")
for r in cur.fetchall():
    print(f"  {r[0]:8s} ({r[1]:20s}) → {r[2]}")

conn.close()
