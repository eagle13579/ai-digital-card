#!/usr/bin/env python
"""
prepare_v2_training_data.py — AI数智名片 V2 训练数据管道（13特征版）

基于原 prepare_training_data.py，在原10个特征基础上新增3个V2特征：
  1. intro_semantic: 仅intro/company/title文本的语义相似度（不含brochure）
  2. provide_need_balance: provide/need标签数量互补度
  3. tag_category_overlap: 标签类别级别的重叠度

输出: D:\AI数智名片\backend\data\v2_training_data.json
"""

import json
import math
import random
import sqlite3
import sys
from collections import defaultdict
from pathlib import Path

import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

# ── 配置 ─────────────────────────────────────────────────────────────
DB_PATH = Path(__file__).resolve().parent.parent / "data" / "digital_brochure.db"
OUTPUT_PATH = Path(__file__).resolve().parent.parent / "data" / "v2_training_data.json"
POSITIVE_SCORE_THRESHOLD = 0.3
NEGATIVE_RATIO = 3.0
SEED = 42

random.seed(SEED)
np.random.seed(SEED)


def get_db_connection() -> sqlite3.Connection:
    if not DB_PATH.exists():
        print(f"[错误] 数据库文件不存在: {DB_PATH}")
        sys.exit(1)
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    return conn


def load_users(conn: sqlite3.Connection) -> dict[int, dict]:
    cur = conn.execute(
        "SELECT id, name, company, title, intro FROM users ORDER BY id"
    )
    users = {}
    for row in cur.fetchall():
        uid = row["id"]
        name = row["name"] or ""
        if name.lower() in ("final", "done", "fixtester") or not name.strip():
            continue
        users[uid] = dict(row)
    return users


def load_user_tags(conn: sqlite3.Connection) -> dict[int, dict[str, dict[str, float]]]:
    cur = conn.execute(
        "SELECT user_id, tag_type, tag, weight FROM user_tags ORDER BY user_id"
    )
    tag_map = defaultdict(lambda: {"provide": {}, "need": {}})
    for row in cur.fetchall():
        uid = row["user_id"]
        tag_type = row["tag_type"]
        if tag_type in ("provide", "need"):
            tag_map[uid][tag_type][row["tag"]] = row["weight"]
    return dict(tag_map)


def load_brochure_texts(conn: sqlite3.Connection) -> dict[int, str]:
    cur = conn.execute(
        "SELECT user_id, title, pages_count FROM brochures WHERE status='published'"
    )
    brochure_texts = defaultdict(list)
    for row in cur.fetchall():
        brochure_texts[row["user_id"]].append(row["title"] or "")
    cur = conn.execute("""
        SELECT b.user_id, p.ai_summary
        FROM pages p
        JOIN brochures b ON p.brochure_id = b.id
        WHERE p.ai_summary != '' AND p.ai_summary IS NOT NULL
    """)
    for row in cur.fetchall():
        if row["ai_summary"]:
            brochure_texts[row["user_id"]].append(row["ai_summary"])
    return {uid: " ".join(texts) for uid, texts in brochure_texts.items()}


def load_match_records(conn: sqlite3.Connection) -> list[dict]:
    cur = conn.execute("SELECT * FROM match_records ORDER BY id")
    return [dict(row) for row in cur.fetchall()]


def build_user_document(
    user_id: int,
    users: dict[int, dict],
    tag_map: dict[int, dict[str, dict[str, float]]],
    brochure_texts: dict[int, str],
) -> str:
    parts = []
    user = users.get(user_id, {})
    intro = user.get("intro") or ""
    if intro:
        parts.append(intro)
    company = user.get("company") or ""
    if company:
        parts.append(company)
    title = user.get("title") or ""
    if title:
        parts.append(title)
    tags = tag_map.get(user_id, {"provide": {}, "need": {}})
    for tag, weight in tags.get("provide", {}).items():
        parts.append(f"提供{tag}")
    for tag, weight in tags.get("need", {}).items():
        parts.append(f"需要{tag}")
    bro_text = brochure_texts.get(user_id, "")
    if bro_text:
        parts.append(bro_text)
    return " ".join(parts)


