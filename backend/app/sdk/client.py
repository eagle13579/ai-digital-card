"""
AI数字名片 Python SDK 客户端
=============================

纯 Python + httpx 实现，支持:
- API 密钥认证（Bearer Token）
- 指数退避自动重试
- 环境变量自动配置
- 类型提示（typing）

用法::

    from app.sdk import ApiClient

    # 从环境变量自动配置
    client = ApiClient()

    # 或显式指定
    client = ApiClient(base_url="http://localhost:8201", api_key="your-token")

    # 登录获取 token
    token = client.auth().login(phone="13800138000", password="xxx")
    client.set_token(token.access_token)

    # 获取当前用户
    me = client.users().me()

    # 列出名片
    brochures = client.brochures().list()

    # CRM 联系人
    contacts = client.crm().contacts()
"""

from __future__ import annotations

import logging
import os
import time
from dataclasses import dataclass, field
from typing import Any, TypeVar

import httpx

from app.sdk.models import (
    # 用户
    TokenResponse,
    User,
    UserCreate,
    UserLogin,
    UserUpdate,
    # 名片
    Brochure,
    BrochureCreate,
    BrochureUpdate,
    CrmActivity,
    CrmContact,
    CrmContactCreate,
    CrmContactUpdate,
    CrmDeal,
    CrmDealCreate,
    CrmNote,
    CrmNoteCreate,
    CrmNoteUpdate,
    CrmPipelineStage,
    # 通用
    PaginatedResponse,
)

logger = logging.getLogger("ai_digital_card.sdk")

T = TypeVar("T")


# ══════════════════════════════════════════════════════════════════════════════
# 异常类
# ══════════════════════════════════════════════════════════════════════════════


class ApiError(Exception):
    """API 业务错误。"""

    def __init__(self, status: int, code: int, message: str, data: Any = None) -> None:
        self.status = status
        self.code = code
        self.data = data
        super().__init__(f"[{status}] {message} (code={code})")


class NetworkError(Exception):
    """网络错误。"""

    def __init__(self, message: str = "网络连接失败", cause: Exception | None = None) -> None:
        self.cause = cause
        super().__init__(message)


class TimeoutError(Exception):
    """请求超时。"""

    def __init__(self, timeout: float) -> None:
        super().__init__(f"请求超时 ({timeout:.0f}s)")


# ══════════════════════════════════════════════════════════════════════════════
# 客户端配置
# ══════════════════════════════════════════════════════════════════════════════


@dataclass
class ClientConfig:
    """SDK 客户端配置。"""

    base_url: str = field(default_factory=lambda: os.getenv("AICARD_BASE_URL", "http://localhost:8201"))
    api_key: str = field(default_factory=lambda: os.getenv("AICARD_API_KEY", ""))
    timeout: float = 15.0
    max_retries: int = 2
    retry_base_delay: float = 1.0
    retry_max_delay: float = 30.0


# ══════════════════════════════════════════════════════════════════════════════
# 默认配置实例
# ══════════════════════════════════════════════════════════════════════════════

_default_config = ClientConfig()


def _should_retry(status: int) -> bool:
    """判断 HTTP 状态码是否可重试。"""
    return status >= 500 or status == 429


# ══════════════════════════════════════════════════════════════════════════════
# 核心客户端
# ══════════════════════════════════════════════════════════════════════════════


