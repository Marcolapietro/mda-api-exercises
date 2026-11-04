# Exercise 11: Authentication with JSON Web Tokens (JWT)

## Objective

Learn how to implement **stateless authentication** using JSON Web Tokens (JWT) in a REST API with FastAPI. Understand why JWT is the preferred authentication method for modern APIs, how it differs from Basic Authentication, and how to use it safely: short-lived access tokens, refresh tokens, and full verification of signature, `exp`, `iss` and `aud`.

## Quick Start

```bash
cd exercises/11-jwt-auth
python -m venv venv
venv\Scripts\activate  # Windows
# source venv/bin/activate  # Linux/Mac
pip install -r requirements.txt
copy .env.example .env  # Windows (cp on Linux/Mac)
fastapi dev app.py
```

Fill the blanks (`_____`) from top to bottom; the app starts once the decorator of `/refresh` and the `Depends(...)` of `/profile` are complete: until then it stops with `AttributeError: 'FastAPI' object has no attribute '_____'` (the decorator), or with `NameError: name '_____' is not defined` on Python 3.12/3.13 and `TypeError: ForwardRef('_____'...) is not a callable object` on Python 3.14 (the `Depends`). The other blanks (the claim names, `HS256`, the header name, `DUMMY_HASH`, the functions that create the tokens, the token type and the `revoked` set) are only used when a request reaches them, so you will notice them while testing. The API runs at `http://127.0.0.1:8000`.

Optional, but recommended: give the signing secret a fixed value in `.env` **before** `fastapi dev app.py`. If you don't, the server generates a random one on every start and your tokens stop working after a restart. Generate a value and paste it after `JWT_SECRET_KEY=` in `.env`:

```bash
python -c "import secrets; print(secrets.token_hex(32))"
```

- `app.py` loads `.env` at startup with `load_dotenv()` (from the `python-dotenv` package), so `os.environ.get("JWT_SECRET_KEY")` finds it.
- `.env` is in `.gitignore`, so the secret never reaches GitHub. `.env.example` has empty values only and **is** committed: it tells others which variables to set.
- `fastapi dev` reloads when you save a `.py` file, not `.env`: after editing `.env`, stop the app (Ctrl+C) and start it again.
- A variable set in the terminal (`$env:JWT_SECRET_KEY=...`, `set`, `export`) still works and wins over `.env`.

---

## What is JWT Authentication?

### The Problem with Basic Auth

In Exercise 08, you learned Basic Authentication where:
- Client sends **username and password with EVERY request**
- Credentials are Base64 encoded (not encrypted!)
- Server must verify credentials on every request
- Credentials travel over the network constantly (security risk)

### The JWT Solution

**JWT (JSON Web Token)** provides **stateless authentication**:
1. Client sends username/password **ONCE** to `/login`
2. Server validates and returns two **signed tokens**: a short-lived **access token** and a longer-lived **refresh token**
3. Client sends the access token with every request
4. Server validates the token signature and claims (no database lookup needed!)
5. When the access token expires (15 minutes), the client calls `/refresh` with the refresh token to get a new one
6. **No more sending passwords over the network after login**

### JWT Structure

A JWT token has three parts separated by dots:
```
eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ1c2VyMSIsImV4cCI6MTY3ODg4ODg4OH0.SflKxwRJSMeKKF2QT4fwpMeJf36POk6yJV_adQssw5c
│                                      │                                      │
│                                      │                                      └─ Signature (verifies token hasn't been tampered with)
│                                      └─ Payload (user identity, expiration, issuer, audience...)
└─ Header (algorithm and token type)
```

**Key Concepts:**
- **Self-contained**: Contains all user info needed (no database lookup)
- **Stateless**: Server doesn't store sessions
- **Signed**: Server can verify it wasn't modified
- **Only encoded, not encrypted**: Anyone who has the token can read the payload
- **Expiration**: Access tokens expire after **15 minutes**; refresh tokens after 1 day

### Access Token vs Refresh Token

