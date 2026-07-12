"""
匹配引擎 MCP 工具 — AI数智名片
基于标签的实时匹配推荐引擎
"""
import sqlite3
import os
import json
from collections import defaultdict
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("AI 数智名片 - 匹配引擎")

DB_PATH = os.path.normpath(os.path.join(os.path.dirname(__file__), '..', 'backend', 'data', 'digital_brochure.db'))


def get_db() -> sqlite3.Connection:
    conn = sqlite3.connect(f"file:{DB_PATH}?mode=ro", uri=True)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA query_only = ON")
    return conn


@mcp.tool()
def get_user_tags(user_id: int = None) -> dict:
    """
    获取用户标签（可供/需求）

    参数:
        user_id: 用户ID，不传则返回所有用户标签统计
    """
    conn = get_db()
    cursor = conn.cursor()

    if user_id:
        cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))
        user = cursor.fetchone()
        if not user:
            conn.close()
            return {"error": f"用户 {user_id} 不存在"}

        cursor.execute("SELECT * FROM user_tags WHERE user_id = ?", (user_id,))
        tags = [dict(r) for r in cursor.fetchall()]

        provides = [t for t in tags if t['tag_type'] == 'provide']
        needs = [t for t in tags if t['tag_type'] == 'need']

        conn.close()
        return {
            "user_id": user_id,
            "user_name": user['name'],
            "company": user['company'],
            "title": user['title'],
            "provides": [{"tag": t['tag'], "weight": t['weight']} for t in provides],
            "needs": [{"tag": t['tag'], "weight": t['weight']} for t in needs],
        }
    else:
        cursor.execute("SELECT COUNT(*) FROM user_tags")
        total = cursor.fetchone()[0]
        cursor.execute("SELECT tag_type, COUNT(*) as cnt FROM user_tags GROUP BY tag_type")
        stats = [dict(r) for r in cursor.fetchall()]
        cursor.execute("SELECT COUNT(DISTINCT user_id) FROM user_tags")
        users_with_tags = cursor.fetchone()[0]
        conn.close()
        return {
            "total_tags": total,
            "by_type": stats,
            "users_with_tags": users_with_tags,
        }


@mcp.tool()
def recommend_matches(user_id: int, top_k: int = 10, min_score: float = 0.1) -> list[dict]:
    """
    为指定用户计算匹配推荐。
    算法：双向标签匹配评分（提供→需求 + 需求→提供）

    参数:
        user_id: 目标用户ID
        top_k: 返回前N个推荐（默认10）
        min_score: 最低匹配分 (0-1)
    """
    conn = get_db()
    cursor = conn.cursor()

    # 验证用户
    cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))
    user = cursor.fetchone()
    if not user:
        conn.close()
        return [{"error": f"用户 {user_id} 不存在"}]

    # 获取当前用户的标签
    cursor.execute("SELECT * FROM user_tags WHERE user_id = ?", (user_id,))
    my_tags = [dict(r) for r in cursor.fetchall()]

    my_provides = {t['tag']: t['weight'] for t in my_tags if t['tag_type'] == 'provide'}
    my_needs = {t['tag']: t['weight'] for t in my_tags if t['tag_type'] == 'need'}

    if not my_provides and not my_needs:
        conn.close()
        return [{
            "message": "当前用户没有标签数据，无法计算匹配。请先添加供需标签。",
            "recommendation": "前往用户设置页面添加你的能力（提供）和需求标签"
        }]

    # 获取所有其他用户的标签
    cursor.execute("SELECT DISTINCT user_id FROM user_tags WHERE user_id != ?", (user_id,))
    other_user_ids = [r[0] for r in cursor.fetchall()]

    if not other_user_ids:
        conn.close()
        return [{"message": "系统内暂无其他用户，无法匹配"}]

    results = []

    for other_id in other_user_ids:
        cursor.execute("SELECT * FROM user_tags WHERE user_id = ?", (other_id,))
        other_tags = [dict(r) for r in cursor.fetchall()]
        other_provides = {t['tag']: t['weight'] for t in other_tags if t['tag_type'] == 'provide'}
        other_needs = {t['tag']: t['weight'] for t in other_tags if t['tag_type'] == 'need'}

        # 双向匹配分
        score = 0.0
        max_score = 0.0
        matched_tags = set()

        # 我提供 匹配 对方需要
        for tag, w in my_provides.items():
            if tag in other_needs:
                s = w * other_needs[tag]
                score += s
                matched_tags.add(tag)
            max_score += w * 5  # 假设对方权重最大5

        # 我需要 匹配 对方提供
        for tag, w in my_needs.items():
            if tag in other_provides:
                s = w * other_provides[tag]
                score += s
                matched_tags.add(tag)
            max_score += w * 5

        if max_score > 0:
            final_score = score / max_score
            if final_score >= min_score:
                # 获取对方基础信息
                cursor.execute("SELECT id, name, company, title, membership_tier FROM users WHERE id = ?", (other_id,))
                other_info = dict(cursor.fetchone())

                # 脱敏处理（free会员）
                if other_info.get('membership_tier') in ('free', None):
                    name = other_info.get('name', '')
                    other_info['name'] = name[:1] + '*' * len(name[1:]) if len(name) > 1 else (name[:1] + '*' if name else '匿名')
                    other_info['company'] = other_info.get('company', '')[:2] + '**' if other_info.get('company') else ''

                results.append({
                    "user_id": other_id,
                    "name": other_info.get('name', '未知'),
                    "company": other_info.get('company', ''),
                    "title": other_info.get('title', ''),
                    "match_score": round(final_score * 100, 1),
                    "matched_tags": list(matched_tags),
                    "user_tags": {
                        "provides": [{"tag": t['tag'], "weight": t['weight']} for t in other_tags if t['tag_type'] == 'provide'],
                        "needs": [{"tag": t['tag'], "weight": t['weight']} for t in other_tags if t['tag_type'] == 'need'],
                    },
                })

    # 排序
    results.sort(key=lambda x: x['match_score'], reverse=True)

    conn.close()

    if not results:
        return [{"message": "暂无匹配，建议调整标签以扩大匹配范围"}]

    return results[:top_k]


