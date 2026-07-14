#!/usr/bin/env python
"""
data_augmentation.py — AI数智名片 V2 训练数据增强脚本（防过拟合核心）

目标: 将训练数据从150条扩充到至少1000条，解决模型AUC=1.0过拟合问题。

策略（不修改数据库，仅操作JSON训练数据）:
  1. Gaussian Noise Injection       — 对特征值添加可控高斯噪声 (±0.01~0.03 std)
  2. SMOTE-style Interpolation      — 同类样本间线性插值生成合成样本
  3. Bootstrap Resampling           — 有放回采样（标签保持）
  4. Feature-wise Perturbation      — 离散特征(common_tag_count)随机偏移
  5. Near-Boundary Mixing           — 正负样本对之间按比例混合生成"困难样本"
  6. Negative Oversampling          — 对负样本特殊增强以缓解数据不平衡

用法:
  python scripts/data_augmentation.py
  python scripts/data_augmentation.py --input data/v2_training_data.json --output_copies 3

输出:
  data/v2_training_data_augmented.json  (增强后的完整数据集)
  data/v2_training_data_augmented_stats.txt (增强统计报告)
"""

import argparse
import json
import math
import os
import random
import sys
import time
from collections import Counter
from copy import deepcopy
from pathlib import Path

import numpy as np

# ── 配置 ─────────────────────────────────────────────────────────────
SEED = 42
random.seed(SEED)
np.random.seed(SEED)

# 特征名称（与 prepare_v2_training_data.py 保持一致）
ALL_FEATURES = [
    "tag_overlap_score", "common_tag_count",
    "overlap_provide_to_need", "overlap_need_to_provide",
    "vector_semantic",
    "tag_count_a", "tag_count_b", "avg_weight_a", "avg_weight_b",
    "tag_weight_score",
    "intro_semantic", "provide_need_balance", "tag_category_overlap",
]

# 连续值特征（可加噪声）
CONTINUOUS_FEATURES = {
    "tag_overlap_score", "overlap_provide_to_need", "overlap_need_to_provide",
    "vector_semantic", "avg_weight_a", "avg_weight_b",
    "tag_weight_score", "intro_semantic",
    "provide_need_balance", "tag_category_overlap",
}

# 离散计数特征（只能整数偏移）
DISCRETE_FEATURES = {
    "common_tag_count", "tag_count_a", "tag_count_b",
}

# 每个特征的典型最大值（用于裁剪，防止生成不合理值）
FEATURE_MAX = {
    "tag_overlap_score": 1.0,
    "common_tag_count": 10,
    "overlap_provide_to_need": 1.0,
    "overlap_need_to_provide": 1.0,
    "vector_semantic": 1.0,
    "tag_count_a": 30,
    "tag_count_b": 30,
    "avg_weight_a": 1.0,
    "avg_weight_b": 1.0,
    "tag_weight_score": 1.0,
    "intro_semantic": 1.0,
    "provide_need_balance": 1.0,
    "tag_category_overlap": 1.0,
}

FEATURE_MIN = {
    "tag_overlap_score": 0.0,
    "common_tag_count": 0,
    "overlap_provide_to_need": 0.0,
    "overlap_need_to_provide": 0.0,
    "vector_semantic": 0.0,
    "tag_count_a": 0,
    "tag_count_b": 0,
    "avg_weight_a": 0.0,
    "avg_weight_b": 0.0,
    "tag_weight_score": 0.0,
    "intro_semantic": 0.0,
    "provide_need_balance": 0.0,
    "tag_category_overlap": 0.0,
}


# ── 工具函数 ──────────────────────────────────────────────────────────

def load_data(path: str) -> dict:
    """加载V2训练数据JSON"""
    path = Path(path)
    if not path.exists():
        print(f"[错误] 训练数据文件不存在: {path}")
        sys.exit(1)
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    return data


def save_data(data: dict, path: str):
    """保存增强后的训练数据"""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"[完成] 增强数据已保存到: {path}")


