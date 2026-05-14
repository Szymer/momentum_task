from datetime import datetime

from pydantic import AliasChoices, BaseModel, ConfigDict, Field, StrictStr


class BookAddRequest(BaseModel):
    title: str = Field(min_length=1, max_length=255)
    author: str = Field(min_length=1, max_length=255)
    isbn: str | None = Field(default=None, min_length=1, max_length=32)


class BookDeleteRequest(BaseModel):
    serial_number: StrictStr = Field(
        validation_alias=AliasChoices("serial_number", "serialNumber", "serialnumber"),
        pattern=r"^\d{6}$",
    )


class BookAddResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    book_id: int
    serial_number: str
    available: bool
    edition_id: int
    edition_title: str
    edition_author: str
    edition_isbn: str


class BookDeleteResponse(BaseModel):
    deleted: bool
    serial_number: str


class BookListItem(BaseModel):
    book_id: int
    serial_number: str
    available: bool
    edition_id: int
    edition_title: str
    edition_author: str
    edition_isbn: str
    library_card_number: str | None
    borrow_time: datetime | None
    reader_first_name: str | None
    reader_last_name: str | None


class BookListResponse(BaseModel):
    total: int
    books: list[BookListItem]


class BookBorrowRequest(BaseModel):
    serial_number: StrictStr = Field(
        validation_alias=AliasChoices("serial_number", "serialNumber", "serialnumber"),
        pattern=r"^\d{6}$",
    )
    borrowed: bool
    library_card_number: StrictStr | None = Field(default=None, pattern=r"^\d{6}$")


class BookBorrowResponse(BaseModel):
    changed: bool
    message: str
    serial_number: str
    available: bool
    library_card_number: str | None
    borrow_time: datetime | None
