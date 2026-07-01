"""
链客宝数据打通桥接层
=====================
Phase 3 实现: 信任网络 → 企盟匹配桥接

【对接目标】
将 AI数字名片的信任网络数据与链客宝企盟匹配系统打通，
实现跨平台的供需匹配推荐。

【配置方式】
在 digital_brochure_api.py 中设置:
  CHAINKE_API_BASE = "http://localhost:8001"
  或通过环境变量 CHAINKE_API_BASE 配置

【桥接接口】
  sync_trust_to_chainke(user_id, trust_data)
    → 推送信任数据到链客宝
  sync_matches_from_chainke(user_id)
    → 从链客宝拉取推荐匹配

【失败策略】
  链客宝后端不可达时自动 fallback 到本地匹配引擎

【依赖】
  仅使用 Python 标准库 urllib（零额外依赖）
"""

import json
import logging
import os
from datetime import datetime
from typing import Optional
from urllib import request as urllib_request
from urllib.error import URLError, HTTPError

logger = logging.getLogger("chainke_bridge")

# ── 配置（运行时从环境或 config 读取）──────────────────
CHAINKE_API_BASE: Optional[str] = None
"""链客宝 API 基地址。设为 None 表示使用本地匹配引擎。"""


def _get_api_base() -> Optional[str]:
    """获取链客宝 API 基地址（按优先级: 全局变量 > 环境变量）。"""
    if CHAINKE_API_BASE:
        return CHAINKE_API_BASE
    env_base = os.environ.get("CHAINKE_API_BASE")
    if env_base:
        return env_base
    return None


def _get_auth_header() -> dict:
    """构造链客宝 API 调用的认证头"""
    from app.config import settings
    if settings.CHAINKE_AUTH_TOKEN:
        return {"Authorization": f"Bearer {settings.CHAINKE_AUTH_TOKEN}"}
    return {}


def _http_request(method: str, url: str, data: Optional[dict] = None,
                  timeout: int = 10) -> Optional[dict]:
    """通用 HTTP 请求封装，使用 urllib。

    Args:
        method: HTTP 方法 (GET/POST/PUT/DELETE)
        url: 完整请求 URL
        data: 请求体 dict（会序列化为 JSON）
        timeout: 超时秒数

    Returns:
        解析后的 JSON 响应 dict，或 None（请求失败）
    """
    try:
        body_bytes = None
        if data is not None:
            body_bytes = json.dumps(data, ensure_ascii=False).encode("utf-8")

        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
            "User-Agent": "AI-digital-brochure/2.2",
        }
        # 合并认证头
        headers.update(_get_auth_header())

        req = urllib_request.Request(
            url,
            data=body_bytes,
            method=method,
            headers=headers,
        )

        with urllib_request.urlopen(req, timeout=timeout) as resp:
            resp_body = resp.read().decode("utf-8")
            if resp_body:
                return json.loads(resp_body)
            return {"status": "ok", "code": 200}

    except HTTPError as e:
        logger.warning("链客宝 HTTP 错误 [%s]: %s %s", e.code, url, e.reason)
        try:
            err_body = e.read().decode("utf-8")
            logger.debug("链客宝错误响应体: %s", err_body)
        except Exception:
            pass
        return None
    except URLError as e:
        logger.warning("链客宝不可达 [%s]: %s", url, e.reason)
        return None
    except json.JSONDecodeError as e:
        logger.warning("链客宝响应解析失败: %s", e)
        return None
    except Exception as e:
        logger.warning("链客宝请求异常 [%s]: %s", url, e)
        return None


# ════════════════════════════════════════════════════════════
# 会员身份桥接（Phase 1）
# ════════════════════════════════════════════════════════════

# 链客宝等级 → AI数字名片等级映射
_CHAINKE_TIER_MAP = {
    "free": "free",
    "gold": "gold",
    "diamond": "diamond",
    "board": "board",
}

# AI数字名片等级 → 每月解锁配额映射
_QUOTA_BY_TIER = {
    "free": 0,
    "gold": 20,
    "diamond": 60,
    "board": 200,
}


