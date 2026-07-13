"""
AI数智名片 — 在线推理 API 服务 (InferenceService)

提供三塔匹配模型的异步推理接口，支持:
  - predict(user_id, candidate_ids)       — 批量预测用户与候选列表的匹配分数
  - predict_pair(user_a_id, user_b_id)   — 单对用户匹配评分
  - get_embedding(user_id)               — 获取用户的特征嵌入 (模型中间层)
  - get_model_info()                     — 模型元数据查询

架构:
  1. 加载已训练的 ThreeTowerModel + StandardScaler 参数
  2. 连接 AI数智名片 SQLite 数据库 (digital_brochure.db)
  3. 在线计算三塔特征:
     - Tower 1: 标签重叠特征 (tag_overlap_score, common_tag_count, ...)
     - Tower 2: 语义相似度 (基于用户文本的 cosine similarity)
     - Tower 3: 标签权重特征 (tag_count, avg_weight, ...)
  4. 标准化后送入模型 → 输出 [0,1] 匹配分数
  5. 模型文件不存在时自动降级为常数评分

用法:
    service = InferenceService()
    await service.initialize()
    results = await service.predict(user_id=1, candidate_ids=[2, 3, 5])
"""

from __future__ import annotations

import json
import logging
import math
import pickle
import sqlite3
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Tuple, Union

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
# 路径常量
# ---------------------------------------------------------------------------
_BASE_DIR = Path(__file__).resolve().parent.parent.parent  # backend/
_DEFAULT_MODEL_PATH = _BASE_DIR / "models" / "matching_model.pt"
_DEFAULT_SCALER_PATH = _BASE_DIR / "models" / "matching_scalers.npy"
_DEFAULT_DB_PATH = _BASE_DIR / "data" / "digital_brochure.db"

# ---------------------------------------------------------------------------
# 三塔特征定义 (与 train_matching_model.py 一致)
# ---------------------------------------------------------------------------
OVERLAP_FEATURES = [
    "tag_overlap_score",
    "common_tag_count",
    "overlap_provide_to_need",
    "overlap_need_to_provide",
]
SEMANTIC_FEATURES = ["vector_semantic"]
WEIGHT_FEATURES = [
    "tag_count_a",
    "tag_count_b",
    "avg_weight_a",
    "avg_weight_b",
    "tag_weight_score",
]
ALL_FEATURES = OVERLAP_FEATURES + SEMANTIC_FEATURES + WEIGHT_FEATURES

# ---------------------------------------------------------------------------
# 数据模型
# ---------------------------------------------------------------------------
@dataclass
class MatchScore:
    """单条匹配结果"""

    user_id: int
    candidate_id: int
    score: float
    details: Dict[str, float] = field(default_factory=dict)


@dataclass
class UserData:
    """用户数据库原始数据快照"""

    user_id: int
    name: str = ""
    company: str = ""
    title: str = ""
    intro: str = ""
    # tag_type → {tag: weight}
    provide_tags: Dict[str, float] = field(default_factory=dict)
    need_tags: Dict[str, float] = field(default_factory=dict)
    brochure_text: str = ""