def clip_features(features: dict) -> dict:
    """裁剪特征值到合理范围"""
    clipped = {}
    for name, val in features.items():
        max_val = FEATURE_MAX.get(name, float("inf"))
        min_val = FEATURE_MIN.get(name, float("-inf"))
        if name in DISCRETE_FEATURES:
            clipped[name] = int(max(min_val, min(max_val, round(val))))
        else:
            clipped[name] = round(max(min_val, min(max_val, float(val))), 4)
    return clipped


def compute_feature_stats(samples: list) -> dict:
    """计算每个特征的均值和标准差（按标签分组）"""
    label_vals = {0: {f: [] for f in ALL_FEATURES},
                  1: {f: [] for f in ALL_FEATURES}}
    for s in samples:
        lbl = s["label"]
        for fname in ALL_FEATURES:
            label_vals[lbl][fname].append(s["features"].get(fname, 0.0))

    stats = {}
    for lbl in (0, 1):
        stats[lbl] = {}
        for fname in ALL_FEATURES:
            vals = label_vals[lbl][fname]
            if vals:
                stats[lbl][fname] = {
                    "mean": float(np.mean(vals)),
                    "std": float(np.std(vals)) if len(vals) > 1 else 0.01,
                    "min": float(min(vals)),
                    "max": float(max(vals)),
                }
            else:
                stats[lbl][fname] = {"mean": 0.0, "std": 0.01, "min": 0.0, "max": 0.0}
    return stats


# ── 增强策略 ──────────────────────────────────────────────────────────

def augment_gaussian_noise(
    samples: list, target_count: int, noise_std: float = 0.015
) -> list:
    """
    策略1: 高斯噪声注入
    对原始样本的特征值添加小幅高斯噪声 (noise_std=0.015 ≈ 特征范围1~3%)
    保持标签不变。适用于连续值特征。
    离散特征(common_tag_count/tag_count)随机±1偏移。
    """
    augmented = []
    if not samples:
        return augmented

    needed = target_count
    while len(augmented) < needed:
        for sample in samples:
            if len(augmented) >= needed:
                break
            new_sample = deepcopy(sample)
            new_feat = {}
            for fname, val in sample["features"].items():
                if fname in CONTINUOUS_FEATURES:
                    noise = np.random.normal(0, noise_std)
                    new_feat[fname] = float(val) + noise
                elif fname in DISCRETE_FEATURES:
                    # 离散特征：±1 或 0
                    shift = np.random.choice([-1, 0, 1])
                    new_feat[fname] = int(val) + shift
                else:
                    new_feat[fname] = val
            new_sample["features"] = clip_features(new_feat)
            # 记录来源
            new_sample["_aug_type"] = "gaussian_noise"
            augmented.append(new_sample)

    return augmented[:needed]


def augment_smote_interpolation(
    class_samples: list, target_count: int, k_neighbors: int = 3
) -> list:
    """
    策略2: SMOTE风格插值
    在同类样本之间进行线性插值，生成合成样本。
    对每个样本，随机选择k个同类邻居，按随机比例λ混合。
    """
    augmented = []
    n = len(class_samples)
    if n < 2:
        # 不足2个样本无法插值，改用噪声增强
        return augment_gaussian_noise(class_samples, target_count, noise_std=0.02)

    needed = target_count
    while len(augmented) < needed:
        # 随机选两个不同的同类样本
        i = random.randint(0, n - 1)
        j = random.randint(0, n - 1)
        while j == i and n > 1:
            j = random.randint(0, n - 1)

        s1 = class_samples[i]
        s2 = class_samples[j]

        # λ ~ Beta(2,2) — 倾向于不极端 (≈0.5)
        lam = np.random.beta(2, 2) if random.random() < 0.7 else random.random()
        # 确保有足够的变化
        lam = max(0.1, min(0.9, lam))

        new_sample = deepcopy(s1)
        new_feat = {}
        for fname in ALL_FEATURES:
            v1 = s1["features"].get(fname, 0.0)
            v2 = s2["features"].get(fname, 0.0)
            interpolated = v1 * (1 - lam) + v2 * lam
            new_feat[fname] = interpolated

        new_sample["features"] = clip_features(new_feat)
        # 如果两个原样本有common_tags, 取并集子集
        # 注意: common_tags可能是字符串列表或dict列表，需安全处理
        def safe_flatten(tags_list):
            """将common_tags展平为字符串列表（跳过不可哈希的dict等类型）"""
            flat = []
            for item in (tags_list or []):
                if isinstance(item, str):
                    flat.append(item)
                elif isinstance(item, (int, float)):
                    flat.append(str(item))
                # 跳过dict等非字符串类型
            return flat

        s1_tags = safe_flatten(s1.get("common_tags"))
        s2_tags = safe_flatten(s2.get("common_tags"))
        if s1_tags or s2_tags:
            combined = list(set(s1_tags) | set(s2_tags))
            k = random.randint(0, min(len(combined), 3))
            new_sample["common_tags"] = random.sample(combined, k) if k > 0 else []
        else:
            new_sample["common_tags"] = []

        # 平均score
        new_sample["score"] = round(
            (s1.get("score", 0.0) + s2.get("score", 0.0)) / 2.0, 4
        )
        new_sample["_aug_type"] = "smote_interpolation"
        augmented.append(new_sample)

    return augmented[:needed]


