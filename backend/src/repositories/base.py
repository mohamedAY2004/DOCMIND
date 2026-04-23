"""Common repository helpers."""
from __future__ import annotations

from typing import Generic, Optional, Sequence, Type, TypeVar

from sqlalchemy import Select, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from db.base import Base

TModel = TypeVar("TModel", bound=Base)


class BaseRepository(Generic[TModel]):
    """Minimal generic repository. Concrete classes add domain-specific queries."""

    model: Type[TModel]

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get(self, pk) -> Optional[TModel]:  # type: ignore[no-untyped-def]
        return await self.session.get(self.model, pk)

    async def list_all(self) -> Sequence[TModel]:
        result = await self.session.execute(select(self.model))
        return result.scalars().all()

    async def delete(self, entity: TModel) -> None:
        await self.session.delete(entity)
        await self.session.flush()

    async def count(self, stmt: Optional[Select] = None) -> int:
        base = stmt if stmt is not None else select(self.model)
        subq = base.with_only_columns(func.count()).order_by(None)
        result = await self.session.execute(subq)
        return int(result.scalar() or 0)
