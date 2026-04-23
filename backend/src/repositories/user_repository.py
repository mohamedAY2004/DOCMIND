"""Data access for :class:`User`."""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional, Sequence

from sqlalchemy import func, or_, select, update

from db.models import User, UserRole, UserStatus

from .base import BaseRepository


class UserRepository(BaseRepository[User]):
    model = User

    async def get(self, user_id: str) -> Optional[User]:
        return await self.session.get(User, user_id)

    async def get_by_username(self, username: str) -> Optional[User]:
        result = await self.session.execute(
            select(User).where(User.username == username)
        )
        return result.scalar_one_or_none()

    async def get_by_email(self, email: str) -> Optional[User]:
        result = await self.session.execute(
            select(User).where(func.lower(User.email) == email.lower())
        )
        return result.scalar_one_or_none()

    async def list_by_ids(self, ids: Sequence[str]) -> Sequence[User]:
        if not ids:
            return []
        result = await self.session.execute(
            select(User).where(User.id.in_(list(ids)))
        )
        return result.scalars().all()

    async def search(
        self,
        *,
        search: Optional[str],
        role: Optional[UserRole],
        offset: int,
        limit: int,
    ) -> tuple[Sequence[User], int]:
        stmt = select(User)
        if role is not None:
            stmt = stmt.where(User.role == role)
        if search:
            like = f"%{search.lower()}%"
            stmt = stmt.where(
                or_(
                    func.lower(User.name).like(like),
                    func.lower(User.email).like(like),
                    func.lower(User.id).like(like),
                )
            )
        total = await self.count(stmt)
        rows = (
            await self.session.execute(
                stmt.order_by(User.registered_at.desc()).offset(offset).limit(limit)
            )
        ).scalars().all()
        return rows, total

    async def add(self, user: User) -> User:
        self.session.add(user)
        await self.session.flush()
        return user

    async def set_status(self, user_id: str, status: UserStatus) -> None:
        await self.session.execute(
            update(User).where(User.id == user_id).values(status=status)
        )

    async def touch_last_active(self, user_id: str) -> None:
        await self.session.execute(
            update(User)
            .where(User.id == user_id)
            .values(last_active=datetime.now(timezone.utc))
        )
