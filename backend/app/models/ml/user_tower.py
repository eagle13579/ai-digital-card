"""AI数智名片 — 用户 Embedding 塔 (UserTower)

四塔 DNN 架构中的用户特征嵌入模块。

架构:
  数值特征 → Linear(BN) ┐
                         ├─→ Concat ─→ DNN(256→128) ─→ L2-Norm ─→ 128d
  类别特征 → EmbeddingBag ┘

训练:
  Triplet Loss (anchor / positive / negative)
  Optimizer: Adam, lr=1e-3
  EarlyStopping: patience=5

用法:
    tower = UserTower(num_features=16, embedding_dim=128, hidden_dims=[256, 128])
    embeddings = tower(user_tensor)          # → (B, 128) L2 normalized

    encoder = UserFeatureEncoder()
    encoder.fit(df)
    tensor = encoder.transform(user_data)    # → (B, num_features)

数据适配:
    基于 AI数智名片 User/UserTag/Brochure 数据模型。
    数值特征: tag_count / brochure_count / view_count / membership_tier_encoded
    类别特征: purpose / top_tag / membership_tier
"""

from __future__ import annotations

import logging
import warnings
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

import numpy as np

try:
    import torch
    import torch.nn as nn
    import torch.nn.functional as F

    TORCH_AVAILABLE = True
except ImportError:
    TORCH_AVAILABLE = False

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# 常量
# ---------------------------------------------------------------------------
DEFAULT_EMBEDDING_DIM = 128
DEFAULT_HIDDEN_DIMS = [256, 128]
DEFAULT_LR = 1e-3
DEFAULT_PATIENCE = 5
DEFAULT_MARGIN = 0.3

# 用户塔特征 schema — 数值特征名列表
# 适配 AI数智名片 的 User / UserTag / Brochure 数据模型
NUMERIC_FEATURES = [
    "tag_count",           # 用户标签数量
    "brochure_count",      # 用户名片数量
    "view_count",          # 总浏览量
    "page_count",          # 名片页数
    "avg_intro_len",       # 简介平均长度
]
# 用户塔特征 schema — 类别特征名列表
CATEGORICAL_FEATURES = [
    "purpose",             # 名片用途 (partner/client/investor/supplier/business/personal/startup)
    "top_tag",             # 最重标签
    "membership_tier",     # 会员等级 (free/gold/diamond/board)
]

ALL_FEATURES = NUMERIC_FEATURES + CATEGORICAL_FEATURES

# 会员等级编码映射
MEMBERSHIP_TIER_MAP: Dict[str, int] = {
    "free": 0,
    "gold": 1,
    "diamond": 2,
    "board": 3,
}

# 名片用途编码映射
PURPOSE_MAP: Dict[str, int] = {
    "": 0,
    "partner": 1,
    "client": 2,
    "investor": 3,
    "supplier": 4,
    "business": 5,
    "personal": 6,
    "startup": 7,
}


# ===================================================================
# Triplet Loss
# ===================================================================
class TripletLoss(nn.Module):
    """Triplet Loss with semi-hard negative mining.

    L = max(d(anchor, positive) - d(anchor, negative) + margin, 0)
    """

    def __init__(self, margin: float = DEFAULT_MARGIN):
        super().__init__()
        self.margin = margin

    def forward(
        self,
        anchor: torch.Tensor,
        positive: torch.Tensor,
        negative: torch.Tensor,
    ) -> torch.Tensor:
        """Compute triplet loss.

        Args:
            anchor:   (B, D) anchor embeddings
            positive: (B, D) positive embeddings
            negative: (B, D) negative embeddings

        Returns:
            scalar loss tensor
        """
        d_pos = F.pairwise_distance(anchor, positive, p=2)       # (B,)
        d_neg = F.pairwise_distance(anchor, negative, p=2)       # (B,)
        loss = F.relu(d_pos - d_neg + self.margin)
        return loss.mean()


