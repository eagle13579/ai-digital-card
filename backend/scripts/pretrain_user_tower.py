"""UserTower 预训练脚本 — 对比学习 (Triplet Loss)

功能:
  1. 从 SQLite 读取用户数据 (User / UserTag / Brochure)
  2. 为每个用户构建特征向量 (tag_count, brochure_count, view_count, purpose 等)
  3. 使用对比学习训练 UserTower (标签重叠作为正样本)
  4. 输出每个用户的 embedding 到 data/user_embeddings.json

用法:
    cd backend && python scripts/pretrain_user_tower.py
"""
import json
import math
import sqlite3
import sys
import warnings
from pathlib import Path

import numpy as np
import torch

# ── 添加项目根目录到 sys.path ──
BASE_DIR = Path(__file__).resolve().parent.parent  # backend/
sys.path.insert(0, str(BASE_DIR))

from app.models.ml.user_tower import (
    UserFeatureEncoder,
    UserTower,
    UserTowerTrainer,
    TripletLoss,
)

warnings.filterwarnings("ignore")

# ── 常量 ──────────────────────────────────────────────────────────────────────
DB_PATH = BASE_DIR / "data" / "digital_brochure.db"
OUTPUT_DIR = BASE_DIR / "data"
MODEL_SAVE_DIR = BASE_DIR / "data" / "models"
EMBEDDINGS_SAVE_PATH = OUTPUT_DIR / "user_embeddings.json"
MODEL_SAVE_PATH = MODEL_SAVE_DIR / "user_tower_pretrained.pt"
ENCODER_SAVE_PATH = MODEL_SAVE_DIR / "user_tower_pretrained_checkpoint.pt"
EPOCHS = 50
BATCH_SIZE = 16
EMBEDDING_DIM = 128
DEVICE = "cuda" if torch.cuda.is_available() else "cpu"

# 排除无标签的测试用户
EXCLUDE_USER_IDS = {16, 17, 18, 19}


def fetch_all_data() -> dict:
    """从 SQLite 提取所有用户 / 标签 / 名片数据。"""
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    # ── 1. 用户 ──
    cursor.execute(
        "SELECT id, name, company, title, intro, membership_tier "
        "FROM users ORDER BY id"
    )
    users = [dict(r) for r in cursor.fetchall()]

    # ── 2. 用户标签 ──
    cursor.execute("SELECT user_id, tag_type, tag, weight FROM user_tags")
    all_tags = [dict(r) for r in cursor.fetchall()]

    # ── 3. 名片 ──
    cursor.execute(
        "SELECT user_id, purpose, pages_count, view_count, status FROM brochures"
    )
    all_brochures = [dict(r) for r in cursor.fetchall()]

    conn.close()

    print(f"[数据] 用户: {len(users)}  标签: {len(all_tags)}  名片: {len(all_brochures)}")

    # ── 按 user_id 分组 ──
    tags_by_user: dict[int, list] = {}
    for t in all_tags:
        tags_by_user.setdefault(t["user_id"], []).append(t)

    brochures_by_user: dict[int, list] = {}
    for b in all_brochures:
        brochures_by_user.setdefault(b["user_id"], []).append(b)

    return {
        "users": users,
        "tags_by_user": tags_by_user,
        "brochures_by_user": brochures_by_user,
    }


def build_feature_rows(data: dict) -> list[dict]:
    """为每个有效用户构建特征行。"""
    rows = []
    users = data["users"]
    tags_by_user = data["tags_by_user"]
    brochures_by_user = data["brochures_by_user"]

    for u in users:
        uid = u["id"]
        if uid in EXCLUDE_USER_IDS:
            continue

        tags = tags_by_user.get(uid, [])
        brochures = brochures_by_user.get(uid, [])

        # ── 标签统计 ──
        tag_count = len(tags)
        top_tag = ""
        if tags:
            sorted_tags = sorted(tags, key=lambda t: t.get("weight", 1.0), reverse=True)
            top_tag = str(sorted_tags[0].get("tag", ""))

        # ── 名片统计 ──
        brochure_count = len(brochures)
        purpose = ""
        total_view_count = 0
        total_page_count = 0
        if brochures:
            purpose = str(brochures[0].get("purpose", ""))
            for b in brochures:
                total_view_count += b.get("view_count", 0) or 0
                total_page_count += b.get("pages_count", 0) or 1

        # ── 简介长度 ──
        intro = u.get("intro", "") or ""
        avg_intro_len = len(intro)

        # ── 会员等级 ──
        membership_tier = str(u.get("membership_tier", "free") or "free")

        row = {
            "user_id": uid,
            "name": u.get("name", ""),
            "tag_count": tag_count,
            "brochure_count": brochure_count,
            "view_count": total_view_count,
            "page_count": total_page_count,
            "avg_intro_len": avg_intro_len,
            "purpose": purpose,
            "top_tag": top_tag,
            "membership_tier": membership_tier,
        }
        rows.append(row)

    print(f"[特征] 有效用户: {len(rows)} 人")
    return rows


