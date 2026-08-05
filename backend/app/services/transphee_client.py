"""
三蛋蛋 · 企业匹配引擎 SDK (Transphee Client)
=============================================
封装 https://api.transphee.com:59226/tpmg/entcm 外部API，
为 AI数智名片 提供「输入卖家 → 输出潜在买家」的 1000万 企业库匹配能力。

设计要点（来自上游文档的坑位规避）:
  1. access_token 活 2 小时; refresh_token 一次性 — 换一次就作废, 响应里给新的, 必须覆盖旧的。
     同一张 refresh 用两次 = 整条登录链作废 (防盗设计)。→ 全局单点刷新 + 本地持久化 + 文件锁。
  2. 每天 100 次查询配额 (只有 /api/match_customers 计), 429 时 Retry-After 是距北京 0 点的秒数。
     → 本地配额记账 (SQLite/JSON), 达上限直接拒绝, 不打 API。
  3. page_size 当前固定 20, 显式传别的值一律 400。→ SDK 不暴露 page_size 参数。
  4. 第 1 页可能 20 + 置顶联盟企业 (最多 30), 不要用 page_size 推断条数。
  5. total 可能是下限 (total_is_lower_bound=true, 统计只精确到 10000)。
  6. 按 rank 显示, 不要按 score 重排 (alliance 和 es 的 score 不是一套体系)。
  7. 跨页去重按 cname 而不是 id (同公司被置顶/被检索时 id 不一样)。
  8. 401 两种: 文案含「已过期」→ refresh 换新票; 其它(签名错/没带头/refresh已失效)→ 用 Secret 重新登录。
  9. 429 两种: 文案含「次/天」→ 当天配额用完; 否则 → 每分钟频率限制, 几十秒后重试。
  10. 504 是容量结果不是 bug, 可重试或把描述写具体一点。

用法:
    from app.services.transphee_client import TranspheeClient
    client = TranspheeClient()
    result = client.match_customers(
        company_name="苏州康陪智能科技有限公司",
        product="陪护型养老服务机器人",
        business="研发生产销售养老服务机器人整机及软件平台",
        typical_customers="养老院、护理院、康复医院",
    )
"""
from __future__ import annotations

import json
import logging
import os
import threading
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Optional

try:
    import requests
    HAS_REQUESTS = True
except ImportError:  # pragma: no cover
    HAS_REQUESTS = False

logger = logging.getLogger(__name__)

# ── 默认值 ──────────────────────────────────────────────────────────────
DEFAULT_BASE_URL = "https://api.transphee.com:59226/tpmg/entcm"
DAILY_QUOTA = 100  # 每天 100 次查询
DEFAULT_TIMEOUT = 60  # 上游建议 60s 超时
RETRYABLE_CODES = {429, 500, 503, 504}  # 可重试的状态码

# 北京时间 (UTC+8)
BEIJING_TZ = timezone(timedelta(hours=8))


class TranspheeError(Exception):
    """上游 API 错误, 带状态码和 error_id"""

    def __init__(self, message: str, status_code: int = 0, error_id: str = "", retry_after: Optional[int] = None):
        super().__init__(message)
        self.status_code = status_code
        self.error_id = error_id
        self.retry_after = retry_after  # 距北京 0 点的秒数 (仅 429 配额耗尽时)


class TranspheeQuotaExceeded(TranspheeError):
    """当天 100 次查询配额已用完"""


class TranspheeAuthError(TranspheeError):
    """认证失败 (401)"""