| | Access token | Refresh token |
|---|---|---|
| **Used for** | Every API request (`/profile`, `/users`...) | Only `POST /refresh` |
| **Lifetime** | Short (15 minutes) | Longer (1 day in this exercise) |
| **If stolen** | Useful to the attacker for 15 minutes at most | Can be revoked with `/logout` |
| **Sent** | On every request | Rarely |

Short access tokens limit the damage of a stolen token; the refresh token means users don't have to type their password every 15 minutes.

---

## API Structure

### Public Endpoints (No Authentication)

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/register` | Register a new user account |
| POST | `/login` | Login with credentials, get access + refresh tokens |

### Token Management

| Method | Endpoint | Token Required | Description |
|--------|----------|----------------|-------------|
| POST | `/refresh` | **Refresh** token | Get a new access token |
| POST | `/logout` | Access **or** refresh token | Revoke the token you send |

### Protected Endpoints (Access Token Required)

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/profile` | Get current user's profile information |
| GET | `/users` | Get list of all users |
| GET | `/protected` | Example protected resource |

---

## How JWT Authentication Works

### Step-by-Step Flow

```
1. User Registration
   Client                    Server
     |                         |
     |  POST /register         |
     |  {username, password}   |
     |------------------------>|
     |                         | • Validate input
     |                         | • Hash password
     |                         | • Store user
     |  201 Created            |
     |<------------------------|

2. User Login (Get Tokens)
   Client                    Server
     |                         |
     |  POST /login            |
     |  {username, password}   |
     |------------------------>|
     |                         | • Validate credentials
     |                         | • Create access token (15 min)
     |                         | • Create refresh token (1 day)
     |                         | • Sign both with the secret
     |  200 OK                 |
     |  {access_token,         |
     |   refresh_token}        |
     |<------------------------|
     | Store tokens securely   |

3. Access Protected Resource
   Client                    Server
     |                         |
     | GET /profile            |
     | Authorization: Bearer   |
     | <access_token>          |
     |------------------------>|
     |                         | • Verify signature
     |                         | • Verify exp, iss, aud
     |                         | • Check it is not revoked
     |                         | • Extract user identity
     |  200 OK                 |
     |  {user data}            |
     |<------------------------|

4. Access Token Expired -> Refresh
   Client                    Server
     |                         |
     | POST /refresh           |
     | Authorization: Bearer   |
     | <refresh_token>         |
     |------------------------>|
     |                         | • Verify it is a REFRESH token
     |                         | • Create new access token
     |  200 OK                 |
     |  {access_token}         |
     |<------------------------|
```

---

## Implementation Details

### 1. JWT Configuration

```python
import os
import secrets
import uuid
from datetime import datetime, timedelta, timezone

import jwt  # PyJWT

# The secret comes from the environment, never from the code.
# Fallback: a random secret per run (tokens die when the server restarts).
JWT_SECRET = os.environ.get("JWT_SECRET_KEY") or secrets.token_hex(32)
JWT_ALG = "HS256"

# Issuer (iss) and audience (aud)
JWT_ISSUER = "notes-api"
JWT_AUDIENCE = "notes-client"

# Revoked tokens, by their unique id (the jti claim)
revoked: set[str] = set()
```

PyJWT is a small library and two functions do the real work. These are the three lines to remember:

```python
token = jwt.encode(claims, JWT_SECRET, algorithm=JWT_ALG)                                               # create and sign
claims = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALG], issuer=JWT_ISSUER, audience=JWT_AUDIENCE)  # verify and read
jwt.decode(token, options={"verify_signature": False})                                                  # only to LOOK inside a token
```

`jwt.decode` checks the signature and `exp` for you, and `iss` and `aud` when you pass `issuer=` and `audience=`. Always pin `algorithms=[...]`: never let the token choose how it is verified.

**Never** write the secret in the code (`JWT_SECRET = "your_secret_key"`): anyone who reads the repository could forge valid tokens for any user.

