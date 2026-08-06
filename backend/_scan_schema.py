# -*- coding: utf-8 -*-
"""扫描 digital_brochure.db 全部表结构 -> 输出 JSON 供文档生成使用"""
import sqlite3, json, sys, io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

conn = sqlite3.connect('data/digital_brochure.db')
cur = conn.cursor()

result = {}

# 1. 所有表和索引
cur.execute("SELECT name, sql FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%' ORDER BY name")
tables = cur.fetchall()

for tname, tsql in tables:
    info = {'create_sql': tsql, 'columns': [], 'indexes': [], 'rowcount': None, 'triggers': []}
    # 列信息
    cur.execute(f"PRAGMA table_info('{tname}')")
    for cid, cname, ctype, notnull, dflt, pk in cur.fetchall():
        info['columns'].append({
            'cid': cid, 'name': cname, 'type': ctype,
            'notnull': bool(notnull), 'default': dflt, 'pk': pk
        })
    # 索引
    cur.execute(f"PRAGMA index_list('{tname}')")
    for idx in cur.fetchall():
        idx_name, unique = idx[1], idx[2]
        cur.execute(f"PRAGMA index_info('{idx_name}')")
        cols = [r[2] for r in cur.fetchall()]
        info['indexes'].append({'name': idx_name, 'unique': bool(unique), 'columns': cols})
    # 行数
    try:
        cur.execute(f"SELECT COUNT(*) FROM '{tname}'")
        info['rowcount'] = cur.fetchone()[0]
    except Exception as e:
        info['rowcount'] = f'ERR:{e}'
    result[tname] = info

with open('data/_schema_dump.json', 'w', encoding='utf-8') as f:
    json.dump(result, f, ensure_ascii=False, indent=1)

# 汇总统计
total_cols = sum(len(v['columns']) for v in result.values())
total_idx = sum(len(v['indexes']) for v in result.values())
nonempty = sum(1 for v in result.values() if isinstance(v['rowcount'], int) and v['rowcount'] > 0)
print(f"TABLES={len(result)} COLUMNS={total_cols} INDEXES={total_idx} NONEMPTY_TABLES={nonempty}")
print("=== 有数据的表(行数>0) ===")
for t, v in sorted(result.items(), key=lambda x: -(x[1]['rowcount'] if isinstance(x[1]['rowcount'], int) else 0)):
    if isinstance(v['rowcount'], int) and v['rowcount'] > 0:
        print(f"  {t}: {v['rowcount']}")