def augment_bootstrap(
    samples: list, target_count: int
) -> list:
    """
    策略3: Bootstrap有放回采样
    带微弱噪声的有放回采样，简单直接。
    """
    augmented = []
    needed = target_count
    n = len(samples)
    if n == 0:
        return augmented

    while len(augmented) < needed:
        idx = random.randint(0, n - 1)
        sample = samples[idx]
        new_sample = deepcopy(sample)

        # 添加微量噪声避免完全重复
        new_feat = {}
        for fname, val in sample["features"].items():
            if fname in CONTINUOUS_FEATURES:
                noise = np.random.normal(0, 0.005)  # 极小的噪声 (0.5%)
                new_feat[fname] = float(val) + noise
            else:
                new_feat[fname] = val
        new_sample["features"] = clip_features(new_feat)
        new_sample["_aug_type"] = "bootstrap"
        augmented.append(new_sample)

    return augmented[:needed]


def augment_near_boundary_mixing(
    pos_samples: list, neg_samples: list, target_count: int
) -> list:
    """
    策略5: 近边界混合（困难样本生成）
    正负样本对按比例混合生成"边界样本"。
    λ取0.3~0.7之间使得样本靠近决策边界。
    标签: 如果λ > 0.5 用正样本标签, 否则用负样本标签。
    这相当于在特征空间中的决策边界附近生成困难样本。
    """
    augmented = []
    if not pos_samples or not neg_samples:
        return augmented

    needed = target_count
    n_pos = len(pos_samples)
    n_neg = len(neg_samples)

    while len(augmented) < needed:
        i = random.randint(0, n_pos - 1)
        j = random.randint(0, n_neg - 1)

        s_pos = pos_samples[i]
        s_neg = neg_samples[j]

        # λ靠近0.5附近 → 边界样本
        lam = np.random.beta(5, 5)  # 集中在0.5附近
        lam = max(0.2, min(0.8, lam))

        new_sample = deepcopy(s_pos)
        new_feat = {}
        for fname in ALL_FEATURES:
            v_pos = s_pos["features"].get(fname, 0.0)
            v_neg = s_neg["features"].get(fname, 0.0)
            mixed = v_pos * lam + v_neg * (1 - lam)
            new_feat[fname] = mixed

        new_sample["features"] = clip_features(new_feat)

        # 标签: 按λ加权确定
        # 如果λ > 0.6 倾向正, λ < 0.4 倾向负, 中间模糊
        if lam > 0.6:
            new_sample["label"] = 1
            new_sample["score"] = round(lam * s_pos.get("score", 0.5), 4)
        elif lam < 0.4:
            new_sample["label"] = 0
            new_sample["score"] = 0.0
        else:
            # 边界模糊区：随机分配，但偏好原有的少数类(负)
            new_sample["label"] = 0 if random.random() < 0.6 else 1
            new_sample["score"] = round(
                new_sample["label"] * lam * s_pos.get("score", 0.5), 4
            )

        new_sample["common_tags"] = []
        # 如果混合后更接近正，可能保留一些tags
        # 安全处理common_tags中的不可哈希类型
        def safe_flatten(tags_list):
            flat = []
            for item in (tags_list or []):
                if isinstance(item, str):
                    flat.append(item)
            return flat

        if new_sample["label"] == 1:
            s_pos_tags = safe_flatten(s_pos.get("common_tags"))
            if s_pos_tags:
                k = random.randint(0, min(len(s_pos_tags), 2))
                new_sample["common_tags"] = (
                    random.sample(s_pos_tags, k) if k > 0 else []
                )
        new_sample["_aug_type"] = "boundary_mixing"
        augmented.append(new_sample)

    return augmented[:needed]