# ===================================================================
# 用户塔
# ===================================================================
class UserTower(nn.Module):
    """用户 Embedding 塔。

    输入: 拼接后的数值 + 类别 embedding 特征向量
    输出: L2 归一化的 128d 用户嵌入向量

    Args:
        num_features: 特征总数 (数值特征数 + 类别 embedding 拼接维数)
        embedding_dim: 输出嵌入维度 (默认 128)
        hidden_dims:   DNN 隐层维度列表 (默认 [256, 128])
        dropout:       Dropout 比率 (默认 0.1)
    """

    def __init__(
        self,
        num_features: int,
        embedding_dim: int = DEFAULT_EMBEDDING_DIM,
        hidden_dims: Optional[List[int]] = None,
        dropout: float = 0.1,
    ):
        super().__init__()
        hidden_dims = hidden_dims or list(DEFAULT_HIDDEN_DIMS)

        if not TORCH_AVAILABLE:
            raise ImportError(
                "PyTorch is required for UserTower. "
                "Install it via: pip install torch"
            )

        self.num_features = num_features
        self.embedding_dim = embedding_dim
        self.dropout_rate = dropout

        # ── DNN 塔 ──
        layers: List[nn.Module] = []
        in_dim = num_features
        for h_dim in hidden_dims:
            layers.extend([
                nn.Linear(in_dim, h_dim),
                nn.BatchNorm1d(h_dim),
                nn.ReLU(inplace=True),
                nn.Dropout(dropout),
            ])
            in_dim = h_dim
        # 输出层 (无激活, 后续 L2 Norm)
        layers.append(nn.Linear(in_dim, embedding_dim))

        self.fc_stack = nn.Sequential(*layers)

        # ── 初始化 ──
        self._init_weights()

    def _init_weights(self):
        """Xavier 均匀初始化"""
        for m in self.modules():
            if isinstance(m, nn.Linear):
                nn.init.xavier_uniform_(m.weight)
                if m.bias is not None:
                    nn.init.zeros_(m.bias)

    def forward(self, user_features: torch.Tensor) -> torch.Tensor:
        """前向传播 → L2 归一化的 128d 嵌入。

        Args:
            user_features: (B, num_features) 特征张量

        Returns:
            (B, embedding_dim) L2 归一化嵌入
        """
        # DNN 编码
        out = self.fc_stack(user_features)  # (B, embedding_dim)
        # L2 归一化
        out = F.normalize(out, p=2, dim=1)
        return out

    @torch.no_grad()
    def predict(self, user_features: torch.Tensor) -> np.ndarray:
        """推理接口, 返回 numpy 数组"""
        self.eval()
        emb = self.forward(user_features)
        return emb.cpu().numpy()

    # ------------------------------------------------------------------
    # 保存 / 加载
    # ------------------------------------------------------------------
    def save_model(self, path: Union[str, Path]) -> None:
        """保存模型权重。

        Args:
            path: 保存路径 (.pt / .pth)
        """
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        torch.save({"model_state_dict": self.state_dict()}, path)
        logger.info("[UserTower] 模型已保存到: %s", path)

    @classmethod
    def load_model(
        cls,
        path: Union[str, Path],
        num_features: int,
        embedding_dim: int = DEFAULT_EMBEDDING_DIM,
        hidden_dims: Optional[List[int]] = None,
        dropout: float = 0.1,
        map_location: Optional[str] = None,
    ) -> "UserTower":
        """加载模型权重。

        Args:
            path: 模型文件路径
            num_features: 特征总数
            embedding_dim: 输出嵌入维度
            hidden_dims:   DNN 隐层维度列表
            dropout:       Dropout 比率
            map_location:  设备映射 (默认自动检测)

        Returns:
            加载好权重的 UserTower 实例
        """
        path = Path(path)
        if map_location is None:
            map_location = "cuda" if torch.cuda.is_available() else "cpu"

        checkpoint = torch.load(path, map_location=map_location, weights_only=True)
        tower = cls(
            num_features=num_features,
            embedding_dim=embedding_dim,
            hidden_dims=hidden_dims,
            dropout=dropout,
        )
        tower.load_state_dict(checkpoint["model_state_dict"])
        tower.eval()
        logger.info("[UserTower] 模型已加载: %s", path)
        return tower

    def __repr__(self) -> str:
        hidden_dims_repr = [
            m.out_features
            for m in self.fc_stack
            if isinstance(m, nn.Linear)
        ][:-1]
        return (
            f"UserTower(num_features={self.num_features}, "
            f"embedding_dim={self.embedding_dim}, "
            f"hidden_dims={hidden_dims_repr})"
        )


