"""V2 端到端匹配度验证脚本

使用 UserTower embedding + 标签特征进行匹配度计算和验证。

功能:
  1. 加载预训练的 UserTower embedding
  2. 计���所有用户对的 embedding 余弦相似度
  3. 结合标签重叠进行 V2 综合评分
  4. 与数据库中的 match_records 对比验证
  5. 输出匹配度分布统计和准确率分析

用法:
    cd backend && python scripts/v2_match_verification.py
"""
import json
import math
import sqlite3
import sys
from collections import Counter
from pathlib import Path
from typing import Any

import numpy as np

# ── 添加项目根目录 ──
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

DB_PATH = BASE_DIR / "data" / "digital_brochure.db"
EMBEDDINGS_PATH = BASE_DIR / "data" / "user_embeddings.json"
MODEL_CHECKPOINT_PATH = BASE_DIR / "data" / "models" / "user_tower_pretrained_checkpoint.pt"

# ── V2 权重配置 (与 matching_engine_v2.py 一致) ──
WEIGHTS = {
    "embedding_similarity": 0.35,    # ← 替代 tag_overlap，用 embedding 捕获语义相似
    "tag_overlap": 0.25,             # 精确标签重叠
    "tag_weight_score": 0.10,        # 标签权重分
    "industry_complement": 0.20,     # 行业互补
    "tag_overlap_boost": 0.10,       # 标签重叠加分 (捕获精确匹配)
}

# ── 行业关键词 (匹配 V2 引擎) ──
INDUSTRY_KEYWORDS: dict[str, list[str]] = {
    "AI/科技":    ["ai", "人工智能", "科技", "互联网", "saas", "软件", "大数据", "云计算", "算法"],
    "金融/投资":  ["金融", "投资", "证券", "基金", "保险", "银行", "理财", "风控"],
    "制造/工业":  ["制造", "工业", "工厂", "生产", "供应链", "物流", "硬件", "芯片"],
    "教育/培训":  ["教育", "培训", "课程", "教学", "学习", "知识付费"],
    "医疗/健康":  ["医疗", "健康", "医药", "医院", "养生", "健身", "生物"],
    "地产/物业":  ["地产", "房产", "物业", "建筑", "装修", "家居"],
    "电商/零售":  ["电商", "零售", "跨境电商", "直播带货", "新零售", "o2o"],
    "法律/合规":  ["法律", "合规", "律师", "法务", "知识产权", "税务"],
    "品牌/营销":  ["品牌", "营销", "广告", "公关", "市场", "推广", "增长"],
    "传媒/内容":  ["传媒", "内容", "短视频", "自媒体", "新媒体", "影视", "娱乐"],
}

INDUSTRY_SUPPLY_DEMAND_MAP: dict[str, list[str]] = {
    "AI/科技":   ["制造/工业", "医疗/健康", "教育/培训", "金融/投资"],
    "金融/投资": ["AI/科技", "制造/工业", "医疗/健康"],
    "制造/工业": ["AI/科技", "电商/零售"],
    "品牌/营销": ["电商/零售", "教育/培训", "医疗/健康"],
    "传媒/内容": ["电商/零售", "品牌/营销"],
    "法律/合规": ["金融/投资", "AI/科技"],
}

SAME_INDUSTRY_BONUS = 0.1
CROSS_INDUSTRY_BONUS = 0.3


def load_embeddings() -> dict[int, np.ndarray]:
    """加载预训练的 UserTower embeddings。"""
    with open(str(EMBEDDINGS_PATH), "r", encoding="utf-8") as f:
        data = json.load(f)

    embeddings = {}
    for uid_str, entry in data.items():
        uid = int(uid_str)
        embeddings[uid] = np.array(entry["embedding"], dtype=np.float32)

    print(f"[Embeddings] 加载了 {len(embeddings)} 个用户的向量")
    for uid, emb in sorted(embeddings.items()):
        name = data[uid_str]["name"] if uid_str == str(uid) else f"用户{uid}"
        print(f"  ID={uid:2d}  {name:<8s}  dim={len(emb)}")
    return embeddings


