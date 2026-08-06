"""芯森态 · 评分解释引擎
为每条评分提供维度贡献分析和可读性解释
"""
import logging
from typing import Dict, List

logger = logging.getLogger("ScoreExplainer")

# 六维权重配置
DIMENSION_WEIGHTS = {
    "score_活跃度": 0.25,
    "score_购买力": 0.20,
    "score_内容共鸣": 0.20,
    "score_影响力": 0.15,
    "score_城市匹配": 0.10,
    "score_信任度": 0.10,
}

DIMENSION_NAMES_CN = {
    "score_活跃度": "活跃度",
    "score_购买力": "购买力",
    "score_内容共鸣": "内容共鸣",
    "score_影响力": "影响力",
    "score_城市匹配": "城市匹配",
    "score_信任度": "信任度",
}


def explain_score(score_row: Dict) -> Dict:
    """解析单条评分，生成维度贡献解释
    
    Args:
        score_row: 包含所有score_*字段的评分字典
    
    Returns:
        {
            "total_score": float,
            "grade": str,
            "dimensions": [{ "name": str, "score": float, "weight": float, "contribution": float }],
            "top3_positive": [str],
            "summary": str,
        }
    """
    total = score_row.get("total_score", 0)
    if total == 0:
        return {"total_score": 0, "grade": "D", "dimensions": [], "top3_positive": [], "summary": "无评分数据"}
    
    dimensions = []
    contributions = []
    
    for key, weight in DIMENSION_WEIGHTS.items():
        raw_score = score_row.get(key, 0)
        # 贡献率 = 维度分 * 权重 / 总分 * 100
        contribution = round(raw_score * weight / total * 100, 1)
        dimensions.append({
            "name": DIMENSION_NAMES_CN.get(key, key),
            "score": raw_score,
            "weight": weight,
            "contribution": contribution,
        })
        contributions.append((DIMENSION_NAMES_CN.get(key, key), contribution))
    
    # Top3 贡献维度
    contributions.sort(key=lambda x: x[1], reverse=True)
    top3 = [c[0] for c in contributions[:3]]
    
    # 自然语言摘要
    top1 = contributions[0]
    summary = f"总分{total}分，{top1[0]}贡献最高({top1[1]}%)"
    if len(contributions) > 1:
        summary += f"，其次{contributions[1][0]}({contributions[1][1]}%)"
    
    return {
        "total_score": total,
        "grade": score_row.get("grade", "D"),
        "dimensions": sorted(dimensions, key=lambda x: x["contribution"], reverse=True),
        "top3_positive": top3,
        "summary": summary,
    }


def batch_explain(scores: List[Dict]) -> List[Dict]:
    """批量评分解释"""
    return [explain_score(s) for s in scores]
