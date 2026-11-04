# mda-api-exercises

Hands-on exercises for the API Management course (EDEM MDIA). You build and secure REST APIs step by step with FastAPI, from the first endpoint to OAuth, rate limiting, webhooks and an MCP server.

## Setup

Python 3.12 or newer. On Windows, clone or copy the repo to a short folder such as `C:\edem` and work there, because pip can hit the long-path limit inside deep OneDrive folders.

Inside the exercise folder you are working on, create the virtual environment:

```bash
python -m venv venv
```

Activate it (do this before installing anything):

- Windows: `venv\Scripts\activate`
- macOS / Linux: `source venv/bin/activate`

Then install the dependencies and run the app:

```bash
pip install -r requirements.txt
fastapi dev app.py
```

Exercise 06b also needs Docker Desktop (or Rancher Desktop): copy its `.env.example` to `.env` and run `docker compose up -d --wait` in its folder before `fastapi dev app.py` (see `readme06b.md`).

Exercises 07 and 17 name their own files in their README (07: `documented_api.py` and `undocumented_api.py` in `01-problem-and-solution`; 17: `notes_api.py`), and exercises 01, 02 and 18 have no code.

Then open http://127.0.0.1:8000/docs for the interactive documentation. Each exercise has its own `readme<NN>.md` with the instructions (some also have `readme<NN>_es.md` in Spanish) and a finished solution in `example/`.

## Exercises

| Exercise | Slide | What you build |
|---|---|---|
| [01-postman](exercises/01-postman/) | 14 | Call a public API from Postman |
| [02-api-introduction](exercises/02-api-introduction/) | 20 | Theory only: research three real APIs |
| [03-fastapi-intro](exercises/03-fastapi-intro/) | 28 | FastAPI basics |
| [04-api-fundamentals](exercises/04-api-fundamentals/) | 29 | Notes API: GET/POST, status codes, JSON validation |
| [05-crud-endpoints](exercises/05-crud-endpoints/) | 29 | Notes API: full CRUD, RFC 9457 errors |
| [06-pagination](exercises/06-pagination/) | 31 | Notes API: offset and cursor pagination |
| [06b-mysql-database](exercises/06b-mysql-database/) | 31 | Library API on a real MySQL database (Docker): raw SQL, 409 from constraints, a transaction |
| [07-openapi](exercises/07-openapi/) | 37 | OpenAPI documentation |
| [08-basic-auth](exercises/08-basic-auth/) | 46 | Basic Auth with HTTPBasic |
| [09-api-key-auth](exercises/09-api-key-auth/) | 48 | API key generation and validation |
| [10-public-api](exercises/10-public-api/) | 48 | Consuming an external API (OpenWeather), JWT login |
| [11-jwt-auth](exercises/11-jwt-auth/) | 51 | JWT access tokens |
| [12-roles-permissions](exercises/12-roles-permissions/) | 51 | Role-based access control (RBAC) |
| [13-oauth](exercises/13-oauth/) | 55 | OAuth Authorization Code + PKCE with GitHub |
| [14-rate-limiting](exercises/14-rate-limiting/) | 60 | Rate limiting with slowapi |
| [15-versioning](exercises/15-versioning/) | 64 | API versioning, Deprecation and Sunset headers |
| [16-webhooks-ngrok](exercises/16-webhooks-ngrok/) | 71 | Expose your API with ngrok, GitHub webhooks with HMAC |
| [17-mcp](exercises/17-mcp/) | 81 | Wrap the Notes API as an MCP server |
| [18-challenge-mastodon](exercises/18-challenge-mastodon/) | 82 | Final challenge with the Mastodon API |
