"""AI 销售预测服务 — 基于历史成交数据的赢单率预测。

使用纯 numpy 实现的逻辑回归（Logistic Regression）：
  - 无外部 ML 依赖（不引入 scikit-learn）
  - 梯度下降训练
  - 特征: 联系人类别/来源/标签数/活动数/跟进时长/金额/管道阶段概率

模型状态（权重 + 偏差）持久化到 JSON 文件，重启不丢失。
"""

from __future__ import annotations

import json
import logging
import math
import os
import random
from pathlib import Path
from typing import Any

import numpy as np

logger = logging.getLogger(__name__)

# ── 模型文件路径 ──────────────────────────────────────────────────────────────────
MODEL_DIR = Path(os.path.dirname(os.path.abspath(__file__))) / ".." / ".." / "data"
MODEL_FILE = MODEL_DIR / "sales_prediction_model.json"

# ── 超参数 ────────────────────────────────────────────────────────────────────────
LEARNING_RATE = 0.01
EPOCHS = 500
BATCH_SIZE = 32
L2_LAMBDA = 0.01  # L2 正则化强度

# ── 特征定义 ──────────────────────────────────────────────────────────────────────
SOURCE_CATEGORIES = ["match", "manual", "visitor", "import"]
NUM_FEATURES = len(SOURCE_CATEGORIES) + 5  # source_onehot(4) + tag_count + activity_count + follow_up_days + deal_value_scaled + stage_win_prob


# ═══════════════════════════════════════════════════════════════════════════════════
# 数据准备
# ═══════════════════════════════════════════════════════════════════════════════════


def _encode_source(source: str | None) -> list[float]:
    """将来源编码为 one-hot 向量。"""
    vec = [0.0] * len(SOURCE_CATEGORIES)
    if source and source in SOURCE_CATEGORIES:
        idx = SOURCE_CATEGORIES.index(source)
        vec[idx] = 1.0
    return vec


def _parse_tags(tags_json: str) -> list[str]:
    """解析 tags JSON 字段。"""
    if not tags_json or tags_json == "[]":
        return []
    try:
        return json.loads(tags_json)
    except (json.JSONDecodeError, TypeError):
        return []


def _compute_follow_up_days(
    last_contacted_at: Any | None,
    created_at: Any | None,
) -> float:
    """计算跟进时长（天数）。"""
    from datetime import datetime, timezone

    now = datetime.now(timezone.utc)
    ref_date = None

    if last_contacted_at:
        if isinstance(last_contacted_at, datetime):
            ref_date = last_contacted_at
        elif isinstance(last_contacted_at, str):
            try:
                ref_date = datetime.fromisoformat(last_contacted_at)
            except ValueError:
                pass

    if ref_date is None and created_at:
        if isinstance(created_at, datetime):
            ref_date = created_at
        elif isinstance(created_at, str):
            try:
                ref_date = datetime.fromisoformat(created_at)
            except ValueError:
                pass

    if ref_date is None:
        return 0.0

    # 处理 naive datetime
    if ref_date.tzinfo is None:
        ref_date = ref_date.replace(tzinfo=timezone.utc)

    delta = now - ref_date
    return max(0.0, delta.total_seconds() / 86400.0)


def _scale_value(value: float | None) -> float:
    """对数缩放金额，减少异常值影响。"""
    if value is None or value <= 0:
        return 0.0
    return math.log10(value + 1.0) / 6.0  # 归一化到 ~0-1


def extract_features(
    deal: dict,
    contact: dict | None,
    activity_count: int = 0,
    stage_win_prob: float = 0.0,
) -> np.ndarray:
    """从 deal + contact 数据提取特征向量。

    特征维度:
      - source_onehot(4): match/manual/visitor/import
      - tag_count(1): 标签数量
      - activity_count(1): 活动数量
      - follow_up_days(1): 跟进天数
      - deal_value_scaled(1): 对数缩放金额
      - stage_win_prob(1): 管道阶段默认赢单率
    """
    source = (contact or {}).get("source", "manual")
    tags_json = (contact or {}).get("tags", "[]")
    tags = _parse_tags(tags_json)
    tag_count = min(len(tags), 20) / 20.0  # 归一化到 0-1

    act_count = min(activity_count, 50) / 50.0  # 归一化到 0-1

    follow_up = _compute_follow_up_days(
        (contact or {}).get("last_contacted_at"),
        (contact or {}).get("created_at"),
    )
    follow_up_norm = min(follow_up, 365) / 365.0  # 归一化到 0-1

    value = deal.get("value", 0)
    value_norm = _scale_value(value)

    stage_prob = max(0.0, min(1.0, stage_win_prob / 100.0))

    one_hot = _encode_source(source)
    features = one_hot + [tag_count, act_count, follow_up_norm, value_norm, stage_prob]
    return np.array(features, dtype=np.float64)


