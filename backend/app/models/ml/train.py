"""
AI数智名片 — 行为塔训练脚本

从模拟行为序列数据训练 BehaviorTower 模型。

用法:
    python -m app.models.ml.train
    python -m app.models.ml.train --epochs 20 --batch-size 64
"""

from __future__ import annotations

import argparse
import logging
import sys
import math
from pathlib import Path
from typing import Optional

import numpy as np

try:
    import torch
    import torch.nn as nn
    import torch.nn.functional as F
except ImportError:
    print("错误: 需要 PyTorch. 请执行: pip install torch")
    sys.exit(1)

from .behavior_tower import (
    BehaviorTower,
    BehaviorSequenceEncoder,
    BEHAVIOR_TYPE_MAP,
)

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# 常量
# ---------------------------------------------------------------------------
DEFAULT_EPOCHS = 50
DEFAULT_BATCH_SIZE = 64
DEFAULT_LR = 1e-3
DEFAULT_PATIENCE = 5
MODEL_SAVE_DIR = Path(__file__).resolve().parent / "checkpoints"

# 行为类型列表 (用于生成模拟数据)
BEHAVIOR_TYPES = list(BEHAVIOR_TYPE_MAP.keys())


# ===================================================================
# 模拟行为序列数据生成
# ===================================================================
def generate_synthetic_behavior_sequences(
    n_users: int = 100,
    seq_length_range: tuple = (1, 30),
    max_seq_len: int = 50,
    feature_dim: int = 32,
    seed: int = 42,
) -> list:
    """生成模拟用户行为序列数据。

    Args:
        n_users: 用户数
        seq_length_range: 序列长度范围 (min, max)
        max_seq_len: 最大序列长度 (用于截断)
        feature_dim: 特征维度
        seed: 随机种子

    Returns:
        List[List[Dict]]: 每个用户的行为序列
    """
    rng = np.random.RandomState(seed)

    sequences = []
    for _ in range(n_users):
        seq_len = rng.randint(seq_length_range[0], seq_length_range[1] + 1)

        seq = []
        for i in range(min(seq_len, max_seq_len * 2)):  # 生成多一些用于截断测试
            behavior = {
                "behavior_type": rng.choice(BEHAVIOR_TYPES),
                "timestamp_gap": float(rng.exponential(scale=10.0)),
                "duration": float(rng.exponential(scale=30.0) + 1.0),
                "target_id": int(rng.randint(1, 50)),
                "action_value": float(rng.uniform(0.5, 5.0)),
            }
            seq.append(behavior)

        sequences.append(seq)

    return sequences


def encode_sequences_to_tensor(
    sequences: list,
    encoder: BehaviorSequenceEncoder,
) -> tuple:
    """将行为序列编码为张量。

    Args:
        sequences: List[List[Dict]] 行为序列
        encoder: BehaviorSequenceEncoder 实例

    Returns:
        (tensor, mask): 行为序列张量和掩码
    """
    tensor, mask = encoder.transform(sequences)
    return tensor, mask


# ===================================================================
# 对比损失 (Contrastive Loss)
# ===================================================================
class ContrastiveLoss(nn.Module):
    """对比损失函数，用于行为序列表示学习。

    正样本对: 同一用户的不同行为序列片段
    负样本对: 不同用户的行为序列

    Args:
        margin: 正负样本边界 (默认 0.5)
        temperature: 温度参数 (默认 0.07)
    """

    def __init__(self, margin: float = 0.5, temperature: float = 0.07):
        super().__init__()
        self.margin = margin
        self.temperature = temperature

    def forward(
        self,
        anchor: torch.Tensor,
        positive: torch.Tensor,
        negative: torch.Tensor,
    ) -> torch.Tensor:
        """计算对比损失。

        Args:
            anchor: (B, D) 锚点嵌入
            positive: (B, D) 正样本嵌入
            negative: (B, D) 负样本嵌入

        Returns:
            scalar 损失值
        """
        # L2 归一化
        anchor = F.normalize(anchor, p=2, dim=1)
        positive = F.normalize(positive, p=2, dim=1)
        negative = F.normalize(negative, p=2, dim=1)

        # 余弦相似度
        pos_sim = (anchor * positive).sum(dim=1)  # (B,)
        neg_sim = (anchor * negative).sum(dim=1)  # (B,)

        # Triplet loss
        losses = F.relu(pos_sim - neg_sim + self.margin)
        return losses.mean()