**The claims we put in every token:**
- `sub` (**subject**): the user. `iat` / `exp`: issued at / expires. Access tokens live 15 minutes, refresh tokens 1 day
- `iss` (**issuer**): who created the token. We reject tokens created by someone else, even if they happen to use the same secret
- `aud` (**audience**): who the token is for. A token issued for another API (e.g. the billing API) must not be accepted by this one
- `jti` (**JWT ID**): a unique id (`uuid4`) per token. The logout blocklist stores these ids
- `type`: `"access"` or `"refresh"`, so a refresh token cannot be used as an access token, nor the other way round

Creating the two kinds of token is one small function:

```python
def create_token(username: str, token_type: str, lifetime: timedelta) -> str:
    now = datetime.now(timezone.utc)
    claims = {
        "sub": username,
        "iat": now,
        "exp": now + lifetime,
        "iss": JWT_ISSUER,
        "aud": JWT_AUDIENCE,
        "jti": str(uuid.uuid4()),
        "type": token_type,
    }
    return jwt.encode(claims, JWT_SECRET, algorithm=JWT_ALG)

def create_access_token(username: str) -> str:
    return create_token(username, "access", timedelta(minutes=15))

def create_refresh_token(username: str) -> str:
    return create_token(username, "refresh", timedelta(days=1))
```

And **one** function checks everything on the way in: signature, `exp`, `iss`, `aud`, `type` and revocation. `require` makes a token without those claims invalid:

```python
def decode_token(token: str, expected_type: str | None) -> dict:
    try:
        claims = jwt.decode(
            token, JWT_SECRET, algorithms=[JWT_ALG],
            issuer=JWT_ISSUER, audience=JWT_AUDIENCE,
            options={"require": ["sub", "exp", "iss", "aud", "jti", "type"]},
        )
    except jwt.ExpiredSignatureError:
        raise unauthorized("Token has expired")
    except jwt.InvalidTokenError:  # bad signature, wrong iss or aud, malformed...
        raise unauthorized("Invalid token")
    if expected_type is not None and claims["type"] != expected_type:
        raise unauthorized(f"Wrong token type: expected {expected_type}")
    if claims["jti"] in revoked:
        raise unauthorized("Token has been revoked")
    return claims
```

`unauthorized(...)` builds `HTTPException(401, detail=..., headers={"WWW-Authenticate": "Bearer"})`. `expected_type=None` accepts either type (only `/logout` uses it).

### 2. User Registration (Public)

```python
@app.post("/register", status_code=201)
def register(data: UserCreate) -> dict[str, str]:
    if data.username in users:
        raise HTTPException(status_code=409, detail="User already exists")
    # Store the bcrypt hash, never the password
    users[data.username] = hash_password(data.password)
    return {"message": "User registered successfully", "username": data.username}
```

`UserCreate` is the Pydantic model from Exercise 08 (password between 8 and 72 characters).

### 3. Login Endpoint (Public)

**This is where JWT differs from Basic Auth!**

```python
class Credentials(BaseModel):
    username: str
    password: str

@app.post("/login")
def login(data: Credentials) -> LoginResponse:
    # Always check a password, even if the user does not exist
    password_ok = verify_password(data.password, users.get(data.username, DUMMY_HASH))
    if data.username not in users or not password_ok:
        raise unauthorized("Invalid credentials")

    # Generate both tokens with the user identity
    return LoginResponse(
        message="Login successful",
        access_token=create_access_token(data.username),
        refresh_token=create_refresh_token(data.username),
        expires_in=15 * 60,
    )
```

`LoginResponse` extends `TokenPair(access_token, refresh_token, token_type="bearer")` with `message` and `expires_in`.

> **Login with JSON, not the password form.** The FastAPI tutorial logs in with `OAuth2PasswordRequestForm`, a form that implements the OAuth **password grant**. OAuth 2.1 removed that grant (you will see why in Exercise 13), so here `/login` takes a plain JSON body and the tokens travel with `HTTPBearer`. Swagger UI (`/docs`) still shows an "Authorize" button for the token.

