"""探索用户/标签/名片数据详情"""
import sqlite3, json
from collections import Counter

db_path = "D:/AI数智名片/backend/data/digital_brochure.db"
conn = sqlite3.connect(db_path)
conn.row_factory = sqlite3.Row
cursor = conn.cursor()

# 1. 所有用户
print("=" * 60)
print(f"{'用户列表':^60}")
print("=" * 60)
cursor.execute("SELECT id, name, company, membership_tier FROM users ORDER BY id")
users = cursor.fetchall()
for u in users:
    print(f"  ID={u['id']:2d}  {u['name']:<8s}  {str(u['company'])[:20]:<20s}  tier={u['membership_tier']:<6s}")
print(f"  共 {len(users)} 个用户\n")

# 2. 每个用户的标签统计
print("=" * 60)
print(f"{'用户标签统计':^60}")
print("=" * 60)
user_tags_count = {}
user_tags_list = {}
for u in users:
    uid = u['id']
    cursor.execute("SELECT tag, tag_type, weight FROM user_tags WHERE user_id=?", (uid,))
    tags = cursor.fetchall()
    user_tags_count[uid] = len(tags)
    user_tags_list[uid] = [t['tag'] for t in tags]
    top_tag = max(tags, key=lambda t: t['weight'])['tag'] if tags else '无'
    print(f"  ID={uid:2d}  {u['name']:<8s}  标签数={len(tags):3d}  最重标签={top_tag:<12s}")
print()

# 3. 每个用户的名片统计
print("=" * 60)
print(f"{'用户名片统计':^60}")
print("=" * 60)
for u in users:
    uid = u['id']
    cursor.execute("SELECT COUNT(*) as cnt, COALESCE(SUM(view_count),0) as views, "
                   "COALESCE(SUM(pages_count),0) as pages FROM brochures WHERE user_id=?", (uid,))
    row = cursor.fetchone()
    purpose = "无"
    cursor.execute("SELECT purpose FROM brochures WHERE user_id=? LIMIT 1", (uid,))
    p_row = cursor.fetchone()
    if p_row and p_row['purpose']:
        purpose = p_row['purpose']
    print(f"  ID={uid:2d}  {u['name']:<8s}  名片数={row['cnt']:2d}  总浏览={row['views']:4d}  总页数={row['pages']:2d}  用途={purpose:<10s}")
print()

# 4. 标签重叠分析 (构建正样本对)
print("=" * 60)
print(f"{'标签重叠分析 (正样本候选)':^60}")
print("=" * 60)
positive_pairs = []
for i in range(len(users)):
    for j in range(i+1, len(users)):
        ua = users[i]['id']
        ub = users[j]['id']
        tags_a = set(user_tags_list.get(ua, []))
        tags_b = set(user_tags_list.get(ub, []))
        overlap = tags_a & tags_b
        if overlap:
            positive_pairs.append((ua, ub, len(overlap), overlap))
            print(f"  {ua:2d}-{ub:2d}: 共{len(overlap)}个相同标签 -> {overlap}")
print(f"  正样本对总数: {len(positive_pairs)}\n")

# 5. 已有的match_records
print("=" * 60)
print(f"{'已有匹配记录 (match_records)':^60}")
print("=" * 60)
cursor.execute("SELECT mr.*, u1.name as name_a, u2.name as name_b "
               "FROM match_records mr "
               "LEFT JOIN users u1 ON mr.user_a_id=u1.id "
               "LEFT JOIN users u2 ON mr.user_b_id=u2.id "
               "ORDER BY mr.match_score DESC")
matches = cursor.fetchall()
for m in matches:
    print(f"  {m['user_a_id']:2d}({m['name_a']:<6s}) <-> {m['user_b_id']:2d}({m['name_b']:<6s})  "
          f"score={m['match_score']:.2f}  status={m['status']:<8s}  tags={m['common_tags']}")
print(f"  共 {len(matches)} 对匹配记录\n")

conn.close()
