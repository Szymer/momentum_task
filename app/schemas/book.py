from pydantic import BaseModel, ConfigDict, Field, AliasChoices


class BookAddRequest(BaseModel):
    title: str = Field(min_length=1, max_length=255)
    author: str = Field(min_length=1, max_length=255)
    isbn: str | None = Field(default=None, min_length=1, max_length=32)


class BookDeleteRequest(BaseModel):
    serial_number: int = Field(
        validation_alias=AliasChoices("serial_number", "serialNumber", "serialnumber"),
        ge=100000,
        le=999999,
    )


class BookAddResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    book_id: int
    serial_number: int
    available: bool
    edition_id: int
    edition_title: str
    edition_author: str
    edition_isbn: str


class BookDeleteResponse(BaseModel):
    deleted: bool
    serial_number: int


class BookListItem(BaseModel):
    book_id: int
    serial_number: int
    available: bool
    edition_id: int
    edition_title: str
    edition_author: str
    edition_isbn: str
    reader_id: int | None


class BookListResponse(BaseModel):
    total: int
    books: list[BookListItem]


class BookBorrowRequest(BaseModel):
    serial_number: int = Field(
        validation_alias=AliasChoices("serial_number", "serialNumber", "serialnumber"),
        ge=100000,
        le=999999,
    )
    borrowed: bool
    reader_id: int | None = None


class BookBorrowResponse(BaseModel):
    changed: bool
    message: str
    serial_number: int
    available: bool
    reader_id: int | None
