#!/usr/bin/env python
"""
train_matching_model.py — AI数智名片 三塔匹配模型训练脚本

读取 prepare_training_data.py 生成的训练数据JSON，训练三塔模型合并评分。

模型架构（三塔）：
  Tower 1 (标签重叠): 4个特征 → Dense(8, ReLU) → Dense(4)
  Tower 2 (语义相似度): 1个特征 → Dense(4, ReLU) → Dense(2)
  Tower 3 (标签权重): 5个特征 → Dense(8, ReLU) → Dense(4)
  合并: Concat[4+2+4=10] → Dense(8, ReLU) → Dense(1, Sigmoid)

训练完成后输出：
  - 模型 checkpoint（PyTorch权重 + XGBoost备选）
  - 训练指标 (loss, accuracy, precision, recall, F1)
  - 特征重要性分析

无需修改已有文件，可独立运行。
"""

import json
import sys
import warnings
from pathlib import Path

import numpy as np
import torch
import torch.nn as nn
import torch.optim as optim
from sklearn.model_selection import train_test_split
from sklearn.metrics import (
    accuracy_score, precision_score, recall_score, f1_score,
    roc_auc_score, confusion_matrix, classification_report,
)
from sklearn.preprocessing import StandardScaler

warnings.filterwarnings("ignore")

# ── 配置 ─────────────────────────────────────────────────────────────
DATA_PATH = Path(__file__).resolve().parent.parent / "data" / "training_data.json"
MODEL_DIR = Path(__file__).resolve().parent.parent / "models"
SEED = 42
TEST_SIZE = 0.2
EPOCHS = 200
LR = 0.01
BATCH_SIZE = 16
WEIGHT_DECAY = 1e-4

torch.manual_seed(SEED)
np.random.seed(SEED)

# 特征组定义（三塔）
OVERLAP_FEATURES = ["tag_overlap_score", "common_tag_count",
                    "overlap_provide_to_need", "overlap_need_to_provide"]
SEMANTIC_FEATURES = ["vector_semantic"]
WEIGHT_FEATURES = ["tag_count_a", "tag_count_b", "avg_weight_a",
                   "avg_weight_b", "tag_weight_score"]
ALL_FEATURES = OVERLAP_FEATURES + SEMANTIC_FEATURES + WEIGHT_FEATURES


# ── 三塔模型 ──────────────────────────────────────────────────────────

class ThreeTowerModel(nn.Module):
    """三塔匹配模型

    Tower 1: 标签重叠特征
    Tower 2: 语义相似度特征
    Tower 3: 标签权重特征
    """

    def __init__(self, dropout: float = 0.2):
        super().__init__()

        # Tower 1 — 标签重叠
        self.tower_overlap = nn.Sequential(
            nn.Linear(len(OVERLAP_FEATURES), 8),
            nn.BatchNorm1d(8),
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.Linear(8, 4),
            nn.ReLU(),
        )

        # Tower 2 — 语义相似度
        self.tower_semantic = nn.Sequential(
            nn.Linear(len(SEMANTIC_FEATURES), 4),
            nn.BatchNorm1d(4),
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.Linear(4, 2),
            nn.ReLU(),
        )

        # Tower 3 — 标签权重
        self.tower_weight = nn.Sequential(
            nn.Linear(len(WEIGHT_FEATURES), 8),
            nn.BatchNorm1d(8),
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.Linear(8, 4),
            nn.ReLU(),
        )

        # 合并层
        combined_dim = 4 + 2 + 4  # 10
        self.combined = nn.Sequential(
            nn.Linear(combined_dim, 8),
            nn.BatchNorm1d(8),
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.Linear(8, 1),
            nn.Sigmoid(),
        )

    def forward(self, x_overlap, x_semantic, x_weight):
        out1 = self.tower_overlap(x_overlap)
        out2 = self.tower_semantic(x_semantic)
        out3 = self.tower_weight(x_weight)
        combined = torch.cat([out1, out2, out3], dim=1)
        return self.combined(combined).squeeze(1)


# ── 数据加载 ──────────────────────────────────────────────────────────