class ApiClient:
    """AI数字名片 API 客户端。

    参数:
        base_url: API 基础地址（默认从 AICARD_BASE_URL 环境变量读取）
        api_key:  API 密钥/Token（默认从 AICARD_API_KEY 环境变量读取）
        config:   完整配置对象（覆盖单个参数）
    """

    def __init__(
        self,
        base_url: str | None = None,
        api_key: str | None = None,
        config: ClientConfig | None = None,
    ) -> None:
        if config is not None:
            self._config = config
        else:
            self._config = ClientConfig()
            if base_url is not None:
                self._config.base_url = base_url
            if api_key is not None:
                self._config.api_key = api_key

        self._token: str = self._config.api_key
        self._http = httpx.Client(timeout=self._config.timeout)

    # ── Token 管理 ────────────────────────────────────────────────────────

    def set_token(self, token: str) -> None:
        """设置 Bearer Token。"""
        self._token = token

    def get_token(self) -> str:
        """获取当前 Token。"""
        return self._token

    def clear_token(self) -> None:
        """清除 Token。"""
        self._token = ""

    # ── HTTP 请求核心 ─────────────────────────────────────────────────────

    def _build_headers(self, skip_auth: bool = False) -> dict[str, str]:
        headers: dict[str, str] = {"Content-Type": "application/json"}
        if not skip_auth and self._token:
            headers["Authorization"] = f"Bearer {self._token}"
        return headers

    def _request(
        self,
        method: str,
        path: str,
        params: dict[str, Any] | None = None,
        json_body: Any = None,
        skip_auth: bool = False,
    ) -> httpx.Response:
        """执行 HTTP 请求（含指数退避重试）。"""
        url = f"{self._config.base_url.rstrip('/')}{path}"
        headers = self._build_headers(skip_auth=skip_auth)

        retries = self._config.max_retries
        base_delay = self._config.retry_base_delay
        max_delay = self._config.retry_max_delay
        last_error: Exception | None = None

        for attempt in range(retries + 1):
            try:
                response = self._http.request(
                    method=method,
                    url=url,
                    headers=headers,
                    params=params,
                    json=json_body,
                    timeout=self._config.timeout,
                )

                if not response.is_success:
                    # 是否可重试
                    if attempt < retries and _should_retry(response.status_code):
                        delay = min(base_delay * (2**attempt), max_delay)
                        logger.warning(
                            "请求 %s %s 失败 (HTTP %d)，第 %d/%d 次重试，等待 %.1fs",
                            method, path, response.status_code,
                            attempt + 1, retries, delay,
                        )
                        time.sleep(delay)
                        continue

                    # 构建业务错误
                    try:
                        err_data = response.json()
                        code = err_data.get("code", response.status_code)
                        message = err_data.get("message", response.reason_phrase or "未知错误")
                    except Exception:
                        code = response.status_code
                        message = f"HTTP {response.status_code}: {response.reason_phrase or '未知错误'}"

                    raise ApiError(
                        status=response.status_code,
                        code=code,
                        message=message,
                        data=err_data if "err_data" in dir() else None,
                    )

                return response

            except httpx.TimeoutException as e:
                if attempt < retries:
                    delay = min(base_delay * (2**attempt), max_delay)
                    logger.warning("请求超时，第 %d/%d 次重试，等待 %.1fs", attempt + 1, retries, delay)
                    time.sleep(delay)
                    continue
                raise TimeoutError(self._config.timeout) from e

            except httpx.TransportError as e:
                if attempt < retries:
                    delay = min(base_delay * (2**attempt), max_delay)
                    logger.warning("网络错误: %s，第 %d/%d 次重试", e, attempt + 1, retries)
                    time.sleep(delay)
                    continue
                raise NetworkError(str(e), cause=e) from e

            except ApiError:
                raise

            except Exception as e:
                if attempt < retries:
                    time.sleep(base_delay)
                    continue
                raise NetworkError(str(e), cause=e) from e

        # 不应到达这里
        raise last_error if last_error else NetworkError("未知错误")

    def _get(
        self,
        path: str,
        params: dict[str, Any] | None = None,
        response_model: type[T] | None = None,
        skip_auth: bool = False,
    ) -> T | Any:
        """GET 请求并解析 JSON 响应。"""
        resp = self._request("GET", path, params=params, skip_auth=skip_auth)
        data = resp.json()
        if response_model is not None:
            return response_model.model_validate(data)
        return data

    def _post(
        self,
        path: str,
        json_body: Any = None,
        response_model: type[T] | None = None,
        skip_auth: bool = False,
    ) -> T | Any:
        """POST 请求并解析 JSON 响应。"""
        resp = self._request("POST", path, json_body=json_body, skip_auth=skip_auth)
        data = resp.json()
        if response_model is not None:
            return response_model.model_validate(data)
        return data

    def _put(
        self,
        path: str,
        json_body: Any = None,
        response_model: type[T] | None = None,
    ) -> T | Any:
        """PUT 请求并解析 JSON 响应。"""
        resp = self._request("PUT", path, json_body=json_body)
        data = resp.json()
        if response_model is not None:
            return response_model.model_validate(data)
        return data

    def _patch(
        self,
        path: str,
        json_body: Any = None,
        response_model: type[T] | None = None,
    ) -> T | Any:
        """PATCH 请求并解析 JSON 响应。"""
        resp = self._request("PATCH", path, json_body=json_body)
        data = resp.json()
        if response_model is not None:
            return response_model.model_validate(data)
        return data

    def _delete(
        self,
        path: str,
        params: dict[str, Any] | None = None,
    ) -> None:
        """DELETE 请求。"""
        self._request("DELETE", path, params=params)

    # ── 领域 API 访问器 ──────────────────────────────────────────────────

    def auth(self) -> AuthAPI:
        """认证相关 API。"""
        return AuthAPI(self)

    def users(self) -> UsersAPI:
        """用户相关 API。"""
        return UsersAPI(self)

    def brochures(self) -> BrochuresAPI:
        """名片相关 API。"""
        return BrochuresAPI(self)

    def contacts(self) -> ContactsAPI:
        """联系人 API（CRM 联系人）。"""
        return ContactsAPI(self)

    def crm(self) -> CrmAPI:
        """CRM 完整 API（联系人 + 机会 + 活动 + 笔记 + 管道）。"""
        return CrmAPI(self)

    def tags(self) -> TagsAPI:
        """标签 API。"""
        return TagsAPI(self)

    def matches(self) -> MatchesAPI:
        """匹配 API。"""
        return MatchesAPI(self)

    def visitors(self) -> VisitorsAPI:
        """访客 API。"""
        return VisitorsAPI(self)

    def subscriptions(self) -> SubscriptionsAPI:
        """订阅/会员 API。"""
        return SubscriptionsAPI(self)

    def messages(self) -> MessagesAPI:
        """消息 API。"""
        return MessagesAPI(self)

    # ── 上下文管理器 ──────────────────────────────────────────────────────

    def __enter__(self) -> ApiClient:
        return self

    def __exit__(self, *args: Any) -> None:
        self._http.close()

    def close(self) -> None:
        """关闭底层 HTTP 连接。"""
        self._http.close()


