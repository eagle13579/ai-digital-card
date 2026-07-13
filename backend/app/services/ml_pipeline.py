"""
链客宝 — 模型训练管线 (自进化闭环)
===================================
全自动 ML 训练管线:
  1. 自动采集: 用户行为数据 + 匹配结果 + 反馈数据
  2. 特征工程: 用户画像特征 + 行为特征 + 时间特征
  3. 模型训练: 调用 training_data_generator 生成训练数据
  4. 模型评估: precision@k, recall@k, nDCG
  5. 模型部署: 自动切换最优模型到生产

用法:
    pipeline = MLPipeline()
    pipeline.run_full_pipeline()       # 全自动运行
    pipeline.train_model(session)      # 单步训练
    pipeline.evaluate(session)         # 单步评估
"""

from __future__ import annotations

import json
import logging
import math
import os
import pickle
import time
import random
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger("chainke.ml_pipeline")

# ---------------------------------------------------------------------------
# 可选依赖 (SKLearn 用于实际训练)
# ---------------------------------------------------------------------------
try:
    from sklearn.ensemble import RandomForestClassifier
    from sklearn.linear_model import LogisticRegression
    from sklearn.model_selection import train_test_split
    from sklearn.metrics import precision_score, recall_score, ndcg_score as sk_ndcg

    _HAS_SKLEARN = True
except ImportError:
    _HAS_SKLEARN = False
    logger.warning("[MLPipeline] sklearn 未安装，使用模拟模式")


# ===================================================================
# 数据模型
# ===================================================================

@dataclass
class ModelVersion:
    """模型版本元数据"""
    version_id: str
    created_at: float
    model_type: str  # "random_forest", "logistic_regression", "simulated"
    metrics: Dict[str, float] = field(default_factory=dict)
    feature_names: List[str] = field(default_factory=list)
    deployed: bool = False

    def to_dict(self) -> dict:
        return {
            "version_id": self.version_id,
            "created_at": datetime.fromtimestamp(self.created_at).isoformat(),
            "model_type": self.model_type,
            "metrics": self.metrics,
            "feature_count": len(self.feature_names),
            "deployed": self.deployed,
        }


@dataclass
class EvalResult:
    """评估结果"""
    precision_at_k: float
    recall_at_k: float
    ndcg_at_k: float
    accuracy: float
    f1_score: float
    k: int
    sample_size: int

    def to_dict(self) -> dict:
        return {
            "precision_at_k": round(self.precision_at_k, 4),
            "recall_at_k": round(self.recall_at_k, 4),
            "ndcg_at_k": round(self.ndcg_at_k, 4),
            "accuracy": round(self.accuracy, 4),
            "f1_score": round(self.f1_score, 4),
            "k": self.k,
            "sample_size": self.sample_size,
        }


@dataclass
class TrainingRun:
    """单次训练运行记录"""
    run_id: str
    model_type: str
    status: str  # "running", "completed", "failed"
    started_at: float
    completed_at: Optional[float] = None
    samples_count: int = 0
    eval_result: Optional[EvalResult] = None
    error: str = ""

    def to_dict(self) -> dict:
        return {
            "run_id": self.run_id,
            "model_type": self.model_type,
            "status": self.status,
            "started_at": datetime.fromtimestamp(self.started_at).isoformat(),
            "completed_at": datetime.fromtimestamp(self.completed_at).isoformat()
                if self.completed_at else None,
            "samples_count": self.samples_count,
            "eval": self.eval_result.to_dict() if self.eval_result else None,
            "error": self.error,
        }


# ===================================================================
# 模型管线
# ===================================================================