# ===================================================================
# 训练器
# ===================================================================
class BehaviorTowerTrainer:
    """BehaviorTower 训练器。

    Args:
        tower: BehaviorTower 实例
        lr: 学习率
        patience: 早停 patience
        margin: Triplet loss margin
        temperature: 对比损失温度
    """

    def __init__(
        self,
        tower: BehaviorTower,
        lr: float = DEFAULT_LR,
        patience: int = DEFAULT_PATIENCE,
        margin: float = 0.5,
        temperature: float = 0.07,
    ):
        self.tower = tower
        self.lr = lr
        self.patience = patience
        self.margin = margin
        self.temperature = temperature

        self.optimizer = torch.optim.Adam(
            self.tower.parameters(), lr=lr, weight_decay=1e-5
        )
        self.scheduler = torch.optim.lr_scheduler.ReduceLROnPlateau(
            self.optimizer, mode="min", factor=0.5, patience=patience // 2, verbose=True
        )
        self.criterion = ContrastiveLoss(margin=margin, temperature=temperature)

        self.best_loss = float("inf")
        self.best_state: Optional[dict] = None
        self.epochs_no_improve = 0

    def fit(
        self,
        train_tensor: torch.Tensor,
        train_mask: torch.Tensor,
        val_tensor: Optional[torch.Tensor] = None,
        val_mask: Optional[torch.Tensor] = None,
        epochs: int = DEFAULT_EPOCHS,
        batch_size: int = DEFAULT_BATCH_SIZE,
        verbose: bool = True,
    ) -> list:
        """训练行为塔。

        Args:
            train_tensor: (N, max_seq_len, feature_dim) 训练数据
            train_mask: (N, max_seq_len) 训练掩码
            val_tensor: (N_val, ...) 验证数据 (可选)
            val_mask: (N_val, ...) 验证掩码 (可选)
            epochs: 最大训练轮数
            batch_size: 批大小
            verbose: 是否打印进度

        Returns:
            训练损失历史
        """
        N = train_tensor.size(0)
        history = []

        for epoch in range(1, epochs + 1):
            self.tower.train()
            epoch_loss = 0.0
            n_batches = 0

            # ── 打乱数据 ──
            indices = torch.randperm(N)
            shuffled_tensor = train_tensor[indices]
            shuffled_mask = train_mask[indices]

            for start in range(0, N, batch_size):
                end = min(start + batch_size, N)
                batch_t = shuffled_tensor[start:end]
                batch_m = shuffled_mask[start:end]

                # 构建正负样本对
                # 锚点: 原始行为序列
                anchor_emb = self.tower(batch_t, batch_m)  # (B, 128)

                # 正样本: 随机 mask 部分行为 (数据增强)
                positive_t = batch_t.clone()
                if batch_m is not None:
                    # 随机丢弃 20% 的有效行为
                    drop_mask = torch.rand_like(batch_m.float()) < 0.2
                    drop_mask = drop_mask & batch_m
                    positive_t = positive_t.clone()
                    positive_t[drop_mask] = 0.0
                    positive_m = batch_m.clone()
                    positive_m[drop_mask] = False
                else:
                    positive_m = None
                positive_emb = self.tower(positive_t, positive_m)

                # 负样本: 使用不同 batch 的行
                if end < N and end + batch_size <= N:
                    neg_idx = indices[start + batch_size - 1:start + 2 * batch_size - 1] if start + 2 * batch_size <= N else indices[:end]
                    neg_t = shuffled_tensor[neg_idx[:batch_t.size(0)]]
                    neg_m = shuffled_mask[neg_idx[:batch_t.size(0)]]
                else:
                    neg_t = shuffled_tensor[:batch_t.size(0)]
                    neg_m = shuffled_mask[:batch_t.size(0)]
                negative_emb = self.tower(neg_t, neg_m)

                # 损失
                loss = self.criterion(anchor_emb, positive_emb, negative_emb)

                self.optimizer.zero_grad()
                loss.backward()
                torch.nn.utils.clip_grad_norm_(self.tower.parameters(), max_norm=1.0)
                self.optimizer.step()

                epoch_loss += loss.item()
                n_batches += 1

            avg_loss = epoch_loss / max(n_batches, 1)

            # ── 验证 ──
            val_loss = None
            if val_tensor is not None:
                val_loss = self._evaluate(val_tensor, val_mask, batch_size)
                self.scheduler.step(val_loss)
            else:
                self.scheduler.step(avg_loss)

            history.append(avg_loss)

            # ── 早停 ──
            monitor_loss = val_loss if val_loss is not None else avg_loss
            if monitor_loss < self.best_loss:
                self.best_loss = monitor_loss
                self.best_state = {
                    k: v.clone().cpu() for k, v in self.tower.state_dict().items()
                }
                self.epochs_no_improve = 0
            else:
                self.epochs_no_improve += 1

            if verbose:
                val_str = f", val_loss={val_loss:.6f}" if val_loss is not None else ""
                print(f"  Epoch {epoch:3d}/{epochs}: loss={avg_loss:.6f}{val_str}")

            if self.epochs_no_improve >= self.patience:
                if verbose:
                    print(f"  早停触发 (patience={self.patience})")
                break

        # ── 恢复最佳状态 ──
        if self.best_state is not None:
            self.tower.load_state_dict(self.best_state)
            if verbose:
                print(f"  已恢复最佳模型 (loss={self.best_loss:.6f})")

        return history

    @torch.no_grad()
    def _evaluate(
        self,
        tensor: torch.Tensor,
        mask: torch.Tensor,
        batch_size: int,
    ) -> float:
        """评估验证集损失"""
        self.tower.eval()
        N = tensor.size(0)
        total_loss = 0.0
        n_batches = 0

        for start in range(0, N, batch_size):
            end = min(start + batch_size, N)
            batch_t = tensor[start:end]
            batch_m = mask[start:end]

            anchor_emb = self.tower(batch_t, batch_m)

            # 正样本 (小噪声)
            noise = torch.randn_like(batch_t) * 0.05
            positive_emb = self.tower(batch_t + noise, batch_m)

            # 负样本 (使用其他用户)
            neg_indices = torch.randperm(N)[:batch_t.size(0)]
            negative_emb = self.tower(tensor[neg_indices], mask[neg_indices])

            loss = self.criterion(anchor_emb, positive_emb, negative_emb)
            total_loss += loss.item()
            n_batches += 1

        return total_loss / max(n_batches, 1)

    def save(self, path: str) -> str:
        """保存训练好的模型和优化器状态"""
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        torch.save({
            "model_state_dict": self.tower.state_dict(),
            "optimizer_state_dict": self.optimizer.state_dict(),
            "best_loss": self.best_loss,
        }, str(path))
        logger.info(f"训练器状态已保存: {path}")
        return str(path)

    def load(self, path: str) -> "BehaviorTowerTrainer":
        """加载训练好的模型"""
        path = Path(path)
        if not path.exists():
            raise FileNotFoundError(f"检查点文件不存在: {path}")
        checkpoint = torch.load(str(path), map_location="cpu")
        self.tower.load_state_dict(checkpoint["model_state_dict"])
        self.optimizer.load_state_dict(checkpoint["optimizer_state_dict"])
        self.best_loss = checkpoint.get("best_loss", float("inf"))
        logger.info(f"训练器状态已加载: {path}")
        return self