# ══════════════════════════════════════════════════════════════════════════════
# 领域 API 类
# ══════════════════════════════════════════════════════════════════════════════


class AuthAPI:
    """认证相关端点。"""

    def __init__(self, client: ApiClient) -> None:
        self._client = client

    def register(
        self,
        phone: str,
        password: str,
        name: str,
        username: str | None = None,
        company: str = "",
        title: str = "",
        intro: str = "",
        avatar: str = "",
    ) -> TokenResponse:
        """手机号注册。"""
        body = UserCreate(
            phone=phone, password=password, name=name,
            username=username, company=company, title=title,
            intro=intro, avatar=avatar,
        )
        return self._client._post(
            "/api/auth/register",
            json_body=body.model_dump(mode="json", exclude_none=True),
            response_model=TokenResponse,
            skip_auth=True,
        )

    def login(self, phone: str, password: str) -> TokenResponse:
        """手机号密码登录。"""
        body = UserLogin(phone=phone, password=password)
        return self._client._post(
            "/api/auth/login",
            json_body=body.model_dump(mode="json"),
            response_model=TokenResponse,
            skip_auth=True,
        )

    def wx_login(self, code: str) -> TokenResponse:
        """微信登录（Mock 实现）。"""
        return self._client._post(
            "/api/auth/wx-login",
            json_body={"code": code},
            response_model=TokenResponse,
            skip_auth=True,
        )


