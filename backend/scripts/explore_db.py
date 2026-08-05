"""探索 SQLite 数据库结构"""
import sqlite3

db_path = "D:/AI数智名片/backend/data/digital_brochure.db"
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# 列出所有表
cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = cursor.fetchall()
print(f"数据库中有 {len(tables)} 个表:\n")

for t in tables:
    table_name = t[0]
    print(f"{'='*60}")
    print(f"表名: {table_name}")
    print(f"{'='*60}")
    cursor.execute(f"PRAGMA table_info({table_name})")
    cols = cursor.fetchall()
    for c in cols:
        print(f"  {c}")
    cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
    cnt = cursor.fetchone()[0]
    print(f"  行数: {cnt}")
    
    # 显示前2行样例
    try:
        cursor.execute(f"SELECT * FROM {table_name} LIMIT 2")
        rows = cursor.fetchall()
        if rows:
            col_names = [desc[0] for desc in cursor.description]
            print(f"  列名: {col_names}")
            for r in rows:
                print(f"  样例: {r}")
    except Exception as e:
        print(f"  查询样例时出错: {e}")
    print()

conn.close()
print("数据库探索完成。")
