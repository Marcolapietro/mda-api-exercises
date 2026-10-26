# Exercise 6: Authentication with JSON Web Tokens (JWT)

## Objective

Learn how to implement **stateless authentication** using JSON Web Tokens (JWT) in a REST API with Flask. Understand why JWT is the preferred authentication method for modern APIs, how it differs from Basic Authentication, and how to use it safely: short-lived access tokens, refresh tokens, and full verification of signature, `exp`, `iss` and `aud`.

## Quick Start

```bash
cd exercises/06-jwt-auth
python -m venv venv
venv\Scripts\activate  # Windows
# source venv/bin/activate  # Linux/Mac
pip install -r requirements.txt
python app.py
```

Optional, but recommended: set the signing secret in an environment variable **before** `python app.py`. If you don't, the server generates a random one on every start and your tokens stop working after a restart.

```bash
# Windows PowerShell
$env:JWT_SECRET_KEY = python -c "import secrets; print(secrets.token_hex(32))"
# Windows CMD: generate it once, then paste it
python -c "import secrets; print(secrets.token_hex(32))"
set JWT_SECRET_KEY=<paste the value>
# Linux/Mac
export JWT_SECRET_KEY=$(python -c "import secrets; print(secrets.token_hex(32))")
```

---

## What is JWT Authentication?

### The Problem with Basic Auth

In Exercise 04, you learned Basic Authentication where:
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
from datetime import timedelta
from flask_jwt_extended import JWTManager

# The secret comes from the environment, never from the code.
# Fallback: a random secret per run (tokens die when the server restarts).
app.config['JWT_SECRET_KEY'] = os.environ.get('JWT_SECRET_KEY') or secrets.token_hex(32)

# Short-lived access tokens + longer-lived refresh tokens
app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(minutes=15)
app.config['JWT_REFRESH_TOKEN_EXPIRES'] = timedelta(days=1)

# Issuer (iss) and audience (aud)
JWT_ISSUER = 'mda-api-exercises'
JWT_AUDIENCE = 'mda-api-clients'
app.config['JWT_ENCODE_ISSUER'] = JWT_ISSUER      # written into our tokens
app.config['JWT_DECODE_ISSUER'] = JWT_ISSUER      # required in received tokens
app.config['JWT_ENCODE_AUDIENCE'] = JWT_AUDIENCE
app.config['JWT_DECODE_AUDIENCE'] = JWT_AUDIENCE

jwt = JWTManager(app)
```

**Never** write the secret in the code (`JWT_SECRET_KEY = 'your_secret_key'`): anyone who reads the repository could forge valid tokens for any user.

**What are `iss` and `aud`?**
- `iss` (**issuer**): who created the token. We reject tokens created by someone else, even if they happen to use the same secret
- `aud` (**audience**): who the token is for. A token issued for another API (e.g. the billing API) must not be accepted by this one
- `ENCODE_*` settings add the claim to the tokens we create; `DECODE_*` settings make `@jwt_required()` **reject** any token whose claim is missing or different

### 2. User Registration (Public)

```python
@app.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')

    # Store user with hashed password
    users[username] = {
        'password': generate_password_hash(password)
    }
    return jsonify({'message': 'User registered'}), 201
```

### 3. Login Endpoint (Public)

**This is where JWT differs from Basic Auth!**

```python
# A hash of a random password, created once at startup
DUMMY_PASSWORD_HASH = generate_password_hash(secrets.token_urlsafe(16))

@app.route('/login', methods=['POST'])
def login():
    # Get credentials from REQUEST BODY, not Authorization header
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')

    # Always check a password, even if the user does not exist
    user = users.get(username)
    password_hash = user['password'] if user else DUMMY_PASSWORD_HASH
    password_ok = check_password_hash(password_hash, password)

    if not user or not password_ok:
        return jsonify({'error': 'Invalid credentials'}), 401

    # Generate both tokens with the user identity
    access_token = create_access_token(identity=username)
    refresh_token = create_refresh_token(identity=username)
    return jsonify({'access_token': access_token,
                    'refresh_token': refresh_token}), 200
