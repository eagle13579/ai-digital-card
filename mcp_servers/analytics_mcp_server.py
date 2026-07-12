"""
数据分析 MCP 工具 — AI数智名片
用户行为分析、趋势分析、业务洞察
"""
import sqlite3
import os
import json
from datetime import datetime, timedelta
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("AI 数智名片 - 数据分析工具")

DB_PATH = os.path.normpath(os.path.join(os.path.dirname(__file__), '..', 'backend', 'data', 'digital_brochure.db'))


def get_db() -> sqlite3.Connection:
    conn = sqlite3.connect(f"file:{DB_PATH}?mode=ro", uri=True)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA query_only = ON")
    return conn


@mcp.tool()
def user_analysis() -> dict:
    """
    用户分析报告：
    - 注册趋势（暂无时间序列时输出当前快照）
    - 会员等级分布
    - 用户标签覆盖
    - 活跃度概览
    """
    conn = get_db()
    cursor = conn.cursor()

    # 会员分布
    cursor.execute("SELECT membership_tier, COUNT(*) as cnt FROM users GROUP BY membership_tier ORDER BY cnt DESC")
    tier_dist = [dict(r) for r in cursor.fetchall()]

    # 完整率（有公司+职位+简介的比例）
    cursor.execute("SELECT COUNT(*) FROM users WHERE company != '' AND company IS NOT NULL")
    has_company = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM users WHERE title != '' AND title IS NOT NULL")
    has_title = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM users WHERE intro != '' AND intro IS NOT NULL")
    has_intro = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM users")
    total_users = cursor.fetchone()[0]

    # 标签分布
    cursor.execute("SELECT tag_type, COUNT(DISTINCT user_id) as users, COUNT(*) as total FROM user_tags GROUP BY tag_type")
    tag_stats = [dict(r) for r in cursor.fetchall()]

    # 热门标签
    cursor.execute("""
        SELECT tag, COUNT(*) as cnt FROM user_tags 
        GROUP BY tag ORDER BY cnt DESC LIMIT 10
    """)
    hot_tags = [dict(r) for r in cursor.fetchall()]

    # 有标签的用户数
    cursor.execute("SELECT COUNT(DISTINCT user_id) FROM user_tags")
    users_with_tags = cursor.fetchone()[0]

    conn.close()
    return {
        "total_users": total_users,
        "profile_completeness": {
            "has_company": f"{has_company}/{total_users} ({round(has_company/total_users*100 if total_users else 0)}%)",
            "has_title": f"{has_title}/{total_users} ({round(has_title/total_users*100 if total_users else 0)}%)",
            "has_intro": f"{has_intro}/{total_users} ({round(has_intro/total_users*100 if total_users else 0)}%)",
        },
        "member_tier_distribution": tier_dist,
        "tag_coverage": {
            "users_with_tags": f"{users_with_tags}/{total_users}",
            "by_type": tag_stats,
            "top_tags": hot_tags,
        },
    }


@mcp.tool()
def match_analysis() -> dict:
    """
    匹配数据分析：
    - 总匹配数、已连接数
    - 平均匹配分
    - 匹配来源分布
    """
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) FROM match_records")
    total = cursor.fetchone()[0]

    if total == 0:
        conn.close()
        return {
            "total_matches": 0,
            "message": "暂无可匹配数据，需要先用用户标签运行匹配引擎",
            "suggestion": "请在用户标签（user_tags 表）中添加标签数据后运行匹配引擎"
        }

    cursor.execute("SELECT status, COUNT(*) as cnt FROM match_records GROUP BY status")
    status_dist = [dict(r) for r in cursor.fetchall()]

    cursor.execute("SELECT AVG(match_score) FROM match_records")
    avg_score = round(cursor.fetchone()[0] or 0, 2)

    cursor.execute("SELECT source, COUNT(*) as cnt FROM match_records GROUP BY source")
    source_dist = [dict(r) for r in cursor.fetchall()]

    cursor.execute("""
        SELECT u.name, m.match_score, m.created_at
        FROM match_records m
        JOIN users u ON u.id = m.user_a_id
        ORDER BY m.match_score DESC LIMIT 5
    """)
    top_matches = [dict(r) for r in cursor.fetchall()]

    cursor.execute("SELECT COUNT(*) FROM connections")
    connections = cursor.fetchone()[0]

    conn.close()
    return {
        "total_matches": total,
        "avg_match_score": avg_score,
        "by_status": status_dist,
        "by_source": source_dist,
        "top_matches": top_matches,
        "connections_established": connections,
    }


@mcp.tool()
def visitor_analysis() -> dict:
    """
    访客数据分析：
    - 总访问数
    - 访问来源分布
    - 感兴趣的用户
    """
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) FROM visitor_logs")
    total_visits = cursor.fetchone()[0]

    if total_visits == 0:
        conn.close()
        return {"total_visits": 0, "message": "暂无访客数据"}

    cursor.execute("SELECT source, COUNT(*) as cnt FROM visitor_logs GROUP BY source ORDER BY cnt DESC")
    source_dist = [dict(r) for r in cursor.fetchall()]

    cursor.execute("SELECT COUNT(*) FROM visitor_logs WHERE interested = 1")
    interested = cursor.fetchone()[0]

    cursor.execute("""
        SELECT b.title, COUNT(*) as visits 
        FROM visitor_logs v 
        JOIN brochures b ON b.id = v.brochure_id 
        GROUP BY v.brochure_id ORDER BY visits DESC LIMIT 5
    """)
    top_brochures = [dict(r) for r in cursor.fetchall()]

    cursor.execute("SELECT AVG(duration) FROM visitor_logs WHERE duration > 0")
    avg_duration = round(cursor.fetchone()[0] or 0, 1)

    conn.close()
    return {
        "total_visits": total_visits,
        "interested_rate": f"{interested}/{total_visits} ({round(interested/total_visits*100 if total_visits else 0)}%)",
        "by_source": source_dist,
        "avg_duration_seconds": avg_duration,
        "most_visited_brochures": top_brochures,
    }


@mcp.tool()
def business_snapshot() -> str:
    """一句话业务快照：当前用户数/名片数/匹配数/连接数/访客数"""
    conn = get_db()
    cursor = conn.cursor()

    counts = {}
    for name, sql in [
        ("users", "SELECT COUNT(*) FROM users"),
        ("brochures", "SELECT COUNT(*) FROM brochures"),
        ("published_brochures", "SELECT COUNT(*) FROM brochures WHERE status='published'"),
        ("tags", "SELECT COUNT(*) FROM user_tags"),
        ("matches", "SELECT COUNT(*) FROM match_records"),
        ("connections", "SELECT COUNT(*) FROM connections WHERE status='approved'"),
        ("visits", "SELECT COUNT(*) FROM visitor_logs"),
    ]:
        cursor.execute(sql)
        counts[name] = cursor.fetchone()[0]

    conn.close()
    return (
        f"📊 AI数智名片 业务快照\n"
        f"用户 {counts['users']} 人 · 名片 {counts['brochures']} 张 (已发布 {counts['published_brochures']}) · "
        f"标签 {counts['tags']} 个 · 匹配 {counts['matches']} 次 · "
        f"连接 {counts['connections']} 个 · 访客 {counts['visits']} 次"
    )


if __name__ == "__main__":
    mcp.run(transport="stdio")
