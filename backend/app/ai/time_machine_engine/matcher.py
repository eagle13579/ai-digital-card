"""
出海时光机引擎 v3 — 环境相似度匹配引擎
========================================
核心算法：
  1. 取中国模式黄金期的环境快照（各维度均值）→ 作为"参考向量"
  2. 取目标国当前的环境参数（最近3年均值）→ 作为"候选向量"
  3. 归一化 + 加权相似度计算（欧氏距离的反向映射 + 方向修正）
  4. 输出 Top N 匹配国家 + 相似度分数

数学说明：
  每个维度先做 z-score 归一化（跨国家/年份），再计算加权欧氏距离。
  相似度 = 1 / (1 + 加权距离) ∈ (0, 1]，越大越相似。
  部分维度有方向偏好（如失业率越低越好），通过 direction 修正。
"""

import math

from .dimensions import DEFAULT_DIM_WEIGHTS, ENV_DIMENSIONS


class EnvironmentMatcher:
    """环境匹配引擎（支持绝对值和分位数两种模式）
    mode='percentile': 把每个维度值转为全球百分位再比较（发展阶段相似性）
    mode='absolute':   直接用原始值比较（原逻辑）
    """

    def __init__(self, dim_weights: dict | None = None, mode: str = "absolute"):
        self.dim_weights = dict(DEFAULT_DIM_WEIGHTS)
        if dim_weights:
            self.dim_weights.update(dim_weights)
        self.mode = mode

    # ── 归一化 ────────────────────────────────────────────

    @staticmethod
    def _zscore_normalize(values: dict[str, float]) -> dict[str, float]:
        """对 {维度: 值} 做 z-score 归一化（带方向修正已在取值处处理）"""
        if not values:
            return {}
        nums = [v for v in values.values() if v is not None]
        if len(nums) < 2:
            return {}
        mean = sum(nums) / len(nums)
        var = sum((v - mean) ** 2 for v in nums) / len(nums)
        std = math.sqrt(var) if var > 0 else 1.0
        return {k: (v - mean) / std if std else 0.0 for k, v in values.items()}

    # ── 相似度 ────────────────────────────────────────────

    def similarity(self, ref: dict, cand: dict) -> dict:
        """计算参考向量 vs 候选向量的加权相似度
        ref:  {dim_key: value}  中国黄金期快照
        cand: {dim_key: value}  目标国当前
        返回: {score, distance, dim_scores, dim_diffs, matched_dims}

        算法（absolute 模式）: 加权相对距离 + 指数映射
          rel_diff = (c - r) / max(|r|, 1)   # 相对偏差，无量纲
          direction=lower 时取反（该维度越低越贴近中国当年）
          距离 = sqrt(Σ w_i·rel_diff² / Σ w_i)
          相似度 = exp(-距离 / 0.35)          # 距离0.35 → 37%，区分度明显

        算法（percentile 模式）: 值已是 0-1 百分位，直接做差
          diff = c - r  (r/c ∈ [0,1])
          距离 = sqrt(Σ w_i·diff² / Σ w_i)
          相似度 = exp(-距离 / 0.15)          # 百分位差0.15 → 37%
        """
        # 只比双方都有数据的维度
        common = [k for k in ref if k in cand and ref[k] is not None and cand[k] is not None]
        if len(common) < 3:
            return {"score": 0.0, "distance": 9.9, "dim_scores": {},
                    "dim_diffs": {}, "matched_dims": len(common)}

        weights = {k: max(self.dim_weights.get(k, 1.0), 0.01) for k in common}
        wsum = sum(weights.values()) or 1.0

        diffs = {}
        dim_scores = {}
        dist_sq = 0.0
        is_pct = (self.mode == "percentile")
        scale = 0.15 if is_pct else 0.35
        for k in common:
            direction = ENV_DIMENSIONS.get(k, {}).get("direction", "higher")
            r, c = ref[k], cand[k]
            if is_pct:
                # 百分位直接差
                rel_diff = c - r
            else:
                # 相对偏差（无量纲），分母用参考值尺度
                base = max(abs(r), 1.0)
                rel_diff = (c - r) / base
                # 方向修正：direction=lower 时 c < r 表示"更友好"
                if direction == "lower":
                    rel_diff = -rel_diff
            # 维度得分: 偏差越小越接近 (指数衰减)
            dim_score = math.exp(-(rel_diff ** 2) / (2 * scale ** 2))
            dim_scores[k] = round(dim_score, 4)
            diffs[k] = round(rel_diff, 3)
            dist_sq += weights[k] * (rel_diff ** 2)

        distance = math.sqrt(dist_sq / wsum)
        score = math.exp(-distance / scale)
        return {
            "score": round(score, 4),
            "distance": round(distance, 4),
            "dim_scores": dim_scores,
            "dim_diffs": diffs,
            "matched_dims": len(common),
        }

    def rank_countries(self, ref_vector: dict, countries: dict[str, dict],
                       top_n: int = 15) -> list[dict]:
        """对一组国家排序
        ref_vector: {dim: value} 中国黄金期快照
        countries:  {iso3: {dim: value}} 各国当前环境
        返回: [{iso3, score, distance, dim_scores, matched_dims}]
        """
        results = []
        for iso3, cand in countries.items():
            sim = self.similarity(ref_vector, cand)
            if sim["matched_dims"] < 3:
                continue
            results.append({"iso3": iso3, **sim})
        results.sort(key=lambda x: x["score"], reverse=True)
        return results[:top_n]

    # ── 参考向量构建 ──────────────────────────────────────

    @staticmethod
    def build_ref_vector(country_avgs: dict[str, float | None]) -> dict[str, float]:
        """从 {dim: 均值} 构建参考向量（丢弃 None）"""
        return {k: v for k, v in country_avgs.items() if v is not None}

    @staticmethod
    def build_candidate_vector(country_avgs: dict[str, float | None]) -> dict[str, float]:
        """同上（候选向量）"""
        return {k: v for k, v in country_avgs.items() if v is not None}