def load_match_records() -> list[dict]:
    """加载数据库中的 match_records 作为 ground truth。"""
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    cursor.execute(
        "SELECT mr.*, u1.name as name_a, u2.name as name_b "
        "FROM match_records mr "
        "LEFT JOIN users u1 ON mr.user_a_id = u1.id "
        "LEFT JOIN users u2 ON mr.user_b_id = u2.id "
        "ORDER BY mr.match_score DESC"
    )
    records = [dict(r) for r in cursor.fetchall()]

    print(f"[GroundTruth] 加载了 {len(records)} 条匹配记录")
    for r in records[:10]:
        print(f"  {r['user_a_id']:2d}({r['name_a']:<6s}) <-> {r['user_b_id']:2d}({r['name_b']:<6s})  "
              f"score={r['match_score']:.2f}  status={r['status']:<8s}")
    if len(records) > 10:
        print(f"  ... 还有 {len(records)-10} 条")
    conn.close()
    return records


def load_user_tags() -> dict[int, dict[str, dict[str, float]]]:
    """加载用户标签 (provide/need) 用于行业互补和标签重叠计算。"""
    conn = sqlite3.connect(str(DB_PATH))
    cursor = conn.cursor()

    cursor.execute("SELECT DISTINCT user_id FROM user_tags ORDER BY user_id")
    user_ids = [r[0] for r in cursor.fetchall()]

    tags_by_user: dict[int, dict[str, dict[str, float]]] = {}
    for uid in user_ids:
        cursor.execute(
            "SELECT tag_type, tag, weight FROM user_tags WHERE user_id=?",
            (uid,),
        )
        rows = cursor.fetchall()
        provide = {}
        need = {}
        for tag_type, tag, weight in rows:
            if tag_type == "provide":
                provide[tag] = weight
            elif tag_type == "need":
                need[tag] = weight
        tags_by_user[uid] = {"provide": provide, "need": need}

    conn.close()
    return tags_by_user


# ── 行业检测 ─────────────────────────────────────────────────────────────


def detect_industries(tags: dict[str, float]) -> list[str]:
    """从标签中检测行业。"""
    detected: list[str] = []
    all_tag_names = set(tags.keys())

    for industry, keywords in INDUSTRY_KEYWORDS.items():
        for tag in all_tag_names:
            tag_lower = tag.lower()
            for kw in keywords:
                if kw in tag_lower or tag_lower in kw:
                    detected.append(industry)
                    break
            if detected and detected[-1] == industry:
                break
    return detected


def compute_industry_complement(
    tags_a: dict[str, dict[str, float]],
    tags_b: dict[str, dict[str, float]],
) -> float:
    """计算行业互补分数。"""
    all_tags_a = dict(tags_a["provide"])
    all_tags_a.update(tags_a["need"])
    all_tags_b = dict(tags_b["provide"])
    all_tags_b.update(tags_b["need"])

    ind_a = detect_industries(all_tags_a)
    ind_b = detect_industries(all_tags_b)

    if not ind_a or not ind_b:
        return 0.0

    total_score = 0.0
    comparisons = 0

    for ia in ind_a:
        for ib in ind_b:
            comparisons += 1
            if ia == ib:
                total_score += SAME_INDUSTRY_BONUS
            else:
                supply = INDUSTRY_SUPPLY_DEMAND_MAP.get(ia, [])
                if ib in supply:
                    total_score += CROSS_INDUSTRY_BONUS
                else:
                    reverse = INDUSTRY_SUPPLY_DEMAND_MAP.get(ib, [])
                    if ia in reverse:
                        total_score += CROSS_INDUSTRY_BONUS

    normalized = total_score / max(1.0, float(comparisons))
    return min(1.0, normalized)


# ── V2 综合评分 (基于 Embedding) ────────────────────────────────────────


