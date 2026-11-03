# Exercise 14: Rate Limiting and API Security

## Quick Start

```bash
cd exercises/14-rate-limiting
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
fastapi dev app.py
```

## Objective

Learn to protect your API from abuse using **rate limiting** with slowapi:

- **Prevent Abuse**: Protect your API from malicious users and bots
- **Resource Management**: Control server load and prevent resource exhaustion
- **Fair Usage**: Ensure all users get fair access to your API
- **Security**: Prevent brute force attacks on authentication endpoints
- **Cost Control**: Limit expensive operations (database queries, external API calls)

## What is Rate Limiting?

**Rate limiting** restricts the number of requests a client can make to your API within a specific time window.

**Real-world examples** (at the time of writing, check each provider's docs):
- **Twitter API**: 300 requests per 15 minutes (free tier)
- **GitHub API**: 60 requests per hour (unauthenticated), 5000/hour (authenticated)
- **Stripe API**: 100 requests per second
- **OpenAI API**: Varies by plan and endpoint

**Why rate limiting matters:**
1. **Prevents DoS attacks**: Malicious users can't overwhelm your server
2. **Stops brute force**: Limits password guessing attempts
3. **Controls costs**: Prevents expensive operations from draining resources
4. **Ensures availability**: Protects the API for all legitimate users
5. **Compliance**: Some regulations require rate limiting (e.g., payment APIs)

## Prerequisites

Before starting this exercise, complete:
- **Exercise 11**: JWT Authentication (this exercise builds on JWT concepts)
- **Exercise 04**: API Fundamentals (understanding HTTP status codes)

## What You'll Learn

1. **slowapi library**: Rate limiting for FastAPI (a port of the popular Flask-Limiter)
2. **Rate limit strategies**:
   - Per IP address (default)
   - Per user (authenticated requests)
   - Per endpoint (different limits for different routes)
3. **HTTP 429 status code**: "Too Many Requests"
4. **Rate limit headers**: `X-RateLimit-Limit`, `X-RateLimit-Remaining`, `Retry-After`
5. **Decorator patterns**: `@limiter.limit()`, `@limiter.exempt`
6. **Custom error handlers**: User-friendly rate limit messages
7. **Security best practices**: Protecting sensitive endpoints

## Installation

The exercise requires these dependencies (already in `requirements.txt`):

```txt
fastapi[standard]==0.162.0
bcrypt==5.0.0
PyJWT==2.15.1
slowapi==0.1.10
```

Install them:
```bash
pip install -r requirements.txt
```

## How slowapi Works

### Basic Concept

```python
from slowapi import Limiter
from slowapi.middleware import SlowAPIMiddleware
from slowapi.util import get_remote_address

limiter = Limiter(
    key_func=get_remote_address,  # Identify clients by IP address
    default_limits=["200/day", "50/hour"]  # Applied to routes without their own limit
)
app.state.limiter = limiter  # slowapi looks the limiter up here
app.add_middleware(SlowAPIMiddleware)  # applies the default limits to every route
```

**Key components:**
- `key_func`: How to identify clients (IP address, user ID, API key, etc.)
- `default_limits`: Fallback limits applied to all routes unless overridden
- `storage_uri`: Where to store rate limit data (memory, Redis, etc.)

**Two things slowapi needs from your route functions** (`app.py` already has them):
- Every route with `@limiter.limit(...)` must take a `request: Request` parameter: slowapi reads the client's address from it.
- A route that returns a plain dict must also take `response: Response`: that is the object slowapi adds the `X-RateLimit-*` headers to on a successful call (on a `429` the error handler adds them).

### Rate Limit Syntax

slowapi uses a short string format, `<amount>/<period>`:

```python
"5/minute"      # 5 requests per minute
"100/hour"      # 100 requests per hour
"1000/day"      # 1000 requests per day
"1/second"      # 1 request per second
"5 per minute"  # Alternative syntax (same as "5/minute")
```

**You can combine limits:**
```python
@limiter.limit("5/minute;100/hour;1000/day")
```

This enforces ALL limits simultaneously - whichever is hit first triggers the rate limit.

## Exercise Structure

The provided `app.py` has a partially complete API with TODOs:

- `app.py` - Starter file with blanks to fill in
- `example/example14.py` - Complete reference solution
- `requirements.txt` - Dependencies
- `readme14.md` - This instruction file

Fill the blanks from top to bottom. The app does not start until `key_func`, `default_limits` and the four `@limiter.limit(_____)` blanks are filled in (Python evaluates them when the file is loaded). The last TODO, the missing `@limiter.exempt`, does not stop the app from starting, but until you add it `/api/unlimited` is limited by the default limits.

## Part 1: Understanding the Code Structure (10 minutes)

### Step 1.1: Review the Setup

Open `app.py` and examine the setup:

```python
from slowapi import Limiter
from slowapi.util import get_remote_address

# TODO: Initialize slowapi
# Hint: limiter = Limiter(key_func=get_remote_address, default_limits=["200/day", "50/hour"])
limiter = Limiter(
    key_func=_____,  # TODO: What function determines who is making the request?
    default_limits=_____,  # TODO: Set default limits (e.g., ["200/day", "50/hour"])
    headers_enabled=True,  # send X-RateLimit-* and Retry-After headers
    storage_uri="memory://",  # in-memory storage (use Redis in production)
)
```

**Your task:**
1. Fill in `key_func` with `get_remote_address` (tracks by IP address)
2. Fill in `default_limits` with `["200/day", "50/hour"]`

**Why these defaults?**
- `200/day`: Prevents a single IP from making thousands of requests
- `50/hour`: More granular control within the day limit
- Both limits are enforced - hitting either one triggers rate limiting

### Step 1.2: Understand Key Function

The `key_func` parameter determines **who** is making the request.

**Common strategies:**

```python
# Strategy 1: By IP address (simple, works for unauthenticated requests)
from slowapi.util import get_remote_address
key_func=get_remote_address

# Strategy 2: By authenticated user (requires JWT/session)
def get_user_id(request: Request) -> str:
    try:
        token = request.headers.get("Authorization", "").removeprefix("Bearer ")
        return jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALG])["sub"]  # JWT username
    except jwt.InvalidTokenError:
        return get_remote_address(request)  # Fall back to IP if not authenticated

key_func=get_user_id
```

For this exercise, we'll use **IP address** since it's simpler and works for both authenticated and unauthenticated endpoints.

## Part 2: Implementing Rate Limits (30 minutes)

### Task 2.1: Protect Registration Endpoint

Registration endpoints are often targeted by bots creating spam accounts.

**Find this code in `app.py`:**

```python
@app.post("/register", status_code=201)
# TODO: Add rate limit to prevent spam registrations
# Hint: @limiter.limit("5/hour")
@limiter.limit(_____)
def register(request: Request, response: Response, data: UserCreate) -> dict[str, str]:
    # ... registration logic
```

**Your task:**
Fill in the blank with: `"5/hour"`

`@limiter.limit` goes directly under the route decorator, and the function must take `request: Request`.

**Why 5 per hour?**
- Legitimate users rarely need to create multiple accounts
- Prevents automated bot registration
- Still allows a user to retry if they make a mistake

**Testing:**
```bash
# Try registering 6 times in quick succession - the 6th should fail
for i in {1..6}; do
  curl -X POST http://127.0.0.1:8000/register \
    -H "Content-Type: application/json" \
    -d "{\"username\":\"user$i\",\"password\":\"pass1234\"}"
  echo ""
done
```

Windows PowerShell (5.1 and 7):
```powershell
for ($i = 1; $i -le 6; $i++) {
  $body = @{ username = "user$i"; password = "pass1234" } | ConvertTo-Json
  try {
    $r = Invoke-WebRequest -UseBasicParsing -Method Post -Uri "http://127.0.0.1:8000/register" `
      -ContentType "application/json" -Body $body
    Write-Host "user$i -> $($r.StatusCode)"
  } catch {
    # Windows PowerShell 5.1 throws on any non-2xx status: read the status code from the error
    $resp = $_.Exception.Response
    if (-not $resp) { throw }  # no HTTP response at all (is the app running?)
    Write-Host "user$i -> $($resp.StatusCode.value__)"
  }
}
```

**Expected:** First 5 succeed, 6th returns HTTP 429 (Rate limit exceeded)

> This test uses up the hour's 5 registrations for your IP. Restart the app before Task 3.2, or its registrations will also return 429.

### Task 2.2: Protect Login Endpoint

Login endpoints are prime targets for **brute force attacks** (trying many passwords).

**Find this code:**

```python
@app.post("/login")
# TODO: Add rate limit to prevent brute force attacks
# Hint: @limiter.limit("10/minute")
@limiter.limit(_____)
def login(request: Request, response: Response, data: Credentials) -> dict[str, str]:
    # ... login logic
