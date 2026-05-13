from sqlalchemy import CheckConstraint, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class Reader(Base):
    __tablename__ = "readers"

    __table_args__ = (
        CheckConstraint(
            "length(library_card_number) = 6",
            name="ck_readers_library_card_number_six_digits",
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    library_card_number: Mapped[str] = mapped_column(String(6), unique=True, nullable=False, index=True)
    first_name: Mapped[str] = mapped_column(String(100), nullable=False)
    last_name: Mapped[str] = mapped_column(String(100), nullable=False)

    books = relationship("Book", back_populates="reader")
