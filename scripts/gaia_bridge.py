#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
芯森态 → 盖娅大脑 数据桥接脚本
将芯森态业务指标写入盖娅大脑 knowledge_models 表，供盖娅认知训练使用。

触发方式（保留原有 cron）：
    python scripts/gaia_bridge.py

每30分钟自动运行一次，每次更新 latest 快照，并记录桥接日志。
"""

import json
import logging
import os
import sqlite3
import sys
from datetime import datetime
from typing import Any, Dict, List, Optional

# ── 路径常量 ──────────────────────────────────────────────
PALACE_ROOT = r"D:\向海容的知识库\wiki\wiki\记忆宫殿"
XINSENTAI_ROOT = os.path.join(PALACE_ROOT, "L5孵化室", "产品开发", "芯森态")
BRIDGE_LOG = os.path.join(XINSENTAI_ROOT, "data", "bridge_log.jsonl")

# 芯森态主库（默认租户）
XINSENTAI_DB = os.path.join(XINSENTAI_ROOT, "code", "api", "data", "xinsentai.db")

# 盖娅大脑知识库
GAIA_KNOWLEDGE_DB = os.path.join(PALACE_ROOT, "brain_daemon", "knowledge_models.db")

# ── 日志 ──────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("GaiaBridge")


# ============================================================
#  工具函数
# ============================================================

def log_bridge_event(event_type: str, source: str, status: str, detail: str = ""):
    """写入桥接日志到 JSONL 文件"""
    os.makedirs(os.path.dirname(BRIDGE_LOG), exist_ok=True)
    entry = {
        "timestamp": datetime.now().isoformat(),
        "event_type": event_type,
        "source": source,
        "status": status,
        "detail": detail,
    }
    with open(BRIDGE_LOG, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")
    return entry


def safe_db_query(db_path: str, sql: str, params: tuple = ()) -> List[tuple]:
    """安全执行 SQL 查询，自动处理 DB 不存在等情况"""
    if not os.path.isfile(db_path):
        logger.warning(f"数据库不存在: {db_path}")
        return []
    try:
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute(sql, params)
        rows = cursor.fetchall()
        conn.close()
        return rows
    except sqlite3.Error as e:
        logger.error(f"数据库查询失败 [{db_path}]: {e}")
        return []


# ============================================================
#  数据采集：从芯森态读取指标
# ============================================================

def collect_xinsentai_metrics() -> Dict[str, Any]:
    """从芯森态主库采集核心业务指标"""
    metrics = {
        "tenant_count": 0,
        "total_users": 0,
        "total_scores": 0,
        "total_grades": 0,
        "total_leads": 0,
        "lead_count": 0,
        "lead_hot": 0,
        "total_contracts": 0,
        "contract_count": 0,
        "contract_amount": 0.0,
        "total_auth_accounts": 0,
        "grade_distribution": {},
        "dimension_avg": {},
        "city_count": 0,
        "audit_7d": 0,
        "last_bridge_time": datetime.now().isoformat(),
        "errors": [],
    }

    # ── 从主库读取 ──
    db = XINSENTAI_DB
    if not os.path.isfile(db):
        metrics["errors"].append(f"芯森态主库不存在: {db}")
        logger.warning(f"芯森态主库不存在: {db}")
        return metrics

    try:
        conn = sqlite3.connect(db)
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()

        # 1. 用户数
        cur.execute("SELECT COUNT(*) AS cnt FROM users")
        metrics["total_users"] = cur.fetchone()["cnt"]

        # 2. 评分记录数
        cur.execute("SELECT COUNT(*) AS cnt FROM scores")
        metrics["total_scores"] = cur.fetchone()["cnt"]

        # 3. 经销商等级数
        cur.execute("SELECT COUNT(*) AS cnt FROM dealer_grades")
        metrics["total_grades"] = cur.fetchone()["cnt"]

        # 4. 线索数
        cur.execute("SELECT COUNT(*) AS cnt FROM leads")
        metrics["total_leads"] = cur.fetchone()["cnt"]

        # 5. 合同数
        cur.execute("SELECT COUNT(*) AS cnt FROM contracts")
        metrics["total_contracts"] = cur.fetchone()["cnt"]
        metrics["contract_count"] = metrics["total_contracts"]  # 别名兼容
        cur.execute("SELECT COALESCE(SUM(amount),0) AS total FROM contracts")
        metrics["contract_amount"] = round(cur.fetchone()["total"], 2)

        # 5b. 线索补充指标
        cur.execute("SELECT COUNT(*) AS cnt FROM leads WHERE status IN ('new','contacted','qualified')")
        metrics["lead_count"] = cur.fetchone()["cnt"]
        lead_row = cur.execute("SELECT COUNT(*) AS cnt FROM leads WHERE status='hot'").fetchone()
        metrics["lead_hot"] = lead_row["cnt"] if lead_row else 0

        # 5c. 近7天审核数
        cur.execute("SELECT COUNT(*) AS cnt FROM dealer_grades WHERE created_at >= datetime('now','-7 days','localtime')")
        metrics["audit_7d"] = cur.fetchone()["cnt"]

        # 6. 注册租户数
        cur.execute("SELECT COUNT(*) AS cnt FROM auth_accounts")
        metrics["total_auth_accounts"] = cur.fetchone()["cnt"]

        # 7. 分级分布 (最新批次)
        cur.execute("""
            SELECT grade, COUNT(*) AS cnt
            FROM scores
            WHERE batch_id = (SELECT batch_id FROM scores ORDER BY scored_at DESC LIMIT 1)
            GROUP BY grade
            ORDER BY grade
        """)
        grade_dist = {}
        for row in cur.fetchall():
            grade_dist[row["grade"]] = row["cnt"]
        metrics["grade_distribution"] = grade_dist

        # 8. 六维评分均值
        cur.execute("""
            SELECT
                ROUND(AVG(score_活跃度), 1)    AS 活跃度,
                ROUND(AVG(score_购买力), 1)    AS 购买力,
                ROUND(AVG(score_内容共鸣), 1)  AS 内容共鸣,
                ROUND(AVG(score_影响力), 1)    AS 影响力,
                ROUND(AVG(score_城市匹配), 1)  AS 城市匹配,
                ROUND(AVG(score_信任度), 1)    AS 信任度,
                ROUND(AVG(total_score), 1)     AS 总分
            FROM scores
            WHERE batch_id = (SELECT batch_id FROM scores ORDER BY scored_at DESC LIMIT 1)
        """)
        dim_avg = dict(cur.fetchone())
        metrics["dimension_avg"] = dim_avg

        # 9. 城市数
        cur.execute(
            "SELECT COUNT(DISTINCT city) AS cnt FROM users WHERE city != '' AND city != '未知'"
        )
        metrics["city_count"] = cur.fetchone()["cnt"]

        # 10. 租户目录数（估算活跃租户）
        tenants_dir = os.path.join(XINSENTAI_ROOT, "code", "data", "tenants")
        if os.path.isdir(tenants_dir):
            dir_count = len([d for d in os.listdir(tenants_dir)
                             if os.path.isdir(os.path.join(tenants_dir, d))])
            cur.execute("SELECT COUNT(DISTINCT tenant_id) AS cnt FROM auth_accounts")
            auth_tenant_count = cur.fetchone()["cnt"]
            metrics["tenant_count"] = max(dir_count, auth_tenant_count)

        conn.close()
        logger.info(f"芯森态数据采集完成: 用户={metrics['total_users']}, "
                     f"评分={metrics['total_scores']}, "
                     f"等级={metrics['total_grades']}, "
                     f"租户={metrics['tenant_count']}")

    except sqlite3.Error as e:
        msg = f"芯森态主库读取异常: {e}"
        metrics["errors"].append(msg)
        logger.error(msg)

    except Exception as e:
        msg = f"数据采集异常: {e}"
        metrics["errors"].append(msg)
        logger.error(msg)

    return metrics


# ============================================================
#  数据写入：写入盖娅大脑 knowledge_models 表
#  注意：该表有 UNIQUE(source, title) 索引，
#  因此使用 INSERT OR REPLACE 来更新最新快照
# ============================================================

def ensure_knowledge_schema(db_path: str):
    """确保盖娅大脑的 knowledge_models 表结构兼容"""
    try:
        conn = sqlite3.connect(db_path)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS knowledge_models (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                source      TEXT NOT NULL DEFAULT '',
                category    TEXT NOT NULL DEFAULT '',
                title       TEXT NOT NULL DEFAULT '',
                content     TEXT NOT NULL DEFAULT '',
                tags        TEXT NOT NULL DEFAULT '[]',
                created_at  TEXT NOT NULL DEFAULT (datetime('now','localtime')),
                ref_count   INTEGER NOT NULL DEFAULT 0
            )
        """)
        conn.commit()
        conn.close()
    except sqlite3.Error:
        pass  # 表已存在则忽略


