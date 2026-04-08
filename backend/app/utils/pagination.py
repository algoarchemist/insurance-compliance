"""Pagination helpers for API responses."""

from typing import TypeVar, Generic, List, Optional
from pydantic import BaseModel

T = TypeVar("T")


class PaginationParams:
    """Standard pagination parameters."""
    def __init__(self, page: int = 1, page_size: int = 20):
        self.page = max(1, page)
        self.page_size = min(max(1, page_size), 100)
        self.offset = (self.page - 1) * self.page_size


def paginate_query(query, page: int = 1, page_size: int = 20):
    """Apply pagination to a SQLAlchemy query."""
    params = PaginationParams(page, page_size)
    return query.offset(params.offset).limit(params.page_size)