# ═══════════════════════════════════════════════════════════════════════════════════
# 逻辑回归模型（纯 numpy）
# ═══════════════════════════════════════════════════════════════════════════════════


def _sigmoid(z: np.ndarray) -> np.ndarray:
    """Sigmoid 激活函数（数值稳定版）。"""
    # 对 z > 0 使用 1/(1+exp(-z)), 对 z <= 0 使用 exp(z)/(1+exp(z))
    # 避免 exp 溢出
    mask = z >= 0
    result = np.empty_like(z, dtype=np.float64)
    result[mask] = 1.0 / (1.0 + np.exp(-z[mask]))
    result[~mask] = np.exp(z[~mask]) / (1.0 + np.exp(z[~mask]))
    return result


class LogisticRegression:
    """纯 numpy 实现的逻辑回归分类器。"""

    def __init__(self, n_features: int = NUM_FEATURES):
        self.n_features = n_features
        self.weights: np.ndarray | None = None
        self.bias: float = 0.0
        self._trained = False
        self._train_samples = 0
        self._accuracy: float = 0.0

    def init_params(self, seed: int = 42) -> None:
        """Xavier 初始化权重。"""
        rng = np.random.RandomState(seed)
        limit = math.sqrt(6.0 / (self.n_features + 1))
        self.weights = rng.uniform(-limit, limit, size=self.n_features).astype(np.float64)
        self.bias = 0.0

    def predict_proba(self, X: np.ndarray) -> np.ndarray:
        """预测概率 (0~1)。"""
        if self.weights is None:
            raise ValueError("模型尚未训练，请先调用 train()")
        z = np.dot(X, self.weights) + self.bias
        return _sigmoid(z)

    def predict(self, X: np.ndarray, threshold: float = 0.5) -> np.ndarray:
        """预测类别 (0=丢失, 1=成交)。"""
        return (self.predict_proba(X) >= threshold).astype(np.int32)

    def compute_loss(
        self, X: np.ndarray, y: np.ndarray, reg: float = L2_LAMBDA
    ) -> float:
        """计算交叉熵损失 + L2 正则化。"""
        m = X.shape[0]
        probs = self.predict_proba(X)
        # 裁剪防止 log(0)
        probs = np.clip(probs, 1e-15, 1 - 1e-15)
        loss = -np.mean(y * np.log(probs) + (1 - y) * np.log(1 - probs))
        # L2 正则化
        if self.weights is not None:
            loss += (reg / (2 * m)) * np.sum(self.weights ** 2)
        return loss

    def train(
        self,
        X: np.ndarray,
        y: np.ndarray,
        lr: float = LEARNING_RATE,
        epochs: int = EPOCHS,
        batch_size: int = BATCH_SIZE,
        reg: float = L2_LAMBDA,
        verbose: bool = False,
    ) -> dict:
        """使用小批量梯度下降训练模型。

        Args:
            X: 特征矩阵 (n_samples, n_features)
            y: 标签向量 (n_samples,) — 0=丢失, 1=成交
            lr: 学习率
            epochs: 训练轮数
            batch_size: 小批量大小
            reg: L2 正则化系数
            verbose: 是否打印训练日志

        Returns:
            训练历史（每轮 loss）
        """
        m = X.shape[0]
        self._train_samples = m

        if self.weights is None:
            self.init_params()

        history = {"loss": []}
        best_loss = float("inf")
        best_weights = self.weights.copy()
        best_bias = self.bias

        for epoch in range(epochs):
            # 随机打乱
            indices = np.random.permutation(m)
            X_shuffled = X[indices]
            y_shuffled = y[indices]

            epoch_loss = 0.0
            n_batches = 0

            for start in range(0, m, batch_size):
                end = min(start + batch_size, m)
                X_batch = X_shuffled[start:end]
                y_batch = y_shuffled[start:end]

                # 前向传播
                z = np.dot(X_batch, self.weights) + self.bias
                probs = _sigmoid(z)

                # 梯度计算
                error = probs - y_batch  # (batch_size,)
                dw = (1.0 / X_batch.shape[0]) * np.dot(X_batch.T, error) + (reg / m) * self.weights
                db = (1.0 / X_batch.shape[0]) * np.sum(error)

                # 参数更新
                self.weights -= lr * dw
                self.bias -= lr * db

                batch_loss = self._batch_loss(X_batch, y_batch, reg)
                epoch_loss += batch_loss
                n_batches += 1

            avg_loss = epoch_loss / n_batches if n_batches > 0 else 0.0
            history["loss"].append(avg_loss)

            # 保存最佳模型
            if avg_loss < best_loss:
                best_loss = avg_loss
                best_weights = self.weights.copy()
                best_bias = self.bias

            if verbose and (epoch + 1) % 100 == 0:
                logger.info("Epoch %d/%d — loss: %.6f", epoch + 1, epochs, avg_loss)

        # 恢复最佳参数
        self.weights = best_weights
        self.bias = best_bias
        self._trained = True

        # 计算训练集准确率
        preds = self.predict(X)
        self._accuracy = float(np.mean(preds == y)) * 100.0

        if verbose:
            logger.info(
                "训练完成 — 样本数: %d, 最终 loss: %.6f, 准确率: %.2f%%",
                m, best_loss, self._accuracy,
            )

        history["final_loss"] = best_loss
        history["accuracy"] = self._accuracy
        return history

    def _batch_loss(self, X_batch: np.ndarray, y_batch: np.ndarray, reg: float) -> float:
        """计算小批量损失。"""
        probs = _sigmoid(np.dot(X_batch, self.weights) + self.bias)
        probs = np.clip(probs, 1e-15, 1 - 1e-15)
        loss = -np.mean(y_batch * np.log(probs) + (1 - y_batch) * np.log(1 - probs))
        loss += (reg / (2 * X_batch.shape[0])) * np.sum(self.weights ** 2)
        return loss

    def get_params(self) -> dict:
        """获取模型参数用于序列化。"""
        if self.weights is None:
            return {"trained": False}
        return {
            "trained": self._trained,
            "n_features": self.n_features,
            "weights": self.weights.tolist(),
            "bias": self.bias,
            "train_samples": self._train_samples,
            "accuracy": self._accuracy,
        }

    def load_params(self, data: dict) -> None:
        """从字典加载模型参数。"""
        self.n_features = data.get("n_features", NUM_FEATURES)
        self.weights = np.array(data.get("weights", []), dtype=np.float64)
        self.bias = data.get("bias", 0.0)
        self._trained = data.get("trained", False)
        self._train_samples = data.get("train_samples", 0)
        self._accuracy = data.get("accuracy", 0.0)

    @property
    def is_trained(self) -> bool:
        return self._trained and self.weights is not None

    @property
    def train_samples(self) -> int:
        return self._train_samples

    @property
    def accuracy(self) -> float:
        return self._accuracy


