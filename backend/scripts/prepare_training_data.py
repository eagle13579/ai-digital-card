#!/usr/bin/env python
"""
prepare_training_data.py — AI数智名片 模型训练数据管道

从数据库提取用户标签/简介数据，构建正负样本对，输出为JSON训练集。

功能：
  1. 读取 SQLite 数据库（users, user_tags, brochures, match_records）
  2. 提取每个用户的标签向量（provide/need）、简介、brochure内容
  3. 构建完整的三塔特征：
     - Tower 1 (标签重叠特征): tag_overlap_score, common_tag_count, ...
     - Tower 2 (语义相似度特征): TF-IDF cosine similarity
     - Tower 3 (标签权重特征): tag_count_score, avg_weight_norm, ...
  4. 正样本: match_records 中得分 >= 0.3 的配对
  5. 负样本: 从未匹配的用户对中随机采样（数量 = 正样本数的 2~3 倍）
  6. 输出为 JSON 训练集

输出格式：
  {
    "samples": [
      {
        "user_id": int,
        "candidate_id": int,
        "label": 0/1,
        "features": {
          "tag_overlap_score": float,
          "common_tag_count": int,
          "overlap_provide_to_need": float,
          "overlap_need_to_provide": float,
          "vector_semantic": float,
          "tag_count_a": int,
          "tag_count_b": int,
          "avg_weight_a": float,
          "avg_weight_b": float,
          "tag_weight_score": float
        }
      }
    ]
  }

不需要修改已有文件，可独立运行。
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
OUTPUT_PATH = Path(__file__).resolve().parent.parent / "data" / "training_data.json"
POSITIVE_SCORE_THRESHOLD = 0.3  # 匹配记录中≥此分认为正样本
NEGATIVE_RATIO = 3.0  # 负样本数 = 正样本数 × 此比例
SEED = 42

random.seed(SEED)
np.random.seed(SEED)


# ── 数据库读取 ─────────────────────────────────────────────────────────

def get_db_connection() -> sqlite3.Connection:
    """获取数据库连接"""
    if not DB_PATH.exists():
        print(f"[错误] 数据库文件不存在: {DB_PATH}")
        sys.exit(1)
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    return conn


def load_users(conn: sqlite3.Connection) -> dict[int, dict]:
    """加载所有用户基本信息（排除测试账号）"""
    cur = conn.execute(
        "SELECT id, name, company, title, intro FROM users ORDER BY id"
    )
    users = {}
    for row in cur.fetchall():
        uid = row["id"]
        name = row["name"] or ""
        # 跳过测试/占位账号
        if name.lower() in ("final", "done", "fixtester") or not name.strip():
            continue
        users[uid] = dict(row)
    return users


def load_user_tags(conn: sqlite3.Connection) -> dict[int, dict[str, dict[str, float]]]:
    """加载用户标签向量 {user_id: {"provide": {tag: weight}, "need": {tag: weight}}}"""
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
    """加载用户 brochure 标题 + ai_summary"""
    cur = conn.execute("SELECT user_id, title, pages_count FROM brochures WHERE status='published'")
    brochure_texts = defaultdict(list)
    for row in cur.fetchall():
        brochure_texts[row["user_id"]].append(row["title"] or "")
    # 获取 pages 的 ai_summary
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
    """加载所有匹配记录"""
    cur = conn.execute("SELECT * FROM match_records ORDER BY id")
    return [dict(row) for row in cur.fetchall()]


# ── 特征构建（三塔） ──────────────────────────────────────────────────

def build_user_document(
    user_id: int,
    users: dict[int, dict],
    tag_map: dict[int, dict[str, dict[str, float]]],
    brochure_texts: dict[int, str],
) -> str:
    """构建用户的文本文档（用于语义相似度 Tower 2）"""
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

    # 归一化: 用最大可能重叠分母
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
    """Tower 2: TF-IDF 语义相似度特征"""
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


def build_all_features(
    user_a_id: int,
    user_b_id: int,
    users: dict[int, dict],
    tag_map: dict[int, dict[str, dict[str, float]]],
    user_docs: dict[int, str],
    vectorizer: TfidfVectorizer,
    tfidf_matrix,
    id_to_idx: dict[int, int],
) -> dict:
    """构建用户对的所有三塔特征"""
    t_a = tag_map.get(user_a_id, {"provide": {}, "need": {}})
    t_b = tag_map.get(user_b_id, {"provide": {}, "need": {}})

    # Tower 1
    overlap_feat = compute_tag_overlap_features(
        t_a["provide"], t_b["need"], t_b["provide"], t_a["need"]
    )
    # Tower 2
    semantic_feat = compute_semantic_features(user_docs, user_a_id, user_b_id,
                                               vectorizer, tfidf_matrix, id_to_idx)
    # Tower 3
    weight_feat = compute_tag_weight_features(
        t_a["provide"], t_a["need"], t_b["provide"], t_b["need"]
    )

    features = {}
    features.update(overlap_feat)
    features.update(semantic_feat)
    features.update(weight_feat)
    return features


# ── 样本生成 ──────────────────────────────────────────────────────────

def generate_samples(conn: sqlite3.Connection) -> dict:
    """主流程：生成训练样本"""
    print("=" * 60)
    print("AI数智名片 — 训练数据管道")
    print("=" * 60)

    # 1. 加载数据
    users = load_users(conn)
    tag_map = load_user_tags(conn)
    brochure_texts = load_brochure_texts(conn)
    match_records = load_match_records(conn)

    real_user_ids = set(users.keys())
    print(f"\n[信息] 真实用户数: {len(users)}")
    print(f"[信息] 用户IDs: {sorted(real_user_ids)}")
    print(f"[信息] 标签数: {sum(len(t.get('provide', {})) + len(t.get('need', {})) for t in tag_map.values())}")
    print(f"[信息] 匹配记录数: {len(match_records)}")

    # 2. 构建用户文档 + TF-IDF
    user_docs = {}
    for uid in real_user_ids:
        user_docs[uid] = build_user_document(uid, users, tag_map, brochure_texts)

    # TF-IDF 向量化（用于 Tower 2 语义相似度）
    doc_ids = sorted(real_user_ids)
    doc_texts = [user_docs[uid] for uid in doc_ids]
    vectorizer = TfidfVectorizer(
        max_features=500,
        token_pattern=r"(?u)\b\w+\b",  # 支持中文分词
        analyzer="word",
        ngram_range=(1, 2),
        max_df=0.85,
        min_df=0.01,
    )
    tfidf_matrix = vectorizer.fit_transform(doc_texts)
    id_to_idx = {uid: i for i, uid in enumerate(doc_ids)}
    print(f"[信息] TF-IDF 特征维度: {tfidf_matrix.shape[1]}")

    # 3. 构建正样本
    positive_pairs: set[tuple[int, int]] = set()
    positive_details = []

    for rec in match_records:
        score = rec["match_score"]
        ua, ub = rec["user_a_id"], rec["user_b_id"]
        if ua not in real_user_ids or ub not in real_user_ids:
            continue
        if score >= POSITIVE_SCORE_THRESHOLD:
            pair = (min(ua, ub), max(ua, ub))
            if pair not in positive_pairs:
                positive_pairs.add(pair)
                positive_details.append((ua, ub, score, rec.get("common_tags", "[]")))

    print(f"\n[信息] 正样本数: {len(positive_pairs)}")

    # 4. 构建负样本（从未匹配对中随机采样）
    all_possible_pairs: set[tuple[int, int]] = set()
    for ua in real_user_ids:
        for ub in real_user_ids:
            if ua < ub:
                all_possible_pairs.add((ua, ub))

    # 已有的匹配对（无论分数高低）
    existing_match_pairs: set[tuple[int, int]] = set()
    for rec in match_records:
        ua, ub = rec["user_a_id"], rec["user_b_id"]
        if ua in real_user_ids and ub in real_user_ids:
            existing_match_pairs.add((min(ua, ub), max(ua, ub)))

    # 候选负样本 = 所有可能对 - 已有匹配对
    negative_candidates = list(all_possible_pairs - existing_match_pairs)
    random.shuffle(negative_candidates)

    target_neg_count = int(len(positive_pairs) * NEGATIVE_RATIO)
    negative_samples = negative_candidates[:target_neg_count]

    print(f"[信息] 负样本候选数: {len(negative_candidates)}")
    print(f"[信息] 取负样本数: {min(len(negative_samples), len(negative_candidates))}")

    # 5. 构建特征
    samples = []

    # 正样本
    for ua, ub, score, common_tags_str in positive_details:
        features = build_all_features(ua, ub, users, tag_map, user_docs,
                                      vectorizer, tfidf_matrix, id_to_idx)
        # 从匹配记录解析 common_tags
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
        features = build_all_features(ua, ub, users, tag_map, user_docs,
                                      vectorizer, tfidf_matrix, id_to_idx)
        samples.append({
            "user_id": ua,
            "candidate_id": ub,
            "label": 0,
            "score": 0.0,
            "common_tags": [],
            "features": features,
        })
        neg_actual += 1

    # 6. 打乱样本顺序
    random.shuffle(samples)

    # 7. 统计
    labels = [s["label"] for s in samples]
    pos_count = sum(labels)
    neg_count = len(labels) - pos_count

    print(f"\n{'=' * 60}")
    print(f"训练集统计")
    print(f"{'=' * 60}")
    print(f"  总样本数: {len(samples)}")
    print(f"  正样本数: {pos_count} ({pos_count/len(samples)*100:.1f}%)")
    print(f"  负样本数: {neg_count} ({neg_count/len(samples)*100:.1f}%)")
    print(f"  特征数:   {len(samples[0]['features']) if samples else 0}")
    feature_keys = list(samples[0]["features"].keys()) if samples else []
    print(f"  特征列表: {feature_keys}")
    print(f"\n输出路径: {OUTPUT_PATH}")

    # 8. 保存
    output = {
        "meta": {
            "total_samples": len(samples),
            "positive_count": pos_count,
            "negative_count": neg_count,
            "feature_names": feature_keys,
            "n_users": len(users),
            "user_ids": sorted(real_user_ids),
        },
        "samples": samples,
    }

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    print(f"[完成] 训练数据已保存到: {OUTPUT_PATH}")
    return output


# ── 入口 ──────────────────────────────────────────────────────────────

if __name__ == "__main__":
    conn = get_db_connection()
    try:
        generate_samples(conn)
    finally:
        conn.close()
