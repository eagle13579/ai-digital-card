import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError
from passlib.context import CryptContext
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth_jwt import create_access_token, decode_access_token
from app.config import settings
from app.database import get_db
from app.models.user import User
from app.schemas import (
    UserCreate,
    UserLogin,
    UserResponse,
    WeChatLogin,
    TokenResponse,
    WeChatMiniLogin,
)
from app.services.chainke_bridge import sync_membership

router = APIRouter(prefix="/api/auth", tags=["认证"])

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")


# ── 密码强度验证 ──────────────────────────────────────────────────────────

def validate_password_strength(password: str) -> str:
    """验证密码强度：最少8位 + 大写字母 + 小写字母 + 数字 + 特殊字符。

    Args:
        password: 原始密码明文。

    Returns:
        验证通过返回原密码字符串。

    Raises:
        HTTPException 400: 密码不满足强度要求。
    """
    errors = []
    if len(password) < 8:
        errors.append("密码长度至少8位")
    if not any(c.isupper() for c in password):
        errors.append("密码需包含大写字母")
    if not any(c.islower() for c in password):
        errors.append("密码需包含小写字母")
    if not any(c.isdigit() for c in password):
        errors.append("密码需包含数字")
    if not any(not c.isalnum() for c in password):
        errors.append("密码需包含特殊字符")
    if errors:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="; ".join(errors),
        )
    return password


# create_access_token 由 app.auth_jwt 提供（RS256 优先 + HS256 降级）


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db),
) -> User:
    """依赖项：从JWT令牌中获取当前用户"""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="无法验证凭证",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = decode_access_token(token)
        user_id_str: str | None = payload.get("sub")
        if user_id_str is None:
            raise credentials_exception
        user_id = int(user_id_str)
    except (JWTError, ValueError):
        raise credentials_exception

    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalars().first()
    if user is None:
        raise credentials_exception
    return user


async def get_optional_user(
    token: str | None = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db),
) -> User | None:
    """依赖项：可选用户认证 — 有 token 则返回用户，无 token 返回 None（不报错）"""
    if token is None:
        return None
    try:
        payload = decode_access_token(token)
        user_id_str: str | None = payload.get("sub")
        if user_id_str is None:
            return None
        user_id = int(user_id_str)
        result = await db.execute(select(User).where(User.id == user_id))
        return result.scalars().first()
    except (JWTError, ValueError, Exception):
        return None


async def authenticate_user(db: AsyncSession, phone: str, password: str) -> User | None:
    result = await db.execute(select(User).where(User.phone == phone))
    user = result.scalars().first()
    if user is None or not pwd_context.verify(password, user.password_hash):
        return None
    return user


@router.post("/register", response_model=TokenResponse)
async def register(data: UserCreate, db: AsyncSession = Depends(get_db)):
    """手机号注册"""
    result = await db.execute(select(User).where(User.phone == data.phone))
    existing = result.scalars().first()
    if existing:
        raise HTTPException(status_code=400, detail="手机号已注册")

    # 密码强度验证
    validate_password_strength(data.password)

    user = User(
        phone=data.phone,
        name=data.name,
        username=data.username,
        company=data.company or "",
        title=data.title or "",
        intro=data.intro or "",
        avatar=data.avatar or "",
        password_hash=pwd_context.hash(data.password),
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)

    # 注册后同步会员信息（异步fallback风格）
    try:
        await sync_membership(user.id)
    except Exception:
        pass

    token = create_access_token({"sub": str(user.id)})
    return TokenResponse(access_token=token, user=UserResponse.model_validate(user))


@router.post("/login", response_model=TokenResponse)
async def login(data: UserLogin, db: AsyncSession = Depends(get_db)):
    """手机号密码登录"""
    user = await authenticate_user(db, data.phone, data.password)
    if user is None:
        raise HTTPException(status_code=401, detail="手机号或密码错误")

    # 登录时同步会员信息
    try:
        await sync_membership(user.id)
    except Exception:
        pass

    token = create_access_token({"sub": str(user.id)})
    return TokenResponse(access_token=token, user=UserResponse.model_validate(user))


@router.post("/wx-login", response_model=TokenResponse)
async def wx_login(data: WeChatLogin, db: AsyncSession = Depends(get_db)):
    """微信登录（Mock实现，无需真实微信AppID）

    接收前端传来的 wx.login() code，生成Mock用户并返回JWT token。
    开发/演示阶段使用，无需配置微信AppID。
    """
    mock_openid = f"mock_wx_{uuid.uuid4().hex[:12]}"
    mock_nickname = f"微信用户_{data.code[-4:]}" if len(data.code) >= 4 else "微信用户"

    result = await db.execute(select(User).where(User.wechat_openid == mock_openid))
    user = result.scalars().first()

    if user is None:
        user = User(
            phone=f"138{mock_openid[-8:]}",
            name=mock_nickname,
            password_hash=pwd_context.hash(mock_openid),
            wechat_openid=mock_openid,
            avatar=f"https://api.dicebear.com/7.x/avataaars/svg?seed={mock_openid[-6:]}",
            company="",
            title="",
            intro="",
        )
        db.add(user)
        await db.commit()
        await db.refresh(user)

    # 登录时同步会员信息
    try:
        await sync_membership(user.id)
    except Exception:
        pass

    token = create_access_token({"sub": str(user.id)})
    return TokenResponse(access_token=token, user=UserResponse.model_validate(user))


