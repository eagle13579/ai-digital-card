#!/usr/bin/env python3
"""Bandit analysis helper - parses bandit txt output to find all issues with locations."""
import subprocess
import sys
import re

result = subprocess.run(
    ['bandit', '-r', 'app', 'ai_service', 'models', 'scripts', 'sdk', '-f', 'txt'],
    capture_output=True, text=True, timeout=120
)
output = result.stdout

# Parse: each issue block starts with ">> Issue:" and has "Location:" line
lines = output.split('\n')
issues = []
current = {}
for line in lines:
    m = re.search(r'\[(B\d+):([^\]]+)\]', line)
    if m:
        current['test_id'] = m.group(1)
        current['title'] = m.group(2)
    if 'Location:' in line:
        loc_match = re.search(r'Location: (.*)', line)
        if loc_match:
            current['location'] = loc_match.group(1).strip()
        if current.get('test_id'):
            issues.append(current.copy())
        current = {}

# Group by test_id
from collections import Counter, defaultdict
tc = Counter()
loc_by_tid = defaultdict(list)
for iss in issues:
    tid = iss.get('test_id', 'UNKNOWN')
    tc[tid] += 1
    loc_by_tid[tid].append(iss.get('location', '?'))

print(f'=== Total non-test issues: {len(issues)} ===')
print()
for tid in sorted(tc.keys()):
    print(f'{tid}: {tc[tid]}')
    for loc in sorted(loc_by_tid[tid]):
        print(f'    {loc}')
    print()
