from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.book import (
    BookAddRequest,
    BookAddResponse,
    BookBorrowRequest,
    BookBorrowResponse,
    BookDeleteRequest,
    BookDeleteResponse,
    BookListResponse,
)
from app.services import book_service

router = APIRouter()


@router.post("/book_add", response_model=BookAddResponse, status_code=status.HTTP_201_CREATED)
def book_add(payload: BookAddRequest, db: Session = Depends(get_db)) -> BookAddResponse:
    return book_service.add_book(db, payload)


@router.patch("/book_borrow", response_model=BookBorrowResponse)
def book_borrow(payload: BookBorrowRequest, db: Session = Depends(get_db)) -> BookBorrowResponse:
    return book_service.borrow_book(db, payload)


@router.get("/books", response_model=BookListResponse)
def books_list(db: Session = Depends(get_db)) -> BookListResponse:
    return book_service.list_books(db)


@router.delete("/book_delete", response_model=BookDeleteResponse)
def book_delete(payload: BookDeleteRequest, db: Session = Depends(get_db)) -> BookDeleteResponse:
    return book_service.delete_book(db, payload)
