# Exercise 5: Creating CRUD Endpoints (Notes API)

## Objective
Implement full CRUD (Create, Read, Update, Delete) for one resource, `/notes`, in a REST API using Python and FastAPI, with the right status codes, headers and error format.

## Description
In exercise 04 you built `GET /notes` and `POST /notes`. Here you complete the Notes API: replace a note (`PUT`), update part of it (`PATCH`) and delete it (`DELETE`). There is **no authentication** in this exercise (auth comes later in the course): the focus is on HTTP methods, status codes, headers and validation. Complete the blanks (`_____`) in `app.py`.

## Quick Start

```bash
cd exercises/05-crud-endpoints
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
# Fill the blanks from top to bottom; the app starts once the PUT, PATCH and DELETE decorators (with the `status_code=` of DELETE) and the `le=` of the limit are complete
fastapi dev app.py
```

The API runs at `http://127.0.0.1:8000` (automatic documentation at `/docs`) and starts with 3 seed notes (ids 1, 2, 3), so `GET /notes` is not empty.

## Requirements
1. **Dependencies:**
   - Only `fastapi[standard]` (see `requirements.txt`).

2. **API Structure:**

   | Method | URI | What it does | Success |
   |--------|-----|--------------|---------|
   | `GET` | `/notes?limit=10` | List notes, newest first | `200` |
   | `POST` | `/notes` | Create a note | `201` + `Location` header |
   | `GET` | `/notes/{id}` | Get one note | `200` (`404` if missing) |
   | `PUT` | `/notes/{id}` | Replace the whole note | `200` |
   | `PATCH` | `/notes/{id}` | Update only the fields sent | `200` |
   | `DELETE` | `/notes/{id}` | Delete the note | `204`, no body |

   - Plural nouns, no verbs in the URIs: the **method** says what happens (`DELETE /notes/1`, not `/deleteNote?id=1`).
   - A note looks like this. `id`, `created_at` and `updated_at` are set by the server (ISO 8601, UTC):

     ```json
     {"id": 1, "title": "Welcome", "content": "This is your Notes API.", "created_at": "2026-10-26T09:30:00Z", "updated_at": "2026-10-26T09:30:00Z"}
     ```

   - `GET /notes` accepts `?limit=` (default `20`, between `1` and `100`). A `limit` above `100` is rejected with `422`, not clamped. Full pagination (offset and cursor) is exercise 06.

3. **CRUD Implementation:**
   - Three Pydantic models describe the data: `NoteCreate` (body of `POST` and `PUT`), `NoteUpdate` (body of `PATCH`) and `Note` (what the API returns).
   - `title` is required in `NoteCreate` and must have at least one character. `content` is a string (optional, it defaults to `""`).
   - `PUT` sends the **complete** resource, so it uses `NoteCreate`: a missing `title` is a `422`.
   - `PATCH` sends only what changes. In `NoteUpdate` every field is optional, and `model_dump(exclude_unset=True)` gives you just the fields the client sent. An empty body (`{}`) changes nothing and is a `422`.
   - Every error uses the same format, RFC 9457 *problem details* (see below).

4. **Testing:**
   - Use Postman or `curl` to test each operation, including the error cases.

## Suggested Steps

1. **Read `app.py`:**
   - It starts from the same code as exercise 04: the models, the `problem()` helper and the two exception handlers.
   - `get_or_404()` returns a note or raises the `404`; the item routes share it.
   - `GET /notes/{id}` is already implemented, and `POST /notes` only misses the name of the header that says where the new note lives. Notice how the same URL `/notes/{id}` does different things depending on the method.

2. **Fill in the blanks (`_____`) in `exercises/05-crud-endpoints/app.py`:**

   ```python
   # Problem details and validation handler: the media type and the status code
   return JSONResponse(body, status_code=status, media_type="_____")
   return problem(request, _____, "Unprocessable Content", ...)

   # POST: the header that says where the new note lives
   response.headers["_____"] = str(request.url_for("get_note", note_id=note.id))

   # PUT vs PATCH vs DELETE: the decorator is named after the HTTP method
   @app._____("/notes/{note_id}")  # which method REPLACES a resource?

   # PATCH: only the fields the client sent
   changes = data.model_dump(_____=True, exclude_none=True)

   # DELETE: success, nothing to send back (in the decorator and in the Response)
   @app._____("/notes/{note_id}", status_code=_____)
   return Response(status_code=_____)

   # GET /notes: the biggest page size
   limit: Annotated[int, Query(ge=1, le=_____)] = 20
   ```

   The comments next to each blank give you a hint. The full solution is in `example/example05.py` (try first!).

