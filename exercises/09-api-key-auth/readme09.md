# Exercise 9: API Key Authentication

## Objective

Learn how to implement **API key authentication** in a FastAPI REST API the way real providers do it: random keys sent in a header, stored only as a hash, shown once, and rotated or revoked when needed.

## Quick Start

```bash
cd exercises/09-api-key-auth
python -m venv venv
venv\Scripts\activate  # Windows
# source venv/bin/activate  # Linux/Mac
pip install -r requirements.txt
fastapi dev app.py
```

Fill the blanks (`_____`) from top to bottom; the app starts once the `auto_error` of `APIKeyHeader`, the decorator of `/api-key/rotate` and the `Depends(...)` of `get_users` are complete. The other blanks (the header names, `401`, `token_urlsafe`, `sha256`, `compare_digest`) are only used when a request reaches them, so you will notice them while testing. If you leave `name="_____"` unfilled, the server looks for a header literally called `_____` and every request answers `401` "API key missing".

---

## What You'll Learn

This exercise builds on Exercise 08 (Basic Authentication) and introduces:

1. **Secure API Key Generation** with `secrets.token_urlsafe()`
2. **Storing only a hash** of the key (SHA-256), never the key itself
3. **Constant-time comparison** with `hmac.compare_digest()`
4. **A reusable dependency** (`Depends(get_current_user)`) that protects any route
5. **Header-based Authentication** with `APIKeyHeader` and `X-API-Key`
6. **Key Rotation and Revocation** with Basic Auth (instead of "recovering" a lost key)

---

## What Are API Keys?

**API keys** are long random secrets used to authenticate API requests without sending username/password credentials repeatedly.

### Real-World Examples:

- **Google Maps API**: Requires API key for every request
- **OpenWeatherMap**: Accepts the key in the query string (`?appid=YOUR_KEY`). Convenient, but URLs end up in server logs, browser history and proxies. In this exercise keys go in a header, **never in the URL**
- **GitHub API**: Uses personal access tokens (a type of API key) with the prefix `ghp_`
- **Stripe**: Uses secret keys with the prefix `sk_live_` / `sk_test_`

### API Key vs Basic Auth

| Feature | Basic Auth | API Key |
|---------|------------|---------|
| **Sends credentials** | Every request (username:password) | Password only at registration and rotation |
| **Token format** | Base64 encoded `user:pass` | Long random string (e.g. `sk_...`) |
| **Expires** | Never (unless password changes) | Can be rotated/revoked at any time |
| **Storage (client)** | Client stores password | Client stores API key (env var, secrets manager) |
| **Storage (server)** | Password hash | API key hash |
| **Use case** | Simple apps, admin panels | Public APIs, third-party access |

---

## API Structure