def sync_membership(user_id: int) -> dict:
    """从链客宝同步用户会员等级到本地数据库。

    调用链客宝 /api/membership/status 接口获取用户最新会员信息，
    同步到 AI数字名片本地 User 记录中。

    Args:
        user_id: AI数字名片本地用户 ID

    Returns:
        同步结果 dict:
            {
                "success": True,
                "synced": True,
                "tier": "gold",
                "expires_at": "...",
                "message": "会员信息同步成功",
            }
            或回退:
            {
                "success": True,
                "synced": False,
                "reason": "链客宝不可达，使用本地会员信息",
            }
    """
    from app.config import settings
    from app.database import SessionLocal
    from app.models.user import User

    api_base = settings.CHAINKE_API_URL
    if not api_base:
        logger.info("[会员同步] CHAINKE_API_URL 未配置，跳过同步")
        return {"success": True, "synced": False, "reason": "链客宝未配置"}

    # 1. 从本地数据库获取用户
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            logger.warning("[会员同步] 用户不存在: user_id=%d", user_id)
            return {"success": False, "synced": False, "error": "用户不存在"}

        # 2. 调用链客宝会员状态接口
        # 使用用户手机号或 openid 作为查询条件
        url = f"{api_base.rstrip('/')}/api/membership/status"
        payload = {
            "user_id": str(user_id),
            "phone": user.phone,
            "source": "ai_digital_brochure",
        }

        logger.info("[会员同步] 请求链客宝会员状态: user_id=%d, url=%s", user_id, url)
        resp = _http_request("GET" if not payload else "POST", url, data=payload)

        if resp is None:
            logger.warning("[会员同步] 链客宝不可达，保留本地会员信息")
            return {
                "success": True,
                "synced": False,
                "reason": "链客宝不可达",
                "tier": user.membership_tier,
            }

        # 3. 解析链客宝响应
        chainke_data = resp.get("data", resp)
        chainke_tier = chainke_data.get("tier", "free")
        expires_at_str = chainke_data.get("expires_at")
        match_credits = chainke_data.get("match_credits", 0)

        # 映射等级
        new_tier = _CHAINKE_TIER_MAP.get(chainke_tier, "free")

        # 解析过期时间
        expires_at = None
        if expires_at_str:
            try:
                expires_at = datetime.fromisoformat(expires_at_str.replace("Z", "+00:00"))
                expires_at = expires_at.replace(tzinfo=None)  # 转为 naive datetime
            except (ValueError, TypeError):
                logger.warning("[会员同步] 解析 expires_at 失败: %s", expires_at_str)

        # 4. 同步到本地数据库
        old_tier = user.membership_tier
        user.membership_tier = new_tier
        user.membership_expires_at = expires_at
        user.membership_synced_at = datetime.utcnow()

        # 同步配额：如果等级变化或是首次同步，重置配额
        if new_tier != old_tier or user.unlock_quota == 0:
            user.unlock_quota = _QUOTA_BY_TIER.get(new_tier, 0)
            user.quota_reset_at = datetime.utcnow()

        db.commit()

        logger.info(
            "[会员同步] 成功: user_id=%d, tier=%s→%s, expires=%s, quota=%d",
            user_id, old_tier, new_tier, expires_at, user.unlock_quota,
        )

        return {
            "success": True,
            "synced": True,
            "tier": new_tier,
            "expires_at": expires_at_str,
            "quota": user.unlock_quota,
            "message": "会员信息同步成功",
        }

    except Exception as e:
        logger.error("[会员同步] 异常: user_id=%d, error=%s", user_id, e)
        db.rollback()
        return {"success": False, "synced": False, "error": str(e)}
    finally:
        db.close()


# ════════════════════════════════════════════════════════════
# 信任网络 → 链客宝数据推送
# ════════════════════════════════════════════════════════════

def sync_trust_to_chainke(user_id: str, trust_data: dict) -> dict:
    """将 AI数字名片的信任网络数据推送到链客宝。

    Args:
        user_id: 当前用户 ID
        trust_data: 信任网络数据 dict，格式:
            {
                "trust_value": {
                    "core_competence": [...],    # 核心能力
                    "industry_experience": [...], # 行业经验
                    "cooperation_advantage": [...] # 合作优势
                },
                "resource_needs": {
                    "resources_required": [...],   # 资源需求
                    "ideal_partner_profile": [...] # 理想合作伙伴画像
                },
                "trust_evidence": {
                    "cooperation_cases": [...],   # 合作案例
                    "client_evaluations": [...]   # 客户评价
                },
                "trusted_user_ids": [...]          # 信任关系用户ID列表
            }

    Returns:
        同步结果 dict:
            {"success": True, "pushed": True, "chainke_response": {...}}
            或 {"success": False, "pushed": False, "error": "..."}
    """
    api_base = _get_api_base()
    if not api_base:
        logger.info("[桥接跳过] CHAINKE_API_BASE 未配置，使用本地匹配")
        return {"success": True, "pushed": False, "reason": "链客宝未配置，已跳过推送"}

    url = f"{api_base.rstrip('/')}/api/external/brochure/trust-sync"
    payload = {
        "user_id": user_id,
        "trust_data": trust_data,
        "source": "ai_digital_brochure",
        "version": "2.2.0",
    }

    logger.info("[链客宝] 推送信任数据: user=%s, trust_count=%d",
                user_id, len(trust_data.get("trusted_user_ids", [])))

    resp = _http_request("POST", url, data=payload)
    if resp is None:
        logger.warning("[链客宝] 推送信任数据失败，已 fallback 到本地匹配")
        return {"success": False, "pushed": False, "error": "链客宝不可达"}

    logger.info("[链客宝] 信任数据推送成功: user=%s", user_id)
    return {
        "success": True,
        "pushed": True,
        "chainke_response": resp,
    }


# ════════════════════════════════════════════════════════════
# 从链客宝拉取推荐匹配
# ════════════════════════════════════════════════════════════