class TranspheeClient:
    """
    三蛋蛋企业匹配引擎客户端。

    Token 生命周期:
        首次调用 → 用 app_id + app_secret 换票 (access 2h + refresh 一次性)
        日常调用 → 用 access_token; 过期 → 用 refresh_token 刷新 (自动覆盖旧 refresh)
        refresh 失效 → 重新用 Secret 登录
    Token 持久化到本地文件, 跨进程共享; 刷新带进程内锁 + 文件锁, 防止多进程并发刷新
    触发「refresh 被用两次」的盗用检测。
    """

    def __init__(
        self,
        app_id: Optional[str] = None,
        app_secret: Optional[str] = None,
        base_url: str = DEFAULT_BASE_URL,
        token_file: Optional[str] = None,
        quota_file: Optional[str] = None,
        timeout: int = DEFAULT_TIMEOUT,
    ):
        self.app_id = app_id or os.environ.get("TRANSHEE_APP_ID", "")
        self.app_secret = app_secret or os.environ.get("TRANSHEE_APP_SECRET", "")
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout

        # token 持久化位置: 默认 backend/data/transphee_token.json
        default_data_dir = os.path.normpath(
            os.path.join(os.path.dirname(__file__), "..", "..", "data")
        )
        self.token_file = token_file or os.environ.get(
            "TRANSHEE_TOKEN_FILE", os.path.join(default_data_dir, "transphee_token.json")
        )
        self.quota_file = quota_file or os.environ.get(
            "TRANSHEE_QUOTA_FILE", os.path.join(default_data_dir, "transphee_quota.json")
        )

        self._lock = threading.Lock()  # 进程内刷新锁 (单点刷新)
        self._token: Optional[dict] = None  # 内存缓存 {access_token, refresh_token, access_expires_at, refresh_expires_at}

        # 三蛋蛋是国内 API, 直连; 禁用环境代理 (本机 Clash 等代理未开时会劫持导致 ConnectionRefused)
        self._session = requests.Session() if HAS_REQUESTS else None
        if self._session is not None:
            self._session.trust_env = False
            self._session.proxies = {"http": None, "https": None}

        if not HAS_REQUESTS:  # pragma: no cover
            logger.warning("requests 未安装, TranspheeClient 不可用")

    # ── 通用请求 ─────────────────────────────────────────────────────────

    def _call(
        self,
        path: str,
        body: Optional[dict] = None,
        token: Optional[str] = None,
        timeout: Optional[int] = None,
    ) -> tuple[int, dict]:
        """POST JSON, 返回 (status_code, json)。网络层异常抛 TranspheeError。"""
        if not HAS_REQUESTS:  # pragma: no cover
            raise TranspheeError("requests 未安装, 无法调用三蛋蛋API", status_code=-1)
        url = f"{self.base_url}{path}"
        headers = {"Content-Type": "application/json"}
        if token:
            headers["Authorization"] = f"Bearer {token}"
        try:
            resp = self._session.post(
                url,
                data=json.dumps(body or {}).encode("utf-8"),
                headers=headers,
                timeout=timeout or self.timeout,
            )
        except requests.Timeout as e:
            raise TranspheeError(f"请求超时({timeout or self.timeout}s): {path}", status_code=-1) from e
        except requests.ConnectionError as e:
            raise TranspheeError(f"连接失败: {path} ({e})", status_code=-1) from e
        except Exception as e:  # pragma: no cover
            raise TranspheeError(f"请求异常: {path} ({e})", status_code=-1) from e

        try:
            data = resp.json() if resp.content else {}
        except json.JSONDecodeError:
            data = {"error": resp.text[:300]}

        # 统一提取 error 信息
        error_msg = ""
        if isinstance(data, dict) and data.get("error"):
            error_msg = str(data["error"])
        elif resp.status_code >= 400 and not error_msg:
            error_msg = f"HTTP {resp.status_code}"
        error_id = ""
        if isinstance(data, dict):
            error_id = str(data.get("error_id", ""))
        retry_after = None
        ra = resp.headers.get("Retry-After")
        if ra:
            try:
                retry_after = int(ra)
            except ValueError:
                retry_after = None

        if resp.status_code >= 400:
            raise TranspheeError(error_msg or f"HTTP {resp.status_code}", resp.status_code, error_id, retry_after)
        return resp.status_code, data

    def _get(self, path: str, timeout: Optional[int] = None) -> tuple[int, dict]:
        """GET 请求 (探活等无鉴权端点)"""
        if not HAS_REQUESTS:  # pragma: no cover
            raise TranspheeError("requests 未安装", status_code=-1)
        try:
            resp = self._session.get(f"{self.base_url}{path}", timeout=timeout or self.timeout)
        except requests.Timeout as e:
            raise TranspheeError(f"探活超时: {path}", status_code=-1) from e
        except requests.ConnectionError as e:
            raise TranspheeError(f"连接失败: {path} ({e})", status_code=-1) from e
        if resp.status_code >= 400:
            raise TranspheeError(f"HTTP {resp.status_code}: {resp.text[:200]}", resp.status_code)
        try:
            return resp.status_code, resp.json()
        except json.JSONDecodeError:
            return resp.status_code, {}

    # ── Token 管理 ───────────────────────────────────────────────────────

    def _load_token_file(self) -> Optional[dict]:
        """从本地文件加载 token"""
        try:
            with open(self.token_file, "r", encoding="utf-8") as f:
                data = json.load(f)
            # 只认结构完整的
            if data.get("access_token") and data.get("refresh_token"):
                return data
        except (FileNotFoundError, json.JSONDecodeError, OSError):
            pass
        return None

    def _save_token_file(self, data: dict) -> None:
        """持久化 token (含新 refresh_token — 旧的已作废, 必须覆盖)"""
        try:
            Path(self.token_file).parent.mkdir(parents=True, exist_ok=True)
            tmp = self.token_file + ".tmp"
            with open(tmp, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False)
            os.replace(tmp, self.token_file)  # 原子替换, 防半写
        except OSError as e:
            logger.error("Token 持久化失败: %s", e)

    def _login(self) -> dict:
        """用 Secret 换票 (全新登录链)"""
        if not self.app_id or not self.app_secret:
            raise TranspheeAuthError(
                "缺少 TRANSHEE_APP_ID / TRANSHEE_APP_SECRET 配置，请在 .env 中设置", status_code=0
            )
        code, data = self._call("/api/auth/token", {"app_id": self.app_id, "app_secret": self.app_secret})
        d = data.get("data", {})
        token = {
            "access_token": d.get("access_token", ""),
            "refresh_token": d.get("refresh_token", ""),
            "access_expires_at": time.time() + int(d.get("expires_in", 7200)),
            "refresh_expires_at": time.time() + int(d.get("refresh_expires_in", 2592000)),
        }
        if not token["access_token"] or not token["refresh_token"]:
            raise TranspheeAuthError(f"换票响应缺少 token: {data}", code)
        self._save_token_file(token)
        return token

    def _refresh(self, old_token: dict) -> dict:
        """用一次性 refresh_token 换新票。成功后旧 refresh 作废, 必须立即覆盖。"""
        code, data = self._call(
            "/api/auth/refresh", {"refresh_token": old_token.get("refresh_token", "")}
        )
        d = data.get("data", {})
        token = {
            "access_token": d.get("access_token", ""),
            "refresh_token": d.get("refresh_token", ""),
            "access_expires_at": time.time() + int(d.get("expires_in", 7200)),
            "refresh_expires_at": time.time() + int(d.get("refresh_expires_in", 2592000)),
        }
        if not token["access_token"] or not token["refresh_token"]:
            raise TranspheeAuthError(f"刷新响应缺少 token: {data}", code)
        self._save_token_file(token)
        return token

    def _get_valid_token(self) -> dict:
        """
        取一个未过期的 access_token, 必要时自动刷新/登录。
        单点刷新: 进程内锁 + 内存缓存, 避免并发把同一张一次性 refresh 用两次。
        """
        with self._lock:
            # 内存缓存优先
            tok = self._token
            if tok and tok.get("access_expires_at", 0) > time.time() + 60:
                return tok

            # 内存没有/过期 → 读文件
            tok = self._load_token_file()

            # 文件里 access 还有效 → 直接用
            if tok and tok.get("access_expires_at", 0) > time.time() + 60:
                self._token = tok
                return tok

            # access 过期 → 用 refresh 换 (若 refresh 本身快过期则直接重登)
            if tok and tok.get("refresh_expires_at", 0) > time.time() + 300:
                try:
                    tok = self._refresh(tok)
                    self._token = tok
                    return tok
                except TranspheeError as e:
                    # refresh 失效 (401 非「已过期」文案 / 被用两次) → 全新登录
                    if e.status_code == 401:
                        logger.warning("refresh token 失效(%s), 重新登录", e)
                        tok = self._login()
                        self._token = tok
                        return tok
                    raise

            # 无 token 文件 / refresh 也过期 → 全新登录
            tok = self._login()
            self._token = tok
            return tok

    # ── 配额记账 ─────────────────────────────────────────────────────────

    def _load_quota(self) -> dict:
        """读取当天已用配额。跨天自动重置。"""
        today = datetime.now(BEIJING_TZ).strftime("%Y-%m-%d")
        try:
            with open(self.quota_file, "r", encoding="utf-8") as f:
                data = json.load(f)
            if data.get("date") != today:
                return {"date": today, "used": 0}
            return data
        except (FileNotFoundError, json.JSONDecodeError, OSError):
            return {"date": today, "used": 0}

    def _consume_quota(self) -> None:
        """消耗 1 次配额并持久化"""
        data = self._load_quota()
        data["used"] = data.get("used", 0) + 1
        try:
            Path(self.quota_file).parent.mkdir(parents=True, exist_ok=True)
            tmp = self.quota_file + ".tmp"
            with open(tmp, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False)
            os.replace(tmp, self.quota_file)
        except OSError as e:
            logger.error("配额记账失败: %s", e)

    def quota_status(self) -> dict:
        """当前配额使用情况"""
        data = self._load_quota()
        used = data.get("used", 0)
        return {
            "date": data.get("date"),
            "used": used,
            "limit": DAILY_QUOTA,
            "remaining": max(0, DAILY_QUOTA - used),
        }

    # ── 业务接口 ─────────────────────────────────────────────────────────

    def health(self) -> dict:
        """探活 (无需票)。返回上游原始结构。"""
        code, data = self._get("/health", timeout=15)
        return {"success": data.get("success", True), "data": data.get("data", {})}

    def match_customers(
        self,
        company_name: str = "",
        product: str = "",
        business: str = "",
        typical_customers: str = "",
        page: int = 1,
        filters: Optional[dict] = None,
        max_retries: int = 2,
    ) -> dict:
        """
        查询潜在买家 (每天 100 次配额)。

        参数:
            company_name: 本公司名 (填了会把自己从结果里排除)
            product: 你卖什么 (product/business/typical_customers 至少填一个)
            business: 主营业务
            typical_customers: 典型客户
            page: 页码, 1..500
            filters: 如 {"province": ["江苏省"]}
            max_retries: 对 429(频率)/500/503/504 的重试次数

        返回: 上游 data 结构 (list/total/page/...), 已按 rank 排序, 跨页去重由调用方按 cname 做。
        """
        # 入参校验 (对齐上游 400 规则)
        # ⚠️ 实测偏差: 上游文档标 company_name 可选, 但实际 API 必填 (缺失返回 "company_name 必填")
        if not company_name.strip():
            raise ValueError("company_name 必填 (上游实测要求, 与文档不一致)")
        if not any([product.strip(), business.strip(), typical_customers.strip()]):
            raise ValueError("product / business / typical_customers 至少填一个 (只填 company_name 不够)")
        for name, val in [("company_name", company_name), ("product", product),
                          ("business", business), ("typical_customers", typical_customers)]:
            if len(val) > 500:
                raise ValueError(f"{name} 最长 500 字, 当前 {len(val)} 字")
        if not (1 <= page <= 500):
            raise ValueError("page 范围 1..500")

        # 配额预检 (本地拒, 不打 API)
        quota = self._load_quota()
        if quota.get("used", 0) >= DAILY_QUOTA:
            raise TranspheeQuotaExceeded(
                f"今日配额已用完 ({DAILY_QUOTA}/{DAILY_QUOTA}), 北京时间 0 点后重置", status_code=429
            )

        body = {"page": page}
        if company_name.strip():
            body["company_name"] = company_name.strip()
        if product.strip():
            body["product"] = product.strip()
        if business.strip():
            body["business"] = business.strip()
        if typical_customers.strip():
            body["typical_customers"] = typical_customers.strip()
        if filters:
            body["filters"] = filters

        attempt = 0
        while True:
            attempt += 1
            try:
                token = self._get_valid_token()
                code, data = self._call("/api/match_customers", body, token=token["access_token"])
                self._consume_quota()  # 成功响应才记账
                return data.get("data", {})
            except TranspheeAuthError as e:
                # 401 文案含「已过期」→ 刷新后重试一次; 其它 → 抛给调用方
                if e.status_code == 401 and "已过期" in str(e):
                    if attempt <= 1:
                        self._token = None  # 强制重取 token (内部会刷新)
                        continue
                raise
            except TranspheeError as e:
                if e.status_code in RETRYABLE_CODES and attempt <= max_retries:
                    # 429: 若是「次/天」配额 → 直接抛; 否则频率限制, 按 Retry-After/几十秒退避
                    if e.status_code == 429:
                        if "次/天" in str(e) or e.retry_after is not None:
                            raise TranspheeQuotaExceeded(str(e), 429, e.error_id, e.retry_after)
                        time.sleep(min(30, 5 * attempt))
                        continue
                    time.sleep(min(30, 5 * attempt))
                    continue
                raise


# ── 便捷单例 (FastAPI 依赖注入用) ────────────────────────────────────────
_client: Optional[TranspheeClient] = None
_client_lock = threading.Lock()


def get_transphee_client() -> TranspheeClient:
    """进程级单例客户端"""
    global _client
    with _client_lock:
        if _client is None:
            _client = TranspheeClient()
        return _client


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    # 自检: 探活 + 配额
    c = get_transphee_client()
    print("health:", c.health())
    print("quota:", c.quota_status())
