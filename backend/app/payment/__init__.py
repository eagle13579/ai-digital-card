"""支付抽象层 — 定义统一支付接口协议。"""

from __future__ import annotations

import abc
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Optional


class PaymentChannel(str, Enum):
    """支持的支付渠道"""
    WECHAT = "wechat"
    ALIPAY = "alipay"


class PaymentStatus(str, Enum):
    """支付状态"""
    PENDING = "pending"          # 待支付
    SUCCESS = "success"          # 支付成功
    FAILED = "failed"            # 支付失败
    REFUNDING = "refunding"      # 退款中
    REFUNDED = "refunded"        # 已退款
    CLOSED = "closed"            # 已关闭


class MembershipTier(str, Enum):
    """会员等级"""
    FREE = "free"
    GOLD = "gold"
    DIAMOND = "diamond"
    BOARD = "board"


@dataclass
class ProductConfig:
    """商品配置"""
    tier: MembershipTier
    name_cn: str
    name_en: str
    price_cents: int          # 单位：分（人民币）
    duration_days: int        # 有效期（天）
    description_cn: str
    description_en: str
    quota: int = 0            # 每月解锁配额


# ── 定价表 ──────────────────────────────────────────────────────────
PRODUCTS: dict[MembershipTier, ProductConfig] = {
    MembershipTier.GOLD: ProductConfig(
        tier=MembershipTier.GOLD,
        name_cn="黄金会员",
        name_en="Gold Member",
        price_cents=2990,          # ¥29.90
        duration_days=30,
        description_cn="每月20次解锁，适合个人用户",
        description_en="20 unlocks/month, for individuals",
        quota=20,
    ),
    MembershipTier.DIAMOND: ProductConfig(
        tier=MembershipTier.DIAMOND,
        name_cn="钻石会员",
        name_en="Diamond Member",
        price_cents=8990,          # ¥89.90
        duration_days=30,
        description_cn="每月60次解锁，适合商务人士",
        description_en="60 unlocks/month, for professionals",
        quota=60,
    ),
    MembershipTier.BOARD: ProductConfig(
        tier=MembershipTier.BOARD,
        name_cn="董事会会员",
        name_en="Board Member",
        price_cents=19990,         # ¥199.90
        duration_days=30,
        description_cn="每月200次解锁，适合高端人脉",
        description_en="200 unlocks/month, for high-end networking",
        quota=200,
    ),
}


def get_product(tier: MembershipTier) -> ProductConfig:
    """按等级获取商品配置"""
    prod = PRODUCTS.get(tier)
    if not prod:
        raise ValueError(f"不支持的会员等级: {tier}")
    return prod


# ── 数据模型 ─────────────────────────────────────────────────────────

@dataclass
class OrderRequest:
    """下单请求"""
    user_id: int
    tier: MembershipTier
    channel: PaymentChannel
    openid: str = ""              # 微信 openid（微信支付必填）
    client_ip: str = "127.0.0.1"


@dataclass
class OrderResponse:
    """下单响应"""
    order_no: str                 # 内部订单号
    channel_order_no: str = ""    # 渠道订单号（微信/支付宝）
    pay_info: dict = field(default_factory=dict)  # 调起支付所需参数
    status: PaymentStatus = PaymentStatus.PENDING
    total_cents: int = 0


@dataclass
class CallbackParams:
    """支付回调通用参数"""
    channel: PaymentChannel
    raw_body: bytes
    raw_headers: dict[str, str]
    query_params: dict[str, str]


@dataclass
class CallbackResult:
    """回调验证结果"""
    valid: bool
    channel_order_no: str = ""
    order_no: str = ""
    trade_status: str = ""
    total_cents: int = 0
    paid_at: Optional[datetime] = None
    error_msg: str = ""


@dataclass
class OrderQueryResult:
    """订单查询结果"""
    order_no: str
    channel_order_no: str
    status: PaymentStatus
    total_cents: int
    paid_at: Optional[datetime] = None
    channel_response: dict[str, Any] = field(default_factory=dict)


# ── 抽象基类 ────────────────────────────────────────────────────────

class PaymentProvider(abc.ABC):
    """支付渠道抽象基类"""

    @abc.abstractmethod
    async def create_order(self, req: OrderRequest) -> OrderResponse:
        """创建订单"""
        ...

    @abc.abstractmethod
    async def verify_callback(self, params: CallbackParams) -> CallbackResult:
        """验证支付回调签名"""
        ...

    @abc.abstractmethod
    async def query_order(self, order_no: str) -> OrderQueryResult:
        """查询订单状态"""
        ...

    @abc.abstractmethod
    async def close_order(self, order_no: str) -> bool:
        """关闭订单"""
        ...


# ── 企业版定价 ────────────────────────────────────────────────────────
ENTERPRISE_PRODUCT: dict[str, dict] = {
    "starter": {
        "price": 1999,
        "price_yuan": "1999.00",
        "seats": 5,
        "name_cn": "入门版",
        "name_en": "Starter",
        "features": ["SSO登录", "自定义域名", "API高级配额", "专属支持", "SLA保障"],
    },
    "business": {
        "price": 4999,
        "price_yuan": "4999.00",
        "seats": 20,
        "name_cn": "企业版",
        "name_en": "Business",
        "features": ["SSO登录", "自定义域名", "API高级配额", "专属支持", "SLA保障"],
    },
    "enterprise": {
        "price": "定制",
        "price_yuan": "定制",
        "seats": "定制",
        "name_cn": "旗舰版",
        "name_en": "Enterprise",
        "features": ["SSO登录", "自定义域名", "API高级配额", "专属支持", "SLA保障"],
    },
}


# ── 金额格式化辅助 ──────────────────────────────────────────────────────

from app.utils.formatting import format_currency  # noqa: E402


def format_price_cents(
    cents: int,
    currency: str = "CNY",
    locale: str = "zh-CN",
) -> str:
    """将分单位的金额格式化为带货币符号的字符串。

    Args:
        cents:    金额（单位：分）。
        currency: 货币代码。
        locale:   locale 字符串。

    Returns:
        格式化后的货币字符串，如 ``"¥29.90"``。
    """
    return format_currency(cents / 100, currency=currency, locale=locale)

