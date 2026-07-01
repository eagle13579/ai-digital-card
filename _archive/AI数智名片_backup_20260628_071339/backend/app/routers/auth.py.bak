import uuid
from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy import select
from sqlalchemy.orm import Session

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


def create_access_token(data: dict) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, settings.JWT_SECRET, algorithm=settings.ALGORITHM)


def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> User:
    """依赖项：从JWT令牌中获取当前用户"""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="无法验证凭证",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, settings.JWT_SECRET, algorithms=[settings.ALGORITHM])
        user_id_str: str | None = payload.get("sub")
        if user_id_str is None:
            raise credentials_exception
        user_id = int(user_id_str)
    except (JWTError, ValueError):
        raise credentials_exception

    user = db.query(User).filter(User.id == user_id).first()
    if user is None:
        raise credentials_exception
    return user


def authenticate_user(db: Session, phone: str, password: str) -> User | None:
    user = db.query(User).filter(User.phone == phone).first()
    if user is None or not pwd_context.verify(password, user.password_hash):
        return None
    return user


@router.post("/register", response_model=TokenResponse)
def register(data: UserCreate, db: Session = Depends(get_db)):
    """手机号注册"""
    existing = db.query(User).filter(User.phone == data.phone).first()
    if existing:
        raise HTTPException(status_code=400, detail="手机号已注册")

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
    db.commit()
    db.refresh(user)

    # 注册后同步会员信息（异步fallback风格）
    try:
        sync_membership(user.id)
    except Exception:
        pass

    token = create_access_token({"sub": str(user.id)})
    return TokenResponse(access_token=token, user=UserResponse.model_validate(user))


@router.post("/login", response_model=TokenResponse)
def login(data: UserLogin, db: Session = Depends(get_db)):
    """手机号密码登录"""
    user = authenticate_user(db, data.phone, data.password)
    if user is None:
        raise HTTPException(status_code=401, detail="手机号或密码错误")

    # 登录时同步会员信息
    try:
        sync_membership(user.id)
    except Exception:
        pass

    token = create_access_token({"sub": str(user.id)})
    return TokenResponse(access_token=token, user=UserResponse.model_validate(user))


@router.post("/wx-login", response_model=TokenResponse)
def wx_login(data: WeChatLogin, db: Session = Depends(get_db)):
    """微信登录（Mock实现，无需真实微信AppID）

    接收前端传来的 wx.login() code，生成Mock用户并返回JWT token。
    开发/演示阶段使用，无需配置微信AppID。
    """
    mock_openid = f"mock_wx_{uuid.uuid4().hex[:12]}"
    mock_nickname = f"微信用户_{data.code[-4:]}" if len(data.code) >= 4 else "微信用户"

    user = db.query(User).filter(User.wechat_openid == mock_openid).first()

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
        db.commit()
        db.refresh(user)

    # 登录时同步会员信息
    try:
        sync_membership(user.id)
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
def wx_mini_login(data: WeChatMiniLogin, db: Session = Depends(get_db)):
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
        user = db.query(User).filter(User.wechat_openid == mock_openid).first()
        if not user:
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
            db.commit()
            db.refresh(user)

        # 同步会员
        try:
            sync_membership(user.id)
        except Exception:
            pass

        token = create_access_token({"sub": str(user.id)})
        return TokenResponse(access_token=token, user=UserResponse.model_validate(user))

    # ── 真实微信小程序登录 ──
    try:
        with _httpx.Client(timeout=10.0) as client:
            resp = client.get(
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
        _logger.error("微信 jscode2session 请求失败: %s", e)
        raise HTTPException(
            status_code=502,
            detail=f"微信登录服务调用失败: {str(e)}",
        )

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
    user = db.query(User).filter(User.wechat_openid == openid).first()

    if not user:
        # 新用户：用微信信息创建
        nick_name = "小程序用户"
        avatar_url = ""
        if data.user_info:
            nick_name = data.user_info.get("nickName", nick_name)
            avatar_url = data.user_info.get("avatarUrl", avatar_url)

        # 生成虚拟手机号（用 openid 哈希取10位数字）
        import hashlib
        phone_suffix = hashlib.md5(openid.encode()).hexdigest()[:8]
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
        db.commit()
        db.refresh(user)

    # 同步链客宝会员等级
    try:
        sync_membership(user.id)
    except Exception:
        pass

    token = create_access_token({"sub": str(user.id)})
    return TokenResponse(access_token=token, user=UserResponse.model_validate(user))