def augment_feature_perturbation(
    class_samples: list, target_count: int
) -> list:
    """
    策略6: 特征扰动增强
    对单个特征进行大尺度扰动（模拟不同配对场景），
    同时保持其他特征不变，标签不变。
    """
    augmented = []
    n = len(class_samples)
    if n == 0:
        return augmented

    needed = target_count
    while len(augmented) < needed:
        idx = random.randint(0, n - 1)
        sample = class_samples[idx]
        new_sample = deepcopy(sample)

        # 随机选择1~3个特征进行扰动
        n_features_to_perturb = random.randint(1, 3)
        perturb_features = random.sample(ALL_FEATURES, n_features_to_perturb)

        new_feat = {}
        for fname, val in sample["features"].items():
            if fname in perturb_features:
                if fname in CONTINUOUS_FEATURES:
                    # 大幅度扰动
                    delta = np.random.uniform(-0.15, 0.15)
                    new_feat[fname] = float(val) + delta
                elif fname in DISCRETE_FEATURES:
                    shift = np.random.choice([-2, -1, 0, 1, 2])
                    new_feat[fname] = int(val) + shift
                else:
                    new_feat[fname] = val
            else:
                new_feat[fname] = val

        new_sample["features"] = clip_features(new_feat)
        new_sample["_aug_type"] = "feature_perturbation"
        augmented.append(new_sample)

    return augmented[:needed]


def augment_negative_oversample(
    neg_samples: list, target_count: int
) -> list:
    """
    策略7: 负样本专项增强
    负样本当前仅45条(30%)，而正样本105条(70%)。
    对负样本使用多种方式增强以改善类别平衡。
    """
    augmented = []
    n = len(neg_samples)
    if n == 0:
        return augmented

    needed = target_count
    while len(augmented) < needed:
        idx = random.randint(0, n - 1)
        sample = neg_samples[idx]

        # 随机选择增强方式
        mode = random.choice(["noise", "smote", "perturb"])

        if mode == "noise":
            new_sample = deepcopy(sample)
            new_feat = {}
            for fname, val in sample["features"].items():
                if fname in CONTINUOUS_FEATURES:
                    noise = np.random.normal(0, 0.025)
                    new_feat[fname] = float(val) + noise
                elif fname in DISCRETE_FEATURES:
                    shift = np.random.choice([-1, 0, 1])
                    new_feat[fname] = int(val) + shift
                else:
                    new_feat[fname] = val
            new_sample["features"] = clip_features(new_feat)

        elif mode == "smote" and n >= 2:
            j = random.randint(0, n - 1)
            while j == idx and n > 1:
                j = random.randint(0, n - 1)
            s2 = neg_samples[j]
            lam = random.random()
            new_sample = deepcopy(sample)
            new_feat = {}
            for fname in ALL_FEATURES:
                v1 = sample["features"].get(fname, 0.0)
                v2 = s2["features"].get(fname, 0.0)
                new_feat[fname] = v1 * (1 - lam) + v2 * lam
            new_sample["features"] = clip_features(new_feat)

        else:  # perturb
            new_sample = deepcopy(sample)
            new_feat = {}
            for fname in ALL_FEATURES:
                new_feat[fname] = sample["features"].get(fname, 0.0)
            # 随机set 1-2个特征到最小值（模拟"完全不匹配"场景）
            zero_features = random.sample(ALL_FEATURES, random.randint(0, 3))
            for zf in zero_features:
                new_feat[zf] = FEATURE_MIN[zf]
            new_sample["features"] = clip_features(new_feat)

        new_sample["label"] = 0
        new_sample["score"] = 0.0
        new_sample["common_tags"] = []
        new_sample["_aug_type"] = f"neg_oversample_{mode}"
        augmented.append(new_sample)

    return augmented[:needed]


