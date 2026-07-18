"""Check if platform tables exist in local DB"""
import sqlite3
import os

db_path = os.path.join('D:\\AI数智名片\\backend\\data', 'digital_brochure.db')
if not os.path.exists(db_path):
    print(f"DB not found at {db_path}")
    exit(1)

conn = sqlite3.connect(db_path)
c = conn.cursor()
c.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = [row[0] for row in c.fetchall()]
print(f"Total tables: {len(tables)}")
print(f"Tables: {sorted(tables)}")
has_platform = any('platform' in t.lower() for t in tables)
print(f"\nplatform table found: {'✅ YES' if has_platform else '❌ NO'}")
conn.close()