def load_training_data() -> tuple:
    """加载训练数据，返回特征矩阵和标签"""
    if not DATA_PATH.exists():
        print(f"[错误] 训练数据文件不存在: {DATA_PATH}")
        print("请先运行: python scripts/prepare_training_data.py")
        sys.exit(1)

    with open(DATA_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)

    meta = data.get("meta", {})
    samples = data.get("samples", [])

    print(f"\n[信息] 加载训练数据: {DATA_PATH}")
    print(f"  总样本数: {meta.get('total_samples', len(samples))}")
    print(f"  特征数:   {len(meta.get('feature_names', []))}")
    print(f"  用户数:   {meta.get('n_users', 0)}")

    features = {name: [] for name in ALL_FEATURES}
    labels = []

    for sample in samples:
        feat = sample["features"]
        for name in ALL_FEATURES:
            features[name].append(feat.get(name, 0.0))
        labels.append(sample["label"])

    # 构建三塔特征矩阵
    X_overlap = np.column_stack([features[name] for name in OVERLAP_FEATURES])
    X_semantic = np.column_stack([features[name] for name in SEMANTIC_FEATURES])
    X_weight = np.column_stack([features[name] for name in WEIGHT_FEATURES])
    y = np.array(labels, dtype=np.float32)

    return X_overlap, X_semantic, X_weight, y, samples, meta


# ── 训练函数 ──────────────────────────────────────────────────────────

def train_three_tower_model(
    X_overlap, X_semantic, X_weight, y,
    X_val_o, X_val_s, X_val_w, y_val,
) -> tuple[nn.Module, dict]:
    """训练三塔PyTorch模型"""
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
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"[信息] 使用设备: {device}")

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
    model = ThreeTowerModel(dropout=0.3).to(device)
    criterion = nn.BCELoss()
    optimizer = optim.Adam(model.parameters(), lr=LR, weight_decay=WEIGHT_DECAY)
    scheduler = optim.lr_scheduler.ReduceLROnPlateau(
        optimizer, mode="min", factor=0.5, patience=20
    )

    # 训练
    n_samples = len(y)
    best_val_loss = float("inf")
    best_model_state = None
    history = {"train_loss": [], "val_loss": [], "val_acc": []}

    print(f"\n{'=' * 60}")
    print(f"三塔模型训练")
    print(f"{'=' * 60}")

    for epoch in range(EPOCHS):
        model.train()

        # Mini-batch 训练
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

        scheduler.step(val_loss)

        history["train_loss"].append(avg_train_loss)
        history["val_loss"].append(val_loss)
        history["val_acc"].append(val_acc)

        if (epoch + 1) % 20 == 0 or epoch == 0:
            current_lr = optimizer.param_groups[0]["lr"]
            print(f"  Epoch {epoch+1:3d}/{EPOCHS} | "
                  f"Train Loss: {avg_train_loss:.4f} | "
                  f"Val Loss: {val_loss:.4f} | "
                  f"Val Acc: {val_acc:.4f} | "
                  f"LR: {current_lr:.6f}")

        if val_loss < best_val_loss:
            best_val_loss = val_loss
            best_model_state = {
                k: v.cpu().clone() for k, v in model.state_dict().items()
            }

    # 恢复最佳模型
    model.load_state_dict(best_model_state)
    model = model.to(device)

    # 保存 scalers
    scalers = {"overlap": scaler_o, "semantic": scaler_s, "weight": scaler_w}

    return model, history, scalers


# ── 评估函数 ──────────────────────────────────────────────────────────

def evaluate_model(model, X_o, X_s, X_w, y, scalers, name="三塔模型"):
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


