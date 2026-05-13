from datetime import datetime

from sqlalchemy import Boolean, CheckConstraint, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class Book(Base):
    __tablename__ = "books"

    __table_args__ = (
        CheckConstraint(
            "length(serial_number) = 6",
            name="ck_books_serial_number_six_digits",
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    serial_number: Mapped[str] = mapped_column(String(6), unique=True, nullable=False, index=True)
    available: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, index=True)
    edition_id: Mapped[int] = mapped_column(
        ForeignKey("editions.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    library_card_number: Mapped[str | None] = mapped_column(
        ForeignKey("readers.library_card_number", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    borrow_time: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    edition = relationship("Edition", back_populates="books")
    reader = relationship("Reader", back_populates="books")