# ── 微信小程序登录（真实场景） ────────────────────────────────────────────

import logging
import httpx as _httpx

_logger = logging.getLogger("wx_mini_login")

_WECHAT_CODE2SESSION_URL = "https://api.weixin.qq.com/sns/jscode2session"


@router.post("/wx-mini-login", response_model=TokenResponse)
async def wx_mini_login(data: WeChatMiniLogin, db: AsyncSession = Depends(get_db)):
    """微信小程序登录

    接收小程序 wx.login() 返回的临时 code，调用微信服务器换取 openid，
    查找或创建用户，同步会员信息，返回 JWT token。

    流程：
    1. code → 微信 jscode2session → openid + session_key
    2. 根据 openid 查找或创建用户
    3. 同步链客宝会员等级
    4. 签发 JWT token
    """
    appid = settings.WECHAT_MINI_APPID
    secret = settings.WECHAT_MINI_SECRET

    if not appid or not secret:
        # 降级：使用 mock 方式（开发/演示模式）
        _logger.warning("微信小程序未配置 WECHAT_MINI_APPID/SECRET，使用 mock 模式")
        mock_openid = f"mock_mini_{uuid.uuid4().hex[:12]}"
        result = await db.execute(select(User).where(User.wechat_openid == mock_openid))
        user = result.scalars().first()

        is_new = False
        if user is None:
            user = User(
                phone=f"139{mock_openid[-8:]}",
                name=data.user_info.get("nickName", f"小程序用户_{data.code[-4:]}") if data.user_info else f"小程序用户_{data.code[-4:]}",
                password_hash=pwd_context.hash(mock_openid),
                wechat_openid=mock_openid,
                avatar=data.user_info.get("avatarUrl", "") if data.user_info else "",
                company="",
                title="",
                intro="",
            )
            db.add(user)
            await db.commit()
            await db.refresh(user)
            is_new = True

        # 同步链客宝会员等级
        try:
            await sync_membership(user.id)
        except Exception:
            pass

        token = create_access_token({"sub": str(user.id)})
        return TokenResponse(access_token=token, user=UserResponse.model_validate(user), is_new=is_new)

    # ── 真实微信小程序登录 ──
    try:
        async with _httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(
                _WECHAT_CODE2SESSION_URL,
                params={
                    "appid": appid,
                    "secret": secret,
                    "js_code": data.code,
                    "grant_type": "authorization_code",
                },
            )
            wx_data = resp.json()
    except Exception as e:
        _logger.warning("微信 jscode2session 请求失败 (%s)，降级到 mock 登录模式", e)
        # 降级：使用 mock 方式（服务器无法访问微信API时）
        mock_openid = f"mock_mini_{uuid.uuid4().hex[:12]}"
        result = await db.execute(select(User).where(User.wechat_openid == mock_openid))
        user = result.scalars().first()
        is_new = False
        if user is None:
            user = User(
                phone=f"139{mock_openid[-8:]}",
                name=data.user_info.get("nickName", f"小程序用户_{data.code[-4:]}") if data.user_info else f"小程序用户_0000",
                password_hash=pwd_context.hash(mock_openid),
                wechat_openid=mock_openid,
                avatar=data.user_info.get("avatarUrl", "") if data.user_info else "",
                company="",
                title="",
                intro="",
            )
            db.add(user)
            await db.commit()
            await db.refresh(user)
            is_new = True
        try:
            await sync_membership(user.id)
        except Exception:
            pass
        token = create_access_token({"sub": str(user.id)})
        return TokenResponse(access_token=token, user=UserResponse.model_validate(user), is_new=is_new)

    # 检查微信返回错误
    if "errcode" in wx_data and wx_data["errcode"] != 0:
        errmsg = wx_data.get("errmsg", "未知错误")
        _logger.error("微信登录错误: code=%s, errcode=%d, errmsg=%s",
                       data.code, wx_data["errcode"], errmsg)
        raise HTTPException(
            status_code=400,
            detail=f"微信登录失败: {errmsg}",
        )

    openid = wx_data.get("openid")
    unionid = wx_data.get("unionid")
    session_key = wx_data.get("session_key")

    if not openid:
        raise HTTPException(status_code=400, detail="微信登录失败: 未获取到 openid")

    # 查找或创建用户
    result = await db.execute(select(User).where(User.wechat_openid == openid))
    user = result.scalars().first()

    is_new = False
    if not user:
        # 新用户：用微信信息创建
        nick_name = "小程序用户"
        avatar_url = ""
        if data.user_info:
            nick_name = data.user_info.get("nickName", nick_name)
            avatar_url = data.user_info.get("avatarUrl", avatar_url)

        # 生成虚拟手机号（用 openid 哈希取10位数字）
        import hashlib
        phone_suffix = hashlib.md5(openid.encode(), usedforsecurity=False).hexdigest()[:8]
        virtual_phone = f"139{phone_suffix}"

        user = User(
            phone=virtual_phone,
            name=nick_name,
            password_hash=pwd_context.hash(openid),
            wechat_openid=openid,
            avatar=avatar_url,
            company="",
            title="",
            intro="",
        )
        db.add(user)
        await db.commit()
        await db.refresh(user)
        is_new = True

    # 同步链客宝会员等级
    try:
        await sync_membership(user.id)
    except Exception:
        pass

    token = create_access_token({"sub": str(user.id)})
    return TokenResponse(access_token=token, user=UserResponse.model_validate(user), is_new=is_new)