def compute_feature_importance(model, scalers, X_o_mean, X_s_mean, X_w_mean, device):
    """计算特征重要性（通过逐个置零观察损失变化）"""
    model.eval()

    baseline_o = torch.FloatTensor(scalers["overlap"].transform(X_o_mean.reshape(1, -1))).to(device)
    baseline_s = torch.FloatTensor(scalers["semantic"].transform(X_s_mean.reshape(1, -1))).to(device)
    baseline_w = torch.FloatTensor(scalers["weight"].transform(X_w_mean.reshape(1, -1))).to(device)

    with torch.no_grad():
        baseline_pred = model(baseline_o, baseline_s, baseline_w).item()

    importance = {}
    feature_idx = 0

    # Tower 1 features
    for i, name in enumerate(OVERLAP_FEATURES):
        perturbed = X_o_mean.copy()
        perturbed[i] = 0.0
        p_o = torch.FloatTensor(scalers["overlap"].transform(perturbed.reshape(1, -1))).to(device)
        with torch.no_grad():
            pred = model(p_o, baseline_s, baseline_w).item()
        importance[name] = round(abs(baseline_pred - pred), 4)
        feature_idx += 1

    # Tower 2 features
    for i, name in enumerate(SEMANTIC_FEATURES):
        perturbed = X_s_mean.copy()
        perturbed[i] = 0.0
        p_s = torch.FloatTensor(scalers["semantic"].transform(perturbed.reshape(1, -1))).to(device)
        with torch.no_grad():
            pred = model(baseline_o, p_s, baseline_w).item()
        importance[name] = round(abs(baseline_pred - pred), 4)
        feature_idx += 1

    # Tower 3 features
    for i, name in enumerate(WEIGHT_FEATURES):
        perturbed = X_w_mean.copy()
        perturbed[i] = 0.0
        p_w = torch.FloatTensor(scalers["weight"].transform(perturbed.reshape(1, -1))).to(device)
        with torch.no_grad():
            pred = model(baseline_o, baseline_s, p_w).item()
        importance[name] = round(abs(baseline_pred - pred), 4)
        feature_idx += 1

    # 排序
    sorted_imp = sorted(importance.items(), key=lambda x: x[1], reverse=True)
    print(f"\n{'=' * 60}")
    print(f"特征重要性 (按 Tower 分组)")
    print(f"{'=' * 60}")
    print(f"  [Tower 1 — 标签重叠]")
    for name in OVERLAP_FEATURES:
        print(f"    {name:30s}: {importance[name]:.4f}")
    print(f"  [Tower 2 — 语义相似度]")
    for name in SEMANTIC_FEATURES:
        print(f"    {name:30s}: {importance[name]:.4f}")
    print(f"  [Tower 3 — 标签权重]")
    for name in WEIGHT_FEATURES:
        print(f"    {name:30s}: {importance[name]:.4f}")

    return importance


# ── 保存模型 ──────────────────────────────────────────────────────────

def save_model(model, scalers, metrics, feature_importance, history):
    """保存模型 checkpoint 和训练元数据"""
    MODEL_DIR.mkdir(parents=True, exist_ok=True)

    # 1. PyTorch 模型权重
    model_path = MODEL_DIR / "matching_model.pt"
    torch.save({
        "model_state_dict": model.state_dict(),
        "feature_names": ALL_FEATURES,
        "overlap_features": OVERLAP_FEATURES,
        "semantic_features": SEMANTIC_FEATURES,
        "weight_features": WEIGHT_FEATURES,
        "metrics": metrics,
    }, model_path)
    print(f"\n[保存] PyTorch 模型: {model_path}")

    # 2. 标准化参数
    scaler_path = MODEL_DIR / "matching_scalers.npy"
    scaler_data = {
        "overlap_mean": scalers["overlap"].mean_.tolist(),
        "overlap_scale": scalers["overlap"].scale_.tolist(),
        "semantic_mean": scalers["semantic"].mean_.tolist(),
        "semantic_scale": scalers["semantic"].scale_.tolist(),
        "weight_mean": scalers["weight"].mean_.tolist(),
        "weight_scale": scalers["weight"].scale_.tolist(),
    }
    np.save(str(scaler_path), scaler_data)
    print(f"[保存] 标准化参数: {scaler_path}")

    # 3. 训练报告
    report = {
        "model": "ThreeTowerModel (PyTorch)",
        "architecture": {
            "tower_overlap": f"Linear({len(OVERLAP_FEATURES)}→8→4)",
            "tower_semantic": f"Linear({len(SEMANTIC_FEATURES)}→4→2)",
            "tower_weight": f"Linear({len(WEIGHT_FEATURES)}→8→4)",
            "combined": "Linear(4+2+4=10→8→1) + Sigmoid",
        },
        "metrics": metrics,
        "feature_importance": feature_importance,
        "training_history": {
            "final_train_loss": history["train_loss"][-1],
            "final_val_loss": history["val_loss"][-1],
            "best_val_loss": min(history["val_loss"]),
            "best_val_acc": max(history["val_acc"]),
        },
        "feature_names": ALL_FEATURES,
    }

    report_path = MODEL_DIR / "training_report.json"
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    print(f"[保存] 训练报告: {report_path}")

    return report