def build_intro_document(
    user_id: int,
    users: dict[int, dict],
) -> str:
    """仅提取intro/company/title，不含标签和brochure（用于V2 intro_semantic特征）"""
    parts = []
    user = users.get(user_id, {})
    intro = user.get("intro") or ""
    if intro:
        parts.append(intro)
    company = user.get("company") or ""
    if company:
        parts.append(company)
    title = user.get("title") or ""
    if title:
        parts.append(title)
    return " ".join(parts)


def compute_tag_overlap_features(
    provide_a: dict[str, float],
    need_b: dict[str, float],
    provide_b: dict[str, float],
    need_a: dict[str, float],
) -> dict:
    """Tower 1: 标签重叠特征"""
    overlap_p2n = sum(provide_a.get(t, 0.0) * w for t, w in need_b.items() if t in provide_a)
    overlap_n2p = sum(provide_b.get(t, 0.0) * w for t, w in need_a.items() if t in provide_b)
    common_a_b = set(provide_a.keys()) & set(need_b.keys())
    common_b_a = set(provide_b.keys()) & set(need_a.keys())
    all_common = common_a_b | common_b_a
    common_count = len(all_common)
    max_possible = max(1, len(all_common))
    total_overlap = overlap_p2n + overlap_n2p
    overlap_norm = min(1.0, total_overlap / max_possible)
    return {
        "tag_overlap_score": round(overlap_norm, 4),
        "common_tag_count": common_count,
        "overlap_provide_to_need": round(overlap_p2n, 4),
        "overlap_need_to_provide": round(overlap_n2p, 4),
    }


def compute_tag_weight_features(
    provide_a: dict[str, float],
    need_a: dict[str, float],
    provide_b: dict[str, float],
    need_b: dict[str, float],
) -> dict:
    """Tower 3: 标签权重特征"""
    total_tags_a = len(provide_a) + len(need_a)
    total_tags_b = len(provide_b) + len(need_b)
    if total_tags_a == 0 or total_tags_b == 0:
        return {"tag_count_a": 0, "tag_count_b": 0, "avg_weight_a": 0.0,
                "avg_weight_b": 0.0, "tag_weight_score": 0.0}
    avg_weight_a = (sum(provide_a.values()) + sum(need_a.values())) / total_tags_a
    avg_weight_b = (sum(provide_b.values()) + sum(need_b.values())) / total_tags_b
    max_tags = max(total_tags_a, total_tags_b)
    tag_count_score = min(total_tags_a, total_tags_b) / max_tags if max_tags > 0 else 0.0
    weight_norm = min(1.0, (avg_weight_a + avg_weight_b) / 4.0)
    tag_weight_score = tag_count_score * 0.5 + weight_norm * 0.5
    return {
        "tag_count_a": total_tags_a,
        "tag_count_b": total_tags_b,
        "avg_weight_a": round(avg_weight_a, 4),
        "avg_weight_b": round(avg_weight_b, 4),
        "tag_weight_score": round(tag_weight_score, 4),
    }


def compute_semantic_features(
    user_docs: dict[int, str],
    user_a_id: int,
    user_b_id: int,
    vectorizer: TfidfVectorizer,
    tfidf_matrix,
    id_to_idx: dict[int, int],
) -> dict:
    """Tower 2: TF-IDF 语义相似度特征（完整文档）"""
    doc_a = user_docs.get(user_a_id, "")
    doc_b = user_docs.get(user_b_id, "")
    if not doc_a.strip() or not doc_b.strip():
        return {"vector_semantic": 0.0}
    idx_a = id_to_idx.get(user_a_id)
    idx_b = id_to_idx.get(user_b_id)
    if idx_a is None or idx_b is None:
        return {"vector_semantic": 0.0}
    sim = cosine_similarity(tfidf_matrix[idx_a:idx_a+1], tfidf_matrix[idx_b:idx_b+1])[0][0]
    return {"vector_semantic": round(float(sim), 4)}


