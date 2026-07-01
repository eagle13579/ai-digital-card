"""GraphQL resolvers for AI数字名片.

Provides data-fetching functions for brochures, users, teams, and health.
Uses async SQLAlchemy sessions for DB access.
"""

import logging
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import AsyncSessionLocal
from app.models.brochure import Brochure
from app.models.team import Team
from app.models.user import User

logger = logging.getLogger(__name__)


async def _get_session() -> AsyncSession:
    async with AsyncSessionLocal() as session:
        yield session


async def resolve_health() -> str:
    """Simple health check."""
    return "OK"


async def resolve_brochures(
    offset: int = 0,
    limit: int = 10,
    status: Optional[str] = None,
) -> list[Brochure]:
    """Fetch brochures with optional pagination and status filter."""
    async with AsyncSessionLocal() as db:
        stmt = select(Brochure).order_by(Brochure.created_at.desc())
        if status:
            stmt = stmt.where(Brochure.status == status)
        stmt = stmt.offset(offset).limit(limit)
        result = await db.execute(stmt)
        return list(result.scalars().all())


async def resolve_users(
    offset: int = 0,
    limit: int = 10,
) -> list[User]:
    """Fetch users with pagination."""
    async with AsyncSessionLocal() as db:
        stmt = select(User).order_by(User.created_at.desc()).offset(offset).limit(limit)
        result = await db.execute(stmt)
        return list(result.scalars().all())


async def resolve_teams(
    offset: int = 0,
    limit: int = 10,
) -> list[Team]:
    """Fetch teams with pagination."""
    async with AsyncSessionLocal() as db:
        stmt = select(Team).order_by(Team.created_at.desc()).offset(offset).limit(limit)
        result = await db.execute(stmt)
        return list(result.scalars().all())