# ===================================================================
# 三塔模型 (PyTorch nn.Module)
# 与 scripts/train_matching_model.py 中的 ThreeTowerModel 结构一致
# ===================================================================
class ThreeTowerModel(nn.Module):
    """三塔匹配模型。

    Tower 1: 标签重叠特征 (4 → 8 → 4)
    Tower 2: 语义相似度特征 (1 → 4 → 2)
    Tower 3: 标签权重特征   (5 → 8 → 4)
    合并: Concat[4+2+4=10] → 8 → 1 + Sigmoid
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

    def forward(
        self,
        x_overlap: torch.Tensor,
        x_semantic: torch.Tensor,
        x_weight: torch.Tensor,
    ) -> torch.Tensor:
        """前向传播 → (B,) 匹配分数 [0, 1]。

        Args:
            x_overlap:  (B, 4)  标签重叠特征
            x_semantic: (B, 1)  语义相似度特征
            x_weight:   (B, 5)  标签权重特征

        Returns:
            (B,) float 张量, 范围 [0, 1]
        """
        out1 = self.tower_overlap(x_overlap)
        out2 = self.tower_semantic(x_semantic)
        out3 = self.tower_weight(x_weight)
        combined = torch.cat([out1, out2, out3], dim=1)
        return self.combined(combined).squeeze(1)

    @torch.no_grad()
    def predict(
        self,
        x_overlap: np.ndarray,
        x_semantic: np.ndarray,
        x_weight: np.ndarray,
    ) -> np.ndarray:
        """推理接口, 接受 numpy 输入, 返回 numpy 分数。

        Args:
            x_overlap:  (B, 4)  numpy 数组
            x_semantic: (B, 1)  numpy 数组
            x_weight:   (B, 5)  numpy 数组

        Returns:
            (B,) numpy 数组, 范围 [0, 1]
        """
        self.eval()
        device = next(self.parameters()).device
        t_o = torch.FloatTensor(x_overlap).to(device)
        t_s = torch.FloatTensor(x_semantic).to(device)
        t_w = torch.FloatTensor(x_weight).to(device)
        out = self.forward(t_o, t_s, t_w)
        return out.cpu().numpy()


# ===================================================================
# 数据库访问 (SQLite 同步包装为异步)
# ===================================================================
class UserDataLoader:
    """从 SQLite 数据库加载用户数据。

    逐用户缓存数据，避免重复查询。
    """

    def __init__(self, db_path: Union[str, Path] = _DEFAULT_DB_PATH):
        self.db_path = Path(db_path)
        self._cache: Dict[int, UserData] = {}
        self._all_user_ids: Optional[List[int]] = None

    def _get_conn(self) -> sqlite3.Connection:
        """获取数据库连接 (同步, 由 async run_in_executor 包装)"""
        if not self.db_path.exists():
            logger.warning("数据库文件不存在: %s, 使用空数据", self.db_path)
            # 返回内存数据库, 保证不崩溃
            conn = sqlite3.connect(":memory:")
            conn.row_factory = sqlite3.Row
            return conn
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        return conn

    def _load_user_sync(self, user_id: int) -> Optional[UserData]:
        """同步加载单个用户数据"""
        if user_id in self._cache:
            return self._cache[user_id]

        conn = self._get_conn()
        try:
            # 用户基本信息
            cur = conn.execute(
                "SELECT id, name, company, title, intro FROM users WHERE id = ?",
                (user_id,),
            )
            row = cur.fetchone()
            if row is None:
                logger.warning("用户 %d 不存在", user_id)
                return None

            user = UserData(
                user_id=row["id"],
                name=row["name"] or "",
                company=row["company"] or "",
                title=row["title"] or "",
                intro=row["intro"] or "",
            )

            # 用户标签
            cur = conn.execute(
                "SELECT tag_type, tag, weight FROM user_tags WHERE user_id = ?",
                (user_id,),
            )
            for tag_row in cur.fetchall():
                ttype = tag_row["tag_type"]
                tag_name = tag_row["tag"]
                weight = tag_row["weight"] or 1.0
                if ttype == "provide":
                    user.provide_tags[tag_name] = weight
                elif ttype == "need":
                    user.need_tags[tag_name] = weight

            # Brochure 文本
            text_parts = []
            cur = conn.execute(
                "SELECT title FROM brochures WHERE user_id = ? AND status = 'published'",
                (user_id,),
            )
            for br_row in cur.fetchall():
                if br_row["title"]:
                    text_parts.append(br_row["title"])

            # Pages AI summary
            cur = conn.execute(
                """SELECT p.ai_summary
                   FROM pages p
                   JOIN brochures b ON p.brochure_id = b.id
                   WHERE b.user_id = ? AND p.ai_summary != '' AND p.ai_summary IS NOT NULL""",
                (user_id,),
            )
            for p_row in cur.fetchall():
                if p_row["ai_summary"]:
                    text_parts.append(p_row["ai_summary"])

            user.brochure_text = " ".join(text_parts)

            self._cache[user_id] = user
            return user
        finally:
            conn.close()

    def _load_all_user_ids_sync(self) -> List[int]:
        """同步加载所有用户 ID"""
        if self._all_user_ids is not None:
            return self._all_user_ids

        conn = self._get_conn()
        try:
            cur = conn.execute(
                "SELECT id FROM users WHERE name != '' AND name NOT IN ('final', 'done', 'fixtester') ORDER BY id"
            )
            ids = [r["id"] for r in cur.fetchall()]
            self._all_user_ids = ids
            return ids
        finally:
            conn.close()

    async def load_user(self, user_id: int) -> Optional[UserData]:
        """异步加载用户数据"""
        import asyncio

        return await asyncio.get_event_loop().run_in_executor(
            None, self._load_user_sync, user_id
        )

    async def load_all_user_ids(self) -> List[int]:
        """异步加载所有用户 ID"""
        import asyncio

        return await asyncio.get_event_loop().run_in_executor(
            None, self._load_all_user_ids_sync
        )


# ===================================================================
# 特征计算
# ===================================================================
def build_user_document(user: UserData) -> str:
    """构建用户的文本文档 (用于语义相似度)。

    拼接: intro + company + title + 标签文本 + brochure 文本
    """
    parts = []
    if user.intro:
        parts.append(user.intro)
    if user.company:
        parts.append(user.company)
    if user.title:
        parts.append(user.title)
    for tag, _ in user.provide_tags.items():
        parts.append(f"提供{tag}")
    for tag, _ in user.need_tags.items():
        parts.append(f"需要{tag}")
    if user.brochure_text:
        parts.append(user.brochure_text)
    return " ".join(parts)


def compute_tag_overlap_features(
    provide_a: Dict[str, float],
    need_b: Dict[str, float],
    provide_b: Dict[str, float],
    need_a: Dict[str, float],
) -> Dict[str, float]:
    """Tower 1: 计算标签重叠特征。"""
    # A提供 ∩ B需要
    overlap_p2n = sum(
        provide_a.get(t, 0.0) * w for t, w in need_b.items() if t in provide_a
    )
    # A需要 ∩ B提供
    overlap_n2p = sum(
        provide_b.get(t, 0.0) * w for t, w in need_a.items() if t in provide_b
    )

    common_p2n = len(set(provide_a.keys()) & set(need_b.keys()))
    common_n2p = len(set(provide_b.keys()) & set(need_a.keys()))
    common_tag_count = common_p2n + common_n2p

    total_provide_a = sum(provide_a.values()) or 1.0
    total_need_b = sum(need_b.values()) or 1.0
    total_provide_b = sum(provide_b.values()) or 1.0
    total_need_a = sum(need_a.values()) or 1.0

    tag_overlap_score = (
        overlap_p2n / (total_provide_a * total_need_b) ** 0.5
        + overlap_n2p / (total_provide_b * total_need_a) ** 0.5
    ) / 2.0

    return {
        "tag_overlap_score": min(tag_overlap_score, 1.0),
        "common_tag_count": float(common_tag_count),
        "overlap_provide_to_need": overlap_p2n,
        "overlap_need_to_provide": overlap_n2p,
    }


def compute_semantic_similarity(
    doc_a: str,
    doc_b: str,
    tfidf_vectorizer: Optional[Any] = None,
) -> float:
    """Tower 2: 计算文本语义相似度。

    使用 TF-IDF + 余弦相似度。如果没有 vectorizer, 降级为 Jaccard 相似度。
    """
    if not doc_a or not doc_b:
        return 0.0

    if tfidf_vectorizer is not None:
        try:
            vecs = tfidf_vectorizer.transform([doc_a, doc_b])
            from sklearn.metrics.pairwise import cosine_similarity

            sim = cosine_similarity(vecs[0:1], vecs[1:2])[0][0]
            return max(0.0, min(1.0, float(sim)))
        except Exception:
            pass

    # 降级: 词集 Jaccard 相似度
    words_a = set(doc_a.split())
    words_b = set(doc_b.split())
    if not words_a or not words_b:
        return 0.0
    intersection = words_a & words_b
    union = words_a | words_b
    return len(intersection) / len(union)


def compute_weight_features(
    user_a: UserData,
    user_b: UserData,
) -> Dict[str, float]:
    """Tower 3: 计算标签权重特征。"""
    tag_count_a = len(user_a.provide_tags) + len(user_a.need_tags)
    tag_count_b = len(user_b.provide_tags) + len(user_b.need_tags)

    avg_weight_a = (
        sum(user_a.provide_tags.values()) / max(len(user_a.provide_tags), 1)
        + sum(user_a.need_tags.values()) / max(len(user_a.need_tags), 1)
    ) / 2.0 if (user_a.provide_tags or user_a.need_tags) else 1.0

    avg_weight_b = (
        sum(user_b.provide_tags.values()) / max(len(user_b.provide_tags), 1)
        + sum(user_b.need_tags.values()) / max(len(user_b.need_tags), 1)
    ) / 2.0 if (user_b.provide_tags or user_b.need_tags) else 1.0

    # 标签重量评分: 共同标签的权重乘积和
    common_provide = set(user_a.provide_tags.keys()) & set(user_b.need_tags.keys())
    common_need = set(user_a.need_tags.keys()) & set(user_b.provide_tags.keys())
    weight_score = 0.0
    for t in common_provide:
        weight_score += user_a.provide_tags.get(t, 0.0) * user_b.need_tags.get(t, 0.0)
    for t in common_need:
        weight_score += user_a.need_tags.get(t, 0.0) * user_b.provide_tags.get(t, 0.0)
    # 归一化
    max_possible = len(common_provide | common_need) * 1.0 * 1.0
    tag_weight_score = weight_score / max_possible if max_possible > 0 else 0.0

    return {
        "tag_count_a": float(tag_count_a),
        "tag_count_b": float(tag_count_b),
        "avg_weight_a": avg_weight_a,
        "avg_weight_b": avg_weight_b,
        "tag_weight_score": min(tag_weight_score, 1.0),
    }


def compute_all_features(
    user_a: UserData,
    user_b: UserData,
    tfidf_vectorizer: Optional[Any] = None,
) -> Dict[str, float]:
    """计算用户对的三塔全量特征。"""
    features = {}

    # Tower 1: 标签重叠
    overlap = compute_tag_overlap_features(
        user_a.provide_tags, user_b.need_tags,
        user_b.provide_tags, user_a.need_tags,
    )
    features.update(overlap)

    # Tower 2: 语义相似度
    doc_a = build_user_document(user_a)
    doc_b = build_user_document(user_b)
    features["vector_semantic"] = compute_semantic_similarity(
        doc_a, doc_b, tfidf_vectorizer
    )

    # Tower 3: 标签权重
    weight = compute_weight_features(user_a, user_b)
    features.update(weight)

    return features


# ===================================================================
# 标准化的三塔特征验证
# ===================================================================
def validate_feature_dict(features: Dict[str, float]) -> bool:
    """验证特征字典包含所有必需字段且值合法。"""
    for name in ALL_FEATURES:
        if name not in features:
            logger.warning("缺少特征: %s", name)
            return False
    return True


# ===================================================================
# InferenceService — 主推理服务
# ===================================================================
class InferenceService:
    """在线推理 API 服务 — 三塔匹配模型。

    用法:
        svc = InferenceService()
        await svc.initialize()
        results = await svc.predict(user_id=1, candidate_ids=[2, 3, 5])
        pair_score = await svc.predict_pair(1, 2)
        emb = await svc.get_embedding(1)
        info = svc.get_model_info()

    降级模式:
        如果模型文件不存在, 服务启动时记录警告, 所有预测返回常数 0.5。
    """

    def __init__(
        self,
        model_path: Union[str, Path] = _DEFAULT_MODEL_PATH,
        scaler_path: Union[str, Path] = _DEFAULT_SCALER_PATH,
        db_path: Union[str, Path] = _DEFAULT_DB_PATH,
    ):
        self.model_path = Path(model_path)
        self.scaler_path = Path(scaler_path)
        self.db_path = Path(db_path)

        # ── 内部状态 (initialize 后可用) ──
        self._model: Optional[ThreeTowerModel] = None
        self._scalers: Optional[Dict[str, Any]] = None
        self._device: str = "cpu"
        self._initialized: bool = False
        self._degraded: bool = False  # True = 模型未加载, 使用常量评分
        self._data_loader: Optional[UserDataLoader] = None
        self._tfidf_vectorizer: Optional[Any] = None
        self._user_cache: Dict[int, UserData] = {}

        # 模型元数据
        self._model_metadata: Dict[str, Any] = {
            "model_type": "ThreeTowerModel",
            "version": "1.0.0",
            "features": {
                "overlap": OVERLAP_FEATURES,
                "semantic": SEMANTIC_FEATURES,
                "weight": WEIGHT_FEATURES,
            },
            "device": "cpu",
            "degraded": True,
            "initialized": False,
        }

    # ------------------------------------------------------------------
    # initialize
    # ------------------------------------------------------------------
    async def initialize(self) -> None:
        """异步初始化: 加载模型、scalers、数据加载器。

        如果模型文件不存在, 自动进入降级模式 (返回常数 0.5)。
        """
        logger.info("[InferenceService] 开始初始化...")

        # 1. 初始化数据加载器
        self._data_loader = UserDataLoader(db_path=self.db_path)

        # 2. 尝试加载 TF-IDF vectorizer (如果存在)
        self._load_tfidf_vectorizer()

        # 3. 加载模型
        self._model, self._scalers = await self._load_model_async()

        # 4. 更新状态
        self._initialized = True
        self._model_metadata["initialized"] = True
        self._model_metadata["degraded"] = self._degraded

        if self._degraded:
            logger.warning(
                "[InferenceService] 模型未加载, 进入降级模式 — 所有预测返回常数 0.5"
            )
        else:
            logger.info(
                "[InferenceService] 初始化完成, 设备=%s, scalers=%s",
                self._device,
                "loaded" if self._scalers else "none",
            )

    def _load_tfidf_vectorizer(self) -> None:
        """尝试加载 TF-IDF vectorizer (保存的训练数据中的)。"""
        vectorizer_path = self.model_path.parent / "tfidf_vectorizer.pkl"
        if vectorizer_path.exists():
            try:
                with open(vectorizer_path, "rb") as f:
                    self._tfidf_vectorizer = pickle.load(f)
                logger.info("[InferenceService] TF-IDF vectorizer 已加载")
            except Exception as e:
                logger.warning("[InferenceService] TF-IDF vectorizer 加载失败: %s", e)
        else:
            logger.info("[InferenceService] 无 TF-IDF vectorizer 文件, 使用 Jaccard 降级")

    async def _load_model_async(
        self,
    ) -> Tuple[Optional[ThreeTowerModel], Optional[Dict[str, Any]]]:
        """异步加载模型和 scalers。"""
        import asyncio

        return await asyncio.get_event_loop().run_in_executor(
            None, self._load_model_sync
        )

    def _load_model_sync(
        self,
    ) -> Tuple[Optional[ThreeTowerModel], Optional[Dict[str, Any]]]:
        """同步加载模型和 scalers (在 executor 中运行)。"""
        # ── 检查模型文件 ──
        if not self.model_path.exists():
            logger.warning("模型文件不存在: %s, 启用降级模式", self.model_path)
            self._degraded = True
            return None, None

        if not TORCH_AVAILABLE:
            logger.warning("PyTorch 不可用, 启用降级模式")
            self._degraded = True
            return None, None

        try:
            # ── 加载 scalers ──
            scalers = None
            if self.scaler_path.exists():
                scaler_data = np.load(
                    str(self.scaler_path), allow_pickle=True
                ).item()
                from sklearn.preprocessing import StandardScaler

                scalers = {
                    "overlap": StandardScaler(),
                    "semantic": StandardScaler(),
                    "weight": StandardScaler(),
                }
                scalers["overlap"].mean_ = np.array(
                    scaler_data.get("overlap_mean", [0.0] * len(OVERLAP_FEATURES))
                )
                scalers["overlap"].scale_ = np.array(
                    scaler_data.get("overlap_scale", [1.0] * len(OVERLAP_FEATURES))
                )
                scalers["semantic"].mean_ = np.array(
                    scaler_data.get("semantic_mean", [0.0])
                )
                scalers["semantic"].scale_ = np.array(
                    scaler_data.get("semantic_scale", [1.0])
                )
                scalers["weight"].mean_ = np.array(
                    scaler_data.get("weight_mean", [0.0] * len(WEIGHT_FEATURES))
                )
                scalers["weight"].scale_ = np.array(
                    scaler_data.get("weight_scale", [1.0] * len(WEIGHT_FEATURES))
                )
                logger.info("[InferenceService] Scalers 已加载")
            else:
                logger.warning("Scaler 文件不存在: %s", self.scaler_path)

            # ── 加载模型 ──
            checkpoint = torch.load(
                str(self.model_path), map_location="cpu", weights_only=True
            )
            model = ThreeTowerModel()
            model.load_state_dict(checkpoint["model_state_dict"])
            model.eval()

            # ── 更新元数据 ──
            metrics = checkpoint.get("metrics", {})
            self._model_metadata["training_metrics"] = metrics
            self._model_metadata["checkpoint_features"] = checkpoint.get(
                "feature_names", []
            )

            self._device = "cuda" if torch.cuda.is_available() else "cpu"
            model = model.to(self._device)
            self._model_metadata["device"] = self._device
            self._degraded = False

            logger.info("[InferenceService] 模型已加载: %s", self.model_path)
            return model, scalers

        except Exception as e:
            logger.error("[InferenceService] 模型加载失败: %s", e)
            self._degraded = True
            return None, None

    # ------------------------------------------------------------------
    # predict — 批量预测
    # ------------------------------------------------------------------
    async def predict(
        self,
        user_id: int,
        candidate_ids: List[int],
        top_k: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """对用户与候选列表进行批量匹配预测。

        Args:
            user_id:        目标用户 ID
            candidate_ids:  候选用户 ID 列表
            top_k:          返回前 K 个结果 (默认返回全部)

        Returns:
            list[dict]:
                [{
                    "user_id": int,
                    "candidate_id": int,
                    "score": float,
                    "features": {...}
                }, ...]
                按 score 降序排列
        """
        if not self._initialized:
            raise RuntimeError("InferenceService 尚未初始化, 请先调用 await initialize()")

        if not candidate_ids:
            return []

        # ── 降级模式 (先于数据库加载检查, 避免空数据库崩溃) ──
        if self._degraded or self._model is None:
            return self._degraded_predict(user_id, candidate_ids, top_k)

        # ── 加载用户数据 ──
        user_a = await self._data_loader.load_user(user_id) if self._data_loader else None
        if user_a is None:
            logger.warning("用户 %d 不存在, 返回空结果", user_id)
            return []

        # ── 批量计算特征 ──
        results: List[MatchScore] = []
        for cand_id in candidate_ids:
            user_b = await self._data_loader.load_user(cand_id) if self._data_loader else None
            if user_b is None:
                continue

            score = self._score_pair_internal(user_a, user_b)
            results.append(
                MatchScore(
                    user_id=user_id,
                    candidate_id=cand_id,
                    score=score["score"],
                    details=score.get("details", {}),
                )
            )

        # ── 排序 ──
        results.sort(key=lambda r: r.score, reverse=True)

        if top_k is not None and top_k > 0:
            results = results[:top_k]

        return [
            {
                "user_id": r.user_id,
                "candidate_id": r.candidate_id,
                "score": r.score,
                "features": r.details,
            }
            for r in results
        ]

    def _score_pair_internal(
        self,
        user_a: UserData,
        user_b: UserData,
    ) -> Dict[str, Any]:
        """内部: 计算单对用户的匹配分数 (不涉及数据库 I/O)。"""
        # 1. 计算特征
        features = compute_all_features(user_a, user_b, self._tfidf_vectorizer)
        if not validate_feature_dict(features):
            return {"score": 0.5, "details": features}

        # 2. 提取三塔特征
        X_o = np.array([[features[f] for f in OVERLAP_FEATURES]], dtype=np.float32)
        X_s = np.array([[features[f] for f in SEMANTIC_FEATURES]], dtype=np.float32)
        X_w = np.array([[features[f] for f in WEIGHT_FEATURES]], dtype=np.float32)

        # 3. 标准化
        if self._scalers:
            X_o = self._scalers["overlap"].transform(X_o)
            X_s = self._scalers["semantic"].transform(X_s)
            X_w = self._scalers["weight"].transform(X_w)

        # 4. 模型推理
        try:
            score_arr = self._model.predict(X_o, X_s, X_w)
            score = float(score_arr[0])
            score = max(0.0, min(1.0, score))
        except Exception as e:
            logger.error("模型推理失败: %s, 使用降级分数", e)
            score = 0.5

        return {"score": score, "details": features}

    def _degraded_predict(
        self,
        user_id: int,
        candidate_ids: List[int],
        top_k: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """降级模式: 返回常数分数 (0.5) 加简单特征。"""
        results = [
            {
                "user_id": user_id,
                "candidate_id": cid,
                "score": 0.5,
                "features": {
                    "tag_overlap_score": 0.0,
                    "common_tag_count": 0.0,
                    "overlap_provide_to_need": 0.0,
                    "overlap_need_to_provide": 0.0,
                    "vector_semantic": 0.0,
                    "tag_count_a": 0.0,
                    "tag_count_b": 0.0,
                    "avg_weight_a": 0.0,
                    "avg_weight_b": 0.0,
                    "tag_weight_score": 0.0,
                },
            }
            for cid in candidate_ids
        ]
        if top_k is not None and top_k > 0:
            results = results[:top_k]
        return results

    # ------------------------------------------------------------------
    # predict_pair — 单对评分
    # ------------------------------------------------------------------
    async def predict_pair(self, user_a_id: int, user_b_id: int) -> float:
        """计算两个用户之间的匹配分数。

        Args:
            user_a_id: 用户 A ID
            user_b_id: 用户 B ID

        Returns:
            float: [0, 1] 范围的匹配分数
        """
        if not self._initialized:
            raise RuntimeError("InferenceService 尚未初始化, 请先调用 await initialize()")

        # ── 降级模式 (先于数据库加载检查) ──
        if self._degraded or self._model is None:
            return 0.5

        # ── 加载数据 ──
        user_a = await self._data_loader.load_user(user_a_id) if self._data_loader else None
        user_b = await self._data_loader.load_user(user_b_id) if self._data_loader else None

        if user_a is None or user_b is None:
            logger.warning(
                "用户不存在: a=%d, b=%d", user_a_id, user_b_id
            )
            return 0.5

        result = self._score_pair_internal(user_a, user_b)
        return result["score"]

    # ------------------------------------------------------------------
    # get_embedding — 获取用户嵌入
    # ------------------------------------------------------------------
    async def get_embedding(self, user_id: int) -> List[float]:
        """获取用户的特征嵌入向量。

        注意: ThreeTowerModel 是评分模型, 没有直接的 user embedding.
        此处返回用户特征的中间表示 (tower 输出拼接), 作为用户画像向量。

        Args:
            user_id: 用户 ID

        Returns:
            list[float]: 10 维嵌入向量 (4+2+4 三塔输出拼接)
        """
        if not self._initialized:
            raise RuntimeError("InferenceService 尚未初始化, 请先调用 await initialize()")

        # ── 降级模式 (先于数据库加载检查, 返回默认零向量) ──
        if self._degraded or self._model is None:
            return [0.0] * 10

        user = await self._data_loader.load_user(user_id) if self._data_loader else None
        if user is None:
            logger.warning("用户 %d 不存在, 返回零向量", user_id)
            return [0.0] * 10

        # 需要另一个用户来计算特征 — 这里用自身作为参照
        features = compute_all_features(user, user, self._tfidf_vectorizer)

        X_o = np.array([[features[f] for f in OVERLAP_FEATURES]], dtype=np.float32)
        X_s = np.array([[features[f] for f in SEMANTIC_FEATURES]], dtype=np.float32)
        X_w = np.array([[features[f] for f in WEIGHT_FEATURES]], dtype=np.float32)

        if self._scalers:
            X_o = self._scalers["overlap"].transform(X_o)
            X_s = self._scalers["semantic"].transform(X_s)
            X_w = self._scalers["weight"].transform(X_w)

        try:
            self._model.eval()
            device = next(self._model.parameters()).device
            with torch.no_grad():
                t_o = torch.FloatTensor(X_o).to(device)
                t_s = torch.FloatTensor(X_s).to(device)
                t_w = torch.FloatTensor(X_w).to(device)
                emb1 = self._model.tower_overlap(t_o).cpu().numpy().flatten().tolist()  # 4d
                emb2 = self._model.tower_semantic(t_s).cpu().numpy().flatten().tolist()  # 2d
                emb3 = self._model.tower_weight(t_w).cpu().numpy().flatten().tolist()  # 4d
            return emb1 + emb2 + emb3
        except Exception as e:
            logger.error("嵌入计算失败: %s", e)
            return [0.0] * 10

    def _compute_degraded_embedding(self, user: UserData) -> List[float]:
        """降级模式: 基于标签统计计算简单的用户画像向量。"""
        # [tag_count, provide_count, need_count, avg_weight, ..., (pad to 10)]
        emb = [
            float(len(user.provide_tags) + len(user.need_tags)),
            float(len(user.provide_tags)),
            float(len(user.need_tags)),
            float(
                sum(user.provide_tags.values()) / max(len(user.provide_tags), 1)
                if user.provide_tags
                else 0.0
            ),
            float(
                sum(user.need_tags.values()) / max(len(user.need_tags), 1)
                if user.need_tags
                else 0.0
            ),
        ]
        # 补零到 10 维
        while len(emb) < 10:
            emb.append(0.0)
        return emb[:10]

    # ------------------------------------------------------------------
    # get_model_info — 模型元数据
    # ------------------------------------------------------------------
    def get_model_info(self) -> Dict[str, Any]:
        """获取模型元数据。

        Returns:
            dict: {
                "model_type": str,
                "version": str,
                "initialized": bool,
                "degraded": bool,
                "device": str,
                "features": {...},
                "training_metrics": {...} | None,
            }
        """
        return dict(self._model_metadata)

    # ------------------------------------------------------------------
    # 生命周期管理
    # ------------------------------------------------------------------
    async def close(self) -> None:
        """释放资源。"""
        self._model = None
        self._scalers = None
        self._data_loader = None
        self._user_cache.clear()
        self._initialized = False
        self._degraded = True
        self._model_metadata["initialized"] = False
        self._model_metadata["degraded"] = True
        logger.info("[InferenceService] 资源已释放")

    async def __aenter__(self) -> "InferenceService":
        await self.initialize()
        return self

    async def __aexit__(self, *args: Any) -> None:
        await self.close()