### Public Endpoints (No Authentication)

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/register` | Register new user, receive API key (shown **once**) |

### Basic Auth Protected

| Method | Endpoint | Auth Required | Description |
|--------|----------|---------------|-------------|
| POST | `/api-key/rotate` | Basic Auth | Issue a new API key; the old one stops working |
| DELETE | `/api-key` | Basic Auth | Revoke your API key (e.g. it leaked) |

### API Key Protected

| Method | Endpoint | Auth Required | Description |
|--------|----------|---------------|-------------|
| GET | `/users` | API Key | List all users |

---

## How It Works

### Pattern 1: Register and Get API Key

```
Client                          Server
  |                               |
  |  POST /register               |
  |  {username, password}         |
  | ----------------------------> |
  |                               | Generate random API key
  |                               | Hash password (bcrypt)
  |                               | Hash API key (SHA-256)
  |                               | Store both HASHES
  |  {api_key: "sk_..."}          |
  | <---------------------------- |
  |                               |
  | Client stores API key safely  |
  | (server can't show it again)  |
```

**Example:**
```bash
curl -X POST -H "Content-Type: application/json" \
     -d '{"username":"alice","password":"secret123"}' \
     http://127.0.0.1:8000/register
```

**Response:**
```json
{
  "message": "User registered successfully",
  "username": "alice",
  "api_key": "sk_Vq3o0m3k8X0bS2Yc1d5yGQ0q3ZpWm1x9lJ7cE4tR2uA",
  "warning": "Store this API key now. It will not be shown again."
}
```

The password is hashed with `bcrypt` and validated like in Exercise 08 (8 to 72 printable ASCII characters; the username cannot contain spaces or `:`, because HTTP Basic sends `username:password` as ASCII). Normal requests use the API key; the password is kept to rotate or revoke the key.

**Client saves this API key** in an environment variable or a secrets manager. Never commit it to Git.

### Pattern 2: Use API Key for Protected Endpoints

```
Client                          Server
  |                               |
  |  GET /users                   |
  |  Header: X-API-Key: sk_...    |
  | ----------------------------> |
  |                               | Hash the received key
  |                               | Compare with stored hashes
  |                               | (constant time)
  |  {users: [...]}               |
  | <---------------------------- |
```

**Example:**
```bash
curl -H "X-API-Key: sk_Vq3o0m3k8X0bS2Yc1d5yGQ0q3ZpWm1x9lJ7cE4tR2uA" \
     http://127.0.0.1:8000/users
```

**Response:**
```json
{
  "users": ["alice", "bob"],
  "count": 2
}
```

> **Header names are case-insensitive** in HTTP. `X-API-Key`, `x-api-key` and `X-API-KEY` are the same header, so older examples that use `x-api-key` still work.

### Pattern 3: Rotate or Revoke a Key

The server **cannot recover** a lost key: it only stores the hash. If you lose the key, or it leaks, you get a **new** one with your username/password (Basic Auth, as in Exercise 08). The old key stops working immediately.

```bash
# Rotate: new key, old key invalidated
curl -X POST -u alice:secret123 http://127.0.0.1:8000/api-key/rotate
```

**Response:**
```json
{
  "message": "API key rotated. The previous key no longer works.",
  "username": "alice",
  "api_key": "sk_9fJk2LmQ0wE7rT1yU5iO3pA8sD6fG4hJ2kL0zX9cV7b",
  "warning": "Store this API key now. It will not be shown again."
}
```

```bash
# Revoke: no key at all until you rotate again
curl -X DELETE -u alice:secret123 http://127.0.0.1:8000/api-key
```

---

## Implementation Guide

### TODOs in app.py

You need to fill in **9 strategic blanks** (search for `_____`):

1. **`api_key_header`**: The header name, `X-API-Key`
2. **`api_key_header`**: `auto_error=False`, so a missing header gives `None` and we return our own 401 message and `WWW-Authenticate` header (FastAPI's default is a generic `401 Not authenticated`)
3. **`generate_api_key()`**: Generate the random part with `secrets.token_urlsafe(32)`
4. **`hash_api_key()`**: Hash the key with `hashlib.sha256(...)`
5. **`find_user_by_api_key()`**: Compare hashes with `hmac.compare_digest()`
6. **`get_current_user()`**: The status code of a missing key, `401`
7. **`get_basic_user()`**: The header that tells the client which authentication is expected, `WWW-Authenticate`
8. **`@app.post("/api-key/rotate")`**: Set the HTTP method of the rotation endpoint
9. **`get_users()`**: Protect the route with `Depends(get_current_user)`

The password hashing and the Basic Auth check (`hash_password`, `verify_password`, `get_basic_user`) are the ones from Exercise 08 and are already written for you.

### Key Concepts to Implement

#### 1. Generating API Keys with `secrets`

```python
import secrets

API_KEY_PREFIX = "sk_"

def generate_api_key() -> str:
    return API_KEY_PREFIX + secrets.token_urlsafe(32)
# Result: "sk_Vq3o0m3k8X0bS2Yc1d5yGQ0q3ZpWm1x9lJ7cE4tR2uA"
```

**Why `secrets` and not `uuid4` or `random`?**
- `secrets` is the standard-library module **designed for secrets**: it uses the operating system's cryptographically secure random generator
- `token_urlsafe(32)` gives 32 random bytes (256 bits), encoded with characters that are safe in headers and URLs
- `uuid4` is designed to be **unique**, not **secret**: it has only 122 random bits and a fixed recognisable format, and the UUID standard does not guarantee a cryptographically secure generator (CPython happens to use one, other libraries may not). Use UUIDs for IDs, `secrets` for keys
- `random` is predictable and must never be used for security

**Why the `sk_` prefix?**
- You recognise at a glance what kind of string it is
- **Secret scanners** (GitHub secret scanning, GitLab, gitleaks...) look for known prefixes. A key with a recognisable prefix that gets pushed to a repository can be detected and revoked automatically

#### 2. Storing Only a Hash of the Key

The database never contains the key. If the database leaks, the attacker gets hashes, not working keys.

```python
import hashlib

def hash_api_key(key: str) -> str:
    return hashlib.sha256(key.encode()).hexdigest()

users[data.username] = {
    "password": hash_password(data.password),  # slow, salted hash (bcrypt)
    "api_key_hash": hash_api_key(api_key),     # fast SHA-256
}
```

**Why is a fast hash (SHA-256) fine for API keys but NOT for passwords?**
- An attacker who steals a hash tries to **guess** the input and hash each guess
- A password is short and chosen by a human (`secret123`). With a fast hash, billions of guesses per second find it quickly. Passwords need a **slow, salted** hash: `bcrypt` makes every guess expensive
- An API key has 256 random bits. There is nothing to guess: even at billions of guesses per second it would take far longer than the age of the universe. A slow hash adds nothing, and a fast one keeps every request fast (the key is checked on **every** request, the password only at login)

This is also why the server **shows the key only once**: after registration it no longer has it.

#### 3. Constant-Time Comparison

```python
import hmac

def find_user_by_api_key(api_key: str) -> str | None:
    candidate_hash = hash_api_key(api_key)

    for username, user_data in users.items():
        stored_hash = user_data["api_key_hash"]
        if stored_hash and hmac.compare_digest(stored_hash, candidate_hash):
            return username

    return None
```

`==` stops at the first different character, so a comparison takes slightly longer the more characters match. Measuring that time difference (a **timing attack**) can leak a secret character by character. `hmac.compare_digest()` always takes the same time. Use it whenever you compare secrets.

> In a real database you would put an index on `api_key_hash` and look it up directly (`WHERE api_key_hash = ?`). That is safe too: the attacker cannot choose the hash of their guess, so timing reveals nothing useful.

#### 4. A Dependency that Protects Routes

Exercise 08 introduced `Depends` and `fastapi.security`; this exercise uses a second ready-made class, `APIKeyHeader`. It reads one header (here `X-API-Key`) and hands its value to your dependency. With `auto_error=False` it gives you `None` when the header is missing, which lets `get_current_user` return our own **401** message and `WWW-Authenticate` header (FastAPI's default is a generic `401 Not authenticated`). `ApiKey` is not an IANA-registered `WWW-Authenticate` scheme (nor is FastAPI's `APIKey`); it is fine for teaching.

```python
from typing import Annotated
from fastapi import Depends, HTTPException
from fastapi.security import APIKeyHeader

api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)