# ── 主流程 ────────────────────────────────────────────────────────────

def compute_augmented_stats(
    original: list, augmented: list, feature_names: list
) -> dict:
    """计算增强前后统计对比"""
    orig_labels = [s["label"] for s in original]
    aug_labels = [s["label"] for s in augmented]

    stats = {
        "original": {
            "total": len(original),
            "positive": sum(orig_labels),
            "negative": len(orig_labels) - sum(orig_labels),
            "pos_ratio": sum(orig_labels) / len(original) if original else 0,
        },
        "augmented": {
            "total": len(augmented),
            "positive": sum(aug_labels),
            "negative": len(aug_labels) - sum(aug_labels),
            "pos_ratio": sum(aug_labels) / len(augmented) if augmented else 0,
        },
        "feature_comparison": {},
        "augmentation_types": Counter(
            s.get("_aug_type", "unknown") for s in augmented
        ),
    }

    # 特征分布对比
    for fname in feature_names:
        orig_vals = [s["features"].get(fname, 0.0) for s in original]
        aug_vals = [s["features"].get(fname, 0.0) for s in augmented]
        if orig_vals:
            stats["feature_comparison"][fname] = {
                "orig_mean": round(float(np.mean(orig_vals)), 4),
                "orig_std": round(float(np.std(orig_vals)), 4),
                "aug_mean": round(float(np.mean(aug_vals)), 4),
                "aug_std": round(float(np.std(aug_vals)), 4),
            }

    return stats


def print_stats(stats: dict):
    """打印增强统计报告"""
    o = stats["original"]
    a = stats["augmented"]

    print("\n" + "=" * 65)
    print("  AI数智名片 — 数据增强统计报告")
    print("=" * 65)
    print(f"\n  [样本量]")
    print(f"    原始:      {o['total']:5d} (正={o['positive']}, 负={o['negative']}, "
          f"正比例={o['pos_ratio']:.1%})")
    print(f"    增强后:    {a['total']:5d} (正={a['positive']}, 负={a['negative']}, "
          f"正比例={a['pos_ratio']:.1%})")
    print(f"    增长倍数:  {a['total'] / max(1, o['total']):.1f}x")

    aug_types = stats["augmentation_types"]
    print(f"\n  [增强策略分布]")
    for aug_type, count in sorted(aug_types.items(), key=lambda x: -x[1]):
        print(f"    {aug_type:30s}: {count:5d} ({count/a['total']*100:.1f}%)")

    print(f"\n  [特征分布对比 (均值 ± 标准差)]")
    print(f"    {'特征名':30s} {'原始均值':>10s} {'原始标准差':>10s} "
          f"{'增强均值':>10s} {'增强标准差':>10s}")
    print(f"    {'-'*30} {'-'*10} {'-'*10} {'-'*10} {'-'*10}")
    for fname in ALL_FEATURES:
        fc = stats["feature_comparison"].get(fname, {})
        if fc:
            print(f"    {fname:30s} {fc['orig_mean']:>10.4f} {fc['orig_std']:>10.4f} "
                  f"{fc['aug_mean']:>10.4f} {fc['aug_std']:>10.4f}")

    pos_diff = a["positive"] - o["positive"]
    neg_diff = a["negative"] - o["negative"]
    print(f"\n  [类别平衡变化]")
    print(f"    正样本增加: {pos_diff:+5d}")
    print(f"    负样本增加: {neg_diff:+5d}")
    print(f"    原始正负比: 1:{o['negative']/max(1,o['positive']):.2f}")
    print(f"    增强正负比: 1:{a['negative']/max(1,a['positive']):.2f}")
    print(f"\n  {'=' * 65}\n")


