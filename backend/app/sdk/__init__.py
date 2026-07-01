"""
AI数字名片 Python SDK
=====================

纯 Python + httpx 实现的 API 客户端包，提供类型安全的接口调用。

快速开始::

    import os
    from app.sdk import ApiClient

    client = ApiClient(
        base_url=os.getenv("AICARD_BASE_URL", "http://localhost:8201"),
        api_key=os.getenv("AICARD_API_KEY", ""),
    )

    # 用户 API
    user = client.users().me()
    print(user.name)

    # 名片 API
    brochures = client.brochures().list()
    for b in brochures:
        print(b.title)

    # CRM API
    contacts = client.crm().contacts()
    for c in contacts:
        print(c.name)

环境变量:
    - ``AICARD_BASE_URL`` — API 基础地址（默认 http://localhost:8201）
    - ``AICARD_API_KEY``  — API 密钥（Bearer Token）
"""

from app.sdk.client import ApiClient, ApiError, NetworkError, TimeoutError
from app.sdk.models import (
    # 用户
    User,
    UserCreate,
    UserLogin,
    UserUpdate,
    TokenResponse,
    # 名片
    Brochure,
    BrochureCreate,
    BrochureUpdate,
    Page,
    # 联系人/CRM
    CrmContact,
    CrmContactCreate,
    CrmContactUpdate,
    CrmDeal,
    CrmDealCreate,
    CrmPipelineStage,
    CrmActivity,
    CrmNote,
    CrmNoteCreate,
    CrmNoteUpdate,
    # 通用
    PaginatedResponse,
    ApiResponse,
)

__all__ = [
    # 客户端
    "ApiClient",
    "ApiError",
    "NetworkError",
    "TimeoutError",
    # 用户模型
    "User",
    "UserCreate",
    "UserLogin",
    "UserUpdate",
    "TokenResponse",
    # 名片模型
    "Brochure",
    "BrochureCreate",
    "BrochureUpdate",
    "Page",
    # CRM 模型
    "CrmContact",
    "CrmContactCreate",
    "CrmContactUpdate",
    "CrmDeal",
    "CrmDealCreate",
    "CrmPipelineStage",
    "CrmActivity",
    "CrmNote",
    "CrmNoteCreate",
    "CrmNoteUpdate",
    # 通用模型
    "PaginatedResponse",
    "ApiResponse",
]

__version__ = "2.0.0"
