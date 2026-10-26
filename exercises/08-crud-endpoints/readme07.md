# Exercise 8: Creating CRUD Endpoints (Notes API)

## Objective
Implement full CRUD (Create, Read, Update, Delete) for one resource, `/notes`, in a REST API using Python and Flask, with the right status codes, headers and error format.

## Description
In exercise 03 you built `GET /notes` and `POST /notes`. Here you complete the Notes API: read one note, replace it (`PUT`), update part of it (`PATCH`) and delete it (`DELETE`). There is **no authentication** in this exercise (auth comes later in the course): the focus is on HTTP methods, status codes, headers and validation. Complete the blanks (`_____`) in `app.py`.

## Quick Start

```bash
cd exercises/08-crud-endpoints
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
python app.py
```

The API runs at `http://127.0.0.1:5000` and starts with 3 seed notes (ids 1, 2, 3), so `GET /notes` is not empty.

## Requirements
1. **Dependencies:**
   - Only `Flask` (see `requirements.txt`).

2. **API Structure:**

   | Method | URI | What it does | Success |
   |--------|-----|--------------|---------|
   | `GET` | `/notes?limit=10` | List notes, newest first | `200` |
   | `POST` | `/notes` | Create a note | `201` + `Location` header |
   | `GET` | `/notes/<id>` | Get one note | `200` (`404` if missing) |
   | `PUT` | `/notes/<id>` | Replace the whole note | `200` |
   | `PATCH` | `/notes/<id>` | Update only the fields sent | `200` |
   | `DELETE` | `/notes/<id>` | Delete the note | `204`, no body |

   - Plural nouns, no verbs in the URIs: the **method** says what happens (`DELETE /notes/1`, not `/deleteNote?id=1`).
   - A note looks like this. `id`, `created_at` and `updated_at` are set by the server (ISO 8601, UTC):

     ```json
     {"id": 1, "title": "Welcome", "content": "This is your Notes API.", "created_at": "2026-10-26T09:30:00Z", "updated_at": "2026-10-26T09:30:00Z"}
     ```

   - `GET /notes` accepts `?limit=` (default `20`, maximum `100`; bigger values are clamped to `100`). Full pagination (offset and cursor) is exercise 09.

3. **CRUD Implementation:**
   - `title` is required and must be a non-empty string. `content` must be a string (optional on `POST`, where it defaults to `""`).
   - `PUT` sends the **complete** resource: `title` and `content` are both required.
   - `PATCH` sends only what changes: at least one of `title` / `content`.
   - Every error uses the same format, RFC 9457 *problem details* (see below).

4. **Testing:**
   - Use Postman or `curl` to test each operation, including the error cases.

## Suggested Steps

1. **Read `app.py`:**
   - The `problem()` helper builds every error response (you met it in exercise 03).
   - `read_json_object()` checks the `Content-Type` and parses the body; `validate_note()` returns the list of field errors.
   - `GET /notes` and `GET /notes/<id>` are already implemented. Notice how the same URL `/notes/<id>` does different things depending on the method.

2. **Fill in the blanks (`_____`) in `exercises/08-crud-endpoints/app.py`:**

   ```python
   # Status codes for errors: 422 (valid JSON, invalid data), 415 (not JSON), 400 (malformed JSON)
   return problem(_____, 'Unprocessable Content', ...)

   # POST: "created" + where the new note lives
   return jsonify(note), _____, {'Location': _____}

   # PUT vs PATCH: the method, and which fields are required
   @app.route('/notes/<int:note_id>', methods=['_____'])  # TODO: Set the HTTP method that REPLACES a resource
   errors = validate_note(data, required=_____)

   # DELETE: success, nothing to send back
   return '', _____
   ```

   The comments next to each blank give you a hint. The full solution is in `example/example08.py` (try first!).

3. **Run the Application:**

   ```bash
   python app.py
   ```

