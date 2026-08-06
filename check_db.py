import sqlite3
conn = sqlite3.connect('D:\\AI数智名片\\backend\\data\\digital_brochure.db')
cur = conn.execute('PRAGMA table_info(pages)')
cols = cur.fetchall()
print('pages表实际列:')
for c in cols:
    print(f'  {c[1]} ({c[2]}) nullable={c[3]} default={c[4]}')
cur2 = conn.execute('PRAGMA table_info(brochures)')
cols2 = cur2.fetchall()
print('\nbrochures表实际列:')
for c in cols2:
    print(f'  {c[1]} ({c[2]}) nullable={c[3]} default={c[4]}')
print('\npages行数:', conn.execute('SELECT COUNT(*) FROM pages').fetchone()[0])
print('brochures行数:', conn.execute('SELECT COUNT(*) FROM brochures').fetchone()[0])
print('users行数:', conn.execute('SELECT COUNT(*) FROM users').fetchone()[0])
conn.close()
