"""Standardized pagination (spec §3.2)."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Generic, Optional, Sequence, TypeVar

from fastapi import Query
from pydantic import BaseModel

T = TypeVar("T")


@dataclass
class PaginationParams:
    page: int
    page_size: int
    sort: Optional[str]
    search: Optional[str]

    @property
    def offset(self) -> int:
        return (self.page - 1) * self.page_size


def pagination_query(
    page: int = Query(1, ge=1),
    pageSize: int = Query(20, ge=1, le=100),
    sort: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
) -> PaginationParams:
    """FastAPI dependency that parses the standard pagination query string."""
    return PaginationParams(page=page, page_size=pageSize, sort=sort, search=search)


def admin_pagination_query(
    page: int = Query(1, ge=1),
    pageSize: int = Query(20, ge=1, le=1000),
    sort: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
) -> PaginationParams:
    """Pagination for admin list endpoints (higher cap for bulk UIs)."""
    return PaginationParams(page=page, page_size=pageSize, sort=sort, search=search)


class Page(BaseModel, Generic[T]):
    """Envelope returned by paginated endpoints (spec §3.2)."""

    items: Sequence[T]
    page: int
    pageSize: int
    total: int
    totalPages: int

    @classmethod
    def build(
        cls, items: Sequence[T], total: int, params: PaginationParams
    ) -> "Page[T]":
        total_pages = (total + params.page_size - 1) // params.page_size if params.page_size else 0
        return cls(
            items=items,
            page=params.page,
            pageSize=params.page_size,
            total=total,
            totalPages=total_pages,
        )
