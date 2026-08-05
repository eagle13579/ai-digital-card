#!/usr/bin/env python3
"""Analyze evolution_log.jsonl and delegation queue."""
import os, json, sys

log_file = r"D:\向海容的知识库\wiki\wiki\记忆宫殿\cache\evolution_log.jsonl"
queue_file = r"D:\向海容的知识库\wiki\wiki\记忆宫殿\cache\gaia_delegation_queue.json"

# Evolution log analysis
if os.path.exists(log_file):
    sz = os.path.getsize(log_file)
    print(f"evolution_log.jsonl: {sz} bytes ({sz/1024/1024:.1f} MB)")
    
    # Read last 5 lines
    with open(log_file, 'r', encoding='utf-8', errors='replace') as f:
        lines = f.readlines()
    print(f"Total lines: {len(lines)}")
    
    if len(lines) >= 5:
        print("\n=== Last 5 entries ===")
        for line in lines[-5:]:
            try:
                entry = json.loads(line.strip())
                print(f"  [{entry.get('type','?')}] {json.dumps(entry.get('data',{}), ensure_ascii=False)[:200]}")
            except:
                print(f"  [parse error] {line.strip()[:200]}")
    
    # Count by type
    types = {}
    for line in lines:
        try:
            entry = json.loads(line.strip())
            t = entry.get('type', 'unknown')
            types[t] = types.get(t, 0) + 1
        except:
            types['parse_error'] = types.get('parse_error', 0) + 1
    print(f"\nEntries by type: {json.dumps(types, ensure_ascii=False)}")

# Queue analysis
if os.path.exists(queue_file):
    q = json.load(open(queue_file, 'r', encoding='utf-8'))
    dels = q.get('delegations', [])
    print(f"\n=== Queue Analysis ===")
    print(f"Total delegations: {len(dels)}")
    print(f"Pending count: {q.get('total_pending', '?')}")
    print(f"Cycle: {q.get('cycle', '?')}")
    
    # Count by source
    sources = {}
    for d in dels:
        src = d.get('source', 'none')
        sources[src] = sources.get(src, 0) + 1
    print(f"By source: {json.dumps(sources, ensure_ascii=False)}")
    
    # P0 from employee_evolution_engine with auto_assign=True and pending
    targets = [d for d in dels 
               if d.get('source') == 'employee_evolution_engine' 
               and d.get('auto_assign') == True 
               and d.get('status', 'pending') == 'pending']
    print(f"P0 / employee_evolution_engine / auto_assign / pending: {len(targets)}")
    for t in targets:
        print(f"  - {t.get('employee_name','?')} | {t.get('priority','?')} | {t.get('task_type','?')}")
    
    # P0 items (any source)
    p0_all = [d for d in dels if d.get('priority') == 'P0' and d.get('status', 'pending') == 'pending']
    print(f"All P0 pending: {len(p0_all)}")
    for p in p0_all:
        print(f"  - [{p.get('source','?')}] {p.get('employee_name','?')} | {p.get('type','?')}")

# Check if any log says prev cycle had L0>0
print("\n=== Full Cycle History ===")
for line in lines[-20:]:
    try:
        entry = json.loads(line.strip())
        if entry.get('type') == 'full_cycle':
            data = entry.get('data', {})
            levels = data.get('levels', {})
            print(f"  Cycle: L0={levels.get('L0',0)} L1={levels.get('L1',0)} L2={levels.get('L2',0)} L3={levels.get('L3',0)} total={data.get('total','?')} actions={data.get('actions_generated','?')}")
    except:
        pass
