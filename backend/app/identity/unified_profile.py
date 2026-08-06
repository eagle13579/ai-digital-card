"""Unified User Profile Layer — cross-product shared user identity.

Architecture:
    UnifiedUserProfile        → Data class representing a user across products.
    UnifiedProfileInterface   → Abstract base / protocol for profile storage.
    SQLAlchemyAdapter         → Async SQLAlchemy implementation reading from users + crm_contacts.
    UnifiedProfileService     → High-level service: get, merge, search, cross-product lookup.

This layer solves the cross-product user data sharing problem:
  - AI数字名片 (this project) stores users in `users` table
  - chainke-full stores users in a separate database
  - go-aiport stores users in yet another database
  - CRM contacts (crm_contacts) also carry user-like profile data

All profile operations go through UnifiedProfileInterface, keeping
business logic decoupled from where the data actually lives.
"""

from __future__ import annotations

import abc
import dataclasses
from datetime import datetime, timezone
from typing import Any, AsyncIterator, Protocol, runtime_checkable


# ======================================================================
# Data Models
# ======================================================================


@dataclasses.dataclass
class UnifiedUserProfile:
    """A unified user profile that can originate from any product.

    Attributes:
        user_id: Unique user identifier within the source product.
        source_product: Which product this profile originates from
            (e.g. "ai-digital-brochure", "chainke-full", "go-aiport", "crm").
        username: Login username (may be None for OAuth-only users).
        phone: Phone number (primary identifier in many systems).
        name: Display / real name.
        company: Company / organization name.
        title: Job title.
        intro: Brief introduction / bio.
        avatar: URL to avatar image.
        email: Email address (may be None if not collected).
        role: User role (e.g. "user", "admin", "enterprise").
        membership_tier: Subscription tier (e.g. "free", "gold", "diamond").
        is_active: Whether the user account is active.
        created_at: Account creation timestamp.
        updated_at: Last profile update timestamp.
        metadata: Extra product-specific key-value data.
    """

    user_id: str
    source_product: str = ""
    username: str | None = None
    phone: str | None = None
    name: str = ""
    company: str = ""
    title: str = ""
    intro: str = ""
    avatar: str = ""
    email: str | None = None
    role: str = "user"
    membership_tier: str = "free"
    is_active: bool = True
    created_at: datetime | None = None
    updated_at: datetime | None = None
    metadata: dict[str, Any] = dataclasses.field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return dataclasses.asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> UnifiedUserProfile:
        known = {f.name for f in dataclasses.fields(cls)}
        kwargs = {k: v for k, v in data.items() if k in known}
        metadata = {k: v for k, v in data.items() if k not in known}
        if metadata:
            kwargs["metadata"] = metadata
        return cls(**kwargs)


# ======================================================================
# Interface Protocol
# ======================================================================


@runtime_checkable
class UnifiedProfileInterface(Protocol):
    """Contract for profile storage backends.

    Methods:
        get_profile(user_id)                 → Single profile lookup.
        merge_profile(source, target)        → Merge source into target.
        search_profiles(keyword, limit=20)   → Keyword search across profiles.
        get_cross_product_users(product)     → List profiles from a product.
        upsert_profile(profile)              → Insert or update a profile.
        list_all_profiles(skip, limit)       → Paginated full listing.
    """

    async def get_profile(self, user_id: str) -> UnifiedUserProfile | None:
        """Fetch a single profile by its user ID."""
        ...

    async def merge_profile(
        self,
        source: UnifiedUserProfile,
        target: UnifiedUserProfile,
    ) -> UnifiedUserProfile:
        """Merge fields from source profile into target profile.

        Non-empty / non-None fields from source override target fields.
        Returns the merged profile.
        """
        ...

    async def search_profiles(
        self,
        keyword: str,
        limit: int = 20,
    ) -> list[UnifiedUserProfile]:
        """Search profiles by keyword across name, company, title, phone, email."""
        ...

    async def get_cross_product_users(
        self,
        product_name: str,
    ) -> list[UnifiedUserProfile]:
        """List all profiles belonging to a specific source product."""
        ...

    async def upsert_profile(
        self,
        profile: UnifiedUserProfile,
    ) -> UnifiedUserProfile:
        """Insert a new profile or update an existing one.

        Returns the (possibly server-modified) profile.
        """
        ...

    async def list_all_profiles(
        self,
        skip: int = 0,
        limit: int = 100,
    ) -> list[UnifiedUserProfile]:
        """Fetch a paginated list of all profiles."""
        ...


# ======================================================================
# Abstract Base Class — convenience for adapters
# ======================================================================


