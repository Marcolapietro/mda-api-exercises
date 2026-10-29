import hashlib
import hmac
import json
import os

from fastapi import FastAPI, Request
from fastapi.exception_handlers import http_exception_handler
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from starlette.exceptions import HTTPException as StarletteHTTPException

app = FastAPI(title="GitHub webhook demo")

if not os.environ.get("GITHUB_WEBHOOK_SECRET"):
    print("WARNING: GITHUB_WEBHOOK_SECRET is not set.")
    print("   /webhooks/github will answer 503 until you set it and restart.")
    print('   Generate one with: python -c "import secrets; print(secrets.token_hex(32))"')

# In-memory storage for demonstration
users = {}
webhook_events = []

# Delivery IDs already processed. GitHub retries failed deliveries (and you can press
# "Redeliver"), and every retry carries the SAME X-GitHub-Delivery ID.
processed_deliveries = set()


class UserCreate(BaseModel):
    username: str
    email: str | None = None


@app.get("/health")
def health() -> dict:
    """
    Health check endpoint to verify the API is running.
    This is useful for testing that ngrok is working correctly.
    """
    return {
        "status": "ok",
        "service": "github-webhook-demo",
        "version": "1.0",
        "message": "API is running and accessible!"
    }


@app.get("/info")
def info(request: Request) -> dict:
    """
    Returns information about the incoming request.
    Useful for debugging ngrok forwarding.
    """
    return {
        "your_ip": request.client.host if request.client else None,
        "your_user_agent": request.headers.get("User-Agent"),
        "host": request.headers.get("Host"),
        "path": request.url.path,
        "method": request.method,
        # Never echo credentials back: this endpoint is public once ngrok is running
        "headers": {k: v for k, v in request.headers.items()
                    if k.lower() not in ("authorization", "cookie", "x-api-key",
                                         "x-hub-signature", "x-hub-signature-256")}
    }


@app.get("/users")
def list_users() -> list[dict]:
    """
    Simple user management for testing team collaboration.

    GET: List all users
    """
    return list(users.values())


@app.post("/users", status_code=201)
def create_user(new_user: UserCreate) -> dict:
    """
    POST: Create a new user
    The JSON body is validated by the UserCreate model (a missing username answers 422).
    """
    if new_user.username in users:
        return JSONResponse({"error": "User already exists"}, status_code=409)

    user = {
        "username": new_user.username,
        "email": new_user.email,
        "id": len(users) + 1
    }
    users[new_user.username] = user

    return user


# ============================================================================
# WEBHOOK SIGNATURE VERIFICATION (HMAC-SHA256) - YOUR TASK
# ============================================================================

def verify_github_signature(payload_body, signature_header, secret):
    """
    Returns True only if `signature_header` is a valid GitHub signature for `payload_body`.

    GitHub computes HMAC-SHA256(secret, raw request body) and sends it as:
        X-Hub-Signature-256: sha256=<hex digest>

    payload_body:     the RAW bytes of the request body (await request.body()), not the parsed JSON
    signature_header: the value of the X-Hub-Signature-256 header (may be None)
    secret:           the shared secret you typed in GitHub's webhook "Secret" field
    """
    # TODO: Only accept the SHA-256 format. Reject a missing header, the legacy
    # "sha1=..." header format, or anything else.
    # Hint: GitHub's header starts with 'sha256='
    if not signature_header or not signature_header.startswith("_____"):
        return False
    received_signature = signature_header[len("sha256="):]

    # TODO: Recompute the signature over the exact bytes we received
    # Hint: hmac.new(key_bytes, message_bytes, hashlib.sha256).hexdigest()
    expected_signature = hmac._____(secret.encode(), payload_body, hashlib.sha256).hexdigest()

    # TODO: Compare the two signatures in CONSTANT time
    # Hint: hmac.compare_digest(a, b) - never use '==', it leaks timing information
    return hmac._____(expected_signature, received_signature)


# ============================================================================
# GITHUB WEBHOOK ENDPOINT - YOUR TASK
# ============================================================================

