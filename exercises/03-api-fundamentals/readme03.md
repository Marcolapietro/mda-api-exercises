# Exercise 3: API Fundamentals (Notes API)

## Introduction

This exercise introduces core HTTP + JSON API fundamentals using a small Notes API built with Flask. It fits between 02 (Postman) and 04 (Basic Auth) and focuses on clean request/response design and basic validation — no authentication yet. The same Notes API grows into full CRUD in exercise 08 and gets pagination in exercise 09.

## Learning Objectives

1. Model resources with plural nouns (`/notes`, `/notes/<id>`), no verbs in the URIs
2. Use HTTP methods correctly (GET/POST) and return proper status codes (`201` + `Location` on create)
3. Validate `Content-Type` and JSON payloads, telling apart `400`, `415` and `422`
4. Return every error in one standard format: RFC 9457 problem details
5. Practice testing with Postman and curl

## Endpoints

- `GET /health`
  - Returns basic service information
  - Response: `200` with `{ status, service, version }`

- `GET /notes`
  - Returns a list of notes (in-memory)
  - Response: `200` with list `[ { id, title, content } ]`

- `POST /notes`
  - Creates a new note
  - Requires `Content-Type: application/json`
  - Body: `{ "title": str, "content": str }`
  - Response: `201` with the created note and a `Location` header pointing to it (e.g. `Location: http://127.0.0.1:5000/notes/1`)
  - Errors: `415` (not JSON), `400` (malformed JSON), `422` (valid JSON but invalid data)

- `GET /notes/<id>`
  - Returns a single note by id
  - Response: `200` on success, `404` if not found

## Requirements

- Use an in-memory store (Python dict) — no database
- Validate requests:
  - Reject non-JSON with `415` (`application/json; charset=utf-8` is still JSON)
  - Reject a body that is not valid JSON with `400`
  - Reject valid JSON with invalid data with `422`: missing fields, wrong types, empty strings, or a body that is not an object (e.g. `[1, 2]`)
- Every error is RFC 9457 *problem details*, with `Content-Type: application/problem+json`, built by one helper, `problem(status, title, detail, **extra)`:

  ```json
  {"type": "about:blank", "title": "Not Found", "status": 404, "detail": "Note 99 does not exist."}
  ```

  Validation errors (`422`) add an `errors` extension with one entry per field (`pointer` is a JSON Pointer to the field):

  ```json
  {
    "type": "about:blank",
    "title": "Unprocessable Content",
    "status": 422,
    "detail": "The note has invalid or missing fields.",
    "errors": [
      {"pointer": "#/title", "detail": "title is required and must be a non-empty string"}
    ]
  }
  ```

- Error handlers for `404` and `405` use the same helper (the `405` response also lists the valid methods in the `Allow` header)

## Starter Files

- `app.py` – Starter with TODOs and blanks (`_____`) for you to fill
- `example/example03.py` – Complete reference solution (for after you try)
- `requirements.txt` – Minimal dependencies

## Getting Started

```bash
# (Optional) Create and activate a virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\Activate.ps1

# Install dependencies
pip install -r requirements.txt

# Run the app
python app.py
```

Open your browser: http://127.0.0.1:5000/health

Debug mode is off by default. To turn it on: `FLASK_DEBUG=1 python app.py` (PowerShell: `$env:FLASK_DEBUG="1"; python app.py`).

## Tasks (fill the blanks in app.py)

1. Problem details
   - Set the media type of the `problem()` helper: `application/problem+json`
2. Routes and methods
   - Add HTTP methods for each route
3. Content-Type validation on `POST /notes`
   - Return `415` if not `application/json`
4. Input validation
   - Parse the body (`400` if it is not valid JSON)
   - Ensure `title` and `content` are present and non-empty strings
   - On error, return `422` with the `errors` list
5. Resource creation
   - Generate `id`, return `201` with the created note and the `Location` header (use `url_for`)

## Testing (curl)

```bash
# Health
curl -i http://127.0.0.1:5000/health

# Create note (success) -> 201 + Location: http://127.0.0.1:5000/notes/1
curl -i -X POST http://127.0.0.1:5000/notes \
  -H "Content-Type: application/json" \
  -d '{"title": "First note", "content": "Hello world"}'

# Create note (wrong content-type) -> 415
curl -i -X POST http://127.0.0.1:5000/notes -d 'title=bad'

# Create note (malformed JSON) -> 400
curl -i -X POST http://127.0.0.1:5000/notes -H "Content-Type: application/json" -d '{"title": '

# Create note (valid JSON, invalid data) -> 422 with an "errors" list
curl -i -X POST http://127.0.0.1:5000/notes -H "Content-Type: application/json" -d '{"title": "", "content": 42}'

# Create note (valid JSON that is not an object) -> 422
curl -i -X POST http://127.0.0.1:5000/notes -H "Content-Type: application/json" -d '[1, 2]'

# List notes -> 200
curl -i http://127.0.0.1:5000/notes

# Get note by id -> 200, or 404 if it does not exist
curl -i http://127.0.0.1:5000/notes/1
curl -i http://127.0.0.1:5000/notes/99

# Method not allowed -> 405 (look at the Allow header)
curl -i -X DELETE http://127.0.0.1:5000/notes
```

> **Windows:** in PowerShell use `curl.exe` (in PowerShell 5.1 `curl` is an alias of `Invoke-WebRequest`). Windows PowerShell 5.1 also removes the inner quotes of `-d '{...}'`, so the JSON arrives broken: run the JSON examples from CMD, or use `Invoke-RestMethod -Method Post -Uri http://127.0.0.1:5000/notes -ContentType "application/json" -Body (@{title="First note"; content="Hello world"} | ConvertTo-Json)`. In CMD, single quotes don't work: use double quotes and escape the inner ones, e.g. `-d "{\"title\": \"First note\", \"content\": \"Hello world\"}"`.

## Acceptance Criteria

- Correct status codes (`200`, `201`, `400`, `404`, `405`, `415`, `422`)
- `POST /notes` returns `201` with the created note and a `Location` header
- Every error is `application/problem+json` with `type`, `title`, `status` and `detail`
- A JSON body that is not an object returns `422`, never `500`
- No authentication used

## Stretch Goals

- Add `PUT`, `PATCH` and `DELETE` (that is exactly exercise 08)
- Add `created_at`/`updated_at` timestamps
- Add pagination (`?offset`/`limit` or a cursor) like exercise 09
- Add simple CORS for browser testing

Good luck building a clean, well-structured API!