def compute_v2_features(
    user_a_id: int,
    user_b_id: int,
    users: dict[int, dict],
    tag_map: dict[int, dict[str, dict[str, float]]],
    intro_docs: dict[int, str],
    intro_vectorizer: TfidfVectorizer,
    intro_tfidf_matrix,
    intro_id_to_idx: dict[int, int],
) -> dict:
    """V2新增的3个特征"""
    result = {}

    # === V2 Feature 1: intro_semantic ===
    # 仅intro/company/title文本的语义相似度（不包含标签和brochure）
    doc_a = intro_docs.get(user_a_id, "")
    doc_b = intro_docs.get(user_b_id, "")
    intro_sim = 0.0
    if doc_a.strip() and doc_b.strip():
        idx_a = intro_id_to_idx.get(user_a_id)
        idx_b = intro_id_to_idx.get(user_b_id)
        if idx_a is not None and idx_b is not None:
            sim = cosine_similarity(
                intro_tfidf_matrix[idx_a:idx_a+1],
                intro_tfidf_matrix[idx_b:idx_b+1]
            )[0][0]
            intro_sim = float(sim)
    result["intro_semantic"] = round(intro_sim, 4)

    # === V2 Feature 2: provide_need_balance ===
    # 衡量两个用户provide/need标签数量的互补度
    t_a = tag_map.get(user_a_id, {"provide": {}, "need": {}})
    t_b = tag_map.get(user_b_id, {"provide": {}, "need": {}})
    p_a = len(t_a.get("provide", {}))
    n_a = len(t_a.get("need", {}))
    p_b = len(t_b.get("provide", {}))
    n_b = len(t_b.get("need", {}))

    # A提供匹配B需要: A的provide数量和B的need数量之间的适配度
    provide_need_match_a = min(p_a, n_b) / max(1, max(p_a, n_b))
    provide_need_match_b = min(p_b, n_a) / max(1, max(p_b, n_a))
    balance = (provide_need_match_a + provide_need_match_b) / 2.0
    result["provide_need_balance"] = round(balance, 4)

    # === V2 Feature 3: tag_category_overlap ===
    # 基于标签类别（关键词的语义类别）的高层重叠度
    # 使用简单的文本相似度：将两个用户的所有标签拼接，比较重叠比例
    tags_a = set(t_a["provide"].keys()) | set(t_a["need"].keys())
    tags_b = set(t_b["provide"].keys()) | set(t_b["need"].keys())

    if len(tags_a) > 0 and len(tags_b) > 0:
        # 计算标签集合的Jaccard相似度
        jaccard = len(tags_a & tags_b) / len(tags_a | tags_b)
        # 也计算cosine角标重叠（基于标签数量比重叠）
        tag_count_ratio = min(len(tags_a), len(tags_b)) / max(1, max(len(tags_a), len(tags_b)))
        category_overlap = (jaccard + tag_count_ratio) / 2.0
    else:
        category_overlap = 0.0
    result["tag_category_overlap"] = round(category_overlap, 4)

    return result