3. **Run the Application:**

   ```bash
   fastapi dev app.py
   ```

4. **Test the API:**

   Use Postman, `curl` or the `/docs` page. `-i` shows the status line and the headers.

   > **Windows:** in PowerShell use `curl.exe` (in Windows PowerShell 5.1 `curl` is an alias of `Invoke-WebRequest`). Even with `curl.exe`, PowerShell 5.1 removes the inner quotes of `-d '{...}'`, so the JSON arrives broken. Use the ready-to-run files instead: `example/commands_cmd.txt` (CMD) and `example/commands_powershell.txt` (PowerShell, with `Invoke-WebRequest`).

   - **List notes (`200`):**
     ```bash
     curl -i "http://127.0.0.1:8000/notes?limit=10"
     ```
     ```json
     {
       "data": [
         {"id": 3, "title": "API Management", "content": "Status codes, Location header and RFC 9457 errors", "created_at": "...", "updated_at": "..."},
         {"id": 2, "title": "Shopping list", "content": "Milk, eggs, coffee", "created_at": "...", "updated_at": "..."},
         {"id": 1, "title": "Welcome", "content": "This is your Notes API.", "created_at": "...", "updated_at": "..."}
       ],
       "page": {"limit": 10, "total": 3}
     }
     ```

   - **`limit` out of range (`422`):** values above `100` (or below `1`, or not a number) are rejected, not clamped.
     ```bash
     curl -i "http://127.0.0.1:8000/notes?limit=500"
     ```

   - **Create a note (`201` + `Location`):**
     ```bash
     curl -i -X POST http://127.0.0.1:8000/notes -H "Content-Type: application/json" -d '{"title": "My first note", "content": "Hello"}'
     ```
     ```
     HTTP/1.1 201 Created
     content-type: application/json
     location: http://127.0.0.1:8000/notes/4

     {"id": 4, "title": "My first note", "content": "Hello", "created_at": "2026-10-26T09:30:00Z", "updated_at": "2026-10-26T09:30:00Z"}
     ```

   - **Get one note (`200`, or `404` if it does not exist):**
     ```bash
     curl -i http://127.0.0.1:8000/notes/4
     curl -i http://127.0.0.1:8000/notes/999
     ```

   - **Replace with PUT (`200`):** all fields are sent.
     ```bash
     curl -i -X PUT http://127.0.0.1:8000/notes/4 -H "Content-Type: application/json" -d '{"title": "Replaced title", "content": "Replaced content"}'
     ```

   - **PUT with a missing field (`422`):** PUT replaces the whole note, so `title` is required.
     ```bash
     curl -i -X PUT http://127.0.0.1:8000/notes/4 -H "Content-Type: application/json" -d '{"content": "No title"}'
     ```

   - **Partial update with PATCH (`200`):** only `content` changes, the title stays the same.
     ```bash
     curl -i -X PATCH http://127.0.0.1:8000/notes/4 -H "Content-Type: application/json" -d '{"content": "Only the content changed"}'
     ```

   - **Delete (`204`, empty body), then get it again (`404`):**
     ```bash
     curl -i -X DELETE http://127.0.0.1:8000/notes/4
     curl -i http://127.0.0.1:8000/notes/4
     ```

   - **Wrong Content-Type (`422`):**
     ```bash
     curl -i -X POST http://127.0.0.1:8000/notes -d 'title=bad'
     ```

   - **Malformed JSON (`422`):**
     ```bash
     curl -i -X POST http://127.0.0.1:8000/notes -H "Content-Type: application/json" -d '{"title": '
     ```

   - **Valid JSON, invalid data (`422`):** empty title, `content` is a number.
     ```bash
     curl -i -X POST http://127.0.0.1:8000/notes -H "Content-Type: application/json" -d '{"title": "", "content": 42}'
     ```
     ```
     HTTP/1.1 422 Unprocessable Content
     content-type: application/problem+json

     {
       "type": "about:blank",
       "title": "Unprocessable Content",
       "status": 422,
       "detail": "Request body or parameters are invalid.",
       "instance": "/notes",
       "errors": [
         {"type": "string_too_short", "loc": ["body", "title"], "msg": "String should have at least 1 character", ...},
         {"type": "string_type", "loc": ["body", "content"], "msg": "Input should be a valid string", ...}
       ]
     }
     ```

   - **Method not allowed (`405`):**
     ```bash
     curl -i -X DELETE http://127.0.0.1:8000/notes
     ```
     Note: the `Allow` header is incomplete here (`POST` only) because FastAPI registers `POST /notes` and `GET /notes` as two separate routes.