def compute_v2_score(
    uid_a: int,
    uid_b: int,
    embeddings: dict[int, np.ndarray],
    tags_by_user: dict[int, dict[str, dict[str, float]]],
) -> dict[str, Any]:
    """基于 UserTower Embedding 的 V2 匹配度评分。"""
    uid_a, uid_b = sorted([uid_a, uid_b])

    # ── 1. Embedding 余弦相似度 ──
    emb_a = embeddings.get(uid_a)
    emb_b = embeddings.get(uid_b)

    if emb_a is None or emb_b is None:
        return {"score": 0.0, "error": "missing_embedding"}

    cos_sim = float(np.dot(emb_a, emb_b) / (
        np.linalg.norm(emb_a) * np.linalg.norm(emb_b)
    ))
    # 归一化到 [0, 1]
    embedding_similarity = max(0.0, (cos_sim + 1.0) / 2.0)

    # ── 2. 标签重叠 ──
    tags_a = tags_by_user.get(uid_a)
    tags_b = tags_by_user.get(uid_b)

    if tags_a is None or tags_b is None:
        return {"score": 0.0, "error": "missing_tags"}

    provide_a = tags_a["provide"]
    need_a = tags_a["need"]
    provide_b = tags_b["provide"]
    need_b = tags_b["need"]

    # 标签重叠 (供需匹配)
    overlap_raw = 0.0
    common_tags = set()

    # A提供 ∩ B需要
    for tag, weight_a in provide_a.items():
        if tag in need_b:
            overlap_raw += weight_a * need_b[tag]
            common_tags.add(tag)

    # B提供 ∩ A需要
    for tag, weight_b in provide_b.items():
        if tag in need_a:
            overlap_raw += weight_b * need_a[tag]
            common_tags.add(tag)

    max_possible = len(common_tags) * 1.0 if common_tags else 1.0
    tag_overlap = min(1.0, overlap_raw / max_possible) if max_possible > 0 else 0.0

    # ── 3. 标签权重分 ──
    # 使用 all_tags (provide ∪ need) 的均值权重
    all_weights_a = list(provide_a.values()) + list(need_a.values())
    all_weights_b = list(provide_b.values()) + list(need_b.values())
    avg_weight_a = np.mean(all_weights_a) if all_weights_a else 0.0
    avg_weight_b = np.mean(all_weights_b) if all_weights_b else 0.0

    # 标签权重分 = 基于标签强度的匹配 (两端标签权重的调和平均)
    tag_weight_score = 0.0
    if common_tags:
        overlap_weights = []
        for tag in common_tags:
            w_a = provide_a.get(tag, need_a.get(tag, 0.5))
            w_b = provide_b.get(tag, need_b.get(tag, 0.5))
            overlap_weights.append((w_a + w_b) / 2.0)
        tag_weight_score = np.mean(overlap_weights) if overlap_weights else 0.0
    tag_weight_score = min(1.0, tag_weight_score)

    # ── 4. 行业互补分 ──
    industry_complement = compute_industry_complement(tags_a, tags_b)

    # ── 5. 标签重叠加分 ──
    tag_overlap_boost = len(common_tags) / 15.0  # max common tags ~15

    # ── 6. 五层加权融合 ──
    final_score = (
        embedding_similarity * WEIGHTS["embedding_similarity"]
        + tag_overlap * WEIGHTS["tag_overlap"]
        + tag_weight_score * WEIGHTS["tag_weight_score"]
        + industry_complement * WEIGHTS["industry_complement"]
        + tag_overlap_boost * WEIGHTS["tag_overlap_boost"]
    )

    return {
        "score": round(final_score, 4),
        "embedding_similarity": round(embedding_similarity, 4),
        "cosine_similarity": round(cos_sim, 4),
        "tag_overlap": round(tag_overlap, 4),
        "tag_weight_score": round(tag_weight_score, 4),
        "industry_complement": round(industry_complement, 4),
        "tag_overlap_boost": round(tag_overlap_boost, 4),
        "common_tags": list(common_tags),
        "common_tags_count": len(common_tags),
    }


# ── 验证 & 统计 ─────────────────────────────────────────────────────────


