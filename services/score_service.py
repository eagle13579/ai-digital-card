
# ── [GBK Emoji 修复] 覆写 stdout/stderr 编码为 UTF-8 ──
# 修复 Windows 中文系统下 GBK 无法编码 Emoji 导致的崩溃
import sys
import io
sys.stdout.reconfigure(encoding='utf-8')
sys.stderr.reconfigure(encoding='utf-8')
# ── [修复结束] ──

"""
芯森态 · 评分服务层
封装 score_engine 调用，对接数据库
"""

import json
import logging
import uuid
from typing import Dict, List, Optional, Tuple

import pandas as pd

# 导入现有引擎 (保持原文件不变)
import sys
import os
_code_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__)))))
if _code_dir not in sys.path:
    sys.path.insert(0, _code_dir)

from data_processor import DataProcessor
from score_engine import ScoreEngine, DIMENSION_SCORERS, DIMENSION_WEIGHTS

from api.models.database import (
    get_grade_list,
    get_overview,
    get_city_heatmap,
    get_score_distribution,
    get_user_score,
    init_db,
    save_dealer_grades,
    save_scores,
    save_users,
    get_latest_scores,
)

logger = logging.getLogger("ScoreService")


def run_full_scoring(data_path: Optional[str] = None) -> Dict:
    """运行全量评分管道: 加载 → 评分 → 分级 → 入库

    Args:
        data_path: 自定义数据路径 (默认使用 demo_data.json)

    Returns:
        {
            "batch_id": str,
            "total_users": int,
            "grade_counts": dict,
            "summary": {...}
        }
    """
    batch_id = uuid.uuid4().hex[:12]

    # Step 1: 加载数据
    dp = DataProcessor(demo_mode=(data_path is None), data_path=data_path)
    features = dp.process()
    logger.info(f"特征矩阵加载完成: {features.shape}")

    # Step 2: 评分
    engine = ScoreEngine()
    full_scores = engine.compute(features)
    logger.info(f"评分完成: {len(full_scores)} 人")

    # Step 3: 保存用户基础信息到数据库
    users = []
    for _, row in features.iterrows():
        users.append(row.to_dict())
    save_users(users)

    # Step 4: 保存评分结果
    score_records = []
    for _, row in full_scores.iterrows():
        record = row.to_dict()
        score_records.append(record)
    save_scores(score_records, batch_id)

    # Step 5: 生成并保存分级结果
    a_profiles = engine.generate_a_profile("A")
    b_scripts = engine.generate_b_script()

    dealer_records = []
    if not a_profiles.empty:
        for _, row in a_profiles.iterrows():
            # 为A级生成个性化话术
            uid = row.get("user_id", "")
            nickname = row.get("nickname", uid)
            city = row.get("city", "该城市")
            total = row.get("total_score", 90)
            strength = row.get("核心优势", "")
            weakness = row.get("待提升", "")
            tags = row.get("标签", "")

            # 从核心优势/待提升中提取top维度
            # 核心优势格式: "活跃度(100分)、内容共鸣(100分)、影响力(100分)"
            top_dims_text = strength[:60] if strength else "综合表现"
            weak_dims_text = weakness[:40] if weakness else ""

            a_script = (
                f"【🔥 A级铁粉·{nickname}专属话术】\n"
                f"{nickname}您好，我是芯森态招商顾问。看到您在{city}社群中"
                f"的{top_dims_text}表现非常突出，"
                f"综合评分{total}分，与我们的经销商画像高度匹配。\n"
                f"{'尤其' + weak_dims_text + '方面还有很大提升空间，我们可以帮您优化。' if weak_dims_text else ''}"
                f"诚邀您参加本月的「城市合伙人」闭门选商会，了解新材料功能服饰万亿市场机遇。"
                f"您这周哪天方便？"
            )

            dealer_records.append({
                "user_id": uid,
                "grade": "A",
                "profile_json": json.dumps(row.to_dict(), ensure_ascii=False, default=str),
                "script_text": a_script,
            })
    if not b_scripts.empty:
        for _, row in b_scripts.iterrows():
            dealer_records.append({
                "user_id": row.get("user_id", ""),
                "grade": "B",
                "profile_json": "{}",
                "script_text": row.get("个性化话术", ""),
            })

    # C级也记录
    c_mask = full_scores["grade"] == "C"
    for _, row in full_scores[c_mask].iterrows():
        dealer_records.append({
            "user_id": row.get("user_id", ""),
            "grade": "C",
            "profile_json": "{}",
            "script_text": "",
        })

    if dealer_records:
        save_dealer_grades(dealer_records, batch_id)

    # Step 6: 返回摘要
    grade_counts = full_scores["grade"].value_counts().to_dict()
    grade_counts = {str(k): int(v) for k, v in grade_counts.items()}

    return {
        "batch_id": batch_id,
        "total_users": len(full_scores),
        "grade_counts": grade_counts,
        "avg_score": round(float(full_scores["total_score"].mean()), 1),
        "max_score": round(float(full_scores["total_score"].max()), 1),
        "min_score": round(float(full_scores["total_score"].min()), 1),
    }


def get_user_detail(user_id: str) -> Optional[Dict]:
    """获取单用户评分详情"""
    return get_user_score(user_id)


def get_dealers_by_grade(grade: str) -> List[Dict]:
    """按等级获取经销商列表"""
    return get_grade_list(grade)


def get_dashboard_overview() -> Dict:
    """获取看板总览数据"""
    return get_overview()


def get_heatmap_data() -> List[Dict]:
    """获取城市热力数据"""
    return get_city_heatmap()


def get_distribution() -> Dict:
    """获取评分分布"""
    return get_score_distribution()
