#!/usr/bin/env python
"""
train_matching_model_v2_mac_mps.py — AI数智名片 V2 三塔模型训练（Mac Mini MPS GPU版）

从 train_matching_model_v2.py 复制，关键改动：
  1. 添加 Apple Silicon MPS 支持（优先使用 MPS > CUDA > CPU）
  2. 支持命令行参数指定数据路径和模型输出路径
  3. 计时功能以计算 GPU vs CPU 加速比
  4. 无交互式依赖，适合远程执行
"""

import argparse
import json
import sys
import time
import warnings
from pathlib import Path

import numpy as np
import torch
import torch.nn as nn
import torch.optim as optim
from sklearn.model_selection import train_test_split
from sklearn.metrics import (
    accuracy_score, precision_score, recall_score, f1_score,
    roc_auc_score, confusion_matrix,
)
from sklearn.preprocessing import StandardScaler

warnings.filterwarnings("ignore")

# ── 配置 ─────────────────────────────────────────────────────────────
SEED = 42
TEST_SIZE = 0.30
EPOCHS = 300
LR = 0.0005
BATCH_SIZE = 8
WEIGHT_DECAY = 1e-2
DROPOUT = 0.5
EARLY_STOP_PATIENCE = 3
MIN_EPOCHS = 10

torch.manual_seed(SEED)
np.random.seed(SEED)

# V2特征组定义（三塔 + V2新增）
OVERLAP_FEATURES = ["tag_overlap_score", "common_tag_count",
                    "overlap_provide_to_need", "overlap_need_to_provide"]
SEMANTIC_FEATURES = ["vector_semantic"]
WEIGHT_FEATURES = ["tag_count_a", "tag_count_b", "avg_weight_a",
                   "avg_weight_b", "tag_weight_score"]
V2_NEW_FEATURES = ["intro_semantic", "provide_need_balance", "tag_category_overlap"]
ALL_FEATURES = OVERLAP_FEATURES + SEMANTIC_FEATURES + WEIGHT_FEATURES + V2_NEW_FEATURES

# Tower划分（V2新增特征归入合适的tower）
SEMANTIC_FEATURES_V2 = SEMANTIC_FEATURES + ["intro_semantic"]
OVERLAP_FEATURES_V2 = OVERLAP_FEATURES + ["provide_need_balance"]
WEIGHT_FEATURES_V2 = WEIGHT_FEATURES + ["tag_category_overlap"]


def get_device(force_cpu: bool = False):
    """智能选择设备：MPS > CUDA > CPU"""
    if force_cpu:
        return torch.device("cpu")

    if torch.backends.mps.is_available() and torch.backends.mps.is_built():
        return torch.device("mps")
    elif torch.cuda.is_available():
        return torch.device("cuda")
    else:
        return torch.device("cpu")


# ── V2 三塔模型（防过拟合版） ──────────────────────────────────────────

class ThreeTowerModelV2(nn.Module):
    """V2三塔匹配模型（防过拟合）

    Tower 1: 标签重叠特征 + provide_need_balance (5个)
    Tower 2: 语义相似度特征 + intro_semantic (2个)
    Tower 3: 标签权重特征 + tag_category_overlap (6个)
    """

    def __init__(self, dropout: float = DROPOUT):
        super().__init__()

        # Tower 1 — 标签重叠（V2: +provide_need_balance）
        self.tower_overlap = nn.Sequential(
            nn.Linear(len(OVERLAP_FEATURES_V2), 10),
            nn.BatchNorm1d(10),
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.Linear(10, 6),
            nn.BatchNorm1d(6),
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.Linear(6, 4),
            nn.ReLU(),
        )

        # Tower 2 — 语义相似度（V2: +intro_semantic）
        self.tower_semantic = nn.Sequential(
            nn.Linear(len(SEMANTIC_FEATURES_V2), 6),
            nn.BatchNorm1d(6),
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.Linear(6, 3),
            nn.ReLU(),
        )

        # Tower 3 — 标签权重（V2: +tag_category_overlap）
        self.tower_weight = nn.Sequential(
            nn.Linear(len(WEIGHT_FEATURES_V2), 10),
            nn.BatchNorm1d(10),
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.Linear(10, 6),
            nn.BatchNorm1d(6),
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.Linear(6, 4),
            nn.ReLU(),
        )

        # 合并层
        combined_dim = 4 + 3 + 4  # 11
        self.combined = nn.Sequential(
            nn.Linear(combined_dim, 12),
            nn.BatchNorm1d(12),
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.Linear(12, 8),
            nn.BatchNorm1d(8),
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.Linear(8, 4),
            nn.BatchNorm1d(4),
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.Linear(4, 1),
            nn.Sigmoid(),
        )

    def forward(self, x_overlap, x_semantic, x_weight):
        out1 = self.tower_overlap(x_overlap)
        out2 = self.tower_semantic(x_semantic)
        out3 = self.tower_weight(x_weight)
        combined = torch.cat([out1, out2, out3], dim=1)
        return self.combined(combined).squeeze(1)


