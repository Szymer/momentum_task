from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models import Reader
from app.schemas.reader import ReaderAddRequest, ReaderAddResponse


def _generate_library_card_number(db: Session) -> str:
    max_card_number = db.scalar(select(func.max(Reader.library_card_number)))
    next_card_number = "000001" if max_card_number is None else f"{int(max_card_number) + 1:06d}"

    if next_card_number > "999999":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No more six-digit library card numbers are available.",
        )

    return next_card_number


def add_reader(db: Session, payload: ReaderAddRequest) -> ReaderAddResponse:
    library_card_number = _generate_library_card_number(db)

    reader = Reader(
        library_card_number=library_card_number,
        first_name=payload.first_name,
        last_name=payload.last_name,
    )

    db.add(reader)
    db.commit()
    db.refresh(reader)

    return ReaderAddResponse(
        library_card_number=reader.library_card_number,
        first_name=reader.first_name,
        last_name=reader.last_name,
    )