# ═══════════════════════════════════════════════════════════════════════════════════
# 置信度计算
# ═══════════════════════════════════════════════════════════════════════════════════


def get_confidence(probability: float, train_samples: int) -> str:
    """根据预测概率和训练样本数计算置信度。

    - 高(high): 概率极端(>0.8 或 <0.2) 且样本数 >= 20
    - 中(medium): 概率中等偏离或样本数较少
    - 低(low): 概率接近 0.5 或样本极少
    """
    if train_samples < 5:
        return "low"

    prob_mid = abs(probability - 0.5)
    if prob_mid > 0.3 and train_samples >= 20:
        return "high"
    elif prob_mid > 0.15 and train_samples >= 10:
        return "medium"
    else:
        return "low"


# ═══════════════════════════════════════════════════════════════════════════════════
# 预测服务
# ═══════════════════════════════════════════════════════════════════════════════════


class SalesPredictionService:
    """AI 销售预测服务。

    管理逻辑回归模型的训练、持久化、预测。
    """

    def __init__(self):
        self.model = LogisticRegression()
        self._load_model()

    # ── 模型持久化 ────────────────────────────────────────────────────────────────

    def _model_path(self) -> Path:
        MODEL_DIR.mkdir(parents=True, exist_ok=True)
        return MODEL_FILE

    def _save_model(self) -> None:
        """保存模型参数到 JSON 文件。"""
        path = self._model_path()
        data = self.model.get_params()
        try:
            with open(path, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            logger.info("销售预测模型已保存 (%s)", path)
        except Exception as e:
            logger.warning("保存模型失败: %s", e)

    def _load_model(self) -> None:
        """从 JSON 文件加载模型参数。"""
        path = self._model_path()
        if not path.exists():
            logger.info("无已保存的模型文件，将使用未训练模型")
            return
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            self.model.load_params(data)
            if self.model.is_trained:
                logger.info(
                    "已加载销售预测模型 (样本数: %d, 准确率: %.1f%%)",
                    self.model.train_samples,
                    self.model.accuracy,
                )
            else:
                logger.info("已加载模型文件，但模型未训练")
        except Exception as e:
            logger.warning("加载模型失败: %s，将使用未训练模型", e)

    # ── 训练 ──────────────────────────────────────────────────────────────────────

    async def train(self, db_session) -> dict:
        """从数据库拉取历史成交/丢失数据，训练模型。

        Args:
            db_session: SQLAlchemy 异步会话

        Returns:
            训练结果 dict
        """
        from sqlalchemy import select, func
        from app.crm.crm_models import CrmContact, CrmDeal, CrmActivity, CrmPipelineStage

        # 1. 获取所有已成交/已丢失的 Deal
        result = await db_session.execute(
            select(CrmDeal).where(CrmDeal.status.in_(["won", "lost"]))
        )
        deals = list(result.scalars().all())

        if len(deals) < 3:
            return {
                "success": False,
                "message": f"训练数据不足（需要至少 3 条已成交/已丢失记录，当前 {len(deals)} 条）",
                "samples": len(deals),
            }

        # 2. 构建训练数据
        X_list: list[np.ndarray] = []
        y_list: list[int] = []

        for deal in deals:
            # 获取联系人
            contact = deal.contact  # lazy="joined"
            if not contact:
                continue

            # 获取活动数
            act_result = await db_session.execute(
                select(func.count(CrmActivity.id)).where(
                    CrmActivity.contact_id == contact.id,
                    CrmActivity.owner_id == deal.owner_id,
                )
            )
            activity_count = act_result.scalar() or 0

            # 管道阶段默认赢单率
            stage_prob = deal.stage.win_probability if deal.stage else 50.0

            # 提取特征
            contact_dict = contact.to_dict() if hasattr(contact, 'to_dict') else {
                "source": contact.source,
                "tags": contact.tags,
                "last_contacted_at": contact.last_contacted_at,
                "created_at": contact.created_at,
            }

            deal_dict = {
                "value": float(deal.value),
            }

            features = extract_features(
                deal_dict, contact_dict, activity_count, stage_prob
            )
            X_list.append(features)
            y_list.append(1 if deal.status == "won" else 0)

        if len(X_list) < 3:
            return {
                "success": False,
                "message": "有效训练数据不足（特征提取后不足 3 条）",
                "samples": len(X_list),
            }

        X = np.array(X_list, dtype=np.float64)
        y = np.array(y_list, dtype=np.float64)

        # 处理类别不平衡（如果有更多数据时自动加权）
        n_won = int(np.sum(y))
        n_lost = len(y) - n_won
        if n_won == 0 or n_lost == 0:
            return {
                "success": False,
                "message": "训练数据中只有一种类别（全部成交或全部丢失），无法训练",
                "samples": len(y),
                "won": n_won,
                "lost": n_lost,
            }

        # 3. 训练
        history = self.model.train(X, y, verbose=True)
        self._save_model()

        return {
            "success": True,
            "message": f"模型训练完成",
            "samples": len(y),
            "won": n_won,
            "lost": n_lost,
            "accuracy": round(self.model.accuracy, 1),
            "final_loss": round(history["final_loss"], 4),
            "features": NUM_FEATURES,
        }

    # ── 单 Deal 预测 ──────────────────────────────────────────────────────────────

    async def predict_deal(self, deal_id: int, db_session) -> dict:
        """对单个 Deal 进行赢单率预测。

        Args:
            deal_id: Deal ID
            db_session: SQLAlchemy 异步会话

        Returns:
            预测结果 dict，包含概率和置信度
        """
        from sqlalchemy import select, func
        from app.crm.crm_models import CrmContact, CrmDeal, CrmActivity, CrmPipelineStage

        # 查询 Deal + 关联数据
        result = await db_session.execute(
            select(CrmDeal).where(CrmDeal.id == deal_id)
        )
        deal = result.unique().scalar_one_or_none()
        if not deal:
            return {"error": "Deal 不存在", "deal_id": deal_id}

        contact = deal.contact
        if not contact:
            return {"error": "Deal 未关联联系人", "deal_id": deal_id}

        # 活动数
        act_result = await db_session.execute(
            select(func.count(CrmActivity.id)).where(
                CrmActivity.contact_id == contact.id,
                CrmActivity.owner_id == deal.owner_id,
            )
        )
        activity_count = act_result.scalar() or 0

        stage_prob = deal.stage.win_probability if deal.stage else 50.0

        # 提取特征
        contact_dict = {
            "source": contact.source,
            "tags": contact.tags,
            "last_contacted_at": contact.last_contacted_at,
            "created_at": contact.created_at,
        }
        deal_dict = {"value": float(deal.value)}

        features = extract_features(deal_dict, contact_dict, activity_count, stage_prob)

        # 预测
        if not self.model.is_trained:
            # 模型未训练，使用管道阶段默认赢单率 + 规则修正
            prob = self._rule_based_prediction(
                contact.source, activity_count, stage_prob
            )
            confidence = "low"
        else:
            X = features.reshape(1, -1)
            prob = float(self.model.predict_proba(X)[0])
            confidence = get_confidence(prob, self.model.train_samples)

        prob_percent = round(prob * 100, 1)

        return {
            "deal_id": deal_id,
            "title": deal.title,
            "contact_name": contact.name,
            "contact_source": contact.source,
            "stage_name": deal.stage.name if deal.stage else None,
            "deal_value": float(deal.value),
            "predicted_win_probability": prob_percent,
            "confidence": confidence,
            "model_trained": self.model.is_trained,
            "features": {
                "source": contact.source,
                "tag_count": len(json.loads(contact.tags)) if contact.tags else 0,
                "activity_count": activity_count,
                "deal_value": float(deal.value),
                "stage_win_probability": stage_prob,
            },
        }

    # ── 规则兜底 ──────────────────────────────────────────────────────────────────

    @staticmethod
    def _rule_based_prediction(
        source: str,
        activity_count: int,
        stage_win_prob: float,
    ) -> float:
        """模型未训练时的规则兜底预测。

        基于管道阶段默认赢单率，结合来源和活动数微调。
        """
        prob = stage_win_prob / 100.0

        # 来源修正
        source_boost = {
            "match": 0.05,   # 名片交换 → 已有互动
            "manual": 0.03,  # 手动录入 → 有意向
            "visitor": 0.0,  # 访客 → 不确定
            "import": -0.05, # 导入 → 冷启动
        }
        prob += source_boost.get(source, 0.0)

        # 活动数修正
        if activity_count >= 5:
            prob += 0.08
        elif activity_count >= 2:
            prob += 0.03

        return max(0.01, min(0.99, prob))

    # ── 模型状态 ──────────────────────────────────────────────────────────────────

    def get_status(self) -> dict:
        """获取模型状态。"""
        return {
            "model_trained": self.model.is_trained,
            "train_samples": self.model.train_samples,
            "accuracy": round(self.model.accuracy, 1) if self.model.is_trained else None,
            "n_features": NUM_FEATURES,
            "features_description": [
                "source_match", "source_manual", "source_visitor", "source_import",
                "tag_count_norm", "activity_count_norm",
                "follow_up_days_norm", "deal_value_norm", "stage_win_prob",
            ],
        }


# ── 全局单例 ──────────────────────────────────────────────────────────────────────

_prediction_service: SalesPredictionService | None = None


def get_prediction_service() -> SalesPredictionService:
    """获取全局销售预测服务实例。"""
    global _prediction_service
    if _prediction_service is None:
        _prediction_service = SalesPredictionService()
    return _prediction_service
