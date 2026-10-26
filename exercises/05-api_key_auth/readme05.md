# Exercise 5: API Key Authentication

## Objective

Learn how to implement **API key authentication** in a Flask REST API the way real providers do it: random keys sent in a header, stored only as a hash, shown once, and rotated or revoked when needed.

## Quick Start

```bash
cd exercises/05-api_key_auth
python -m venv venv
venv\Scripts\activate  # Windows
# source venv/bin/activate  # Linux/Mac
pip install -r requirements.txt
python app.py
```

---

## What You'll Learn

This exercise builds on Exercise 04 (Basic Authentication) and introduces:

1. **Secure API Key Generation** with `secrets.token_urlsafe()`
2. **Storing only a hash** of the key (SHA-256), never the key itself
3. **Constant-time comparison** with `hmac.compare_digest()`
4. **Custom Decorators** for API key validation
5. **Header-based Authentication** with `X-API-Key`
6. **Key Rotation and Revocation** (instead of "recovering" a lost key)

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
  |                               | Hash password (werkzeug)
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
     http://127.0.0.1:5000/register
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
     http://127.0.0.1:5000/users
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

The server **cannot recover** a lost key: it only stores the hash. If you lose the key, or it leaks, you get a **new** one with your username/password. The old key stops working immediately.

```bash
# Rotate: new key, old key invalidated
curl -X POST -u alice:secret123 http://127.0.0.1:5000/api-key/rotate
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
curl -X DELETE -u alice:secret123 http://127.0.0.1:5000/api-key
```

---

## Implementation Guide

### TODOs in app.py

You need to fill in **8 strategic blanks** (search for `_____`):

1. **`generate_api_key()`**: Generate the random part with `secrets.token_urlsafe(32)`
2. **`hash_api_key()`**: Hash the key with `hashlib.sha256(...)`
3. **`find_user_by_api_key()`**: Compare hashes with `hmac.compare_digest()`
4. **`api_key_required`**: Read the `X-API-Key` header
5. **`register()`**: Store the **hash** of the key, not the key
6. **`rotate_api_key()`**: Set the HTTP method of the rotation endpoint
7. **`rotate_api_key()`**: Overwrite the stored hash with the hash of the new key
8. **`get_users()`**: Apply the `@api_key_required` decorator

### Key Concepts to Implement

#### 1. Generating API Keys with `secrets`

```python
import secrets

API_KEY_PREFIX = 'sk_'

def generate_api_key():
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

def hash_api_key(api_key):
    return hashlib.sha256(api_key.encode('utf-8')).hexdigest()

users[username] = {
    'password': generate_password_hash(password),  # slow, salted hash
    'api_key_hash': hash_api_key(api_key)          # fast SHA-256
}
```

**Why is a fast hash (SHA-256) fine for API keys but NOT for passwords?**
- An attacker who steals a hash tries to **guess** the input and hash each guess
- A password is short and chosen by a human (`secret123`). With a fast hash, billions of guesses per second find it quickly. Passwords need a **slow, salted** hash: werkzeug's `generate_password_hash` (scrypt/pbkdf2) makes every guess expensive
- An API key has 256 random bits. There is nothing to guess: even at billions of guesses per second it would take far longer than the age of the universe. A slow hash adds nothing, and a fast one keeps every request fast (the key is checked on **every** request, the password only at login)

This is also why the server **shows the key only once**: after registration it no longer has it.

#### 3. Constant-Time Comparison

```python
import hmac

def find_user_by_api_key(api_key):
    candidate_hash = hash_api_key(api_key)

    for username, user_data in users.items():
        stored_hash = user_data.get('api_key_hash')
        if stored_hash and hmac.compare_digest(stored_hash, candidate_hash):
            return username

    return None
```

`==` stops at the first different character, so a comparison takes slightly longer the more characters match. Measuring that time difference (a **timing attack**) can leak a secret character by character. `hmac.compare_digest()` always takes the same time. Use it whenever you compare secrets.

> In a real database you would put an index on `api_key_hash` and look it up directly (`WHERE api_key_hash = ?`). That is safe too: the attacker cannot choose the hash of their guess, so timing reveals nothing useful.

#### 4. Creating Custom Decorators

**What is a decorator?**
A decorator is a function that wraps another function to add extra behavior.

**Basic decorator pattern:**
```python
from functools import wraps

def my_decorator(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Code before the function
        print("Before function call")

        # Call the original function
        result = f(*args, **kwargs)

        # Code after the function
        print("After function call")

        return result
    return decorated_function

@my_decorator
def hello():
    print("Hello!")
```