class MLPipeline:
    """机器学习训练管线 — 自进化闭环核心

    管线步骤:
        1. collect_data   → 从 DB / 合成生成训练数据
        2. feature_engineer → 特征提取与归一化
        3. train_model    → 训练分类模型
        4. evaluate       → precision@k / recall@k / nDCG
        5. deploy         → 部署最优模型到生产
    """

    MODELS_DIR = os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        "..", "..", "models",
    )

    def __init__(self):
        self._versions: Dict[str, ModelVersion] = {}
        self._current_model: Any = None
        self._current_version_id: Optional[str] = None
        self._training_runs: List[TrainingRun] = []
        self._feature_names: List[str] = []

        os.makedirs(self.MODELS_DIR, exist_ok=True)
        self._load_versions()

    # ── 全自动管线 ──────────────────────────────────────────────────

    def run_full_pipeline(
        self,
        db_session=None,
        model_type: str = "auto",
        test_size: float = 0.2,
        k: int = 10,
    ) -> TrainingRun:
        """全自动运行训练管线

        Args:
            db_session: 数据库会话 (None 则使用合成数据)
            model_type: "random_forest", "logistic_regression", "auto"
            test_size: 测试集比例
            k: 评估 top-k

        Returns:
            本次训练运行记录
        """
        run_id = f"run_{int(time.time())}"
        run = TrainingRun(
            run_id=run_id,
            model_type=model_type,
            status="running",
            started_at=time.time(),
        )
        self._training_runs.append(run)

        try:
            logger.info("[MLPipeline] 开始全自动管线 run=%s", run_id)

            # Step 1: 数据采集
            data = self.collect_data(db_session=db_session)
            run.samples_count = len(data)

            if not data:
                raise ValueError("训练数据为空，无法训练")

            # Step 2: 特征工程
            X, y = self.feature_engineer(data)

            if len(X) < 10:
                raise ValueError(f"训练样本过少 ({len(X)}), 至少需要 10 条")

            # Step 3: 训练
            self._current_model, metrics = self.train_model(
                X, y, model_type=model_type, test_size=test_size,
            )

            # Step 4: 评估
            eval_result = self.evaluate(X, y, k=k)

            # Step 5: 保存版本
            version = ModelVersion(
                version_id=f"v_{int(time.time())}",
                created_at=time.time(),
                model_type=model_type if model_type != "auto" else type(self._current_model).__name__,
                metrics=metrics,
                feature_names=self._feature_names,
            )
            self._save_model(version)

            run.status = "completed"
            run.completed_at = time.time()
            run.eval_result = eval_result
            run.model_type = version.model_type

            logger.info(
                "[MLPipeline] 管线完成 run=%s, model=%s, samples=%d, precision@%d=%.4f",
                run_id, version.model_type, run.samples_count, k, eval_result.precision_at_k,
            )

        except Exception as e:
            logger.exception("[MLPipeline] 管线失败 run=%s", run_id)
            run.status = "failed"
            run.completed_at = time.time()
            run.error = str(e)

        return run

    # ── 步骤 1: 数据采集 ──────────────────────────────────────────

    def collect_data(
        self,
        db_session=None,
        days_back: int = 90,
        max_samples: int = 5000,
    ) -> List[Dict[str, Any]]:
        """采集训练数据"""
        from app.services.training_data_generator import generate_training_data

        logger.info("[MLPipeline] 采集训练数据...")
        data = generate_training_data(
            db_session=db_session,
            days_back=days_back,
            max_samples=max_samples,
        )
        logger.info("[MLPipeline] 采集到 %d 条训练数据", len(data))
        return data

    # ── 步骤 2: 特征工程 ──────────────────────────────────────────

    def feature_engineer(
        self,
        data: List[Dict[str, Any]],
    ) -> Tuple[List[List[float]], List[int]]:
        """特征工程: 从原始数据中提取特征矩阵

        Args:
            data: 原始训练数据列表

        Returns:
            (X, y) — 特征矩阵和标签向量
        """
        logger.info("[MLPipeline] 执行特征工程...")

        # 固定特征顺序
        from app.services.training_data_generator import get_feature_names
        feature_names = get_feature_names()
        self._feature_names = feature_names

        X: List[List[float]] = []
        y: List[int] = []

        for sample in data:
            features = sample.get("features", {})
            label = sample.get("label", 0)

            # 提取特征向量 (固定顺序)
            vec = [float(features.get(name, 0.0)) for name in feature_names]
            X.append(vec)
            y.append(label)

        logger.info(
            "[MLPipeline] 特征工程完成: %d 样本 x %d 特征",
            len(X), len(feature_names),
        )
        return X, y

    # ── 步骤 3: 模型训练 ──────────────────────────────────────────

    def train_model(
        self,
        X: List[List[float]],
        y: List[int],
        model_type: str = "auto",
        test_size: float = 0.2,
    ) -> Tuple[Any, Dict[str, float]]:
        """训练模型

        Args:
            X: 特征矩阵
            y: 标签向量
            model_type: "random_forest", "logistic_regression", "simulated", "auto"
            test_size: 测试集比例

        Returns:
            (model, metrics_dict)
        """
        logger.info("[MLPipeline] 开始训练模型 (type=%s)...", model_type)

        if not _HAS_SKLEARN or model_type == "simulated":
            return self._train_simulated(X, y)

        # 自动选择
        if model_type == "auto":
            model_type = "random_forest" if len(X) >= 100 else "logistic_regression"

        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=test_size, random_state=42,
        )

        if model_type == "random_forest":
            model = RandomForestClassifier(
                n_estimators=100, max_depth=10, random_state=42, n_jobs=-1,
            )
        elif model_type == "logistic_regression":
            model = LogisticRegression(
                max_iter=1000, random_state=42, n_jobs=-1,
            )
        else:
            raise ValueError(f"Unknown model_type: {model_type}")

        model.fit(X_train, y_train)

        # 计算指标
        y_pred = model.predict(X_test)
        acc = float(precision_score(y_test, y_pred, average="binary", zero_division=0))
        rec = float(recall_score(y_test, y_pred, average="binary", zero_division=0))

        metrics = {
            "accuracy": acc,
            "recall": rec,
            "precision": acc,
            "train_samples": len(X_train),
            "test_samples": len(X_test),
            "feature_count": len(self._feature_names),
        }

        self._current_model = model
        logger.info("[MLPipeline] 模型训练完成: accuracy=%.4f, recall=%.4f", acc, rec)
        return model, metrics

    def _train_simulated(
        self,
        X: List[List[float]],
        y: List[int],
    ) -> Tuple[Any, Dict[str, float]]:
        """模拟训练 (无 sklearn 时的降级)"""
        logger.info("[MLPipeline] 使用模拟训练模式")
        y_pred = []
        for vec in X:
            score = sum(vec) / max(len(vec), 1)
            y_pred.append(1 if score > 0.4 else 0)

        correct = sum(1 for i in range(len(y)) if y_pred[i] == y[i])
        acc = correct / max(len(y), 1)
        pos_correct = sum(1 for i in range(len(y)) if y_pred[i] == 1 and y[i] == 1)
        pos_total = sum(1 for i in range(len(y)) if y[i] == 1)
        recall = pos_correct / max(pos_total, 1)

        self._current_model = {"type": "simulated", "threshold": 0.4}
        metrics = {
            "accuracy": acc,
            "recall": recall,
            "precision": pos_correct / max(sum(1 for p in y_pred if p == 1), 1),
            "train_samples": len(X),
            "test_samples": 0,
            "feature_count": len(self._feature_names),
        }
        return self._current_model, metrics

    # ── 步骤 4: 评估 ──────────────────────────────────────────────

    def evaluate(
        self,
        X: List[List[float]],
        y: List[int],
        k: int = 10,
    ) -> EvalResult:
        """评估模型: precision@k, recall@k, nDCG@k

        Args:
            X: 特征矩阵
            y: 真实标签
            k: top-k

        Returns:
            EvalResult
        """
        logger.info("[MLPipeline] 开始评估 (k=%d)...", k)

        if not X or not y:
            return EvalResult(
                precision_at_k=0.0, recall_at_k=0.0, ndcg_at_k=0.0,
                accuracy=0.0, f1_score=0.0, k=k, sample_size=0,
            )

        # 获取预测分数
        scores = self._predict_scores(X)

        # 转 numpy 格式如果可用
        try:
            import numpy as np
            scores_np = np.array(scores)
            y_np = np.array(y)
            _HAS_NUMPY = True
        except ImportError:
            _HAS_NUMPY = False

        # precision@k: top-k 中正确的比例
        top_k_indices = sorted(
            range(len(scores)), key=lambda i: scores[i], reverse=True,
        )[:min(k, len(scores))]

        top_k_relevant = sum(1 for i in top_k_indices if y[i] == 1)
        precision_at_k = top_k_relevant / max(k, 1)

        # recall@k: top-k 中正确的 / 总相关数
        total_relevant = sum(1 for label in y if label == 1)
        recall_at_k = top_k_relevant / max(total_relevant, 1)

        # nDCG@k
        ndcg = self._ndcg_at_k(scores, y, min(k, len(scores)))

        # 整体准确率和 F1
        preds = [1 if s > 0.5 else 0 for s in scores]
        correct = sum(1 for i in range(len(y)) if preds[i] == y[i])
        accuracy = correct / max(len(y), 1)

        tp = sum(1 for i in range(len(y)) if preds[i] == 1 and y[i] == 1)
        fp = sum(1 for i in range(len(y)) if preds[i] == 1 and y[i] == 0)
        fn = sum(1 for i in range(len(y)) if preds[i] == 0 and y[i] == 1)
        f1 = (2 * tp) / max((2 * tp + fp + fn), 1)

        result = EvalResult(
            precision_at_k=precision_at_k,
            recall_at_k=recall_at_k,
            ndcg_at_k=ndcg,
            accuracy=accuracy,
            f1_score=f1,
            k=k,
            sample_size=len(y),
        )

        logger.info(
            "[MLPipeline] 评估完成: precision@%d=%.4f, recall@%d=%.4f, nDCG=%.4f",
            k, precision_at_k, k, recall_at_k, ndcg,
        )
        return result

    def _predict_scores(self, X: List[List[float]]) -> List[float]:
        """获取预测分数 (0~1)"""
        if self._current_model is None:
            return [0.5] * len(X)

        try:
            # sklearn 模型
            import numpy as np
            if hasattr(self._current_model, "predict_proba"):
                probas = self._current_model.predict_proba(np.array(X))
                return [float(p[1]) if probas.shape[1] > 1 else float(p[0]) for p in probas]
            if hasattr(self._current_model, "predict"):
                return [float(p) for p in self._current_model.predict(np.array(X))]
        except Exception:
            pass

        # 模拟模式
        if isinstance(self._current_model, dict):
            threshold = self._current_model.get("threshold", 0.4)
            return [sum(v) / max(len(v), 1) for v in X]

        return [0.5] * len(X)

    @staticmethod
    def _ndcg_at_k(scores: List[float], y: List[int], k: int) -> float:
        """计算 nDCG@k"""
        if k <= 0 or not scores:
            return 0.0

        # 按分数降序排序
        pairs = list(zip(scores, y))
        pairs.sort(key=lambda p: p[0], reverse=True)
        ranked = pairs[:k]

        dcg = 0.0
        for i, (_, rel) in enumerate(ranked):
            dcg += (2 ** rel - 1) / math.log2(i + 2)

        # IDCG: 理想排序
        ideal = sorted(y, reverse=True)[:k]
        idcg = sum((2 ** rel - 1) / math.log2(i + 2) for i, rel in enumerate(ideal))

        return dcg / idcg if idcg > 0 else 0.0

    # ── 步骤 5: 部署 ──────────────────────────────────────────────

    def deploy(self, version_id: str) -> bool:
        """部署指定版本到生产

        Args:
            version_id: 模型版本 ID

        Returns:
            是否成功
        """
        if version_id not in self._versions:
            logger.error("[MLPipeline] 版本 %s 不存在，无法部署", version_id)
            return False

        # 取消所有已部署版本
        for vid, v in self._versions.items():
            if v.deployed:
                v.deployed = False

        self._versions[version_id].deployed = True
        self._current_version_id = version_id
        self._save_versions()

        # 加载模型文件
        model_path = os.path.join(self.MODELS_DIR, f"{version_id}.pkl")
        if os.path.exists(model_path):
            try:
                with open(model_path, "rb") as f:
                    self._current_model = pickle.load(f)  # nosec - loading model files from controlled MODELS_DIR
                logger.info("[MLPipeline] 模型 %s 已加载到生产", version_id)
            except Exception as e:
                logger.warning("[MLPipeline] 加载模型 %s 失败: %s", version_id, e)

        logger.info("[MLPipeline] 部署版本 %s 到生产", version_id)
        return True

    def auto_deploy(self) -> Optional[str]:
        """自动选择并部署最优模型

        规则: 选择 precision@k 最高的版本
        """
        if not self._versions:
            logger.info("[MLPipeline] 无可用模型版本，跳过自动部署")
            return None

        best_vid = max(
            self._versions.keys(),
            key=lambda vid: self._versions[vid].metrics.get("precision", 0),
        )

        self.deploy(best_vid)
        logger.info(
            "[MLPipeline] 自动部署最优版本 %s (precision=%.4f)",
            best_vid,
            self._versions[best_vid].metrics.get("precision", 0),
        )
        return best_vid

    # ── 持久化 ────────────────────────────────────────────────────

    def _save_model(self, version: ModelVersion) -> None:
        """保存模型到磁盘"""
        self._versions[version.version_id] = version

        # 保存模型文件
        if self._current_model is not None:
            model_path = os.path.join(self.MODELS_DIR, f"{version.version_id}.pkl")
            try:
                with open(model_path, "wb") as f:
                    pickle.dump(self._current_model, f)
                logger.info("[MLPipeline] 模型保存到 %s", model_path)
            except Exception as e:
                logger.warning("[MLPipeline] 保存模型失败: %s", e)

        self._save_versions()

    def _save_versions(self) -> None:
        """保存版本元数据"""
        meta_path = os.path.join(self.MODELS_DIR, "versions.json")
        try:
            data = {
                vid: v.to_dict()
                for vid, v in self._versions.items()
            }
            with open(meta_path, "w") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.warning("[MLPipeline] 保存版本元数据失败: %s", e)

    def _load_versions(self) -> None:
        """加载已有的版本元数据"""
        meta_path = os.path.join(self.MODELS_DIR, "versions.json")
        if os.path.exists(meta_path):
            try:
                with open(meta_path) as f:
                    data = json.load(f)
                for vid, info in data.items():
                    self._versions[vid] = ModelVersion(
                        version_id=vid,
                        created_at=datetime.fromisoformat(info["created_at"]).timestamp(),
                        model_type=info["model_type"],
                        metrics=info.get("metrics", {}),
                        feature_names=[],
                        deployed=info.get("deployed", False),
                    )
                logger.info(
                    "[MLPipeline] 加载 %d 个已保存的模型版本", len(self._versions)
                )
            except Exception as e:
                logger.warning("[MLPipeline] 加载版本元数据失败: %s", e)

    # ── 查询接口 ──────────────────────────────────────────────────

    def list_versions(self) -> List[ModelVersion]:
        """列出所有模型版本"""
        return list(self._versions.values())

    def get_production_model(self) -> Optional[str]:
        """获取当前生产模型的版本 ID"""
        for vid, v in self._versions.items():
            if v.deployed:
                return vid
        return None

    def get_recent_runs(self, limit: int = 10) -> List[TrainingRun]:
        """获取最近的训练运行记录"""
        return sorted(
            self._training_runs,
            key=lambda r: r.started_at,
            reverse=True,
        )[:limit]

    def predict(self, features: Dict[str, float]) -> Dict[str, Any]:
        """使用当前生产模型进行预测

        Args:
            features: 特征字典，key 需与训练时一致

        Returns:
            {"score": 0.85, "label": 1, "version_id": "v_1234567890"}
        """
        if not self._feature_names:
            return {"score": 0.5, "label": 0, "version_id": None, "error": "no_trained_model"}

        vec = [float(features.get(name, 0.0)) for name in self._feature_names]

        if self._current_model is None:
            score = sum(vec) / max(len(vec), 1)
        else:
            scores = self._predict_scores([vec])
            score = scores[0] if scores else 0.5

        return {
            "score": round(score, 4),
            "label": 1 if score > 0.5 else 0,
            "version_id": self._current_version_id,
            "feature_names": self._feature_names,
        }


# ===================================================================
# 单例
# ===================================================================

pipeline = MLPipeline()

__all__ = [
    "MLPipeline",
    "ModelVersion",
    "EvalResult",
    "TrainingRun",
    "pipeline",
]