class UsersAPI:
    """用户相关端点。"""

    def __init__(self, client: ApiClient) -> None:
        self._client = client

    def me(self) -> User:
        """获取当前用户信息。"""
        return self._client._get("/api/user/me", response_model=User)

    def update(self, updates: UserUpdate) -> User:
        """更新个人信息。"""
        return self._client._patch(
            "/api/user/me",
            json_body=updates.model_dump(mode="json", exclude_none=True),
            response_model=User,
        )

    def get(self, user_id: int) -> User:
        """获取指定用户信息。"""
        return self._client._get(f"/api/user/{user_id}", response_model=User)


class BrochuresAPI:
    """名片相关端点。"""

    def __init__(self, client: ApiClient) -> None:
        self._client = client

    def list(
        self,
        page: int = 1,
        page_size: int = 20,
        sort_by: str | None = None,
        sort_order: str | None = None,
    ) -> PaginatedResponse[Brochure]:
        """获取名片列表。"""
        params: dict[str, Any] = {"page": page, "page_size": page_size}
        if sort_by:
            params["sort_by"] = sort_by
        if sort_order:
            params["sort_order"] = sort_order
        data = self._client._get("/api/brochures", params=params)
        return PaginatedResponse[Brochure].model_validate(data)

    def get(self, brochure_id: int) -> Brochure:
        """获取名片详情。"""
        return self._client._get(f"/api/brochures/{brochure_id}", response_model=Brochure)

    def create(self, data: BrochureCreate) -> Brochure:
        """创建名片。"""
        return self._client._post(
            "/api/brochures",
            json_body=data.model_dump(mode="json", exclude_none=True),
            response_model=Brochure,
        )

    def update(self, brochure_id: int, data: BrochureUpdate) -> Brochure:
        """更新名片。"""
        return self._client._put(
            f"/api/brochures/{brochure_id}",
            json_body=data.model_dump(mode="json", exclude_none=True),
            response_model=Brochure,
        )

    def delete(self, brochure_id: int) -> None:
        """删除名片。"""
        self._client._delete(f"/api/brochures/{brochure_id}")

    def publish(self, brochure_id: int) -> Brochure:
        """发布名片。"""
        return self._client._post(
            f"/api/brochures/{brochure_id}/publish",
            response_model=Brochure,
        )

    def unpublish(self, brochure_id: int) -> Brochure:
        """下架名片。"""
        return self._client._post(
            f"/api/brochures/{brochure_id}/unpublish",
            response_model=Brochure,
        )


class ContactsAPI:
    """联系人 API（CRM 联系人）。"""

    def __init__(self, client: ApiClient) -> None:
        self._client = client

    def list(
        self,
        page: int = 1,
        page_size: int = 20,
        search: str | None = None,
        source: str | None = None,
    ) -> PaginatedResponse[CrmContact]:
        """联系人列表。"""
        params: dict[str, Any] = {"page": page, "page_size": page_size}
        if search:
            params["search"] = search
        if source:
            params["source"] = source
        data = self._client._get("/api/crm/contacts", params=params)
        return PaginatedResponse[CrmContact].model_validate(data)

    def get(self, contact_id: int) -> CrmContact:
        """联系人详情。"""
        return self._client._get(f"/api/crm/contacts/{contact_id}", response_model=CrmContact)

    def create(self, data: CrmContactCreate) -> CrmContact:
        """创建联系人。"""
        return self._client._post(
            "/api/crm/contacts",
            json_body=data.model_dump(mode="json", exclude_none=True),
            response_model=CrmContact,
        )

    def update(self, contact_id: int, data: CrmContactUpdate) -> CrmContact:
        """更新联系人。"""
        return self._client._put(
            f"/api/crm/contacts/{contact_id}",
            json_body=data.model_dump(mode="json", exclude_none=True),
            response_model=CrmContact,
        )

    def delete(self, contact_id: int) -> None:
        """删除联系人。"""
        self._client._delete(f"/api/crm/contacts/{contact_id}")

    def timeline(self, contact_id: int) -> list[CrmActivity]:
        """联系人活动时间线。"""
        data = self._client._get(f"/api/crm/contacts/{contact_id}/timeline")
        if isinstance(data, list):
            return [CrmActivity.model_validate(item) for item in data]
        return []

    def notes(self, contact_id: int) -> list[CrmNote]:
        """联系人笔记列表。"""
        data = self._client._get(f"/api/crm/contacts/{contact_id}/notes")
        if isinstance(data, list):
            return [CrmNote.model_validate(item) for item in data]
        return []