```

**Why the dummy hash?** `check_password_hash` is deliberately slow (around 100 ms). If an unknown username returned immediately, an attacker could measure the response time and find out **which usernames exist** (user enumeration). Checking against a dummy hash makes both failures take the same time, and both return the same message.

**Key Differences from Exercise 04:**
- ❌ NO `@auth.login_required` decorator
- ❌ NO HTTP Basic Auth header
- ✅ Credentials sent in JSON body
- ✅ Returns JWT tokens instead of session

### 4. Protected Endpoints (JWT Required)

```python
@app.route('/profile', methods=['GET'])
@jwt_required()  # ← Validates the access token
def profile():
    # Extract user identity from token
    current_user = get_jwt_identity()
    return jsonify({'username': current_user}), 200
```

**How `@jwt_required()` works:**
1. Extracts token from `Authorization: Bearer <token>` header
2. Verifies token signature using `JWT_SECRET_KEY`
3. Checks token hasn't expired (`exp`)
4. Checks issuer (`iss`) and audience (`aud`)
5. Checks it is an **access** token (refresh tokens are rejected here)
6. Checks it is not in the blocklist (logout)
7. Makes user identity available via `get_jwt_identity()`

### 5. Refresh Endpoint

```python
@app.route('/refresh', methods=['POST'])
@jwt_required(refresh=True)  # ← ONLY refresh tokens accepted
def refresh():
    current_user = get_jwt_identity()
    access_token = create_access_token(identity=current_user)
    return jsonify({'access_token': access_token}), 200
```

### 6. Logout (Token Revocation)

JWTs are stateless, so the server cannot "delete" one. To revoke a token before it expires, we keep a **blocklist** of revoked token ids (the `jti` claim) and check it on every request:

```python
revoked_tokens = set()  # in memory: lost on restart (use Redis or a DB in production)

@jwt.token_in_blocklist_loader
def is_token_revoked(jwt_header, jwt_payload):
    return jwt_payload['jti'] in revoked_tokens

@app.route('/logout', methods=['POST'])
@jwt_required(verify_type=False)  # accepts access OR refresh tokens
def logout():
    revoked_tokens.add(get_jwt()['jti'])
    return jsonify({'message': 'Token revoked'}), 200
```

Call `/logout` once with the access token and once with the refresh token to fully log out.

---

## Testing the API

> The commands below use `curl` with `bash` quoting. In **Windows CMD** use `example/commands_cmd.txt`, and in **PowerShell** use `example/commands_powershell.txt`.

### 1. Register a User

```bash
curl -X POST http://127.0.0.1:5000/register \
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
curl -X POST http://127.0.0.1:5000/login \
  -H "Content-Type: application/json" \
  -d '{"username": "alice", "password": "secret123"}'
```

**Expected Response:**
```json
{
  "message": "Login successful",
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "Bearer",
  "expires_in": 900
}
```

**Save both tokens** - you'll need them for the next requests!

### 3. Access Protected Endpoint with Token

Replace `<YOUR_TOKEN>` with the `access_token` from step 2:

```bash
curl -X GET http://127.0.0.1:5000/profile \
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
curl -X GET http://127.0.0.1:5000/profile
```

**Expected Response (401):**
```json
{
  "msg": "Missing Authorization Header"
}
```

### 5. Get All Users (Protected)

```bash
curl -X GET http://127.0.0.1:5000/users \
  -H "Authorization: Bearer <YOUR_TOKEN>"
```

### 6. Get a New Access Token with the Refresh Token

```bash
curl -X POST http://127.0.0.1:5000/refresh \
  -H "Authorization: Bearer <YOUR_REFRESH_TOKEN>"