**For API key validation:**
```python
def api_key_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        # 1. Extract API key from headers
        api_key = request.headers.get('X-API-Key')

        # 2. Validate it exists
        if not api_key:
            return jsonify({'error': 'API key missing'}), 401

        # 3. Look it up by hash
        if find_user_by_api_key(api_key) is None:
            return jsonify({'error': 'Invalid API key'}), 401

        # 4. If valid, call the original function
        return f(*args, **kwargs)

    return decorated
```

#### 5. Reading Headers in Flask

```python
from flask import request

# Get a specific header (the lookup is case-insensitive)
api_key = request.headers.get('X-API-Key')

# Check if header exists
if 'X-API-Key' in request.headers:
    print("API key present")

# Get all headers
all_headers = request.headers
```

**Common API key header names:**
- `X-API-Key` (most common; also written `x-api-key`, it is the same header)
- `Authorization: Bearer YOUR_KEY`
- `api-key`

**Never** send the key in the URL (`/users?api_key=...`): URLs are stored in logs, browser history and proxy caches.

#### 6. Rotating and Revoking Keys

```python
@app.route('/api-key/rotate', methods=['POST'])
@auth.login_required          # username + password (Basic Auth)
def rotate_api_key():
    current_user = auth.current_user()
    new_api_key = generate_api_key()

    # Overwriting the hash invalidates the old key immediately
    users[current_user]['api_key_hash'] = hash_api_key(new_api_key)

    return jsonify({'api_key': new_api_key}), 200   # shown once


@app.route('/api-key', methods=['DELETE'])
@auth.login_required
def revoke_api_key():
    users[auth.current_user()]['api_key_hash'] = None
    return jsonify({'message': 'API key revoked'}), 200
```

- **Rotate** regularly, and always when a key may have leaked or someone who knew it leaves the team
- **Revoke** when a key leaked and you do not need a replacement yet
- Rotation uses `POST` because it **creates** a new key on every call

---

## Testing the API

> The commands below use `curl` with `bash` quoting. In **Windows CMD** use `example/commands_cmd.txt`, and in **PowerShell** use `example/commands_powershell.txt`.

### 1. Register a New User

```bash
curl -X POST -H "Content-Type: application/json" \
     -d '{"username":"alice","password":"secret123"}' \
     http://127.0.0.1:5000/register
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
     http://127.0.0.1:5000/users
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
     http://127.0.0.1:5000/users
```

**Expected Response (401):**
```json
{
  "error": "Invalid API key",
  "message": "API key not recognized"
}
```

### 4. Test with Missing API Key

```bash
curl http://127.0.0.1:5000/users
```

**Expected Response (401):**
```json
{
  "error": "API key missing",
  "message": "Include X-API-Key header"
}
```

### 5. Rotate Your API Key

```bash
curl -X POST -u alice:secret123 http://127.0.0.1:5000/api-key/rotate
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
curl -X DELETE -u alice:secret123 http://127.0.0.1:5000/api-key
```

**Expected Response:**
```json
{
  "message": "API key revoked. Use POST /api-key/rotate to get a new one.",
  "username": "alice"
}
```

---

## Understanding the Code Flow

### Registration Flow

```python
@app.route('/register', methods=['POST'])
def register():
    # 1. Get username and password from JSON body
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')

    # 2. Validate input
    if not username or not password:
        return jsonify({'error': 'Username and password required'}), 400

    # 3. Check if user exists
    if username in users:
        return jsonify({'error': 'User already exists'}), 409

    # 4. Generate a random API key
    api_key = generate_api_key()

    # 5. Store the password hash and the API key HASH
    users[username] = {
        'password': generate_password_hash(password),
        'api_key_hash': hash_api_key(api_key)
    }

    # 6. Return the API key to the client (the only time)
    return jsonify({'api_key': api_key}), 201
```

### API Key Validation Flow

```python
def api_key_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        # 1. Extract API key from headers
        api_key = request.headers.get('X-API-Key')

        # 2. Check if present
        if not api_key:
            return error_response('API key missing'), 401

        # 3. Hash it and compare with the stored hashes (constant time)
        if find_user_by_api_key(api_key) is None:
            return error_response('Invalid API key'), 401

        # 4. Valid! Call the protected function
        return f(*args, **kwargs)

    return decorated
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
  "error": "Invalid API key"
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
curl -H "X-API-Key: $API_KEY" http://127.0.0.1:5000/users
```

### Issue 3: API Key Missing Error

**Symptom:**
```json
{
  "error": "API key missing"
}
```