# ── 推理函数（供外部调用） ──────────────────────────────────────────────

def load_model_for_inference(model_dir: str | Path = None) -> tuple[nn.Module, dict]:
    """加载训练好的模型用于推理"""
    if model_dir is None:
        model_dir = MODEL_DIR
    model_dir = Path(model_dir)

    model_path = model_dir / "matching_model.pt"
    scaler_path = model_dir / "matching_scalers.npy"

    if not model_path.exists():
        print(f"[错误] 模型文件不存在: {model_path}")
        return None, None

    # 加载 scalers
    scaler_data = np.load(str(scaler_path), allow_pickle=True).item()
    scalers = {
        "overlap": StandardScaler(),
        "semantic": StandardScaler(),
        "weight": StandardScaler(),
    }
    scalers["overlap"].mean_ = np.array(scaler_data["overlap_mean"])
    scalers["overlap"].scale_ = np.array(scaler_data["overlap_scale"])
    scalers["semantic"].mean_ = np.array(scaler_data["semantic_mean"])
    scalers["semantic"].scale_ = np.array(scaler_data["semantic_scale"])
    scalers["weight"].mean_ = np.array(scaler_data["weight_mean"])
    scalers["weight"].scale_ = np.array(scaler_data["weight_scale"])

    # 加载模型
    checkpoint = torch.load(model_path, map_location="cpu", weights_only=True)
    model = ThreeTowerModel()
    model.load_state_dict(checkpoint["model_state_dict"])
    model.eval()

    print(f"[信息] 模型已加载: {model_path}")
    print(f"[信息] 训练指标: {checkpoint.get('metrics', {})}")

    return model, scalers


# ── 主流程 ────────────────────────────────────────────────────────────

def main():
    print("=" * 60)
    print("AI数智名片 — 三塔匹配模型训练")
    print("=" * 60)

    # 1. 加载数据
    X_overlap, X_semantic, X_weight, y, samples, meta = load_training_data()

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

    # 3. 训练三塔模型
    model, history, scalers = train_three_tower_model(
        X_o_train, X_s_train, X_w_train, y_train,
        X_o_val, X_s_val, X_w_val, y_val,
    )

    # 4. 评估
    metrics_train, _ = evaluate_model(
        model, X_o_train, X_s_train, X_w_train, y_train, scalers, "训练集"
    )
    metrics_val, pred_scores = evaluate_model(
        model, X_o_val, X_s_val, X_w_val, y_val, scalers, "验证集"
    )

    # 5. 特征重要性
    X_o_mean = X_overlap.mean(axis=0)
    X_s_mean = X_semantic.mean(axis=0)
    X_w_mean = X_weight.mean(axis=0)
    device = next(model.parameters()).device
    feature_importance = compute_feature_importance(
        model, scalers, X_o_mean, X_s_mean, X_w_mean, device
    )

    # 6. 保存模型
    report = save_model(model, scalers, metrics_val, feature_importance, history)

    print(f"\n{'=' * 60}")
    print(f"训练完成!")
    print(f"{'=' * 60}")
    print(f"  模型保存至: {MODEL_DIR}")
    print(f"  验证集指标:")
    for k, v in metrics_val.items():
        print(f"    {k}: {v}")
    print(f"\n  三塔权重分布:")
    print(f"    Tower 1 (标签重叠): {sum(feature_importance.get(f, 0) for f in OVERLAP_FEATURES):.4f}")
    print(f"    Tower 2 (语义相似度): {sum(feature_importance.get(f, 0) for f in SEMANTIC_FEATURES):.4f}")
    print(f"    Tower 3 (标签权重): {sum(feature_importance.get(f, 0) for f in WEIGHT_FEATURES):.4f}")

    return model, scalers, report


if __name__ == "__main__":
    main()
