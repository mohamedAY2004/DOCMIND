"""Declarative base + common mixins.

Every ORM model inherits from :class:`Base`. :class:`TimestampMixin` provides a
uniform ``created_at`` / ``updated_at`` pair.
"""
from __future__ import annotations

import enum as _enum
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import DateTime, Enum
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def pg_enum(py_enum: type[_enum.Enum], *, name: str) -> Enum:
    """Return a SQLAlchemy ``Enum`` bound to a Postgres enum type.

    By default SQLAlchemy sends the Python enum *member name* (e.g. ``"ADMIN"``)
    to Postgres. Our Postgres enum types are created with lowercase *values*
    (e.g. ``"admin"``), so we wire ``values_callable`` to emit ``.value`` instead.
    """

    def _values(cls: type[_enum.Enum]) -> list[Any]:
        return [m.value for m in cls]

    return Enum(py_enum, name=name, values_callable=_values, native_enum=True)


class Base(DeclarativeBase):
    """Project-wide declarative base."""


class TimestampMixin:
    """Adds ``created_at`` and ``updated_at`` columns in UTC."""

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=_utcnow,
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=_utcnow,
        onupdate=_utcnow,
        nullable=False,
    )
