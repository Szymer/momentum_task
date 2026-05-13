# Momentum Task

Minimalny szkielet aplikacji FastAPI z klasycznym podziałem na warstwy.

## Baza danych

- domyślnie PostgreSQL pod `postgresql+psycopg://postgres:postgres@localhost:5432/momentum_task`
- migracje Alembic są w katalogu `alembic/`
- pierwsza migracja tworzy tabele `editions`, `readers` i `books`

Jeśli chcesz uruchomić lokalnie, ustaw `DATABASE_URL` w `.env` na własną instancję Postgresa.

## Model danych

- `editions` - ISBN, autor, tytuł
- `readers` - czytelnicy
- `books` - fizyczne egzemplarze z unikalnym 6-cyfrowym numerem seryjnym
- książka ma pole `available` (`true`/`false`)
- `reader_id` jest ustawiany przy wypożyczeniu i czyszczony przy zwrocie

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
- `POST /api/v1/book_add` - dodaje egzemplarz książki na podstawie `title`, `author` i opcjonalnie `isbn`
- `PATCH /api/v1/book_borrow` - zmienia status wypożyczenia książki (`borrowed: true/false`) po `serial_number`
- `GET /api/v1/books` - pobiera listę wszystkich książek
- `DELETE /api/v1/book_delete` - usuwa książkę po `serial_number`

Zasada działania `book_add`:

- jeśli `isbn` istnieje w bazie, dodaje nowy egzemplarz do istniejącego wydania
- jeśli `isbn` nie istnieje, tworzy nowe wydanie i dodaje egzemplarz
- jeśli `isbn` nie podano, ale `title` i `author` wskazują na istniejące wydanie, dodaje nowy egzemplarz do tego wydania
- jeśli `isbn` nie podano i nie ma pasującego wydania, endpoint zwraca błąd 400

Zasada działania `book_borrow`:

- wymagane: `serial_number`, `borrowed`
- jeśli ustawiasz `borrowed=true`, wymagane jest też `reader_id`
- nieistniejący `serial_number` zwraca 404
- nieistniejący `reader_id` zwraca 404
- jeśli status się nie zmienia, endpoint zwraca `changed=false`