def build_all_features(
    user_a_id: int,
    user_b_id: int,
    users: dict[int, dict],
    tag_map: dict[int, dict[str, dict[str, float]]],
    user_docs: dict[int, str],
    vectorizer: TfidfVectorizer,
    tfidf_matrix,
    id_to_idx: dict[int, int],
    intro_docs: dict[int, str],
    intro_vectorizer: TfidfVectorizer,
    intro_tfidf_matrix,
    intro_id_to_idx: dict[int, int],
) -> dict:
    """构建用户对的所有三塔+V2特征（共13个）"""
    t_a = tag_map.get(user_a_id, {"provide": {}, "need": {}})
    t_b = tag_map.get(user_b_id, {"provide": {}, "need": {}})

    # Tower 1
    overlap_feat = compute_tag_overlap_features(
        t_a["provide"], t_b["need"], t_b["provide"], t_a["need"]
    )
    # Tower 2
    semantic_feat = compute_semantic_features(
        user_docs, user_a_id, user_b_id, vectorizer, tfidf_matrix, id_to_idx
    )
    # Tower 3
    weight_feat = compute_tag_weight_features(
        t_a["provide"], t_a["need"], t_b["provide"], t_b["need"]
    )
    # V2新特征
    v2_feat = compute_v2_features(
        user_a_id, user_b_id, users, tag_map,
        intro_docs, intro_vectorizer, intro_tfidf_matrix, intro_id_to_idx
    )

    features = {}
    features.update(overlap_feat)
    features.update(semantic_feat)
    features.update(weight_feat)
    features.update(v2_feat)
    return features