**Solution:**
Make sure you're including the `-H` flag with curl:
```bash
# Wrong (no header)
curl http://127.0.0.1:5000/users

# Wrong (key in the URL: ignored by the server, and it ends up in logs)
curl "http://127.0.0.1:5000/users?api_key=YOUR_KEY"

# Right
curl -H "X-API-Key: YOUR_KEY" http://127.0.0.1:5000/users
```

### Issue 4: Decorator Not Working

**Symptom:**
Protected endpoint accessible without API key.

**Solution:**
Make sure decorator is applied:
```python
# Wrong
@app.route('/users', methods=['GET'])
def get_users():  # Missing @api_key_required
    ...

# Right
@app.route('/users', methods=['GET'])
@api_key_required  # Decorator applied
def get_users():
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
- ✅ Use custom decorator for API key protection
- ✅ Allow multiple users with unique API keys

---

## Stretch Goals

Once you complete the basic implementation:

### 1. Add a Grace Period on Rotation

Rotating a key breaks every client that still uses the old one. Keep the previous hash valid for a short time so clients can switch:

```python
from datetime import datetime, timedelta

users[current_user]['previous_api_key_hash'] = users[current_user]['api_key_hash']
users[current_user]['previous_valid_until'] = datetime.now() + timedelta(hours=24)
users[current_user]['api_key_hash'] = hash_api_key(new_api_key)
```

Then accept either hash in `find_user_by_api_key()` while `previous_valid_until` has not passed.

### 2. Add API Key Expiration

Track when API keys were created and expire old ones:

```python
from datetime import datetime, timedelta

# On registration and rotation
users[username] = {
    'password': hashed_password,
    'api_key_hash': hash_api_key(api_key),
    'key_created_at': datetime.now()
}

# In the decorator, after finding the user
created = users[username]['key_created_at']
if datetime.now() - created > timedelta(days=90):
    return jsonify({'error': 'API key expired', 'message': 'Rotate your key'}), 401
```

### 3. Add Rate Limiting

Track API calls per key and limit requests (Exercise 12 does this properly with Flask-Limiter):

```python
from collections import defaultdict
from datetime import datetime, timedelta

# Track requests per user (never use the plain key as a dictionary key)
api_calls = defaultdict(list)  # {username: [timestamp1, timestamp2, ...]}

def api_key_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        api_key = request.headers.get('X-API-Key')
        username = find_user_by_api_key(api_key) if api_key else None
        if username is None:
            return jsonify({'error': 'Invalid API key'}), 401

        # Rate limiting: Max 10 requests per minute
        now = datetime.now()
        minute_ago = now - timedelta(minutes=1)

        # Remove old calls
        api_calls[username] = [t for t in api_calls[username] if t > minute_ago]

        # Check limit
        if len(api_calls[username]) >= 10:
            return jsonify({'error': 'Rate limit exceeded'}), 429

        # Record this call
        api_calls[username].append(now)

        return f(*args, **kwargs)

    return decorated
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
    'alice': {
        'password': 'hashed',
        'api_keys': {
            'k_1a2b': {'hash': 'sha256...', 'scopes': ['read', 'write']},
            'k_3c4d': {'hash': 'sha256...', 'scopes': ['read']}  # Read-only key
        }
    }
}

def api_key_required(scopes=None):
    def decorator(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            api_key = request.headers.get('X-API-Key', '')
            candidate_hash = hash_api_key(api_key)

            # Validate API key and check scopes
            for username, user_data in users.items():
                for key_id, key_info in user_data['api_keys'].items():
                    if hmac.compare_digest(key_info['hash'], candidate_hash):
                        if scopes and not set(scopes).issubset(key_info['scopes']):
                            return jsonify({'error': 'Insufficient permissions'}), 403
                        return f(*args, **kwargs)

            return jsonify({'error': 'Invalid API key'}), 401

        return decorated
    return decorator

# Usage
@app.route('/users', methods=['GET'])
@api_key_required(scopes=['read'])
def get_users():
    ...

@app.route('/users', methods=['POST'])
@api_key_required(scopes=['write'])
def create_user():
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

### Use JWT (Next Exercise) When:

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
   - Use `request.headers.get('X-API-Key')`
   - Headers are case-insensitive (`x-api-key` is the same header)

5. **Security Best Practices**
   - Hash passwords and API keys, never store plain text
   - Keep keys in environment variables or a secrets manager, never in code or Git
   - Rotate keys regularly and revoke leaked ones immediately
   - Always use HTTPS in production

**Next Steps:**
- **Exercise 06**: JWT Authentication (stateless tokens)
- **Exercise 07**: Consuming External Public APIs
- **Exercise 08**: CRUD Operations

Good luck! 🔑