# ===================================================================
# 训练入口
# ===================================================================
def train(args: argparse.Namespace) -> BehaviorTowerTrainer:
    """执行行为塔训练。

    Args:
        args: 命令行参数

    Returns:
        BehaviorTowerTrainer 实例 (已训练)
    """
    print("=" * 60)
    print("  行为序列塔 — 训练")
    print("=" * 60)
    print()

    # ── 1. 生成数据 ──
    print("[1/5] 生成模拟行为序列数据...")
    sequences = generate_synthetic_behavior_sequences(
        n_users=args.n_users,
        seq_length_range=(1, args.max_seq_len),
        max_seq_len=args.max_seq_len,
        feature_dim=args.feature_dim,
        seed=args.seed,
    )
    print(f"       → {len(sequences)} 个用户的行为序列")

    # ── 2. 构建编码器 ──
    print("[2/5] 构建行为序列编码器...")
    # 先从序列中提取扁平化 DataFrame
    flat_data = []
    for user_seq in sequences:
        for behavior in user_seq:
            flat_data.append(behavior)

    import pandas as pd
    df = pd.DataFrame(flat_data)
    print(f"       → {len(df)} 条行为记录")

    encoder = BehaviorSequenceEncoder(
        max_seq_len=args.max_seq_len,
        feature_dim=args.feature_dim,
    )
    encoder.fit(df)
    print(f"       → {encoder}")

    # ── 3. 编码数据 ──
    print("[3/5] 编码行为序列...")
    tensor, mask = encode_sequences_to_tensor(sequences, encoder)
    N = tensor.size(0)
    split = int(N * 0.8)
    train_tensor, train_mask = tensor[:split], mask[:split]
    val_tensor, val_mask = tensor[split:], mask[split:]
    print(f"       → 训练集: {split} 用户, 验证集: {N - split} 用户")
    print(f"       → 张量形状: {tensor.shape}")

    # ── 4. 构建模型 ──
    print("[4/5] 构建 BehaviorTower 模型...")
    tower = BehaviorTower(
        max_seq_len=args.max_seq_len,
        feature_dim=args.feature_dim,
        hidden_dim=args.hidden_dim,
        nhead=args.nhead,
        num_layers=args.num_layers,
        dropout=args.dropout,
    )
    print(f"       → {tower}")
    print(f"       → 参数量: {sum(p.numel() for p in tower.parameters()):,}")

    # ── 5. 训练 ──
    print("[5/5] 开始训练...")
    trainer = BehaviorTowerTrainer(
        tower=tower,
        lr=args.lr,
        patience=args.patience,
        margin=args.margin,
        temperature=args.temperature,
    )
    trainer.fit(
        train_tensor=train_tensor,
        train_mask=train_mask,
        val_tensor=val_tensor,
        val_mask=val_mask,
        epochs=args.epochs,
        batch_size=args.batch_size,
        verbose=True,
    )

    # ── 保存 ──
    if args.save_dir:
        save_path = Path(args.save_dir)
    else:
        save_path = MODEL_SAVE_DIR
    save_path.mkdir(parents=True, exist_ok=True)

    # 保存模型
    model_path = save_path / "behavior_tower.pt"
    tower.save(str(model_path))

    # 保存训练器状态
    trainer_path = save_path / "trainer_checkpoint.pt"
    trainer.save(str(trainer_path))
    print(f"\n  → 模型已保存: {model_path}")

    # ── 验证推理 ──
    print("\n  → 推理验证:")
    sample_t = tensor[:3]
    sample_m = mask[:3]
    embeddings = tower.predict(sample_t, sample_m)
    for i, emb in enumerate(embeddings):
        norm = np.linalg.norm(emb)
        print(f"      用户 {i+1}: norm={norm:.6f}, dim={emb.shape[0]}")

    print()
    print("=" * 60)
    print("  训练完成!")
    print("=" * 60)
    return trainer


