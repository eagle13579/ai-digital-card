#!/usr/bin/env python
"""在线学习引擎 — 触发学习周期并输出执行报告

等效替代已被移除的 scripts/online_learning_pipeline.py
使用重构后的 app/ai/online_learning.py::OnlineLearningEngine
"""

import sys
import os

backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, backend_dir)
os.chdir(backend_dir)

# 解析参数 — 保留兼容接口
min_feedback = 5
for arg in sys.argv[1:]:
    if arg.startswith("--min-feedback="):
        min_feedback = int(arg.split("=")[1])

from app.ai.feedback_loop import get_feedback_loop
from app.ai.online_learning import get_online_learning_engine, get_all_online_weights, _DEFAULT_WEIGHTS

# 1. 检查反馈量
loop = get_feedback_loop()
stats = loop.get_global_stats()
total = stats.get("total_feedback", 0)
positive = stats.get("positive_feedback", 0)
negative = stats.get("negative_feedback", 0)

print(f"反馈统计: total={total}, positive={positive}, negative={negative}")

if total < min_feedback:
    print(f"\n状态: skipped")
    print(f"反馈数 {total} < min_feedback {min_feedback}, 跳过学习")
    sys.exit(0)

# 2. 读取当前权重
weights_before = get_all_online_weights()
print(f"\n当前全局调整系数: {weights_before.get('global_adjustment', 1.0):.4f}")
print(f"当前权重 (原始): tag_match={_DEFAULT_WEIGHTS.get('tag_match',0)} graph={_DEFAULT_WEIGHTS.get('graph',0)} semantic={_DEFAULT_WEIGHTS.get('semantic',0)}")
print(f"当前权重 (调整后): {weights_before}")

# 3. 执行在线学习
engine = get_online_learning_engine()
report = engine.run_learning_cycle()

# 4. 读取调整后权重
weights_after = get_all_online_weights()

# 5. 输出报告
print(f"\n状态: {report.get('status', 'completed')}")
print(f"学习周期: #{report.get('cycle', 0)}")
print(f"耗时: {report.get('duration_seconds', 0):.3f}s")
print(f"处理反馈数: total={report['feedback_stats']['total']}, "
      f"positive={report['feedback_stats']['positive']}, "
      f"negative={report['feedback_stats']['negative']}, "
      f"新增={report['feedback_stats']['new_since_last']}")

wc = report.get('weight_changes', {})
print(f"\n权重变化:")
old_adj = wc.get('old_global_adjustment', 1.0)
new_adj = wc.get('new_global_adjustment', 1.0)
print(f"  全局调整系数: {old_adj:.4f} → {new_adj:.4f} (变化: {new_adj - old_adj:+.4f})")
for key in ['tag_match', 'graph', 'semantic']:
    old_w = wc.get('old_weights', {}).get(key, 'N/A')
    new_w = wc.get('new_weights', {}).get(key, 'N/A')
    if isinstance(old_w, (int, float)) and isinstance(new_w, (int, float)):
        print(f"  {key}: {old_w:.4f} → {new_w:.4f} (变化: {new_w - old_w:+.4f})")
    else:
        print(f"  {key}: {old_w} → {new_w}")

net_adjust = wc.get('net_adjust', 0)
if abs(net_adjust) < 0.0001:
    print(f"\n⚠ 净调整接近零 — 正负反馈基本平衡或暂无新增反馈")
else:
    direction = "↑ 推荐强度增加" if net_adjust > 0 else "↓ 推荐强度降低"
    print(f"\n✅ 权重已更新: 净调整={net_adjust:+.4f} {direction}")
