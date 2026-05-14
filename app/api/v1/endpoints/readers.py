from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.reader import ReaderAddRequest, ReaderAddResponse
from app.services import reader_service

router = APIRouter()


@router.post("/reader_add", response_model=ReaderAddResponse, status_code=status.HTTP_201_CREATED)
def reader_add(payload: ReaderAddRequest, db: Session = Depends(get_db)) -> ReaderAddResponse:
    return reader_service.add_reader(db, payload)