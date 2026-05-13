from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from fastapi.testclient import TestClient

from app.db.base import Base
from app.db.session import get_db
from app.main import app
from app.models import Book, Edition, Reader


def test_library_schema_supports_borrowed_book() -> None:
    engine = create_engine(
        "sqlite+pysqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)

    with Session(engine) as session:
        edition = Edition(isbn="9780132350884", author="Robert C. Martin", title="Clean Code")
        reader = Reader(library_card_number=123456, first_name="Jan", last_name="Kowalski")
        session.add_all([edition, reader])
        session.flush()

        book = Book(
            serial_number=123456,
            available=False,
            edition_id=edition.id,
            reader_id=reader.id,
        )
        session.add(book)
        session.commit()

        saved_book = session.get(Book, book.id)

    assert saved_book is not None
    assert saved_book.serial_number == 123456
    assert saved_book.available is False
    assert saved_book.reader_id == reader.id
    assert saved_book.edition_id == edition.id


def test_book_add_creates_new_edition_when_isbn_is_new() -> None:
    engine = create_engine(
        "sqlite+pysqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)

    def override_get_db():
        with Session(engine) as session:
            yield session

    app.dependency_overrides[get_db] = override_get_db

    try:
        client = TestClient(app)
        response = client.post(
            "/api/v1/book_add",
            json={"title": "Clean Code", "author": "Robert C. Martin", "isbn": "9780132350884"},
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 201
    assert response.json()["serial_number"] == 100000
    assert response.json()["edition_isbn"] == "9780132350884"


def test_book_add_appends_to_existing_edition_without_isbn() -> None:
    engine = create_engine(
        "sqlite+pysqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)

    with Session(engine) as session:
        edition = Edition(isbn="9780132350884", author="Robert C. Martin", title="Clean Code")
        session.add(edition)
        session.commit()

    def override_get_db():
        with Session(engine) as session:
            yield session

    app.dependency_overrides[get_db] = override_get_db

    try:
        client = TestClient(app)
        response = client.post(
            "/api/v1/book_add",
            json={"title": "Clean Code", "author": "Robert C. Martin"},
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 201
    assert response.json()["serial_number"] == 100000
    assert response.json()["edition_isbn"] == "9780132350884"


def test_books_list_returns_all_books() -> None:
    engine = create_engine(
        "sqlite+pysqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)

    with Session(engine) as session:
        edition = Edition(isbn="9780132350884", author="Robert C. Martin", title="Clean Code")
        session.add(edition)
        session.flush()
        session.add_all([
            Book(serial_number=100000, available=True, edition_id=edition.id),
            Book(serial_number=100001, available=True, edition_id=edition.id),
        ])
        session.commit()

    def override_get_db():
        with Session(engine) as session:
            yield session

    app.dependency_overrides[get_db] = override_get_db

    try:
        client = TestClient(app)
        response = client.get("/api/v1/books")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    body = response.json()
    assert body["total"] == 2
    serials = {b["serial_number"] for b in body["books"]}
    assert serials == {100000, 100001}


def _make_engine_with_edition_and_book(borrowed: bool = False, reader_id: int | None = None):
    engine = create_engine(
        "sqlite+pysqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)

    with Session(engine) as session:
        edition = Edition(isbn="9780132350884", author="Robert C. Martin", title="Clean Code")
        session.add(edition)
        session.flush()
        if borrowed:
            reader = Reader(library_card_number=200001, first_name="Anna", last_name="Nowak")
            session.add(reader)
            session.flush()
            book = Book(
                serial_number=100000,
                available=False,
                edition_id=edition.id,
                reader_id=reader.id,
            )
        else:
            book = Book(
                serial_number=100000,
                available=True,
                edition_id=edition.id,
            )
        session.add(book)
        session.commit()

    return engine


def test_book_borrow_returns_404_when_not_found() -> None:
    engine = create_engine(
        "sqlite+pysqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)

    def override_get_db():
        with Session(engine) as session:
            yield session

    app.dependency_overrides[get_db] = override_get_db
    try:
        response = TestClient(app).patch(
            "/api/v1/book_borrow",
            json={"serial_number": 111111, "borrowed": True, "reader_id": 1},
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 404


def test_book_borrow_reports_unchanged_when_status_already_set() -> None:
    engine = _make_engine_with_edition_and_book(borrowed=False)

    def override_get_db():
        with Session(engine) as session:
            yield session

    app.dependency_overrides[get_db] = override_get_db
    try:
        response = TestClient(app).patch(
            "/api/v1/book_borrow",
            json={"serial_number": 100000, "borrowed": False},
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    body = response.json()
    assert body["changed"] is False
    assert body["available"] is True


def test_book_borrow_changes_status_to_borrowed() -> None:
    engine = _make_engine_with_edition_and_book(borrowed=False)

    with Session(engine) as session:
        reader = Reader(library_card_number=300001, first_name="Piotr", last_name="Wiśniewski")
        session.add(reader)
        session.commit()
        reader_id = reader.id

    def override_get_db():
        with Session(engine) as session:
            yield session

    app.dependency_overrides[get_db] = override_get_db
    try:
        response = TestClient(app).patch(
            "/api/v1/book_borrow",
            json={"serial_number": 100000, "borrowed": True, "reader_id": reader_id},
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    body = response.json()
    assert body["changed"] is True
    assert body["available"] is False
    assert body["reader_id"] == reader_id


def test_book_borrow_fails_for_non_existing_reader() -> None:
    engine = _make_engine_with_edition_and_book(borrowed=False)

    def override_get_db():
        with Session(engine) as session:
            yield session

    app.dependency_overrides[get_db] = override_get_db
    try:
        response = TestClient(app).patch(
            "/api/v1/book_borrow",
            json={"serial_number": 100000, "borrowed": True, "reader_id": 999999},
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 404
    assert response.json()["detail"] == "Reader not found."


def test_book_delete_requires_serial_number() -> None:
    client = TestClient(app)

    response = client.request("DELETE", "/api/v1/book_delete", json={})

    assert response.status_code == 422


def test_book_delete_removes_book_by_serial_number() -> None:
    engine = create_engine(
        "sqlite+pysqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)

    with Session(engine) as session:
        edition = Edition(isbn="9780132350884", author="Robert C. Martin", title="Clean Code")
        session.add(edition)
        session.flush()
        book = Book(serial_number=123456, available=True, edition_id=edition.id)
        session.add(book)
        session.commit()

    def override_get_db():
        with Session(engine) as session:
            yield session

    app.dependency_overrides[get_db] = override_get_db

    try:
        client = TestClient(app)
        response = client.request("DELETE", "/api/v1/book_delete", json={"serial_number": 123456})
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json() == {"deleted": True, "serial_number": 123456}

    with Session(engine) as session:
        deleted_book = session.query(Book).filter(Book.serial_number == 123456).one_or_none()

    assert deleted_book is None
