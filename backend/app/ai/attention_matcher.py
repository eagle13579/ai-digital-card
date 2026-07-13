"""
Attention Matcher — 多头注意力匹配引擎
========================================
四头注意力机制，分别从行业、能力、地区、热度四个维度衡量用户匹配度。

与Transformer的映射:
  Token Embedding  → 各头的特征稀疏向量
  Q·K^T/√d         → 需求-能力相关性评分 (每头独立计算)
  softmax           → 注意力权重归一化 (每头独立计算)
  Σ(alpha·V)       → 各头加权融合 → 综合匹配度

评分公式:
  final_score = Σ(head_weight * head_attention_score)
  其中 head_weight = [行业:0.30, 能力:0.35, 地区:0.20, 热度:0.15]
"""

import math
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

# ── 四头注意力权重系数 ────────────────────────────────────────────────
HEAD_WEIGHTS: Dict[str, float] = {
    "industry": 0.30,
    "capability": 0.35,
    "region": 0.20,
    "hotness": 0.15,
}


def softmax(scores: List[float], temperature: float = 1.0) -> List[float]:
    """softmax归一化 — Transformer的softmax(QK^T/√d)

    Args:
        scores: 原始分数列表
        temperature: 温度系数，>1 使分布更平滑，<1 使分布更尖锐

    Returns:
        归一化后的概率分布
    """
    if not scores:
        return []
    if temperature <= 0:
        temperature = 1.0
    scaled = [s / temperature for s in scores]
    max_s = max(scaled)
    exps = [math.exp(s - max_s) for s in scaled]
    total = sum(exps)
    return [e / total for e in exps]


@dataclass
class UserFeatures:
    """用户特征数据 — 四个注意力头的输入

    Attributes:
        industries:   行业标签列表 (行业头)
        capabilities: 能力/技能标签列表 (能力头)
        regions:      地区/位置标签列表 (地区头)
        hotness:      热度/活跃度得分, 范围 [0,1] (热度头)
        load:         当前负载/任务数, 用于可用性计算
        max_load:     最大负载上限
    """
    industries: List[str] = field(default_factory=list)
    capabilities: List[str] = field(default_factory=list)
    regions: List[str] = field(default_factory=list)
    hotness: float = 0.0
    load: int = 0
    max_load: int = 10