def write_metrics_to_gaia(metrics: Dict[str, Any]) -> int:
    """将采集的指标写入盖娅大脑 knowledge_models 表（幂等更新）

    使用 INSERT OR REPLACE 确保唯一索引 (source, title) 约束下每次运行都更新最新数据，
    避免重复积累，同时保留每次运行都会刷新快照。
    """
    db = GAIA_KNOWLEDGE_DB
    os.makedirs(os.path.dirname(db), exist_ok=True)
    ensure_knowledge_schema(db)

    now = datetime.now().isoformat()
    source = "xinsentai-bridge"

    # 构造写入条目（title 固定，每次 REPLACE）
    entries = []

    # ── 1. 总览快照 ──
    overview_content = json.dumps({
        "tenant_count": metrics["tenant_count"],
        "total_users": metrics["total_users"],
        "total_scores": metrics["total_scores"],
        "total_grades": metrics["total_grades"],
        "total_leads": metrics["total_leads"],
        "total_contracts": metrics["total_contracts"],
        "total_auth_accounts": metrics["total_auth_accounts"],
        "contract_count": metrics["contract_count"],
        "total_amount": round(metrics["contract_amount"],2),
        "lead_count": metrics["lead_count"],
        "lead_hot": metrics["lead_hot"],
        "audit_7d": metrics["audit_7d"],
        "city_count": metrics["city_count"],
        "collected_at": now,
    }, ensure_ascii=False)
    entries.append({
        "title": "芯森态总览快照",
        "category": "xinsentai_metrics",
        "content": overview_content,
        "tags": json.dumps(["xinsentai", "overview", "metrics"], ensure_ascii=False),
    })

    # ── 2. 分级分布 ──
    if metrics["grade_distribution"]:
        grade_content = json.dumps(metrics["grade_distribution"], ensure_ascii=False)
        entries.append({
            "title": "芯森态经销商分级分布",
            "category": "xinsentai_metrics",
            "content": grade_content,
            "tags": json.dumps(["xinsentai", "grade", "distribution"], ensure_ascii=False),
        })

    # ── 3. 六维评分均值 ──
    if metrics["dimension_avg"]:
        dim_content = json.dumps(metrics["dimension_avg"], ensure_ascii=False)
        entries.append({
            "title": "芯森态六维评分均值",
            "category": "xinsentai_metrics",
            "content": dim_content,
            "tags": json.dumps(["xinsentai", "dimension", "average"], ensure_ascii=False),
        })

    # ── 4. 异常记录（如果有） ──
    if metrics.get("errors"):
        entries.append({
            "title": "芯森态桥接异常",
            "category": "xinsentai_errors",
            "content": json.dumps(metrics["errors"], ensure_ascii=False),
            "tags": json.dumps(["xinsentai", "error"], ensure_ascii=False),
        })

    # 批量写入（INSERT OR REPLACE — 利用 unique(source, title) 索引）
    written = 0
    try:
        conn = sqlite3.connect(db)
        cur = conn.cursor()
        for entry in entries:
            cur.execute("""
                INSERT OR REPLACE INTO knowledge_models
                    (source, category, title, content, tags, created_at)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                source,
                entry["category"],
                entry["title"],
                entry["content"],
                entry["tags"],
                now,
            ))
            written += 1
        conn.commit()
        conn.close()
        logger.info(f"成功写入/更新 {written} 条知识条目到盖娅大脑")
    except sqlite3.Error as e:
        logger.error(f"写入盖娅大脑失败: {e}")
        written = 0

    return written


# ============================================================
#  主流程
# ============================================================

def bridge_xinsentai_to_gaia() -> List[Dict[str, Any]]:
    """芯森态→盖娅大脑 主桥接流程"""
    results = []
    logger.info("=" * 60)
    logger.info("芯森态 → 盖娅大脑 数据桥接开始")
    logger.info(f"芯森态主库: {XINSENTAI_DB}")
    logger.info(f"盖娅大脑:    {GAIA_KNOWLEDGE_DB}")
    logger.info("=" * 60)

    # Step 1: 采集数据
    logger.info("[Step 1/3] 采集芯森态业务指标...")
    metrics = collect_xinsentai_metrics()

    # Step 2: 写入盖娅大脑
    logger.info("[Step 2/3] 写入盖娅大脑 knowledge_models 表...")
    written = write_metrics_to_gaia(metrics)

    # Step 3: 日志记录
    logger.info("[Step 3/3] 记录桥接日志...")
    status = "success" if written > 0 else "failed"
    detail_parts = [
        f"采集项: {len(metrics)}",
        f"写入: {written} 条",
        f"用户: {metrics['total_users']}",
        f"评分: {metrics['total_scores']}",
        f"等级: {metrics['total_grades']}",
        f"租户: {metrics['tenant_count']}",
    ]
    if metrics.get("errors"):
        detail_parts.append(f"异常: {len(metrics['errors'])} 项")
        status = "partial"

    detail = " | ".join(detail_parts)
    entry = log_bridge_event("bridge_run", "芯森态→盖娅大脑", status, detail)
    results.append(entry)

    logger.info(f"桥接完成: status={status}, detail={detail}")
    logger.info("=" * 60)
    return results


# ============================================================
#  入口
# ============================================================

if __name__ == "__main__":
    results = bridge_xinsentai_to_gaia()
    print(json.dumps(results, ensure_ascii=False, indent=2))
    # 返回码让 cron / CI 可判断
    if any(r.get("status") == "failed" for r in results):
        sys.exit(1)