class CrmAPI:
    """CRM 完整 API。"""

    def __init__(self, client: ApiClient) -> None:
        self._client = client
        self._contacts_api = ContactsAPI(client)

    def contacts(self) -> ContactsAPI:
        """CRM 联系人 API。"""
        return self._contacts_api

    # ── 管道阶段 ──────────────────────────────────────────────────────────

    def stages(self) -> list[CrmPipelineStage]:
        """获取管道阶段列表。"""
        data = self._client._get("/api/crm/pipeline/stages")
        if isinstance(data, list):
            return [CrmPipelineStage.model_validate(item) for item in data]
        return []

    def update_stage(self, stage_id: int, name: str | None = None, sort_order: int | None = None) -> CrmPipelineStage:
        """更新管道阶段。"""
        body: dict[str, Any] = {}
        if name is not None:
            body["name"] = name
        if sort_order is not None:
            body["sort_order"] = sort_order
        return self._client._put(
            f"/api/crm/pipeline/stages/{stage_id}",
            json_body=body,
            response_model=CrmPipelineStage,
        )

    # ── 销售机会 ──────────────────────────────────────────────────────────

    def deals(self, stage_id: int | None = None) -> list[CrmDeal]:
        """获取机会列表（按阶段分组）。"""
        params = {"stage_id": stage_id} if stage_id else None
        data = self._client._get("/api/crm/pipeline/deals", params=params)
        if isinstance(data, list):
            return [CrmDeal.model_validate(item) for item in data]
        return []

    def create_deal(self, data: CrmDealCreate) -> CrmDeal:
        """创建销售机会。"""
        return self._client._post(
            "/api/crm/deals",
            json_body=data.model_dump(mode="json", exclude_none=True),
            response_model=CrmDeal,
        )

    def move_deal(self, deal_id: int, pipeline_stage_id: int) -> CrmDeal:
        """拖拽变更机会阶段。"""
        return self._client._put(
            f"/api/crm/deals/{deal_id}/stage",
            json_body={"pipeline_stage_id": pipeline_stage_id},
            response_model=CrmDeal,
        )

    # ── 活动 ──────────────────────────────────────────────────────────────

    def create_activity(
        self,
        contact_id: int,
        activity_type: str,
        title: str = "",
        description: str = "",
        deal_id: int | None = None,
    ) -> CrmActivity:
        """手动添加活动记录。"""
        body: dict[str, Any] = {
            "contact_id": contact_id,
            "activity_type": activity_type,
            "title": title,
            "description": description,
        }
        if deal_id is not None:
            body["deal_id"] = deal_id
        return self._client._post(
            "/api/crm/activities",
            json_body=body,
            response_model=CrmActivity,
        )

    # ── 笔记 ──────────────────────────────────────────────────────────────

    def create_note(self, data: CrmNoteCreate) -> CrmNote:
        """创建笔记。"""
        return self._client._post(
            "/api/crm/notes",
            json_body=data.model_dump(mode="json", exclude_none=True),
            response_model=CrmNote,
        )

    def update_note(self, note_id: int, data: CrmNoteUpdate) -> CrmNote:
        """更新笔记。"""
        return self._client._put(
            f"/api/crm/notes/{note_id}",
            json_body=data.model_dump(mode="json", exclude_none=True),
            response_model=CrmNote,
        )

    def delete_note(self, note_id: int) -> None:
        """删除笔记。"""
        self._client._delete(f"/api/crm/notes/{note_id}")

    # ── 统计 ──────────────────────────────────────────────────────────────

    def stats(self) -> dict[str, Any]:
        """CRM 统计信息。"""
        return self._client._get("/api/crm/stats")

    # ── 自动创建 ──────────────────────────────────────────────────────────

    def auto_create_from_match(self, match_id: int) -> CrmContact:
        """从名片交换记录自动创建联系人。"""
        return self._client._post(
            f"/api/crm/auto/match/{match_id}",
            response_model=CrmContact,
        )