```

**Your task:**
Fill in: `"10/minute"`

**Why 10 per minute?**
- Allows legitimate users to retry incorrect passwords
- Prevents automated password guessing
- Industry standard for authentication endpoints

**Real-world comparison** (at the time of writing, check each provider's docs):
- **GitHub**: 5 failed login attempts triggers CAPTCHA
- **AWS**: Throttles after 5 failed attempts
- **Google**: Uses adaptive rate limiting (slows down after failures)

### Task 2.3: General API Endpoint

Most API endpoints need moderate rate limiting.

**Find this code:**

```python
@app.get("/api/data")
# TODO: Add rate limit for general API usage
# Hint: @limiter.limit("20/minute")
@limiter.limit(_____)
def get_data(
    request: Request,
    response: Response,
    creds: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer)],
) -> dict:
    # ... data retrieval logic
```

**Your task:**
Fill in: `"20/minute"`

**Why 20 per minute?**
- Allows normal application usage
- Prevents a single user from overwhelming the server
- Balances usability with protection

### Task 2.4: Expensive Operations

Some endpoints are **resource-intensive** (complex database queries, external API calls, AI processing).

**Find this code:**

```python
@app.get("/api/search")
# TODO: Add strict rate limit for expensive operations
# Hint: @limiter.limit("5/minute")
@limiter.limit(_____)
def search(
    request: Request,
    response: Response,
    q: Annotated[str, Query(min_length=1)],
    creds: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer)],
) -> dict:
    # ... expensive search operation