@app._____("/webhooks/github", status_code=_____)  # TODO: Which HTTP method? Which status code on success?
# Hint: Webhooks use POST to send data to your server; success is 200
async def github_webhook(request: Request) -> dict:
    """
    Receives REAL push events from GitHub.

    When you configure a webhook in GitHub repository settings, it sends POST
    requests to this endpoint with information about repository events.

    This is the only `async def` in the course: reading the raw body is a coroutine,
    so the function must be `async def` and the call needs `await`.

    Security steps, in this order:
    1. Refuse to work without a configured secret (never accept unsigned requests)
    2. Verify X-Hub-Signature-256 over the RAW body          -> 401 if missing/invalid
    3. Deduplicate by X-GitHub-Delivery (retries happen)      -> 200 "duplicate, ignored"
    4. Store a minimal record and answer 2xx quickly

    Official documentation: https://docs.github.com/en/webhooks/webhook-events-and-payloads
    Signature validation:   https://docs.github.com/en/webhooks/using-webhooks/validating-webhook-deliveries

    Real GitHub push webhook payload structure (verified 2025):
    {
      "ref": "refs/heads/main",                    # Branch that was pushed
      "repository": {
        "name": "repo-name",
        "full_name": "user/repo-name",             # Full repository name
        "owner": {...}
      },
      "pusher": {"name": "...", "email": "..."},   # Who pushed the code
      "sender": {...},                             # GitHub user who triggered
      "commits": [                                 # Array of commits
        {
          "id": "abc123...",                       # Full commit SHA
          "message": "commit message",              # Commit message
          "author": {"name": "...", "email": "..."}, # Commit author
          "timestamp": "2025-01-15T10:30:00Z"
        }
      ],
      "head_commit": {...}                         # Most recent commit
    }
    """
    # 1. The secret comes ONLY from the environment. Without it we cannot verify anything,
    #    so we refuse to process instead of silently accepting unsigned requests.
    secret = os.environ.get("GITHUB_WEBHOOK_SECRET")
    if not secret:
        return JSONResponse({
            "error": "Webhook secret not configured",
            "message": "Set the GITHUB_WEBHOOK_SECRET environment variable and restart the app."
        }, status_code=503)

    # 2. Verify the signature on the RAW body, before parsing or trusting anything in it.
    #    Re-serialising the parsed JSON would change spaces/key order and break the HMAC.
    # TODO: Read the RAW body bytes (verify exactly what GitHub signed, before parsing JSON)
    # Hint: await request.body()   (it is a coroutine, so it needs `await`)
    body = await request._____()
    signature = request.headers.get("X-Hub-Signature-256")
    if not verify_github_signature(body, signature, secret):
        print("WARNING: Invalid or missing X-Hub-Signature-256 - rejecting webhook")
        return JSONResponse({
            "error": "Unauthorized",
            "message": "Missing or invalid X-Hub-Signature-256 signature"
        }, status_code=401)

    # 3. Deduplicate: GitHub may deliver the same event more than once
    delivery_id = request.headers.get("X-GitHub-Delivery")
    if not delivery_id:
        return JSONResponse({"error": "Bad Request", "message": "Missing X-GitHub-Delivery header"},
                            status_code=400)

    # TODO: If we already processed this delivery ID, ignore it
    # Hint: check membership in the set of already-processed IDs (processed_deliveries)
    if delivery_id in _____:
        print(f"Duplicate delivery {delivery_id} - ignored")
        return {"status": "duplicate, ignored", "delivery_id": delivery_id}

    # TODO: Only now is it safe to parse the JSON payload from the raw bytes
    # (a body that is not valid JSON gives None)
    # Hint: json.loads(body)
    try:
        data = json._____(body)
    except ValueError:
        data = None

    if not data or not isinstance(data, dict):
        return JSONResponse({
            "error": "Invalid payload",
            "message": "Expected a JSON body (set Content type to 'application/json' in GitHub)"
        }, status_code=400)

    # Handle GitHub "ping" event (sent when webhook is first created)
    # This confirms your webhook endpoint is reachable
    if "zen" in data and "hook_id" in data:
        processed_deliveries.add(delivery_id)
        print(f"\n{'='*60}")
        print("GitHub Webhook Ping Received!")
        print(f"   Hook ID: {data.get('hook_id')}")
        print(f"   Zen: {data.get('zen')}")
        print("   OK: Webhook is configured correctly (and the signature is valid)!")
        print(f"{'='*60}\n")
        return {"status": "pong"}

    # TODO: Extract repository info from real GitHub payload
    # Hint: data.get('repository', {})
    repository = _____
    repo_name = repository.get("full_name", "unknown") if repository else "unknown"

    # TODO: Extract pusher info (who pushed the code)
    # Hint: data.get('pusher', {})
    pusher = _____
    pusher_name = pusher.get("name", "unknown") if pusher else "unknown"

    # TODO: Extract commits list
    # Hint: data.get('commits', [])
    commits = _____

    # TODO: Extract ref (which branch was pushed)
    # Hint: data.get('ref', 'unknown')
    ref = _____

    # Log the webhook with detailed output
    print(f"\n{'='*60}")
    print("REAL GitHub Webhook Received!")
    print(f"Delivery: {delivery_id}")
    print(f"Repository: {repo_name}")
    print(f"Pushed by: {pusher_name}")
    print(f"Branch: {ref}")
    print(f"Commits: {len(commits)}")

    # Show details of each commit
    for i, commit in enumerate(commits, 1):
        commit_msg = commit.get("message", "No message")
        commit_id = commit.get("id", "unknown")[:7]  # Short SHA (first 7 chars)
        author = commit.get("author", {}).get("name", "unknown")
        print(f"   {i}. [{commit_id}] {commit_msg} (by {author})")

    print(f"{'='*60}\n")

    # 4. Store a minimal record (fast). In a real system you would put the event on a
    #    queue here and let a background worker do the slow work (run tests, deploy...).
    webhook_event = {
        "type": "github_push",
        "delivery_id": delivery_id,
        "repository": repo_name,
        "pusher": pusher_name,
        "ref": ref,
        "commits_count": len(commits),
        "commit_messages": [c.get("message", "") for c in commits]
    }
    webhook_events.append(webhook_event)

    # TODO: Remember this delivery so a retry with the same ID is not stored twice
    # Hint: processed_deliveries is a set -> processed_deliveries.add(delivery_id)
    processed_deliveries._____(delivery_id)

    # GitHub expects a 2xx status quickly (it times out after 10 seconds)
    # If you return non-2xx, GitHub will mark the webhook as failed
    return {"status": "received", "commits_processed": len(commits)}


