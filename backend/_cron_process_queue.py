#!/usr/bin/env python3
"""Process delegation queue for employee evolution - Step 3"""
import json
import os

QUEUE_PATH = r"D:/向海容的知识库/wiki/wiki/记忆宫殿/cache/gaia_delegation_queue.json"

with open(QUEUE_PATH, 'r', encoding='utf-8') as f:
    data = json.load(f)

items = data.get('delegations', [])
print(f"Total items in queue: {len(items)}")

# Filter: P0, source=employee_evolution_engine, auto_assign=True, status=pending
matching = []
for i in items:
    if (i.get('priority') == 'P0' and
        i.get('source') == 'employee_evolution_engine' and
        i.get('auto_assign') is True and
        i.get('status') == 'pending'):
        matching.append(i)

print(f"Matching P0/auto_assign/pending items: {len(matching)}")

# Take up to 5
to_consume = matching[:5]
print(f"\nConsuming {len(to_consume)} items:")

assigned_tasks = []
for m in to_consume:
    name = m['employee_name']
    dept = m['department']
    task_type = m['task_label']
    emp_dir = m['employee_dir']
    
    # Build a simple goal (<=200 characters)
    if '文档' in task_type or '知识' in task_type:
        goal = f"撰写一份{dept}知识整理笔记，总结当前{dept}的关键知识点和工具链，300-500字，作为L0→L1晋升材料。"
    elif '运营' in task_type:
        goal = f"梳理{dept}日常运营SOP流程，整理成结构化文档（步骤+责任人+工具），200-400字。"
    elif '测试' in task_type or '技术' in task_type:
        goal = f"编写一份{dept}技术组件测试清单，覆盖核心功能点，记录测试方法和预期结果，200-400字。"
    elif '市场' in task_type or '调研' in task_type:
        goal = f"完成一份{dept}市场趋势简析报告，列出3个关键方向并附简要说明，200-400字。"
    elif '法务' in task_type or '合规' in task_type:
        goal = f"整理一份{dept}合规检查清单，覆盖主要风险点，200-400字。"
    elif '财务' in task_type:
        goal = f"完成一份简单的{dept}财务模型框架说明，列出关键假设和计算公式，200-400字。"
    else:
        goal = f"完成一份{dept}工作知识整理报告，总结核心流程和经验要点，200-400字。"
    
    # Truncate to 200 chars if needed
    if len(goal) > 200:
        goal = goal[:197] + "..."
    
    m['status'] = 'consumed'
    m['consumed_at'] = '2026-07-14T01:11:35+00:00'
    m['assigned_goal'] = goal
    
    assigned_tasks.append({
        'employee': name,
        'department': dept,
        'task': task_type,
        'goal': goal,
        'employee_dir': emp_dir
    })
    
    print(f"  ✓ {name} ({dept}) → {task_type}")
    print(f"    Goal: {goal}")

# Write back
os.makedirs(os.path.dirname(QUEUE_PATH), exist_ok=True)
with open(QUEUE_PATH, 'w', encoding='utf-8') as f:
    json.dump(data, f, ensure_ascii=False, indent=2)

print(f"\n=== Summary ===")
print(f"Items consumed: {len(to_consume)}")
print(f"Items remaining pending: {len(matching) - len(to_consume)}")
print(f"Total queue size: {len(items)}")

# Output JSON for parsing
print("\n---JSON_OUTPUT---")
print(json.dumps({
    "consumed": len(to_consume),
    "remaining_matching": len(matching) - len(to_consume),
    "total_queue": len(items),
    "assigned": assigned_tasks
}, ensure_ascii=False))
