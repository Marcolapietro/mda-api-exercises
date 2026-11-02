# Exercise 4: API Fundamentals (Notes API)

## Introduction

This exercise introduces core HTTP + JSON API fundamentals using a small Notes API built with FastAPI. It comes right after 03 (FastAPI intro) and before 05 (CRUD) and focuses on clean request/response design and basic validation, with no authentication yet. The same Notes API grows into full CRUD in exercise 05 and gets pagination in exercise 06.

## Learning Objectives

1. Model resources with plural nouns (`/notes`, `/notes/{id}`), no verbs in the URIs
2. Use HTTP methods correctly (GET/POST) and return proper status codes (`201` + `Location` on create)
3. Let FastAPI validate the request with Pydantic models and understand the `422` it answers
4. Return every error in one standard format: RFC 9457 problem details
5. Practice testing with Postman and curl

## Endpoints

- `GET /health`
  - Returns basic service information
  - Response: `200` with `{ "status": "ok" }`

- `GET /notes`
  - Returns a list of notes (in-memory)
  - Response: `200` with list `[ { id, title, content } ]`

- `POST /notes`
  - Creates a new note
  - Body (JSON): `{ "title": str, "content": str }`; `title` must have at least one character, `content` is optional and defaults to `""`
  - Response: `201` with the created note and a `Location` header pointing to it (e.g. `Location: http://127.0.0.1:8000/notes/1`)
  - Errors: `422` for anything FastAPI cannot accept as a valid note (see below)

- `GET /notes/{id}`
  - Returns a single note by id
  - Response: `200` on success, `404` if not found

## Requirements

- Use an in-memory store (Python dict), no database
- Describe the data with Pydantic models: `NoteCreate` (what the client sends) and `Note` (what the API returns)
- Every error is RFC 9457 *problem details*, with `Content-Type: application/problem+json`, built by one helper, `problem(request, status, title, detail, **extra)`. `instance` is the path of the request that failed:

  ```json
  {"type": "about:blank", "title": "Not Found", "status": 404, "detail": "Note 99 does not exist.", "instance": "/notes/99"}
  ```

  Validation errors (`422`) add an `errors` extension with the list that Pydantic produces, one entry per problem (`loc` says where the problem is):

  ```json
  {
    "type": "about:blank",
    "title": "Unprocessable Content",
    "status": 422,
    "detail": "Request body or parameters are invalid.",
    "instance": "/notes",
    "errors": [
      {"type": "missing", "loc": ["body", "title"], "msg": "Field required", "input": {"content": "Hello"}}
    ]
  }
  ```

- Two exception handlers produce these responses: one for `HTTPException` (your `404`s, and also the `404` and `405` that the router raises by itself) and one for `RequestValidationError` (the `422`s)

## How FastAPI answers invalid input

In HTTP, `400` means "I could not understand the request" and `415` means "I do not accept this media type". We do not write those checks by hand here. FastAPI validates the *shape* and the *content* of the request together, before your function runs, and answers `422 Unprocessable Content` with the details of what is wrong. That covers a `Content-Type` that is not JSON, malformed JSON, a missing field, a field of the wrong type and an empty `title`. Your code only declares the model; if the function runs, the data is valid. `400` and `415` still exist in HTTP, we just do not fabricate them here.

## Starter Files

- `app.py` – Starter with TODOs and blanks (`_____`) for you to fill
- `example/example04.py` – Complete reference solution (for after you try)
- `requirements.txt` – Minimal dependencies

## Getting Started

```bash
# (Optional) Create and activate a virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run the app (fill the blanks from top to bottom; the app starts once the decorators and the `status_code=` of `POST /notes` are complete)
fastapi dev app.py
```

Open your browser: http://127.0.0.1:8000/health, and http://127.0.0.1:8000/docs for the automatic documentation.

## Response models and status codes

As in 03, the return type annotation does the work: `-> Note` tells FastAPI the shape of the response. It filters the output to the fields of `Note`, validates it and documents it in `/docs`; `-> list[Note]` does the same for a list. (If a function returns something that is not the type you want to document, pass `response_model=` to the decorator instead.)

A successful `GET` answers `200` by default. For other cases you set the status in the decorator: `@app.post("/notes", status_code=201)`. We write the number, as the slides do; `fastapi.status` has named constants for the same codes (`status.HTTP_201_CREATED`) if you prefer them.

To add a header to the response, declare a parameter of type `Response`; FastAPI gives you the response it is about to send, and you set `response.headers["Name"] = value`. To build the URL of another route from its function name, use `request.url_for("get_note", note_id=1)`.

## Tasks (fill the blanks in app.py)

1. Problem details
   - Set the media type of the `problem()` helper: `application/problem+json`
   - Answer `422` in the validation handler
2. Routes and methods
   - Choose the decorator (`get` or `post`) of each route
3. Resource creation
   - Answer `201` with the created note and the `Location` header
4. Not found
   - Answer `404` when the note does not exist

## Testing (curl)

```bash
# Health
curl -i http://127.0.0.1:8000/health

# Create note (success) -> 201 + Location: http://127.0.0.1:8000/notes/1
curl -i -X POST http://127.0.0.1:8000/notes \
  -H "Content-Type: application/json" \
  -d '{"title": "First note", "content": "Hello world"}'

# Create note (malformed JSON) -> 422 problem+json
curl -i -X POST http://127.0.0.1:8000/notes -H "Content-Type: application/json" -d '{"title": '

# Create note (missing title) -> 422 problem+json with an "errors" list
curl -i -X POST http://127.0.0.1:8000/notes -H "Content-Type: application/json" -d '{"content": "No title"}'

# List notes -> 200
curl -i http://127.0.0.1:8000/notes

# Get note by id -> 200, or 404 if it does not exist
curl -i http://127.0.0.1:8000/notes/1
curl -i http://127.0.0.1:8000/notes/99

# Method not allowed -> 405
curl -i -X DELETE http://127.0.0.1:8000/notes
```

Note: the `Allow` header is incomplete here (`GET` only) because FastAPI registers `GET /notes` and `POST /notes` as two separate routes.

> **Windows:** in PowerShell use `curl.exe` (in PowerShell 5.1 `curl` is an alias of `Invoke-WebRequest`). Windows PowerShell 5.1 also removes the inner quotes of `-d '{...}'`, so the JSON arrives broken: run the JSON examples from CMD, or use `Invoke-RestMethod -Method Post -Uri http://127.0.0.1:8000/notes -ContentType "application/json" -Body (@{title="First note"; content="Hello world"} | ConvertTo-Json)`. In CMD, single quotes don't work: use double quotes and escape the inner ones, e.g. `-d "{\"title\": \"First note\", \"content\": \"Hello world\"}"`.

## Acceptance Criteria

- Correct status codes (`200`, `201`, `404`, `405`, `422`)
- `POST /notes` returns `201` with the created note and a `Location` header
- Every error is `application/problem+json` with `type`, `title`, `status` and `detail`
- Invalid input (malformed JSON, missing or empty `title`, a body that is not JSON) returns `422`, never `500`
- No authentication used

## Stretch Goals

- Add `PUT`, `PATCH` and `DELETE` (that is exactly exercise 05)
- Add `created_at`/`updated_at` timestamps
- Add pagination (`?offset`/`limit` or a cursor) like exercise 06
- Add simple CORS for browser testing

Good luck building a clean, well-structured API!
