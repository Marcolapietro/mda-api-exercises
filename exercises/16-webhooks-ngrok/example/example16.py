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
# Grows forever: a real service would cap this list or expire old entries (and persist them)
webhook_events = []

# Delivery IDs already processed. GitHub retries failed deliveries (and you can press
# "Redeliver"), and every retry carries the SAME X-GitHub-Delivery ID.
# Grows forever too: a real service would expire IDs after a few days
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
        # Behind ngrok this is the tunnel agent (127.0.0.1); the real caller IP is in X-Forwarded-For
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
# WEBHOOK SIGNATURE VERIFICATION (HMAC-SHA256) - COMPLETE SOLUTION
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
    # Only accept the SHA-256 format. Reject a missing header, the legacy "sha1=..." header
    # format, or anything else.
    if not signature_header or not signature_header.startswith("sha256="):
        return False
    received_signature = signature_header[len("sha256="):]

    # Recompute the signature over the exact bytes we received
    expected_signature = hmac.new(secret.encode(), payload_body, hashlib.sha256).hexdigest()

    # Constant-time comparison: '==' stops at the first different character, which leaks
    # timing information an attacker can use to guess the signature byte by byte
    return hmac.compare_digest(expected_signature, received_signature)


# ============================================================================
# GITHUB WEBHOOK ENDPOINT - COMPLETE SOLUTION
# ============================================================================

@app.post("/webhooks/github", status_code=200)
async def github_webhook(request: Request) -> dict:
    """
    Receives REAL push events from GitHub.

    When you configure a webhook in GitHub repository settings, it sends POST
    requests to this endpoint with information about repository events.

    Besides the two Authlib routes of exercise 13, this is the only route that awaits the raw request body:
    `request.body()` is a coroutine, so the function must be `async def` and the call needs `await`.

    Steps, in this order:
    1. Refuse to work without a configured secret (never accept unsigned requests)
    2. Verify X-Hub-Signature-256 over the RAW body          -> 401 if missing/invalid
    3. Read the event type from X-GitHub-Event               -> 400 if missing
    4. Deduplicate by X-GitHub-Delivery (retries happen)      -> 200 "duplicate, ignored"
    5. "ping" -> 200 "pong"; anything but "push"              -> 200 "ignored" (not stored)
    6. Store a minimal record of the push and answer 2xx quickly

    Official documentation: https://docs.github.com/en/webhooks/webhook-events-and-payloads
    Signature validation:   https://docs.github.com/en/webhooks/using-webhooks/validating-webhook-deliveries
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
    body = await request.body()
    signature = request.headers.get("X-Hub-Signature-256")
    if not verify_github_signature(body, signature, secret):
        print("WARNING: Invalid or missing X-Hub-Signature-256 - rejecting webhook")
        return JSONResponse({
            "error": "Unauthorized",
            "message": "Missing or invalid X-Hub-Signature-256 signature"
        }, status_code=401)

    # 3. Which event is this? GitHub says so in a header, not in the body
    event = request.headers.get("X-GitHub-Event", "")
    if not event:
        return JSONResponse({"error": "Bad Request", "message": "Missing X-GitHub-Event header"},
                            status_code=400)

    # 4. Deduplicate: GitHub may deliver the same event more than once
    delivery_id = request.headers.get("X-GitHub-Delivery")
    if not delivery_id:
        return JSONResponse({"error": "Bad Request", "message": "Missing X-GitHub-Delivery header"},
                            status_code=400)

    if delivery_id in processed_deliveries:
        print(f"Duplicate delivery {delivery_id} - ignored")
        return {"status": "duplicate, ignored", "delivery_id": delivery_id}

    # Only now is it safe to parse the payload (a body that is not valid JSON gives None)
    try:
        data = json.loads(body)
    except ValueError:
        data = None

    if not data or not isinstance(data, dict):
        return JSONResponse({
            "error": "Invalid payload",
            "message": "Expected a JSON body (set Content type to 'application/json' in GitHub)"
        }, status_code=400)

    # Handle GitHub "ping" event (sent when webhook is first created)
    # This confirms your webhook endpoint is reachable
    if event == "ping":
        processed_deliveries.add(delivery_id)
        print(f"\n{'='*60}")
        print("GitHub Webhook Ping Received!")
        print(f"   Hook ID: {data.get('hook_id')}")
        print(f"   Zen: {data.get('zen')}")
        print("   OK: Webhook is configured correctly (and the signature is valid)!")
        print(f"{'='*60}\n")
        return {"status": "pong"}

    # Any other event (issues, pull_request...) is acknowledged but not stored: a 2xx tells
    # GitHub the delivery worked, so it does not retry it
    if event != "push":
        print(f"Event '{event}' ignored (only push events are stored)")
        return {"status": "ignored", "event": event}

    # Extract repository info from real GitHub payload
    repository = data.get("repository", {})
    repo_name = repository.get("full_name", "unknown") if repository else "unknown"

    # Extract pusher info (who pushed the code)
    pusher = data.get("pusher", {})
    pusher_name = pusher.get("name", "unknown") if pusher else "unknown"

    # Extract commits list
    commits = data.get("commits", [])

    # Extract ref (which branch was pushed)
    ref = data.get("ref", "unknown")

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

    # 6. Store a minimal record (fast). In a real system you would put the event on a
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

    # Remember this delivery so a retry with the same ID is not stored twice
    processed_deliveries.add(delivery_id)

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
        # Behind ngrok this is the tunnel agent (127.0.0.1); the real caller IP is in X-Forwarded-For
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


# Start it with:  fastapi dev example/example16.py   (it runs at http://127.0.0.1:8000)
# Then expose it with:  ngrok http 8000
# Set GITHUB_WEBHOOK_SECRET in the terminal first (see readme16.md, Task 2.2). Without it,
# /webhooks/github answers 503. Generate one with:
#     python -c "import secrets; print(secrets.token_hex(32))"
