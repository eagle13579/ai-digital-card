#!/usr/bin/env python
"""
create_sample_data.py — 创建示例训练数据文件（以人类可读格式展示数据管道输出）
"""

import json
from pathlib import Path

DATA_PATH = Path(__file__).resolve().parent.parent / "data" / "training_data.json"
SAMPLE_PATH = Path(__file__).resolve().parent.parent / "data" / "training_data_sample.json"

with open(DATA_PATH, "r", encoding="utf-8") as f:
    data = json.load(f)

# 取10个样本（5正5负，尽可能覆盖不同用户对）
meta = data["meta"]
samples = data["samples"]

# 按label分组，各取前5
pos_samples = [s for s in samples if s["label"] == 1][:5]
neg_samples = [s for s in samples if s["label"] == 0][:5]

sample_output = {
    "meta": {
        "total_samples": len(pos_samples) + len(neg_samples),
        "positive_count": len(pos_samples),
        "negative_count": len(neg_samples),
        "feature_names": meta["feature_names"],
        "n_users": meta["n_users"],
        "user_ids": meta["user_ids"],
        "description": "这是训练数据示例（10条），完整训练数据包含104条。"
                       "正样本来自match_records中得分≥0.3的配对，"
                       "负样本从未匹配的用户对中随机采样。",
    },
    "samples": pos_samples + neg_samples,
}

with open(SAMPLE_PATH, "w", encoding="utf-8") as f:
    json.dump(sample_output, f, ensure_ascii=False, indent=2)

print(f"[完成] 示例数据已保存: {SAMPLE_PATH}")
print(f"  包含 {len(pos_samples)} 个正样本 + {len(neg_samples)} 个负样本")
