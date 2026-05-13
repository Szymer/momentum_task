# Momentum Task

Minimalny szkielet aplikacji FastAPI z klasycznym podziałem na warstwy.

## Baza danych

- konfiguracja bazy jest pobierana ze zmiennej `DATABASE_URL` (plik `.env`)
- migracje Alembic są w katalogu `alembic/`
- pierwsza migracja tworzy tabele `editions`, `readers` i `books`

Jeśli chcesz uruchomić lokalnie, ustaw `DATABASE_URL` w `.env` na własną instancję Postgresa.

## Model danych

- `editions` - ISBN, autor, tytuł
- `readers` - czytelnicy
- `books` - fizyczne egzemplarze z unikalnym 6-cyfrowym numerem seryjnym
- książka ma pole `available` (`true`/`false`)
- `library_card_number` jest ustawiany przy wypożyczeniu i czyszczony przy zwrocie
- `borrow_time` zapisuje lokalny czas wypożyczenia (`datetime` z lokalną strefą), a przy zwrocie jest czyszczony

## Struktura

- `app/main.py` - punkt startowy aplikacji
- `app/api` - routery HTTP
- `app/core` - konfiguracja i ustawienia środowiska
- `app/db` - miejsce na sesje i konfigurację bazy
- `app/models` - modele domenowe / ORM
- `app/schemas` - schematy Pydantic
- `app/services` - logika biznesowa
- `app/repositories` - dostęp do danych
- `tests` - testy aplikacji

## Uruchomienie Docker Compose

Najprostsza opcja uruchomienia całego środowiska (API + PostgreSQL):

1. Skopiuj plik przykładowy:

```bash
cp .env.example .env
```

2. Ustaw własne wartości (minimum: `POSTGRES_PASSWORD`) w `.env`.

3. Uruchom:

```bash
docker compose up
```

Compose:

- uruchamia PostgreSQL (`db`)
- czeka na gotowość bazy (`healthcheck`)
- uruchamia migracje (`alembic upgrade head`)
- startuje API na `http://localhost:8000`

Dokumentacja Swagger: `http://localhost:8000/docs`

## Uruchomienie

```bash
uvicorn app.main:app --reload
```

## Migracje

```bash
alembic upgrade head
```

## Endpointy

- `GET /api/v1/health` - prosty healthcheck
- `POST /api/v1/reader_add` - dodaje czytelnika na podstawie `first_name` i `last_name`, numer karty bibliotecznej (6-cyfrowy string) jest generowany automatycznie
- `POST /api/v1/book_add` - dodaje egzemplarz książki na podstawie `title`, `author` i opcjonalnie `isbn`
- `PATCH /api/v1/book_borrow` - zmienia status wypożyczenia książki (`borrowed: true/false`) po `serial_number`
- `GET /api/v1/books` - pobiera listę wszystkich książek
- `DELETE /api/v1/book_delete` - usuwa książkę po `serial_number`

## Przykładowe payloady JSON

### `GET /api/v1/health`

Request body: brak

Przykładowa odpowiedź:

```json
{
  "status": "ok"
}
```

### `POST /api/v1/reader_add`

Przykładowy request:

```json
{
  "first_name": "Jan",
  "last_name": "Kowalski"
}
```

Przykładowa odpowiedź:

```json
{
  "library_card_number": "000001",
  "first_name": "Jan",
  "last_name": "Kowalski"
}
```

### `POST /api/v1/book_add`

Przykładowy request (z ISBN):

```json
{
  "title": "Solaris",
  "author": "Stanislaw Lem",
  "isbn": "9780156027607"
}
```

Przykładowy request (bez ISBN):

```json
{
  "title": "Solaris",
  "author": "Stanislaw Lem"
}
```

Przykładowa odpowiedź:

```json
{
  "book_id": 1,
  "serial_number": "000001",
  "available": true,
  "edition_id": 1,
  "edition_title": "Solaris",
  "edition_author": "Stanislaw Lem",
  "edition_isbn": "9780156027607"
}
```

### `PATCH /api/v1/book_borrow`

Przykładowy request (wypożyczenie):

```json
{
  "serial_number": "000001",
  "borrowed": true,
  "library_card_number": "000001"
}
```

Przykładowy request (zwrot):

```json
{
  "serial_number": "000001",
  "borrowed": false
}
```

Przykładowa odpowiedź:

```json
{
  "changed": true,
  "message": "Book is now borrowed.",
  "serial_number": "000001",
  "available": false,
  "library_card_number": "000001",
  "borrow_time": "2026-05-13T10:15:30.123456+02:00"
}
```

### `GET /api/v1/books`

Request body: brak

Przykładowa odpowiedź:

```json
{
  "total": 1,
  "books": [
    {
      "book_id": 1,
      "serial_number": "000001",
      "available": false,
      "edition_id": 1,
      "edition_title": "Solaris",
      "edition_author": "Stanislaw Lem",
      "edition_isbn": "9780156027607",
      "library_card_number": "000001",
      "borrow_time": "2026-05-13T10:15:30.123456+02:00",
      "reader_first_name": "Jan",
      "reader_last_name": "Kowalski"
    }
  ]
}
```

### `DELETE /api/v1/book_delete`

Przykładowy request:

```json
{
  "serial_number": "000001"
}
```

Przykładowa odpowiedź:

```json
{
  "deleted": true,
  "serial_number": "000001"
}
```

Zasada działania `book_add`:

- jeśli `isbn` istnieje w bazie, dodaje nowy egzemplarz do istniejącego wydania
- jeśli `isbn` nie istnieje, tworzy nowe wydanie i dodaje egzemplarz
- jeśli `isbn` nie podano, ale `title` i `author` wskazują na istniejące wydanie, dodaje nowy egzemplarz do tego wydania
- jeśli `isbn` nie podano i nie ma pasującego wydania, endpoint zwraca błąd 400

Zasada działania `book_borrow`:

- wymagane: `serial_number`, `borrowed`
- jeśli ustawiasz `borrowed=true`, wymagane jest `library_card_number`
- nieistniejący `serial_number` zwraca 404
- nieistniejący `library_card_number` zwraca 404
- przy `borrowed=true` API zapisuje `borrow_time` jako `datetime.now().astimezone()`
- przy `borrowed=false` API czyści `borrow_time`
- jeśli status się nie zmienia, endpoint zwraca `changed=false`