def get_current_user(api_key: Annotated[str | None, Depends(api_key_header)]) -> str:
    # 1. The header is missing
    if api_key is None:
        raise HTTPException(status_code=401, detail="API key missing: include the X-API-Key header",
                            headers={"WWW-Authenticate": "ApiKey"})

    # 2. Look it up by its hash
    username = find_user_by_api_key(api_key)
    if username is None:
        raise HTTPException(status_code=401, detail="Invalid API key",
                            headers={"WWW-Authenticate": "ApiKey"})

    # 3. Valid: this is the value the route receives
    return username


@app.get("/users")
def get_users(user: Annotated[str, Depends(get_current_user)]) -> dict[str, object]:
    ...
```

If `get_current_user` raises, the route never runs. Adding the `Depends(get_current_user)` parameter is all it takes to protect a route, and that is how `GET /users` is protected. Swagger UI (`/docs`) shows an "Authorize" button where you paste the key once.

#### 5. Reading Headers in FastAPI

`APIKeyHeader` already reads the header for you. For any other header, declare a parameter with `Header()`:

```python
from typing import Annotated
from fastapi import Header

@app.get("/whoami")
def whoami(x_api_key: Annotated[str | None, Header()] = None):
    # Header() turns x_api_key into the header X-API-Key (and header names are case-insensitive)
    return {"has_key": x_api_key is not None}
