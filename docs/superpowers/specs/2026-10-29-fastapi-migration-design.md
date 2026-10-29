# Migrate the exercises from Flask to FastAPI

Date: 2026-10-29. Branch: `fastapi` (created from `fix/security-and-broken-exercises` at `efbfe89`).

## Intent

The repository teaches API Management at EDEM (MDIA 2026/27). Every exercise with code is
written in Flask with 2023-era libraries (Flask 3.0.0, Flask-RESTX with Swagger 2.0,
Flask-JWT-Extended, Flask-Principal, Flask-Limiter). The teacher wants the code students touch
to be what they would meet in a company today: FastAPI with Pydantic, `fastapi dev`, OpenAPI
3.1 generated from the code.

What students learn does not change. Every exercise keeps its title, its goals, its steps, its
fill-in-the-blanks format and its place in the slides. Only the framework underneath changes.

The first group to use this is Grupo A, taught on 4 and 5 November 2026. The slide decks are
updated after the branch is finished (see "Publication order").

## Goals

- All exercises with code (03 to 17) run on FastAPI, started with `fastapi dev app.py` on
  port 8000.
- Every exercise still has an `app.py` with `_____` blanks and `TODO` comments, a complete
  solution in `example/`, a `requirements.txt`, and README in English and Spanish where one
  exists today.
- The commands in each README and in the matching practice slide work as written, on Windows
  (PowerShell 5.1 and Git Bash) and on macOS/Linux, with Python 3.12 to 3.14.
- Exercise 07 shows the OpenAPI 3.1 spec and Swagger UI that FastAPI generates; the
  "undocumented" API genuinely has no docs.
- One commit per exercise, plus a first commit for conventions and a last one for the
  repo-level files, so the history reads as a migration log.

## Non-goals

- Changing what any exercise teaches, adding exercises, or reordering them.
- Completing the Spanish READMEs that are shorter than the English ones (13, 14), or adding
  Spanish READMEs where there are none (02, 03, 07, 18). Translate only what changes.
- Tracking the Postman collection in git (it is in `.gitignore`); only its host is updated.
- Fixing the pedagogy issues listed in `Revision ejercicios API 2026-10.md` that are not caused
  by the framework.
- Databases, async database access, Docker, tests for students, type-checking setup.

## Anti-goals (what would make this a failure even if it runs)

- A student opens `app.py` and finds twice as many concepts as before (dependency injection,
  async, Pydantic models, routers) with no explanation. The exercise must read as simply as the
  Flask one; new FastAPI ideas are introduced one at a time, in the README, when first used.
- The slides and the repo disagree on a command, route, field name or header. Students run the
  slide command and get a 404.
- An exercise works in the solution but the starter `app.py` cannot run until every blank is
  filled, when before it could. Keep the same "runs with blanks filled one by one" behaviour
  where the Flask version had it.
- Something that only works on the teacher's machine (a cached package, a Python 3.14-only
  feature, an emoji that crashes a cp1252 console).

## Constraints

- Deadline: the branch must be merged and the decks updated before 4 November 2026.
- Students use Windows laptops with Python 3.12+ and PowerShell 5.1 (`curl` there is
  `Invoke-WebRequest`; READMEs already use `curl.exe` or Git Bash where that matters). Keep
  that.