@mcp.tool()
def run_full_match() -> dict:
    """
    全量运行匹配引擎：对所有用户两两计算匹配分，
    将结果写入 match_records 表
    """
    conn = get_db()
    cursor = conn.cursor()

    # 获取所有有标签的用户
    cursor.execute("SELECT DISTINCT user_id FROM user_tags")
    user_ids = [r[0] for r in cursor.fetchall()]

    if len(user_ids) < 2:
        conn.close()
        return {"message": "至少需要2个有标签的用户才能运行匹配", "users_with_tags": len(user_ids)}

    # 清空旧的匹配记录
    cursor.execute("DELETE FROM match_records")
    matches_created = 0

    for i, uid_a in enumerate(user_ids):
        cursor.execute("SELECT * FROM user_tags WHERE user_id = ?", (uid_a,))
        tags_a = [dict(r) for r in cursor.fetchall()]
        provides_a = {t['tag']: t['weight'] for t in tags_a if t['tag_type'] == 'provide'}
        needs_a = {t['tag']: t['weight'] for t in tags_a if t['tag_type'] == 'need'}

        for uid_b in user_ids[i + 1:]:
            cursor.execute("SELECT * FROM user_tags WHERE user_id = ?", (uid_b,))
            tags_b = [dict(r) for r in cursor.fetchall()]
            provides_b = {t['tag']: t['weight'] for t in tags_b if t['tag_type'] == 'provide'}
            needs_b = {t['tag']: t['weight'] for t in tags_b if t['tag_type'] == 'need'}

            # 双向评分
            score = 0.0
            max_score = 0.0
            common_tags = set()

            # A提供 ↔ B需要
            for tag, w in provides_a.items():
                if tag in needs_b:
                    score += w * needs_b[tag]
                    common_tags.add(tag)
                max_score += w * 5

            # A需要 ↔ B提供
            for tag, w in needs_a.items():
                if tag in provides_b:
                    score += w * provides_b[tag]
                    common_tags.add(tag)
                max_score += w * 5

            if max_score > 0 and common_tags:
                final_score = score / max_score
                # 写入 match_records
                cursor.execute(
                    "INSERT INTO match_records (user_a_id, user_b_id, match_score, status, common_tags, source) "
                    "VALUES (?, ?, ?, 'pending', ?, 'auto')",
                    (uid_a, uid_b, round(final_score, 4), json.dumps(list(common_tags)))
                )
                matches_created += 1

    conn.commit()
    conn.close()

    return {
        "message": f"全量匹配完成",
        "users_with_tags": len(user_ids),
        "matches_created": matches_created,
    }


if __name__ == "__main__":
    mcp.run(transport="stdio")