# ── 数据加载 ──────────────────────────────────────────────────────────

def load_v2_training_data(data_path: Path) -> tuple:
    """加载V2训练数据（13特征）"""
    if not data_path.exists():
        print(f"[错误] V2训练数据文件不存在: {data_path}")
        sys.exit(1)

    with open(data_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    meta = data.get("meta", {})
    samples = data.get("samples", [])

    print(f"\n[信息] 加载V2训练数据: {data_path}")
    print(f"  总样本数: {meta.get('total_samples', len(samples))}")
    print(f"  特征数:   {len(meta.get('feature_names', []))}")
    print(f"  用户数:   {meta.get('n_users', 0)}")
    print(f"  版本:     {meta.get('version', 'v1')}")
    if meta.get("v2_new_features"):
        print(f"  V2新增:   {meta['v2_new_features']}")

    features = {name: [] for name in ALL_FEATURES}
    labels = []

    for sample in samples:
        feat = sample["features"]
        for name in ALL_FEATURES:
            features[name].append(feat.get(name, 0.0))
        labels.append(sample["label"])

    # 构建V2三塔特征矩阵
    X_overlap = np.column_stack([features[name] for name in OVERLAP_FEATURES_V2])
    X_semantic = np.column_stack([features[name] for name in SEMANTIC_FEATURES_V2])
    X_weight = np.column_stack([features[name] for name in WEIGHT_FEATURES_V2])
    y = np.array(labels, dtype=np.float32)

    return X_overlap, X_semantic, X_weight, y, samples, meta


# ── 训练函数（防过拟合版） ──────────────────────────────────────────

def train_three_tower_v2(
    X_overlap, X_semantic, X_weight, y,
    X_val_o, X_val_s, X_val_w, y_val,
    device,
) -> tuple[nn.Module, dict, dict]:
    """训练V2三塔模型（防过拟合）"""
    # 标准化
    scaler_o = StandardScaler()
    scaler_s = StandardScaler()
    scaler_w = StandardScaler()

    X_overlap_norm = scaler_o.fit_transform(X_overlap)
    X_semantic_norm = scaler_s.fit_transform(X_semantic)
    X_weight_norm = scaler_w.fit_transform(X_weight)

    X_val_o_norm = scaler_o.transform(X_val_o)
    X_val_s_norm = scaler_s.transform(X_val_s)
    X_val_w_norm = scaler_w.transform(X_val_w)

    # 转换为 Tensor
    print(f"[信息] 使用设备: {device}")
    if device.type == "mps":
        print(f"[信息] Apple Silicon GPU (MPS) 加速已启用!")

    t_overlap = torch.FloatTensor(X_overlap_norm).to(device)
    t_semantic = torch.FloatTensor(X_semantic_norm).to(device)
    t_weight = torch.FloatTensor(X_weight_norm).to(device)
    t_labels = torch.FloatTensor(y).to(device)

    t_val_o = torch.FloatTensor(X_val_o_norm).to(device)
    t_val_s = torch.FloatTensor(X_val_s_norm).to(device)
    t_val_w = torch.FloatTensor(X_val_w_norm).to(device)
    t_val_labels = torch.FloatTensor(y_val).to(device)

    # 处理类别不平衡：计算权重
    pos_weight = (len(y) - y.sum()) / y.sum() if y.sum() > 0 else 1.0
    print(f"[信息] 正样本权重: {pos_weight:.2f}")

    # 初始化模型
    model = ThreeTowerModelV2(dropout=DROPOUT).to(device)

    criterion = nn.BCELoss()
    optimizer = optim.AdamW(
        model.parameters(), lr=LR, weight_decay=WEIGHT_DECAY
    )
    scheduler = optim.lr_scheduler.ReduceLROnPlateau(
        optimizer, mode="min", factor=0.5, patience=2,
        min_lr=1e-6,
    )

    # 训练
    n_samples = len(y)
    best_val_loss = float("inf")
    best_val_auc = 0.0
    best_model_state = None
    early_stop_counter = 0
    history = {"train_loss": [], "val_loss": [], "val_acc": [], "val_auc": [], "lr": []}

    print(f"\n{'=' * 60}")
    print(f"V2三塔模型训练（防过拟合版）")
    print(f"  Dropout: {DROPOUT}, WeightDecay: {WEIGHT_DECAY}, LR: {LR}")
    print(f"  ValRatio: {TEST_SIZE}, EarlyStopPatience: {EARLY_STOP_PATIENCE}")
    print(f"  Tower1: {len(OVERLAP_FEATURES_V2)}f, Tower2: {len(SEMANTIC_FEATURES_V2)}f, Tower3: {len(WEIGHT_FEATURES_V2)}f")
    print(f"  Device: {device}")
    print(f"{'=' * 60}")

    for epoch in range(EPOCHS):
        model.train()

        permutation = torch.randperm(n_samples)
        epoch_loss = 0.0
        n_batches = 0

        for i in range(0, n_samples, BATCH_SIZE):
            indices = permutation[i:i + BATCH_SIZE]

            batch_o = t_overlap[indices]
            batch_s = t_semantic[indices]
            batch_w = t_weight[indices]
            batch_y = t_labels[indices]

            optimizer.zero_grad()
            outputs = model(batch_o, batch_s, batch_w)
            loss = criterion(outputs, batch_y)
            loss.backward()

            torch.nn.utils.clip_grad_norm_(model.parameters(), max_norm=1.0)

            optimizer.step()

            epoch_loss += loss.item()
            n_batches += 1

        avg_train_loss = epoch_loss / max(1, n_batches)

        # 验证
        model.eval()
        with torch.no_grad():
            val_outputs = model(t_val_o, t_val_s, t_val_w)
            val_loss = criterion(val_outputs, t_val_labels).item()
            val_preds = (val_outputs > 0.5).float().cpu().numpy()
            val_acc = accuracy_score(y_val, val_preds)
            try:
                val_auc = roc_auc_score(y_val, val_outputs.cpu().numpy())
            except Exception:
                val_auc = 0.0

        scheduler.step(val_loss)
        current_lr = optimizer.param_groups[0]["lr"]

        history["train_loss"].append(avg_train_loss)
        history["val_loss"].append(val_loss)
        history["val_acc"].append(val_acc)
        history["val_auc"].append(val_auc)
        history["lr"].append(current_lr)

        print(f"  Epoch {epoch+1:3d}/{EPOCHS} | "
              f"Train Loss: {avg_train_loss:.4f} | "
              f"Val Loss: {val_loss:.4f} | "
              f"Val Acc: {val_acc:.4f} | "
              f"Val AUC: {val_auc:.4f} | "
              f"LR: {current_lr:.6f}")

        if val_auc > best_val_auc and epoch >= MIN_EPOCHS:
            best_val_auc = val_auc
            best_val_loss = val_loss
            best_model_state = {
                k: v.cpu().clone() for k, v in model.state_dict().items()
            }
            early_stop_counter = 0
        else:
            if epoch >= MIN_EPOCHS:
                early_stop_counter += 1
                if early_stop_counter >= EARLY_STOP_PATIENCE:
                    print(f"\n[早停] 验证集AUC连续{EARLY_STOP_PATIENCE}轮未提升，停止训练")
                    break

    if best_model_state is None:
        best_model_state = {
            k: v.cpu().clone() for k, v in model.state_dict().items()
        }

    model.load_state_dict(best_model_state)
    model = model.to(device)

    scalers = {"overlap": scaler_o, "semantic": scaler_s, "weight": scaler_w}

    return model, history, scalers


# ── 评估函数 ──────────────────────────────────────────────────────────

def evaluate_model(model, X_o, X_s, X_w, y, scalers, name="V2三塔模型"):
    """评估模型性能"""
    device = next(model.parameters()).device

    model.eval()
    X_o_norm = scalers["overlap"].transform(X_o)
    X_s_norm = scalers["semantic"].transform(X_s)
    X_w_norm = scalers["weight"].transform(X_w)

    with torch.no_grad():
        t_o = torch.FloatTensor(X_o_norm).to(device)
        t_s = torch.FloatTensor(X_s_norm).to(device)
        t_w = torch.FloatTensor(X_w_norm).to(device)
        outputs = model(t_o, t_s, t_w).cpu().numpy()

    y_pred_binary = (outputs > 0.5).astype(int).flatten()
    y_true = y.flatten()

    acc = accuracy_score(y_true, y_pred_binary)
    prec = precision_score(y_true, y_pred_binary, zero_division=0)
    rec = recall_score(y_true, y_pred_binary, zero_division=0)
    f1 = f1_score(y_true, y_pred_binary, zero_division=0)
    try:
        auc = roc_auc_score(y_true, outputs.flatten())
    except Exception:
        auc = 0.0

    print(f"\n{'=' * 60}")
    print(f"模型评估 — {name}")
    print(f"{'=' * 60}")
    print(f"  准确率 (Accuracy):  {acc:.4f}")
    print(f"  精确率 (Precision): {prec:.4f}")
    print(f"  召回率 (Recall):    {rec:.4f}")
    print(f"  F1 分数:           {f1:.4f}")
    print(f"  AUC:               {auc:.4f}")
    print(f"\n  混淆矩阵:")
    cm = confusion_matrix(y_true, y_pred_binary)
    print(f"    TN={cm[0][0]:4d}  FP={cm[0][1]:4d}")
    print(f"    FN={cm[1][0]:4d}  TP={cm[1][1]:4d}")

    metrics = {
        "accuracy": round(float(acc), 4),
        "precision": round(float(prec), 4),
        "recall": round(float(rec), 4),
        "f1": round(float(f1), 4),
        "auc": round(float(auc), 4),
    }
    return metrics, outputs.flatten()


# ── 特征重要性分析（V2版本） ──────────────────────────────────────────

def compute_feature_importance_v2(model, scalers, X_o_mean, X_s_mean, X_w_mean, device):
    """计算所有13个特征的重要性（逐个置零法）"""
    model.eval()

    baseline_o = torch.FloatTensor(scalers["overlap"].transform(X_o_mean.reshape(1, -1))).to(device)
    baseline_s = torch.FloatTensor(scalers["semantic"].transform(X_s_mean.reshape(1, -1))).to(device)
    baseline_w = torch.FloatTensor(scalers["weight"].transform(X_w_mean.reshape(1, -1))).to(device)

    with torch.no_grad():
        baseline_pred = model(baseline_o, baseline_s, baseline_w).item()

    importance = {}

    # Tower 1 features (V2)
    for i, name in enumerate(OVERLAP_FEATURES_V2):
        perturbed = X_o_mean.copy()
        perturbed[i] = 0.0
        p_o = torch.FloatTensor(scalers["overlap"].transform(perturbed.reshape(1, -1))).to(device)
        with torch.no_grad():
            pred = model(p_o, baseline_s, baseline_w).item()
        importance[name] = round(abs(baseline_pred - pred), 6)

    # Tower 2 features (V2)
    for i, name in enumerate(SEMANTIC_FEATURES_V2):
        perturbed = X_s_mean.copy()
        perturbed[i] = 0.0
        p_s = torch.FloatTensor(scalers["semantic"].transform(perturbed.reshape(1, -1))).to(device)
        with torch.no_grad():
            pred = model(baseline_o, p_s, baseline_w).item()
        importance[name] = round(abs(baseline_pred - pred), 6)

    # Tower 3 features (V2)
    for i, name in enumerate(WEIGHT_FEATURES_V2):
        perturbed = X_w_mean.copy()
        perturbed[i] = 0.0
        p_w = torch.FloatTensor(scalers["weight"].transform(perturbed.reshape(1, -1))).to(device)
        with torch.no_grad():
            pred = model(baseline_o, baseline_s, p_w).item()
        importance[name] = round(abs(baseline_pred - pred), 6)

    sorted_imp = sorted(importance.items(), key=lambda x: x[1], reverse=True)

    print(f"\n{'=' * 60}")
    print(f"特征重要性（V2，按Tower分组）")
    print(f"{'=' * 60}")
    print(f"  [Tower 1 — 标签重叠] (含V2: provide_need_balance)")
    for name in OVERLAP_FEATURES_V2:
        marker = " [V2新增]" if name in V2_NEW_FEATURES else ""
        print(f"    {name:30s}: {importance[name]:.6f}{marker}")
    print(f"  [Tower 2 — 语义相似度] (含V2: intro_semantic)")
    for name in SEMANTIC_FEATURES_V2:
        marker = " [V2新增]" if name in V2_NEW_FEATURES else ""
        print(f"    {name:30s}: {importance[name]:.6f}{marker}")
    print(f"  [Tower 3 — 标签权重] (含V2: tag_category_overlap)")
    for name in WEIGHT_FEATURES_V2:
        marker = " [V2新增]" if name in V2_NEW_FEATURES else ""
        print(f"    {name:30s}: {importance[name]:.6f}{marker}")

    print(f"\n  [全局排序 - 按重要性降序]")
    for i, (name, imp) in enumerate(sorted_imp, 1):
        marker = " [V2新增]" if name in V2_NEW_FEATURES else ""
        print(f"    {i:2d}. {name:30s}: {imp:.6f}{marker}")

    return importance


# ── 保存模型（V2版本） ──────────────────────────────────────────────

def save_model_v2(model, scalers, metrics, feature_importance, history, config, model_dir: Path):
    """保存V2模型 checkpoint 和训练元数据"""
    model_dir.mkdir(parents=True, exist_ok=True)

    model_path = model_dir / "matching_model_v2.pt"
    torch.save({
        "model_state_dict": model.state_dict(),
        "feature_names": ALL_FEATURES,
        "overlap_features": OVERLAP_FEATURES_V2,
        "semantic_features": SEMANTIC_FEATURES_V2,
        "weight_features": WEIGHT_FEATURES_V2,
        "v2_new_features": V2_NEW_FEATURES,
        "metrics": metrics,
        "config": config,
    }, model_path)
    print(f"\n[保存] V2 PyTorch 模型: {model_path}")

    # 标准化参数
    scaler_path = model_dir / "matching_scalers_v2.npy"
    scaler_data = {
        "overlap_mean": scalers["overlap"].mean_.tolist(),
        "overlap_scale": scalers["overlap"].scale_.tolist(),
        "semantic_mean": scalers["semantic"].mean_.tolist(),
        "semantic_scale": scalers["semantic"].scale_.tolist(),
        "weight_mean": scalers["weight"].mean_.tolist(),
        "weight_scale": scalers["weight"].scale_.tolist(),
    }
    np.save(str(scaler_path), scaler_data)
    print(f"[保存] V2 标准化参数: {scaler_path}")

    # 训练报告
    report = {
        "model": "ThreeTowerModelV2 (PyTorch, 防过拟合版)",
        "version": "v2",
        "config": config,
        "architecture": {
            "tower_overlap": f"Linear({len(OVERLAP_FEATURES_V2)}→10→6→4)",
            "tower_semantic": f"Linear({len(SEMANTIC_FEATURES_V2)}→6→3)",
            "tower_weight": f"Linear({len(WEIGHT_FEATURES_V2)}→10→6→4)",
            "combined": "Linear(4+3+4=11→12→8→4→1) + Sigmoid",
        },
        "feature_groups": {
            "tower1_overlap": OVERLAP_FEATURES_V2,
            "tower2_semantic": SEMANTIC_FEATURES_V2,
            "tower3_weight": WEIGHT_FEATURES_V2,
            "v2_new": V2_NEW_FEATURES,
        },
        "data_summary": {
            "total_samples": metrics.get("_total_samples", 0),
            "n_features": len(ALL_FEATURES),
            "version": "v2",
        },
        "metrics": {
            "train": {k: v for k, v in metrics.items() if k != "_total_samples"},
            "val": {k: v for k, v in metrics.items() if k != "_total_samples"},
        },
        "feature_importance": feature_importance,
        "training_history": {
            "final_train_loss": float(history["train_loss"][-1]),
            "final_val_loss": float(history["val_loss"][-1]),
            "best_val_loss": float(min(history["val_loss"])),
            "best_val_acc": float(max(history["val_acc"])),
            "best_val_auc": float(max(history["val_auc"])),
            "epochs_trained": len(history["train_loss"]),
            "final_lr": float(history["lr"][-1]),
        },
        "anti_overfitting_measures": [
            f"Dropout={DROPOUT}",
            f"WeightDecay={WEIGHT_DECAY}",
            f"EarlyStopPatience={EARLY_STOP_PATIENCE}",
            f"ValRatio={TEST_SIZE}",
            f"LR={LR}",
            "GradientClipping(max_norm=1.0)",
            "AdamW(stronger regularization than Adam)",
            "BatchNormalization in all layers",
            "ReducedLROnPlateau(patience=2)",
        ],
        "feature_names": ALL_FEATURES,
    }

    report_path = model_dir / "training_report_v2.json"
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    print(f"[保存] V2训练报告: {report_path}")

    return report


# ── 主流程 ────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="AI数智名片 V2 三塔模型训练（Mac MPS版）")
    parser.add_argument("--data", type=str, default=None,
                        help="V2训练数据JSON路径")
    parser.add_argument("--output", type=str, default=None,
                        help="模型输出目录")
    parser.add_argument("--force-cpu", action="store_true",
                        help="强制使用CPU（用于加速比对比）")
    args = parser.parse_args()

    print("=" * 60)
    print("AI数智名片 — V2三塔匹配模型训练（Mac MPS版）")
    print("=" * 60)

    # 设备选择
    device = get_device(force_cpu=args.force_cpu)
    print(f"[信息] 训练设备: {device}")
    if device.type == "mps":
        print("[信息] ✓ Apple Silicon GPU (MPS) 加速已启用")
    elif device.type == "cpu" and not args.force_cpu:
        print("[信息] ⚠ 未检测到GPU，使用CPU训练")
    elif args.force_cpu:
        print("[信息] 强制使用CPU模式（用于加速比对比）")

    config = {
        "dropout": DROPOUT,
        "weight_decay": WEIGHT_DECAY,
        "learning_rate": LR,
        "batch_size": BATCH_SIZE,
        "test_size": TEST_SIZE,
        "early_stop_patience": EARLY_STOP_PATIENCE,
        "min_epochs": MIN_EPOCHS,
        "max_epochs": EPOCHS,
        "seed": SEED,
        "version": "v2",
        "n_features": len(ALL_FEATURES),
        "v2_new_features": V2_NEW_FEATURES,
        "device": str(device),
    }

    # 路径
    script_dir = Path(__file__).resolve().parent
    data_path = Path(args.data) if args.data else (script_dir.parent / "data" / "v2_training_data.json")
    model_dir = Path(args.output) if args.output else (script_dir.parent / "models")

    print(f"[信息] 数据路径: {data_path}")
    print(f"[信息] 输出目录: {model_dir}")

    # 1. 加载V2数据
    X_overlap, X_semantic, X_weight, y, samples, meta = load_v2_training_data(data_path)

    n_pos = int(y.sum())
    n_neg = len(y) - n_pos
    print(f"\n  正样本: {n_pos} ({n_pos/len(y)*100:.1f}%)")
    print(f"  负样本: {n_neg} ({n_neg/len(y)*100:.1f}%)")

    # 2. 划分训练集/验证集
    split = train_test_split(
        X_overlap, X_semantic, X_weight, y,
        test_size=TEST_SIZE,
        random_state=SEED,
        stratify=y,
    )
    X_o_train, X_o_val = split[0], split[1]
    X_s_train, X_s_val = split[2], split[3]
    X_w_train, X_w_val = split[4], split[5]
    y_train, y_val = split[6], split[7]

    print(f"\n  训练集: {len(y_train)} 样本")
    print(f"  验证集: {len(y_val)} 样本")

    # 3. 训练V2三塔模型（计时）
    print(f"\n{'─' * 60}")
    print(f"开始训练...")
    print(f"{'─' * 60}")

    train_start = time.time()
    model, history, scalers = train_three_tower_v2(
        X_o_train, X_s_train, X_w_train, y_train,
        X_o_val, X_s_val, X_w_val, y_val,
        device,
    )
    train_elapsed = time.time() - train_start
    print(f"\n[计时] 训练耗时: {train_elapsed:.2f} 秒 ({train_elapsed/60:.2f} 分钟)")

    # 4. 评估
    metrics_train, _ = evaluate_model(
        model, X_o_train, X_s_train, X_w_train, y_train, scalers, "V2训练集"
    )
    metrics_val, pred_scores = evaluate_model(
        model, X_o_val, X_s_val, X_w_val, y_val, scalers, "V2验证集"
    )

    all_metrics = {}
    all_metrics.update({f"train_{k}": v for k, v in metrics_train.items()})
    all_metrics.update({f"val_{k}": v for k, v in metrics_val.items()})
    all_metrics["_total_samples"] = len(y)

    # 5. 特征重要性
    X_o_mean = X_overlap.mean(axis=0)
    X_s_mean = X_semantic.mean(axis=0)
    X_w_mean = X_weight.mean(axis=0)
    device_model = next(model.parameters()).device
    feature_importance = compute_feature_importance_v2(
        model, scalers, X_o_mean, X_s_mean, X_w_mean, device_model
    )

    # 6. 保存模型
    config["training_time_seconds"] = round(train_elapsed, 2)
    report = save_model_v2(model, scalers, all_metrics, feature_importance, history, config, model_dir)

    # 7. 输出总结
    print(f"\n{'=' * 60}")
    print(f"V2训练完成!")
    print(f"{'=' * 60}")
    print(f"  训练设备:     {device}")
    print(f"  训练耗时:     {train_elapsed:.2f} 秒 ({train_elapsed/60:.2f} 分钟)")
    print(f"  模型保存至:   {model_dir}")
    print(f"\n  训练/验证集指标:")
    print(f"    Train Accuracy: {metrics_train['accuracy']:.4f}")
    print(f"    Train AUC:      {metrics_train['auc']:.4f}")
    print(f"    Val   Accuracy: {metrics_val['accuracy']:.4f}")
    print(f"    Val   AUC:      {metrics_val['auc']:.4f}")
    print(f"\n  过拟合诊断:")
    acc_gap = metrics_train["accuracy"] - metrics_val["accuracy"]
    auc_gap = metrics_train["auc"] - metrics_val["auc"]
    print(f"    Acc Gap (Train-Val): {acc_gap:.4f} ({'✅ 良好' if acc_gap < 0.15 else '⚠️ 警惕' if acc_gap < 0.3 else '❌ 过拟合'})")
    print(f"    AUC Gap (Train-Val): {auc_gap:.4f} ({'✅ 良好' if auc_gap < 0.15 else '⚠️ 警惕' if auc_gap < 0.3 else '❌ 过拟合'})")
    print(f"\n  三塔权重分布:")
    t1_sum = sum(feature_importance.get(f, 0) for f in OVERLAP_FEATURES_V2)
    t2_sum = sum(feature_importance.get(f, 0) for f in SEMANTIC_FEATURES_V2)
    t3_sum = sum(feature_importance.get(f, 0) for f in WEIGHT_FEATURES_V2)
    total = t1_sum + t2_sum + t3_sum
    if total > 0:
        print(f"    Tower 1 (标签重叠):     {t1_sum:.6f} ({t1_sum/total*100:.1f}%)")
        print(f"    Tower 2 (语义相似度):   {t2_sum:.6f} ({t2_sum/total*100:.1f}%)")
        print(f"    Tower 3 (标签权重):     {t3_sum:.6f} ({t3_sum/total*100:.1f}%)")

    print(f"\n  V2新特征贡献:")
    for feat in V2_NEW_FEATURES:
        print(f"    {feat}: {feature_importance.get(feat, 0):.6f}")

    # 8. GPU vs CPU 加速比信息
    if not args.force_cpu and device.type != "cpu":
        print(f"\n  {'─' * 40}")
        print(f"  GPU加速信息:")
        print(f"  {'─' * 40}")
        print(f"    训练设备: {device}")
        print(f"    训练耗时: {train_elapsed:.2f} 秒")
        print(f"    提示: 用 --force-cpu 参数运行可对比CPU训练耗时")
        print(f"    用法: python {sys.argv[0]} --force-cpu --data {data_path}")

    return model, scalers, report


if __name__ == "__main__":
    main()