- No em dashes in new prose (the teacher's style rule for the course material). Use commas,
  colons or parentheses.
- Each exercise folder stays self-contained: no shared package imported across folders. If a
  helper (for example the RFC 9457 `problem()` function) is needed in several exercises, it is
  copied into each, as today.
- The pinned versions must install on Python 3.14 on Windows. Verified on 2026-10-29 with
  `pip install "fastapi[standard]" slowapi pyjwt bcrypt authlib itsdangerous`:
  fastapi 0.162.0, fastapi-cli 0.0.32, uvicorn 0.54.0, pydantic 2.14.1, starlette 1.10.0,
  slowapi 0.1.10, PyJWT 2.15.1, bcrypt 5.0.0, Authlib 1.9.1, itsdangerous 2.2.0.
  Pin with `==` to these versions (or newer ones the builder verifies the same way).

## Decisions already taken

### How exercises start

- `fastapi dev app.py` (from `fastapi[standard]`), which runs uvicorn with reload on
  `http://127.0.0.1:8000`. Every README "Quick Start", every example URL, every slide and the
  Postman `baseUrl` move from port 5000 to 8000.
- Keep `if __name__ == "__main__": uvicorn.run(...)` out of the files: one way to start, the
  idiomatic one. The README mentions once (exercise 03) that `fastapi dev` is a development
  server and `fastapi run` is the production equivalent.
- `FLASK_DEBUG` disappears. Reload is what `fastapi dev` does; there is no debugger to expose.

### Libraries (Flask thing, FastAPI replacement)

| Flask | FastAPI branch | Used in |
|---|---|---|
| `Flask`, `jsonify`, `request.get_json()` | `FastAPI`, Pydantic models for bodies, return dicts/models | all |
| `@app.route(..., methods=[...])` | `@app.get`, `@app.post`, `@app.put`, `@app.patch`, `@app.delete` | all |
| `abort()` / manual error dicts | `HTTPException` plus a `problem()` helper and exception handlers that render RFC 9457 `application/problem+json` (see "Errors") | 04, 05, 06, 15, 17 (and anywhere the Flask version already used problem+json) |
| Flask-RESTX | nothing: FastAPI generates OpenAPI 3.1 at `/openapi.json`, Swagger UI at `/docs`, ReDoc at `/redoc` | 07 |
| Flask-HTTPAuth | `fastapi.security.HTTPBasic` + `HTTPBasicCredentials` as a dependency | 08 |
| custom `X-API-Key` check | `fastapi.security.APIKeyHeader` as a dependency | 09, 17 (`notes_api.py`) |
| `werkzeug.security.generate_password_hash` | `bcrypt.hashpw` / `bcrypt.checkpw` (two lines, no passlib) | 08 to 15 |
| Flask-JWT-Extended | `PyJWT` directly (`jwt.encode` / `jwt.decode` with `exp`, `iss`, `aud`) and `fastapi.security.HTTPBearer`; a `get_current_user` dependency replaces `@jwt_required()` | 10, 11, 12, 13, 15 |
| Flask-Principal | a `require_role("admin")` dependency that reads the `role` claim from the JWT | 12 |
| `authlib.integrations.flask_client` | `authlib.integrations.starlette_client.OAuth` + `SessionMiddleware` (`itsdangerous`) | 13 |
| Flask-Limiter | `slowapi` (`Limiter(key_func=get_remote_address, headers_enabled=True)`, `@limiter.limit("10/minute")`, `app.state.limiter`, 429 handler) | 14 |
| URL-prefixed routes | `APIRouter(prefix="/api/v1")` and `/api/v2`; deprecation headers added by a router dependency | 15 |
| `request.get_data()` for HMAC | `await request.body()` (the only `async def` in the course, explained in the README) | 16 |
| `requests` | `httpx` (same call shape, already a dependency of 17) | 10, 17 |

Exercise 17's `mcp_server.py`, `client.py` and `example/example17.py` do not change except the
default `NOTES_API_URL` (port 8000).

### Errors

FastAPI answers `{"detail": ...}` by default and uses 422 for validation errors. The course
teaches RFC 9457, so:

- Exercises that already used problem+json in Flask (04, 05, 06, 17) keep a `problem()` helper
  and register handlers for `HTTPException` and `RequestValidationError` that return
  `application/problem+json` with `type`, `title`, `status`, `detail`, `instance`.
- Validation errors stay 422 (matches slide 11 and the RFC 9457 example on slide 65). The
  `detail` field summarises Pydantic's errors in one sentence; the raw error list goes in an
  extra `errors` field.
- Exercises that used plain `{"error": ...}` JSON in Flask (08 to 16) may keep FastAPI's
  default `{"detail": ...}`; do not add problem+json there unless the Flask version had it.

### Blanks and starter files

- Keep the same number of blanks per exercise, give or take two, and the same kind of thing
  being blanked: HTTP method, status code, header name, dependency name, field name. Do not
  blank things the student has not been taught (for example `Depends` in exercise 03).
- Where the Flask starter had a hint comment above a blank, the FastAPI starter has one too.
- A new FastAPI concept gets a two-to-five-line explanation in the README the first time it
  appears, in this order: path operation decorators and path parameters (03), Pydantic models
  and automatic validation (03, body of the greet endpoint), `response_model` and
  `status_code` (04), `Response` for headers and 204 (05), `Query` parameters with validation
  (06), `Depends` and `fastapi.security` (08), routers (15), `async def` for the raw body (16).

### Exercise 03

- Folder renamed to `03-fastapi-intro`; files `readme03.md` and `readme03_es.md` keep their
  names. The rename is its own commit (`git mv`) before the content commit, so history follows
  the files.
- Same five endpoints as today (`/`, `/about`, `/api/hello`, `/api/user/{username}`, `POST
  /api/greet`), with the greet body as a Pydantic model.

### Exercise 07

- `undocumented_api.py`: FastAPI app created with `docs_url=None, redoc_url=None,
  openapi_url=None`, raw dict bodies (`body: dict`) and no response models, so there is nothing
  to discover. Same hidden `?author=` filter.
- `documented_api.py`: the same API with Pydantic models, `tags`, `summary`, `description`,
  `response_model`, `responses={404: ...}` and `examples`, so Swagger UI shows what the Flask
  version showed. Spec is served at `/openapi.json` (README Part 2 "Method 1" changes from
  `/swagger.json`).
- `02-postman-integration/books-api-openapi.yaml`: the server URL moves to port 8000. The
  builder may regenerate it from the documented app (`openapi: 3.1.0`) if the hand-written 3.0.3
  file would otherwise disagree with `/openapi.json`; the import into Postman must still work.
- `requirements.txt` of 07 drops Flask-RESTX.

### Exercise 13 (OAuth)

- Callback URL becomes `http://127.0.0.1:8000/callback`. The README and slide 55 tell students
  to register that URL in their GitHub OAuth App (and to open `127.0.0.1`, not `localhost`).
- PKCE stays on through `client_kwargs={'code_challenge_method': 'S256'}` as today. The
  session that stores Authlib's state and verifier is `SessionMiddleware` with a secret from
  the environment, random per run if unset (same policy as today's `secret_key`).

### Exercise 16 (webhooks)

- `ngrok http 8000`. The README's step list and the slide's terminal change accordingly.
- Signature verification over `await request.body()`; the rest of the flow is unchanged.

### Repo-level files (last commit)

- `README.md` (root) gets a short map: what the repo is, how to set up one venv for all
  exercises (`pip install -r requirements.txt` per exercise still works), and the slide-to-
  exercise table from `CLAUDE.md`.
- `CLAUDE.md` (ignored by git, but present on the teacher's machine): update "Flask" to
  "FastAPI", the exercise list and the 03 folder name.
- `mda-apis.postman_collection.json` (ignored by git): `baseUrl` default and the one hard-coded
  `127.0.0.1:5000` become port 8000; the 07 request that points at `/swagger.json` becomes
  `/openapi.json`.
- Delete the stale `venv/` folders inside `exercises/14-rate-limiting` and
  `exercises/15-versioning` from the working tree (they are ignored by git; just noise).

### Commits

Branch `fastapi`, in this order, one-line messages, no trailers:

1. `Add FastAPI migration design`
2. `Rename 03-flask-intro to 03-fastapi-intro`
3. `Migrate 03 to FastAPI` ... one per exercise, 03 to 17, in numeric order
4. `Update root README, Postman hosts and CLAUDE.md for FastAPI`

Every "Migrate NN" commit leaves that exercise fully working: starter runs, solution passes the
README commands, both READMEs updated. Do not batch two exercises in one commit.

### Publication order

1. `fix/security-and-broken-exercises` is merged into `main` (it holds the whole 2026 rework
   and is currently unmerged; `origin/main` is still at `74de5e5`).
2. `fastapi` is merged into `main`.
3. Only then are the practice slides changed in both decks (Grupo A and Grupo B), so the slides
   never point at a command that `main` does not have.

The deck changes are not part of this design; they are listed here so the builder records what
each exercise's final commands are. Slides affected: 28 (03), 29 (04/05), 31 (06), 37 (07), 46
(08), 48 (09/10), 51 (11/12), 55 (13), 60 (14, mentions Flask-Limiter), 64 (15), 71 (16), 81
(17), plus any `127.0.0.1:5000` or `python app.py` elsewhere in the practice slides.

## Verification (what "done" means per exercise)

- `fastapi dev app.py` starts the solution and the starter (with blanks filled) on Windows in
  PowerShell 5.1 and in Git Bash, from a fresh venv built with that exercise's
  `requirements.txt` on Python 3.14.
- Every command block in the English README, and every command on the matching practice
  slide, is run against the solution and produces the status code, header or body the text
  says. Keep a scratch script (FastAPI `TestClient` is fine) that exercises these so they can
  be rerun after a late change; it does not need to be committed.
- `/docs` and `/openapi.json` open on every exercise except `undocumented_api.py` (07).
- Exercise 17: `python client.py example/example17.py` against the FastAPI `notes_api.py`
  prints the three tools and the created note, as today.
- Exercise 14: the 11th call to `POST /login` within a minute returns 429 with `Retry-After`
  and `X-RateLimit-Limit`, `X-RateLimit-Remaining`, `X-RateLimit-Reset` present.
- Exercise 13 is checked by hand once with a real GitHub OAuth App on port 8000.
- No startup message or README command contains characters outside Latin-1 (cp1252 consoles).

## Left to the builder

- Exact wording of the new README explanations and of hints above blanks.
- Which lines to blank in each starter, within the rules above.
- Whether each exercise's data lives in a module-level dict (as today) or in a small class;
  keep whatever reads simplest.
- Response models: use them where they make Swagger UI clearer (04 onwards); plain dicts are
  fine in 03 and in the "undocumented" API.
- Whether to keep the long "educational" docstrings and startup `print()` banners of the Flask
  versions. Shorten them if they explain Flask internals; keep the ones that explain the API.
- How `slowapi` is wired so the 429 body matches the README (custom handler or the default one).
