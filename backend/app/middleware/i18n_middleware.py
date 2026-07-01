"""
国际化中间件 (I18n Localization Middleware)

基于 contextvars 将 Accept-Language 解析后的语言代码注入到当前请求上下文，
业务代码通过 gettext() 函数查询翻译。

用法:
    # 注册中间件 (FastAPI)
    app.add_middleware(I18nMiddleware)

    # 在业务代码中查询翻译
    from app.middleware.i18n_middleware import gettext, locale_var

    msg = gettext("success")             # 使用当前请求的语言
    msg = gettext("success", "en")        # 指定语言
    locale = locale_var.get()             # 获取当前语言代码
"""

from contextvars import ContextVar
from app.i18n import t as _t, detect_lang as _detect_lang

# ── ContextVar: 线程/协程安全的语言代码存储 ──────────────────────
locale_var: ContextVar[str] = ContextVar("locale", default="zh")


def gettext(key: str, locale: str | None = None) -> str:
    """翻译查询函数，基于 contextvars 的当前语言。

    Args:
        key: 翻译键名，对应 i18n.py 中 TRANSLATIONS 的 key
        locale: 语言代码 (zh / en)，None 时从 context 获取当前请求语言

    Returns:
        翻译后的文本，找不到 key 时返回 key 本身
    """
    if locale is None:
        locale = locale_var.get()
    return _t(key, locale)


# ── ASGI 中间件 ──────────────────────────────────────────────────
class I18nMiddleware:
    """ASGI 中间件：从 Accept-Language 头解析语言，注入到 contextvars。

    支持的语种: zh-CN, en-US, zh-TW (均映射到 i18n.py 的 zh/en)
    回退策略: 无法识别时默认为中文 (zh)

    使用方式 (FastAPI):
        from app.middleware.i18n_middleware import I18nMiddleware
        app.add_middleware(I18nMiddleware)

    使用方式 (Starlette / 原生 ASGI):
        from app.middleware.i18n_middleware import I18nMiddleware
        app = I18nMiddleware(app)
    """

    __slots__ = ("app", "supported_locales", "default_locale")

    def __init__(self, app):
        self.app = app
        self.supported_locales = ["zh-CN", "en-US", "zh-TW"]
        self.default_locale = "zh-CN"

    async def __call__(self, scope, receive, send):
        # 仅处理 HTTP 请求
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        # ── 1. 从 Accept-Language 头中提取语言偏好 ────────────
        headers = dict(scope.get("headers", []))
        raw_accept_lang = headers.get(b"accept-language", b"")
        accept_language = raw_accept_lang.decode("utf-8", errors="replace")

        # ── 2. 复用 i18n.py 的 detect_lang 检测语言 ──────────
        #    返回 'zh' 或 'en'
        locale = _detect_lang(accept_language)

        # ── 3. 注入到 context ──────────────────────────────────
        token = locale_var.set(locale)

        try:
            await self.app(scope, receive, send)
        finally:
            # ── 4. 清理 context ──────────────────────────────
            locale_var.reset(token)