# ===================================================================
# CLI
# ===================================================================
def parse_args(argv: Optional[list] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="AI数智名片 — 行为塔训练脚本",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument("--epochs", type=int, default=DEFAULT_EPOCHS,
                        help="最大训练 epoch 数")
    parser.add_argument("--batch-size", type=int, default=DEFAULT_BATCH_SIZE,
                        help="批大小")
    parser.add_argument("--lr", type=float, default=DEFAULT_LR,
                        help="学习率")
    parser.add_argument("--hidden-dim", type=int, default=128,
                        help="Transformer 隐层维度")
    parser.add_argument("--feature-dim", type=int, default=32,
                        help="行为特征维度")
    parser.add_argument("--max-seq-len", type=int, default=50,
                        help="最大行为序列长度")
    parser.add_argument("--nhead", type=int, default=4,
                        help="Multi-head attention 头数")
    parser.add_argument("--num-layers", type=int, default=2,
                        help="Transformer encoder 层数")
    parser.add_argument("--dropout", type=float, default=0.1,
                        help="Dropout 比率")
    parser.add_argument("--patience", type=int, default=DEFAULT_PATIENCE,
                        help="早停 patience")
    parser.add_argument("--margin", type=float, default=0.5,
                        help="Contrastive Loss margin")
    parser.add_argument("--temperature", type=float, default=0.07,
                        help="对比损失温度参数")
    parser.add_argument("--n-users", type=int, default=100,
                        help="模拟用户数")
    parser.add_argument("--save-dir", type=str, default=None,
                        help="模型保存目录 (默认: ml/models/checkpoints/)")
    parser.add_argument("--seed", type=int, default=42,
                        help="随机种子")
    return parser.parse_args(argv)


if __name__ == "__main__":
    args = parse_args()
    train(args)