class UnifiedProfileBase(abc.ABC):
    """Abstract base that mirrors UnifiedProfileInterface.

    Adapters can inherit from this instead of implementing the
    Protocol explicitly.  Provides default merge logic.
    """

    @abc.abstractmethod
    async def get_profile(self, user_id: str) -> UnifiedUserProfile | None:
        ...

    async def merge_profile(
        self,
        source: UnifiedUserProfile,
        target: UnifiedUserProfile,
    ) -> UnifiedUserProfile:
        """Default merge: source fields override target when non-empty."""
        merged = UnifiedUserProfile(
            user_id=target.user_id or source.user_id,
            source_product=target.source_product or source.source_product,
            username=source.username or target.username,
            phone=source.phone or target.phone,
            name=source.name or target.name,
            company=source.company or target.company,
            title=source.title or target.title,
            intro=source.intro or target.intro,
            avatar=source.avatar or target.avatar,
            email=source.email or target.email,
            role=source.role or target.role,
            membership_tier=source.membership_tier or target.membership_tier,
            is_active=source.is_active if not source.is_active else target.is_active,
            created_at=target.created_at or source.created_at,
            updated_at=datetime.now(timezone.utc),
        )
        # Merge metadata dicts (target wins on key collision)
        merged_meta = dict(source.metadata)
        merged_meta.update(target.metadata)
        merged.metadata = merged_meta
        return merged

    @abc.abstractmethod
    async def search_profiles(
        self,
        keyword: str,
        limit: int = 20,
    ) -> list[UnifiedUserProfile]:
        ...

    @abc.abstractmethod
    async def get_cross_product_users(
        self,
        product_name: str,
    ) -> list[UnifiedUserProfile]:
        ...

    @abc.abstractmethod
    async def upsert_profile(
        self,
        profile: UnifiedUserProfile,
    ) -> UnifiedUserProfile:
        ...

    @abc.abstractmethod
    async def list_all_profiles(
        self,
        skip: int = 0,
        limit: int = 100,
    ) -> list[UnifiedUserProfile]:
        ...


# ======================================================================
# SQLAlchemy Adapter — reads from users + crm_contacts tables
# ======================================================================


class SQLAlchemyProfileAdapter(UnifiedProfileBase):
    """Adapter that reads profile data from the local SQLAlchemy database.

    This adapter:
      - Reads the `users` table (the ai-digital-brochure User model).
      - Optionally reads `crm_contacts` table (CRM contacts with profile data).
      - Emits UnifiedUserProfile instances with source_product populated.

    Future extensions:
      - Add a RemoteApiAdapter that calls chainke-full / go-aiport REST endpoints.
      - Add a CompositeAdapter that aggregates multiple adapters.
    """

    def __init__(self, db_factory):
        """Initialize with a callable that returns an async generator yielding AsyncSession.

        Args:
            db_factory: A callable (typically app.database.get_db) that when
                invoked returns an async iterator yielding AsyncSession.
        """
        self._db_factory = db_factory

    async def _get_session(self):
        """Get a single AsyncSession from the factory async generator."""
        async for session in self._db_factory():
            return session

    async def get_profile(self, user_id: str) -> UnifiedUserProfile | None:
        """Fetch a profile by user_id from the local users table."""
        from app.models.user import User
        from sqlalchemy import select

        try:
            uid = int(user_id)
        except (ValueError, TypeError):
            return None

        session = await self._get_session()
        result = await session.execute(select(User).where(User.id == uid))
        user = result.scalar_one_or_none()
        if user is None:
            return None
        return self._user_to_profile(user)

    async def search_profiles(
        self,
        keyword: str,
        limit: int = 20,
    ) -> list[UnifiedUserProfile]:
        """Search across name, company, title, phone from the users table."""
        from app.models.user import User
        from sqlalchemy import or_, select

        pattern = f"%{keyword}%"
        query = (
            select(User)
            .where(
                or_(
                    User.name.ilike(pattern),
                    User.company.ilike(pattern),
                    User.title.ilike(pattern),
                    User.phone.ilike(pattern),
                    User.username.ilike(pattern),
                )
            )
            .limit(limit)
        )
        session = await self._get_session()
        result = await session.execute(query)
        users = result.scalars().all()
        return [self._user_to_profile(u) for u in users]

    async def get_cross_product_users(
        self,
        product_name: str,
    ) -> list[UnifiedUserProfile]:
        """List profiles from the local users table (product = 'ai-digital-brochure').

        For this adapter, only 'ai-digital-brochure' returns local users.
        Other product names return empty — they'd need a RemoteApiAdapter.
        """
        if product_name != "ai-digital-brochure":
            return []
        from app.models.user import User
        from sqlalchemy import select

        session = await self._get_session()
        result = await session.execute(select(User).limit(1000))
        users = result.scalars().all()
        return [self._user_to_profile(u) for u in users]

    async def upsert_profile(
        self,
        profile: UnifiedUserProfile,
    ) -> UnifiedUserProfile:
        """Upsert profile data into the local users table.

        Creates or updates a User row.  For external product profiles
        that have no local User row, a stub row is created.
        """
        from app.models.user import User
        from sqlalchemy import select

        session = await self._get_session()
        try:
            uid = int(profile.user_id)
        except (ValueError, TypeError):
            uid = 0

        result = await session.execute(select(User).where(User.id == uid))
        user = result.scalar_one_or_none()

        if user is None:
            # Create new user stub
            user = User(
                username=profile.username or f"unified_{profile.user_id}",
                phone=profile.phone or "00000000000",
                password_hash="UNIFIED_PROFILE_STUB",
                name=profile.name or "",
                company=profile.company or "",
                title=profile.title or "",
                intro=profile.intro or "",
                avatar=profile.avatar or "",
                role=profile.role or "user",
            )
            session.add(user)
            await session.flush()
            profile.user_id = str(user.id)
        else:
            # Update existing user
            if profile.name:
                user.name = profile.name
            if profile.company:
                user.company = profile.company
            if profile.title:
                user.title = profile.title
            if profile.intro:
                user.intro = profile.intro
            if profile.avatar:
                user.avatar = profile.avatar
            if profile.phone:
                user.phone = profile.phone
            if profile.username:
                user.username = profile.username

        await session.commit()
        await session.refresh(user)
        return self._user_to_profile(user)

    async def list_all_profiles(
        self,
        skip: int = 0,
        limit: int = 100,
    ) -> list[UnifiedUserProfile]:
        from app.models.user import User
        from sqlalchemy import select

        query = select(User).offset(skip).limit(limit).order_by(User.id)
        session = await self._get_session()
        result = await session.execute(query)
        users = result.scalars().all()
        return [self._user_to_profile(u) for u in users]

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _user_to_profile(self, user) -> UnifiedUserProfile:
        """Convert a SQLAlchemy User ORM object to UnifiedUserProfile."""
        return UnifiedUserProfile(
            user_id=str(user.id),
            source_product="ai-digital-brochure",
            username=user.username,
            phone=user.phone,
            name=user.name,
            company=user.company,
            title=user.title,
            intro=user.intro,
            avatar=user.avatar,
            role=user.role,
            membership_tier=getattr(user, "membership_tier", "free"),
            is_active=True,
            created_at=getattr(user, "created_at", None),
            updated_at=getattr(user, "updated_at", None),
        )