class AttentionMatcher:
    """多头注意力匹配引擎

    四头注意力:
      1. 行业头 (industry)   — 行业标签相似度, 权重 0.30
      2. 能力头 (capability) — 能力/技能标签相似度, 权重 0.35
      3. 地区头 (region)     — 地区/位置匹配度, 权重 0.20
      4. 热度头 (hotness)    — 热度/活跃度编码, 权重 0.15

    Usage:
        matcher = AttentionMatcher()
        score = await matcher.score(user_features, candidate_features)
        scores = await matcher.batch_score(user_features, candidates)
        details = await matcher.explain(user_features, candidate_features)
    """

    def __init__(self, temperature: float = 0.8):
        """初始化注意力匹配引擎

        Args:
            temperature: softmax温度系数, 默认0.8
        """
        self.temperature = temperature
        # 各头的词表 (feature -> index)
        self._vocab: dict[str, dict[str, int]] = {
            "industry": {},
            "capability": {},
            "region": {},
        }
        # 各头的嵌入维度
        self._dims: dict[str, int] = {
            "industry": 0,
            "capability": 0,
            "region": 0,
        }
        self._sqrt_dims: dict[str, float] = {
            "industry": 1.0,
            "capability": 1.0,
            "region": 1.0,
        }

    # ── 词表管理 ─────────────────────────────────────────────────────

    def register_features(self, head: str, features: List[str]) -> None:
        """注册/扩展指定头的特征词表

        Args:
            head: 头名称, 可选 'industry' / 'capability' / 'region'
            features: 待注册的特征标签列表
        """
        if head not in self._vocab:
            return
        for feat in features:
            if feat not in self._vocab[head]:
                self._vocab[head][feat] = len(self._vocab[head])
        self._dims[head] = len(self._vocab[head])
        self._sqrt_dims[head] = math.sqrt(self._dims[head]) if self._dims[head] > 0 else 1.0

    # ── 向量化 ───────────────────────────────────────────────────────

    def _vectorize(self, head: str, items: List[str]) -> List[float]:
        """将特征列表编码为稀疏向量 (Token Embedding)

        Args:
            head: 头名称
            items: 特征标签列表

        Returns:
            稀疏向量, 维度 = 词表大小
        """
        vec = [0.0] * self._dims[head]
        for item in items:
            if item in self._vocab[head]:
                vec[self._vocab[head][item]] = 1.0
        return vec

    def _dot_product(self, a: List[float], b: List[float]) -> float:
        """向量点积 — Q·K^T"""
        return sum(x * y for x, y in zip(a, b))

    # ── 各头评分 ─────────────────────────────────────────────────────

    def _score_head(
        self,
        head: str,
        query_features: List[str],
        candidate_features: List[str],
    ) -> float:
        """计算单头注意力评分: softmax(Q·K^T/√d)

        Args:
            head: 头名称
            query_features: 查询方特征
            candidate_features: 候选方特征

        Returns:
            单头注意力权重 [0, 1]
        """
        # 确保词表覆盖双方特征
        self.register_features(head, query_features)
        self.register_features(head, candidate_features)

        q_vec = self._vectorize(head, query_features)
        k_vec = self._vectorize(head, candidate_features)
        dot = self._dot_product(q_vec, k_vec)
        scaled = dot / self._sqrt_dims[head]
        # 使用 sigmoid-like 归一化到 [0, 1]
        return 1.0 / (1.0 + math.exp(-scaled))

    def _score_hotness_head(
        self,
        query_hotness: float,
        candidate_hotness: float,
    ) -> float:
        """热度头评分 — 热度互补匹配

        热度越高 = 越活跃, 但高热度用户对低热度用户的吸引力递减。
        使用互补公式: 1 - |query_hotness - candidate_hotness|

        Args:
            query_hotness: 查询方热度 [0, 1]
            candidate_hotness: 候选方热度 [0, 1]

        Returns:
            热度匹配度 [0, 1]
        """
        diff = abs(query_hotness - candidate_hotness)
        return 1.0 - diff

    # ── 可用性计算 ───────────────────────────────────────────────────

    def _availability(self, load: int, max_load: int) -> float:
        """计算可用性 — V (Value) 在 Transformer 中对应负载感知

        Args:
            load: 当前负载
            max_load: 最大负载

        Returns:
            可用性 [0, 1]
        """
        return max(0.0, 1.0 - load / max_load) if max_load > 0 else 1.0

    # ── 公共接口 ─────────────────────────────────────────────────────

    async def score(
        self,
        user_features: UserFeatures,
        candidate_features: UserFeatures,
    ) -> float:
        """计算用户和候选用户的综合匹配度

        四头注意力加权:
          score = Σ(head_weight * head_attention) * availability

        Args:
            user_features:     用户特征 (Q)
            candidate_features: 候选特征 (K)

        Returns:
            综合匹配度 [0, 1]
        """
        # 各头注意力得分
        industry_score = self._score_head(
            "industry", user_features.industries, candidate_features.industries,
        )
        capability_score = self._score_head(
            "capability", user_features.capabilities, candidate_features.capabilities,
        )
        region_score = self._score_head(
            "region", user_features.regions, candidate_features.regions,
        )
        hotness_score = self._score_hotness_head(
            user_features.hotness, candidate_features.hotness,
        )

        # 加权融合
        weighted_sum = (
            HEAD_WEIGHTS["industry"] * industry_score
            + HEAD_WEIGHTS["capability"] * capability_score
            + HEAD_WEIGHTS["region"] * region_score
            + HEAD_WEIGHTS["hotness"] * hotness_score
        )

        # 可用性调节 (双方负载综合)
        avail_a = self._availability(user_features.load, user_features.max_load)
        avail_b = self._availability(candidate_features.load, candidate_features.max_load)
        combined_avail = (avail_a + avail_b) / 2.0

        return round(weighted_sum * combined_avail, 4)

    async def batch_score(
        self,
        user_features: UserFeatures,
        candidates: List[UserFeatures],
    ) -> List[float]:
        """批量评分 — 对一组候选特征计算匹配度

        Args:
            user_features: 用户特征 (Q)
            candidates:    候选特征列表 (K)

        Returns:
            匹配度分数列表, 顺序与 candidates 一致
        """
        scores = []
        for cand in candidates:
            s = await self.score(user_features, cand)
            scores.append(s)
        return scores

    async def explain(
        self,
        user_a: UserFeatures,
        user_b: UserFeatures,
    ) -> Dict[str, Any]:
        """解释两个用户之间的匹配结果 — 返回每头注意力权重

        Args:
            user_a: 用户A特征
            user_b: 用户B特征

        Returns:
            {
                "score": 综合匹配度,
                "details": {
                    "industry":   { "attention": 0.xx, "weight": 0.30, "contribution": 0.xx },
                    "capability": { "attention": 0.xx, "weight": 0.35, "contribution": 0.xx },
                    "region":     { "attention": 0.xx, "weight": 0.20, "contribution": 0.xx },
                    "hotness":    { "attention": 0.xx, "weight": 0.15, "contribution": 0.xx },
                },
                "availability": 0.xx,
                "features": {
                    "user_a": { "industries": [...], "capabilities": [...], "regions": [...], "hotness": x },
                    "user_b": { "industries": [...], "capabilities": [...], "regions": [...], "hotness": x },
                }
            }
        """
        # 各头注意力得分
        industry_score = self._score_head(
            "industry", user_a.industries, user_b.industries,
        )
        capability_score = self._score_head(
            "capability", user_a.capabilities, user_b.capabilities,
        )
        region_score = self._score_head(
            "region", user_a.regions, user_b.regions,
        )
        hotness_score = self._score_hotness_head(
            user_a.hotness, user_b.hotness,
        )

        # 可用性
        avail_a = self._availability(user_a.load, user_a.max_load)
        avail_b = self._availability(user_b.load, user_b.max_load)
        combined_avail = (avail_a + avail_b) / 2.0

        # 各头贡献
        contributions = {}
        head_scores = {
            "industry": industry_score,
            "capability": capability_score,
            "region": region_score,
            "hotness": hotness_score,
        }
        weighted_sum = 0.0
        for head_name, head_score in head_scores.items():
            weight = HEAD_WEIGHTS[head_name]
            contribution = head_score * weight
            weighted_sum += contribution
            contributions[head_name] = {
                "attention": round(head_score, 4),
                "weight": weight,
                "contribution": round(contribution, 4),
            }

        final_score = round(weighted_sum * combined_avail, 4)

        return {
            "score": final_score,
            "details": contributions,
            "availability": round(combined_avail, 4),
            "features": {
                "user_a": {
                    "industries": user_a.industries,
                    "capabilities": user_a.capabilities,
                    "regions": user_a.regions,
                    "hotness": user_a.hotness,
                },
                "user_b": {
                    "industries": user_b.industries,
                    "capabilities": user_b.capabilities,
                    "regions": user_b.regions,
                    "hotness": user_b.hotness,
                },
            },
        }


