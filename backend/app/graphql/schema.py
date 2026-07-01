"""GraphQL Schema for AI数字名片.

Defines Strawberry types (BrochureType, UserType, TeamType) and the Query root
with fields: brochures, users, teams, health.
"""

from datetime import datetime
from typing import Optional

import strawberry

from app.graphql.resolvers import (
    resolve_brochures,
    resolve_health,
    resolve_teams,
    resolve_users,
)


# ── Strawberry Types ──────────────────────────────────────────────────


@strawberry.type
class BrochureType:
    id: int
    user_id: int
    title: str
    cover: str
    purpose: str
    pages_count: int
    status: str
    share_token: str
    view_count: int
    created_at: datetime
    updated_at: datetime


@strawberry.type
class UserType:
    id: int
    username: Optional[str]
    phone: str
    name: str
    company: str
    title: str
    intro: str
    avatar: str
    role: str
    created_at: datetime
    updated_at: datetime


@strawberry.type
class TeamType:
    id: int
    name: str
    slug: str
    description: str
    logo: str
    website: str
    industry: str
    size: str
    owner_id: int
    max_members: int
    is_active: bool
    created_at: datetime
    updated_at: datetime


# ── Query ─────────────────────────────────────────────────────────────


@strawberry.type
class Query:
    @strawberry.field
    async def health(self) -> str:
        """Health check — returns 'OK'."""
        return await resolve_health()

    @strawberry.field
    async def brochures(
        self,
        offset: int = 0,
        limit: int = 10,
        status: Optional[str] = None,
    ) -> list[BrochureType]:
        """List brochures (paginated, optionally filtered by status)."""
        rows = await resolve_brochures(offset=offset, limit=limit, status=status)
        return [
            BrochureType(
                id=b.id,
                user_id=b.user_id,
                title=b.title,
                cover=b.cover or "",
                purpose=b.purpose or "",
                pages_count=b.pages_count,
                status=b.status or "draft",
                share_token=b.share_token or "",
                view_count=b.view_count or 0,
                created_at=b.created_at,
                updated_at=b.updated_at,
            )
            for b in rows
        ]

    @strawberry.field
    async def users(
        self,
        offset: int = 0,
        limit: int = 10,
    ) -> list[UserType]:
        """List users (paginated)."""
        rows = await resolve_users(offset=offset, limit=limit)
        return [
            UserType(
                id=u.id,
                username=u.username,
                phone=u.phone,
                name=u.name,
                company=u.company or "",
                title=u.title or "",
                intro=u.intro or "",
                avatar=u.avatar or "",
                role=u.role or "user",
                created_at=u.created_at,
                updated_at=u.updated_at,
            )
            for u in rows
        ]

    @strawberry.field
    async def teams(
        self,
        offset: int = 0,
        limit: int = 10,
    ) -> list[TeamType]:
        """List teams (paginated)."""
        rows = await resolve_teams(offset=offset, limit=limit)
        return [
            TeamType(
                id=t.id,
                name=t.name,
                slug=t.slug,
                description=t.description or "",
                logo=t.logo or "",
                website=t.website or "",
                industry=t.industry or "",
                size=t.size or "1-10",
                owner_id=t.owner_id,
                max_members=t.max_members or 50,
                is_active=t.is_active if hasattr(t, "is_active") else True,
                created_at=t.created_at,
                updated_at=t.updated_at,
            )
            for t in rows
        ]


# ── Schema ────────────────────────────────────────────────────────────

schema = strawberry.Schema(query=Query)