# ===================================================================
# 特征编码器
# ===================================================================
class UserFeatureEncoder:
    """用户特征编码器。

    将原始用户特征 (dict/DataFrame) 编码为 UserTower 可接受的张量。

    数值特征: tag_count / brochure_count / view_count / page_count / avg_intro_len
    类别特征: purpose / top_tag / membership_tier — 用 EmbeddingBag 映射为稠密向量

    数据来源:
        - User: membership_tier
        - UserTag: tag_type, tag, weight
        - Brochure: purpose, pages_count, view_count, status

    Usage:
        encoder = UserFeatureEncoder(embedding_dim=16)
        encoder.fit(df)          # 学习统计量和类别数
        tensor = encoder.transform(user_data)  # → torch.Tensor
    """

    def __init__(
        self,
        embedding_dim: int = 16,
        numeric_features: Optional[List[str]] = None,
        categorical_features: Optional[List[str]] = None,
    ):
        self.embedding_dim = embedding_dim
        self.numeric_features = numeric_features or list(NUMERIC_FEATURES)
        self.categorical_features = categorical_features or list(CATEGORICAL_FEATURES)

        # ── 状态 (fit 后填充) ──
        self.numeric_mean: Dict[str, float] = {}
        self.numeric_std: Dict[str, float] = {}
        self.categorical_cardinality: Dict[str, int] = {}
        # 类别 → 索引映射
        self.categorical_mappings: Dict[str, Dict[Any, int]] = {}

        # PyTorch EmbeddingBag 层 (fit 后创建)
        self.embedding_bags: nn.ModuleDict = nn.ModuleDict()

        self._fitted = False

    # ------------------------------------------------------------------
    # fit
    # ------------------------------------------------------------------
    def fit(self, df: "Any") -> "UserFeatureEncoder":
        """从 DataFrame 学习特征统计。

        Args:
            df: pandas DataFrame, 列包含 numeric_features + categorical_features

        Returns:
            self (链式调用)
        """
        # ── 惰性导入 pandas ──
        try:
            import pandas as pd
        except ImportError:
            raise ImportError("pandas required for UserFeatureEncoder.fit()")

        if not isinstance(df, pd.DataFrame):
            raise TypeError(f"Expected pd.DataFrame, got {type(df).__name__}")

        # ── 数值特征统计 ──
        for feat in self.numeric_features:
            if feat not in df.columns:
                logger.warning("[UserFeatureEncoder] 数值特征 '%s' 不在 DataFrame 中, 使用默认值", feat)
                self.numeric_mean[feat] = 0.0
                self.numeric_std[feat] = 1.0
                continue
            col = df[feat].dropna()
            if len(col) == 0:
                self.numeric_mean[feat] = 0.0
                self.numeric_std[feat] = 1.0
            else:
                self.numeric_mean[feat] = float(col.mean())
                self.numeric_std[feat] = float(col.std()) or 1.0

        # ── 类别特征统计 ──
        for feat in self.categorical_features:
            if feat not in df.columns:
                logger.warning("[UserFeatureEncoder] 类别特征 '%s' 不在 DataFrame 中, 使用默认值", feat)
                self.categorical_cardinality[feat] = 2
                self.categorical_mappings[feat] = {}
                continue
            # 对类别特征: 先进行编码映射 (合并已知映射)
            col_unique = df[feat].dropna().unique()

            # 构建类别→索引映射 (优先使用预定义映射)
            if feat == "membership_tier":
                mapping: Dict[Any, int] = {}
                for val in col_unique:
                    mapping[val] = MEMBERSHIP_TIER_MAP.get(str(val), 1)
                # 确保所有标准值都在映射中
                for std_val, idx in MEMBERSHIP_TIER_MAP.items():
                    if std_val not in mapping:
                        mapping[std_val] = idx
                # 去重 (同一个idx保留一个)
                unique_mapping: Dict[Any, int] = {}
                seen_indices: set = set()
                for val, idx in sorted(mapping.items(), key=lambda x: x[1]):
                    if idx not in seen_indices:
                        unique_mapping[val] = idx
                        seen_indices.add(idx)
                self.categorical_mappings[feat] = unique_mapping
                self.categorical_cardinality[feat] = len(seen_indices) + 1  # +1 for unknown
            elif feat == "purpose":
                mapping = {}
                for val in col_unique:
                    mapping[val] = PURPOSE_MAP.get(str(val), 0)
                for std_val, idx in PURPOSE_MAP.items():
                    if std_val not in mapping:
                        mapping[std_val] = idx
                unique_mapping = {}
                seen_indices = set()
                for val, idx in sorted(mapping.items(), key=lambda x: x[1]):
                    if idx not in seen_indices:
                        unique_mapping[val] = idx
                        seen_indices.add(idx)
                self.categorical_mappings[feat] = unique_mapping
                self.categorical_cardinality[feat] = len(seen_indices) + 1
            else:
                # top_tag — 动态映射
                mapping = {val: idx + 1 for idx, val in enumerate(sorted(col_unique))}
                self.categorical_mappings[feat] = mapping
                self.categorical_cardinality[feat] = len(mapping) + 1  # +1 for unknown

        # ── 创建 EmbeddingBag 层 ──
        if TORCH_AVAILABLE:
            self.embedding_bags.clear()
            for feat in self.categorical_features:
                num_embeddings = self.categorical_cardinality.get(feat, 2)
                self.embedding_bags[feat] = nn.EmbeddingBag(
                    num_embeddings=num_embeddings,
                    embedding_dim=self.embedding_dim,
                    mode="mean",
                    padding_idx=0,
                )

        self._fitted = True
        return self

    # ------------------------------------------------------------------
    # transform
    # ------------------------------------------------------------------
    def transform(
        self,
        user_data: Union[Dict[str, Any], List[Dict[str, Any]], "Any"],
    ) -> "torch.Tensor":
        """将用户数据编码为张量。

        Args:
            user_data: 单个 dict 或 list[dict] 或 pd.DataFrame

        Returns:
            torch.Tensor shape (B, total_feature_dim)
            其中 total_feature_dim = len(numeric_features) + len(categorical_features) * embedding_dim
        """
        if not self._fitted:
            raise RuntimeError("UserFeatureEncoder 尚未 fit, 请先调用 .fit(df)")

        # ── 统一为 list[dict] ──
        rows = self._to_rows(user_data)
        B = len(rows)

        # ── 数值特征 (B, N_num) ──
        numeric_list = []
        for feat in self.numeric_features:
            vals = []
            for row in rows:
                raw = row.get(feat, 0.0)
                try:
                    v = (float(raw) - self.numeric_mean.get(feat, 0.0)) / self.numeric_std.get(feat, 1.0)
                except (ValueError, TypeError):
                    v = 0.0
                vals.append(v)
            numeric_list.append(vals)
        # (N_num, B) → (B, N_num)
        numeric_tensor = torch.tensor(numeric_list, dtype=torch.float32).T

        # ── 类别特征 (B, N_cat * embedding_dim) ──
        cat_embeddings_list = []
        for feat in self.categorical_features:
            indices = []
            mapping = self.categorical_mappings.get(feat, {})
            for row in rows:
                raw = row.get(feat, None)
                idx = mapping.get(raw, 0)  # 0 = unknown / padding
                indices.append(idx)
            # EmbeddingBag 需要 (B,) 索引 + (B,) 每样本偏移
            idx_tensor = torch.tensor(indices, dtype=torch.long)
            offsets = torch.arange(0, B, dtype=torch.long)
            if feat in self.embedding_bags:
                emb = self.embedding_bags[feat](idx_tensor, offsets)  # (B, embedding_dim)
            else:
                emb = torch.zeros(B, self.embedding_dim)
            cat_embeddings_list.append(emb)
        # (N_cat * B, embedding_dim) → (B, N_cat * embedding_dim)
        cat_tensor = torch.cat(cat_embeddings_list, dim=1) if cat_embeddings_list else torch.zeros(B, 0)

        # ── 拼接 ──
        out = torch.cat([numeric_tensor, cat_tensor], dim=1)
        return out.detach()  # 编码属于数据预处理, 不追踪梯度

    # ------------------------------------------------------------------
    # 便捷方法: 从 User / UserTag / Brochure 对象提取特征
    # ------------------------------------------------------------------
    @staticmethod
    def extract_features_from_models(
        user: Any,
        tags: Optional[List[Any]] = None,
        brochures: Optional[List[Any]] = None,
    ) -> Dict[str, Any]:
        """从 AI数智名片 数据模型对象提取特征 dict。

        Args:
            user: User 对象 (有 company, title, intro, membership_tier 等字段)
            tags: UserTag 对象列表 (有 tag_type, tag, weight 字段)
            brochures: Brochure 对象列表 (有 purpose, pages_count, view_count, status 字段)

        Returns:
            feature dict, 可直接传给 .transform() 或用于 DataFrame 构建
        """
        tags = tags or []
        brochures = brochures or []

        # 统计标签
        tag_count = len(tags)
        top_tag = ""
        if tags:
            # 按 weight 取最重标签
            sorted_tags = sorted(tags, key=lambda t: getattr(t, "weight", 1.0), reverse=True)
            top_tag = str(getattr(sorted_tags[0], "tag", ""))

        # 统计名片
        brochure_count = len(brochures)
        purpose = ""
        total_view_count = 0
        total_page_count = 0
        if brochures:
            purpose = str(getattr(brochures[0], "purpose", ""))
            for b in brochures:
                total_view_count += getattr(b, "view_count", 0) or 0
                total_page_count += getattr(b, "pages_count", 0) or 1

        # 简介长度
        intro = getattr(user, "intro", "") or ""
        avg_intro_len = len(intro)

        # 会员等级
        membership = getattr(user, "membership_tier", "free") or "free"

        return {
            "tag_count": tag_count,
            "brochure_count": brochure_count,
            "view_count": total_view_count,
            "page_count": total_page_count,
            "avg_intro_len": avg_intro_len,
            "purpose": purpose,
            "top_tag": top_tag,
            "membership_tier": membership,
        }

    # ------------------------------------------------------------------
    # 计算特征总维度 (供 UserTower 初始化使用)
    # ------------------------------------------------------------------
    @property
    def total_feature_dim(self) -> int:
        """编码后的特征总维度"""
        num_n = len(self.numeric_features)
        num_c = len(self.categorical_features)
        return num_n + num_c * self.embedding_dim

    # ------------------------------------------------------------------
    # 内部辅助
    # ------------------------------------------------------------------
    @staticmethod
    def _to_rows(
        user_data: Union[Dict, List[Dict], "Any"],
    ) -> List[Dict[str, Any]]:
        """统一输入为 list[dict]"""
        if isinstance(user_data, dict):
            return [user_data]
        if isinstance(user_data, list):
            return user_data
        # 尝试 pandas DataFrame
        try:
            import pandas as pd

            if isinstance(user_data, pd.DataFrame):
                return user_data.to_dict(orient="records")
        except ImportError:
            pass
        raise TypeError(
            f"不支持的输入类型: {type(user_data).__name__}, "
            f"期望 dict / list[dict] / pd.DataFrame"
        )

    def __repr__(self) -> str:
        status = "fitted" if self._fitted else "not fitted"
        return (
            f"UserFeatureEncoder("
            f"num_numeric={len(self.numeric_features)}, "
            f"num_categorical={len(self.categorical_features)}, "
            f"embedding_dim={self.embedding_dim}, "
            f"total_dim={self.total_feature_dim}, "
            f"status={status})"
        )


