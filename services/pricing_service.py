"""
芯森态·定价跟踪埋点服务
记录: 定价页浏览/试用点击/商务咨询/注册转化
用法: from api.services.pricing_service import record_pricing_click
"""
import json, logging, sqlite3, os
from datetime import datetime

logger = logging.getLogger(__name__)
DB = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
                  "api", "data", "xinsentai.db")

def _ensure_table():
    """确保 pricing_events 表存在"""
    c = sqlite3.connect(DB)
    c.execute("""
        CREATE TABLE IF NOT EXISTS pricing_events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT,
            plan TEXT,
            action_type TEXT,
            page_url TEXT,
            ip_address TEXT,
            user_agent TEXT,
            created_at TEXT DEFAULT (datetime('now'))
        )
    """)
    c.execute("CREATE INDEX IF NOT EXISTS idx_pricing_action ON pricing_events(action_type)")
    c.commit()
    c.close()

def record_pricing_click(user_id=None, plan=None, action_type="view_pricing",
                          page_url=None, ip_address=None, user_agent=None):
    """
    记录定价相关行为
    action_type: view_pricing / click_trial / click_contact / register_after_pricing
    plan: basic / standard / flagship
    """
    _ensure_table()
    c = sqlite3.connect(DB)
    try:
        c.execute(
            "INSERT INTO pricing_events (user_id, plan, action_type, page_url, ip_address, user_agent) VALUES (?,?,?,?,?,?)",
            (str(user_id) if user_id else None, plan, action_type, page_url, ip_address, user_agent)
        )
        c.commit()
    finally:
        c.close()

def get_pricing_stats():
    """获取定价统计: 各计划点击次数、注册转化率"""
    _ensure_table()
    c = sqlite3.connect(DB)
    try:
        total_views = c.execute("SELECT COUNT(*) FROM pricing_events WHERE action_type='view_pricing'").fetchone()[0]
        total_trials = c.execute("SELECT COUNT(*) FROM pricing_events WHERE action_type='click_trial'").fetchone()[0]
        total_contacts = c.execute("SELECT COUNT(*) FROM pricing_events WHERE action_type='click_contact'").fetchone()[0]
        plan_breakdown = c.execute(
            "SELECT plan, action_type, COUNT(*) FROM pricing_events GROUP BY plan, action_type"
        ).fetchall()
        return {
            "total_views": total_views,
            "total_trials": total_trials,
            "total_contacts": total_contacts,
            "trial_conversion_rate": round(total_trials / total_views * 100, 1) if total_views > 0 else 0,
            "plan_breakdown": [{"plan": r[0], "action": r[1], "count": r[2]} for r in plan_breakdown]
        }
    finally:
        c.close()
