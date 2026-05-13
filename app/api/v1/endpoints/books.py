from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models import Book, Edition, Reader
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

router = APIRouter()


def _get_or_create_edition(db: Session, payload: BookAddRequest) -> Edition:
    if payload.isbn:
        edition = db.scalar(select(Edition).where(Edition.isbn == payload.isbn))
        if edition is not None:
            return edition

        edition = Edition(isbn=payload.isbn, author=payload.author, title=payload.title)
        db.add(edition)
        db.flush()
        return edition

    edition = db.scalar(
        select(Edition).where(
            Edition.title == payload.title,
            Edition.author == payload.author,
        )
    )
    if edition is not None:
        return edition

    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail="ISBN is required when the edition does not already exist by title and author.",
    )


def _generate_serial_number(db: Session) -> int:
    max_serial_number = db.scalar(select(func.max(Book.serial_number)))
    next_serial_number = 100000 if max_serial_number is None else max_serial_number + 1

    if next_serial_number > 999999:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No more six-digit serial numbers are available.",
        )

    return next_serial_number


@router.post("/book_add", response_model=BookAddResponse, status_code=status.HTTP_201_CREATED)
def book_add(payload: BookAddRequest, db: Session = Depends(get_db)) -> BookAddResponse:
    edition = _get_or_create_edition(db, payload)
    serial_number = _generate_serial_number(db)

    book = Book(
        serial_number=serial_number,
        available=True,
        edition_id=edition.id,
    )
    db.add(book)
    db.commit()
    db.refresh(book)
    db.refresh(edition)

    return BookAddResponse(
        book_id=book.id,
        serial_number=book.serial_number,
        available=book.available,
        edition_id=edition.id,
        edition_title=edition.title,
        edition_author=edition.author,
        edition_isbn=edition.isbn,
    )


@router.patch("/book_borrow", response_model=BookBorrowResponse)
def book_borrow(payload: BookBorrowRequest, db: Session = Depends(get_db)) -> BookBorrowResponse:
    book = db.scalar(select(Book).where(Book.serial_number == payload.serial_number))
    if book is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Book not found.")

    desired_available = not payload.borrowed

    if book.available == desired_available:
        return BookBorrowResponse(
            changed=False,
            message=f"Book is already {'available' if desired_available else 'borrowed'}.",
            serial_number=book.serial_number,
            available=book.available,
            reader_id=book.reader_id,
        )

    if payload.borrowed and payload.reader_id is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="reader_id is required when borrowing a book.",
        )

    if payload.borrowed:
        reader_exists = db.scalar(select(Reader.id).where(Reader.id == payload.reader_id))
        if reader_exists is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Reader not found.",
            )

    book.available = desired_available
    book.reader_id = payload.reader_id if payload.borrowed else None
    db.commit()
    db.refresh(book)

    return BookBorrowResponse(
        changed=True,
        message=f"Book is now {'available' if desired_available else 'borrowed'}.",
        serial_number=book.serial_number,
        available=book.available,
        reader_id=book.reader_id,
    )


@router.get("/books", response_model=BookListResponse)
def books_list(db: Session = Depends(get_db)) -> BookListResponse:
    rows = db.execute(
        select(Book, Edition).join(Edition, Book.edition_id == Edition.id)
    ).all()

    items = [
        BookListItem(
            book_id=book.id,
            serial_number=book.serial_number,
            available=book.available,
            edition_id=edition.id,
            edition_title=edition.title,
            edition_author=edition.author,
            edition_isbn=edition.isbn,
            reader_id=book.reader_id,
        )
        for book, edition in rows
    ]

    return BookListResponse(total=len(items), books=items)


@router.delete("/book_delete", response_model=BookDeleteResponse)
def book_delete(payload: BookDeleteRequest, db: Session = Depends(get_db)) -> BookDeleteResponse:
    book = db.scalar(select(Book).where(Book.serial_number == payload.serial_number))
    if book is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Book not found.")

    db.delete(book)
    db.commit()

    return BookDeleteResponse(deleted=True, serial_number=payload.serial_number)
