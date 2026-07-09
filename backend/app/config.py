import os

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    APP_NAME: str = "AI数智名片"
    DATABASE_URL: str = "sqlite+aiosqlite:///./data/digital_brochure.db"
    JWT_SECRET: str  # 必须从环境变量 JWT_SECRET 读取，无默认值 — 生产环境使用 256 位随机密钥
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60  # 60 minutes (security: reduced from 7 days)

    # ── RS256 JWT 非对称签名 ──────────────────────────────────────────────────
    JWT_ALGORITHM: str = "RS256"
    """优先使用的 JWT 签名算法（RS256 非对称），验证时 fallback 到 HS256"""
    RSA_PRIVATE_KEY_PATH: str = "./data/jwt_rsa_private.pem"
    """RSA 私钥路径（自动生成如果不存在）"""
    RSA_PUBLIC_KEY_PATH: str = "./data/jwt_rsa_public.pem"
    """RSA 公钥路径（自动生成如果不存在）"""

    # AI 能力
    DEEPSEEK_API_KEY: str = ""
    DEEPSEEK_API_URL: str = "https://api.deepseek.com/v1/chat/completions"

    # 文件上传
    UPLOAD_DIR: str = "./uploads"

    # 视频上传
    VIDEO_MAX_SIZE: int = 100 * 1024 * 1024  # 100MB
    """视频文件最大大小（字节），默认 100MB"""
    VIDEO_ALLOWED_EXTENSIONS: set[str] = {"mp4", "webm"}
    """允许的视频文件扩展名"""
    VIDEO_ALLOWED_MIME_TYPES: set[str] = {"video/mp4", "video/webm"}
    """允许的视频 MIME 类型"""
    VIDEO_UPLOAD_DIR: str = "./uploads/videos"
    """视频上传存储目录"""

    # Sentry
    SENTRY_DSN: str = ""

    # 外部集成
    CHAINKE_API_URL: str = "http://localhost:8000"
    """链客宝用户系统对接基地址。设为空字符串则使用本地 SQLite 用户系统。"""
    CORS_ORIGINS: str = "https://liankebao.top,https://api.liankebao.top,http://localhost:5173,http://localhost:8200"
    """CORS 允许的来源（逗号分隔）。生产环境: https://liankebao.top,https://api.liankebao.top ; 开发环境添加 localhost"""

    # ── 链客宝会员桥接 ────────────────────────────────────────────────────
    CHAINKE_AUTH_TOKEN: str = ""
    """调用链客宝API的认证令牌"""
    MEMBERSHIP_FREE_QUOTA: int = 0
    """free 会员每月解锁配额（默认为0，不允许解锁）"""
    MEMBERSHIP_GOLD_QUOTA: int = 20
    """gold 会员每月解锁配额"""
    MEMBERSHIP_DIAMOND_QUOTA: int = 60
    """diamond 会员每月解锁配额"""
    MEMBERSHIP_BOARD_QUOTA: int = 200
    """board 会员每月解锁配额"""

    # ── 微信小程序 ─────────────────────────────────────────────────────────
    WECHAT_MINI_APPID: str = ""
    """微信小程序 AppID"""
    WECHAT_MINI_SECRET: str = ""
    """微信小程序 AppSecret"""

    # ── 微信支付 ───────────────────────────────────────────────────────────
    WECHAT_MCH_ID: str = ""
    """微信商户号"""
    WECHAT_PAY_API_KEY: str = ""
    """微信支付 API V2 密钥"""
    WECHAT_PAY_V3_KEY: str = ""
    """微信支付 API V3 密钥"""

    # ── 支付宝 ─────────────────────────────────────────────────────────────
    ALIPAY_APP_ID: str = ""
    """支付宝应用ID"""
    ALIPAY_PRIVATE_KEY: str = ""
    """支付宝应用私钥"""
    ALIPAY_PUBLIC_KEY: str = ""
    """支付宝公钥"""

    # ── 向量搜索 ──────────────────────────────────────────────────────────
    USE_VECTOR_SEARCH: bool = True
    """是否启用向量搜索（设为 False 回退到旧版 TF-IDF）"""

    EMBEDDING_PROVIDER: str = "m3e"
    """Embedding 后端: m3e | numpy | openai | deepseek"""

    EMBEDDING_DIM: int = 768
    """向量维度（m3e=768, openai 3-small=1536, deepseek=1024）"""

    EMBEDDING_API_KEY: str = ""
    """OpenAI / DeepSeek API Key（本地 m3e 不需要）"""

    EMBEDDING_MODEL: str = ""
    """模型名，默认根据 provider 自动选择（m3e: moka-ai/m3e-base）"""

    VECTOR_TOP_K: int = 50
    """向量搜索返回数量上限"""

    # ── HyDE 检索增强 ────────────────────────────────────────────────────
    USE_HYDE: bool = True
    """是否启用 HyDE（Hypothetical Document Embeddings）检索增强。生成假设文档替代原查询进行向量搜索。"""

    # ── Redis 缓存 ────────────────────────────────────────────────────────
    REDIS_HOST: str = "localhost"
    """Redis 服务地址（docker 中为 redis）"""

    REDIS_PORT: int = 6379
    """Redis 服务端口"""

    # ── 分享 ──────────────────────────────────────────────────────────────
    BASE_URL: str = "http://localhost:8000"
    """对外公开的基础 URL（前端地址），用于生成分享链接和 QR 码"""

    REDIS_DB: int = 0
    """Redis 数据库编号"""

    REDIS_PASSWORD: str = ""
    """Redis 密码（无密码留空）"""

    REDIS_MAX_CONNECTIONS: int = 20
    """Redis 连接池大小"""

    REDIS_CACHE_TTL: int = 300
    """默认缓存过期时间（秒）"""

    # ── 异步任务队列 ─────────────────────────────────────────────────
    TASK_QUEUE_MAX_WORKERS: int = 4
    """任务队列并发工作协程数。名片AI扫描/匹配/通知/导出共享此池。"""

    TASK_QUEUE_MAX_SIZE: int = 0
    """任务队列最大长度（0 = 无限）。生产环境建议设 1000 防止内存溢出。"""

    @property
    def REDIS_URL(self) -> str:
        """Build Redis URL from component parts."""
        prefix = "rediss" if getattr(self, "REDIS_SSL", False) else "redis"
        auth = f":{self.REDIS_PASSWORD}@" if self.REDIS_PASSWORD else ""
        return f"{prefix}://{auth}{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_DB}"

    # ── SSO / OAuth2 ──────────────────────────────────────────────────────────
    SSO_GOOGLE_CLIENT_ID: str = ""
    """Google OAuth2 Client ID"""
    SSO_GOOGLE_CLIENT_SECRET: str = ""
    """Google OAuth2 Client Secret"""

    SSO_GITHUB_CLIENT_ID: str = ""
    """GitHub OAuth2 Client ID"""
    SSO_GITHUB_CLIENT_SECRET: str = ""
    """GitHub OAuth2 Client Secret"""

    # ── 邮件服务 (SMTP) ────────────────────────────────────────────────────────
    SMTP_HOST: str = ""
    """SMTP 服务器地址。为空则邮件服务降级为日志输出"""
    SMTP_PORT: int | str = 587
    """SMTP 服务器端口 (587=TLS, 465=SSL)。环境变量中空字符串视为默认值587"""
    SMTP_USER: str = ""
    """SMTP 登录用户名"""
    SMTP_PASSWORD: str = ""
    """SMTP 登录密码"""
    SMTP_USE_TLS: bool = True
    """是否使用 TLS (True=端口587, False=端口465 SSL)"""
    SMTP_FROM: str = "noreply@aibizcard.com"
    """发件人邮箱地址"""
    SMTP_FROM_NAME: str = "AI数智名片"
    """发件人显示名称"""

    # ── IM 机器人 (Slack / 飞书 / 钉钉) ────────────────────────────────────────
    SLACK_BOT_TOKEN: str = ""
    """Slack Bot User OAuth Token (xoxb-...)。为空则降级到日志输出"""
    SLACK_SIGNING_SECRET: str = ""
    """Slack Signing Secret，用于验证请求签名。为空则跳过验证"""

    FEISHU_APP_ID: str = ""
    """飞书应用 App ID。为空则降级到日志输出"""
    FEISHU_APP_SECRET: str = ""
    """飞书应用 App Secret"""
    FEISHU_BOT_NAME: str = "AI数字名片助手"
    """飞书机器人名称"""

    FEISHU_BAIZE_API_URL: str = "https://open.feishu.cn/open-apis/ai/v1/chat/completions"
    """飞书白泽 API 地址"""
    FEISHU_BAIZE_DEFAULT_MODEL: str = "baize-4k"
    """飞书白泽默认模型"""

    DINGTALK_WEBHOOK_URL: str = ""
    """钉钉自定义机器人 Webhook URL。为空则降级到日志输出"""
    DINGTALK_SECRET: str = ""
    """钉钉机器人加签密钥（v2.0 签名模式）。为空则不签名"""

    # ── 企业 OIDC ──────────────────────────────────────────────────────────────
    SSO_OIDC_AUTHORIZE_URL: str = ""
    """企业 OIDC 授权地址"""
    SSO_OIDC_TOKEN_URL: str = ""
    """企业 OIDC 令牌地址"""
    SSO_OIDC_USERINFO_URL: str = ""
    """企业 OIDC 用户信息地址"""
    SSO_OIDC_CLIENT_ID: str = ""
    """企业 OIDC Client ID"""
    SSO_OIDC_CLIENT_SECRET: str = ""
    """企业 OIDC Client Secret"""
    SSO_OIDC_SCOPES: str = "openid,email,profile"
    """企业 OIDC 请求的 scopes（逗号分隔）"""

    # ── 日历集成 (Zoom) ───────────────────────────────────────────────────────
    ZOOM_ACCOUNT_ID: str = ""
    """Zoom Server-to-Server OAuth Account ID。为空则 Zoom 日历降级为日志输出"""
    ZOOM_CLIENT_ID: str = ""
    """Zoom Server-to-Server OAuth Client ID"""
    ZOOM_CLIENT_SECRET: str = ""
    """Zoom Server-to-Server OAuth Client Secret"""
    ZOOM_API_KEY: str = ""
    """Zoom JWT API Key（传统方式，向后兼容）"""
    ZOOM_API_SECRET: str = ""
    """Zoom JWT API Secret（传统方式，向后兼容）"""

    # ── 日历集成 (腾讯会议) ──────────────────────────────────────────────────
    TENCENT_MEETING_APP_ID: str = ""
    """腾讯会议开放平台 App ID。为空则腾讯会议日历降级为日志输出"""
    TENCENT_MEETING_SDK_ID: str = ""
    """腾讯会议 SDK ID（可选，默认同 App ID）"""
    TENCENT_MEETING_SECRET: str = ""
    """腾讯会议 API Secret"""
    TENCENT_WECHAT_APP_ID: str = ""
    """（向后兼容）腾讯会议旧版配置"""
    TENCENT_WECHAT_SECRET: str = ""
    """（向后兼容）腾讯会议旧版配置"""

    # ── API 文档暴露控制 ──────────────────────────────────────────────
    @property
    def docs_enabled(self) -> bool:
        """API 文档端点 /docs /redoc /openapi.json 是否启用。
        生产环境 (ENV=production) 自动禁用。
        也可通过 DISABLE_DOCS=true 环境变量强制禁用。
        """
        env = os.getenv("ENV", "development").lower()
        docs_disabled = os.getenv("DISABLE_DOCS", "").lower() in ("1", "true", "yes")
        return env not in ("production", "prod") and not docs_disabled

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()


# Sentry DSN (从环境变量读取)
SENTRY_DSN: str = os.getenv("SENTRY_DSN", "")