```

**Common API key header names:**
- `X-API-Key` (most common; also written `x-api-key`, it is the same header)
- `Authorization: Bearer YOUR_KEY`
- `api-key`

**Never** send the key in the URL (`/users?api_key=...`): URLs are stored in logs, browser history and proxy caches.

#### 6. Rotating and Revoking Keys

Rotating and revoking are protected with **Basic Auth** (the `HTTPBasic` dependency of Exercise 08, wrapped in `get_basic_user`): you prove who you are with your password, which is what lets you get a new key even if you lost the old one.

```python
@app.post("/api-key/rotate")
def rotate_api_key(user: Annotated[str, Depends(get_basic_user)]) -> dict[str, str]:
    new_api_key = generate_api_key()

    # Overwriting the hash invalidates the old key immediately
    users[user]["api_key_hash"] = hash_api_key(new_api_key)

    return {
        "message": "API key rotated. The previous key no longer works.",
        "username": user,
        "api_key": new_api_key,   # shown once
        "warning": "Store this API key now. It will not be shown again.",
    }


@app.delete("/api-key")
def revoke_api_key(user: Annotated[str, Depends(get_basic_user)]) -> dict[str, str]:
    users[user]["api_key_hash"] = None
    return {"message": "API key revoked. Use POST /api-key/rotate to get a new one.", "username": user}
```

- **Rotate** regularly, and always when a key may have leaked or someone who knew it leaves the team
- **Revoke** when a key leaked and you do not need a replacement yet
- Rotation uses `POST` because it **creates** a new key on every call
- An API key alone cannot rotate or revoke itself: `get_basic_user` answers `401` with `WWW-Authenticate: Basic realm="Authentication Required"` unless username and password match

---

## Testing the API

> The commands below use `curl` with `bash` quoting. In **Windows CMD** use `example/commands_cmd.txt`, and in **PowerShell** use `example/commands_powershell.txt`.

### 1. Register a New User

```bash
curl -X POST -H "Content-Type: application/json" \
     -d '{"username":"alice","password":"secret123"}' \
     http://127.0.0.1:8000/register
```

**Expected Response:**
```json
{
  "message": "User registered successfully",
  "username": "alice",
  "api_key": "sk_Vq3o0m3k8X0bS2Yc1d5yGQ0q3ZpWm1x9lJ7cE4tR2uA",
  "warning": "Store this API key now. It will not be shown again."
}
```

**Save the API key!** You'll need it for subsequent requests, and the server cannot show it again.

### 2. Access Protected Endpoint with API Key

```bash
curl -H "X-API-Key: sk_Vq3o0m3k8X0bS2Yc1d5yGQ0q3ZpWm1x9lJ7cE4tR2uA" \
     http://127.0.0.1:8000/users
```

**Expected Response:**
```json
{
  "users": ["alice"],
  "count": 1
}
```

### 3. Test with Invalid API Key

```bash
curl -H "X-API-Key: sk_invalid-key-12345" \
     http://127.0.0.1:8000/users