def main():
    parser = argparse.ArgumentParser(
        description="AI数智名片 V2 训练数据增强 - 解决过拟合"
    )
    parser.add_argument(
        "--input",
        type=str,
        default=os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            "data", "v2_training_data.json",
        ),
        help="输入训练数据JSON路径 (默认: ../data/v2_training_data.json)",
    )
    parser.add_argument(
        "--output",
        type=str,
        default=None,
        help="输出增强数据JSON路径 (默认: 输入路径同目录/_augmented.json)",
    )
    parser.add_argument(
        "--target",
        type=int,
        default=1200,
        help="目标样本总数 (默认: 1200)",
    )
    parser.add_argument(
        "--noise_std",
        type=float,
        default=0.015,
        help="高斯噪声标准差 (默认: 0.015)",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=SEED,
        help="随机种子 (默认: 42)",
    )

    args = parser.parse_args()

    # 设置种子
    random.seed(args.seed)
    np.random.seed(args.seed)

    # 1. 加载原始数据
    print("[1/5] 加载原始训练数据...")
    data = load_data(args.input)
    original_samples = data["samples"]
    meta = data["meta"]

    print(f"  原始样本数: {meta['total_samples']}")
    print(f"  正样本: {meta['positive_count']}")
    print(f"  负样本: {meta['negative_count']}")
    print(f"  用户数: {meta['n_users']}")

    # 2. 分离正负样本
    pos_samples = [s for s in original_samples if s["label"] == 1]
    neg_samples = [s for s in original_samples if s["label"] == 0]

    print(f"\n[2/5] 分离正负样本...")
    print(f"  正样本: {len(pos_samples)}")
    print(f"  负样本: {len(neg_samples)}")

    # 3. 计算特征统计（用于控制噪声幅度）
    print(f"\n[3/5] 计算特征统计分布...")
    stats = compute_feature_stats(original_samples)
    for lbl in (0, 1):
        lbl_name = "负样本" if lbl == 0 else "正样本"
        print(f"  {lbl_name}特征均值范围: ", end="")
        means = [stats[lbl][f]["mean"] for f in ALL_FEATURES]
        print(f"[{min(means):.4f}, {max(means):.4f}]")

    # 4. 执行数据增强
    print(f"\n[4/5] 执行数据增强 (目标: {args.target} 条)...")

    target_pos = int(args.target * 0.55)  # 55% 正样本 (略低于原始70%)
    target_neg = args.target - target_pos  # 45% 负样本

    # 正样本增强
    aug_pos_smote = augment_smote_interpolation(
        pos_samples, int(target_pos * 0.30)
    )
    aug_pos_noise = augment_gaussian_noise(
        pos_samples, int(target_pos * 0.25), args.noise_std
    )
    aug_pos_bootstrap = augment_bootstrap(
        pos_samples, int(target_pos * 0.20)
    )
    aug_pos_perturb = augment_feature_perturbation(
        pos_samples, int(target_pos * 0.15)
    )
    aug_pos_boundary = augment_near_boundary_mixing(
        pos_samples, neg_samples, int(target_pos * 0.10)
    )

    # 负样本增强（需要更多增强以平衡类别）
    aug_neg_smote = augment_smote_interpolation(
        neg_samples, int(target_neg * 0.25)
    )
    aug_neg_noise = augment_gaussian_noise(
        neg_samples, int(target_neg * 0.20), args.noise_std
    )
    aug_neg_oversample = augment_negative_oversample(
        neg_samples, int(target_neg * 0.30)
    )
    aug_neg_boundary = augment_near_boundary_mixing(
        pos_samples, neg_samples, int(target_neg * 0.15)
    )
    aug_neg_bootstrap = augment_bootstrap(
        neg_samples, int(target_neg * 0.10)
    )

    # 合并所有增强样本
    all_augmented = (
        aug_pos_smote + aug_pos_noise + aug_pos_bootstrap +
        aug_pos_perturb + aug_pos_boundary +
        aug_neg_smote + aug_neg_noise + aug_neg_oversample +
        aug_neg_boundary + aug_neg_bootstrap
    )

    # 如果还不够目标数，用bootstrap补足
    if len(all_augmented) < args.target - len(original_samples):
        shortfall = args.target - len(original_samples) - len(all_augmented)
        print(f"  补足 {shortfall} 条...")
        filler = augment_bootstrap(original_samples, shortfall)
        all_augmented.extend(filler)

    # 打乱增强样本
    random.shuffle(all_augmented)

    # 合并原始 + 增强
    final_samples = original_samples + all_augmented
    random.shuffle(final_samples)

    # 如果超出目标，截断
    if len(final_samples) > args.target:
        final_samples = final_samples[:args.target]
    # 或者仍不足，再补一批
    elif len(final_samples) < args.target:
        extra = augment_bootstrap(
            original_samples, args.target - len(final_samples)
        )
        final_samples.extend(extra)

    print(f"\n  增强结果:")
    print(f"    原始样本:     {len(original_samples):5d}")
    print(f"    增强样本:     {len(all_augmented):5d}")
    print(f"    最终总样本:   {len(final_samples):5d}")

    # 统计最终标签
    final_labels = [s["label"] for s in final_samples]
    final_pos = sum(final_labels)
    final_neg = len(final_labels) - final_pos
    print(f"    最终正样本:   {final_pos:5d} ({final_pos/len(final_samples)*100:.1f}%)")
    print(f"    最终负样本:   {final_neg:5d} ({final_neg/len(final_samples)*100:.1f}%)")

    # 5. 构建输出并保存
    print(f"\n[5/5] 保存增强数据...")

    new_meta = {
        "total_samples": len(final_samples),
        "positive_count": final_pos,
        "negative_count": final_neg,
        "feature_names": ALL_FEATURES,
        "n_users": meta["n_users"],
        "user_ids": meta["user_ids"],
        "version": "v2_augmented",
        "v2_new_features": meta.get("v2_new_features", []),
        "augmentation_info": {
            "original_count": len(original_samples),
            "augmented_count": len(final_samples) - len(original_samples),
            "target_count": args.target,
            "noise_std": args.noise_std,
            "seed": args.seed,
            "strategies": [
                "gaussian_noise",
                "smote_interpolation",
                "bootstrap_resampling",
                "feature_perturbation",
                "near_boundary_mixing",
                "negative_oversampling",
            ],
        },
    }

    # 移除_aug_type辅助字段
    output_samples = []
    for s in final_samples:
        clean = {k: v for k, v in s.items() if not k.startswith("_")}
        output_samples.append(clean)

    output_data = {
        "meta": new_meta,
        "samples": output_samples,
    }

    # 确定输出路径
    if args.output:
        output_path = args.output
    else:
        input_path = Path(args.input)
        output_path = str(
            input_path.parent / f"v2_training_data_augmented.json"
        )

    save_data(output_data, output_path)

    # 计算并打印统计
    print(f"\n[增强统计]")
    aug_stats = compute_augmented_stats(
        original_samples, final_samples, ALL_FEATURES
    )
    print_stats(aug_stats)

    # 同时保存统计报告到txt
    stats_path = Path(output_path).parent / "v2_training_data_augmented_stats.txt"
    with open(stats_path, "w", encoding="utf-8") as f:
        # 重定向print到文件
        import io
        old_stdout = sys.stdout
        sys.stdout = io.StringIO()
        print_stats(aug_stats)
        stats_text = sys.stdout.getvalue()
        sys.stdout = old_stdout
        f.write(stats_text)

    print(f"[完成] 统计报告已保存到: {stats_path}")

    # 返回最后信息
    print(f"\n✅ 数据增强完成!")
    print(f"   原数据: {len(original_samples)} 条 → 增强后: {len(final_samples)} 条")
    print(f"   正:负 = {final_pos}:{final_neg} (1:{final_neg/max(1,final_pos):.2f})")
    print(f"\n💡 提示: 运行训练时使用增强数据:")
    print(f"   python scripts/train_matching_model_v2.py --data data/v2_training_data_augmented.json")
    print(f"   或手动将 v2_training_data_augmented.json 复制为 v2_training_data.json")


if __name__ == "__main__":
    main()
