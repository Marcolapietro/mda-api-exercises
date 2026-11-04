# Exercise 6b: An API on top of a MySQL database (Library API)

## Objective
Build a REST API on top of a **real MySQL database** that already exists: connect to it, turn each HTTP request into SQL, and turn database errors into the right HTTP errors.

## Description
Up to exercise 06 the notes lived in a Python dict and were lost on every restart. In real projects the data lives in a database, and very often **the database already exists** when you arrive: someone designed the tables years ago and your job is to put an API in front of them.

That is this exercise. You get a MySQL database (in Docker) with a library: **22 authors and 150 books**. The Library API already has most of its code; you complete the blanks (`_____`) in `app.py`. Everything you learned in 04-06 still applies (CRUD, `201` + `Location`, `204`, RFC 9457 errors, offset pagination). What is new is where the data comes from:

| In 04-06 (dict) | Here (MySQL) |
|---|---|
| `notes[note_id]` | `SELECT ... WHERE id = %s` |
| `next_id += 1` | MySQL generates the id (`AUTO_INCREMENT`), you read it with `cur.lastrowid` |
| `notes[id] = note` | `INSERT` / `UPDATE` + `conn.commit()` |
| `del notes[id]` | `DELETE` (`cur.rowcount` says if a row was there) |
| `sorted(...)[offset:offset + limit]` | `ORDER BY id LIMIT %s OFFSET %s` |
| You check duplicates by hand (or not at all) | MySQL rejects them (`UNIQUE`, foreign keys) and you answer `409` |
| Data lost on restart | Data stays |

There is **no authentication** in this exercise, and **no ORM**: you write the SQL, so you see exactly what each endpoint asks the database.

## Quick Start

You need **Docker Desktop** (or Rancher Desktop) running, and Python 3.12 or newer.

```bash
cd exercises/06b-mysql-database

# 1. The database: copy the settings and start MySQL
#    (the first time Docker downloads the images, a few hundred MB: run `docker compose pull` before class)
cp .env.example .env            # Windows CMD: copy .env.example .env
docker compose up -d --wait

# 2. The API
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
# Fill the blanks from top to bottom; the app starts once the PATCH and DELETE decorators (with the `status_code=` of DELETE) and the `le=` of the limit are complete
fastapi dev app.py
```

The API runs at `http://127.0.0.1:8000` (automatic documentation at `/docs`).

`docker compose up -d --wait` starts two containers: **MySQL** on port `3306` and **Adminer** on `http://127.0.0.1:8080`, a web page to look at the tables. Log in to Adminer with System `MySQL`, Server `mysql`, Username `library`, Password `library-pass`, Database `library`. Keep it open while you test: after each request, look at what changed in the table.

While a decorator blank is still there, `fastapi dev` stops with an `AttributeError` that points at `@app._____`. After you fix it, the `status_code=_____` of DELETE gives a `NameError`, and an unfinished `le=_____` also stops the start-up: the error ends in `'le' must be coercible to an integer` (on Python 3.13 or older, a `NameError` pointing at the `limit` line), because FastAPI reads the `Query(...)` rules when it registers the route. The other blanks sit inside functions or inside SQL strings, so they only fail when a request reaches them (a `500` or a wrong answer).

## The database

`db/init.sql` creates the two tables and loads the data. Docker runs it **only the first time**, when the data volume is empty.

```
authors                          books
---------------------------      --------------------------------------------
id          INT PK AUTO_INC      id          INT PK AUTO_INC
name        VARCHAR UNIQUE       title       VARCHAR NOT NULL
country     VARCHAR              isbn        CHAR(13) UNIQUE
birth_year  SMALLINT             year        SMALLINT
                                 author_id   INT  -> authors.id (foreign key)
                                 created_at  TIMESTAMP (set by MySQL)
                                 updated_at  TIMESTAMP (set by MySQL on every UPDATE)
```

Three rules live **in the database**, not in Python, and the API turns them into HTTP errors:

- `isbn` is `UNIQUE`: a second book with the same ISBN is rejected → `409 Conflict`.
- `authors.name` is `UNIQUE`: the same for a duplicate author → `409 Conflict`.
- `books.author_id` is a **foreign key**: a book cannot point to an author that does not exist (→ `422`), and an author who still has books cannot be deleted (→ `409`).

The titles, authors and years are real. The ISBNs are made up (13 digits with a valid check digit).

## Requirements

1. **Dependencies** (`requirements.txt`): `fastapi[standard]`, `PyMySQL` (the MySQL driver), `cryptography` (needed by PyMySQL to log in to MySQL 8) and `python-dotenv` (reads `.env`).

2. **API Structure:**

   **Books** (full CRUD, this is where the blanks are)

   | Method | URI | SQL | Success | Errors |
   |--------|-----|-----|---------|--------|
   | `GET` | `/books?limit=20&offset=0&author_id=2&q=sol` | `SELECT ... JOIN authors ... LIMIT %s OFFSET %s` | `200` | `422` |
   | `GET` | `/books/{id}` | `SELECT ... WHERE b.id = %s` | `200` | `404` |
   | `POST` | `/books` | `INSERT` | `201` + `Location` | `409` duplicate ISBN, `422` unknown `author_id` or invalid body |
   | `PUT` | `/books/{id}` | `UPDATE` all the fields | `200` | `404`, `409`, `422` |
   | `PATCH` | `/books/{id}` | `UPDATE` only the fields sent | `200` | `404`, `409`, `422` |
   | `DELETE` | `/books/{id}` | `DELETE` | `204`, no body | `404` |

   **Authors** (already written, read them)

   | Method | URI | Success | Errors |
   |--------|-----|---------|--------|
   | `GET` | `/authors?q=garcia` | `200` | |
   | `GET` | `/authors/{id}` | `200` (includes `book_count`) | `404` |
   | `POST` | `/authors` | `201` + `Location` (can also create the author's books, in one transaction) | `409`, `422` |
   | `DELETE` | `/authors/{id}` | `204` | `404`, `409` if the author still has books |

   A book looks like this. `id`, `created_at` and `updated_at` come from MySQL; `author` comes from a `JOIN` with the `authors` table:

   ```json
   {"id": 5, "title": "Cien años de soledad", "isbn": "9788410395954", "year": 1967,
    "author": {"id": 2, "name": "Gabriel García Márquez"},
    "created_at": "2026-11-04T09:30:00Z", "updated_at": "2026-11-04T09:30:00Z"}
   ```

   - `GET /books`: books by `id`. `limit` (default `20`, between `1` and `100`, above `100` is a `422`), `offset` (default `0`), `author_id` (only that author's books) and `q` (part of the title, accents and case do not matter). The `page` object has `limit`, `offset`, `total`, and `next`/`prev` links that keep your filters.
   - `BookCreate` (body of `POST` and `PUT`): `title` (required), `author_id` (required), `isbn` (13 digits, optional) and `year` (optional). `PUT` sends the complete book: a field you leave out becomes `null`.
   - `BookUpdate` (body of `PATCH`): every field optional; an empty body is a `422`.
   - Every error is RFC 9457 `application/problem+json`, as in 04-06.

3. **Testing:** use Postman, `curl` or `/docs`, and watch the tables in Adminer.

## Suggested Steps

1. **Read `app.py` from the top:**
   - `MYSQL` reads the connection settings from `.env`.
   - `db()` opens **one connection per request** and always closes it. `autocommit` is off: nothing is saved until you call `conn.commit()`.
   - `integrity_error()` translates MySQL's error codes (1062 duplicate, 1451 still referenced, 1452 unknown foreign key) into HTTP errors.
   - `BOOK_SELECT` is the `SELECT ... JOIN` shared by every endpoint that returns books, and `to_book()` turns one row into a `Book`.
   - The `503` handler: if MySQL is not running, every request answers `503` with a message that tells you what to do.

2. **Fill in the blanks (`_____`) in `app.py`:**

   ```python
   # integrity_error: a duplicate value -> which status code?
   return HTTPException(status_code=_____, detail=...)

   # get_book_or_404: the placeholder for the id (never paste values into the SQL)
   cur.execute(BOOK_SELECT + " WHERE b.id = _____", (book_id,))

   # POST /books: the id MySQL generated, saving, and where the new book lives
   book_id = cur._____
   conn._____()
   response.headers["_____"] = ...

   # PATCH and DELETE: the decorators and the 204
   @app._____("/books/{book_id}")
   @app._____("/books/{book_id}", status_code=_____)
   if cur._____ == 0:              # how many rows did the DELETE remove?
   return Response(status_code=_____)

   # GET /books: the biggest page, and one page only
   limit: Annotated[int, Query(ge=1, le=_____)] = 20
   "... ORDER BY b.id LIMIT _____ OFFSET _____"
   ```

   The comments next to each blank give you a hint. The full solution is in `example/example06b.py` (try first!).

3. **Run the application** with `fastapi dev app.py` and test it (next section).

4. **Read `POST /authors`** (already written): it is the transaction of the "Transactions" box below.

## Test the API

`-i` shows the status line and the headers. These commands assume a **fresh database** (see "Reset the data"); with other data the ids can differ.

> **Windows:** in PowerShell use `curl.exe` (in Windows PowerShell 5.1 `curl` is an alias of `Invoke-WebRequest`). Even with `curl.exe`, PowerShell 5.1 removes the inner quotes of `-d '{...}'`, so the JSON arrives broken. Use the ready-to-run files instead: `example/commands_cmd.txt` (CMD) and `example/commands_powershell.txt` (PowerShell, with `Invoke-WebRequest`).
>
> Windows terminals do not always send accents (`á`, `ñ`) as UTF-8, and the API answers `400` "There was an error parsing the body". That is why the JSON bodies below have no accents. Accents work fine in Postman and in `/docs`.

- **List books (`200`):**
  ```bash
  curl -i "http://127.0.0.1:8000/books?limit=2"
  ```
  ```json
  {
    "data": [
      {"id": 1, "title": "Don Quijote de la Mancha", "isbn": "9788410079199", "year": 1605, "author": {"id": 1, "name": "Miguel de Cervantes"}, "created_at": "...", "updated_at": "..."},
      {"id": 2, "title": "Novelas ejemplares", "isbn": "9788410158382", "year": 1613, "author": {"id": 1, "name": "Miguel de Cervantes"}, "created_at": "...", "updated_at": "..."}
    ],
    "page": {"limit": 2, "offset": 0, "total": 150, "next": "http://127.0.0.1:8000/books?offset=2&limit=2", "prev": null}
  }
  ```

- **Last page (`next` is `null`) and a page that is too big (`422`):**
  ```bash
  curl -i "http://127.0.0.1:8000/books?offset=145&limit=5"
  curl -i "http://127.0.0.1:8000/books?limit=500"
  ```

- **Filters (`200`):** García Márquez's books whose title contains "soledad".
  ```bash
  curl -i "http://127.0.0.1:8000/books?author_id=2&q=soledad"
  ```

- **Get one book (`200`, or `404` if it does not exist):**
  ```bash
  curl -i http://127.0.0.1:8000/books/1
  curl -i http://127.0.0.1:8000/books/999
  ```

- **Create a book (`201` + `Location`):** MySQL generates the id and the timestamps.
  ```bash
  curl -i -X POST http://127.0.0.1:8000/books -H "Content-Type: application/json" -d '{"title": "El maestro de esgrima", "isbn": "9788490000014", "year": 1988, "author_id": 7}'
  ```
  ```
  HTTP/1.1 201 Created
  location: http://127.0.0.1:8000/books/151

  {"id": 151, "title": "El maestro de esgrima", "isbn": "9788490000014", "year": 1988, "author": {"id": 7, "name": "Arturo Pérez-Reverte"}, "created_at": "...", "updated_at": "..."}
  ```
  Refresh the `books` table in Adminer: the row is there.

- **Duplicate ISBN (`409`):** the ISBN of Don Quijote. MySQL refuses it because the column is `UNIQUE`.
  ```bash
  curl -i -X POST http://127.0.0.1:8000/books -H "Content-Type: application/json" -d '{"title": "Copy", "isbn": "9788410079199", "author_id": 1}'
  ```
  ```json
  {"type": "about:blank", "title": "Conflict", "status": 409, "detail": "'9788410079199' already exists and must be unique.", "instance": "/books"}
  ```

- **Unknown author (`422`):** the foreign key does not let a book point to author 999.
  ```bash
  curl -i -X POST http://127.0.0.1:8000/books -H "Content-Type: application/json" -d '{"title": "Orphan", "author_id": 999}'
  ```

- **Replace with PUT (`200`), then change only the year with PATCH (`200`):**
  ```bash
  curl -i -X PUT http://127.0.0.1:8000/books/151 -H "Content-Type: application/json" -d '{"title": "El maestro de esgrima (revised)", "isbn": "9788490000014", "year": 1988, "author_id": 7}'
  curl -i -X PATCH http://127.0.0.1:8000/books/151 -H "Content-Type: application/json" -d '{"year": 2000}'
  ```
  Look at `updated_at`: MySQL changed it by itself (`ON UPDATE CURRENT_TIMESTAMP`).

- **Empty PATCH (`422`):**
  ```bash
  curl -i -X PATCH http://127.0.0.1:8000/books/151 -H "Content-Type: application/json" -d '{}'
  ```

- **Delete (`204`, empty body), then get it again (`404`):**
  ```bash
  curl -i -X DELETE http://127.0.0.1:8000/books/151
  curl -i http://127.0.0.1:8000/books/151
  ```

- **Authors (`200`):**
  ```bash
  curl -i "http://127.0.0.1:8000/authors?q=garcia"
  curl -i http://127.0.0.1:8000/authors/2
  ```

- **Delete an author who still has books (`409`), and one who has none (`204`):**
  ```bash
  curl -i -X DELETE http://127.0.0.1:8000/authors/1
  curl -i -X DELETE http://127.0.0.1:8000/authors/22
  ```
  ```json
  {"type": "about:blank", "title": "Conflict", "status": 409, "detail": "Author 1 still has books. Delete or move them first.", "instance": "/authors/1"}
  ```
  Your Python code never checks this: the foreign key protects the data even if the code forgets.

- **The transaction: all or nothing.** Create an author together with two books. The second ISBN is Don Quijote's again, so it fails (`409`)...
  ```bash
  curl -i -X POST http://127.0.0.1:8000/authors -H "Content-Type: application/json" -d '{"name": "Rosa Montero", "country": "Spain", "birth_year": 1951, "books": [{"title": "La loca de la casa", "isbn": "9788490000021", "year": 2003}, {"title": "Copy", "isbn": "9788410079199"}]}'
  ```
  ...and **nothing** was saved: not the author, not the first book.
  ```bash
  curl -i "http://127.0.0.1:8000/authors?q=montero"
  ```
  ```json
  {"data": []}
  ```
  Now with two valid books (`201`):
  ```bash
  curl -i -X POST http://127.0.0.1:8000/authors -H "Content-Type: application/json" -d '{"name": "Rosa Montero", "country": "Spain", "birth_year": 1951, "books": [{"title": "La loca de la casa", "isbn": "9788490000021", "year": 2003}, {"title": "Historia del rey transparente", "isbn": "9788490000038", "year": 2005}]}'
  ```
  Look at the new id: it is `24`, not `23`. The failed attempt used `23`, and a rollback does not give `AUTO_INCREMENT` numbers back. Ids are identifiers, not counters.

- **The data stays:** stop `fastapi dev` (`Ctrl+C`), start it again and ask for Rosa Montero: she is still there. Compare this with exercises 04-06.
  ```bash
  curl -i "http://127.0.0.1:8000/authors?q=montero"
  ```

## SQL injection: always `%s`

Never build SQL by pasting the user's text into the string:

```python
# WRONG: q becomes part of the SQL
cur.execute(f"SELECT * FROM books WHERE title LIKE '%{q}%'")
```

With `q = "' OR '1'='1"` the query changes meaning, and with worse text an attacker can read or delete other tables. With a placeholder, PyMySQL sends the text **as a value**, so it can never become SQL:

```python
# RIGHT
cur.execute("SELECT * FROM books WHERE title LIKE %s", (f"%{q}%",))
```

Try `curl -i "http://127.0.0.1:8000/books?q=%27%20OR%20%271%27=%271"`: you get an empty list, not the whole table. In `PATCH`, the column **names** of the `UPDATE` come from our own model (never from the client) and the values still travel as `%s`.

## `commit()` and transactions

`db()` opens the connection with `autocommit` off, so every `INSERT`, `UPDATE` or `DELETE` is **pending** until `conn.commit()`. If the request fails before that, the connection is rolled back and closed, and the database stays as it was.

A **transaction** is a group of statements that is saved **all or nothing**. `POST /authors` runs one `INSERT` for the author plus one per book; it commits only if all of them worked, and calls `conn.rollback()` if any of them fails. Without it, a failed book would leave half an author in the database.

## Reset the data

- `docker compose down` stops the containers and **keeps** the data (it lives in the `library-data` volume).
- `docker compose down -v` also deletes the volume. On the next `docker compose up -d --wait`, `init.sql` runs again and you get the original 22 authors and 150 books.
- Changing `init.sql` does nothing until you reset with `-v`: Docker only runs it on an empty volume.

## Troubleshooting

- **`503 Service Unavailable` "Cannot connect to MySQL"**: Docker is not running, or MySQL is still starting. Run `docker compose up -d --wait` in this folder (and `docker compose ps` to see the state). The API does not need a restart.
- **`Ports are not available` or `port is already allocated` on 3306**: you already have a MySQL on your computer. Set `MYSQL_PORT=3307` in `.env` and run `docker compose up -d --wait` again; the API reads the same `.env`. The same for Adminer on 8080: change `ADMINER_PORT`.
- **`503` "refused the connection: Access denied"**: the user or password of `.env` do not match the database. If you changed them after the first start, the volume still has the old ones: `docker compose down -v` and start again.
- **`500 Internal Server Error`**: a blank is still there or a SQL string is wrong. Look at the terminal running `fastapi dev`: `TypeError: not all arguments converted during string formatting` means a `%s` placeholder is missing (a `_____` is still in the SQL); `You have an error in your SQL syntax` comes from MySQL.
- **pip fails with a long path error on Windows**: copy the repo to a short folder such as `C:\edem` (see the main README).

## Expected Results

- `GET /books` returns 20 books per page with `total`, `next` and `prev`; `?limit=500` is a `422`.
- `POST /books` returns `201` with `Location`, and the new row appears in Adminer.
- A duplicate ISBN is a `409`, an unknown `author_id` is a `422`, deleting an author with books is a `409`; every error is `application/problem+json`.
- `PATCH` with one field changes only that field; `DELETE` returns `204` with no body.
- A failed `POST /authors` leaves nothing behind.
- The data survives a restart of the API; `docker compose down -v` brings back the original data.

## Stretch Goals

1. **Cursor pagination in SQL:** add `?cursor=` to `GET /books` as in exercise 06. Hint: `WHERE b.id > %s ORDER BY b.id LIMIT %s` (no `OFFSET`, and it stays fast with millions of rows).
2. **Loans, with a transaction:** add a `loans` table (`book_id`, `borrower`, `loaned_at`, `returned_at`) and `POST /books/{id}/loan`. In one transaction, check that the book has no open loan and insert the loan; answer `409` if it is already on loan.
3. **An ORM:** rewrite `/books` with [SQLModel](https://sqlmodel.tiangolo.com/) (from the author of FastAPI). Compare: which code disappears, and which SQL can you no longer see?

## Additional Resources

- [PyMySQL documentation](https://pymysql.readthedocs.io/)
- [MySQL 8.4: CREATE TABLE and foreign keys](https://dev.mysql.com/doc/refman/8.4/en/create-table-foreign-keys.html)
- [Docker Hub: the official MySQL image](https://hub.docker.com/_/mysql)
- [OWASP: SQL Injection](https://owasp.org/www-community/attacks/SQL_Injection)
- [FastAPI: SQL databases](https://fastapi.tiangolo.com/tutorial/sql-databases/)