```

**Expected Response:**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "Bearer",
  "expires_in": 900
}
```

Try it with the **access** token instead: you get `422 {"msg": "Only refresh tokens are allowed"}`.

### 7. Logout

```bash
curl -X POST http://127.0.0.1:5000/logout \
  -H "Authorization: Bearer <YOUR_TOKEN>"
```

**Expected Response:**
```json
{
  "message": "Access token revoked"
}
```

Using that token again returns `401 {"msg": "Token has been revoked"}`.

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

**Option 2: PyJWT (already installed with Flask-JWT-Extended)**
```python
import jwt
print(jwt.decode("eyJ...", options={"verify_signature": False}))
```

`verify_signature: False` is **only** for looking inside a token. Never use it to authenticate a request.

You will see something like:

```json
{
  "fresh": false,
  "iat": 1793034905,
  "jti": "54acfacf-b34e-4c02-8440-6868bc0de9f6",
  "type": "access",
  "sub": "alice",
  "nbf": 1793034905,
  "csrf": "4ba7fa40-ec45-41a1-aa21-f921784e12d3",
  "aud": "mda-api-clients",
  "iss": "mda-api-exercises",
  "exp": 1793035805
}
```

| Claim | Meaning |
|-------|---------|
| `sub` | Subject: the user identity |
| `iat` / `nbf` / `exp` | Issued at / not before / expires (Unix timestamps). `exp - iat` = 900 s = 15 min |
| `iss` | Issuer: who created the token |
| `aud` | Audience: who the token is for |
| `jti` | Unique token id (used by the logout blocklist) |
| `type` | `access` or `refresh` |
| `fresh`, `csrf` | Flask-JWT-Extended internals (`csrf` only matters when tokens are sent in cookies) |

Online decoders such as jwt.io are fine for **throwaway tokens** you create for a demo, never for real ones.

**Important:** The token is **signed**, not **encrypted**:
- ✅ Server can verify it hasn't been tampered with
- ❌ Anyone can read the contents: **never put sensitive data in the payload** (passwords, personal data, internal IDs you would not show the user...)
- ✅ If someone modifies the payload, signature verification fails

---

## JWT vs Basic Auth Comparison

| Feature | Basic Auth (Exercise 04) | JWT (Exercise 06) |
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
4. **Verify everything** - Signature, `exp`, `iss` and `aud` (Flask-JWT-Extended does it with the config above)
5. **Store tokens securely**:
   - Web: `httpOnly` cookies (prevents XSS)
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

### 1. Missing Authorization Header (401)

```json
{"msg": "Missing Authorization Header"}
```

**Solution:** Add header to request:
```bash
-H "Authorization: Bearer <token>"
```

### 2. Invalid Token (422)

```json
{"msg": "Signature verification failed"}
```

**Causes:**
- Token was modified
- Wrong `JWT_SECRET_KEY`
- Token was generated by a different server, **or by the same server before a restart** (if `JWT_SECRET_KEY` is not set, the secret is random per run)

### 3. Wrong Issuer or Audience (422)

```json
{"msg": "Invalid issuer"}
{"msg": "Audience doesn't match"}
```

**Cause:** The token was not created by this API, or was created for a different one.

### 4. Expired Token (401)

```json
{"msg": "Token has expired"}
```

**Solution:** Call `POST /refresh` with your refresh token. If the refresh token has also expired, login again.

### 5. Wrong Token Type (422)

```json
{"msg": "Only refresh tokens are allowed"}
{"msg": "Only non-refresh tokens are allowed"}
```

**Cause:** You sent the access token to `/refresh`, or the refresh token to a protected endpoint.

### 6. Revoked Token (401)

```json
{"msg": "Token has been revoked"}
```

**Cause:** You called `/logout` with that token. Login again.

### 7. Malformed Token (422)

```json
{"msg": "Not enough segments"}
```