## Response models, `Response` and `Query`

Exercise 04 introduced `-> Note` and `status_code=201`. Two more pieces appear here.

**`204 No Content` means there is no body.** If a function simply returned `None`, FastAPI would send the JSON text `null` as the body, which a `204` must not have. So `DELETE` returns an empty response explicitly: `return Response(status_code=204)` (and the decorator says `status_code=204`, so `/docs` documents it).

**`Query` validates the query string.** `limit: Annotated[int, Query(ge=1, le=100)] = 20` reads like this: an integer, greater than or equal to 1, less than or equal to 100, and `20` if the client sends nothing. If the value is not an integer or is out of range, FastAPI answers `422` before your function runs. Exercise 06 goes deeper into `Query`.

## Expected Results

- The API lets you create, read, replace, partially update and delete notes.
- `POST` returns `201` with a `Location` header; `DELETE` returns `204` with no body.
- `PUT` without `title` returns `422`; `PATCH` with one field only changes that field.
- `?limit=500` returns `422`, it is not clamped to `100`.
- Every error is `application/problem+json` with `type`, `title`, `status`, `detail` and `instance`.

## Understanding HTTP Status Codes

- **200 OK**: request succeeded (`GET`, `PUT`, `PATCH`)
- **201 Created**: new resource created (`POST`). The `Location` header says where it lives.
- **204 No Content**: success with no body (`DELETE`)
- **404 Not Found**: the resource does not exist
- **405 Method Not Allowed**: the URL exists but not with that method
- **422 Unprocessable Content**: FastAPI could not accept the request: a body that is not JSON, malformed JSON, missing fields, wrong types, an empty title, a `limit` that is not a number or out of range
- **409 Conflict**: not used here (two notes may share a title). You would use it for a real conflict, e.g. a duplicate value of a field that must be unique.
- **500 Internal Server Error**: server-side error

`400` and `415` still exist in HTTP, but as in exercise 04 we do not write those checks by hand: FastAPI validates the shape and the content of the request together and answers `422` with the details.

### HTTP Methods and Their Purpose

- **POST**: create a new resource
- **GET**: retrieve one or many resources
- **PUT**: replace the **whole** resource (send every field)
- **PATCH**: change **some** fields (send only what changes)
- **DELETE**: remove a resource

### Errors: RFC 9457 Problem Details

All errors share one shape and the `Content-Type: application/problem+json`. They are built by one small helper, `problem(request, status, title, detail, **extra)`, used by the two exception handlers (the `HTTPException` one covers your `404`s and also the `404` and `405` raised by the router itself). Validation errors add an `errors` extension with the list that Pydantic produces; `loc` says where the problem is:

```json
{"type": "about:blank", "title": "Not Found", "status": 404, "detail": "Note 999 does not exist.", "instance": "/notes/999"}
```

## Additional Resources

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [RFC 9457: Problem Details for HTTP APIs](https://www.rfc-editor.org/rfc/rfc9457)
- [RFC 9110: HTTP Semantics (methods and status codes)](https://www.rfc-editor.org/rfc/rfc9110)
- [HTTP Status Codes](https://developer.mozilla.org/en-US/docs/Web/HTTP/Status)

## Notes

- This exercise uses in-memory storage, so all data (and your new notes) is lost when the application restarts. `fastapi dev` also reloads the app when you save `app.py`, which resets the data as well.
- The code includes blanks (`_____`) for you to complete: focus on **why** each status code and header is the right one.