```

**Expected Response (401):**
```json
{
  "detail": "Invalid API key"
}
```

### 4. Test with Missing API Key

```bash
curl -i http://127.0.0.1:8000/users
```

**Expected Response (401, with the header `WWW-Authenticate: ApiKey`):**
```json
{
  "detail": "API key missing: include the X-API-Key header"
}
```

### 5. Rotate Your API Key

```bash
curl -X POST -u alice:secret123 http://127.0.0.1:8000/api-key/rotate
```

**Expected Response:**
```json
{
  "message": "API key rotated. The previous key no longer works.",
  "username": "alice",
  "api_key": "sk_9fJk2LmQ0wE7rT1yU5iO3pA8sD6fG4hJ2kL0zX9cV7b",
  "warning": "Store this API key now. It will not be shown again."
}
```

Now repeat step 2 with the **old** key (401) and with the **new** key (200).

### 6. Revoke Your API Key

```bash
curl -X DELETE -u alice:secret123 http://127.0.0.1:8000/api-key
```

**Expected Response:**
```json
{
  "message": "API key revoked. Use POST /api-key/rotate to get a new one.",
  "username": "alice"
}
```

Repeat step 2 with that key: it now answers 401. Rotate again (step 5) to get a working key.

---

## Understanding the Code Flow

### Registration Flow

```python
@app.post("/register", status_code=201)
def register(data: UserCreate) -> dict[str, str]:
    # 1. FastAPI has already validated the JSON body against UserCreate (422 if it does not fit)

    # 2. Check if user exists
    if data.username in users:
        raise HTTPException(status_code=409, detail="User already exists")

    # 3. Generate a random API key
    api_key = generate_api_key()

    # 4. Store the password hash and the API key HASH
    users[data.username] = {
        "password": hash_password(data.password),
        "api_key_hash": hash_api_key(api_key),
    }

    # 5. Return the API key to the client (the only time)
    return {"message": "User registered successfully", "username": data.username,
            "api_key": api_key, "warning": "Store this API key now. It will not be shown again."}
```

### API Key Validation Flow

```
GET /users  (header X-API-Key: sk_...)
   |
   v
APIKeyHeader            reads the header, gives str or None (auto_error=False)
   |
   v
get_current_user        None            -> 401 "API key missing"
                        no hash matches -> 401 "Invalid API key"
                        match           -> returns the username
   |
   v
get_users(user)         runs only if the dependency did not raise
```

---

## Common Issues and Solutions

### Issue 1: "pip install secrets" fails

**Symptom:**
```
ERROR: Could not find a version that satisfies the requirement secrets
```

**Solution:**
`secrets`, `hashlib` and `hmac` are part of Python's standard library. **You don't need to install them.**
Just import them directly:
```python
import hashlib
import hmac
import secrets
```

### Issue 2: API Key Not Working

**Symptom:**
```json
{
  "detail": "Invalid API key"
}
```

**Solution:**
- Verify you're using the exact API key from the **latest** registration or rotation response (rotating invalidates the old key)
- Restarting the server deletes all users and keys (in-memory storage): register again
- Check for extra spaces or quotes in the header
- The header name is `X-API-Key` (case-insensitive in HTTP, so `x-api-key` also works)

**Debug tip:**
```bash
# Store API key in variable to avoid typos
API_KEY="sk_Vq3o0m3k8X0bS2Yc1d5yGQ0q3ZpWm1x9lJ7cE4tR2uA"
curl -H "X-API-Key: $API_KEY" http://127.0.0.1:8000/users
```

### Issue 3: API Key Missing Error

**Symptom:**
```json
{
  "detail": "API key missing: include the X-API-Key header"
}
```

**Solution:**
If *every* request fails this way, even with the header, check the `name="_____"` blank of `APIKeyHeader`: left unfilled, the server looks for a header literally called `_____`. Otherwise, make sure you're including the `-H` flag with curl:
```bash
# Wrong (no header)
curl http://127.0.0.1:8000/users

# Wrong (key in the URL: ignored by the server, and it ends up in logs)
curl "http://127.0.0.1:8000/users?api_key=YOUR_KEY"