def build_training_triplets(feature_rows: list[dict]) -> tuple:
    """基于标签重叠构建训练三元组 (anchor, positive, negative)。

    正样本: 共享至少 1 个相同标签的用户对
    负样本: 完全无标签重叠的用户对
    """
    # ── 按 user_id 索引 ──
    rows_by_id = {r["user_id"]: r for r in feature_rows}

    # ── 标签重叠矩阵 ──
    # 先收集所有 real_user 的 tag 集合
    conn = sqlite3.connect(str(DB_PATH))
    cursor = conn.cursor()
    tags_set: dict[int, set[str]] = {}
    for r in feature_rows:
        uid = r["user_id"]
        cursor.execute("SELECT tag FROM user_tags WHERE user_id=?", (uid,))
        tags_set[uid] = {row[0] for row in cursor.fetchall()}
    conn.close()

    user_ids = [r["user_id"] for r in feature_rows]
    n = len(user_ids)

    positives = []  # (uid_a, uid_b) — same tags
    negatives = []  # (uid_a, uid_b) — no shared tags

    for i in range(n):
        for j in range(i + 1, n):
            uid_a = user_ids[i]
            uid_b = user_ids[j]
            overlap = tags_set[uid_a] & tags_set[uid_b]
            if len(overlap) >= 1:
                positives.append((uid_a, uid_b))
            else:
                negatives.append((uid_a, uid_b))

    print(f"[三元组] 正样本对: {len(positives)}  负样本对: {len(negatives)}")

    # ── 构建三元组: 每个正样本对 → (anchor, positive) + 随机负样本 ──
    # 为简化，对每个正样本对: anchor=A, positive=B, negative=C (C随机从负样本集选取)
    triplets = []
    for uid_a, uid_b in positives:
        # 找与 uid_a 无重叠的用户 C
        candidates_c = [u for u in user_ids
                        if u != uid_a and u != uid_b
                        and not (tags_set[uid_a] & tags_set[u])]
        if candidates_c:
            uid_c = np.random.choice(candidates_c)
            triplets.append((uid_a, uid_b, uid_c))

    print(f"[三元组] 最终训练三元组: {len(triplets)}")

    return triplets, user_ids, rows_by_id


