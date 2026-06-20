"""Data access for :class:`Material`."""
from __future__ import annotations

from typing import Optional, Sequence

from sqlalchemy import select, update

from db.models import Material, MaterialStatus

from .base import BaseRepository


class MaterialRepository(BaseRepository[Material]):
    model = Material

    async def get(self, material_id: str) -> Optional[Material]:
        return await self.session.get(Material, material_id)

    async def list_for_subject(self, subject_id: str) -> Sequence[Material]:
        result = await self.session.execute(
            select(Material)
            .where(Material.subject_id == subject_id)
            .order_by(Material.created_at.desc())
        )
        return result.scalars().all()

    async def processed_names_for_subject(self, subject_id: str) -> Sequence[str]:
        """Names of a subject's PROCESSED (retrievable) materials, newest first.

        Used to build the corpus manifest injected into tutor prompts so the
        model knows which materials it can actually ground answers in.
        """
        result = await self.session.execute(
            select(Material.name)
            .where(
                Material.subject_id == subject_id,
                Material.status == MaterialStatus.PROCESSED,
            )
            .order_by(Material.created_at.desc())
        )
        return result.scalars().all()

    async def processed_materials_for_subject(
        self, subject_id: str
    ) -> Sequence[tuple[str, str]]:
        """``(id, name)`` for a subject's PROCESSED materials, newest first.

        Used to build the corpus manifest *and* the name->id allowlist the
        planner's source filter is validated against.
        """
        result = await self.session.execute(
            select(Material.id, Material.name)
            .where(
                Material.subject_id == subject_id,
                Material.status == MaterialStatus.PROCESSED,
            )
            .order_by(Material.created_at.desc())
        )
        return [(row[0], row[1]) for row in result.all()]

    async def count_for_subject(self, subject_id: str) -> int:
        from sqlalchemy import func

        result = await self.session.execute(
            select(func.count(Material.id)).where(Material.subject_id == subject_id)
        )
        return int(result.scalar() or 0)

    async def count_processed(self, subject_id: str) -> int:
        from sqlalchemy import func

        result = await self.session.execute(
            select(func.count(Material.id)).where(
                Material.subject_id == subject_id,
                Material.status == MaterialStatus.PROCESSED,
            )
        )
        return int(result.scalar() or 0)

    async def name_exists(self, subject_id: str, name: str) -> bool:
        result = await self.session.execute(
            select(Material.id).where(
                Material.subject_id == subject_id, Material.name == name
            )
        )
        return result.scalar_one_or_none() is not None

    async def add(self, material: Material) -> Material:
        self.session.add(material)
        await self.session.flush()
        return material

    async def set_status(self, material_id: str, status: MaterialStatus) -> None:
        await self.session.execute(
            update(Material).where(Material.id == material_id).values(status=status)
        )

    async def rename(self, material_id: str, name: str) -> None:
        await self.session.execute(
            update(Material).where(Material.id == material_id).values(name=name)
        )