# Right
curl -H "X-API-Key: YOUR_KEY" http://127.0.0.1:8000/users
```

### Issue 4: Protected Route Accessible Without a Key

**Symptom:**
Protected endpoint accessible without API key.

**Solution:**
Make sure the route has the dependency parameter:
```python
# Wrong
@app.get("/users")
def get_users():  # Missing the Depends(get_current_user) parameter
    ...

# Right
@app.get("/users")
def get_users(user: Annotated[str, Depends(get_current_user)]):
    ...
```

### Issue 5: "I lost my API key, how do I get it back?"

You can't, and that is on purpose: the server only stores the hash. Call `POST /api-key/rotate` with your username and password to get a new one.

---

## Acceptance Criteria

Your implementation should:

- ✅ Generate API keys with `secrets.token_urlsafe(32)` (with the `sk_` prefix)
- ✅ Store only the SHA-256 **hash** of each API key, never the key
- ✅ Return the API key **once**, on registration (and on rotation)
- ✅ Validate API keys from the `X-API-Key` header
- ✅ Compare hashes with `hmac.compare_digest()`
- ✅ Reject requests with missing API keys (401)
- ✅ Reject requests with invalid API keys (401)
- ✅ Rotate keys with `POST /api-key/rotate` (Basic Auth); the old key stops working
- ✅ Revoke keys with `DELETE /api-key` (Basic Auth)
- ✅ Protect routes with a `Depends(get_current_user)` dependency built on `APIKeyHeader`
- ✅ Answer a missing or invalid key with 401 and `WWW-Authenticate`
- ✅ Allow multiple users with unique API keys

---

## Stretch Goals

Once you complete the basic implementation:

### 1. Add a Grace Period on Rotation

Rotating a key breaks every client that still uses the old one. Keep the previous hash valid for a short time so clients can switch:

```python
from datetime import datetime, timedelta

users[user]["previous_api_key_hash"] = users[user]["api_key_hash"]
users[user]["previous_valid_until"] = datetime.now() + timedelta(hours=24)
users[user]["api_key_hash"] = hash_api_key(new_api_key)
```

Then accept either hash in `find_user_by_api_key()` while `previous_valid_until` has not passed.

### 2. Add API Key Expiration

Track when API keys were created and expire old ones:

```python
from datetime import datetime, timedelta

# On registration and rotation
users[data.username] = {
    "password": hash_password(data.password),
    "api_key_hash": hash_api_key(api_key),
    "key_created_at": datetime.now(),
}

# In get_current_user, after finding the user
created = users[username]["key_created_at"]
if datetime.now() - created > timedelta(days=90):
    raise HTTPException(status_code=401, detail="API key expired: rotate your key",
                        headers={"WWW-Authenticate": "ApiKey"})
```

### 3. Add Rate Limiting

Track API calls per user and limit requests (Exercise 14 does this properly with `slowapi`). A second dependency can wrap the first one:

```python
from collections import defaultdict
from datetime import datetime, timedelta

# Track requests per user (never use the plain key as a dictionary key)
api_calls: dict[str, list[datetime]] = defaultdict(list)

def rate_limited_user(user: Annotated[str, Depends(get_current_user)]) -> str:
    # Rate limiting: max 10 requests per minute
    now = datetime.now()
    minute_ago = now - timedelta(minutes=1)

    # Remove old calls
    api_calls[user] = [t for t in api_calls[user] if t > minute_ago]

    # Check limit
    if len(api_calls[user]) >= 10:
        raise HTTPException(status_code=429, detail="Rate limit exceeded")

    # Record this call
    api_calls[user].append(now)
    return user

@app.get("/users")
def get_users(user: Annotated[str, Depends(rate_limited_user)]):
    ...