def main():
    print(f"{'='*60}")
    print(f"  UserTower 预训练")
    print(f"  设备: {DEVICE}  嵌入维度: {EMBEDDING_DIM}  Epochs: {EPOCHS}")
    print(f"{'='*60}")

    # ── 1. 加载数据 ──
    print("\n[1/6] 加载数据...")
    raw_data = fetch_all_data()
    feature_rows = build_feature_rows(raw_data)

    # ── 2. 构建 DataFrame → 训练编码器 ──
    print("\n[2/6] 构建特征编码器...")
    import pandas as pd

    df = pd.DataFrame(feature_rows)
    print(f"  DataFrame 列: {list(df.columns)}")
    print(f"  purpose 分布: {df['purpose'].value_counts().to_dict()}")
    print(f"  top_tag 分布: {df['top_tag'].value_counts().head(10).to_dict()}")
    print(f"  membership_tier 分布: {df['membership_tier'].value_counts().to_dict()}")

    encoder = UserFeatureEncoder(embedding_dim=16)
    encoder.fit(df)
    print(f"  编码器: {encoder}")

    # ── 3. 编码所有用户特征 ──
    print("\n[3/6] 编码用户特征...")
    all_tensor = encoder.transform(df)  # (N, total_feature_dim)
    N = all_tensor.size(0)
    total_dim = all_tensor.size(1)
    print(f"  特征张量: shape={all_tensor.shape}  total_dim={total_dim}")

    # ── 4. 构建三元组 ──
    print("\n[4/6] 构建训练三元组...")
    triplets, user_ids, rows_by_id = build_training_triplets(feature_rows)
    print(f"  user_ids: {user_ids}")

    if len(triplets) == 0:
        print("  ❌ 无训练三元组！检查标签重叠数据。")
        return

    # 创建 id→index 映射
    id_to_idx = {uid: idx for idx, uid in enumerate(user_ids)}

    # 构建张量
    anchors = []
    positives = []
    negatives = []
    for uid_a, uid_b, uid_c in triplets:
        anchors.append(all_tensor[id_to_idx[uid_a]].unsqueeze(0))
        positives.append(all_tensor[id_to_idx[uid_b]].unsqueeze(0))
        negatives.append(all_tensor[id_to_idx[uid_c]].unsqueeze(0))

    anchor_tensor = torch.cat(anchors, dim=0)
    positive_tensor = torch.cat(positives, dim=0)
    negative_tensor = torch.cat(negatives, dim=0)

    print(f"  锚点:   {anchor_tensor.shape}")
    print(f"  正样本: {positive_tensor.shape}")
    print(f"  负样本: {negative_tensor.shape}")

    # ── 5. 训练 ──
    print(f"\n[5/6] 训练 UserTower ({EPOCHS} epochs)...")

    # 拆分训练/验证 (80/20)
    n_train = int(len(triplets) * 0.8)
    indices = torch.randperm(len(triplets))

    train_idx = indices[:n_train]
    val_idx = indices[n_train:]

    tower = UserTower(
        num_features=total_dim,
        embedding_dim=EMBEDDING_DIM,
        hidden_dims=[256, 128],
        dropout=0.1,
    )
    print(f"  模型: {tower}")

    trainer = UserTowerTrainer(
        tower=tower,
        encoder=encoder,
        lr=1e-3,
        patience=8,
        margin=0.3,
        device=DEVICE,
    )

    if len(val_idx) > 0:
        trainer.fit(
            train_anchors=anchor_tensor[train_idx],
            train_positives=positive_tensor[train_idx],
            train_negatives=negative_tensor[train_idx],
            val_anchors=anchor_tensor[val_idx],
            val_positives=positive_tensor[val_idx],
            val_negatives=negative_tensor[val_idx],
            epochs=EPOCHS,
            batch_size=BATCH_SIZE,
            verbose=True,
        )
    else:
        trainer.fit(
            train_anchors=anchor_tensor,
            train_positives=positive_tensor,
            train_negatives=negative_tensor,
            epochs=EPOCHS,
            batch_size=BATCH_SIZE,
            verbose=True,
        )

    # ── 6. 提取 Embedding 并保存 ──
    print(f"\n[6/6] 提取 Embedding 并保存...")

    MODEL_SAVE_DIR.mkdir(parents=True, exist_ok=True)
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # 提取所有用户 embedding
    tower.eval()
    tower = tower.to("cpu")
    with torch.no_grad():
        embeddings = tower(all_tensor).numpy()  # (N, 128)

    # 保存 embeddings
    embeddings_dict = {}
    for idx, uid in enumerate(user_ids):
        emb = embeddings[idx].tolist()
        name = rows_by_id[uid]["name"]
        embeddings_dict[str(uid)] = {
            "user_id": uid,
            "name": name,
            "embedding": emb,
        }

    with open(str(EMBEDDINGS_SAVE_PATH), "w", encoding="utf-8") as f:
        json.dump(embeddings_dict, f, ensure_ascii=False, indent=2)

    # 保存模型
    tower.save_model(str(MODEL_SAVE_PATH))
    trainer.save(str(ENCODER_SAVE_PATH))

    print(f"  ✅ Embedding 已保存: {EMBEDDINGS_SAVE_PATH}")
    print(f"  ✅ 模型已保存: {MODEL_SAVE_PATH}")
    print(f"  ✅ 训练检查点已保存: {ENCODER_SAVE_PATH}")
    print(f"  用户数: {len(embeddings_dict)}  嵌入维度: {EMBEDDING_DIM}")

    # ── 统计 ──
    print(f"\n{'='*60}")
    print(f"  训练完成统计")
    print(f"{'='*60}")
    print(f"  最终 train_loss: {trainer.train_losses[-1]:.6f}" if trainer.train_losses else "")
    if trainer.val_losses:
        print(f"  最佳 val_loss: {trainer.best_val_loss:.6f}")
    print(f"  训练 epochs: {trainer.current_epoch}")
    print(f"  早停触发: {'是' if trainer.epochs_no_improve >= trainer.patience else '否'}")
    print(f"  Embedding 余弦相似度统计:")
    cos_sims = []
    for i in range(len(embeddings)):
        for j in range(i + 1, len(embeddings)):
            cos = np.dot(embeddings[i], embeddings[j]) / (
                np.linalg.norm(embeddings[i]) * np.linalg.norm(embeddings[j])
            )
            cos_sims.append(cos)
    print(f"    均值: {np.mean(cos_sims):.4f}")
    print(f"    标准差: {np.std(cos_sims):.4f}")
    print(f"    最大值: {np.max(cos_sims):.4f}")
    print(f"    最小值: {np.min(cos_sims):.4f}")
    print(f"{'='*60}")


if __name__ == "__main__":
    main()
