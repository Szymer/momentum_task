from sqlalchemy import Boolean, CheckConstraint, ForeignKey, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class Book(Base):
    __tablename__ = "books"

    __table_args__ = (
        CheckConstraint(
            "serial_number BETWEEN 100000 AND 999999",
            name="ck_books_serial_number_six_digits",
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    serial_number: Mapped[int] = mapped_column(Integer, unique=True, nullable=False, index=True)
    available: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, index=True)
    edition_id: Mapped[int] = mapped_column(
        ForeignKey("editions.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    reader_id: Mapped[int | None] = mapped_column(
        ForeignKey("readers.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    edition = relationship("Edition", back_populates="books")
    reader = relationship("Reader", back_populates="books")
