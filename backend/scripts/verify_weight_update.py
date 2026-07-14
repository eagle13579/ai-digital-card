#!/usr/bin/env python
"""运行在线学习管道并验证权重真正变化"""

import sys, os, json

backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, backend_dir)
os.chdir(backend_dir)

# 1. Reset service singleton
from app.services.online_learning_service import reset_online_learning_service
reset_online_learning_service()

# 2. Get fresh optimizer
from app.models.ml.tower_ensemble import OnlineWeightOptimizer

# Create a fresh optimizer and directly verify weight updates work
opt = OnlineWeightOptimizer(lr=0.1, baseline_decay=0.9)  # higher lr for visibility

print("=" * 60)
print("  在线权重优化器 — 直接验证 (lr=0.1)")
print("=" * 60)

print(f"\n初始权重: {opt.get_weights()}")
print(f"初始基线: {opt.reward_baseline:.4f}")

# Simulate 5 feedback rounds with real click reward
rewards = [1.0, 1.0, 2.0, -0.5, 0.5]  # click, click, unlock, ignore, rate
for i, r in enumerate(rewards):
    sim = 0.5 + (max(-0.5, min(2.0, r)) / 2.5) * 0.4
    new_w = opt.update(sim_user_ent=sim, sim_behavior_ent=sim, sim_user_behavior=sim, reward=r)
    print(f"  第{i+1}次: reward={r:+.1f} α={new_w['alpha']:.4f} β={new_w['beta']:.4f} γ={new_w['gamma']:.4f} "
          f"基线={opt.reward_baseline:.4f}")

print(f"\n最终权重: {opt.get_weights()}")

# Now run the pipeline with the real optimizer
reset_online_learning_service()

# Patch the global optimizer's lr temporarily
from app.services.online_learning_service import get_online_learning_service
svc = get_online_learning_service()
svc._weight_optimizer.lr = 0.1

print(f"\n{'='*60}")
print("  通过在线学习管道运行")
print(f"{'='*60}")

from scripts.online_learning_pipeline import OnlineLearningPipeline
pipeline = OnlineLearningPipeline(
    min_feedback=1,
    weights_only=True,
)

report = pipeline.run()
print(f"\n状态: {report.status}")
print(f"处理反馈: {report.feedback_records_processed} 条")
print(f"权重更新次数: {report.total_weight_updates}")
print(f"权重: {report.weights_after}")
print(f"权重变化: {report.weight_changes}")

# Verify it really changed
all_zero = all(abs(v) < 0.0001 for v in report.weight_changes.values())
if not all_zero:
    print("\n✅ 权重已真正更新 (变化非零)")
else:
    print("\n⚠ 权重变化为接近零 (reward太小或sim=0.5导致梯度为零)")

# Also show with more precision
print(f"\n详细权重:")
for k in ["alpha", "beta", "gamma"]:
    before = report.weights_before.get(k, 0)
    after = report.weights_after.get(k, 0)
    change = after - before
    print(f"  {k}: {before:.6f} → {after:.6f} (变化: {change:+.6f})")