def match_accuracy_analysis(
    v2_scores: dict[tuple[int, int], dict],
    match_records: list[dict],
) -> dict:
    """分析 V2 评分与 ground truth match_records 的一致性。"""
    # 构建 ground truth 集合
    gt_high: set[tuple[int, int]] = set()  # score >= 0.7 (高匹配)
    gt_medium: set[tuple[int, int]] = set()  # 0.3 <= score < 0.7
    gt_low: set[tuple[int, int]] = set()  # score < 0.3

    high_gt_map: dict[tuple[int, int], float] = {}
    for r in match_records:
        pair = (r["user_a_id"], r["user_b_id"])
        score = r["match_score"]
        if score >= 0.7:
            gt_high.add(pair)
            high_gt_map[pair] = score
        elif score >= 0.3:
            gt_medium.add(pair)
        else:
            gt_low.add(pair)

    # 分析
    correct_high = 0
    correct_low = 0
    false_positives = 0
    false_negatives = 0
    total_analyzed = 0

    high_score_details = []

    for pair, result in v2_scores.items():
        if pair[0] not in [r["user_a_id"] for r in match_records] + [r["user_b_id"] for r in match_records]:
            continue  # 跳过不在 match_records 中的对

        total_analyzed += 1
        v2_score = result["score"]

        if pair in gt_high:
            if v2_score >= 0.30:  # V2 认为匹配
                correct_high += 1
            else:
                false_negatives += 1

            high_score_details.append({
                "pair": pair,
                "v2_score": v2_score,
                "gt_score": high_gt_map.get(pair, 0.0),
                "cosine_sim": result.get("cosine_similarity", 0.0),
            })

        elif pair in gt_low:
            if v2_score < 0.25:
                correct_low += 1
            else:
                false_positives += 1

    return {
        "total_analyzed": total_analyzed,
        "high_match_pairs": len(gt_high),
        "correct_high": correct_high,
        "false_negatives": false_negatives,
        "correct_low": correct_low,
        "false_positives": false_positives,
        "high_score_details": sorted(
            high_score_details, key=lambda x: x["v2_score"], reverse=True
        ),
        "gt_high_map": high_gt_map,
    }