```

**Your task:**
Fill in: `"5/minute"`

**Why stricter limits?**
- Search often involves database scans or external API calls
- Prevents resource exhaustion
- Encourages efficient client-side caching

**Real examples** (at the time of writing, check each provider's docs):
- **Algolia Search**: 10,000 requests/month (free tier)
- **Elasticsearch**: Often limited to 5-10 concurrent searches
- **OpenAI GPT-4**: 3 requests/minute (free tier)

### Task 2.5: Exempt Endpoints

Some endpoints should **never** be rate limited.

**Find this code:**

```python
@app.get("/api/unlimited")
# TODO: Exempt this endpoint from rate limiting by adding the @limiter.exempt decorator above this line
def unlimited(creds: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer)]) -> dict[str, str]:
    # ... critical operation
```

**Your task:**
Add: `@limiter.exempt`

**When to exempt endpoints:**
- Health checks (monitoring systems need reliable access)
- Critical emergency operations (e.g., "delete my account")
- Internal microservice communication
- Webhooks from trusted sources

**Warning:** Use exemptions sparingly - even "unlimited" endpoints can be abused!

## Part 3: Testing Rate Limits (30 minutes)

### Task 3.1: Run the Application

```bash
cd exercises/14-rate-limiting
fastapi dev app.py
```

You should see the server start on `http://127.0.0.1:8000`. The endpoints and their limits:

```
  POST   /register          - Register new user (5/hour)
  POST   /login             - Login (10/minute)
  GET    /api/data          - Get data (20/minute)
  GET    /api/search?q=...  - Search (5/minute)
  GET    /api/unlimited     - No rate limit
  GET    /api/stats         - Get stats (10/minute)
  GET    /health            - Health check (no limit)
```

Default limits for any other route: 200/day and 50/hour. Swagger UI is at `http://127.0.0.1:8000/docs`. `/docs` and
`/openapi.json` are "other routes" too, so the default limits apply to them (slowapi keeps a separate default counter
per route, and Swagger UI fetches `/openapi.json` on every reload): reload `/docs` about 50 times in an hour and it answers 429.

### Task 3.2: Test Registration Rate Limit

> **Already ran the Task 2.1 test?** Those 6 attempts used up this hour's 5 registrations for your IP, so Step 1 below would return 429, even with a new username, because the limit is per client IP, not per username. Restart the app first (`Ctrl+C`, then `fastapi dev app.py`): the `memory://` storage starts empty again (counters *and* registered users).

**Step 1: Register a user (should succeed):**
```bash
curl -X POST http://127.0.0.1:8000/register \
  -H "Content-Type: application/json" \
  -d '{"username":"alice","password":"password123"}'
```

Windows PowerShell (5.1 and 7):
```powershell
$body = @{ username = "alice"; password = "password123" } | ConvertTo-Json
Invoke-RestMethod -Method Post -Uri "http://127.0.0.1:8000/register" -ContentType "application/json" -Body $body
```

**Expected response:**
```json
{
  "message": "User alice registered successfully"
}
```

**Step 2: Try to register 5 more users rapidly:**

Windows PowerShell (5.1 and 7):
```powershell
for ($i = 1; $i -le 5; $i++) {
  $body = @{ username = "user$i"; password = "pass1234" } | ConvertTo-Json
  try {
    $r = Invoke-WebRequest -UseBasicParsing -Method Post -Uri "http://127.0.0.1:8000/register" `
      -ContentType "application/json" -Body $body
    Write-Host "user$i -> $($r.StatusCode)  X-RateLimit-Remaining: $($r.Headers['X-RateLimit-Remaining'])"
  } catch {
    # Windows PowerShell 5.1 throws on any non-2xx status: read the response from the error
    $resp = $_.Exception.Response
    if (-not $resp) { throw }  # no HTTP response at all (is the app running?)
    Write-Host "user$i -> $($resp.StatusCode.value__)  Retry-After: $($resp.Headers.GetValues('Retry-After'))"
    Write-Host $_.ErrorDetails.Message  # the JSON body of the error
  }
}
```

Mac/Linux:
```bash
for i in {1..5}; do
  curl -X POST http://127.0.0.1:8000/register \
    -H "Content-Type: application/json" \
    -d "{\"username\":\"user$i\",\"password\":\"pass1234\"}"
  echo ""
