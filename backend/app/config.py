import os

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    APP_NAME: str = "AI数字名片"
    DATABASE_URL: str = "sqlite:///./data/digital_brochure.db"
    JWT_SECRET: str = "change-this-to-a-secure-random-secret-key"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7 days

    # AI 能力
    DEEPSEEK_API_KEY: str = ""
    DEEPSEEK_API_URL: str = "https://api.deepseek.com/v1/chat/completions"

    # 文件上传
    UPLOAD_DIR: str = "./uploads"

    # Sentry
    SENTRY_DSN: str = ""

    # 外部集成
    CHAINKE_API_URL: str = "http://localhost:8000"
    """链客宝用户系统对接基地址。设为空字符串则使用本地 SQLite 用户系统。"""
    CORS_ORIGINS: str = "*"
    """CORS 允许的来源（逗号分隔）"""

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

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()


# Sentry DSN (从环境变量读取)
SENTRY_DSN: str = os.getenv("SENTRY_DSN", "")