4. **Test the API:**

   Use Postman or `curl`. `-i` shows the status line and the headers.

   > **Windows:** in PowerShell use `curl.exe` (in Windows PowerShell 5.1 `curl` is an alias of `Invoke-WebRequest`). Even with `curl.exe`, PowerShell 5.1 removes the inner quotes of `-d '{...}'`, so the JSON arrives broken. Use the ready-to-run files instead: `example/commands_cmd.txt` (CMD) and `example/commands_powershell.txt` (PowerShell, with `Invoke-WebRequest`).

   - **List notes (`200`):**
     ```bash
     curl -i "http://127.0.0.1:5000/notes?limit=10"
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

   - **Create a note (`201` + `Location`):**
     ```bash
     curl -i -X POST http://127.0.0.1:5000/notes -H "Content-Type: application/json" -d '{"title": "My first note", "content": "Hello"}'
     ```
     ```
     HTTP/1.1 201 CREATED
     Content-Type: application/json
     Location: http://127.0.0.1:5000/notes/4

     {"id": 4, "title": "My first note", "content": "Hello", "created_at": "2026-10-26T09:30:00Z", "updated_at": "2026-10-26T09:30:00Z"}
     ```

   - **Get one note (`200`, or `404` if it does not exist):**
     ```bash
     curl -i http://127.0.0.1:5000/notes/4
     curl -i http://127.0.0.1:5000/notes/999
     ```

   - **Replace with PUT (`200`):** all fields are sent.
     ```bash
     curl -i -X PUT http://127.0.0.1:5000/notes/4 -H "Content-Type: application/json" -d '{"title": "Replaced title", "content": "Replaced content"}'
     ```

   - **PUT with a missing field (`422`):** PUT replaces the whole note, so `content` is required.
     ```bash
     curl -i -X PUT http://127.0.0.1:5000/notes/4 -H "Content-Type: application/json" -d '{"title": "Only the title"}'
     ```

   - **Partial update with PATCH (`200`):** only `content` changes, the title stays the same.
     ```bash
     curl -i -X PATCH http://127.0.0.1:5000/notes/4 -H "Content-Type: application/json" -d '{"content": "Only the content changed"}'
     ```

   - **Delete (`204`, empty body), then get it again (`404`):**
     ```bash
     curl -i -X DELETE http://127.0.0.1:5000/notes/4
     curl -i http://127.0.0.1:5000/notes/4
     ```

   - **Wrong Content-Type (`415`):**
     ```bash
     curl -i -X POST http://127.0.0.1:5000/notes -d 'title=bad'
     ```

   - **Malformed JSON (`400`):**
     ```bash
     curl -i -X POST http://127.0.0.1:5000/notes -H "Content-Type: application/json" -d '{"title": '
     ```

   - **Valid JSON, invalid data (`422`):** empty title, `content` is a number.
     ```bash
     curl -i -X POST http://127.0.0.1:5000/notes -H "Content-Type: application/json" -d '{"title": "", "content": 42}'
     ```
     ```
     HTTP/1.1 422 UNPROCESSABLE ENTITY
     Content-Type: application/problem+json

     {
       "type": "about:blank",
       "title": "Unprocessable Content",
       "status": 422,
       "detail": "The note has invalid or missing fields.",
       "errors": [
         {"pointer": "#/title", "detail": "title must be a non-empty string"},
         {"pointer": "#/content", "detail": "content must be a string"}
       ]
     }
     ```

   - **Method not allowed (`405`, with an `Allow` header):**
     ```bash
     curl -i -X DELETE http://127.0.0.1:5000/notes
     ```

   - **Invalid limit (`400`):**
     ```bash
     curl -i "http://127.0.0.1:5000/notes?limit=0"
     ```

## Expected Results

- The API lets you create, read, replace, partially update and delete notes.
- `POST` returns `201` with a `Location` header; `DELETE` returns `204` with no body.
- `PUT` without all the fields returns `422`; `PATCH` with one field only changes that field.
- Every error is `application/problem+json` with `type`, `title`, `status` and `detail`.

## Understanding HTTP Status Codes

- **200 OK**: request succeeded (`GET`, `PUT`, `PATCH`)
- **201 Created**: new resource created (`POST`). The `Location` header says where it lives.
- **204 No Content**: success with no body (`DELETE`)
- **400 Bad Request**: the request itself is broken: malformed JSON, `?limit=abc`
- **404 Not Found**: the resource does not exist
- **405 Method Not Allowed**: the URL exists but not with that method (the `Allow` header lists the valid ones)
- **415 Unsupported Media Type**: the body is not `application/json`
- **422 Unprocessable Content**: valid JSON, but invalid data: missing fields, wrong types, empty title
- **409 Conflict**: not used here (two notes may share a title). You would use it for a real conflict, e.g. a duplicate value of a field that must be unique.
- **500 Internal Server Error**: server-side error

### 400 vs 422

`{"title": ` cannot even be parsed: **400**. `{"title": ""}` is perfectly valid JSON, but the data breaks the rules: **422**. A JSON body that is not an object (`[1, 2]`) is also **422**.

### HTTP Methods and Their Purpose

- **POST**: create a new resource
- **GET**: retrieve one or many resources
- **PUT**: replace the **whole** resource (send every field)
- **PATCH**: change **some** fields (send only what changes)
- **DELETE**: remove a resource

### Errors: RFC 9457 Problem Details

All errors share one shape and the `Content-Type: application/problem+json`. They are built by one small helper, `problem(status, title, detail, **extra)`, used everywhere, including the `404`/`405` handlers. Validation errors add an `errors` extension with one entry per field (`pointer` is a JSON Pointer to the field):

```json
{"type": "about:blank", "title": "Not Found", "status": 404, "detail": "Note 999 does not exist."}
```

## Additional Resources

- [Flask Documentation](https://flask.palletsprojects.com/)
- [RFC 9457: Problem Details for HTTP APIs](https://www.rfc-editor.org/rfc/rfc9457)
- [RFC 9110: HTTP Semantics (methods and status codes)](https://www.rfc-editor.org/rfc/rfc9110)
- [HTTP Status Codes](https://developer.mozilla.org/en-US/docs/Web/HTTP/Status)

## Notes

- This exercise uses in-memory storage, so all data (and your new notes) is lost when the application restarts.
- Debug mode is off by default. To turn it on: `FLASK_DEBUG=1 python app.py` (PowerShell: `$env:FLASK_DEBUG="1"; python app.py`).
- The code includes blanks (`_____`) for you to complete: focus on **why** each status code and header is the right one.