# ========== 使用示例 ==========
if __name__ == "__main__":
    import asyncio

    async def demo():
        print("=" * 60)
        print("  Attention Matcher Demo — 四头注意力")
        print("  Q=需求特征  K=候选特征  V=可用性")
        print("  Attention = softmax(Q·K^T/√d) · V")
        print("=" * 60)

        matcher = AttentionMatcher()

        # 用户A: 需要AI+出海+SaaS服务的企业家
        user_a = UserFeatures(
            industries=["科技", "互联网", "saas"],
            capabilities=["ai", "机器学习", "产品设计"],
            regions=["北京", "上海"],
            hotness=0.7,
            load=3,
            max_load=10,
        )

        # 用户B: 提供AI技术+电商出海能力的服务商
        user_b = UserFeatures(
            industries=["科技", "电商", "ai"],
            capabilities=["ai", "深度学习", "跨境运营"],
            regions=["深圳", "上海"],
            hotness=0.5,
            load=2,
            max_load=10,
        )

        score = await matcher.score(user_a, user_b)
        print(f"\n📊 综合匹配度: {score:.4f}")

        details = await matcher.explain(user_a, user_b)
        print(f"\n🔍 匹配详情:")
        print(f"  {'头名称':12s} {'注意力':10s} {'权重':8s} {'贡献':10s}")
        print(f"  {'─' * 42}")
        for head_name, info in details["details"].items():
            print(f"  {head_name:12s} {info['attention']:.4f}    {info['weight']:.2f}    {info['contribution']:.4f}")
        print(f"\n  可用性: {details['availability']:.4f}")
        print(f"  综合分: {details['score']:.4f}")

        # 批量评分
        candidates = [
            UserFeatures(
                industries=["教育", "培训"],
                capabilities=["ai", "nlp"],
                regions=["北京"],
                hotness=0.3,
                load=5,
            ),
            UserFeatures(
                industries=["金融", "科技"],
                capabilities=["区块链", "ai"],
                regions=["上海"],
                hotness=0.8,
                load=1,
            ),
        ]
        batch_scores = await matcher.batch_score(user_a, candidates)
        print(f"\n📦 批量评分:")
        for i, s in enumerate(batch_scores):
            print(f"  候选{i + 1}: {s:.4f}")

    asyncio.run(demo())
