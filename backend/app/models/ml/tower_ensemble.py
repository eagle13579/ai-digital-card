"""
AI数智名片 — 三塔集成评分推理 (TowerEnsemble)

整合行为塔(BehaviorTower)，实现企业-用户行为匹配评分与排序推理。

架构:
  TowerEnsemble(nn.Module):
    集成三塔输出做最终评分，可用于训练和推理

  MatchingScorer:
    score = α * cos(behavior_emb, target_emb)
          + β * (用户行为模式匹配度)
          + γ * (行为多样性)

    权重默认: α=0.5 (行为-目标相似度), β=0.3 (行为模式匹配), γ=0.2 (行为一致性)

  MatchingAPI:
    predict(user_id, candidates) → 排序后的 [(enterprise, score), ...]

用法:
    from app.models.ml import TowerEnsemble, MatchingScorer, MatchingAPI

    ensemble = TowerEnsemble(behavior_tower, hidden_dim=128)
    score = ensemble(user_features, behavior_tensor, behavior_mask)

    api = MatchingAPI(behavior_tower, behavior_encoder)
    results = api.predict(user_info, candidate_list)
"""

from __future__ import annotations

import json
import logging
import math
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
# 常量
# ---------------------------------------------------------------------------
DEFAULT_WEIGHTS = {"alpha": 0.5, "beta": 0.3, "gamma": 0.2}

