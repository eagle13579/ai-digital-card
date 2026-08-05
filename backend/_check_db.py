import sqlite3, os

os.chdir('D:/AI数智名片/backend')

# Check feedback.db
db = 'data/feedback.db'
conn = sqlite3.connect(db)
total = conn.execute('SELECT COUNT(*) FROM feedback').fetchone()[0]
pos = conn.execute('SELECT COUNT(*) FROM feedback WHERE rating>0').fetchone()[0]
neg = conn.execute('SELECT COUNT(*) FROM feedback WHERE rating<0').fetchone()[0]
print(f'feedback.db: total={total}, positive={pos}, negative={neg}')
meta = conn.execute('SELECT * FROM feedback_meta').fetchall()
print(f'meta rows: {meta}')
conn.close()

# Check online_learning.db
db2 = 'data/online_learning.db'
conn2 = sqlite3.connect(db2)
tables = conn2.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()
print(f'\nonline_learning.db tables: {[t[0] for t in tables]}')
for t in [t[0] for t in tables]:
    cnt = conn2.execute(f'SELECT COUNT(*) FROM "{t}"').fetchone()[0]
    print(f'  {t}: {cnt} rows')
conn2.close()