**Cause:** The token is incomplete or has extra characters (usually a copy/paste problem)
**Solution:** Copy the whole token again, without quotes or line breaks

### 8. Missing "Bearer" (401)

```json
{"msg": "Missing 'Bearer' type in 'Authorization' header. Expected 'Authorization: Bearer <JWT>'"}
```

**Solution:** Ensure format is `Bearer <token>`, not just `<token>`

---

## Acceptance Criteria

Your implementation should:

- ✅ Allow user registration via POST `/register`
- ✅ Accept login credentials in JSON body (not Authorization header)
- ✅ Return an `access_token` (15 minutes) **and** a `refresh_token` on successful login
- ✅ Read `JWT_SECRET_KEY` from the environment (random fallback)
- ✅ Set and verify `iss` and `aud` on every token
- ✅ Issue new access tokens via POST `/refresh` with `@jwt_required(refresh=True)`
- ✅ Revoke tokens via POST `/logout` (blocklist)
- ✅ Protect routes with `@jwt_required()` decorator
- ✅ Extract user identity with `get_jwt_identity()`
- ✅ Return 401 for invalid credentials, with the same timing for unknown users and wrong passwords
- ✅ Return 401 for missing/expired/revoked JWT tokens
- ✅ Hash passwords before storage
- ✅ Use consistent error response format

---

## Stretch Goals

Once you complete the basic implementation:

1. **Refresh Token Rotation**
   Return a **new** refresh token from `/refresh` and revoke the old one, so a stolen refresh token can only be used once:
   ```python
   @app.route('/refresh', methods=['POST'])
   @jwt_required(refresh=True)
   def refresh():
       revoked_tokens.add(get_jwt()['jti'])
       current_user = get_jwt_identity()
       return jsonify({
           'access_token': create_access_token(identity=current_user),
           'refresh_token': create_refresh_token(identity=current_user)
       }), 200
   ```

2. **Persistent Blocklist**
   Store revoked `jti` values in Redis with an expiry equal to the token's remaining lifetime, so the blocklist survives restarts and does not grow forever.

3. **Fresh Tokens for Sensitive Actions**
   Mark login tokens as fresh (`create_access_token(identity=..., fresh=True)`) and protect sensitive endpoints with `@jwt_required(fresh=True)`, so tokens obtained via `/refresh` cannot be used for them.

4. **Add User Profile Update**
   ```python
   @app.route('/profile', methods=['PUT'])
   @jwt_required()
   def update_profile():
       # Update user data
   ```

5. **Add Password Change Endpoint**
   - Require current password for verification
   - Hash new password before storing
   - Revoke the user's existing tokens

---

## Next Steps

**Exercise 07:** Learn to consume external APIs (weather, GitHub, etc.)

**Exercise 10:** Add **Authorization** (roles and permissions) to your JWT tokens
- Current exercise: **Authentication** (who you are)
- Exercise 10: **Authorization** (what you can do)
- JWT will include role claims (admin, user, etc.)

---

## Additional Resources

- [Flask-JWT-Extended Documentation](https://flask-jwt-extended.readthedocs.io/)
- [Flask-JWT-Extended: Refresh Tokens](https://flask-jwt-extended.readthedocs.io/en/stable/refreshing_tokens.html)
- [Flask-JWT-Extended: Blocklist and Token Revoking](https://flask-jwt-extended.readthedocs.io/en/stable/blocklist_and_token_revoking.html)
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
   - All protected routes use `@jwt_required()`

4. **Security**
   - Use HTTPS in production
   - Short-lived access tokens + refresh tokens
   - Verify signature, `exp`, `iss` and `aud`
   - Secret from the environment, never in the code
   - Never put sensitive data in the JWT payload, and decode tokens locally
   - Same response and timing for unknown users and wrong passwords

5. **Authentication ≠ Authorization**
   - This exercise: Who are you? (Authentication)
   - Exercise 10: What can you do? (Authorization with roles)

Good luck! 🚀