done
```

**Expected:** Step 1 already used one of the 5 registrations, so `user1`-`user4` succeed (201) and `user5` gets:
```json
{
  "error": "Rate limit exceeded",
  "message": "5 per 1 hour",
  "retry_after_seconds": 3599
}
```

**HTTP Status:** `429 Too Many Requests`

`retry_after_seconds` (and the `Retry-After` header) is the number of seconds until the one-hour window resets: about 3600 right after Step 1, and lower the longer you wait.

### Task 3.3: Inspect Rate Limit Headers

Successful responses and `429` responses carry the limit headers (the `429` also has `Retry-After`). The `401` answers of `/login` do not: slowapi adds the headers only when the route returns normally or when the rate limit is exceeded, so a failed login shows no `X-RateLimit-*`. Exempt endpoints such as `/health` don't have a limit, so they don't send these headers.

You need an access token for `/api/data`: run **Task 3.4 Step 1** first, then come back here.

**Make a request to a limited endpoint:**
```bash
curl -i http://127.0.0.1:8000/api/data -H "Authorization: Bearer YOUR_TOKEN"
```

Windows PowerShell (5.1 and 7), with `$TOKEN` set in Task 3.4 Step 1:
```powershell
$r = Invoke-WebRequest -UseBasicParsing -Uri "http://127.0.0.1:8000/api/data" -Headers @{ Authorization = "Bearer $TOKEN" }
$r.StatusCode
'X-RateLimit-Limit', 'X-RateLimit-Remaining', 'X-RateLimit-Reset', 'Retry-After' |
  ForEach-Object { "${_}: $($r.Headers[$_])" }
```
> You can also use `curl.exe -i ...` (not `curl`: in PowerShell 5.1, `curl` is an alias of `Invoke-WebRequest`).

**Look for these headers:**
```
X-RateLimit-Limit: 20
X-RateLimit-Remaining: 19
X-RateLimit-Reset: 1704672000.51
Retry-After: 60
```

**Header meanings:**
- `X-RateLimit-Limit`: Total requests allowed in the window
- `X-RateLimit-Remaining`: Requests left before hitting the limit
- `X-RateLimit-Reset`: Unix timestamp when the limit resets (slowapi may include decimals)
- `Retry-After`: Seconds until the window resets - on a `429` this is how long the client must wait. slowapi also
  sends it on successful responses, but per RFC 9110 it only has meaning on a `429` (and `503`/`3xx`), so standard
  clients ignore it on a `200`

**Clients should use these headers to:**
1. Display remaining quota to users
2. Automatically retry after the cooldown period
3. Implement exponential backoff

### Task 3.4: Test Login Rate Limit

**Step 1: Login successfully:**
```bash
curl -X POST http://127.0.0.1:8000/login \
  -H "Content-Type: application/json" \
  -d '{"username":"alice","password":"password123"}'
```

Save the `access_token` from the response.

Windows PowerShell (5.1 and 7) - this saves the token in `$TOKEN` for the next tasks:
```powershell
$body = @{ username = "alice"; password = "password123" } | ConvertTo-Json
$TOKEN = (Invoke-RestMethod -Method Post -Uri "http://127.0.0.1:8000/login" -ContentType "application/json" -Body $body).access_token
$TOKEN
```

**Step 2: Simulate brute force attack (11 rapid login attempts):**

Windows PowerShell (5.1 and 7):
```powershell
$body = @{ username = "alice"; password = "wrongpassword" } | ConvertTo-Json
for ($i = 1; $i -le 11; $i++) {
  try {
    $r = Invoke-WebRequest -UseBasicParsing -Method Post -Uri "http://127.0.0.1:8000/login" `
      -ContentType "application/json" -Body $body
    Write-Host "Attempt $i -> $($r.StatusCode)"
  } catch {
    $resp = $_.Exception.Response
    if (-not $resp) { throw }
    $code = $resp.StatusCode.value__
    if ($code -eq 429) {
      Write-Host "Attempt $i -> $code  X-RateLimit-Remaining: $($resp.Headers.GetValues('X-RateLimit-Remaining'))  Retry-After: $($resp.Headers.GetValues('Retry-After'))"
    } else {
      Write-Host "Attempt $i -> $code"
    }
  }
}
```

Mac/Linux:
```bash
for i in {1..11}; do
  echo "Attempt $i"
  curl -X POST http://127.0.0.1:8000/login \
    -H "Content-Type: application/json" \
    -d '{"username":"alice","password":"wrongpassword"}'
  echo ""
done
```

**Expected:** Every request to `/login` counts towards the 10 per minute, successful or not, and the Step 1 login already used one. So attempts 1-9 return 401 (Unauthorized) and attempts 10-11 return 429 (Rate limit exceeded).

> If more than a minute passed between Step 1 and Step 2, the window has already reset: attempts 1-10 return 401 and attempt 11 returns 429.

**Security benefit:** An attacker can only try 10 passwords per minute, making brute force impractical.

### Task 3.5: Test Authenticated Endpoints

**Step 1: Get a valid token:**

Reuse the token from Task 3.4 Step 1 (it is valid for 1 hour). If you need a new one, **wait one minute first**: Task 3.4 used up this minute's logins, so logging in right now returns 429.
```bash
curl -X POST http://127.0.0.1:8000/login \
  -H "Content-Type: application/json" \
  -d '{"username":"alice","password":"password123"}'
```

Copy the `access_token`. (In PowerShell, run the Task 3.4 Step 1 commands again to refresh `$TOKEN`.)

**Step 2: Test the `/api/data` endpoint (limit: 20 per minute):**

Windows PowerShell (5.1 and 7):
```powershell
# Only if $TOKEN is not set yet in this window:
# $TOKEN = "YOUR_TOKEN_HERE"

for ($i = 1; $i -le 21; $i++) {
  try {
    $r = Invoke-WebRequest -UseBasicParsing -Uri "http://127.0.0.1:8000/api/data" `
      -Headers @{ Authorization = "Bearer $TOKEN" }
    Write-Host "Request $i -> $($r.StatusCode)  X-RateLimit-Remaining: $($r.Headers['X-RateLimit-Remaining'])"
  } catch {
    $resp = $_.Exception.Response
    if (-not $resp) { throw }
    Write-Host "Request $i -> $($resp.StatusCode.value__)  Retry-After: $($resp.Headers.GetValues('Retry-After'))"
  }
}
```

Mac/Linux:
```bash
# Replace YOUR_TOKEN_HERE with your actual token
TOKEN="YOUR_TOKEN_HERE"
for i in {1..21}; do
  echo "Request $i"
  curl http://127.0.0.1:8000/api/data \
    -H "Authorization: Bearer $TOKEN"
  echo ""
