"""Schemas package."""

from app.schemas.book import (
    BookAddRequest,
    BookAddResponse,
    BookBorrowRequest,
    BookBorrowResponse,
    BookDeleteRequest,
    BookDeleteResponse,
    BookListItem,
    BookListResponse,
)

__all__ = [
    "BookAddRequest",
    "BookAddResponse",
    "BookBorrowRequest",
    "BookBorrowResponse",
    "BookDeleteRequest",
    "BookDeleteResponse",
    "BookListItem",
    "BookListResponse",
]