def generate_v2_training_data(conn: sqlite3.Connection) -> dict:
    """主流程：生成V2训练数据（13特征）"""
    print("=" * 60)
    print("AI数智名片 — V2训练数据管道（13特征）")
    print("=" * 60)

    # 1. 加载数据
    users = load_users(conn)
    tag_map = load_user_tags(conn)
    brochure_texts = load_brochure_texts(conn)
    match_records = load_match_records(conn)

    real_user_ids = set(users.keys())
    print(f"\n[信息] 真实用户数: {len(users)}")
    print(f"[信息] 用户IDs: {sorted(real_user_ids)}")
    print(f"[信息] 匹配记录数: {len(match_records)}")

    # 2. 构建完整文档（V1方式）
    user_docs = {}
    for uid in real_user_ids:
        user_docs[uid] = build_user_document(uid, users, tag_map, brochure_texts)

    doc_ids = sorted(real_user_ids)
    doc_texts = [user_docs[uid] for uid in doc_ids]
    vectorizer = TfidfVectorizer(
        max_features=500,
        token_pattern=r"(?u)\b\w+\b",
        analyzer="word",
        ngram_range=(1, 2),
        max_df=0.85,
        min_df=0.01,
    )
    tfidf_matrix = vectorizer.fit_transform(doc_texts)
    id_to_idx = {uid: i for i, uid in enumerate(doc_ids)}
    print(f"[信息] V1 TF-IDF 特征维度: {tfidf_matrix.shape[1]}")

    # 3. 构建intro-only文档（V2新增）
    intro_docs = {}
    for uid in real_user_ids:
        intro_docs[uid] = build_intro_document(uid, users)

    # 对intro文档做独立的TF-IDF
    intro_texts = [intro_docs[uid] for uid in doc_ids]
    intro_vectorizer = TfidfVectorizer(
        max_features=200,
        token_pattern=r"(?u)\b\w+\b",
        analyzer="word",
        ngram_range=(1, 2),
        max_df=0.9,
        min_df=0.01,
    )
    intro_tfidf_matrix = intro_vectorizer.fit_transform(intro_texts)
    intro_id_to_idx = {uid: i for i, uid in enumerate(doc_ids)}
    print(f"[信息] V2 Intro TF-IDF 特征维度: {intro_tfidf_matrix.shape[1]}")

    # 4. 构建正样本
    positive_pairs_set: set[tuple[int, int]] = set()
    positive_details = []

    for rec in match_records:
        score = rec["match_score"]
        ua, ub = rec["user_a_id"], rec["user_b_id"]
        if ua not in real_user_ids or ub not in real_user_ids:
            continue
        if score >= POSITIVE_SCORE_THRESHOLD:
            pair = (min(ua, ub), max(ua, ub))
            if pair not in positive_pairs_set:
                positive_pairs_set.add(pair)
                positive_details.append((ua, ub, score, rec.get("common_tags", "[]")))

    print(f"\n[信息] 正样本数: {len(positive_pairs_set)}")

    # 5. 构建负样本
    all_possible_pairs: set[tuple[int, int]] = set()
    for ua in real_user_ids:
        for ub in real_user_ids:
            if ua < ub:
                all_possible_pairs.add((ua, ub))

    existing_match_pairs: set[tuple[int, int]] = set()
    for rec in match_records:
        ua, ub = rec["user_a_id"], rec["user_b_id"]
        if ua in real_user_ids and ub in real_user_ids:
            existing_match_pairs.add((min(ua, ub), max(ua, ub)))

    negative_candidates = list(all_possible_pairs - existing_match_pairs)
    random.shuffle(negative_candidates)
    target_neg_count = int(len(positive_pairs_set) * NEGATIVE_RATIO)
    negative_samples = negative_candidates[:target_neg_count]

    print(f"[信息] 负样本候选数: {len(negative_candidates)}")
    print(f"[信息] 取负样本数: {min(len(negative_samples), len(negative_candidates))}")

    # 6. 构建特征
    samples = []

    # 正样本
    for ua, ub, score, common_tags_str in positive_details:
        features = build_all_features(
            ua, ub, users, tag_map, user_docs,
            vectorizer, tfidf_matrix, id_to_idx,
            intro_docs, intro_vectorizer, intro_tfidf_matrix, intro_id_to_idx,
        )
        try:
            ctags = json.loads(common_tags_str) if isinstance(common_tags_str, str) else []
        except (json.JSONDecodeError, TypeError):
            ctags = []
        samples.append({
            "user_id": ua,
            "candidate_id": ub,
            "label": 1,
            "score": score,
            "common_tags": ctags,
            "features": features,
        })

    # 负样本
    neg_actual = 0
    for ua, ub in negative_samples[:target_neg_count]:
        features = build_all_features(
            ua, ub, users, tag_map, user_docs,
            vectorizer, tfidf_matrix, id_to_idx,
            intro_docs, intro_vectorizer, intro_tfidf_matrix, intro_id_to_idx,
        )
        samples.append({
            "user_id": ua,
            "candidate_id": ub,
            "label": 0,
            "score": 0.0,
            "common_tags": [],
            "features": features,
        })
        neg_actual += 1

    random.shuffle(samples)

    # 7. 统计
    labels = [s["label"] for s in samples]
    pos_count = sum(labels)
    neg_count = len(labels) - pos_count

    V2_FEATURE_NAMES = [
        "tag_overlap_score", "common_tag_count",
        "overlap_provide_to_need", "overlap_need_to_provide",
        "vector_semantic",
        "tag_count_a", "tag_count_b", "avg_weight_a", "avg_weight_b",
        "tag_weight_score",
        "intro_semantic", "provide_need_balance", "tag_category_overlap",
    ]

    print(f"\n{'=' * 60}")
    print(f"V2训练集统计")
    print(f"{'=' * 60}")
    print(f"  总样本数: {len(samples)}")
    print(f"  正样本数: {pos_count} ({pos_count/len(samples)*100:.1f}%)")
    print(f"  负样本数: {neg_count} ({neg_count/len(samples)*100:.1f}%)")
    print(f"  特征数:   {len(V2_FEATURE_NAMES)}")
    print(f"  特征列表: {V2_FEATURE_NAMES}")

    # 8. 保存
    output = {
        "meta": {
            "total_samples": len(samples),
            "positive_count": pos_count,
            "negative_count": neg_count,
            "feature_names": V2_FEATURE_NAMES,
            "n_users": len(users),
            "user_ids": sorted(real_user_ids),
            "version": "v2",
            "v2_new_features": ["intro_semantic", "provide_need_balance", "tag_category_overlap"],
        },
        "samples": samples,
    }

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    print(f"[完成] V2训练数据已保存到: {OUTPUT_PATH}")
    return output


if __name__ == "__main__":
    conn = get_db_connection()
    try:
        generate_v2_training_data(conn)
    finally:
        conn.close()
