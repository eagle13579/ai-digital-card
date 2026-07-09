"""
芯森态·支付集成服务骨架
订单创建 + 支付网关接口 + 回调处理 + 订阅激活
待接入: 微信支付/支付宝商户号后替换 mock 实现
"""
import json, logging, os, sqlite3, secrets
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)
DB = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
                  "api", "data", "xinsentai.db")

PRICING = {
    "basic": {"name": "基础版", "price": 999, "period_days": 30},
    "standard": {"name": "标准版", "price": 1999, "period_days": 30},
    "flagship": {"name": "旗舰版", "price": 3999, "period_days": 30},
}

def _ensure_tables():
    c = sqlite3.connect(DB)
    c.execute("""
        CREATE TABLE IF NOT EXISTS payment_orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            order_no TEXT UNIQUE NOT NULL,
            user_id INTEGER,
            tenant_id TEXT,
            plan TEXT NOT NULL,
            amount REAL NOT NULL,
            status TEXT DEFAULT 'pending',
            payment_method TEXT,
            paid_at TEXT,
            expire_at TEXT,
            created_at TEXT DEFAULT (datetime('now'))
        )
    """)
    c.execute("""
        CREATE TABLE IF NOT EXISTS subscriptions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            tenant_id TEXT,
            plan TEXT NOT NULL,
            status TEXT DEFAULT 'active',
            started_at TEXT DEFAULT (datetime('now')),
            expire_at TEXT,
            auto_renew INTEGER DEFAULT 1,
            cancelled_at TEXT
        )
    """)
    c.commit()
    c.close()

def create_order(user_id: int, tenant_id: str, plan: str) -> dict:
    """创建支付订单"""
    if plan not in PRICING:
        raise ValueError(f"无效套餐: {plan}")
    
    _ensure_tables()
    plan_info = PRICING[plan]
    order_no = f"ORD{datetime.now():%Y%m%d%H%M%S}{secrets.token_hex(4).upper()}"
    
    c = sqlite3.connect(DB)
    try:
        c.execute(
            "INSERT INTO payment_orders (order_no, user_id, tenant_id, plan, amount, expire_at) VALUES (?,?,?,?,?,datetime('now','+1 hour'))",
            (order_no, user_id, tenant_id, plan, plan_info["price"])
        )
        c.commit()
        order = dict(c.execute("SELECT * FROM payment_orders WHERE order_no=?", (order_no,)).fetchone())
        logger.info(f"订单已创建: {order_no}, 套餐: {plan}, 金额: {plan_info['price']}")
        return {
            "order_no": order_no,
            "amount": plan_info["price"],
            "plan": plan,
            "plan_name": plan_info["name"],
            "status": "pending",
            "pay_url": f"/payment/{order_no}",  # 前端支付页面
        }
    finally:
        c.close()

def process_payment(order_no: str, method: str = "mock") -> dict:
    """模拟支付处理（替换为真实支付网关调用）"""
    c = sqlite3.connect(DB)
    try:
        order = c.execute("SELECT * FROM payment_orders WHERE order_no=?", (order_no,)).fetchone()
        if not order:
            return {"success": False, "error": "订单不存在"}
        if order[6] != "pending":  # status column
            return {"success": False, "error": f"订单状态异常: {order[6]}"}
        
        # Mock: 模拟支付成功
        c.execute(
            "UPDATE payment_orders SET status='paid', payment_method=?, paid_at=datetime('now') WHERE order_no=?",
            (method, order_no)
        )
        c.commit()
        
        # 激活订阅
        plan = order[4]
        period = PRICING[plan]["period_days"]
        c.execute(
            "INSERT INTO subscriptions (user_id, tenant_id, plan, expire_at) VALUES (?,?,?,datetime('now','+? days'))",
            (order[2], order[3], plan, period)
        )
        c.commit()
        
        logger.info(f"支付成功: {order_no}, 套餐: {plan}")
        return {"success": True, "order_no": order_no, "plan": plan}
    finally:
        c.close()

def get_subscription(user_id: int) -> dict:
    """查询用户当前订阅"""
    c = sqlite3.connect(DB)
    try:
        sub = c.execute(
            "SELECT * FROM subscriptions WHERE user_id=? AND status='active' ORDER BY id DESC LIMIT 1",
            (user_id,)
        ).fetchone()
        if not sub:
            return {"active": False, "plan": None}
        return {"active": True, "plan": sub[3], "expire_at": sub[5], "auto_renew": bool(sub[6])}
    finally:
        c.close()
