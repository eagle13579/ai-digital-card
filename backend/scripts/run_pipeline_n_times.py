#!/usr/bin/env python
"""多次运行在线学习管道以累积权重变化"""

import subprocess
import sys
import os

backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(backend_dir)

for i in range(1, 11):
    print(f"\n{'='*60}")
    print(f"  Run #{i}")
    print(f"{'='*60}")
    
    # Reset singleton each time to avoid duplication
    subprocess.run(
        [sys.executable, "scripts/reset_online_service.py"],
        capture_output=True, text=True
    )
    
    result = subprocess.run(
        [sys.executable, "scripts/online_learning_pipeline.py",
         "--weights-only", "--min-feedback", "1"],
        capture_output=True, text=True,
        cwd=backend_dir,
        env={**os.environ, "no_proxy": "*"}
    )
    
    # Extract key lines
    for line in result.stdout.split('\n'):
        if '权重' in line and ('α=' in line or '→' in line or '更新' in line):
            print(f"  {line.strip()}")
    
    if result.returncode != 0:
        print(f"  ⚠ Exit code: {result.returncode}")

print(f"\n{'='*60}")
print("  最终检查: 在线权重变化累计")
print(f"{'='*60}")

# Read the last checkpoint
import json
checkpoint_dir = os.path.join(backend_dir, "models")
checkpoints = sorted([f for f in os.listdir(checkpoint_dir) if f.startswith("online_checkpoint_")])
if checkpoints:
    with open(os.path.join(checkpoint_dir, checkpoints[-1])) as f:
        data = json.load(f)
    print(f"  Checkpoint: {checkpoints[-1]}")
    print(f"  Total weight updates: {data['total_weight_updates']}")
    print(f"  Weights: {data['weights']}")
    print(f"  Weight changes: {data['weight_changes']}")
else:
    print("  No checkpoints found")

# Verify by directly checking the optimizer
sys.path.insert(0, backend_dir)
from app.models.ml.tower_ensemble import OnlineWeightOptimizer
opt = OnlineWeightOptimizer()
print(f"  Fresh optimizer weights: {opt.get_weights()}")
print(f"  Fresh optimizer total_updates: {opt.total_updates}")