done
```

**Expected:** Requests 1-20 succeed, request 21 returns 429.

> If you called `/api/data` in Task 3.3 less than a minute ago, that request counts too, so the 429 arrives one request earlier.

### Task 3.6: Test Expensive Search Endpoint

**Test the strict limit on search (5 per minute):**

Windows PowerShell (5.1 and 7):
```powershell
for ($i = 1; $i -le 6; $i++) {
  try {
    $r = Invoke-WebRequest -UseBasicParsing -Uri "http://127.0.0.1:8000/api/search?q=test" `
      -Headers @{ Authorization = "Bearer $TOKEN" }
    Write-Host "Search $i -> $($r.StatusCode)  X-RateLimit-Remaining: $($r.Headers['X-RateLimit-Remaining'])"
  } catch {
    $resp = $_.Exception.Response
    if (-not $resp) { throw }
    Write-Host "Search $i -> $($resp.StatusCode.value__)  Retry-After: $($resp.Headers.GetValues('Retry-After'))"
  }
}
```

Mac/Linux:
```bash
TOKEN="YOUR_TOKEN_HERE"
for i in {1..6}; do
  echo "Search $i"
  curl "http://127.0.0.1:8000/api/search?q=test" \
    -H "Authorization: Bearer $TOKEN"
  echo ""
done
```

**Expected:** Searches 1-5 succeed, search 6 returns 429.

**Note:** The stricter limit (5 vs 20) simulates protecting an expensive operation.

### Task 3.7: Test Exempt Endpoint

**Test the unlimited endpoint:**

Make 100 requests rapidly - all should succeed.

Windows PowerShell (5.1 and 7):
```powershell
$ok = 0
for ($i = 1; $i -le 100; $i++) {
  $r = Invoke-WebRequest -UseBasicParsing -Uri "http://127.0.0.1:8000/api/unlimited" `
    -Headers @{ Authorization = "Bearer $TOKEN" }
  if ($r.StatusCode -eq 200) { $ok++ }
}
Write-Host "$ok of 100 requests returned 200"
```

Mac/Linux:
```bash
TOKEN="YOUR_TOKEN_HERE"
for i in {1..100}; do
  curl http://127.0.0.1:8000/api/unlimited \
    -H "Authorization: Bearer $TOKEN" -s | head -n 1
done
```

**Expected:** All 100 requests succeed - no rate limiting!

## Part 4: Understanding Rate Limit Strategies (20 minutes)

### Strategy 1: Per-IP Rate Limiting (Current Implementation)

**How it works:**
- Tracks requests by the client's IP address
- Uses `get_remote_address()` as the key function

**Pros:**
- Simple to implement
- Works for unauthenticated requests
- Protects against single-source attacks

**Cons:**
- Users behind the same NAT/proxy share the same limit
- Doesn't distinguish between authenticated users from the same IP
- Can block legitimate users in shared networks (offices, universities)

> **Behind a proxy:** if the app runs behind nginx, Railway, Render... `get_remote_address` sees the proxy's
> IP, so *every* user shares one bucket. `fastapi dev`/`fastapi run` (uvicorn) already read `X-Forwarded-For`, but only trust
> it from `127.0.0.1` (that is why ngrok, whose agent runs on your own machine, works out of the box). For a proxy on another
> machine, start the app with `--forwarded-allow-ips=<proxy ip>` so that `request.client.host` is the real client, or write a
> key function that reads `X-Forwarded-For` only when the request comes from your trusted proxy. slowapi's `get_ipaddr`
> trusts that header blindly, and any client can forge it.

**Use cases:**
- Public endpoints (registration, login)
- Anonymous APIs
- Simple applications

### Strategy 2: Per-User Rate Limiting

**How it works:**
- Tracks requests by authenticated user ID (from JWT)
- Falls back to IP for unauthenticated requests

**Implementation example:**
```python
def get_user_key(request: Request) -> str:
    """Use the JWT username if the token is valid, otherwise the IP address"""
    token = request.headers.get("Authorization", "").removeprefix("Bearer ")
    try:
        return jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALG])["sub"]
    except jwt.InvalidTokenError:
        return get_remote_address(request)