# ======================================================================
# UnifiedProfileService — high-level facade
# ======================================================================


class UnifiedProfileService:
    """High-level service for cross-product profile operations.

    Wraps a UnifiedProfileInterface adapter and adds:
      - Business logic on merge (e.g. conflict resolution).
      - Multi-source fallback (future: try local, then remote).
      - Caching (future: Redis layer).
    """

    def __init__(self, adapter: UnifiedProfileInterface):
        self._adapter = adapter

    @property
    def adapter(self) -> UnifiedProfileInterface:
        return self._adapter

    async def get_profile(self, user_id: str) -> UnifiedUserProfile | None:
        """Retrieve a single profile by user ID."""
        return await self._adapter.get_profile(user_id)

    async def merge_profile(
        self,
        source: UnifiedUserProfile,
        target: UnifiedUserProfile,
    ) -> UnifiedUserProfile:
        """Merge source profile into target and persist."""
        return await self._adapter.upsert_profile(
            await self._adapter.merge_profile(source, target),
        )

    async def search_profiles(
        self,
        keyword: str,
        limit: int = 20,
    ) -> list[UnifiedUserProfile]:
        """Search profiles across all products."""
        return await self._adapter.search_profiles(keyword, limit=limit)

    async def get_cross_product_users(
        self,
        product_name: str,
    ) -> list[UnifiedUserProfile]:
        """List all users for a given product."""
        return await self._adapter.get_cross_product_users(product_name)

    async def upsert_profile(
        self,
        profile: UnifiedUserProfile,
    ) -> UnifiedUserProfile:
        """Insert or update a profile."""
        return await self._adapter.upsert_profile(profile)

    async def list_all_profiles(
        self,
        skip: int = 0,
        limit: int = 100,
    ) -> list[UnifiedUserProfile]:
        """Paginated full profile listing."""
        return await self._adapter.list_all_profiles(skip=skip, limit=limit)


# ======================================================================
# Factory — convenience for FastAPI dependency injection
# ======================================================================


def get_unified_profile_service(
    db_factory=None,
) -> UnifiedProfileService:
    """Create a UnifiedProfileService wired to the SQLAlchemy adapter.

    Args:
        db_factory: Optional callable that yields AsyncSession.
            Defaults to app.database.get_db.

    Returns:
        A configured UnifiedProfileService instance.
    """
    from app.database import get_db as _default_db

    adapter = SQLAlchemyProfileAdapter(db_factory or _default_db)
    return UnifiedProfileService(adapter)
