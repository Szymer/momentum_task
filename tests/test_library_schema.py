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
        reader = Reader(library_card_number="123456", first_name="Jan", last_name="Kowalski")
        session.add_all([edition, reader])
        session.flush()
        edition_id = edition.id
        reader_card_number = reader.library_card_number

        book = Book(
            serial_number="123456",
            available=False,
            edition_id=edition_id,
            library_card_number=reader_card_number,
        )
        session.add(book)
        session.commit()

        saved_book = session.get(Book, book.id)

    assert saved_book is not None
    assert saved_book.serial_number == "123456"
    assert saved_book.available is False
    assert saved_book.library_card_number == reader_card_number
    assert saved_book.edition_id == edition_id


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
    assert response.json()["serial_number"] == "000001"
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
    assert response.json()["serial_number"] == "000001"
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
            Book(serial_number="000001", available=True, edition_id=edition.id),
            Book(serial_number="000002", available=True, edition_id=edition.id),
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
    assert serials == {"000001", "000002"}


def test_books_list_includes_reader_name_for_borrowed_book() -> None:
    engine = create_engine(
        "sqlite+pysqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)

    with Session(engine) as session:
        edition = Edition(isbn="9780132350884", author="Robert C. Martin", title="Clean Code")
        reader = Reader(library_card_number="400000", first_name="Jan", last_name="Kowalski")
        session.add_all([edition, reader])
        session.flush()
        session.add(Book(
            serial_number="000001",
            available=False,
            edition_id=edition.id,
            library_card_number=reader.library_card_number,
        ))
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
    assert body["total"] == 1
    assert body["books"][0]["library_card_number"] == "400000"
    assert body["books"][0]["reader_first_name"] == "Jan"
    assert body["books"][0]["reader_last_name"] == "Kowalski"


def _make_engine_with_edition_and_book(borrowed: bool = False):
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
            reader = Reader(library_card_number="200001", first_name="Anna", last_name="Nowak")
            session.add(reader)
            session.flush()
            book = Book(
                serial_number="000001",
                available=False,
                edition_id=edition.id,
                library_card_number=reader.library_card_number,
            )
        else:
            book = Book(
                serial_number="000001",
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
            json={"serial_number": "111111", "borrowed": True, "library_card_number": "100000"},
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
            json={"serial_number": "000001", "borrowed": False},
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
        reader = Reader(library_card_number="300001", first_name="Piotr", last_name="Wiśniewski")
        session.add(reader)
        session.commit()
        reader_card_number = reader.library_card_number

    def override_get_db():
        with Session(engine) as session:
            yield session

    app.dependency_overrides[get_db] = override_get_db
    try:
        response = TestClient(app).patch(
            "/api/v1/book_borrow",
            json={"serial_number": "000001", "borrowed": True, "library_card_number": reader_card_number},
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    body = response.json()
    assert body["changed"] is True
    assert body["available"] is False
    assert body["library_card_number"] == reader_card_number


def test_book_borrow_fails_for_non_existing_reader() -> None:
    engine = _make_engine_with_edition_and_book(borrowed=False)

    def override_get_db():
        with Session(engine) as session:
            yield session

    app.dependency_overrides[get_db] = override_get_db
    try:
        response = TestClient(app).patch(
            "/api/v1/book_borrow",
            json={"serial_number": "000001", "borrowed": True, "library_card_number": "999999"},
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 404
    assert response.json()["detail"] == "Reader not found."


def test_book_borrow_changes_status_using_library_card_number() -> None:
    engine = _make_engine_with_edition_and_book(borrowed=False)

    with Session(engine) as session:
        reader = Reader(library_card_number="310000", first_name="Ewa", last_name="Kaczmarek")
        session.add(reader)
        session.commit()
        expected_card_number = reader.library_card_number

    def override_get_db():
        with Session(engine) as session:
            yield session

    app.dependency_overrides[get_db] = override_get_db
    try:
        response = TestClient(app).patch(
            "/api/v1/book_borrow",
            json={"serial_number": "000001", "borrowed": True, "library_card_number": "310000"},
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    body = response.json()
    assert body["changed"] is True
    assert body["available"] is False
    assert body["library_card_number"] == expected_card_number


def test_book_delete_requires_serial_number() -> None:
    client = TestClient(app)

    response = client.request("DELETE", "/api/v1/book_delete", json={})

    assert response.status_code == 422


def test_book_delete_rejects_numeric_serial_number_type() -> None:
    client = TestClient(app)

    response = client.request("DELETE", "/api/v1/book_delete", json={"serial_number": 123456})

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
        book = Book(serial_number="123456", available=True, edition_id=edition.id)
        session.add(book)
        session.commit()

    def override_get_db():
        with Session(engine) as session:
            yield session

    app.dependency_overrides[get_db] = override_get_db

    try:
        client = TestClient(app)
        response = client.request("DELETE", "/api/v1/book_delete", json={"serial_number": "123456"})
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json() == {"deleted": True, "serial_number": "123456"}

    with Session(engine) as session:
        deleted_book = session.query(Book).filter(Book.serial_number == "123456").one_or_none()

    assert deleted_book is None


def test_reader_add_creates_reader_with_auto_card_number() -> None:
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
            "/api/v1/reader_add",
            json={"first_name": "Jan", "last_name": "Kowalski"},
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 201
    assert response.json() == {
        "library_card_number": "000001",
        "first_name": "Jan",
        "last_name": "Kowalski",
    }


def test_reader_add_increments_library_card_number() -> None:
    engine = create_engine(
        "sqlite+pysqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)

    with Session(engine) as session:
        session.add(Reader(library_card_number="000001", first_name="Anna", last_name="Nowak"))
        session.commit()

    def override_get_db():
        with Session(engine) as session:
            yield session

    app.dependency_overrides[get_db] = override_get_db

    try:
        client = TestClient(app)
        response = client.post(
            "/api/v1/reader_add",
            json={"first_name": "Piotr", "last_name": "Zielinski"},
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 201
    assert response.json()["library_card_number"] == "000002"