limiter = Limiter(
    key_func=get_user_key,  # Per-user tracking
    default_limits=["1000/day", "100/hour"]
)
```

**Pros:**
- Fair limits per user (not per IP)
- Users in shared networks don't affect each other
- Can offer different limits for different user tiers (free vs premium)

**Cons:**
- Requires authentication
- Doesn't protect unauthenticated endpoints
- Users can create multiple accounts to bypass limits
- The key falls back to the IP when the token is invalid, so a client that sends garbage tokens leaves the per-user
  bucket and lands in the IP one; in production reject invalid tokens before rate limiting, or key by IP + token

**Use cases:**
- SaaS APIs with user accounts
- Premium/tiered services
- Per-user quota systems

### Strategy 3: Tiered Rate Limiting (Advanced)

**How it works:**
- Different limits based on user role, subscription tier, or API key

**Implementation example:**
```python
def get_rate_limit(key: str) -> str:
    """Return different limits based on user role.
    slowapi calls this with the client key that key_func returned (here: the username, or the IP)."""
    if key not in users:
        return "10/hour"  # Unauthenticated users (the key is an IP address)

    role = users[key]["role"]
    if role == "admin":
        return "1000/hour"
    elif role == "premium":
        return "500/hour"
    else:  # free tier
        return "50/hour"

# Dynamic limit based on user (key_func must be a per-user one, such as get_user_key above)
@app.get("/api/data")
@limiter.limit(get_rate_limit)
def get_data(request: Request, response: Response):
    # ...
```

**Use cases:**
- Multi-tier SaaS platforms
- Freemium models
- Enterprise APIs

## Part 5: Best Practices (15 minutes)

### Best Practice 1: Use Different Limits for Different Endpoints

```python
# Generous limit for reading data
@app.get("/api/data")
@limiter.limit("100/minute")

# Strict limit for creating data
@app.post("/api/data")
@limiter.limit("10/minute")

# Very strict for expensive operations
@app.get("/api/export")
@limiter.limit("1/hour")
```

**Why?** Read operations are usually cheaper than writes, and some operations (exports, reports) are very expensive.

### Best Practice 2: Always Include Rate Limit Headers

Clients need to know their quota! slowapi sends these headers **only when `headers_enabled=True`** (already set in `app.py`):
- `X-RateLimit-Limit`
- `X-RateLimit-Remaining`
- `X-RateLimit-Reset`
- `Retry-After`

> The IETF is standardising `RateLimit` / `RateLimit-Policy` headers to replace the `X-RateLimit-*` de facto ones.

**Best practice for clients:**
```python
# Pseudo-code for API client
response = make_request()

if response.status == 429:
    retry_after = int(response.headers['Retry-After'])
    # Cap the wait and add jitter: if every client retried at the exact same second,
    # they would all hit the limit again together (thundering herd)
    sleep(min(retry_after, 60) + random.uniform(0, 1))
    retry_request()

remaining = response.headers['X-RateLimit-Remaining']
if remaining < 10:
    warn_user("Approaching rate limit")
```

### Best Practice 3: User-Friendly Error Messages

Don't just return "429 Too Many Requests" - explain what happened!

**Good error handler (already in `app.py`):**
```python
def rate_limit_handler(request: Request, exc: RateLimitExceeded) -> JSONResponse:
    # slowapi's own handler already builds the 429 and adds the headers
    # (this handler relies on headers_enabled=True in Limiter(...): without it there is no Retry-After)
    default = _rate_limit_exceeded_handler(request, exc)
    return JSONResponse(
        {
            "error": "Rate limit exceeded",
            "message": str(exc.detail),  # e.g., "5 per 1 hour"
            "retry_after_seconds": int(default.headers.get("Retry-After", "0")),  # same value as the Retry-After header
        },
        status_code=429,
        headers={k: v for k, v in default.headers.items() if k.lower().startswith(("retry-after", "x-ratelimit"))},
    )

app.add_exception_handler(RateLimitExceeded, rate_limit_handler)
```

**Example response:**
```json
{
  "error": "Rate limit exceeded",
  "message": "5 per 1 hour",
  "retry_after_seconds": 3540
}
```

### Best Practice 4: Exempt Critical Endpoints

```python
@app.get("/health")
@limiter.exempt  # Monitoring systems need reliable access
def health():
    return {"status": "ok"}

@app.post("/api/emergency-stop")
@limiter.exempt  # Critical safety operation
def emergency_stop(creds: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer)]):
    # Stop dangerous operation
    pass