# ============================================================================
# MONITORING AND DEBUGGING
# ============================================================================

@app.get("/webhooks/events")
def list_webhook_events() -> dict:
    """
    Returns all received webhook events.
    Useful for debugging and verifying webhooks were received.
    """
    return {
        "total_events": len(webhook_events),
        "events": webhook_events
    }


@app.post("/webhooks/events/clear")
def clear_webhook_events() -> dict:
    """
    Clears all stored webhook events and the list of processed delivery IDs.
    Useful for testing - start fresh.
    """
    count = len(webhook_events)
    webhook_events.clear()
    processed_deliveries.clear()
    return {
        "message": f"Cleared {count} webhook events",
        "remaining": 0
    }


# ============================================================================
# REQUEST LOGGING (for debugging)
# ============================================================================

@app.middleware("http")
async def log_request(request: Request, call_next):
    """
    Logs all incoming requests.
    This helps you see traffic coming through ngrok.
    """
    # Skip logging for some paths to reduce noise
    if request.url.path != "/favicon.ico":
        print(f"\n{'='*60}")
        print("Incoming Request:")
        print(f"   Method: {request.method}")
        print(f"   Path: {request.url.path}")
        print(f"   From: {request.client.host if request.client else 'unknown'}")
        print(f"   User-Agent: {request.headers.get('User-Agent', 'Unknown')[:50]}")
        print(f"{'='*60}\n")

    return await call_next(request)


# ============================================================================
# ERROR HANDLERS
# ============================================================================

@app.exception_handler(StarletteHTTPException)
async def http_error(request: Request, exc: StarletteHTTPException):
    if exc.status_code == 404:
        return JSONResponse({
            "error": "Not Found",
            "message": f"The endpoint {request.url.path} does not exist",
            "tip": "Try /health to verify the API is running"
        }, status_code=404)
    if exc.status_code == 405:
        return JSONResponse({
            "error": "Method Not Allowed",
            "message": f"{request.method} is not allowed for {request.url.path}"
        }, status_code=405)
    return await http_exception_handler(request, exc)


@app.exception_handler(Exception)
async def internal_error(request: Request, exc: Exception):
    print(f"Internal server error: {exc}")
    return JSONResponse({
        "error": "Internal Server Error",
        "message": "Something went wrong on the server"
    }, status_code=500)


# Start it with:  fastapi dev app.py   (it runs at http://127.0.0.1:8000)
# Then expose it with:  ngrok http 8000
# Set GITHUB_WEBHOOK_SECRET in the terminal first (see readme16.md, Task 2.2). Without it,
# /webhooks/github answers 503. Generate one with:
#     python -c "import secrets; print(secrets.token_hex(32))"