# ===================================================================
# 训练管线
# ===================================================================
class UserTowerTrainer:
    """用户塔训练管线。

    使用 Triplet Loss 训练 UserTower。

    Args:
        tower: UserTower 实例
        encoder: UserFeatureEncoder 实例
        lr: 学习率 (默认 1e-3)
        patience: 早停 patience (默认 5)
        margin: Triplet Loss margin (默认 0.3)
        device: 训练设备 (默认 auto)
    """

    def __init__(
        self,
        tower: UserTower,
        encoder: UserFeatureEncoder,
        lr: float = DEFAULT_LR,
        patience: int = DEFAULT_PATIENCE,
        margin: float = DEFAULT_MARGIN,
        device: Optional[str] = None,
    ):
        if not TORCH_AVAILABLE:
            raise ImportError("PyTorch required for training")

        self.tower = tower
        self.encoder = encoder
        self.lr = lr
        self.patience = patience
        self.margin = margin

        # ── 设备 ──
        if device is None:
            self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        else:
            self.device = torch.device(device)

        self.tower = self.tower.to(self.device)
        self.encoder.embedding_bags = self.encoder.embedding_bags.to(self.device)

        # ── 优化器 & 损失 ──
        self.optimizer = torch.optim.Adam(
            self.tower.parameters(),
            lr=self.lr,
            weight_decay=1e-5,
        )
        self.criterion = TripletLoss(margin=self.margin)

        # ── 训练状态 ──
        self.train_losses: List[float] = []
        self.val_losses: List[float] = []
        self.best_val_loss = float("inf")
        self.best_state_dict: Optional[Dict[str, Any]] = None
        self.epochs_no_improve = 0
        self.current_epoch = 0

    # ------------------------------------------------------------------
    # 训练一步
    # ------------------------------------------------------------------
    def train_step(
        self,
        anchor: torch.Tensor,
        positive: torch.Tensor,
        negative: torch.Tensor,
    ) -> float:
        """执行一步训练 (forward + backward + optimize)。

        Args:
            anchor:   (B, D) 锚点特征
            positive: (B, D) 正样本特征
            negative: (B, D) 负样本特征

        Returns:
            float: loss 值
        """
        self.tower.train()

        anchor = anchor.to(self.device)
        positive = positive.to(self.device)
        negative = negative.to(self.device)

        self.optimizer.zero_grad()

        a_emb = self.tower(anchor)
        p_emb = self.tower(positive)
        n_emb = self.tower(negative)

        loss = self.criterion(a_emb, p_emb, n_emb)
        loss.backward()
        self.optimizer.step()

        return loss.item()

    # ------------------------------------------------------------------
    # 训练一个 epoch
    # ------------------------------------------------------------------
    def train_epoch(
        self,
        anchors: torch.Tensor,
        positives: torch.Tensor,
        negatives: torch.Tensor,
        batch_size: int = 64,
    ) -> float:
        """完整遍历一个 epoch。

        Args:
            anchors:   (N, D) 所有锚点
            positives: (N, D) 所有正样本
            negatives: (N, D) 所有负样本
            batch_size: 批大小

        Returns:
            float: 平均 loss
        """
        N = anchors.size(0)
        indices = torch.randperm(N)
        total_loss = 0.0
        n_batches = 0

        for start in range(0, N, batch_size):
            end = min(start + batch_size, N)
            idx = indices[start:end]

            loss = self.train_step(
                anchors[idx],
                positives[idx],
                negatives[idx],
            )
            total_loss += loss
            n_batches += 1

        avg_loss = total_loss / max(n_batches, 1)
        self.train_losses.append(avg_loss)
        self.current_epoch += 1
        return avg_loss

    # ------------------------------------------------------------------
    # 验证
    # ------------------------------------------------------------------
    @torch.no_grad()
    def evaluate(
        self,
        anchors: torch.Tensor,
        positives: torch.Tensor,
        negatives: torch.Tensor,
        batch_size: int = 64,
    ) -> float:
        """验证集评估。

        Returns:
            float: 平均 loss
        """
        self.tower.eval()
        N = anchors.size(0)
        total_loss = 0.0
        n_batches = 0

        for start in range(0, N, batch_size):
            end = min(start + batch_size, N)
            a_emb = self.tower(anchors[start:end].to(self.device))
            p_emb = self.tower(positives[start:end].to(self.device))
            n_emb = self.tower(negatives[start:end].to(self.device))

            loss = self.criterion(a_emb, p_emb, n_emb)
            total_loss += loss.item()
            n_batches += 1

        avg_loss = total_loss / max(n_batches, 1)
        self.val_losses.append(avg_loss)

        # ── 早停检查 ──
        if avg_loss < self.best_val_loss:
            self.best_val_loss = avg_loss
            self.best_state_dict = {
                k: v.cpu().clone()
                for k, v in self.tower.state_dict().items()
            }
            self.epochs_no_improve = 0
        else:
            self.epochs_no_improve += 1

        return avg_loss

    # ------------------------------------------------------------------
    # 完整训练
    # ------------------------------------------------------------------
    def fit(
        self,
        train_anchors: torch.Tensor,
        train_positives: torch.Tensor,
        train_negatives: torch.Tensor,
        val_anchors: Optional[torch.Tensor] = None,
        val_positives: Optional[torch.Tensor] = None,
        val_negatives: Optional[torch.Tensor] = None,
        epochs: int = 50,
        batch_size: int = 64,
        verbose: bool = True,
    ) -> "UserTowerTrainer":
        """完整训练循环 (支持早停)。

        Args:
            train_anchors:   (N_train, D) 训练锚点
            train_positives: (N_train, D) 训练正样本
            train_negatives: (N_train, D) 训练负样本
            val_anchors:     (N_val, D) 验证锚点
            val_positives:   (N_val, D) 验证正样本
            val_negatives:   (N_val, D) 验证负样本
            epochs:          最大 epoch 数
            batch_size:      批大小
            verbose:         是否打印进度

        Returns:
            self
        """
        has_val = (
            val_anchors is not None
            and val_positives is not None
            and val_negatives is not None
        )

        for epoch in range(1, epochs + 1):
            train_loss = self.train_epoch(
                train_anchors, train_positives, train_negatives, batch_size
            )

            if has_val:
                val_loss = self.evaluate(
                    val_anchors, val_positives, val_negatives, batch_size
                )
                if verbose:
                    print(
                        f"Epoch {epoch:3d}/{epochs}  "
                        f"train_loss={train_loss:.6f}  "
                        f"val_loss={val_loss:.6f}  "
                        f"patience={self.patience - self.epochs_no_improve}/{self.patience}"
                    )

                # 早停
                if self.epochs_no_improve >= self.patience:
                    if verbose:
                        print(f"  → 早停触发 (epoch {epoch})")
                    break
            else:
                if verbose:
                    print(f"Epoch {epoch:3d}/{epochs}  train_loss={train_loss:.6f}")

        # ── 恢复最佳权重 ──
        if self.best_state_dict is not None:
            self.tower.load_state_dict(self.best_state_dict)
            if verbose:
                print(f"  → 已恢复最佳权重 (val_loss={self.best_val_loss:.6f})")

        return self

    # ------------------------------------------------------------------
    # 保存/加载
    # ------------------------------------------------------------------
    def save(self, path: Union[str, Path]) -> None:
        """保存模型权重和编码器状态。"""
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)

        checkpoint = {
            "tower_state_dict": self.tower.state_dict(),
            "encoder_numeric_mean": self.encoder.numeric_mean,
            "encoder_numeric_std": self.encoder.numeric_std,
            "encoder_categorical_cardinality": self.encoder.categorical_cardinality,
            "encoder_categorical_mappings": self.encoder.categorical_mappings,
            "encoder_embedding_dim": self.encoder.embedding_dim,
            "encoder_numeric_features": self.encoder.numeric_features,
            "encoder_categorical_features": self.encoder.categorical_features,
            "train_losses": self.train_losses,
            "val_losses": self.val_losses,
            "best_val_loss": self.best_val_loss,
            "current_epoch": self.current_epoch,
            "margin": self.margin,
        }
        torch.save(checkpoint, path)
        logger.info("[UserTowerTrainer] 模型已保存到: %s", path)

    def load(self, path: Union[str, Path]) -> "UserTowerTrainer":
        """加载模型权重。"""
        path = Path(path)
        checkpoint = torch.load(path, map_location=self.device)

        self.tower.load_state_dict(checkpoint["tower_state_dict"])
        self.encoder.numeric_mean = checkpoint["encoder_numeric_mean"]
        self.encoder.numeric_std = checkpoint["encoder_numeric_std"]
        self.encoder.categorical_cardinality = checkpoint["encoder_categorical_cardinality"]
        self.encoder.categorical_mappings = checkpoint["encoder_categorical_mappings"]
        self.encoder.embedding_dim = checkpoint["encoder_embedding_dim"]
        self.encoder.numeric_features = checkpoint["encoder_numeric_features"]
        self.encoder.categorical_features = checkpoint["encoder_categorical_features"]
        self.train_losses = checkpoint.get("train_losses", [])
        self.val_losses = checkpoint.get("val_losses", [])
        self.best_val_loss = checkpoint.get("best_val_loss", float("inf"))
        self.current_epoch = checkpoint.get("current_epoch", 0)
        self.margin = checkpoint.get("margin", self.margin)
        self.encoder._fitted = True

        logger.info("[UserTowerTrainer] 模型已加载: %s", path)
        return self
