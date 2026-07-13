"""
API 错误码国际化映射框架
=========================

将 app.api_standards.ErrorCode 枚举值与 i18n 翻译键关联，
使所有 API 错误响应可以自动根据请求语言返回本地化消息。

用法:
    from app.i18n.error_codes import get_error_message, register_error_code

    # 在路由中生成国际化错误
    raise_http_error(400, ErrorCode.VALIDATION_ERROR,
                     get_error_message("validation_required_field"))

    # 直接获取本地化消息
    msg = get_error_message("brochure_not_found", lang="en")
    # -> "Brochure not found"

支持语言: zh / en / ja / ko / es / fr / de / pt / ru / ar / th / vi
"""

from typing import Optional

from app.i18n import t as _translate

# ═══════════════════════════════════════════════════════════════════
# 错误码 ↔ i18n 键名映射表
# 将 ErrorCode 枚举值映射到对应的 i18n 翻译键前缀
# ═══════════════════════════════════════════════════════════════════

# 标准错误码映射: ErrorCode 枚举值 -> i18n 翻译键
ERROR_CODE_I18N_MAP: dict[str, str] = {
    # 通用错误
    "VALIDATION_ERROR": "bad_request",
    "UNAUTHORIZED": "auth_missing_header",
    "FORBIDDEN": "auth_token_invalid",
    "NOT_FOUND": "not_found",
    "RESOURCE_CONFLICT": "resource_conflict",
    "RATE_LIMITED": "rate_limit_exceeded",
    "INTERNAL_ERROR": "internal_error",
    "SERVICE_UNAVAILABLE": "service_unavailable",
    "DEPRECATED": "deprecated",
    "PAYMENT_REQUIRED": "payment_unsupported_channel",
    "QUOTA_EXCEEDED": "match_quota_exhausted",
}

# 领域错误码映射: 业务领域 -> 对应的 i18n 翻译键前缀
DOMAIN_ERROR_MAP: dict[str, str] = {
    "brochure": "brochure",
    "auth": "auth",
    "user": "user",
    "tag": "tag",
    "match": "match",
    "recommend": "recommend",
    "payment": "payment",
    "trust": "trust",
    "team": "team",
    "visitor": "visitor",
    "webhook": "webhook",
    "integration": "integration",
    "share": "share",
    "sso": "sso",
    "approval": "approval",
    "ab_test": "ab_test",
    "api_key": "api_key",
    "gdpr": "gdpr",
    "media": "media",
    "batch": "batch",
    "notification": "notification",
}


def get_error_message(
    key: str,
    lang: Optional[str] = None,
    default_message: str = "",
) -> str:
    """获取错误码对应的国际化消息。

    从请求上下文自动获取语言，也支持手动指定。

    Args:
        key: i18n 翻译键名（如 'brochure_not_found', 'auth_login_failed'）
        lang: 语言代码，不传则从当前请求上下文获取
        default_message: 找不到翻译时的默认消息

    Returns:
        本地化后的错误消息字符串

    Example:
        >>> get_error_message("brochure_not_found", "en")
        'Brochure not found'

        >>> get_error_message("auth_login_failed", "zh")
        '手机号或密码错误'
    """
    if lang is None:
        try:
            from app.middleware.i18n_middleware import locale_var
            lang = locale_var.get() or "zh"
        except (ImportError, AttributeError, LookupError):
            lang = "zh"

    msg = _translate(key, lang)
    if msg != key or not default_message:
        return msg
    return default_message


def get_error_message_with_details(
    key: str,
    lang: Optional[str] = None,
    default_message: str = "",
    **fmt_kwargs,
) -> str:
    """获取带格式化参数的国际化错误消息。

    支持模板变量替换，如 '{field}' 会被传入的命名参数替换。

    Args:
        key: i18n 翻译键名
        lang: 语言代码
        default_message: 默认消息
        **fmt_kwargs: 格式化参数

    Returns:
        格式化后的本地化消息

    Example:
        >>> get_error_message_with_details("batch_import_result", "zh",
        ...                                 success=10, fail=2)
        '成功导入 10 个用户，失败 2 个'
    """
    msg = get_error_message(key, lang, default_message)
    if fmt_kwargs:
        try:
            msg = msg.format(**fmt_kwargs)
        except KeyError:
            pass  # 忽略模板变量缺失，保持原样
    return msg


def resolve_error_code_message(
    error_code: str,
    lang: Optional[str] = None,
) -> str:
    """将 ErrorCode 枚举值解析为本地化消息。

    根据 ERROR_CODE_I18N_MAP 查找对应的 i18n 翻译键。

    Args:
        error_code: ErrorCode 枚举值（如 'VALIDATION_ERROR'）
        lang: 语言代码

    Returns:
        本地化错误消息，找不到时返回 error_code 本身

    Example:
        >>> resolve_error_code_message("VALIDATION_ERROR", "zh")
        '请求参数错误'
    """
    key = ERROR_CODE_I18N_MAP.get(error_code)
    if key:
        msg = get_error_message(key, lang)
        if msg != key:
            return msg

    # 兜底：直接查找 error_code 小写形式的翻译键
    key = error_code.lower()
    msg = get_error_message(key, lang)
    if msg != key:
        return msg

    return error_code


def get_domain_error_message(
    domain: str,
    action: str,
    lang: Optional[str] = None,
    **fmt_kwargs,
) -> str:
    """构建领域错误消息。

    格式: {domain}_{action}
    例如: brochure_not_found, auth_login_failed, payment_success

    Args:
        domain: 业务领域（如 'brochure', 'auth', 'payment'）
        action: 操作/状态（如 'not_found', 'login_failed', 'success'）
        lang: 语言代码
        **fmt_kwargs: 格式化参数

    Returns:
        本地化领域错误消息
    """
    key = f"{domain}_{action}"
    return get_error_message_with_details(key, lang, "", **fmt_kwargs)


# ═══════════════════════════════════════════════════════════════════
# 便捷函数：常用 HTTP 状态码对应的错误消息
# ═══════════════════════════════════════════════════════════════════

HTTP_STATUS_MESSAGES: dict[int, str] = {
    400: "bad_request",
    401: "auth_missing_header",
    403: "auth_token_invalid",
    404: "not_found",
    429: "too_many_requests",
    500: "internal_error",
    502: "service_unavailable",
    503: "service_unavailable",
}


def get_http_status_message(
    status_code: int,
    lang: Optional[str] = None,
) -> str:
    """根据 HTTP 状态码返回本地化消息。

    Args:
        status_code: HTTP 状态码
        lang: 语言代码

    Returns:
        本地化状态消息
    """
    key = HTTP_STATUS_MESSAGES.get(status_code)
    if key:
        return get_error_message(key, lang)
    return get_error_message("internal_error", lang)
