# FastAPI Migration Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Move every exercise with code (03 to 17) from Flask to FastAPI, one commit per exercise, without changing what each exercise teaches.

**Architecture:** Each exercise folder stays self-contained (one `app.py` starter with `_____` blanks, one `example/exampleNN.py` solution, `requirements.txt`, README EN and ES). The Flask solution is the behavioural reference: same routes, same JSON shapes, same status codes except where the design moves input validation to FastAPI's 422. A scratch pytest suite outside the repo pins the README and slide commands for each exercise and is rerun after every task.

**Tech Stack:** Python 3.12 to 3.14, `fastapi[standard]==0.162.0` (uvicorn 0.54.0, pydantic 2.14.1, starlette 1.10.0, fastapi-cli 0.0.32), `PyJWT==2.15.1`, `bcrypt==5.0.0`, `slowapi==0.1.10`, `Authlib==1.9.1`, `itsdangerous==2.2.0`, `httpx==0.28.1`, `mcp==2.3.0` (17 only).

**Spec:** `docs/superpowers/specs/2026-10-29-fastapi-migration-design.md`

## Global Constraints

- Branch `fastapi` (already exists, from `fix/security-and-broken-exercises`). Commit with `git -c commit.gpgsign=false commit -m "<one line>"`: no trailers, no GPG (the teacher's rule).
- Start command everywhere: `fastapi dev app.py`, base URL `http://127.0.0.1:8000`. No `if __name__ == "__main__"` block, no `uvicorn.run`, no `FLASK_DEBUG`.
- Pins in every `requirements.txt`: `fastapi[standard]==0.162.0` plus only what that exercise imports, at the versions above.
- Style: `Annotated[...]` for `Query`, `Path`, `Header`, `Depends`; return-type annotations for response models; plain `def` path operations except `async def` where the body awaits; numeric `status_code=201`; type hints on every parameter; models named `Note`, `NoteCreate`, `NoteUpdate`, `UserCreate`, `Credentials`, `TokenPair` as given per task.
- Missing or invalid credentials answer **401** with a `WWW-Authenticate` header (slide 13: "a request without a token returns 401"). FastAPI's `HTTPBearer`/`APIKeyHeader` answer 403 by default, so they are created with `auto_error=False` and the dependency raises `HTTPException(401, headers={"WWW-Authenticate": "Bearer"})` (or `"ApiKey"`). `HTTPBasic` already answers 401.
- Passwords: `bcrypt.hashpw(pw.encode(), bcrypt.gensalt())` / `bcrypt.checkpw`. Every password field is `Field(min_length=8, max_length=72)` (bcrypt 5 rejects more than 72 bytes with a `ValueError`; the model turns that into a 422).
- Every file the teacher's rule covers (READMEs, docstrings, startup prints) uses no em dash (`—`) and no character outside Latin-1 in anything printed to a console.
- READMEs (EN and ES where present): replace `python app.py` with `fastapi dev app.py`, port 5000 with 8000, "Flask" with "FastAPI" where it names the framework, drop the `FLASK_DEBUG` paragraph, drop `pip install flask` in favour of `pip install -r requirements.txt`, keep the rest. Add the one new-concept paragraph the design assigns to that exercise, and only that one.
- Scratch tests live in `$TESTS` = `C:\Users\mocp\AppData\Local\Temp\claude\C--Users-mocp-OneDrive---GFT-Technologies-SE-EDEM-MDA\ffe9b460-6054-4603-85df-55b9144e189e\scratchpad\fastapi-tests` and run with `$PY` = `C:\Users\mocp\AppData\Local\Temp\claude\C--Users-mocp-OneDrive---GFT-Technologies-SE-EDEM-MDA\ffe9b460-6054-4603-85df-55b9144e189e\scratchpad\vfa\Scripts\python.exe` (venv with the stack already installed). They are never committed. Each test module loads a solution with `load_app("exercises/NN-name/example/exampleNN.py")` from `conftest.py` (Task 1) and calls it through `fastapi.testclient.TestClient`.
- Every "Migrate NN" task ends with the exercise's `example/` solution passing its tests, the starter importing once its blanks are filled (checked by copying the solution over the starter in a temp dir is NOT acceptable; check by reading that each `_____` is in a spot the README hint explains), and both READMEs updated, in one commit.

## Review Focus

1. A student runs `fastapi dev app.py` before filling the decorator blanks: the error must point at the first blank, not at a Pydantic internals trace. Test in Task 3 (`test_starter_fails_at_first_blank`).
2. A 100-character password on `/register`: must answer 422, never a 500 from bcrypt. Test in Task 8 (`test_register_rejects_long_password`), the pattern is reused by 09 to 15.
3. Malformed JSON (`{"title": `) to `POST /notes` in 04/05/06 must be a 422 **problem+json**, not FastAPI's default JSON. Test in Task 4 (`test_malformed_json_is_problem_422`).
4. `GET /profile` with no `Authorization` header in 11/12/13/15 must be 401 with `WWW-Authenticate: Bearer`, not 403. Test in Task 11 (`test_missing_token_is_401`).
5. A webhook whose body contains non-ASCII (`"zen": "Caf\u00e9"`) must verify the HMAC over the raw bytes exactly as GitHub signs them. Test in Task 16 (`test_signature_over_raw_utf8_body`).

---

### Task 1: Scratch test harness

**Files:**
- Create: `$TESTS/conftest.py`
- Create: `$TESTS/pytest.ini`

**Interfaces:**
- Produces: `load_app(rel_path: str, env: dict[str, str] | None = None) -> fastapi.testclient.TestClient`. `rel_path` is relative to the repo root `C:\Users\mocp\OneDrive - GFT Technologies SE\EDEM-MDA\mda-api-exercises`. It sets `env` into `os.environ` before import, inserts the file's directory at the front of `sys.path`, imports the module under a unique name with `importlib.util`, and returns `TestClient(module.app, base_url="http://127.0.0.1:8000")`. Each call imports a fresh module (in-memory stores start empty).
- Produces: `REPO: pathlib.Path` constant. `load_app` also accepts an absolute path, and sets `client.module` to the imported module (tests that monkeypatch module globals use it).
- Produces test helpers in `conftest.py`, imported by every test module: `bearer(token: str) -> dict` (`{"Authorization": f"Bearer {token}"}`, used as `b(tok)` below), `register_login(client, username: str = "ana", password: str = "pw123456") -> str` (POST `/register` then `/login`, returns `access_token`; for 15 it uses `/auth/register` and `/auth/login` when `client.module.app.url_path_for` knows them). Each test module defines `P = "exercises/NN-name/example/exampleNN.py"` and `c = lambda: load_app(P)`.

- [ ] **Step 1: Install pytest into the scratch venv**

Run: `$PY -m pip install -q pytest==8.4.1`
Expected: exit 0.

- [ ] **Step 2: Write `conftest.py` with `REPO` and `load_app` as specified, and `pytest.ini` containing `[pytest]` and `addopts = -q -p no:cacheprovider`**

- [ ] **Step 3: Prove the harness against a throwaway app**

Create `$TESTS/_probe/app.py` with a minimal FastAPI app exposing `GET /ping -> {"pong": true}` and `$TESTS/test_00_harness.py` with one test: `load_app(str(Path(__file__).parent / "_probe/app.py")).get("/ping").json() == {"pong": True}`.
Run: `$PY -m pytest $TESTS/test_00_harness.py`
Expected: 1 passed. Delete `_probe/` and `test_00_harness.py` afterwards.

(No commit: nothing in the repo changes.)

### Task 2: Rename exercise 03

**Files:**
- Rename: `exercises/03-flask-intro/` -> `exercises/03-fastapi-intro/` (all files inside, names unchanged)

- [ ] **Step 1: `git mv exercises/03-flask-intro exercises/03-fastapi-intro`**

- [ ] **Step 2: Verify nothing else references the old folder**

Run: `git grep -n "03-flask-intro" -- . ':!docs'`
Expected: hits only in `exercises/02-api-introduction/readme02.md` line 6 ("continue with exercise 03 (Flask intro)") and any other README; change each to `03-fastapi-intro` / "FastAPI intro" in the same commit.

- [ ] **Step 3: Commit**

`git add -A exercises && git -c commit.gpgsign=false commit -m "Rename 03-flask-intro to 03-fastapi-intro"`

### Task 3: Migrate 03 (FastAPI intro)

**Files:**
- Modify: `exercises/03-fastapi-intro/app.py`, `example/example03.py`, `requirements.txt`, `readme03.md`, `readme03_es.md`

**Interfaces:**
- Produces: routes `GET /` (plain text, `PlainTextResponse`), `GET /about` (plain text), `GET /api/hello -> {"message": "Hello, World!"}`, `GET /api/user/{username} -> {"username", "message": "Welcome, <username>!"}`, `POST /api/greet` with body model `GreetRequest(name: str = "Guest") -> {"greeting": "Hello, <name>!"}`.

- [ ] **Step 1: Write `$TESTS/test_03.py`**

```python
def test_hello(): assert c().get("/api/hello").json() == {"message": "Hello, World!"}
def test_user_path_param(): assert c().get("/api/user/ana").json()["message"] == "Welcome, ana!"
def test_greet_default(): assert c().post("/api/greet", json={}).json() == {"greeting": "Hello, Guest!"}
def test_greet_name(): assert c().post("/api/greet", json={"name": "Ana"}).json() == {"greeting": "Hello, Ana!"}
def test_docs_served(): assert c().get("/docs").status_code == 200
def test_starter_fails_at_first_blank():
    # importing the starter must raise, and the traceback's last frame must be inside app.py
    import importlib.util, traceback
    try: load_app("exercises/03-fastapi-intro/app.py")
    except Exception as e:
        assert "app.py" in traceback.extract_tb(e.__traceback__)[-1].filename
    else: assert False, "starter imported with blanks in place"
```
where `c = lambda: load_app("exercises/03-fastapi-intro/example/example03.py")`.

- [ ] **Step 2: Run: `$PY -m pytest $TESTS/test_03.py`** Expected: fails on import of Flask code (`ModuleNotFoundError: flask` or `AttributeError`).

- [ ] **Step 3: Rewrite `example/example03.py` in FastAPI with the five routes above; `app = FastAPI(title="FastAPI Intro")`**

- [ ] **Step 4: Rewrite `app.py` as the starter: same file with 10 to 12 blanks of the same kinds as today (function name, path string, response key, path parameter name, decorator method for greet, body field). First blank is the `/_____` path of `/about`. Keep a `# Hint:` above each.**

- [ ] **Step 5: `requirements.txt` -> `fastapi[standard]==0.162.0`**

- [ ] **Step 6: Update `readme03.md` and `readme03_es.md`**: title and prose from Flask to FastAPI; Quick Start `pip install -r requirements.txt` / `fastapi dev app.py`; replace the `app.run(debug=True)` code blocks with the FastAPI minimal app; add the two new-concept paragraphs: path operation decorators + path parameters, and Pydantic model for the greet body; one sentence that `fastapi dev` is the development server and `fastapi run` the production one; one sentence that `/docs` is generated automatically; the "fill the blanks top to bottom; the app starts once the decorators are complete" note.

- [ ] **Step 7: Run: `$PY -m pytest $TESTS/test_03.py`** Expected: 6 passed.

- [ ] **Step 8: Start it the way a student would**

Run (PowerShell, from the exercise folder, with `$PY`'s venv Scripts on PATH): `fastapi dev example/example03.py` for 5 seconds, then `curl.exe -s 127.0.0.1:8000/api/hello`.
Expected: `{"message":"Hello, World!"}`. Stop the server.

- [ ] **Step 9: Commit** `git add -A exercises/03-fastapi-intro && git -c commit.gpgsign=false commit -m "Migrate 03 to FastAPI"`

### Task 4: Migrate 04 (Notes API: GET and POST)

**Files:**
- Modify: `exercises/04-api-fundamentals/app.py`, `example/example04.py`, `requirements.txt`, `readme04.md`

**Interfaces:**
- Produces, and 05/06/17 copy verbatim: the **problem+json pattern**:
  - `def problem(status: int, title: str, detail: str, **extra) -> JSONResponse` returning `{"type": "about:blank", "title", "status", "detail", **extra}` with `media_type="application/problem+json"`.
  - `@app.exception_handler(HTTPException)` -> `problem(exc.status_code, <reason phrase>, exc.detail)`.
  - `@app.exception_handler(RequestValidationError)` -> `problem(422, "Unprocessable Content", "Request body or parameters are invalid.", errors=exc.errors())` (the `errors` list made JSON-safe with `jsonable_encoder`).
- Produces models: `NoteCreate(title: str = Field(min_length=1), content: str = "")`, `Note(id: int, title: str, content: str)`.
- Routes: `GET /health -> {"status": "ok"}`, `GET /notes -> list[Note]`, `POST /notes -> Note` with `status_code=201` and `Location: http://127.0.0.1:8000/notes/{id}` (`str(request.url_for("get_note", note_id=...))`), `GET /notes/{note_id} -> Note` or 404 problem "Note {id} does not exist.".

- [ ] **Step 1: Write `$TESTS/test_04.py`**

```python
def test_create_201_location():
    r = c().post("/notes", json={"title": "a", "content": "b"})
    assert r.status_code == 201 and r.headers["location"].endswith("/notes/1") and r.json()["id"] == 1
def test_missing_title_422_problem():
    r = c().post("/notes", json={"content": "b"})
    assert r.status_code == 422 and r.headers["content-type"].startswith("application/problem+json")
    assert r.json()["status"] == 422 and "errors" in r.json()
def test_malformed_json_is_problem_422():
    r = c().post("/notes", content=b'{"title": ', headers={"Content-Type": "application/json"})
    assert r.status_code == 422 and r.headers["content-type"].startswith("application/problem+json")
def test_wrong_content_type_422():
    r = c().post("/notes", content=b"title=a", headers={"Content-Type": "text/plain"})
    assert r.status_code == 422
def test_404_problem():
    r = c().get("/notes/99"); assert r.status_code == 404 and r.json()["title"] == "Not Found"
```

- [ ] **Step 2: Run** Expected: fails (Flask import).
- [ ] **Step 3: Rewrite `example/example04.py`** per Interfaces.
- [ ] **Step 4: Rewrite `app.py`** with ~10 blanks: decorator methods of the three routes, `status_code=_____`, the `Location` header name, the problem media type, the 404 status, the `min_length` value.
- [ ] **Step 5: `requirements.txt` -> `fastapi[standard]==0.162.0`**
- [ ] **Step 6: Update `readme04.md`**: rewrite the status-code section per the design's "Input validation follows FastAPI" paragraph (415 and 400 removed; 422 explained; `curl` examples replaced by one malformed-JSON and one missing-field example both showing 422 problem+json); add the `response_model`/return annotation and `status_code` paragraph; mention `fastapi.status` constants once.
- [ ] **Step 7: Run: `$PY -m pytest $TESTS/test_04.py`** Expected: 5 passed.
- [ ] **Step 8: Commit** `"Migrate 04 to FastAPI"`

### Task 5: Migrate 05 (Notes API: full CRUD)

**Files:**
- Modify: `exercises/05-crud-endpoints/app.py`, `example/example05.py`, `example/commands_cmd.txt`, `example/commands_powershell.txt`, `requirements.txt`, `readme05.md`, `readme05_es.md`

**Interfaces:**
- Consumes: problem+json pattern and `NoteCreate`/`Note` from Task 4 (copied).
- Produces: `NoteUpdate(title: str | None = Field(None, min_length=1), content: str | None = None)` (PATCH, `exclude_unset`), `Note` gains `created_at: str`, `updated_at: str` (ISO 8601 UTC with `Z`, as the Flask solution).
- Routes: `GET /notes?limit=` with `limit: Annotated[int, Query(ge=1, le=100)] = 20` -> `{"data": list[Note], "page": {"limit": int, "total": int}}` newest first; `POST /notes` 201 + Location; `GET /notes/{id}`; `PUT /notes/{id}` body `NoteCreate` -> 200 `Note`; `PATCH /notes/{id}` body `NoteUpdate` -> 200; `DELETE /notes/{id}` -> `Response(status_code=204)`.

- [ ] **Step 1: Write `$TESTS/test_05.py`**

```python
def test_slide_29_sequence():
    k = c(); assert k.get("/notes?limit=10").status_code == 200
    r = k.post("/notes", json={"title": "a", "content": "b"}); assert r.status_code == 201 and "location" in r.headers
    nid = r.json()["id"]
    assert k.patch(f"/notes/{nid}", json={"title": "x"}).json()["title"] == "x"
    assert k.delete(f"/notes/{nid}").status_code == 204
    r = k.get(f"/notes/{nid}"); assert r.status_code == 404 and r.headers["content-type"].startswith("application/problem+json")
def test_limit_over_100_is_422(): assert c().get("/notes?limit=500").status_code == 422
def test_limit_not_int_is_422(): assert c().get("/notes?limit=abc").status_code == 422
def test_page_shape(): assert set(c().get("/notes").json()["page"]) == {"limit", "total"}
```

- [ ] **Step 2: Run** Expected: fails.
- [ ] **Step 3: Rewrite `example/example05.py`**.
- [ ] **Step 4: Rewrite `app.py`**: blanks on the PUT/PATCH/DELETE decorator methods ("which method REPLACES / PARTIALLY updates / removes"), the 204 status, `exclude_unset=True`, `le=100`, plus the carried-over 04 blanks trimmed to keep ~10.
- [ ] **Step 5: `commands_*.txt` and `requirements.txt`**: port 8000; remove the clamping example; FastAPI pin only.
- [ ] **Step 6: READMEs EN and ES**: validation section per design (limit over 100 is rejected with 422, not clamped); add the `Response` for 204 paragraph; `Query` with `ge`/`le` gets one sentence here, the full paragraph is 06's.
- [ ] **Step 7: Run: `$PY -m pytest $TESTS/test_05.py`** Expected: 4 passed.
- [ ] **Step 8: Commit** `"Migrate 05 to FastAPI"`

### Task 6: Migrate 06 (pagination)

**Files:**
- Modify: `exercises/06-pagination/app.py`, `example/example06.py`, `example/commands_cmd.txt`, `example/commands_powershell.txt`, `requirements.txt`, `readme06.md`, `readme06_es.md`

**Interfaces:**
- Consumes: Task 5 models and pattern.
- Produces: `GET /notes` with `limit: Annotated[int, Query(ge=1, le=100)] = 20`, `offset: Annotated[int | None, Query(ge=0)] = None`, `cursor: Annotated[str | None, Query()] = None`. Offset mode when `offset` is given, cursor mode otherwise; both at once -> 400 problem "Use either offset or cursor, not both."; bad cursor -> 400 problem. `encode_cursor(note_id: int) -> str` / `decode_cursor(cursor: str) -> int` (URL-safe base64 without padding; 91 -> `"OTE"`). Responses keep the Flask shapes: offset `{"data", "page": {"mode": "offset", "offset", "limit", "total", "next", "prev"}}`, cursor `{"data", "page": {"mode": "cursor", "limit", "next_cursor", "next", "prev"}}`, plus a `Link` header with `rel="next"`/`rel="prev"` URLs built on `http://127.0.0.1:8000`. Seed 95 notes.

- [ ] **Step 1: Write `$TESTS/test_06.py`**

```python
def test_offset_page(): p = c().get("/notes?offset=0&limit=5").json()["page"]; assert p["mode"] == "offset" and p["total"] == 95 and "offset=5" in p["next"]
def test_cursor_first_page(): p = c().get("/notes?limit=5").json()["page"]; assert p["next_cursor"] == "OTE"
def test_cursor_follow(): assert [n["id"] for n in c().get("/notes?cursor=OTE&limit=5").json()["data"]] == [90, 89, 88, 87, 86]
def test_both_modes_400(): r = c().get("/notes?offset=0&cursor=OTE"); assert r.status_code == 400 and r.json()["status"] == 400
def test_bad_cursor_400(): assert c().get("/notes?cursor=@@").status_code == 400
def test_limit_501_422(): assert c().get("/notes?limit=501").status_code == 422
def test_link_header(): assert 'rel="next"' in c().get("/notes?offset=40&limit=20").headers["link"]
def test_insert_shifts_offset_not_cursor():
    k = c(); page1 = k.get("/notes?offset=0&limit=5").json()["data"]; cur = k.get("/notes?limit=5").json()["page"]["next_cursor"]
    k.post("/notes", json={"title": "Inserted while paginating"})
    assert k.get("/notes?offset=5&limit=5").json()["data"][0]["id"] == page1[-1]["id"]  # repeated
    assert k.get(f"/notes?cursor={cur}&limit=5").json()["data"][0]["id"] == 90           # not repeated
```

- [ ] **Step 2: Run** Expected: fails.
- [ ] **Step 3: Rewrite `example/example06.py`**.
- [ ] **Step 4: Rewrite `app.py`**: blanks on `ge=`/`le=` values, the base64 call, the "both modes" 400, `next_cursor` key, slice bounds; ~9 blanks.
- [ ] **Step 5: `commands_*.txt`, `requirements.txt`**.
- [ ] **Step 6: READMEs EN and ES**: validation table per design (non-integer and out-of-range `limit` are 422; 400 only for cursor errors); add the `Query` paragraph (this is where it is introduced); port 8000 in every URL and `Link` example.
- [ ] **Step 7: Run: `$PY -m pytest $TESTS/test_06.py`** Expected: 8 passed.
- [ ] **Step 8: Commit** `"Migrate 06 to FastAPI"`

### Task 7: Migrate 07 (OpenAPI)

**Files:**
- Modify: `exercises/07-openapi/01-problem-and-solution/undocumented_api.py`, `documented_api.py`, `requirements.txt`, `README.md`; `02-postman-integration/README.md`, `books-api-openapi.yaml`; `03-real-world-apis/README.md` (port only, if any); `readme07.md`

**Interfaces:**
- `undocumented_api.py`: `app = FastAPI(docs_url=None, redoc_url=None, openapi_url=None)`; same routes as the Flask file (`/`, `/api/books` GET with hidden `author` filter, POST with `body: dict`, `/api/books/{book_id}` GET/PUT/DELETE as the Flask version has them), no models.
- `documented_api.py`: `app = FastAPI(title="Books API", version="1.0.0", description=...)`, `Book`/`BookCreate` models, `tags=["books"]`, `summary=` and `responses={404: {"description": "Book not found"}}` on each route, `Field(examples=[...])` on model fields. Docs at `/docs`, spec at `/openapi.json`.

- [ ] **Step 1: Write `$TESTS/test_07.py`**

```python
def test_undocumented_has_no_docs():
    u = load_app("exercises/07-openapi/01-problem-and-solution/undocumented_api.py")
    assert u.get("/docs").status_code == 404 and u.get("/openapi.json").status_code == 404
    assert u.get("/api/books").status_code == 200
def test_documented_spec_is_31():
    d = load_app("exercises/07-openapi/01-problem-and-solution/documented_api.py")
    assert d.get("/docs").status_code == 200
    spec = d.get("/openapi.json").json(); assert spec["openapi"].startswith("3.1") and "/api/books" in spec["paths"]
    assert spec["paths"]["/api/books"]["get"]["tags"] == ["books"]
```

- [ ] **Step 2: Run** Expected: fails.
- [ ] **Step 3: Rewrite both apps** per Interfaces.
- [ ] **Step 4: `requirements.txt`** -> FastAPI pin only (Flask-RESTX gone).
- [ ] **Step 5: Regenerate `02-postman-integration/books-api-openapi.yaml`** from `documented_api.py`: `$PY -c "import yaml, json, importlib..."` (or `TestClient(app).get('/openapi.json')` dumped with `pyyaml`, installed in the scratch venv only). Keep the `servers:` entry `http://127.0.0.1:8000`.
- [ ] **Step 6: READMEs**: `01-problem-and-solution/README.md` run commands `fastapi dev undocumented_api.py` / `fastapi dev documented_api.py`, port 8000, `/swagger.json` -> `/openapi.json`, "Flask-RESTX" prose -> "FastAPI generates the spec from the type hints and models"; `02-postman-integration/README.md` Method 1 link `http://127.0.0.1:8000/openapi.json`; `readme07.md` Part 1 wording.
- [ ] **Step 7: Run: `$PY -m pytest $TESTS/test_07.py`** Expected: 2 passed.
- [ ] **Step 8: Import check**: open `books-api-openapi.yaml` in Postman (Import > File) once by hand, or at minimum validate it parses with `$PY -c "import yaml,sys; yaml.safe_load(open(sys.argv[1]))" <file>`. Expected: no error.
- [ ] **Step 9: Commit** `"Migrate 07 to FastAPI"`

### Task 8: Migrate 08 (Basic Auth)

**Files:**
- Modify: `exercises/08-basic-auth/app.py`, `example/example08.py`, `example/commands_*.txt`, `requirements.txt`, `readme08.md`, `readme08_es.md`

**Interfaces:**
- Produces, and 09 to 15 copy: **password pattern** `hash_password(pw: str) -> str` / `verify_password(pw: str, hashed: str) -> bool` with `bcrypt`; `UserCreate(username: str = Field(min_length=1), password: str = Field(min_length=8, max_length=72))`.
- `security = HTTPBasic(realm="Authentication Required")`; dependency `get_current_user(creds: Annotated[HTTPBasicCredentials, Depends(security)]) -> str` raising `HTTPException(401, headers={"WWW-Authenticate": 'Basic realm="Authentication Required"'})` on bad credentials (compare with `secrets.compare_digest` on the username and `verify_password` on the password; use a dummy hash when the user does not exist).
- Routes: `POST /users` -> 201 `{"message", "username"}` (409 on duplicate), `GET /users` (protected) -> list of usernames.

- [ ] **Step 1: Write `$TESTS/test_08.py`**

```python
def test_slide_46_sequence():
    k = c(); r = k.get("/users"); assert r.status_code == 401 and r.headers["www-authenticate"] == 'Basic realm="Authentication Required"'
    assert k.post("/users", json={"username": "user1", "password": "password123"}).status_code == 201
    assert k.get("/users", auth=("user1", "password123")).status_code == 200
    assert k.get("/users", auth=("user1", "wrong")).status_code == 401
def test_register_rejects_long_password():
    assert c().post("/users", json={"username": "u", "password": "x" * 100}).status_code == 422
```

- [ ] **Step 2: Run** Expected: fails.
- [ ] **Step 3: Rewrite `example/example08.py`**; **Step 4: `app.py`** with the single blank the Flask starter had on the method plus the `Depends(get_current_user)` blank and the `WWW-Authenticate` header name (3 blanks, Flask had 1: acceptable).
- [ ] **Step 5: `requirements.txt`** -> FastAPI pin + `bcrypt==5.0.0`; `commands_*.txt` port 8000.
- [ ] **Step 6: READMEs EN and ES**: Flask-HTTPAuth prose -> `fastapi.security.HTTPBasic`; add the `Depends` + `fastapi.security` paragraph (introduced here); password rules (8 to 72 characters).
- [ ] **Step 7: Run: `$PY -m pytest $TESTS/test_08.py`** Expected: 2 passed.
- [ ] **Step 8: Commit** `"Migrate 08 to FastAPI"`

### Task 9: Migrate 09 (API keys)

**Files:**
- Modify: `exercises/09-api-key-auth/app.py`, `example/example09.py`, `example/commands_*.txt`, `requirements.txt`, `readme09.md`, `readme09_es.md`

**Interfaces:**
- Consumes: password pattern (Task 8).
- `api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)`; dependency `get_current_user(api_key: Annotated[str | None, Depends(api_key_header)]) -> str` raising 401 `{"WWW-Authenticate": "ApiKey"}` when missing or unknown. Keys generated with `secrets.token_urlsafe(32)`, stored as SHA-256 hex (`hash_api_key(key: str) -> str`), shown once.
- Routes as Flask: `POST /register` -> 201 `{"message", "username", "api_key"}`; `POST /api-key/rotate` (protected, no body: the key identifies the user) -> 200 `{"message", "api_key"}`; `DELETE /api-key` (protected) -> 200; `GET /users` (protected).

- [ ] **Step 1: Write `$TESTS/test_09.py`**

```python
def test_slide_48_sequence():
    k = c(); r = k.post("/register", json={"username": "ana", "password": "pw123456"}); key = r.json()["api_key"]
    assert r.status_code == 201 and key
    assert k.get("/users", headers={"X-API-Key": key}).status_code == 200
    r = k.get("/users"); assert r.status_code == 401 and r.headers["www-authenticate"] == "ApiKey"
    assert k.get("/users", headers={"X-API-Key": "nope"}).status_code == 401
def test_rotate_invalidates_old_key():
    k = c(); key = k.post("/register", json={"username": "ana", "password": "pw123456"}).json()["api_key"]
    new = k.post("/api-key/rotate", headers={"X-API-Key": key}).json()["api_key"]
    assert k.get("/users", headers={"X-API-Key": key}).status_code == 401 and k.get("/users", headers={"X-API-Key": new}).status_code == 200
```
- [ ] **Step 2: Run** Expected: fails.
- [ ] **Step 3 to 6: Rewrite solution, starter (~8 blanks: header name, `auto_error`, 401 code, `token_urlsafe`, rotate method, `sha256`), `requirements.txt` (FastAPI + bcrypt), `commands_*.txt`, READMEs** (the `APIKeyHeader` dependency replaces the Flask decorator; keep the "shown once / hashed / rotate" lessons).
- [ ] **Step 7: Run: `$PY -m pytest $TESTS/test_09.py`** Expected: 2 passed.
- [ ] **Step 8: Commit** `"Migrate 09 to FastAPI"`

### Task 10: Migrate 10 (public API, OpenWeather)

**Files:**
- Modify: `exercises/10-public-api/app.py`, `example/example10.py`, `example/commands_*.txt`, `requirements.txt`, `readme10.md`, `readme10_es.md`

**Interfaces:**
- Produces, and 11 to 15 copy: **JWT pattern** with PyJWT: `JWT_SECRET = os.environ.get("JWT_SECRET_KEY") or secrets.token_hex(32)`, `JWT_ALG = "HS256"`, `create_access_token(username: str) -> str` (`sub`, `iat`, `exp` 15 min), `bearer = HTTPBearer(auto_error=False)`, `get_current_user(creds: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer)]) -> str` raising 401 `{"WWW-Authenticate": "Bearer"}` when missing, expired or invalid.
- Routes: `POST /register` 201, `POST /login` -> `{"access_token", "token_type": "bearer"}`, `GET /profile` (protected), `GET /weather?city=` (protected) calling OpenWeather geocoding then weather with `httpx.Client(timeout=10)`; 503 `{"detail": ...}` when `OPENWEATHER_API_KEY` is unset, same JSON shape as the Flask solution on success.

- [ ] **Step 1: Write `$TESTS/test_10.py`**

```python
def test_weather_requires_token(): assert c().get("/weather?city=valencia").status_code == 401
def test_weather_without_key_is_503(monkeypatch):
    monkeypatch.delenv("OPENWEATHER_API_KEY", raising=False); k = c()
    k.post("/register", json={"username": "ana", "password": "pw123456"}); tok = k.post("/login", json={"username": "ana", "password": "pw123456"}).json()["access_token"]
    assert k.get("/weather?city=valencia", headers={"Authorization": f"Bearer {tok}"}).status_code == 503
def test_weather_calls_openweather(monkeypatch):
    import httpx; k = load_app(P, env={"OPENWEATHER_API_KEY": "k"})
    geo = httpx.Response(200, json=[{"name": "Valencia", "country": "ES", "lat": 39.47, "lon": -0.38}])
    wx = httpx.Response(200, json={"main": {"temp": 21, "feels_like": 20, "humidity": 50, "pressure": 1012}, "weather": [{"description": "clear", "main": "Clear", "icon": "01d"}], "wind": {"speed": 3, "deg": 90}, "dt": 1793000000})
    answers = iter([geo, wx]); monkeypatch.setattr(k.module.httpx.Client, "get", lambda self, url, **kw: next(answers))
    tok = register_login(k); r = k.get("/weather?city=valencia", headers=b(tok))
    assert r.status_code == 200 and r.json()["location"]["city"] == "Valencia" and r.json()["weather"]["temperature"] == 21
```

- [ ] **Step 2 to 6: Rewrite solution, starter (~12 blanks as today: env var name, `httpx.get`, status checks, `Depends`), `requirements.txt` (FastAPI, bcrypt, PyJWT; httpx comes with `fastapi[standard]`), `commands_*.txt`, READMEs** (`requests` -> `httpx`; `pip install requests` line removed; `timeout=` kept).
- [ ] **Step 7: Run: `$PY -m pytest $TESTS/test_10.py`** Expected: 3 passed.
- [ ] **Step 8: Commit** `"Migrate 10 to FastAPI"`

### Task 11: Migrate 11 (JWT)

**Files:**
- Modify: `exercises/11-jwt-auth/app.py`, `example/example11.py`, `example/commands_*.txt`, `requirements.txt`, `readme11.md`, `readme11_es.md`

**Interfaces:**
- Consumes: JWT pattern (Task 10), extended: tokens carry `iss="notes-api"`, `aud="notes-client"`, `jti` (uuid4), `type` ("access" 15 min / "refresh" 1 day); `create_refresh_token(username) -> str`; `revoked: set[str]` of `jti`; `decode_token(token: str, expected_type: str) -> dict` validates signature, `exp`, `iss`, `aud`, `type` and revocation.
- `TokenPair(access_token: str, refresh_token: str, token_type: str = "bearer")`.
- Routes as Flask: `POST /register` 201, `POST /login -> TokenPair`, `POST /refresh` (refresh token in `Authorization: Bearer`) -> new access token, `POST /logout` (revokes the presented access token's `jti`), `GET /profile`, `GET /users`, `GET /protected`.

- [ ] **Step 1: Write `$TESTS/test_11.py`**

```python
def test_slide_51_sequence():
    k = c(); assert k.post("/register", json={"username": "ana", "password": "pw123456"}).status_code == 201
    r = k.post("/login", json={"username": "ana", "password": "pw123456"}); tok = r.json()["access_token"]; assert r.status_code == 200 and tok
    assert k.get("/profile", headers={"Authorization": f"Bearer {tok}"}).status_code == 200
def test_missing_token_is_401(): r = c().get("/profile"); assert r.status_code == 401 and r.headers["www-authenticate"] == "Bearer"
def test_claims(): import jwt; tok = login(c()); p = jwt.decode(tok, options={"verify_signature": False}, audience="notes-client"); assert p["iss"] == "notes-api" and p["type"] == "access" and "jti" in p
def test_logout_revokes():
    k = c(); tok = login(k); h = {"Authorization": f"Bearer {tok}"}; assert k.post("/logout", headers=h).status_code == 200; assert k.get("/profile", headers=h).status_code == 401
def test_refresh_token_cannot_access_profile():
    k = c(); k.post("/register", json={"username": "ana", "password": "pw123456"}); rt = k.post("/login", json={"username": "ana", "password": "pw123456"}).json()["refresh_token"]
    assert k.get("/profile", headers={"Authorization": f"Bearer {rt}"}).status_code == 401
    assert k.post("/refresh", headers={"Authorization": f"Bearer {rt}"}).status_code == 200
```

- [ ] **Step 2 to 6: Rewrite solution, starter (~12 blanks: `exp`, `iss`, `aud`, `jti`, `HS256`, `Depends`, `WWW-Authenticate`, type checks), `requirements.txt` (FastAPI, bcrypt, PyJWT), `commands_*.txt`, READMEs** (Flask-JWT-Extended prose becomes PyJWT: show the three lines `jwt.encode` / `jwt.decode`; keep the "signed, not encrypted", short expiry + refresh, revocation lessons; keep the `JWT_SECRET_KEY` env paragraph; add the "login with JSON + HTTPBearer, not the password-grant form" note from the design).
- [ ] **Step 7: Run: `$PY -m pytest $TESTS/test_11.py`** Expected: 5 passed.
- [ ] **Step 8: Commit** `"Migrate 11 to FastAPI"`

### Task 12: Migrate 12 (roles)

**Files:**
- Modify: `exercises/12-roles-permissions/app.py`, `example/example12.py`, `example/commands_*.txt`, `requirements.txt`, `readme12.md`, `readme12_es.md`

**Interfaces:**
- Consumes: JWT pattern (access token only, as the Flask solution; `role` added as an informative claim).
- Produces: `get_current_user(...) -> dict` returning the stored user record; `require_role(role: str) -> Callable` that returns a dependency raising `HTTPException(403, "Permission denied.")` when `users[username]["role"] != role` **read from the store**, not the token. `VALID_ROLES = ("admin", "student")`; `/register` always creates `student`; startup creates `admin` with `ADMIN_PASSWORD` from the environment or a random one printed to stderr (ASCII only), exactly as the Flask solution; seeded test users as today.
- Routes as Flask: `POST /register`, `POST /login`, `GET /profile`, `GET /users` (admin), `PUT /users/{username}` (admin; body `UserUpdate(role: str | None, password: str | None)` with role validated against `VALID_ROLES` -> 422), `DELETE /users/{username}` (admin), `GET /admin/dashboard` (admin), `GET /student/data` (student).

- [ ] **Step 1: Write `$TESTS/test_12.py`**

```python
def test_student_gets_403_on_dashboard(): k = c(); tok = register_login(k, "stu"); assert k.get("/admin/dashboard", headers=b(tok)).status_code == 403
def test_register_ignores_role(): k = c(); r = k.post("/register", json={"username": "evil", "password": "pw123456", "role": "admin"}); assert r.status_code == 201 and r.json()["role"] == "student"
def test_promotion_works_with_old_token():
    k = load_app(P, env={"ADMIN_PASSWORD": "admin-pw-123"})
    atok = k.post("/login", json={"username": "admin", "password": "admin-pw-123"}).json()["access_token"]
    stok = register_login(k, "stu")
    assert k.put("/users/stu", headers=b(atok), json={"role": "admin"}).status_code == 200
    assert k.get("/admin/dashboard", headers=b(stok)).status_code == 200   # role read from the store
def test_missing_token_is_401(): assert c().get("/admin/dashboard").status_code == 401
```

- [ ] **Step 2 to 6: Rewrite solution, starter (4 blanks as today: `require_role("_____")` on dashboard and student data, the 403 code, the forced `"student"` role), `requirements.txt` (FastAPI, bcrypt, PyJWT; Flask-Principal gone), `commands_*.txt`, READMEs** (Flask-Principal prose becomes "a dependency that checks the role"; step 4 "no need to log in again" stays).
- [ ] **Step 7: Run: `$PY -m pytest $TESTS/test_12.py`** Expected: 4 passed.
- [ ] **Step 8: Commit** `"Migrate 12 to FastAPI"`

### Task 13: Migrate 13 (OAuth with GitHub)

**Files:**
- Modify: `exercises/13-oauth/app.py`, `example/example13.py`, `requirements.txt`, `readme13.md`, `readme13_es.md`

**Interfaces:**
- Consumes: JWT pattern.
- `app.add_middleware(SessionMiddleware, secret_key=os.environ.get("SESSION_SECRET") or secrets.token_hex(32))`; `oauth = OAuth(); oauth.register(name="github", client_id=os.environ["GITHUB_CLIENT_ID"], client_secret=os.environ["GITHUB_CLIENT_SECRET"], access_token_url=..., authorize_url=..., api_base_url="https://api.github.com/", client_kwargs={"scope": "user:email", "code_challenge_method": "S256"})` from `authlib.integrations.starlette_client`. Startup fails with a plain message if either env var is missing (as today).
- Routes `async def`: `GET /` (index JSON), `GET /login/github` -> `await oauth.github.authorize_redirect(request, str(request.url_for("callback")))`, `GET /callback` -> exchanges code (`await oauth.github.authorize_access_token(request)`), fetches `user`, stores by GitHub `id` (string) and returns the JWT JSON; `GET /profile`, `GET /users` (protected, `def`), `POST /logout`.

- [ ] **Step 1: Write `$TESTS/test_13.py`**

```python
ENV = {"GITHUB_CLIENT_ID": "x", "GITHUB_CLIENT_SECRET": "y"}
def test_login_redirects_to_github_with_pkce():
    k = load_app("exercises/13-oauth/example/example13.py", env=ENV); r = k.get("/login/github", follow_redirects=False)
    assert r.status_code == 302 and "github.com/login/oauth/authorize" in r.headers["location"]
    assert "code_challenge_method=S256" in r.headers["location"] and "redirect_uri=http%3A%2F%2F127.0.0.1%3A8000%2Fcallback" in r.headers["location"]
def test_profile_needs_token(): assert load_app("exercises/13-oauth/example/example13.py", env=ENV).get("/profile").status_code == 401
def test_missing_env_fails_fast(): import pytest; with pytest.raises(SystemExit): load_app("exercises/13-oauth/example/example13.py", env={"GITHUB_CLIENT_ID": "", "GITHUB_CLIENT_SECRET": ""})
```

- [ ] **Step 2 to 6: Rewrite solution, starter (8 blanks as today: provider name, `url_for("callback")`, `authorize_redirect`, `authorize_access_token`, `"user"` endpoint, `create_access_token`, `GET`, `get_current_user`), `requirements.txt` (FastAPI, PyJWT, Authlib, itsdangerous), READMEs** (callback `http://127.0.0.1:8000/callback` everywhere, the `127.0.0.1` not `localhost` warning kept, Flask session prose -> `SessionMiddleware` one-liner, `SESSION_SECRET` env var mentioned next to `JWT_SECRET_KEY`).
- [ ] **Step 7: Run: `$PY -m pytest $TESTS/test_13.py`** Expected: 3 passed.
- [ ] **Step 8: Manual check (teacher)**: with a real GitHub OAuth App whose callback is `http://127.0.0.1:8000/callback`, run `fastapi dev example/example13.py`, open `http://127.0.0.1:8000/login/github`, approve, confirm the JSON with `access_token` comes back and `GET /profile` with it answers 200. Record the date in the commit message body if done; otherwise leave a line in the README "last verified with a real GitHub app on <date>" unchanged until the teacher does it.
- [ ] **Step 9: Commit** `"Migrate 13 to FastAPI"`

### Task 14: Migrate 14 (rate limiting)

**Files:**
- Modify: `exercises/14-rate-limiting/app.py`, `example/example14.py`, `requirements.txt`, `readme14.md`, `readme14_es.md`; delete the stray `exercises/14-rate-limiting/venv/` from the working tree.

**Interfaces:**
- `limiter = Limiter(key_func=get_remote_address, default_limits=["200/day", "50/hour"], headers_enabled=True)`; `app.state.limiter = limiter`; `app.add_exception_handler(RateLimitExceeded, rate_limit_handler)` where `rate_limit_handler(request, exc) -> JSONResponse` returns 429 `{"error": "Too Many Requests", "message": str(exc.detail), "retry_after_seconds": int}` and calls `request.app.state.limiter._inject_headers(response, request.state.view_rate_limit)` so `Retry-After` and `X-RateLimit-*` are present (verify in slowapi 0.1.10 whether the default `_rate_limit_exceeded_handler` already injects them; if it does, wrap it instead of reimplementing).
- Every limited route takes `request: Request` as its first parameter (slowapi requirement; one README sentence explains it).
- Routes and limits exactly as the Flask solution: `/health` exempt, `POST /register` `5/hour`, `POST /login` `10/minute`, `GET /api/data` `20/minute`, `GET /api/search` `5/minute`, `GET /api/unlimited` exempt, `GET /api/stats` `10/minute`.

- [ ] **Step 1: Write `$TESTS/test_14.py`**

```python
def test_slide_60_loop():
    k = c(); codes = [k.post("/login", json={"username": "x", "password": "y"}).status_code for _ in range(12)]
    assert codes[:10] == [401] * 10 and codes[10:] == [429, 429]
    r = k.post("/login", json={"username": "x", "password": "y"})
    assert r.headers["retry-after"].isdigit() and r.headers["x-ratelimit-limit"] == "10" and "x-ratelimit-remaining" in r.headers and "x-ratelimit-reset" in r.headers
def test_health_exempt(): k = c(); assert all(k.get("/health").status_code == 200 for _ in range(60))
```

- [ ] **Step 2 to 6: Rewrite solution, starter (6 blanks as today: `default_limits`, the four `@limiter.limit("_____")` strings, the missing `@limiter.exempt`), `requirements.txt` (FastAPI, bcrypt, PyJWT, slowapi), READMEs** (Flask-Limiter -> slowapi; the decorator-order paragraph becomes "`@limiter.limit` goes directly under the route decorator, and the function must take `request: Request`"; `curl.exe` note kept).
- [ ] **Step 7: Run: `$PY -m pytest $TESTS/test_14.py`** Expected: 2 passed.
- [ ] **Step 8: Commit** `"Migrate 14 to FastAPI"` (the deleted `venv/` is untracked; nothing to commit for it).

### Task 15: Migrate 15 (versioning)

**Files:**
- Modify: `exercises/15-versioning/app.py`, `example/example15.py`, `requirements.txt`, `readme15.md`, `readme15_es.md`; delete the stray `venv/`.

**Interfaces:**
- Consumes: JWT pattern.
- `v1 = APIRouter(prefix="/api/v1", tags=["v1 (deprecated)"], dependencies=[Depends(get_current_user)])`, `v2 = APIRouter(prefix="/api/v2", tags=["v2"], dependencies=[Depends(get_current_user)])`. Deprecation headers on every v1 response through a router-level dependency `add_deprecation_headers(response: Response)` setting `Deprecation: @1767225600`, `Sunset: Wed, 30 Jun 2027 00:00:00 GMT`, `Link: </api/v2>; rel="successor-version"` (computed from `API_VERSIONS` with `to_epoch` / `to_http_date` as today). Routes, bodies and response shapes exactly as the Flask solution (v1 list returns a bare list; v2 returns `{"data", "count", "version"}` with pagination; v2 adds `PUT`). `GET /api/versions`, `GET /`, `GET /health` unversioned.

- [ ] **Step 1: Write `$TESTS/test_15.py`**

```python
def test_slide_64_headers():
    k = c(); tok = register_login(k); r = k.get("/api/v1/notes", headers=b(tok))
    assert r.status_code == 200 and r.headers["deprecation"] == "@1767225600" and r.headers["sunset"] == "Wed, 30 Jun 2027 00:00:00 GMT" and r.headers["link"] == '</api/v2>; rel="successor-version"'
    r2 = k.get("/api/v2/notes", headers=b(tok)); assert r2.status_code == 200 and "deprecation" not in r2.headers and set(r2.json()) >= {"data", "count", "version"}
def test_v2_put_exists_v1_does_not(): k = c(); tok = register_login(k); assert k.put("/api/v1/notes/1", headers=b(tok), json={}).status_code == 405 and k.put("/api/v2/notes/1", headers=b(tok), json={"title": "t", "content": "c"}).status_code in (200, 404)
def test_versions_endpoint(): assert c().get("/api/versions").json()["v1"]["status"] == "deprecated"
```

- [ ] **Step 2 to 6: Rewrite solution, starter (~15 blanks as today: prefixes, header names, `rel` value, status codes, `include_router`), `requirements.txt` (FastAPI, bcrypt, PyJWT), READMEs** (add the routers paragraph, introduced here; `$TOKEN` examples on port 8000).
- [ ] **Step 7: Run: `$PY -m pytest $TESTS/test_15.py`** Expected: 3 passed.
- [ ] **Step 8: Commit** `"Migrate 15 to FastAPI"`

### Task 16: Migrate 16 (webhooks with ngrok)

**Files:**
- Modify: `exercises/16-webhooks-ngrok/app.py`, `example/example16.py`, `example/send_signed_webhook.py`, `requirements.txt`, `readme16.md`, `readme16_es.md`

**Interfaces:**
- `verify_signature(secret: str, body: bytes, signature_header: str | None) -> bool` (HMAC-SHA256, `hmac.compare_digest`, header `sha256=<hex>`), unchanged logic.
- `@app.post("/webhooks/github") async def github_webhook(request: Request) -> dict`: reads `await request.body()`, requires `GITHUB_WEBHOOK_SECRET` (503 if unset), 401 on bad signature, 400 without `X-GitHub-Delivery`, 200 `{"status": "duplicate, ignored", "delivery_id"}` on repeat, `ping` -> `{"status": "pong"}`, `push` -> `{"status": "received", "commits_processed": n}`. Other routes (`/health`, `/info` without echoing `Authorization`, `/users` GET/POST, `/webhooks/events` GET, `/webhooks/events/clear` POST) as the Flask solution.

- [ ] **Step 1: Write `$TESTS/test_16.py`**

```python
ENV = {"GITHUB_WEBHOOK_SECRET": "s3cret"}
def sig(body): import hmac, hashlib; return "sha256=" + hmac.new(b"s3cret", body, hashlib.sha256).hexdigest()
H = {"Content-Type": "application/json", "X-GitHub-Event": "ping", "X-GitHub-Delivery": "d1"}
def test_valid_and_invalid_signature():
    k = load_app(P, env=ENV); body = b'{"zen": "hi", "hook_id": 1}'
    assert k.post("/webhooks/github", content=body, headers={**H, "X-Hub-Signature-256": sig(body)}).status_code == 200
    assert k.post("/webhooks/github", content=body, headers={**H, "X-Hub-Signature-256": "sha256=00"}).status_code == 401
def test_signature_over_raw_utf8_body():
    k = load_app(P, env=ENV); body = '{"zen": "Caf\u00e9", "hook_id": 1}'.encode("utf-8")
    assert k.post("/webhooks/github", content=body, headers={**H, "X-Hub-Signature-256": sig(body)}).json() == {"status": "pong"}
def test_duplicate_delivery(): k = load_app(P, env=ENV); body = b'{"zen": "x"}'; h = {**H, "X-Hub-Signature-256": sig(body)}; k.post("/webhooks/github", content=body, headers=h); assert k.post("/webhooks/github", content=body, headers=h).json()["status"] == "duplicate, ignored"
def test_unset_secret_503(): assert load_app(P, env={"GITHUB_WEBHOOK_SECRET": ""}).post("/webhooks/github", content=b"{}", headers=H).status_code == 503
```

- [ ] **Step 2 to 6: Rewrite solution, starter (~13 blanks as today: `post`, `await request.body()`, `sha256`, `compare_digest`, header names, status codes), `send_signed_webhook.py` (default URL port 8000), `requirements.txt` (FastAPI only), READMEs** (`ngrok http 8000`; add the `async def` + `await request.body()` paragraph; "Flask" -> "the API").
- [ ] **Step 7: Run: `$PY -m pytest $TESTS/test_16.py`** Expected: 4 passed.
- [ ] **Step 8: Commit** `"Migrate 16 to FastAPI"`

### Task 17: Migrate 17 (MCP, Notes API only)

**Files:**
- Modify: `exercises/17-mcp/notes_api.py`, `mcp_server.py` (docstring + default URL), `client.py` (only if it names the start command), `example/example17.py` (default URL), `requirements.txt`, `readme17.md`, `readme17_es.md`

**Interfaces:**
- `notes_api.py`: the Task 5 Notes API (CRUD, `limit`, problem+json) plus optional API key: `NOTES_API_KEY = os.environ.get("NOTES_API_KEY", "")`; when set, every route requires `X-API-Key` equal to it (401 `{"WWW-Authenticate": "ApiKey"}` otherwise) through `APIKeyHeader(name="X-API-Key", auto_error=False)`. Seed the three notes the Flask version seeds (`Welcome`, `Shopping list`, `API Management`).
- `NOTES_API_URL` default `http://127.0.0.1:8000` in `mcp_server.py` and `example17.py`.

- [ ] **Step 1: Write `$TESTS/test_17.py`**

```python
def test_notes_api_seed_and_key_off(): k = load_app(P, env={"NOTES_API_KEY": ""}); assert [n["title"] for n in k.get("/notes?limit=3").json()["data"]] == ["API Management", "Shopping list", "Welcome"]
def test_notes_api_key_on(): k = load_app(P, env={"NOTES_API_KEY": "k"}); assert k.get("/notes").status_code == 401 and k.get("/notes", headers={"X-API-Key": "k"}).status_code == 200
def test_mcp_default_url(): import re; src = open(REPO / "exercises/17-mcp/mcp_server.py", encoding="utf-8").read(); assert "127.0.0.1:8000" in src and "5000" not in src
```

- [ ] **Step 2 to 6: Rewrite `notes_api.py`; edit `mcp_server.py`, `example17.py` (URL + docstring "start the API with `fastapi dev notes_api.py`"); `requirements.txt` (FastAPI, httpx pin, mcp pin); READMEs** (`fastapi dev notes_api.py`, drop the `FLASK_DEBUG` line, port 8000).
- [ ] **Step 7: Run: `$PY -m pytest $TESTS/test_17.py`** Expected: 3 passed.
- [ ] **Step 8: End-to-end as the slide**: in a venv with `pip install -r exercises/17-mcp/requirements.txt` (the scratch `v17` venv plus `fastapi[standard]`), run `fastapi dev notes_api.py` in one terminal and `python client.py example/example17.py` in another.
Expected output contains `tools/list` with `list_notes`, `get_note`, `create_note`, a created note, and `delete_note is NOT exposed`.
- [ ] **Step 9: Commit** `"Migrate 17 to FastAPI"`

### Task 18: Repo-level files

**Files:**
- Modify: `README.md` (root), `CLAUDE.md` (ignored by git, edit anyway), `mda-apis.postman_collection.json` (ignored by git, edit anyway)

- [ ] **Step 1: Root `README.md`**: title, two sentences on what the repo is (API Management, EDEM MDIA, FastAPI), setup block (`python -m venv venv`, activate on Windows and macOS/Linux, `pip install -r requirements.txt` inside the exercise, `fastapi dev app.py`, open `http://127.0.0.1:8000/docs`), and the 18-row table "Exercise | Slide | What you build" taken from `CLAUDE.md`'s progression with slide numbers from the design (14 -> 01, 20 -> 02, 28 -> 03, 29 -> 04/05, 31 -> 06, 37 -> 07, 46 -> 08, 48 -> 09/10, 51 -> 11/12, 55 -> 13, 60 -> 14, 64 -> 15, 71 -> 16, 81 -> 17, 82 -> 18).
- [ ] **Step 2: `CLAUDE.md`**: "Flask" -> "FastAPI" throughout, 03 folder name, "Running an Exercise" block to `fastapi dev app.py` on 8000, "Common Patterns" code block to the FastAPI minimal app, authentication patterns to the dependency names from Tasks 8 to 11, dependencies list to the pins in Global Constraints, ngrok block to port 8000, "Port 5000 already in use" -> 8000, remove "Debug mode always on".
- [ ] **Step 3: Postman collection**: set the `baseUrl` variable's default value to `http://127.0.0.1:8000`, replace the single hard-coded `127.0.0.1:5000`, and replace `/swagger.json` with `/openapi.json`. Validate: `$PY -c "import json,sys; json.load(open(sys.argv[1], encoding='utf-8'))" mda-apis.postman_collection.json`.
- [ ] **Step 4: Whole-suite run**: `$PY -m pytest $TESTS` Expected: all passed (56 tests across 03 to 17).
- [ ] **Step 5: Grep for leftovers**: `git grep -n -i -E "flask|5000|FLASK_DEBUG|python app.py|swagger.json" -- exercises ':!exercises/*/venv/*'` Expected: no hits except historical mentions a README keeps on purpose (for example "Swagger was the original name"). Then `git grep -n -P "[^ -ÿ]" -- 'exercises/*.py' 'exercises/*/*.py' 'exercises/*/example/*.py'` Expected: no hits (no non-Latin-1 characters in code or startup prints). Fix anything else.
- [ ] **Step 5b: Fresh-venv start for every exercise, as a student would**: a PowerShell loop over the 15 exercise folders with code that, for each, creates `venv` in a temp dir, runs `pip install -r requirements.txt`, then `python -c "import <solution module>"` from inside `example/` (and, for 07, both apps), and finally starts `fastapi dev <solution>` for 5 seconds and curls `/openapi.json` (or `/api/books` for the undocumented one). Expected: every install succeeds, every import succeeds, every curl returns 200. Record the Python version used in the commit message body.
- [ ] **Step 6: Commit** `git add README.md && git -c commit.gpgsign=false commit -m "Update root README, Postman hosts and CLAUDE.md for FastAPI"` (CLAUDE.md and the collection are ignored; the message still names them so the history says they were updated by hand).
