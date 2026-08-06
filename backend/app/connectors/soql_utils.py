"""SOQL 安全工具 — Salesforce 查询参数化与严格转义。

供 salesforce_connector.py / crm_salesforce.py 统一使用，防止 SOQL 注入：

1. soql_escape: 对 SOQL 字符串字面量与 LIKE 通配符（' % _ \\）全量转义
2. validate_email: Email 格式白名单校验（非法值抛 ValueError）
3. validate_limit: LIMIT 参数 int 白名单（1~200，非法值抛 ValueError）

用法:
    from app.connectors.soql_utils import soql_escape, validate_email, validate_limit

    safe = soql_escape(user_input)                 # → 字面量/LIKE 安全
    email = validate_email(raw_email)              # → 抛 ValueError 或返回规范值
    limit = validate_limit(raw_limit)              # → 抛 ValueError 或返回白名单内整数
"""

from __future__ import annotations

import re

# SOQL 转义表：字符串字面量中的单引号 + LIKE 模式中的通配符
# 注意顺序：反斜杠必须最先处理，否则会被二次转义
_SOQL_ESCAPE_MAP = {
    "\\": "\\\\",
    "'": "\\'",
    "%": "\\%",
    "_": "\\_",
}

# Email 格式白名单（RFC 5322 简化版，仅允许常见合法字符）
_EMAIL_RE = re.compile(r"^[A-Za-z0-9.!#$%&'*+/=?^_`{|}~-]+@[A-Za-z0-9](?:[A-Za-z0-9-]{0,61}[A-Za-z0-9])?(?:\.[A-Za-z0-9](?:[A-Za-z0-9-]{0,61}[A-Za-z0-9])?)+$")

# LIMIT 白名单范围（Salesforce 单次查询上限 2000，业务侧再收紧到 200）
LIMIT_MIN = 1
LIMIT_MAX = 200


def soql_escape(value: object) -> str:
    """SOQL 安全转义：对 ' % _ \\ 全量转义。

    - 用于 WHERE 字面量时，转义后的字符串可直接放入单引号内
    - 用于 LIKE 模式时，通配符被转义为字面字符（不参与模糊匹配注入）

    Args:
        value: 任意输入（None 视为空串）。

    Returns:
        转义后的安全字符串。
    """
    if value is None:
        return ""
    return "".join(_SOQL_ESCAPE_MAP.get(ch, ch) for ch in str(value))


def validate_email(email: object) -> str:
    """Email 格式白名单校验。

    Args:
        email: 待校验的 Email 值。

    Returns:
        去除首尾空白后的 Email 字符串。

    Raises:
        ValueError: 格式非法或超长（>254 字符）。
    """
    raw = str(email or "").strip()
    if not raw:
        raise ValueError("Email 不能为空")
    if len(raw) > 254:
        raise ValueError("Email 长度超过 254 字符")
    if not _EMAIL_RE.match(raw):
        raise ValueError(f"Email 格式非法: {raw!r}")
    return raw


def validate_limit(limit: object) -> int:
    """LIMIT 参数 int 白名单校验。

    Args:
        limit: 待校验的 limit 值。

    Returns:
        白名单内的整数 limit。

    Raises:
        ValueError: 非整数、布尔值或超出 1~200 范围。
    """
    if isinstance(limit, bool) or not isinstance(limit, int):
        raise ValueError(f"limit 必须是整数，收到: {type(limit).__name__}")
    if not LIMIT_MIN <= limit <= LIMIT_MAX:
        raise ValueError(f"limit 必须在 {LIMIT_MIN}~{LIMIT_MAX} 之间，收到: {limit}")
    return limit
