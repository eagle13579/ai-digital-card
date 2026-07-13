"""AI数智名片 — 企业 Embedding 塔 (EnterpriseTower)

四塔 DNN 架构中的企业特征嵌入模块。

架构:
  企业特征 → BN → DNN(256→128) → L2-Norm → 128d

特征 (基于 AI数智名片 Brochure/User 数据模型):
  - brochure_count          名片数量
  - avg_pages_per_brochure  平均名片页数
  - total_view_count        总浏览量
  - brochure_diversity      名片用途多样性 (不同 purpose 数量)
  - company_name_len        公司名称长度
  - pages_with_ai_summary   AI摘要页数
  - purpose                 名片用途 (类别)
  - visibility              可见性 (类别)

用法:
    tower = EnterpriseTower(num_features=7, embedding_dim=128, hidden_dims=[256, 128])
    embeddings = tower(enterprise_features)  # → (B, 128) L2 normalized

    encoder = EnterpriseFeatureEncoder()
    encoder.fit(df)
    tensor = encoder.transform(enterprise_data)  # → (B, num_features)
"""

from __future__ import annotations

import logging
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

# 企业塔特征 schema — 全部作为数值特征处理
ENTERPRISE_FEATURES = [
    "brochure_count",             # 名片数量
    "avg_pages_per_brochure",     # 平均名片页数
    "total_view_count",           # 总浏览量
    "brochure_diversity",         # 名片用途多样性
    "company_name_len",           # 公司名称长度
    "pages_with_ai_summary",      # AI摘要页数
]

# 类别特征 (通过 EmbeddingBag 或枚举映射)
ENTERPRISE_CATEGORICAL_FEATURES = [
    "purpose",                    # 名片用途 (partner/client/investor/...)
    "visibility",                 # 可见性 (public/platform/network/private)
]

# 名片用途映射
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

# 可见性映射
VISIBILITY_MAP: Dict[str, int] = {
    "public": 0,
    "platform": 1,
    "network": 2,
    "private": 3,
}

ALL_FEATURES = ENTERPRISE_FEATURES + ENTERPRISE_CATEGORICAL_FEATURES


