"""ALTER TABLE to add missing columns to platforms table"""
import sqlite3
import os

db_path = 'D:\\AI数智名片\\backend\\data\\digital_brochure.db'
conn = sqlite3.connect(db_path)
c = conn.cursor()

# Check what columns exist
c.execute('PRAGMA table_info(platforms)')
existing = {row[1] for row in c.fetchall()}
print(f"Existing columns: {sorted(existing)}")

# Columns to add (from the model)
to_add = {
    'province': 'VARCHAR(32)',
    'city': 'VARCHAR(32)',
    'district': 'VARCHAR(32)',
    'contact_name': 'VARCHAR(64)',
    'phone': 'VARCHAR(20)',
    'industries': 'TEXT',
}

added = 0
for col, col_type in to_add.items():
    if col not in existing:
        sql = f'ALTER TABLE platforms ADD COLUMN {col} {col_type} NULL'
        c.execute(sql)
        print(f'✅ Added column: {col} {col_type}')
        added += 1
    else:
        print(f'⏭️  Already exists: {col}')

conn.commit()
conn.close()
print(f'\nTotal: {added} columns added')