def sync_matches_from_chainke(user_id: str) -> dict:
    """从链客宝拉取针对该用户的推荐匹配列表。

    Args:
        user_id: 当前用户 ID

    Returns:
        匹配结果 dict:
            {
                "success": True,
                "pulled": True,
                "matches": [...],       # 从链客宝获取的匹配列表
                "fallback": False,
            }
            失败时 fallback 到本地匹配返回:
            {
                "success": True,
                "pulled": False,
                "matches": [...],       # 本地匹配结果
                "fallback": True,
            }
    """
    api_base = _get_api_base()
    if not api_base:
        logger.info("[桥接跳过] CHAINKE_API_BASE 未配置，使用本地匹配")
        return _local_fallback_matches(user_id)

    url = f"{api_base.rstrip('/')}/api/external/brochure/matches?user_id={user_id}&source=ai_digital_brochure"

    logger.info("[链客宝] 拉取推荐匹配: user=%s", user_id)

    resp = _http_request("GET", url)
    if resp is None:
        logger.warning("[链客宝] 拉取匹配失败，fallback 到本地匹配引擎")
        return _local_fallback_matches(user_id)

    matches = resp.get("data", resp.get("matches", []))
    logger.info("[链客宝] 拉取匹配成功: user=%s, match_count=%d",
                user_id, len(matches))

    return {
        "success": True,
        "pulled": True,
        "matches": matches,
        "fallback": False,
        "source": "chainke",
    }


# ════════════════════════════════════════════════════════════
# 本地匹配引擎 Fallback
# ════════════════════════════════════════════════════════════

def _local_fallback_matches(user_id: str) -> dict:
    """链客宝不可达时的本地匹配引擎 fallback。

    使用 digital_brochure_api.py 中的匹配引擎逻辑。
    通过导入本地匹配模块实现降级。
    """
    try:
        # 尝试导入本地匹配引擎
        import sys as _sys
        import os as _os

        # 尝试从 digital_brochure_api.py 导入匹配函数
        _api_path = _os.path.join(
            _os.path.dirname(_os.path.dirname(_os.path.dirname(_os.path.abspath(__file__)))),
            "digital_brochure_api.py"
        )
        if _os.path.exists(_api_path):
            # 目录添加到 path
            _api_dir = _os.path.dirname(_api_path)
            if _api_dir not in _sys.path:
                _sys.path.insert(0, _api_dir)

            # 动态导入
            import importlib.util
            _spec = importlib.util.spec_from_file_location(
                "digital_brochure_api", _api_path
            )
            if _spec and _spec.loader:
                _mod = importlib.util.module_from_spec(_spec)
                _spec.loader.exec_module(_mod)
                if hasattr(_mod, "run_matching") and hasattr(_mod, "BROCHURES"):
                    results = _mod.run_matching(user_id, _mod.BROCHURES)
                    logger.info("[本地Fallback] 匹配完成: user=%s, count=%d",
                                user_id, len(results))
                    return {
                        "success": True,
                        "pulled": False,
                        "matches": results,
                        "fallback": True,
                        "source": "local",
                    }
    except Exception as e:
        logger.warning("[本地Fallback] 匹配引擎调用失败: %s", e)

    # 最后的 fallback：返回空列表
    return {
        "success": True,
        "pulled": False,
        "matches": [],
        "fallback": True,
        "source": "local",
    }


# ════════════════════════════════════════════════════════════
# 原有 Phase 2 用户认证桥接接口（保持不变）
# ════════════════════════════════════════════════════════════

async def chainke_register(name: str, phone: str, password: str) -> Optional[dict]:
    """将用户注册请求转发至链客宝。"""
    if not CHAINKE_API_BASE:
        logger.warning("chainke_register 被调用但 CHAINKE_API_BASE 未配置")
        return None

    logger.info("[桥接预留] chainke_register(%s, %s)", name, phone)
    return None


async def chainke_login(phone: str, password: str) -> Optional[dict]:
    """将用户登录请求转发至链客宝。"""
    if not CHAINKE_API_BASE:
        logger.warning("chainke_login 被调用但 CHAINKE_API_BASE 未配置")
        return None

    logger.info("[桥接预留] chainke_login(%s)", phone)
    return None


async def chainke_verify_token(token: str) -> Optional[dict]:
    """向链客宝验证 token 有效性。"""
    if not CHAINKE_API_BASE:
        logger.warning("chainke_verify_token 被调用但 CHAINKE_API_BASE 未配置")
        return None

    logger.info("[桥接预留] chainke_verify_token(token)  token前缀=%s...",
                token[:12] if token else "None")
    return None


async def chainke_get_user(user_id: str) -> Optional[dict]:
    """从链客宝获取用户信息。"""
    if not CHAINKE_API_BASE:
        logger.warning("chainke_get_user 被调用但 CHAINKE_API_BASE 未配置")
        return None

    logger.info("[桥接预留] chainke_get_user(%s)", user_id)
    return None