# ===================================================================
# 企业塔
# ===================================================================
class EnterpriseTower(nn.Module):
    """企业 Embedding 塔。

    输入: 企业特征 (数值化后)
    输出: L2 归一化的 128d 企业嵌入向量

    Args:
        num_features: 特征总数 (默认: len(ENTERPRISE_FEATURES) + 类别embedding维数)
        embedding_dim: 输出嵌入维度 (默认 128)
        hidden_dims:   DNN 隐层维度列表 (默认 [256, 128])
        dropout:       Dropout 比率 (默认 0.1)
    """

    def __init__(
        self,
        num_features: int = len(ENTERPRISE_FEATURES),
        embedding_dim: int = DEFAULT_EMBEDDING_DIM,
        hidden_dims: Optional[List[int]] = None,
        dropout: float = 0.1,
    ):
        super().__init__()

        if not TORCH_AVAILABLE:
            raise ImportError(
                "PyTorch is required for EnterpriseTower. "
                "Install it via: pip install torch"
            )

        self.num_features = num_features
        self.embedding_dim = embedding_dim
        self.dropout_rate = dropout

        hidden_dims = hidden_dims or list(DEFAULT_HIDDEN_DIMS)

        # ── 批量归一化 ──
        self.input_bn = nn.BatchNorm1d(num_features)

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

    def forward(self, enterprise_features: torch.Tensor) -> torch.Tensor:
        """前向传播 → L2 归一化的 128d 嵌入。

        Args:
            enterprise_features: (B, num_features) 特征张量

        Returns:
            (B, embedding_dim) L2 归一化嵌入
        """
        # BN 预处理
        x = self.input_bn(enterprise_features)
        # DNN 编码
        out = self.fc_stack(x)  # (B, embedding_dim)
        # L2 归一化
        out = F.normalize(out, p=2, dim=1)
        return out

    @torch.no_grad()
    def predict(self, enterprise_features: torch.Tensor) -> np.ndarray:
        """推理接口, 返回 numpy 数组"""
        self.eval()
        emb = self.forward(enterprise_features)
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
        logger.info("[EnterpriseTower] 模型已保存到: %s", path)

    @classmethod
    def load_model(
        cls,
        path: Union[str, Path],
        num_features: int = len(ENTERPRISE_FEATURES),
        embedding_dim: int = DEFAULT_EMBEDDING_DIM,
        hidden_dims: Optional[List[int]] = None,
        dropout: float = 0.1,
        map_location: Optional[str] = None,
    ) -> "EnterpriseTower":
        """加载模型权重。

        Args:
            path: 模型文件路径
            num_features: 特征总数
            embedding_dim: 输出嵌入维度
            hidden_dims:   DNN 隐层维度列表
            dropout:       Dropout 比率
            map_location:  设备映射 (默认自动检测)

        Returns:
            加载好权重的 EnterpriseTower 实例
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
        logger.info("[EnterpriseTower] 模型已加载: %s", path)
        return tower

    def __repr__(self) -> str:
        return (
            f"EnterpriseTower(num_features={self.num_features}, "
            f"embedding_dim={self.embedding_dim})"
        )


# ===================================================================
# 企业特征编码器
# ===================================================================
class EnterpriseFeatureEncoder:
    """企业特征编码器。

    将原始企业特征 (dict/DataFrame) 编码为 EnterpriseTower 可接受的张量。

    特征处理:
      - 数值特征: z-score 标准化
      - 类别特征: 按照预定义映射编码为数值 + z-score 标准化

    数据来源:
        - Brochure: purpose, pages_count, view_count, visibility, status
        - User: company, title

    Usage:
        encoder = EnterpriseFeatureEncoder()
        encoder.fit(df)                  # 学习统计量
        tensor = encoder.transform(data) # → torch.Tensor
    """

    def __init__(
        self,
        cat_embedding_dim: int = 8,
        numeric_features: Optional[List[str]] = None,
        categorical_features: Optional[List[str]] = None,
    ):
        self.cat_embedding_dim = cat_embedding_dim
        self.numeric_features = numeric_features or list(ENTERPRISE_FEATURES)
        self.categorical_features = categorical_features or list(ENTERPRISE_CATEGORICAL_FEATURES)

        # ── 状态 (fit 后填充) ──
        self.feature_mean: Dict[str, float] = {}
        self.feature_std: Dict[str, float] = {}
        self.categorical_cardinality: Dict[str, int] = {}
        self.categorical_mappings: Dict[str, Dict[Any, int]] = {}

        # PyTorch EmbeddingBag 层 (fit 后创建)
        self.embedding_bags: nn.ModuleDict = nn.ModuleDict()

        self._fitted = False

    # ------------------------------------------------------------------
    # fit
    # ------------------------------------------------------------------
    def fit(self, df: "Any") -> "EnterpriseFeatureEncoder":
        """从 DataFrame 学习特征统计量。

        Args:
            df: pandas DataFrame, 列包含 numeric_features + categorical_features

        Returns:
            self (链式调用)
        """
        try:
            import pandas as pd
        except ImportError:
            raise ImportError("pandas required for EnterpriseFeatureEncoder.fit()")

        if not isinstance(df, pd.DataFrame):
            raise TypeError(f"Expected pd.DataFrame, got {type(df).__name__}")

        # ── 数值特征统计 ──
        for feat in self.numeric_features:
            if feat not in df.columns:
                logger.warning(
                    "[EnterpriseFeatureEncoder] 特征 '%s' 不在 DataFrame 中, 使用默认值", feat
                )
                self.feature_mean[feat] = 0.0
                self.feature_std[feat] = 1.0
                continue
            col = df[feat].dropna()
            if len(col) == 0:
                self.feature_mean[feat] = 0.0
                self.feature_std[feat] = 1.0
            else:
                self.feature_mean[feat] = float(col.mean())
                self.feature_std[feat] = float(col.std()) or 1.0

        # ── 类别特征统计 ──
        for feat in self.categorical_features:
            if feat not in df.columns:
                logger.warning("[EnterpriseFeatureEncoder] 类别特征 '%s' 不在 DataFrame 中, 使用默认值", feat)
                self.categorical_cardinality[feat] = 2
                self.categorical_mappings[feat] = {}
                continue
            mapping: Dict[Any, int] = {}
            col_unique = df[feat].dropna().unique()
            if feat == "purpose":
                for val in col_unique:
                    mapping[val] = PURPOSE_MAP.get(str(val), 0)
                for std_val, idx in PURPOSE_MAP.items():
                    if std_val not in mapping:
                        mapping[std_val] = idx
            elif feat == "visibility":
                for val in col_unique:
                    mapping[val] = VISIBILITY_MAP.get(str(val), 0)
                for std_val, idx in VISIBILITY_MAP.items():
                    if std_val not in mapping:
                        mapping[std_val] = idx
            else:
                mapping = {val: idx + 1 for idx, val in enumerate(sorted(col_unique))}

            # 去重
            unique_mapping: Dict[Any, int] = {}
            seen_indices: set = set()
            for val, idx in sorted(mapping.items(), key=lambda x: x[1]):
                if idx not in seen_indices:
                    unique_mapping[val] = idx
                    seen_indices.add(idx)
            self.categorical_mappings[feat] = unique_mapping
            self.categorical_cardinality[feat] = len(seen_indices) + 1  # +1 for unknown

        # ── 创建 EmbeddingBag 层 ──
        if TORCH_AVAILABLE:
            self.embedding_bags.clear()
            for feat in self.categorical_features:
                num_embeddings = self.categorical_cardinality.get(feat, 2)
                self.embedding_bags[feat] = nn.EmbeddingBag(
                    num_embeddings=num_embeddings,
                    embedding_dim=self.cat_embedding_dim,
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
        enterprise_data: Union[Dict[str, Any], List[Dict[str, Any]], "Any"],
    ) -> "torch.Tensor":
        """将企业数据编码为张量。

        Args:
            enterprise_data: 单个 dict 或 list[dict] 或 pd.DataFrame

        Returns:
            torch.Tensor shape (B, total_feature_dim)
            其中 total_feature_dim = len(numeric_features) + len(categorical_features) * cat_embedding_dim
        """
        if not self._fitted:
            raise RuntimeError("EnterpriseFeatureEncoder 尚未 fit, 请先调用 .fit(df)")

        # ── 统一为 list[dict] ──
        rows = self._to_rows(enterprise_data)
        B = len(rows)

        # ── 数值特征 (B, N_num) ──
        feat_vals = []
        for feat in self.numeric_features:
            vals = []
            for row in rows:
                raw = row.get(feat, 0.0)
                try:
                    v = float(raw)
                except (ValueError, TypeError):
                    v = 0.0
                # z-score 标准化
                mean_v = self.feature_mean.get(feat, 0.0)
                std_v = self.feature_std.get(feat, 1.0)
                vals.append((v - mean_v) / std_v)
            feat_vals.append(vals)

        # (N_num, B) → (B, N_num)
        numeric_tensor = torch.tensor(feat_vals, dtype=torch.float32).T

        # ── 类别特征 (B, N_cat * cat_embedding_dim) ──
        cat_embeddings_list = []
        for feat in self.categorical_features:
            indices = []
            mapping = self.categorical_mappings.get(feat, {})
            for row in rows:
                raw = row.get(feat, None)
                idx = mapping.get(raw, 0)  # 0 = unknown / padding
                indices.append(idx)
            idx_tensor = torch.tensor(indices, dtype=torch.long)
            offsets = torch.arange(0, B, dtype=torch.long)
            if feat in self.embedding_bags:
                emb = self.embedding_bags[feat](idx_tensor, offsets)  # (B, cat_embedding_dim)
            else:
                emb = torch.zeros(B, self.cat_embedding_dim)
            cat_embeddings_list.append(emb)
        cat_tensor = torch.cat(cat_embeddings_list, dim=1) if cat_embeddings_list else torch.zeros(B, 0)

        # ── 拼接 ──
        out = torch.cat([numeric_tensor, cat_tensor], dim=1)
        return out.detach()

    # ------------------------------------------------------------------
    # 便捷方法: 从 Brochure / User 对象提取特征
    # ------------------------------------------------------------------
    @staticmethod
    def extract_features_from_models(
        user: Any,
        brochures: Optional[List[Any]] = None,
    ) -> Dict[str, Any]:
        """从 AI数智名片 数据模型对象提取企业特征 dict。

        Args:
            user: User 对象 (有 company 字段)
            brochures: Brochure 对象列表 (有 purpose, pages_count, view_count, visibility 等字段)

        Returns:
            feature dict, 可直接传给 .transform()
        """
        brochures = brochures or []

        brochure_count = len(brochures)
        total_view_count = 0
        total_pages = 0
        ai_summary_pages = 0
        purposes: set = set()
        visibility = "public"
        purpose = ""

        for b in brochures:
            total_view_count += getattr(b, "view_count", 0) or 0
            pages_count = getattr(b, "pages_count", 0) or 1
            total_pages += pages_count
            b_purpose = str(getattr(b, "purpose", "") or "")
            if b_purpose:
                purposes.add(b_purpose)
            b_visibility = str(getattr(b, "visibility", "public") or "public")
            # 取最小可见性 (最严格的那个)
            vis_order = {"public": 0, "platform": 1, "network": 2, "private": 3}
            if vis_order.get(b_visibility, 0) > vis_order.get(visibility, 0):
                visibility = b_visibility

            # AI 摘要统计
            pages = getattr(b, "pages", [])
            for page in pages:
                summary = getattr(page, "ai_summary", "") or ""
                if summary:
                    ai_summary_pages += 1

        if brochures:
            purpose = str(getattr(brochures[0], "purpose", "") or "")

        avg_pages = total_pages / max(brochure_count, 1)
        diversity = len(purposes)
        company_name = getattr(user, "company", "") or ""
        company_name_len = len(company_name)

        return {
            "brochure_count": brochure_count,
            "avg_pages_per_brochure": avg_pages,
            "total_view_count": total_view_count,
            "brochure_diversity": diversity,
            "company_name_len": company_name_len,
            "pages_with_ai_summary": ai_summary_pages,
            "purpose": purpose,
            "visibility": visibility,
        }

    # ------------------------------------------------------------------
    # 内部辅助
    # ------------------------------------------------------------------
    @staticmethod
    def _to_rows(
        enterprise_data: Union[Dict, List[Dict], "Any"],
    ) -> List[Dict[str, Any]]:
        """统一输入为 list[dict]"""
        if isinstance(enterprise_data, dict):
            return [enterprise_data]
        if isinstance(enterprise_data, list):
            return enterprise_data
        try:
            import pandas as pd

            if isinstance(enterprise_data, pd.DataFrame):
                return enterprise_data.to_dict(orient="records")
        except ImportError:
            pass
        raise TypeError(
            f"不支持的输入类型: {type(enterprise_data).__name__}, "
            f"期望 dict / list[dict] / pd.DataFrame"
        )

    @property
    def total_feature_dim(self) -> int:
        """编码后的特征总维度"""
        num_n = len(self.numeric_features)
        num_c = len(self.categorical_features)
        return num_n + num_c * self.cat_embedding_dim

    def __repr__(self) -> str:
        status = "fitted" if self._fitted else "not fitted"
        return (
            f"EnterpriseFeatureEncoder("
            f"num_numeric={len(self.numeric_features)}, "
            f"num_categorical={len(self.categorical_features)}, "
            f"cat_embedding_dim={self.cat_embedding_dim}, "
            f"total_dim={self.total_feature_dim}, "
            f"status={status})"
        )
