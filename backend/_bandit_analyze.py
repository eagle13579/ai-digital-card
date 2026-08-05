#!/usr/bin/env python3
"""Analyze bandit JSON results, excluding .venv and tests_bak."""
import json
import sys

with open('D:\\AppData\\Local\\Temp\\bandit_results.json', 'r') as f:
    data = json.load(f)

results = data.get('results', [])

# Filter out .venv and tests_bak
project_results = []
for r in results:
    fn = r['filename'].replace('\\', '/')
    if '.venv/' in fn or 'tests_bak/' in fn:
        continue
    project_results.append(r)

from collections import Counter, defaultdict
tc = Counter()
sev_detail = defaultdict(lambda: Counter())
files = Counter()

for r in project_results:
    tid = r.get('test_id', 'UNKNOWN')
    sev = r.get('issue_severity', '?')
    tc[tid] += 1
    sev_detail[tid][sev] += 1
    files[r['filename']] += 1

print(f'=== Total project issues: {len(project_results)} ===')
print()
print('=== By test_id with severity breakdown ===')
for tid in sorted(tc.keys()):
    total = tc[tid]
    details = ', '.join(f'{sev}: {c}' for sev, c in sorted(sev_detail[tid].items()))
    print(f'  {tid}: {total} ({details})')

print()
print('=== Top 25 files with issues ===')
for f, c in files.most_common(25):
    print(f'  {c:4d}  {f}')

# List all unique filenames
print()
print('=== All unique files ===')
for f in sorted(files.keys()):
    print(f'  {files[f]:4d}  {f}')