class TagsAPI:
    """标签 API。"""

    def __init__(self, client: ApiClient) -> None:
        self._client = client

    def list(self, tag_type: str | None = None) -> list[dict[str, Any]]:
        """获取标签列表。"""
        params = {"tag_type": tag_type} if tag_type else None
        return self._client._get("/api/tags", params=params)

    def batch_set(self, tags: list[dict[str, Any]], tag_type: str, source: str = "manual") -> list[dict[str, Any]]:
        """批量设置标签。"""
        return self._client._post(
            "/api/tags/batch",
            json_body={"tags": tags, "tag_type": tag_type, "source": source},
        )


class MatchesAPI:
    """匹配 API。"""

    def __init__(self, client: ApiClient) -> None:
        self._client = client

    def list(
        self,
        page: int = 1,
        page_size: int = 20,
        status: str | None = None,
    ) -> PaginatedResponse[Any]:
        """匹配列表。"""
        params: dict[str, Any] = {"page": page, "page_size": page_size}
        if status:
            params["status"] = status
        data = self._client._get("/api/matches", params=params)
        return PaginatedResponse.model_validate(data)

    def update_status(self, match_id: int, status: str) -> dict[str, Any]:
        """更新匹配状态。"""
        return self._client._post(
            f"/api/matches/{match_id}",
            json_body={"status": status},
        )


class VisitorsAPI:
    """访客 API。"""

    def __init__(self, client: ApiClient) -> None:
        self._client = client

    def list(self, brochure_id: int | None = None, page: int = 1, page_size: int = 20) -> PaginatedResponse[Any]:
        """访客列表。"""
        params: dict[str, Any] = {"page": page, "page_size": page_size}
        if brochure_id is not None:
            params["brochure_id"] = brochure_id
        data = self._client._get("/api/visitors", params=params)
        return PaginatedResponse.model_validate(data)


class SubscriptionsAPI:
    """订阅/会员 API。"""

    def __init__(self, client: ApiClient) -> None:
        self._client = client

    def get_plans(self) -> list[dict[str, Any]]:
        """获取套餐列表。"""
        return self._client._get("/api/subscription/plans")

    def get_current(self) -> dict[str, Any]:
        """获取当前订阅状态。"""
        return self._client._get("/api/subscription/current")

    def start_trial(self) -> dict[str, Any]:
        """开始试用。"""
        return self._client._post("/api/subscription/trial")

    def upgrade(self, tier: str) -> dict[str, Any]:
        """升级套餐。"""
        return self._client._post("/api/subscription/upgrade", json_body={"tier": tier})

    def cancel(self, reason: str | None = None) -> dict[str, Any]:
        """取消订阅。"""
        body = {"reason": reason} if reason else {}
        return self._client._post("/api/subscription/cancel", json_body=body)


class MessagesAPI:
    """消息 API。"""

    def __init__(self, client: ApiClient) -> None:
        self._client = client

    def conversations(self) -> list[dict[str, Any]]:
        """获取会话列表。"""
        return self._client._get("/api/messages/conversations")

    def get_messages(self, conversation_id: int, page: int = 1, page_size: int = 50) -> PaginatedResponse[Any]:
        """获取会话消息。"""
        data = self._client._get(
            f"/api/messages/conversations/{conversation_id}",
            params={"page": page, "page_size": page_size},
        )
        return PaginatedResponse.model_validate(data)

    def send(self, receiver_id: int, content: str, brochure_id: int | None = None) -> dict[str, Any]:
        """发送消息。"""
        body: dict[str, Any] = {"receiver_id": receiver_id, "content": content}
        if brochure_id is not None:
            body["brochure_id"] = brochure_id
        return self._client._post("/api/messages/send", json_body=body)

    def unread_count(self) -> dict[str, Any]:
        """未读消息数。"""
        return self._client._get("/api/messages/unread/count")
