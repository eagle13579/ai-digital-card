# -*- coding: utf-8 -*-
"""组装 doc1 最终版: head + 附录A 全量表字段字典"""
import io, sys, re
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

head = open('data/_doc1_head.md', encoding='utf-8').read()
tables = open('data/_doc1_tables.md', encoding='utf-8').read()

out = [head.rstrip(), '', '---', '', '## 附录A: 全量表字段字典（自动化实查）', '']
out.append('> 以下由数据库实查脚本自动生成（sqlite_master + PRAGMA table_info/index_list），字段说明列留空处参见正文各表业务说明。')
out.append('')

sections = re.split(r'\n(?=### )', tables)
for s in sections:
    if s.strip().startswith('### '):
        out.append(s.rstrip())
        out.append('')

full = '\n'.join(out)
open('data/_doc1_final.md', 'w', encoding='utf-8').write(full)
lines = full.count('\n') + 1
print(f'FINAL LINES: {lines}')