```

**When to exempt:**
- Health checks (monitoring)
- Emergency/safety operations
- Internal microservice endpoints (use authentication instead)

### Best Practice 5: Use Redis in Production

For this exercise, we use in-memory storage:
```python
limiter = Limiter(
    key_func=get_remote_address,
    storage_uri="memory://"  # Simple, but doesn't scale
)
```

**In production, use Redis:**
```python
limiter = Limiter(
    key_func=get_remote_address,
    storage_uri="redis://localhost:6379"  # Shared across multiple servers
)
```

**Why Redis?**
- Shared rate limit counters across multiple API servers
- Persistent across app restarts
- Fast and reliable
- Industry standard

### Best Practice 6: Log Rate Limit Violations

Add logging to detect abuse:

```python
import logging

def rate_limit_handler(request: Request, exc: RateLimitExceeded) -> JSONResponse:
    # Log the violation
    logging.warning(
        f"Rate limit exceeded: IP={get_remote_address(request)}, "
        f"Path={request.url.path}, Limit={exc.detail}"
    )

    # Same response as the handler in app.py (keeps the Retry-After and X-RateLimit-* headers)
    default = _rate_limit_exceeded_handler(request, exc)
    return JSONResponse(
        {
            "error": "Rate limit exceeded",
            "message": str(exc.detail),
            "retry_after_seconds": int(default.headers.get("Retry-After", "0")),
        },
        status_code=429,
        headers={k: v for k, v in default.headers.items() if k.lower().startswith(("retry-after", "x-ratelimit"))},
    )
```

**Use logs to:**
- Identify abusive IPs
- Detect bot traffic
- Optimize rate limits based on real usage patterns

## Testing Checklist

**Basic Setup:**
- [ ] slowapi installed (`pip install -r requirements.txt`)
- [ ] App runs without errors (`fastapi dev app.py`)
- [ ] Health check endpoint accessible (`/health`)

**Rate Limit Implementation:**
- [ ] Limiter initialized with `get_remote_address` and default limits
- [ ] Registration endpoint limited to "5/hour"
- [ ] Login endpoint limited to "10/minute"
- [ ] Data endpoint limited to "20/minute"
- [ ] Search endpoint limited to "5/minute"
- [ ] Unlimited endpoint marked with `@limiter.exempt`

**Testing:**
- [ ] Registration limit enforced (6th attempt in an hour fails)
- [ ] Login limit enforced (11th attempt in a minute fails)
- [ ] Data endpoint limit enforced (21st request fails)
- [ ] Search limit enforced (6th search fails)
- [ ] Unlimited endpoint has no limit (100+ requests succeed)
- [ ] Rate limit headers present in responses
- [ ] 429 status code returned when limit exceeded
- [ ] Custom error handler returns JSON response

**Understanding:**
- [ ] Can explain when to use rate limiting
- [ ] Understands different rate limit strategies (per-IP vs per-user)
- [ ] Knows when to exempt endpoints
- [ ] Can choose appropriate limits for different operations

## Common Issues and Solutions

### Issue 1: Rate Limit Not Working

**Symptom:** Can make unlimited requests without getting 429 errors.

**Possible causes:**
1. **Wrong decorator position or missing `request`:**
   `@limiter.limit` goes directly under the route decorator, and the function must take `request: Request`:
   ```python
   # WRONG - the limiter decorates a function that FastAPI never registered
   # (it is above the route decorator), so nothing is limited
   @limiter.limit("5/minute")
   @app.get("/endpoint")
   def endpoint(request: Request, response: Response):
       pass

   # CORRECT
   @app.get("/endpoint")
   @limiter.limit("5/minute")
   def endpoint(request: Request, response: Response):
       pass
   ```
   Also note that FastAPI resolves `Depends(...)` parameters BEFORE running your function, and the limiter counts a request when your function starts. If the token check were a dependency that raises `401`, requests with a missing or invalid token would be rejected before the limiter counts them, so token guessing would never be limited. That is why `app.py` only receives the token in the parameter and checks it inside the function body. For the same reason, requests that fail body or query validation (`422`) are rejected by FastAPI before the limiter counts them, so a flood of malformed JSON to `/login` is not limited by these decorators.

2. **Endpoint marked as exempt:**
   Check if `@limiter.exempt` is applied (intentionally or by mistake).

3. **Limits too generous:**
   "1000/minute" won't trigger during manual testing - use small limits for testing.

### Issue 2: Rate Limit Resets Too Quickly

**Symptom:** After hitting the limit, it resets immediately instead of waiting the full window.

**Cause:** Restarting the app (or saving `app.py`, which makes `fastapi dev` reload it) clears in-memory rate limit counters.

**Solution:** This is expected behavior with `memory://` storage. In production, use Redis for persistent counters.

### Issue 3: Multiple Users from Same IP Share Limit

**Symptom:** Two users on the same network (office, university) share the same rate limit.

**Cause:** Using `get_remote_address()` (IP-based) instead of per-user tracking. The same happens to *everyone* when the app runs behind a reverse proxy on another machine (nginx, Railway, Render): the app only sees the proxy's IP.

**Solution:** Implement per-user rate limiting (see Part 4, Strategy 2). Behind a proxy, start the app with `--forwarded-allow-ips=<proxy ip>`, or read `X-Forwarded-For` only from your trusted proxy (see the note in Strategy 1).