**Why the dummy hash?** `bcrypt.checkpw` is deliberately slow (a few hundred milliseconds). If an unknown username returned immediately, an attacker could measure the response time and find out **which usernames exist** (user enumeration). Checking against a dummy hash makes both failures take the same time, and both return the same message. `Credentials` uses plain `str` fields (no length limits), so wrong credentials always answer `401`, never `422`.

**Key Differences from Exercise 08:**
- ❌ NO `HTTPBasic` dependency
- ❌ NO HTTP Basic Auth header
- ✅ Credentials sent in JSON body
- ✅ Returns JWT tokens instead of session

### 4. Protected Endpoints (JWT Required)

`HTTPBearer` reads `Authorization: Bearer <token>`. With `auto_error=False` a missing header gives us `None` and we return our own `401` message and `WWW-Authenticate` header (FastAPI's default is a generic `401 Not authenticated`). Two small dependencies, one on top of the other, replace a "login required" decorator:

```python
bearer = HTTPBearer(auto_error=False)

def get_token(creds: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer)]) -> str:
    if creds is None:
        raise unauthorized("Missing or invalid token")
    return creds.credentials

def get_current_user(token: Annotated[str, Depends(get_token)]) -> str:
    return decode_token(token, "access")["sub"]

@app.get("/profile")
def profile(user: Annotated[str, Depends(get_current_user)]) -> dict[str, str]:  # ← validates the access token
    return {"username": user, "profile": f"Profile information for {user}", "account_created": "2025-01-01"}
```

**How `get_current_user` works** (any route that lists it in its parameters is protected):
1. Reads the token from the `Authorization: Bearer <token>` header (no header: `401`)
2. Verifies the signature using `JWT_SECRET`
3. Checks the token hasn't expired (`exp`)
4. Checks issuer (`iss`) and audience (`aud`)
5. Checks it is an **access** token (refresh tokens are rejected here)
6. Checks it is not in the blocklist (logout)
7. Returns the username (`sub`) to the route

### 5. Refresh Endpoint

```python
@app.post("/refresh")
def refresh(token: Annotated[str, Depends(get_token)]) -> dict[str, str | int]:
    claims = decode_token(token, "refresh")  # ← ONLY refresh tokens accepted
    return {"access_token": create_access_token(claims["sub"]), "token_type": "bearer", "expires_in": 900}
```

### 6. Logout (Token Revocation)

JWTs are stateless, so the server cannot "delete" one. To revoke a token before it expires, we keep a **blocklist** of revoked token ids (the `jti` claim) and `decode_token` checks it on every request (the `revoked` set from step 1):

```python
@app.post("/logout")
def logout(token: Annotated[str, Depends(get_token)]) -> dict[str, str]:
    claims = decode_token(token, None)  # accepts access OR refresh tokens
    revoked.add(claims["jti"])
    return {"message": f"{claims['type'].capitalize()} token revoked"}
```

Call `/logout` once with the access token and once with the refresh token to fully log out.

---

## Testing the API

> The commands below use `curl` with `bash` quoting. In **Windows CMD** use `example/commands_cmd.txt`, and in **PowerShell** use `example/commands_powershell.txt`.

### 1. Register a User

```bash
curl -X POST http://127.0.0.1:8000/register \
  -H "Content-Type: application/json" \
  -d '{"username": "alice", "password": "secret123"}'
```

**Expected Response:**
```json
{
  "message": "User registered successfully",
  "username": "alice"
}
```

### 2. Login and Get JWT Tokens

```bash
curl -X POST http://127.0.0.1:8000/login \
  -H "Content-Type: application/json" \
  -d '{"username": "alice", "password": "secret123"}'
```

**Expected Response:**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "message": "Login successful",
  "expires_in": 900
}
```

**Save both tokens** - you'll need them for the next requests!

### 3. Access Protected Endpoint with Token

Replace `<YOUR_TOKEN>` with the `access_token` from step 2:

```bash
curl -X GET http://127.0.0.1:8000/profile \
  -H "Authorization: Bearer <YOUR_TOKEN>"
