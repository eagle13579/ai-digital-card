"""
数据库 MCP 工具 — AI数智名片
直接查询 SQLite 数据库，支持任意 SQL（只读模式）
"""
import sqlite3
import os
import json
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("AI 数智名片 - 数据库查询工具")

DB_PATH = os.path.join(os.path.dirname(__file__), '..', 'backend', 'data', 'digital_brochure.db')
DB_PATH = os.path.normpath(DB_PATH)


def get_db() -> sqlite3.Connection:
    """获取只读数据库连接"""
    conn = sqlite3.connect(f"file:{DB_PATH}?mode=ro", uri=True)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA query_only = ON")
    return conn


@mcp.tool()
def list_tables() -> list[dict]:
    """列出数据库中所有表及其行数、字段列表"""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
    tables = []
    for row in cursor.fetchall():
        name = row[0]
        # 行数
        cursor.execute(f"SELECT COUNT(*) FROM \"{name}\"")
        row_count = cursor.fetchone()[0]
        # 字段
        cursor.execute(f"PRAGMA table_info(\"{name}\")")
        columns = [{"name": c[1], "type": c[2], "nullable": not c[3]} for c in cursor.fetchall()]
        tables.append({"name": name, "row_count": row_count, "columns": columns})
    conn.close()
    return tables


@mcp.tool()
def query(sql: str, params: dict = None) -> list[dict]:
    """
    执行只读 SQL 查询

    参数:
        sql: SQL 语句（仅支持 SELECT）
        params: 可选参数（如 {"id": 1}）

    示例:
        query("SELECT * FROM users WHERE membership_tier = :tier", {"tier": "gold"})
        query("SELECT tag, weight FROM user_tags WHERE user_id = :uid and tag_type = 'provide'", {"uid": 1})
    """
    sql_upper = sql.strip().upper()
    if not sql_upper.startswith("SELECT") and not sql_upper.startswith("PRAGMA") and not sql_upper.startswith("EXPLAIN"):
        return [{"error": "仅支持 SELECT 查询（只读模式）"}]

    conn = get_db()
    cursor = conn.cursor()
    try:
        if params:
            cursor.execute(sql, params)
        else:
            cursor.execute(sql)
        rows = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return rows
    except Exception as e:
        conn.close()
        return [{"error": str(e)}]


@mcp.tool()
def get_user_detail(user_id: int) -> dict:
    """获取用户详细信息（含标签和画册统计）"""
    conn = get_db()
    cursor = conn.cursor()

    # 用户信息
    cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))
    user = dict(cursor.fetchone() or {})

    if not user:
        conn.close()
        return {"error": f"用户 {user_id} 不存在"}

    # 排除敏感字段
    user.pop("password_hash", None)
    user.pop("wechat_openid", None)

    # 统计
    cursor.execute("SELECT COUNT(*) FROM brochures WHERE user_id = ?", (user_id,))
    user["brochure_count"] = cursor.fetchone()[0]

    cursor.execute("SELECT tag, tag_type, weight FROM user_tags WHERE user_id = ?", (user_id,))
    user["tags"] = [dict(r) for r in cursor.fetchall()]

    cursor.execute("SELECT COUNT(*) FROM match_records WHERE user_a_id = ? OR user_b_id = ?", (user_id, user_id))
    user["match_count"] = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM connections WHERE user_id = ? AND status = 'approved'", (user_id,))
    user["connection_count"] = cursor.fetchone()[0]

    conn.close()
    return user


@mcp.tool()
def get_business_summary() -> dict:
    """获取业务总览数据（用户数、名片数、匹配数等）"""
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) FROM users")
    total_users = cursor.fetchone()[0]

    cursor.execute("SELECT membership_tier, COUNT(*) as cnt FROM users GROUP BY membership_tier")
    tier_dist = {r[0]: r[1] for r in cursor.fetchall()}

    cursor.execute("SELECT COUNT(*) FROM brochures")
    total_brochures = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM brochures WHERE status = 'published'")
    published_brochures = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM user_tags")
    total_tags = cursor.fetchone()[0]

    cursor.execute("SELECT tag_type, COUNT(*) as cnt FROM user_tags GROUP BY tag_type")
    tag_types = {r[0]: r[1] for r in cursor.fetchall()}

    cursor.execute("SELECT COUNT(*) FROM match_records")
    total_matches = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM connections WHERE status = 'approved'")
    total_connections = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM visitor_logs")
    total_visits = cursor.fetchone()[0]

    conn.close()
    return {
        "users": {"total": total_users, "by_tier": tier_dist},
        "brochures": {"total": total_brochures, "published": published_brochures},
        "tags": {"total": total_tags, "by_type": tag_types},
        "matches": {"total": total_matches},
        "connections": {"total": total_connections},
        "visits": {"total": total_visits},
    }


if __name__ == "__main__":
    mcp.run(transport="stdio")
