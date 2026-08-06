"""芯森态 · Negative Scoring 评分管道集成
在score_engine评分前插入排除门禁过滤低质线索
"""
import logging
from typing import Dict, List, Optional

logger = logging.getLogger("ExclusionIntegrator")


def apply_exclusion_gate(features_df, exclusion_gate=None):
    """在评分前执行排除门禁
    
    Args:
        features_df: pandas DataFrame, 包含用户特征
        exclusion_gate: ExclusionGate实例, None则自动创建
    
    Returns:
        (passed_df, excluded_records):
            passed_df - 通过排除门禁的用户(可进入评分)
            excluded_records - 被排除的用户及原因
    """
    from api.services.exclusion_gate import ExclusionGate
    
    gate = exclusion_gate or ExclusionGate()
    
    import pandas as pd
    passed_rows = []
    excluded = []
    
    for idx, row in features_df.iterrows():
        user_data = row.to_dict()
        result = gate.evaluate(user_data)
        
        if result["excluded"]:
            excluded.append({
                "user_id": user_data.get("user_id", f"row_{idx}"),
                "nickname": user_data.get("nickname", ""),
                "reason": "硬排除",
                "triggers": result["triggers"],
                "details": result["details"],
            })
            logger.info(f"  排除: {user_data.get('nickname','')} - {result['triggers']}")
        elif result["penalty"] > 0:
            # Soft排除 - 扣分后进入评分
            modified = dict(user_data)
            passed_rows.append(modified)
            logger.info(f"  扣分: {user_data.get('nickname','')} -{result['penalty']}分")
        else:
            passed_rows.append(dict(user_data))
    
    if passed_rows:
        passed_df = pd.DataFrame(passed_rows)
    else:
        passed_df = pd.DataFrame()
    
    return passed_df, excluded


def get_exclusion_summary(excluded_records: List[Dict]) -> Dict:
    """生成排除摘要"""
    total = len(excluded_records)
    by_rule = {}
    for rec in excluded_records:
        for trigger in rec.get("triggers", []):
            by_rule[trigger] = by_rule.get(trigger, 0) + 1
    
    return {
        "total_excluded": total,
        "by_rule": by_rule,
        "excluded_users": [
            {"user_id": r["user_id"], "nickname": r["nickname"], "reason": r["reason"]}
            for r in excluded_records
        ],
    }