```

### 4. Add Multiple API Keys per User

Allow users to have one key per application, so you can revoke one without breaking the others. Store hashes, plus a short non-secret **key id** so users can tell keys apart:

```python
users = {
    'alice': {
        'password': 'hashed',
        'api_keys': {
            # key id -> metadata (the key itself is never stored)
            'k_1a2b': {'hash': 'sha256...', 'name': 'Mobile App', 'last4': 'tR2u'},
            'k_3c4d': {'hash': 'sha256...', 'name': 'Web Dashboard', 'last4': 'cV7b'}
        }
    }
}
```

### 5. Add API Key Scopes

Implement permissions for API keys:

```python
users = {
    "alice": {
        "password": "hashed",
        "api_keys": {
            "k_1a2b": {"hash": "sha256...", "scopes": ["read", "write"]},
            "k_3c4d": {"hash": "sha256...", "scopes": ["read"]},  # Read-only key
        }
    }
}

def require_scope(scope: str):
    """Dependency factory: returns a dependency that checks one scope."""
    def check(api_key: Annotated[str | None, Depends(api_key_header)]) -> str:
        candidate_hash = hash_api_key(api_key or "")

        # Validate API key and check scopes
        for username, user_data in users.items():
            for key_info in user_data["api_keys"].values():
                if hmac.compare_digest(key_info["hash"], candidate_hash):
                    if scope not in key_info["scopes"]:
                        raise HTTPException(status_code=403, detail="Insufficient permissions")
                    return username

        raise HTTPException(status_code=401, detail="Invalid API key",
                            headers={"WWW-Authenticate": "ApiKey"})
    return check

# Usage
@app.get("/users")
def get_users(user: Annotated[str, Depends(require_scope("read"))]):
    ...

@app.post("/users")
def create_user(user: Annotated[str, Depends(require_scope("write"))]):
    ...
```

---

## When to Use API Keys vs Other Auth Methods

### Use API Keys When:

✅ Building public APIs for third-party developers
✅ Allowing programmatic access (scripts, bots)
✅ Need to revoke access without changing passwords
✅ Want to track usage per application
✅ Building server-to-server communication

### Use Basic Auth When:

✅ Simple admin panels
✅ Internal tools
✅ Temporary authentication
✅ Quick prototypes
✅ Key management endpoints (rotate/revoke), as in this exercise

### Use JWT (Exercise 11) When:

✅ Stateless authentication needed
✅ Microservices architecture
✅ Mobile/web applications
✅ Need expiring tokens
✅ Want to embed user identity in token

---

## Summary

**Key Takeaways:**

1. **API Keys vs Basic Auth**
   - API keys are long-lived random secrets
   - Basic Auth sends credentials every request
   - API keys better for public APIs

2. **Generating Keys with `secrets`**
   - Standard library, no installation needed
   - `secrets.token_urlsafe(32)`: 256 random bits from a cryptographically secure generator
   - `uuid4` is for unique IDs, not for secrets
   - A recognisable prefix (`sk_`) helps secret scanners catch leaked keys

3. **Store a Hash, Show the Key Once**
   - The server stores SHA-256(key), never the key
   - A fast hash is fine for high-entropy random keys; passwords need a slow, salted hash
   - Compare with `hmac.compare_digest()`, never `==`
   - Lost key? Rotate, don't recover

4. **Header-based Authentication**
   - Send keys in a header (`X-API-Key`), never in URLs
   - Use `APIKeyHeader(name="X-API-Key", auto_error=False)` to return your own 401 message and `WWW-Authenticate` header (FastAPI's default is a generic `401 Not authenticated`)
   - Headers are case-insensitive (`x-api-key` is the same header)

5. **Security Best Practices**
   - Hash passwords and API keys, never store plain text
   - Keep keys in environment variables or a secrets manager, never in code or Git
   - Rotate keys regularly and revoke leaked ones immediately
   - Always use HTTPS in production

**Next Steps:**
- **Exercise 10**: Consuming External Public APIs
- **Exercise 11**: JWT Authentication (stateless tokens)

Good luck! 🔑