### Issue 4: Rate Limit Headers Not Showing

**Symptom:** No `X-RateLimit-*` headers in responses.

**Causes:**
1. slowapi only sends them when `headers_enabled=True` is passed to `Limiter(...)` (it is off by default).
2. The endpoint is exempt (e.g. `/health`): no limit, so no headers. A limited route that returns a dict also needs the `response: Response` parameter, or its successful responses have no headers.
3. Your client hides headers: use `curl -i` (`curl.exe -i` in PowerShell) or the browser DevTools Network tab.

### Issue 5: "429 Too Many Requests" for Health Checks

**Symptom:** Monitoring system gets 429 errors when checking `/health`.

**Solution:** Exempt the health check endpoint:
```python
@app.get("/health")
@limiter.exempt
def health():
    return {"status": "ok"}
```

## Real-World Rate Limiting Examples

### Example 1: GitHub API

**Free tier (unauthenticated):**
- 60 requests per hour

**Authenticated:**
- 5,000 requests per hour

**Search API (special limit):**
- 10 requests per minute (stricter because search is expensive)

**How they communicate limits:**
```
X-RateLimit-Limit: 5000
X-RateLimit-Remaining: 4999
X-RateLimit-Reset: 1704672000
X-RateLimit-Resource: core
```

### Example 2: Twitter API v2

Figures at the time of writing (check the provider's docs, these tiers change often).

**Free tier:**
- 500,000 Tweets read per month
- 1,667 Tweets per hour

**Basic tier ($100/month):**
- 10,000,000 Tweets per month

**How they enforce:**
- Returns 429 with `x-rate-limit-reset` header
- Clients must wait until reset time before retrying

### Example 3: Stripe API

**Limits:**
- 100 read requests per second
- 100 write requests per second (stricter in practice)

**Special handling:**
- Payment endpoints have stricter limits
- Test mode has separate limits from live mode

**How they handle overages:**
- 429 status code
- Exponential backoff recommended
- SDKs automatically retry with backoff

## Beyond This Exercise

### Next Steps

1. **Exercise 15+**: Apply rate limiting to your final project API
2. **Production deployment**: Configure Redis for rate limit storage
3. **Monitoring**: Set up alerts for rate limit violations
4. **Analytics**: Track API usage patterns to optimize limits

### Advanced Topics (Beyond This Course)

1. **Distributed Rate Limiting**:
   - Redis Cluster for high-availability
   - Consistent hashing for sharding

2. **Adaptive Rate Limiting**:
   - Increase limits for trusted users
   - Decrease limits for suspicious IPs
   - Machine learning-based anomaly detection

3. **Token Bucket Algorithm**:
   - More sophisticated than fixed windows
   - Allows burst traffic
   - Refills at a steady rate

4. **Geographic Rate Limiting**:
   - Different limits by region
   - Stricter limits for high-risk countries
   - GeoIP-based blocking

5. **Cost-Based Rate Limiting**:
   - Assign "cost" to each endpoint
   - Track total cost instead of request count
   - Example: 1 search = 5 points, 1 read = 1 point

## Additional Resources

### Official Documentation
- **[slowapi Docs](https://slowapi.readthedocs.io/)** - Library reference (slowapi is a port of [Flask-Limiter](https://flask-limiter.readthedocs.io/))
- **[RFC 6585](https://tools.ietf.org/html/rfc6585)** - HTTP 429 status code specification
- **[Redis](https://redis.io/)** - In-memory data store for production

### Tutorials
- [Rate Limiting Best Practices](https://nordicapis.com/everything-you-need-to-know-about-api-rate-limiting/)
- [GitHub API Rate Limiting](https://docs.github.com/en/rest/overview/resources-in-the-rest-api#rate-limiting)

### Alternative Libraries
- **[django-ratelimit](https://django-ratelimit.readthedocs.io/)** - For Django applications
- **[express-rate-limit](https://github.com/nfriedly/express-rate-limit)** - For Node.js/Express

## Deliverables

When you complete this exercise, you should have:

1. **Completed `app.py`**:
   - All TODOs filled in correctly
   - Limiter initialized with proper key function and defaults
   - All endpoints have appropriate rate limits
   - Exempt endpoint configured

2. **Testing Evidence**:
   - Screenshots or logs showing rate limit enforcement
   - 429 responses when limits exceeded
   - Rate limit headers in successful responses

3. **Understanding**:
   - Explain why different endpoints have different limits
   - Describe when to use per-IP vs per-user rate limiting
   - Identify appropriate limits for your own API projects

## Questions to Consider

1. Why is the login endpoint more strictly limited than the data endpoint?
2. What would happen if you used per-user rate limiting for the `/register` endpoint?
3. How would you implement different rate limits for free vs premium users?
4. When would you exempt an endpoint from rate limiting? What are the risks?
5. How do rate limit headers help API clients implement better retry logic?
6. What's the difference between rate limiting and throttling?

Good luck protecting your APIs! 🛡️