```

**Expected Response:**
```json
{
  "username": "alice",
  "profile": "Profile information for alice",
  "account_created": "2025-01-01"
}
```

### 4. Try WITHOUT Token (Should Fail)

```bash
curl -X GET http://127.0.0.1:8000/profile
```

**Expected Response (401, with the `WWW-Authenticate: Bearer` header):**
```json
{
  "detail": "Missing or invalid token"
}
```

### 5. Get All Users (Protected)

```bash
curl -X GET http://127.0.0.1:8000/users \
  -H "Authorization: Bearer <YOUR_TOKEN>"
```

### 6. Get a New Access Token with the Refresh Token

```bash
curl -X POST http://127.0.0.1:8000/refresh \
  -H "Authorization: Bearer <YOUR_REFRESH_TOKEN>"
```

**Expected Response:**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "expires_in": 900
}
```

Try it with the **access** token instead: you get `401 {"detail": "Wrong token type: expected refresh"}`.

### 7. Logout

```bash
curl -X POST http://127.0.0.1:8000/logout \
  -H "Authorization: Bearer <YOUR_TOKEN>"
```

**Expected Response:**
```json
{
  "message": "Access token revoked"
}
```

Using that token again returns `401 {"detail": "Token has been revoked"}`.

---

## Understanding JWT Tokens

### Inspecting Your Token (Locally)

The payload is only **Base64URL-encoded**, so you can read it without the secret. Do it **locally**: never paste a real token into a website. Whoever has the token can use it until it expires.

**Option 1: plain Python (no libraries)**
```python
import base64, json

token = "eyJ..."                      # your access_token
payload = token.split('.')[1]         # header.PAYLOAD.signature
payload += '=' * (-len(payload) % 4)  # restore Base64 padding
print(json.dumps(json.loads(base64.urlsafe_b64decode(payload)), indent=2))
```

**Option 2: PyJWT (already installed with `requirements.txt`)**
```python
import jwt
print(jwt.decode("eyJ...", options={"verify_signature": False}))
```

`verify_signature: False` is **only** for looking inside a token. Never use it to authenticate a request.

You will see something like:

```json
{
  "sub": "alice",
  "iat": 1793281345,
  "exp": 1793282245,
  "iss": "notes-api",
  "aud": "notes-client",
  "jti": "72526770-fdda-4e67-ada3-0f9d265c83be",
  "type": "access"
}
```

| Claim | Meaning |
|-------|---------|
| `sub` | Subject: the user identity |
| `iat` / `exp` | Issued at / expires (Unix timestamps). `exp - iat` = 900 s = 15 min |
| `iss` | Issuer: who created the token |
| `aud` | Audience: who the token is for |
| `jti` | Unique token id (used by the logout blocklist) |
| `type` | `access` or `refresh` |

Online decoders such as jwt.io are fine for **throwaway tokens** you create for a demo, never for real ones.

**Important:** The token is **signed**, not **encrypted**:
- ✅ Server can verify it hasn't been tampered with
- ❌ Anyone can read the contents: **never put sensitive data in the payload** (passwords, personal data, internal IDs you would not show the user...)
- ✅ If someone modifies the payload, signature verification fails

---

## JWT vs Basic Auth Comparison

| Feature | Basic Auth (Exercise 08) | JWT (Exercise 11) |
|---------|--------------------------|-------------------|
| **Credentials sent** | Every request | Only at login |
| **Stateful/Stateless** | Stateless (but less secure) | Stateless |
| **Server-side storage** | No sessions | No sessions (only a blocklist for logout) |
| **Database lookup** | Every request | Only at login |
| **Scalability** | Good | Excellent |
| **Security** | Base64 (not secure) | Signed tokens |
| **Token expiration** | No | Yes (15 min access, refresh to renew) |
| **Mobile/SPA friendly** | Not ideal | Perfect |
| **Use case** | Simple APIs, testing | Production APIs |

### When to Use Each

**Basic Auth:**
- Internal tools
- Quick prototypes
- Development/testing
- Simple server-to-server APIs