# ---------------------------------------------------------------------------
# TowerEnsemble — 三塔集成评分 nn.Module
# ---------------------------------------------------------------------------
class TowerEnsemble(nn.Module):
    """三塔集成评分模块 (nn.Module)。

    将行为塔输出的 128d 嵌入与目标嵌入做集成评分。
    可用作可训练的评分头。

    Args:
        behavior_tower: BehaviorTower 实例
        hidden_dim:     隐层维度 (默认 128)
        dropout:        Dropout 比率 (默认 0.1)
    """

    def __init__(
        self,
        behavior_tower: nn.Module,
        hidden_dim: int = 128,
        dropout: float = 0.1,
    ):
        super().__init__()

        if not TORCH_AVAILABLE:
            raise ImportError("PyTorch is required for TowerEnsemble.")

        self.behavior_tower = behavior_tower
        self.hidden_dim = hidden_dim

        # ── 评分头: 将行为嵌入映射为三通道评分 ──
        self.scoring_head = nn.Sequential(
            nn.Linear(hidden_dim, hidden_dim // 2),
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.Linear(hidden_dim // 2, 3),  # [α, β, γ] 原始权重
        )

        # ── 最终评分投影 (可选) ──
        self.final_proj = nn.Linear(hidden_dim, 1)

        self._init_weights()

    def _init_weights(self):
        """初始化权重"""
        for m in self.modules():
            if isinstance(m, nn.Linear):
                nn.init.xavier_uniform_(m.weight)
                if m.bias is not None:
                    nn.init.zeros_(m.bias)

    def forward(
        self,
        behavior_sequence: torch.Tensor,
        mask: Optional[torch.Tensor] = None,
        target_embedding: Optional[torch.Tensor] = None,
    ) -> torch.Tensor:
        """前向传播 → 评分。

        Args:
            behavior_sequence: (B, max_seq_len, feature_dim) 行为序列
            mask: (B, max_seq_len) 布尔掩码, True=有效
            target_embedding: (B, 128) 目标嵌入 (可选)

        Returns:
            (B,) 评分张量, 范围 [0, 1]
        """
        # ── 行为嵌入 ──
        behav_emb = self.behavior_tower(behavior_sequence, mask)  # (B, 128)

        # ── 评分头预测权重 ──
        raw_weights = self.scoring_head(behav_emb)  # (B, 3)
        weights = F.softmax(raw_weights, dim=1)  # (B, 3), sum=1 per row

        # ── 三通道评分 ──
        if target_embedding is not None:
            target_emb = target_embedding
            sim_behavior_target = F.cosine_similarity(behav_emb, target_emb, dim=1)  # (B,)
        else:
            sim_behavior_target = torch.ones(behav_emb.size(0), device=behav_emb.device) * 0.5

        # 行为模式强度 (自身 norm 的代理)
        behav_norm = behav_emb.norm(p=2, dim=1)  # (B,), 因 L2 归一化 ≈1
        behav_intensity = behav_norm / math.sqrt(self.hidden_dim)  # 归一化

        # 行为一致性 (与历史均值的余弦)
        behav_mean = behav_emb.mean(dim=0, keepdim=True).expand_as(behav_emb)
        behav_consistency = F.cosine_similarity(behav_emb, behav_mean, dim=1)

        # ── 加权求和 ──
        scores = (
            weights[:, 0] * sim_behavior_target
            + weights[:, 1] * behav_intensity
            + weights[:, 2] * behav_consistency
        )

        return scores.clamp(0.0, 1.0)

    @torch.no_grad()
    def predict(
        self,
        behavior_sequence: torch.Tensor,
        mask: Optional[torch.Tensor] = None,
    ) -> np.ndarray:
        """推理接口, 返回 numpy 评分数组"""
        self.eval()
        scores = self.forward(behavior_sequence, mask)
        return scores.cpu().numpy()

    def save(self, path: Union[str, Path]) -> str:
        """保存模型权重"""
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        torch.save(self.state_dict(), str(path))
        logger.info(f"TowerEnsemble 模型已保存: {path}")
        return str(path)

    @classmethod
    def load(cls, path: Union[str, Path], behavior_tower: nn.Module, **kwargs) -> "TowerEnsemble":
        """从文件加载模型权重"""
        path = Path(path)
        if not path.exists():
            raise FileNotFoundError(f"模型文件不存在: {path}")
        model = cls(behavior_tower=behavior_tower, **kwargs)
        state = torch.load(str(path), map_location="cpu")
        model.load_state_dict(state)
        model.eval()
        logger.info(f"TowerEnsemble 模型已加载: {path}")
        return model

    def __repr__(self) -> str:
        return (
            f"TowerEnsemble("
            f"hidden_dim={self.hidden_dim})"
        )


# ---------------------------------------------------------------------------
# 在线权重优化器
# ---------------------------------------------------------------------------
class OnlineWeightOptimizer:
    """在线权重优化器。

    根据用户隐式反馈 (点击/匹配成功) 在线调整 MatchingScorer 的三项权重。

    更新策略 (Bandit-like):
      α ← α + η * (reward - baseline) * (sim_user_ent - baseline_sim)

    Args:
        lr: 学习率 (默认 0.01)
        baseline_decay: 基线衰减系数 (默认 0.9)
        initial_weights: 初始权重 dict {"alpha": 0.5, "beta": 0.3, "gamma": 0.2}
        weight_bounds: 权重范围 (默认 [0.1, 0.8])
    """

    def __init__(
        self,
        lr: float = 0.01,
        baseline_decay: float = 0.9,
        initial_weights: Optional[Dict[str, float]] = None,
        weight_bounds: Tuple[float, float] = (0.05, 0.9),
    ):
        self.lr = lr
        self.baseline_decay = baseline_decay
        self.weights = dict(initial_weights or DEFAULT_WEIGHTS)
        self.weight_bounds = weight_bounds

        # ── 状态 ──
        self.total_updates = 0
        self.reward_baseline = 0.0
        self.reward_history: List[float] = []
        self.weight_history: List[Dict[str, float]] = []

    def update(
        self,
        sim_user_ent: float,
        sim_behavior_ent: float,
        sim_user_behavior: float,
        reward: float,
    ) -> Dict[str, float]:
        """根据一次交互反馈更新权重。

        Args:
            sim_user_ent:      用户-企业余弦相似度
            sim_behavior_ent:  行为-企业余弦相似度
            sim_user_behavior: 用户-行为余弦相似度
            reward:            反馈奖励 (点击=1.0, 匹配成功=2.0, 无反应=0.0, 负反馈=-0.5)

        Returns:
            更新后的权重 dict
        """
        # ── 更新基线 ──
        self.reward_baseline = (
            self.baseline_decay * self.reward_baseline
            + (1 - self.baseline_decay) * reward
        )

        # ── 计算优势 (Advantage) ──
        advantage = reward - self.reward_baseline

        # ── 更新每个权重 ──
        alpha_grad = advantage * (sim_user_ent - 0.5)
        self.weights["alpha"] += self.lr * alpha_grad

        beta_grad = advantage * (sim_behavior_ent - 0.5)
        self.weights["beta"] += self.lr * beta_grad

        gamma_grad = advantage * (sim_user_behavior - 0.5)
        self.weights["gamma"] += self.lr * gamma_grad

        # ── 约束权重范围 ──
        lower, upper = self.weight_bounds
        for k in self.weights:
            self.weights[k] = max(lower, min(upper, self.weights[k]))

        # ── 归一化使权重和为 1 ──
        total = sum(self.weights.values())
        if total > 0:
            for k in self.weights:
                self.weights[k] /= total

        # ── 记录 ──
        self.total_updates += 1
        self.reward_history.append(reward)
        self.weight_history.append(dict(self.weights))

        return dict(self.weights)

    def get_weights(self) -> Dict[str, float]:
        """返回当前权重 (深拷贝)"""
        return dict(self.weights)

    def reset_weights(self, weights: Optional[Dict[str, float]] = None) -> None:
        """重置权重"""
        self.weights = dict(weights or DEFAULT_WEIGHTS)
        self.reward_baseline = 0.0

    def __repr__(self) -> str:
        return (
            f"OnlineWeightOptimizer("
            f"α={self.weights['alpha']:.4f}, "
            f"β={self.weights['beta']:.4f}, "
            f"γ={self.weights['gamma']:.4f}, "
            f"updates={self.total_updates})"
        )


# ===================================================================
# 匹配评分器
# ===================================================================
class MatchingScorer:
    """三塔拼接匹配评分器。

    计算:
        score = α * cos(behavior_emb, target_emb)
              + β * cos(behavior_emb, target_emb)
              + γ * cos(behavior_emb, behavior_emb)

    Args:
        behavior_tower:   BehaviorTower 实例
        weights:          权重 dict {"alpha": 0.5, "beta": 0.3, "gamma": 0.2}
        use_online_opt:   是否使用 OnlineWeightOptimizer (默认 False)
    """

    def __init__(
        self,
        behavior_tower: nn.Module,
        weights: Optional[Dict[str, float]] = None,
        use_online_opt: bool = False,
    ):
        if not TORCH_AVAILABLE:
            raise ImportError("PyTorch is required for MatchingScorer.")

        self.behavior_tower = behavior_tower
        self.weights = dict(weights or DEFAULT_WEIGHTS)
        self.weight_optimizer: Optional[OnlineWeightOptimizer] = None
        if use_online_opt:
            self.weight_optimizer = OnlineWeightOptimizer(initial_weights=self.weights)

        # ── 设备 ──
        self.device = torch.device("cpu")
        params = list(self.behavior_tower.parameters())
        if params:
            self.device = params[0].device

    # ------------------------------------------------------------------
    # score: 单次评分
    # ------------------------------------------------------------------
    @torch.no_grad()
    def score(
        self,
        user_features: torch.Tensor,
        target_features: torch.Tensor,
        behavior_sequence: Optional[torch.Tensor] = None,
        behavior_mask: Optional[torch.Tensor] = None,
    ) -> float:
        """计算用户行为与目标的匹配分数。

        Args:
            user_features:       (1, D_user) 用户特征
            target_features:     (1, D_target) 目标特征
            behavior_sequence:   (1, S, D_behav) 行为序列 (可选)
            behavior_mask:       (1, S) 行为掩码 (可选)

        Returns:
            float: 0~1 匹配分数
        """
        self.behavior_tower.eval()

        user_features = user_features.to(self.device)
        target_features = target_features.to(self.device)

        # 如果没有行为数据, 只用基础相似度
        if behavior_sequence is None:
            sim = F.cosine_similarity(user_features, target_features, dim=1).item()
            final_score = self.weights["alpha"] * sim
            return float(max(0.0, min(1.0, final_score)))

        behavior_sequence = behavior_sequence.to(self.device)
        if behavior_mask is not None:
            behavior_mask = behavior_mask.to(self.device)

        behav_emb = self.behavior_tower(behavior_sequence, behavior_mask)  # (1, 128)

        sim_behavior_target = F.cosine_similarity(behav_emb, target_features, dim=1).item()
        sim_user_behavior = F.cosine_similarity(user_features, behav_emb, dim=1).item()

        # ── 计算加权分数 ──
        w = self.weights
        # 使用行为-目标相似度 + 用户-行为一致性
        final_score = (
            w["alpha"] * sim_behavior_target
            + w["beta"] * max(sim_behavior_target, sim_user_behavior)
            + w["gamma"] * sim_user_behavior
        )

        self._last_sims = (sim_behavior_target, sim_behavior_target, sim_user_behavior)

        return float(max(0.0, min(1.0, final_score)))

    # ------------------------------------------------------------------
    # forward: 批量评分 (返回张量)
    # ------------------------------------------------------------------
    @torch.no_grad()
    def forward(
        self,
        user_features: torch.Tensor,
        target_features: torch.Tensor,
        behavior_sequence: Optional[torch.Tensor] = None,
        behavior_mask: Optional[torch.Tensor] = None,
    ) -> torch.Tensor:
        """批量计算匹配分数。

        Args:
            user_features:       (1, D_user) 或 (B, D_user)
            target_features:     (1, D_target) 或 (B, D_target)
            behavior_sequence:   (1, S, D_behav) 或 None
            behavior_mask:       (1, S) 或 None

        Returns:
            (B,) 匹配分数张量
        """
        self.behavior_tower.eval()

        user_features = user_features.to(self.device)
        target_features = target_features.to(self.device)

        sim_user_target = F.cosine_similarity(user_features, target_features, dim=1)

        if behavior_sequence is not None:
            behavior_sequence = behavior_sequence.to(self.device)
            if behavior_mask is not None:
                behavior_mask = behavior_mask.to(self.device)
            behav_emb = self.behavior_tower(behavior_sequence, behavior_mask)

            sim_behavior_target = F.cosine_similarity(behav_emb, target_features, dim=1)
            sim_user_behavior = F.cosine_similarity(user_features, behav_emb, dim=1)

            w = self.weights
            scores = (
                w["alpha"] * sim_behavior_target
                + w["beta"] * sim_user_target
                + w["gamma"] * sim_user_behavior
            )
        else:
            scores = self.weights["alpha"] * sim_user_target

        return scores.clamp(0.0, 1.0)

    # ------------------------------------------------------------------
    # 权重管理
    # ------------------------------------------------------------------
    def update_weights(
        self,
        user_features: torch.Tensor,
        target_features: torch.Tensor,
        behavior_sequence: Optional[torch.Tensor],
        behavior_mask: Optional[torch.Tensor],
        reward: float,
    ) -> Dict[str, float]:
        """根据反馈更新权重。

        Args:
            user_features:       用户特征
            target_features:     目标特征
            behavior_sequence:   行为序列 (可选)
            behavior_mask:       行为掩码 (可选)
            reward:              反馈奖励

        Returns:
            更新后的权重 dict
        """
        if self.weight_optimizer is None:
            logger.warning("OnlineWeightOptimizer 未启用, 权重未更新")
            return dict(self.weights)

        self.score(
            user_features, target_features,
            behavior_sequence, behavior_mask,
        )

        sim_user_ent, sim_behavior_ent, sim_user_behavior = self._last_sims
        new_weights = self.weight_optimizer.update(
            sim_user_ent, sim_behavior_ent, sim_user_behavior, reward,
        )
        self.weights = new_weights
        return new_weights

    def set_weights(self, weights: Dict[str, float]) -> None:
        """手动设置权重"""
        self.weights = dict(weights)

    def get_weights(self) -> Dict[str, float]:
        """获取当前权重"""
        return dict(self.weights)

    def __repr__(self) -> str:
        return (
            f"MatchingScorer("
            f"α={self.weights['alpha']:.3f}, "
            f"β={self.weights['beta']:.3f}, "
            f"γ={self.weights['gamma']:.3f}"
            f")"
        )


# ===================================================================
# 匹配推理 API
# ===================================================================
@dataclass
class MatchResult:
    """匹配结果数据类"""
    target_id: Union[str, int]
    score: float
    sim_feature: float = 0.0
    sim_behavior: float = 0.0
    sim_consistency: float = 0.0

    def __lt__(self, other: "MatchResult") -> bool:
        return self.score < other.score


class MatchingAPI:
    """行为塔匹配推理 API。

    端到端推理管线: 用户行为 → 候选集 → 排序匹配。

    Args:
        behavior_tower: BehaviorTower 实例
        behavior_encoder: BehaviorSequenceEncoder 实例
        top_k: 默认返回 top-K 结果 (默认 20)
        batch_size: 批量推理大小 (默认 64)
    """

    def __init__(
        self,
        behavior_tower: BehaviorTower,
        behavior_encoder: BehaviorSequenceEncoder,
        top_k: int = 20,
        batch_size: int = 64,
    ):
        self.behavior_tower = behavior_tower
        self.behavior_encoder = behavior_encoder
        self.top_k = top_k
        self.batch_size = batch_size

        self._validate_encoders()

    def _validate_encoders(self):
        """验证编码器状态"""
        if not hasattr(self.behavior_encoder, '_fitted') or not self.behavior_encoder._fitted:
            raise RuntimeError("behavior_encoder 尚未 fit")

    # ------------------------------------------------------------------
    # predict: 主推理入口
    # ------------------------------------------------------------------
    @torch.no_grad()
    def predict(
        self,
        behavior_sequences: Optional[Union[Dict, List[Dict], List[List[Dict]]]] = None,
        candidates: Optional[List[Dict[str, Any]]] = None,
        candidate_embeddings: Optional[torch.Tensor] = None,
        top_k: Optional[int] = None,
    ) -> List[MatchResult]:
        """执行匹配推理, 返回排序后的匹配列表。

        Args:
            behavior_sequences: 用户行为序列 (可选)
                - None: 返回空结果
                - Dict: 单条行为
                - List[Dict]: 行为序列
            candidates: 候选目标信息列表 (与 candidate_embeddings 二选一)
            candidate_embeddings: (N, 128) 预计算候选嵌入 (与 candidates 二选一)
            top_k: 返回 top-K (默认使用实例的 top_k)

        Returns:
            List[MatchResult]: 按分数降序排列
        """
        top_k = top_k or self.top_k

        if behavior_sequences is None:
            return []

        # ── 编码行为序列 ──
        behavior_tensor, behavior_mask = self.behavior_encoder.transform(
            behavior_sequences
        )

        # ── 计算行为嵌入 ──
        behavior_emb = self.behavior_tower(behavior_tensor, behavior_mask)  # (1, 128)

        # ── 如果提供了候选嵌入, 直接计算相似度 ──
        if candidate_embeddings is not None:
            candidate_embeddings = candidate_embeddings.to(behavior_emb.device)
            sims = F.cosine_similarity(
                behavior_emb, candidate_embeddings, dim=1
            )  # (N,)
            scores = self.weights["alpha"] * sims.clamp(0.0, 1.0)

            all_results = [
                MatchResult(target_id=i, score=float(s))
                for i, s in enumerate(scores.tolist())
            ]
            all_results.sort(key=lambda r: r.score, reverse=True)
            return all_results[:top_k]

        # ── 否则使用候选列表 ──
        if candidates is None:
            return []

        all_results: List[MatchResult] = []
        n_candidates = len(candidates)

        for start in range(0, n_candidates, self.batch_size):
            end = min(start + self.batch_size, n_candidates)
            batch = candidates[start:end]

            for i, candidate in enumerate(batch):
                # 使用候选特征与行为嵌入计算分数
                # 候选的embedding由其特征与行为嵌入的余弦相似度决定
                cand_feat = candidate.get("feature", None)
                if cand_feat is not None:
                    if isinstance(cand_feat, (list, np.ndarray)):
                        cand_tensor = torch.tensor(cand_feat, dtype=torch.float32, device=behavior_emb.device).unsqueeze(0)
                        sim = float(F.cosine_similarity(behavior_emb, cand_tensor, dim=1).item())
                    else:
                        sim = 0.5
                else:
                    sim = 0.5

                target_id = candidate.get("target_id", candidate.get("id", f"target_{start + i}"))
                all_results.append(MatchResult(
                    target_id=target_id,
                    score=sim,
                ))

        all_results.sort(key=lambda r: r.score, reverse=True)
        return all_results[:top_k]

    # ------------------------------------------------------------------
    # save / load
    # ------------------------------------------------------------------
    def save(self, path: Union[str, Path], save_encoder: bool = True) -> str:
        """保存 API 状态 (行为塔权重 + 编码器状态)。

        Args:
            path: 保存目录路径
            save_encoder: 是否同时保存编码器状态

        Returns:
            保存路径
        """
        path = Path(path)
        path.mkdir(parents=True, exist_ok=True)

        # 保存行为塔
        tower_path = path / "behavior_tower.pt"
        self.behavior_tower.save(tower_path)

        # 保存编码器状态
        if save_encoder:
            import pickle
            encoder_path = path / "behavior_encoder.pkl"
            with open(encoder_path, "wb") as f:
                pickle.dump(self.behavior_encoder, f)

        # 保存配置
        config = {
            "top_k": self.top_k,
            "batch_size": self.batch_size,
        }
        config_path = path / "matching_api_config.json"
        with open(config_path, "w", encoding="utf-8") as f:
            json.dump(config, f, ensure_ascii=False, indent=2)

        logger.info(f"MatchingAPI 已保存到: {path}")
        return str(path)

    @classmethod
    def load(
        cls,
        path: Union[str, Path],
        tower_kwargs: Optional[Dict[str, Any]] = None,
    ) -> "MatchingAPI":
        """从文件加载 API 状态。

        Args:
            path: 保存目录路径
            tower_kwargs: 传递给 BehaviorTower 构造函数的参数

        Returns:
            MatchingAPI 实例
        """
        path = Path(path)
        if not path.exists():
            raise FileNotFoundError(f"MatchingAPI 保存目录不存在: {path}")

        # 加载配置
        config_path = path / "matching_api_config.json"
        if config_path.exists():
            with open(config_path, "r", encoding="utf-8") as f:
                config = json.load(f)
        else:
            config = {}

        # 加载行为塔
        tower_path = path / "behavior_tower.pt"
        if not tower_path.exists():
            raise FileNotFoundError(f"行为塔模型文件不存在: {tower_path}")
        tower = BehaviorTower.load(tower_path, **(tower_kwargs or {}))

        # 加载编码器
        import pickle
        encoder_path = path / "behavior_encoder.pkl"
        if encoder_path.exists():
            with open(encoder_path, "rb") as f:
                encoder = pickle.load(f)
        else:
            encoder = BehaviorSequenceEncoder()
            logger.warning("未找到编码器文件, 创建默认 BehaviorSequenceEncoder")
            encoder._fitted = False

        api = cls(
            behavior_tower=tower,
            behavior_encoder=encoder,
            top_k=config.get("top_k", 20),
            batch_size=config.get("batch_size", 64),
        )
        logger.info(f"MatchingAPI 已从 {path} 加载")
        return api

    def __repr__(self) -> str:
        return (
            f"MatchingAPI("
            f"top_k={self.top_k}, "
            f"batch_size={self.batch_size})"
        )


# ===================================================================
# 简易测试 (python tower_ensemble.py)
# ===================================================================
def _get_behavior_tower():
    """获取 BehaviorTower 实例 (支持包内和独立运行)"""
    try:
        from .behavior_tower import BehaviorTower
    except ImportError:
        from behavior_tower import BehaviorTower
    return BehaviorTower


def _test_tower_ensemble_forward():
    """TC1: TowerEnsemble 前向传播"""
    if not TORCH_AVAILABLE:
        print("  ⚠ PyTorch 不可用, 跳过测试")
        return

    BT = _get_behavior_tower()
    behav_tower = BT(max_seq_len=5, feature_dim=8, hidden_dim=64)
    ensemble = TowerEnsemble(behavior_tower=behav_tower)

    b = torch.randn(3, 5, 8)
    m = torch.ones(3, 5, dtype=torch.bool)

    scores = ensemble(b, m)
    assert scores.shape == (3,), f"输出 shape 应为 (3,), 收到 {scores.shape}"
    assert (scores >= 0).all() and (scores <= 1).all(), "分数应在 [0,1]"
    print(f"  ✓ test_tower_ensemble_forward (scores={scores.tolist()})")


def _test_matching_scorer_score():
    """TC2: MatchingScorer.score 基本评分"""
    if not TORCH_AVAILABLE:
        print("  ⚠ PyTorch 不可用, 跳过测试")
        return

    BT = _get_behavior_tower()
    behav_tower = BT(max_seq_len=5, feature_dim=8, hidden_dim=64)
    scorer = MatchingScorer(behav_tower)

    u = torch.randn(1, 4)
    e = torch.randn(1, 6)
    b = torch.randn(1, 5, 8)
    m = torch.ones(1, 5, dtype=torch.bool)

    score = scorer.score(u, e, b, m)
    assert isinstance(score, float), f"score 应为 float, 收到 {type(score)}"
    assert 0.0 <= score <= 1.0, f"score 应在 [0,1] 范围内, 收到 {score}"
    print(f"  ✓ test_matching_scorer_score (score={score:.6f})")


def _test_matching_scorer_no_behavior():
    """TC3: 无行为数据时的评分回退"""
    if not TORCH_AVAILABLE:
        print("  ⚠ PyTorch 不可用, 跳过测试")
        return

    BT = _get_behavior_tower()
    behav_tower = BT(max_seq_len=5, feature_dim=8, hidden_dim=64)
    scorer = MatchingScorer(behav_tower)

    u = torch.randn(1, 4)
    e = torch.randn(1, 6)

    score = scorer.score(u, e)
    assert isinstance(score, float), f"score 应为 float, 收到 {type(score)}"
    assert 0.0 <= score <= 1.0, f"score 应在 [0,1] 范围内, 收到 {score}"
    print(f"  ✓ test_matching_scorer_no_behavior (score={score:.6f})")


def _test_matching_scorer_forward():
    """TC4: MatchingScorer.forward 批量评分"""
    if not TORCH_AVAILABLE:
        print("  ⚠ PyTorch 不可用, 跳过测试")
        return

    BT = _get_behavior_tower()
    behav_tower = BT(max_seq_len=5, feature_dim=8, hidden_dim=64)
    scorer = MatchingScorer(behav_tower)

    B = 3
    u = torch.randn(B, 4)
    e = torch.randn(B, 6)
    b = torch.randn(B, 5, 8)
    m = torch.ones(B, 5, dtype=torch.bool)

    scores = scorer.forward(u, e, b, m)
    assert scores.shape == (B,), f"forward 输出 shape 应为 ({B},), 收到 {scores.shape}"
    assert (scores >= 0).all() and (scores <= 1).all(), "分数应在 [0,1]"
    print(f"  ✓ test_matching_scorer_forward (scores={scores.tolist()})")


def _test_online_weight_optimizer():
    """TC5: OnlineWeightOptimizer 权重更新"""
    opt = OnlineWeightOptimizer(lr=0.1)

    w0 = opt.get_weights()
    assert abs(w0["alpha"] - 0.5) < 0.01

    w1 = opt.update(
        sim_user_ent=0.9, sim_behavior_ent=0.3, sim_user_behavior=0.5, reward=1.0
    )
    assert opt.total_updates == 1
    assert all(0.05 <= v <= 0.9 for v in w1.values()), "权重应在范围内"
    assert abs(sum(w1.values()) - 1.0) < 0.01, "权重和应为 1"

    w2 = opt.update(
        sim_user_ent=0.2, sim_behavior_ent=0.8, sim_user_behavior=0.3, reward=-0.5
    )
    assert opt.total_updates == 2
    print(f"  ✓ test_online_weight_optimizer (w={w2})")


def _test_online_weight_reset():
    """TC6: 权重重置"""
    opt = OnlineWeightOptimizer()
    opt.update(sim_user_ent=0.5, sim_behavior_ent=0.5, sim_user_behavior=0.5, reward=1.0)
    opt.reset_weights()
    w = opt.get_weights()
    assert abs(w["alpha"] - 0.5) < 0.01
    assert abs(w["beta"] - 0.3) < 0.01
    assert abs(w["gamma"] - 0.2) < 0.01
    print("  ✓ test_online_weight_reset")


def _test_match_result_dataclass():
    """TC7: MatchResult 排序"""
    r1 = MatchResult(target_id=1, score=0.9)
    r2 = MatchResult(target_id=2, score=0.5)
    r3 = MatchResult(target_id=3, score=0.7)

    sorted_results = sorted([r1, r2, r3], reverse=True)
    assert sorted_results[0].score == 0.9
    assert sorted_results[1].score == 0.7
    assert sorted_results[2].score == 0.5
    print("  ✓ test_match_result_dataclass")


# ===================================================================
# 主入口
# ===================================================================
if __name__ == "__main__":
    print("=" * 60)
    print("  三塔集成评分推理 — 单元测试")
    print("=" * 60)
    print()

    tests = [
        ("TowerEnsemble 前向传播", _test_tower_ensemble_forward),
        ("MatchingScorer.score 基本评分", _test_matching_scorer_score),
        ("无行为数据评分回退", _test_matching_scorer_no_behavior),
        ("MatchingScorer.forward 批量评分", _test_matching_scorer_forward),
        ("OnlineWeightOptimizer 权重更新", _test_online_weight_optimizer),
        ("权重重置", _test_online_weight_reset),
        ("MatchResult 排序", _test_match_result_dataclass),
    ]

    passed = 0
    failed = 0
    for name, fn in tests:
        try:
            fn()
            passed += 1
        except Exception as e:
            print(f"  ✗ {name}: {e}")
            import traceback
            traceback.print_exc()
            failed += 1

    print()
    print("-" * 60)
    print(f"  结果: {passed} 通过, {failed} 失败, {len(tests)} 总计")
    if failed == 0:
        print("  ✓ 全部通过!")
    else:
        print("  ✗ 存在失败的测试!")
    print("=" * 60)