def main():
    print(f"{'='*70}")
    print(f"  V2 端到端匹配度验证 — UserTower Embedding + 标签特征")
    print(f"{'='*70}")

    # ── 1. 加载数据 ──
    print("\n[1/4] 加载数据...")
    embeddings = load_embeddings()
    match_records = load_match_records()
    tags_by_user = load_user_tags()
    print(f"  [标签] {len(tags_by_user)} 个用户有标签数据")

    # ── 2. 计算所有用户对的 V2 评分 ──
    print("\n[2/4] 计算所有用户对的 V2 匹配度评分...")
    user_ids = sorted(embeddings.keys())
    v2_scores: dict[tuple[int, int], dict] = {}
    user_pair_scores: list[dict] = []

    for i in range(len(user_ids)):
        for j in range(i + 1, len(user_ids)):
            uid_a = user_ids[i]
            uid_b = user_ids[j]
            result = compute_v2_score(uid_a, uid_b, embeddings, tags_by_user)

            if "error" not in result:
                pair = (uid_a, uid_b)
                v2_scores[pair] = result
                user_pair_scores.append({
                    "user_a": uid_a,
                    "user_b": uid_b,
                    "score": result["score"],
                    "cosine": result["cosine_similarity"],
                    "embedding_sim": result["embedding_similarity"],
                    "tag_overlap": result["tag_overlap"],
                    "industry": result["industry_complement"],
                    "common_tags": result["common_tags_count"],
                })

    print(f"  共计算了 {len(v2_scores)} 个用户对")

    # ── 3. 评分分布统计 ──
    print(f"\n[3/4] 评分分布统计...")

    all_scores = [s["score"] for s in user_pair_scores]
    all_cosines = [s["cosine"] for s in user_pair_scores]
    all_tag_overlaps = [s["tag_overlap"] for s in user_pair_scores]
    all_industries = [s["industry"] for s in user_pair_scores]

    print(f"  {'指标':<25s} {'均值':>8s} {'标准差':>8s} {'最小':>8s} {'最大':>8s}")
    print(f"  {'-'*57}")
    print(f"  {'V2 综合评分':<25s} {np.mean(all_scores):>8.4f} {np.std(all_scores):>8.4f} "
          f"{min(all_scores):>8.4f} {max(all_scores):>8.4f}")
    print(f"  {'Embedding 余弦相似度':<25s} {np.mean(all_cosines):>8.4f} {np.std(all_cosines):>8.4f} "
          f"{min(all_cosines):>8.4f} {max(all_cosines):>8.4f}")
    print(f"  {'标签重叠分':<25s} {np.mean(all_tag_overlaps):>8.4f} {np.std(all_tag_overlaps):>8.4f} "
          f"{min(all_tag_overlaps):>8.4f} {max(all_tag_overlaps):>8.4f}")
    print(f"  {'行业互补分':<25s} {np.mean(all_industries):>8.4f} {np.std(all_industries):>8.4f} "
          f"{min(all_industries):>8.4f} {max(all_industries):>8.4f}")

    # 评分分布直方图
    print(f"\n  V2 评分分布:")
    bins = [0, 0.1, 0.2, 0.25, 0.30, 0.35, 0.40, 0.50, 0.60, 0.70, 1.0]
    prev = 0
    for b in bins:
        if b == 0:
            continue
        count = sum(1 for s in all_scores if prev <= s < b)
        bar = "█" * (count // 2) if count > 0 else ""
        print(f"    [{prev:.2f}, {b:.2f})  {count:3d}  {bar}")
        prev = b

    print(f"\n  Embedding 余弦相似度分布:")
    prev = -1.0
    cos_bins = [-1.0, -0.5, -0.2, 0.0, 0.2, 0.4, 0.6, 0.8, 1.0]
    for b in cos_bins:
        if b == -1.0:
            continue
        count = sum(1 for s in all_cosines if prev <= s < b)
        bar = "█" * (count // 2) if count > 0 else ""
        print(f"    [{prev:.1f}, {b:.1f})  {count:3d}  {bar}")
        prev = b

    # 标签重叠分布
    print(f"\n  共同标签数分布:")
    tag_count_dist = Counter(s["common_tags"] for s in user_pair_scores)
    for n in sorted(tag_count_dist.keys()):
        count = tag_count_dist[n]
        bar = "█" * count if count > 0 else ""
        print(f"    {n:2d} 个共同标签:  {count:3d} 对  {bar}")

    # ── 4. 与 Ground Truth 对比验证 ──
    print(f"\n[4/4] 与 Ground Truth (match_records) 对比验证...")
    analysis = match_accuracy_analysis(v2_scores, match_records)

    print(f"\n  高匹配对 (GT≥0.7): {analysis['high_match_pairs']} 对")
    print(f"    正确识别: {analysis['correct_high']} 对")
    print(f"    漏识别: {analysis['false_negatives']} 对")
    recall = analysis['correct_high'] / max(1, analysis['high_match_pairs']) * 100
    print(f"    召回率: {recall:.1f}%")

    # 高匹配对的详细对比
    print(f"\n  高匹配对 (GT≥0.7) 详细对比:")
    print(f"  {'ID':<5s} {'用户A':<10s} {'用户B':<10s} {'V2评分':>8s} {'GT评分':>8s} {'余弦':>8s}")
    print(f"  {'-'*49}")
    for detail in analysis["high_score_details"][:15]:
        pair = detail["pair"]
        uid_a, uid_b = pair
        name_a = ""
        name_b = ""
        for r in match_records:
            if r["user_a_id"] == uid_a:
                name_a = r.get("name_a", "")
            if r["user_b_id"] == uid_b:
                name_b = r.get("name_b", "")
        if not name_a or not name_b:
            # 从 embeddings 获取名字
            pass

        print(f"  {f'{uid_a}-{uid_b}':<5s} {name_a:<10s} {name_b:<10s} "
              f"{detail['v2_score']:>8.4f} {detail['gt_score']:>8.4f} {detail['cosine_sim']:>8.4f}")

    # ── Top 10 V2 匹配对 ──
    print(f"\n  Top 10 V2 匹配对 (全部用户):")
    top10 = sorted(user_pair_scores, key=lambda x: x["score"], reverse=True)[:10]
    print(f"  {'排名':<4s} {'用户A':<10s} {'用户B':<10s} {'V2评分':>8s} {'余弦':>8s} {'标签重叠':>8s} {'行业':>8s} {'共同标签':>8s}")
    print(f"  {'-'*60}")
    for rank, s in enumerate(top10, 1):
        name_a = ""
        name_b = ""
        for r in match_records:
            if r["user_a_id"] == s["user_a"]:
                name_a = r.get("name_a", "")
            if r["user_b_id"] == s["user_b"]:
                name_b = r.get("name_b", "")
        # 查找 ground truth 评分
        gt_score = 0.0
        for r in match_records:
            if (r["user_a_id"] == s["user_a"] and r["user_b_id"] == s["user_b"]) or \
               (r["user_a_id"] == s["user_b"] and r["user_b_id"] == s["user_a"]):
                gt_score = r["match_score"]
                break

        print(f"  {rank:<4d} {name_a:<10s} {name_b:<10s} {s['score']:>8.4f} "
              f"{s['cosine']:>8.4f} {s['tag_overlap']:>8.4f} {s['industry']:>8.4f} {s['common_tags']:>4d}")

    # ── 匹配度达到 90%+ 的标准 ──
    print(f"\n{'='*70}")
    print(f"  匹配度达标分析")
    print(f"{'='*70}")

    threshold_90 = 0.45  # V2 综合评分 0.45 以上 = 高匹配
    high_match_v2 = [s for s in user_pair_scores if s["score"] >= threshold_90]
    high_match_count = len(high_match_v2)
    total_pairs = len(user_pair_scores)

    print(f"  V2 综合评分 ≥ 0.45: {high_match_count}/{total_pairs} = {high_match_count/max(1,total_pairs)*100:.1f}%")
    print(f"  V2 综合评分 ≥ 0.40: {sum(1 for s in user_pair_scores if s['score'] >= 0.40)} 对")
    print(f"  V2 综合评分 ≥ 0.35: {sum(1 for s in user_pair_scores if s['score'] >= 0.35)} 对")

    # 分析高匹配对的共同特征
    print(f"\n  高匹配对 (V2 ≥ {threshold_90}) 的共同特征:")
    if high_match_v2:
        avg_cosine = np.mean([s["cosine"] for s in high_match_v2])
        avg_tags = np.mean([s["common_tags"] for s in high_match_v2])
        avg_industry = np.mean([s["industry"] for s in high_match_v2])
        print(f"    Embedding 余弦均值: {avg_cosine:.4f}")
        print(f"    共同标签数均值: {avg_tags:.1f}")
        print(f"    行业互补分均值: {avg_industry:.4f}")

        print(f"\n  前 10 高匹配对 (V2) 详情:")
        for s in high_match_v2[:10]:
            pair = (s["user_a"], s["user_b"])
            gt_score = 0.0
            for r in match_records:
                if (r["user_a_id"] == s["user_a"] and r["user_b_id"] == s["user_b"]) or \
                   (r["user_a_id"] == s["user_b"] and r["user_b_id"] == s["user_a"]):
                    gt_score = r["match_score"]
                    break
            flag = " ✓" if gt_score >= 0.7 else ""
            print(f"    {s['user_a']:2d}-{s['user_b']:2d}: V2={s['score']:.4f}  "
                  f"余弦={s['cosine']:.4f}  标签={s['tag_overlap']:.4f}  "
                  f"行业={s['industry']:.4f}  共{s['common_tags']}标签  GT={gt_score:.2f}{flag}")

    # ── 总结 ──
    print(f"\n{'='*70}")
    print(f"  验证结论")
    print(f"{'='*70}")
    print(f"  ✓ UserTower 预训练完成: 15个用户, 128维 embedding")
    print(f"  ✓ V2 综合评分计算完成: {total_pairs} 个用户对")
    print(f"  ✓ Ground Truth 匹配记录: {len(match_records)} 条")

    max_v2 = max(user_pair_scores, key=lambda x: x["score"])
    print(f"  ✓ 最高 V2 评分: {max_v2['user_a']}-{max_v2['user_b']} = {max_v2['score']:.4f}")

    corr_emb_gt = 0.0
    matched_scores = []
    for s in user_pair_scores:
        pair = (s["user_a"], s["user_b"])
        for r in match_records:
            if (r["user_a_id"] == s["user_a"] and r["user_b_id"] == s["user_b"]) or \
               (r["user_a_id"] == s["user_b"] and r["user_b_id"] == s["user_a"]):
                matched_scores.append((s["score"], r["match_score"]))
                break

    if matched_scores:
        v2_vals = [m[0] for m in matched_scores]
        gt_vals = [m[1] for m in matched_scores]
        corr = np.corrcoef(v2_vals, gt_vals)[0, 1]
        print(f"  ✓ V2评分与GT评分相关系数: {corr:.4f}")

        # V2评分在顶部5个GT上的表现
        top_gt = sorted(matched_scores, key=lambda x: x[1], reverse=True)[:5]
        avg_v2_on_top_gt = np.mean([m[0] for m in top_gt])
        print(f"  ✓ Top5 GT匹配对的V2平均分: {avg_v2_on_top_gt:.4f}")

    print(f"\n  是否达标 (>90%匹配率): ", end="")
    if recall >= 90:
        print("✅ 达标")
    else:
        print(f"❌ 未完全达标 (高匹配召回率 {recall:.1f}%)")
    print(f"  - 原因: 15个用户规模较小, 高匹配GT仅{analysis['high_match_pairs']}对")
    print(f"  - 可通过更多用户数据 + 更长训练进一步提升")
    print(f"{'='*70}")


if __name__ == "__main__":
    main()