**JWT:**
- Production web applications
- Mobile apps
- Single Page Applications (React, Vue, Angular)
- Microservices architecture
- APIs accessed by multiple clients

---

## Security Best Practices

### ✅ DO

1. **Use HTTPS in production** - Tokens can be intercepted on HTTP
2. **Keep access tokens short-lived** - 15 minutes, as in this exercise
3. **Use refresh tokens** - For longer sessions without re-login, and revoke them on logout
4. **Verify everything** - Signature, `exp`, `iss` and `aud` (`jwt.decode` with `issuer=` and `audience=`, as above)
5. **Store tokens securely**:
   - Web: `httpOnly` cookies (JavaScript cannot read the token, so an XSS cannot steal it)
   - Mobile: Secure storage (Keychain, KeyStore)
   - NOT in localStorage (vulnerable to XSS)
6. **Use strong secret keys** - Random, long, from an environment variable or secrets manager
7. **Validate all inputs** - Check username/password format

### ❌ DON'T

1. **Don't put sensitive data in JWT** - It is only encoded; anyone can decode it
2. **Don't hard-code or use weak secrets** - Makes tokens easy to forge
3. **Don't skip HTTPS** - Tokens can be stolen
4. **Don't make tokens valid forever** - Security risk
5. **Don't paste real tokens into online decoders** - Decode them locally
6. **Don't reveal which usernames exist** - Same message and same timing for "unknown user" and "wrong password"
7. **Don't store passwords in plain text** - Always hash

---

## Common Errors and Solutions

Every authentication failure answers `401` with a `WWW-Authenticate: Bearer` header and a `detail` message. The client only needs to know "get a valid token", so a bad signature, a wrong issuer and a malformed token all share the same message.

### 1. Missing Authorization Header (401)

```json
{"detail": "Missing or invalid token"}
```

**Solution:** Add header to request:
```bash
-H "Authorization: Bearer <token>"
```

### 2. Invalid Token (401)

```json
{"detail": "Invalid token"}
```

**Causes:**
- Token was modified
- Wrong `JWT_SECRET_KEY`
- Token was generated by a different server, **or by the same server before a restart** (if `JWT_SECRET_KEY` is not set, the secret is random per run)

### 3. Wrong Issuer or Audience (401)

```json
{"detail": "Invalid token"}
```

**Cause:** The token was not created by this API (`iss`), or was created for a different one (`aud`). PyJWT raises `InvalidIssuerError` or `InvalidAudienceError`; our `except jwt.InvalidTokenError` catches both.

### 4. Expired Token (401)

```json
{"detail": "Token has expired"}
```

**Solution:** Call `POST /refresh` with your refresh token. If the refresh token has also expired, login again.

### 5. Wrong Token Type (401)

```json
{"detail": "Wrong token type: expected refresh"}
```

**Cause:** You sent the access token to `/refresh`, or the refresh token to a protected endpoint.

### 6. Revoked Token (401)

```json
{"detail": "Token has been revoked"}
```

**Cause:** You called `/logout` with that token. Login again.

### 7. Malformed Token (401)

```json
{"detail": "Invalid token"}
```

**Cause:** The token is incomplete or has extra characters (usually a copy/paste problem)
**Solution:** Copy the whole token again, without quotes or line breaks

### 8. Missing "Bearer" (401)

```json
{"detail": "Missing or invalid token"}
```

**Solution:** Ensure format is `Bearer <token>`, not just `<token>`

---

## Acceptance Criteria

Your implementation should:

- ✅ Allow user registration via POST `/register`
- ✅ Accept login credentials in JSON body (not Authorization header)
- ✅ Return an `access_token` (15 minutes) **and** a `refresh_token` on successful login
- ✅ Read `JWT_SECRET_KEY` from the environment (random fallback)
- ✅ Put `iss`, `aud`, `jti` and `type` in every token, and verify `iss`, `aud` and `type` on every request
- ✅ Issue new access tokens via POST `/refresh`, accepting only refresh tokens
- ✅ Revoke tokens via POST `/logout` (blocklist of `jti`)
- ✅ Protect routes with `Depends(get_current_user)`
- ✅ Get the user identity from the `sub` claim
- ✅ Return 401 (with `WWW-Authenticate: Bearer`) for invalid credentials, with the same timing for unknown users and wrong passwords
- ✅ Return 401 for missing/expired/revoked/wrong-type JWT tokens
- ✅ Hash passwords before storage
- ✅ Use consistent error response format

---

## Stretch Goals

Once you complete the basic implementation:

1. **Refresh Token Rotation**
   Return a **new** refresh token from `/refresh` and revoke the old one, so a stolen refresh token can only be used once:
   ```python
   @app.post("/refresh")
   def refresh(token: Annotated[str, Depends(get_token)]) -> dict[str, str]:
       claims = decode_token(token, "refresh")
       revoked.add(claims["jti"])
       return {
           "access_token": create_access_token(claims["sub"]),
           "refresh_token": create_refresh_token(claims["sub"]),
       }
   ```

2. **Persistent Blocklist**
   Store revoked `jti` values in Redis with an expiry equal to the token's remaining lifetime, so the blocklist survives restarts and does not grow forever.

3. **Fresh Tokens for Sensitive Actions**
   Add a `"fresh": True` claim to the access token created at login (and `False` to the ones created by `/refresh`), and write a second dependency that rejects tokens that are not fresh. Use it on sensitive endpoints, so tokens obtained via `/refresh` cannot be used for them.

4. **Add User Profile Update**
   PATCH, not PUT: the client sends only the fields it changes (Exercise 05).
   ```python
   @app.patch("/profile")
   def update_profile(user: Annotated[str, Depends(get_current_user)]):
       # Update only the fields that were sent
       ...
   ```

5. **Add Password Change Endpoint**
   - Require current password for verification
   - Hash new password before storing
   - Revoke the user's existing tokens

---

## Next Steps

**Exercise 12:** Roles and Permissions: add **Authorization** to your JWT tokens
- Current exercise: **Authentication** (who you are)
- Exercise 12: **Authorization** (what you can do)
- JWT will include role claims (admin, user, etc.)

**Exercise 13:** OAuth with GitHub (Authorization Code + PKCE): let users log in with an external identity provider

---

## Additional Resources

- [PyJWT Documentation](https://pyjwt.readthedocs.io/)
- [FastAPI: Security](https://fastapi.tiangolo.com/tutorial/security/)
- [FastAPI: Dependencies](https://fastapi.tiangolo.com/tutorial/dependencies/)
- [RFC 7519 - JWT Specification](https://tools.ietf.org/html/rfc7519)
- [OWASP JWT Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/JSON_Web_Token_for_Java_Cheat_Sheet.html)

---

## Summary

**Key Takeaways:**

1. **JWT = Stateless Authentication**
   - Send credentials once, get tokens
   - Use the access token for all subsequent requests
   - No server-side sessions needed

2. **JWT Structure**
   - Header + Payload + Signature
   - Signed (verifiable) but only encoded, not encrypted (readable)
   - Contains user identity, expiration, issuer and audience

3. **Best Practice Flow**
   - POST /login with JSON body → get access token (15 min) + refresh token
   - Store tokens securely
   - Send the access token in Authorization header: `Bearer <token>`
   - When it expires, POST /refresh with the refresh token
   - POST /logout to revoke tokens
   - All protected routes use `Depends(get_current_user)`

4. **Security**
   - Use HTTPS in production
   - Short-lived access tokens + refresh tokens
   - Verify signature, `exp`, `iss` and `aud`
   - Secret from the environment, never in the code
   - Never put sensitive data in the JWT payload, and decode tokens locally
   - Same response and timing for unknown users and wrong passwords

5. **Authentication ≠ Authorization**
   - This exercise: Who are you? (Authentication)
   - Exercise 12: What can you do? (Authorization with roles)

Good luck! 🚀
