# Exercise 16: Exposing Your API Publicly with ngrok and GitHub Webhooks

## Introduction

In this exercise, you'll learn how to expose your local API to the internet using **ngrok** and configure **real GitHub webhooks**. This is essential for:
- Receiving webhook notifications from GitHub when code is pushed
- Sharing your API with team members without deploying
- Understanding how services communicate via webhooks
- Learning production webhook patterns used in CI/CD systems

As soon as your API has a public URL, **anyone** can POST to it. That is why this exercise treats webhook security as part of the core task, not as an extra: your endpoint will only accept requests that carry a valid GitHub signature.

## Learning Objectives

By the end of this exercise, you will be able to:

1. Install and configure ngrok on your system (verified 2025)
2. Expose a local API to a public HTTPS URL
3. Configure real GitHub webhooks in repository settings
4. Implement webhook endpoints that handle authentic GitHub payloads
5. **Verify the `X-Hub-Signature-256` HMAC signature** on every call, with a constant-time comparison
6. **Deduplicate deliveries** by `X-GitHub-Delivery`, because retries happen
7. Use ngrok's dashboard for request inspection and debugging
8. Collaborate with teammates by sharing ngrok URLs

## What is ngrok?

**ngrok** is a tool that creates a secure tunnel from a public URL to your local development server. It provides:
- A public HTTPS URL that forwards to localhost
- A web dashboard showing all HTTP requests in real-time
- Request inspection and replay capabilities
- Free tier with essential features (perfect for learning)

**Official site:** https://ngrok.com

**Use Cases:**
- **GitHub Webhooks**: Receive push notifications from GitHub to your local app
- **Team collaboration**: Share your API during the ProManage project without deployment
- **CI/CD Development**: Build automated workflows triggered by GitHub events
- **Microservices Testing**: Test service-to-service communication locally

## Prerequisites

Before starting this exercise, you should have completed:
- **Exercise 04**: API Fundamentals (understanding basic FastAPI apps)
- **Exercise 11**: JWT Authentication (optional, but recommended)

## Installation

### Step 1: Download ngrok

**Windows:**
1. Visit [ngrok.com/download](https://ngrok.com/download)
2. Download the Windows ZIP file
3. Extract `ngrok.exe` to a folder (e.g., `C:\ngrok\`)
4. Add to PATH (optional but recommended):
   - Open "Environment Variables" in System Settings
   - Edit "Path" variable
   - Add `C:\ngrok\` (or your chosen location)
   - Restart terminal

**Mac (with Homebrew):**
```bash
brew install ngrok/ngrok/ngrok
```

**Linux:**
```bash
# Download
curl -s https://ngrok-agent.s3.amazonaws.com/ngrok.asc | sudo tee /etc/apt/trusted.gpg.d/ngrok.asc >/dev/null
echo "deb https://ngrok-agent.s3.amazonaws.com buster main" | sudo tee /etc/apt/sources.list.d/ngrok.list
sudo apt update && sudo apt install ngrok
```

**Verify Installation:**
```bash
ngrok version
# Should show: ngrok version 3.x.x
```

### Step 2: Sign Up for ngrok Account (Free)

1. Go to [ngrok.com/signup](https://ngrok.com/signup)
2. Create a free account (required - no credit card needed)
3. Verify your email address

**Free tier includes:**
- 1 online ngrok process
- 40 connections/minute
- HTTPS tunnels
- Request inspection

### Step 3: Authenticate ngrok (Updated 2025)

1. Log in to [dashboard.ngrok.com](https://dashboard.ngrok.com)
2. Navigate to "Getting Started" → "Your Authtoken"
3. Copy your authtoken
4. Run in terminal:
   ```bash
   ngrok config add-authtoken YOUR_AUTH_TOKEN_HERE
   ```

**Example:**
```bash
ngrok config add-authtoken 2bXjYZ1234abcd5678efgh_9IJKLMnopqrstuvwxyz
```

This saves your token to the ngrok configuration file:
- **Mac/Linux**: `~/.ngrok2/ngrok.yml`
- **Windows**: `%USERPROFILE%\.ngrok2\ngrok.yml`

## Quick Start

### Run the Starter API

```bash
cd exercises/16-webhooks-ngrok
python -m venv venv

# Activate virtual environment
# Windows:
venv\Scripts\activate
# Mac/Linux:
source venv/bin/activate

pip install -r requirements.txt
fastapi dev app.py
```

Your app runs at `http://127.0.0.1:8000`

> **The starter does not start yet.** In FastAPI the HTTP method and `status_code` live in the decorator,
> which Python evaluates when the file is loaded. The decorator of `/webhooks/github` has two blanks
> (`@app._____("/webhooks/github", status_code=_____)`): fill them first (blanks 4 and 5 in Task 2.3: `post` and `200`)
> and `fastapi dev app.py` starts. The other 11 blanks are inside functions and only matter when a
> webhook arrives, so `/health`, `/info` and `/users` already work.

> At startup the app prints a **warning** if `GITHUB_WEBHOOK_SECRET` is not set. `/health`, `/info` and `/users`
> work anyway, but `/webhooks/github` answers **503** until you set the secret (see Task 2.2).

### Expose with ngrok

**Open a new terminal** (keep the API running) and run:
```bash
ngrok http 8000
```

You'll see output like:
```
ngrok

Session Status                online
Account                       your-email@example.com (Plan: Free)
Version                       3.5.0
Region                        United States (us)
Latency                       25ms
Web Interface                 http://127.0.0.1:4040
Forwarding                    https://abcd-1234-5678-efgh.ngrok-free.app -> http://localhost:8000

Connections                   ttl     opn     rt1     rt5     p50     p90
                              0       0       0.00    0.00    0.00    0.00
```

**Your public URL**: `https://abcd-1234-5678-efgh.ngrok-free.app`

Anyone can now access your API at this URL!

### Test It

```bash
# From anywhere (your phone, another computer, etc.)
curl https://abcd-1234-5678-efgh.ngrok-free.app/health
```

## Exercise Structure

This exercise provides:
- `app.py` - Starter app with TODOs for webhook implementation (signature check, dedupe, payload)
- `example/example16.py` - Complete reference solution
- `example/send_signed_webhook.py` - Helper that sends **signed** test webhooks to your app, without GitHub
- `readme16.md` / `readme16_es.md` - This instruction file (English / Spanish)

## Part 1: Basic Exposure (15 minutes)

### Task 1.1: Run the Sample App

The provided `app.py` has a basic API with health check and user endpoints. Remember to fill the two blanks in the `/webhooks/github` decorator first (see the note in Quick Start), otherwise it does not start.

```bash
fastapi dev app.py
```

Visit `http://localhost:8000/health` - should return `{"status": "ok"}`

### Task 1.2: Expose with ngrok

In a **new terminal**:
```bash
ngrok http 8000
```

Copy your public URL (the `https://....ngrok-free.app` address).

### Task 1.3: Test Public Access

From your browser or curl:
```bash
curl https://YOUR-NGROK-URL.ngrok-free.app/health
```

**Expected Result**: Same response as localhost

### Task 1.4: Explore ngrok Dashboard

Open `http://localhost:4040` in your browser.

You'll see:
- List of all HTTP requests
- Request/response details (headers, body, status)
- Ability to replay requests
- Connection statistics

Try making several requests and watch them appear in real-time.

## Part 2: Real, Signed GitHub Webhook (60 minutes)

This is the core of the exercise. You'll configure a **real GitHub webhook** that triggers when you push code, and your endpoint will **only accept it if GitHub's signature is valid**.

### Task 2.1: Create or Choose a GitHub Repository

**Option A - Create New Test Repo:**
1. Go to [github.com/new](https://github.com/new)
2. Name it `api-webhook-test` (or anything you like)
3. Make it **Public** (required for free webhooks)
4. Initialize with a README
5. Create repository

**Option B - Use Existing Repo:**
- Any public repo you own will work
- You'll need admin access to configure webhooks

### Task 2.2: Generate the Webhook Secret and Set It as an Environment Variable

GitHub and your app share a **secret**. GitHub uses it to sign every delivery; your app uses it to check the signature. Nobody else knows it, so nobody else can produce a valid signature.

**Step 1: Generate a secret** (works the same on Windows, Mac and Linux):
```bash
python -c "import secrets; print(secrets.token_hex(32))"
```

This prints 64 hexadecimal characters (32 random bytes) from Python's **cryptographically secure** generator, for example `3f9c...e1a7`. Copy it.

> Don't invent the secret yourself and don't use non-cryptographic generators (such as PowerShell's
> `Get-Random` or Python's `random`): their output can be predicted.

**Step 2: Set it as an environment variable** in the **same terminal** where you will run `fastapi dev app.py` (it only lasts for that terminal session):

```bash
# Linux / macOS (bash, zsh)
export GITHUB_WEBHOOK_SECRET="paste-the-64-hex-characters-here"
```

```powershell
# Windows PowerShell
$env:GITHUB_WEBHOOK_SECRET="paste-the-64-hex-characters-here"
```

```bat
:: Windows CMD (no quotes, no spaces around =)
set GITHUB_WEBHOOK_SECRET=paste-the-64-hex-characters-here
```

**Never** paste the secret into `app.py`: anything in the code ends up in Git. Keep the value somewhere safe: in Task 2.6 you will paste the **same value** into GitHub's webhook **Secret** field.

If the variable is not set, the app prints a warning at startup and `/webhooks/github` answers:
```json
{"error": "Webhook secret not configured", "message": "Set the GITHUB_WEBHOOK_SECRET environment variable and restart the app."}
```
with status **503**. It **never** falls back to accepting unsigned requests.

### Task 2.3: Complete the Webhook Endpoint

#### How GitHub webhook signatures (HMAC) work

```
GitHub                                         Your API
──────                                         ──────────────
body = the raw JSON bytes                      body = await request.body()   (raw bytes!)
sig  = HMAC-SHA256(secret, body)               expected = HMAC-SHA256(secret, body)

POST /webhooks/github                          header must start with "sha256="
X-Hub-Signature-256: sha256=<sig in hex>  ──►  compare_digest(expected, received)?
X-GitHub-Delivery:   <unique id>                 ✅ equal      → continue
                                                 ❌ different  → 401 Unauthorized
```

1. You set the secret in GitHub when configuring the webhook (and in your app's environment).
2. GitHub computes an **HMAC-SHA256** of the request body using the secret.
3. GitHub sends it in the `X-Hub-Signature-256` header, as `sha256=<hex digest>`.
4. Your app recomputes the HMAC over the bytes it received and compares.
5. If they match → the request came from GitHub and the body was not modified. If not → reject with **401**.

**Four details that matter:**
- **Use the RAW body** (`await request.body()`), never `json.dumps(json.loads(body))`. Re-serialising changes spaces and key order, and the HMAC no longer matches.
- **Check the `sha256=` prefix.** Reject a missing header, the old `X-Hub-Signature: sha1=...` format, or anything else. Simply splitting on `=` would accept garbage.
- **Compare in constant time** with `hmac.compare_digest`. A normal `==` returns as soon as one character differs, and that timing difference can be measured to guess the signature byte by byte.
- **No secret, no processing.** If `GITHUB_WEBHOOK_SECRET` is missing the endpoint answers 503. An endpoint that "verifies only if a secret is configured" is an endpoint that accepts forged requests.

> **Same idea, other providers:** GitHub calls this header `X-Hub-Signature-256`. Stripe uses
> `Stripe-Signature` (it also signs a timestamp to stop replays), Slack uses `X-Slack-Signature`, and so on.
> The header name and format change, but the pattern is always: shared secret + HMAC of the raw body +
> constant-time comparison.

#### Why `async def` and `await request.body()`?

Until now every path operation in the course was a plain `def`. Reading the raw request body is different: `request.body()` is a **coroutine**, a function that has to wait for the bytes to arrive from the network, so you call it with `await`, and `await` is only allowed inside an `async def` function. That is why `github_webhook` is the **only `async def` in the course**. Everything else stays `def`: FastAPI runs those in a thread pool, and you only need `async def` when the function body awaits something. Why not simply declare a body model, as in the earlier exercises? Because a model gives you the *parsed* JSON, and the HMAC must be computed over the exact bytes GitHub sent.

#### Deduplicate by delivery ID

If your endpoint is slow, fails, or GitHub doesn't get the answer, GitHub **delivers the same event again**. You can also press **Redeliver** in GitHub. Each delivery carries an `X-GitHub-Delivery` header with a unique ID, and a redelivery keeps the **same** ID. Your app remembers the IDs it has already processed (`processed_deliveries`, a Python `set`) and answers a repeat with:
```json
{"status": "duplicate, ignored", "delivery_id": "..."}
```
with status **200**, so GitHub stops retrying, but the event is **not stored twice**.

> The delivery ID is not part of the signature, so deduplication protects you against **retries**, not against
> an attacker replaying a captured request. Providers such as Stripe also sign a timestamp to limit that.

#### Respond fast, process later

GitHub waits **10 seconds** for your answer; after that it marks the delivery as failed (and may retry). So the endpoint should only verify, store a minimal record and answer **2xx** immediately. Slow work (running tests, deploying, sending emails) belongs in a **queue** processed by a background worker (e.g. Celery, RQ, a cloud queue). In this exercise "storing" is appending to an in-memory list, which is fast enough.

#### Your TODOs in `app.py`

Open `app.py` and fill in the **13 blanks** (`_____`). The order of the checks in the endpoint is: secret configured → signature → dedupe → parse JSON → store → answer.

| # | Where (function / section) | What to write |
|---|----------------------------|---------------|
| 1 | `verify_github_signature()` | Required prefix: `signature_header.startswith('sha256=')` |
| 2 | `verify_github_signature()` | Compute the HMAC: `hmac.new(secret.encode(), payload_body, hashlib.sha256).hexdigest()` |
| 3 | `verify_github_signature()` | Constant-time comparison: `hmac.compare_digest(expected_signature, received_signature)` |
| 4 | `@app._____("/webhooks/github", ...)` | HTTP method (decorator, **blocks startup**): `post` |
| 5 | `@app.post("/webhooks/github", status_code=_____)` | Success status code (decorator, **blocks startup**): `200` |
| 6 | `github_webhook()` | Raw body: `await request.body()` |
| 7 | `github_webhook()` | Dedupe check: `if delivery_id in processed_deliveries:` |
| 8 | `github_webhook()` | Parse JSON (after verifying!): `json.loads(body)` |
| 9 | `github_webhook()` | Repository: `data.get('repository', {})` |
| 10 | `github_webhook()` | Pusher: `data.get('pusher', {})` |
| 11 | `github_webhook()` | Commits: `data.get('commits', [])` |
| 12 | `github_webhook()` | Branch: `data.get('ref', 'unknown')` |
| 13 | `github_webhook()` | Remember the delivery: `processed_deliveries.add(delivery_id)` |

Only blanks 4 and 5 stop the app from starting (they are in the decorator, which runs when the file is loaded). The rest fail only when a webhook reaches that line.

The signature function you complete:

```python
def verify_github_signature(payload_body, signature_header, secret):
    # TODO: Only accept the SHA-256 format
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
```

And the security part of the endpoint:

```python
@app._____("/webhooks/github", status_code=_____)  # TODO: Which HTTP method? Which status code on success?
# Hint: Webhooks use POST to send data to your server; success is 200
async def github_webhook(request: Request) -> dict:
    # 1. No secret -> refuse (never accept unsigned requests)
    secret = os.environ.get("GITHUB_WEBHOOK_SECRET")
    if not secret:
        return JSONResponse({"error": "Webhook secret not configured", ...}, status_code=503)

    # 2. TODO: Read the RAW body bytes. Hint: await request.body()
    body = await request._____()
    signature = request.headers.get("X-Hub-Signature-256")
    if not verify_github_signature(body, signature, secret):
        return JSONResponse({"error": "Unauthorized", ...}, status_code=401)

    # 3. Deduplicate
    delivery_id = request.headers.get("X-GitHub-Delivery")
    ...
    # TODO: If we already processed this delivery ID, ignore it
    if delivery_id in _____:
        return {"status": "duplicate, ignored", "delivery_id": delivery_id}

    # TODO: Only now is it safe to parse the JSON. Hint: json.loads(body)
    try:
        data = json._____(body)
    except ValueError:
        data = None
    ...
    # (extract repository, pusher, commits and ref, log them and store a minimal record)
    ...
    # TODO: Remember this delivery. Hint: processed_deliveries.add(delivery_id)
    processed_deliveries._____(delivery_id)

    # The status code (200) was set in the decorator: just return the dict
    return {"status": "received", "commits_processed": len(commits)}
```

The error answers (503, 401, 400) are `JSONResponse(..., status_code=...)`: returning a response object lets one function answer with different status codes and keep the `{"error": ..., "message": ...}` shape.

Real GitHub push payload structure (the part we read):
```
{
  "ref": "refs/heads/main",
  "repository": {"name": "...", "full_name": "user/repo"},
  "pusher": {"name": "...", "email": "..."},
  "commits": [{"id": "...", "message": "...", "author": {...}}, ...]
}
```

### Task 2.4: Test Locally Without GitHub

Before involving GitHub, prove that your endpoint accepts good signatures and rejects bad ones. `example/send_signed_webhook.py` signs a sample push payload exactly like GitHub does and sends it to your app.

**Terminal 1 - API** (with `GITHUB_WEBHOOK_SECRET` set, Task 2.2):
```bash
fastapi dev app.py
```

**Terminal 2 - helper** (set the **same** `GITHUB_WEBHOOK_SECRET` in this terminal too):
```bash
python example/send_signed_webhook.py
```

Expected output (delivery IDs will differ):
```
[valid       ] delivery=6f1c... -> HTTP 200 {"status":"received","commits_processed":1}
[valid       ] delivery=0b7e... -> HTTP 200 {"status":"received","commits_processed":1}
   ...sending the same delivery ID again (simulating a GitHub retry):
[valid       ] delivery=0b7e... -> HTTP 200 {"status":"duplicate, ignored","delivery_id":"0b7e..."}
[tampered    ] delivery=9a42... -> HTTP 401 {"error":"Unauthorized","message":"Missing or invalid X-Hub-Signature-256 signature"}
[unsigned    ] delivery=c3d5... -> HTTP 401 {"error":"Unauthorized",...}
[wrong-prefix] delivery=e8f0... -> HTTP 401 {"error":"Unauthorized",...}
```

Then check that the duplicate was **not** stored twice:
```bash
curl http://127.0.0.1:8000/webhooks/events
# total_events: 2  (two different valid deliveries, the repeated one counted once)
```

You can run a single case with `--mode valid|duplicate|tampered|unsigned|wrong-prefix`, or point it at your public URL with `--url https://YOUR-NGROK-URL.ngrok-free.app/webhooks/github`.

**What each case proves:**
- **valid** → the signature you compute matches GitHub's algorithm.
- **duplicate** → a retry with the same `X-GitHub-Delivery` is acknowledged but ignored.
- **tampered** → the body was changed after signing: the HMAC no longer matches.
- **unsigned** → no header: rejected, even though the JSON is perfectly valid.
- **wrong-prefix** → the right digest with a `sha1=` prefix: rejected, only `sha256=` is accepted.

### Task 2.5: Run Your API and ngrok

**Terminal 1 - API** (with `GITHUB_WEBHOOK_SECRET` set):
```bash
cd exercises/16-webhooks-ngrok
fastapi dev app.py
```

**Terminal 2 - ngrok:**
```bash
ngrok http 8000
```

**Copy your ngrok URL** from the output:
```
Forwarding    https://abc123-xyz.ngrok-free.app -> http://localhost:8000
              ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
              Copy this URL!
```

ngrok gives you an **HTTPS** URL: use it. Webhook payloads and signatures should always travel over HTTPS.

### Task 2.6: Configure GitHub Webhook

1. **Go to your repository on GitHub**
   - Navigate to `https://github.com/YOUR-USERNAME/YOUR-REPO`

2. **Open Settings → Webhooks**
   - Click the repository **Settings** tab (top right)
   - Scroll down and click **Webhooks** in the left sidebar
   - Click **Add webhook** button

3. **Configure the Webhook**
   - **Payload URL**: `https://YOUR-NGROK-URL.ngrok-free.app/webhooks/github`
     - Example: `https://abc123-xyz.ngrok-free.app/webhooks/github`
     - ⚠️ Make sure to include `/webhooks/github` at the end!

   - **Content type**: Select `application/json` (with the default `application/x-www-form-urlencoded` the body is not JSON and the app answers 400)

   - **Secret**: Paste the **same value** you put in `GITHUB_WEBHOOK_SECRET` (Task 2.2)

   - **SSL verification**: Keep it enabled

   - **Which events?**: Select "Just the push event"

   - **Active**: Check this box ✅

   - Click **Add webhook**

4. **Verify Setup**
   - GitHub will immediately send a signed "ping" event
   - Check your API terminal - you should see `GitHub Webhook Ping Received!`
   - In GitHub, scroll down to "Recent Deliveries" - should show green checkmark ✅

**Common Issue**: If you see a red X, check:
- Is the API running? Is ngrok running?
- Did you copy the correct ngrok URL, including `/webhooks/github`?
- **401 Unauthorized** → the Secret in GitHub and `GITHUB_WEBHOOK_SECRET` are different (copy them again, without extra spaces), or you set the variable in a different terminal.
- **503** → `GITHUB_WEBHOOK_SECRET` is not set in the terminal that runs the API.
- **400 Invalid payload** → Content type is not `application/json`.

### Task 2.7: Trigger the Webhook with a Real Push

Now for the magic moment! Make a change to your repository:

**Method 1 - GitHub Web Interface (easiest):**
1. Go to your repo on GitHub
2. Click on `README.md`
3. Click the pencil icon (Edit)
4. Add a line: `Testing webhook at [current time]`
5. Scroll down, click **Commit changes**
6. Click **Commit changes** again

**Watch your API terminal** - you should see:
```
============================================================
REAL GitHub Webhook Received!
Delivery: 72d3162e-cc78-11e3-81ab-4c9367dc0958
Repository: your-username/api-webhook-test
Pushed by: your-username
Branch: refs/heads/main
Commits: 1
   1. [a1b2c3d] Update README.md (by Your Name)
============================================================
```

**Method 2 - Git Command Line (if you have git):**
```bash
git clone https://github.com/YOUR-USERNAME/YOUR-REPO.git
cd YOUR-REPO
echo "Test webhook $(date)" >> README.md
git add README.md
git commit -m "Test webhook trigger"
git push
```

### Task 2.8: Inspect (and Replay) the Webhook in ngrok Dashboard

1. Open `http://localhost:4040` in your browser
2. You'll see the POST request from GitHub
3. Click on it to see:
   - Full headers, including `X-Hub-Signature-256`, `X-GitHub-Delivery` and `X-GitHub-Event`
   - Complete JSON payload (the raw bytes that were signed)
   - Your response (200 OK)
4. Click **Replay**: ngrok resends the exact same request, with the same delivery ID. Your app answers `"duplicate, ignored"` and `/webhooks/events` does not grow. That is deduplication working.
5. Try **Redeliver** in GitHub ("Recent Deliveries" → a delivery → **Redeliver**): same result, because a redelivery keeps its `X-GitHub-Delivery`.

**This is extremely useful for debugging webhooks!**

### Task 2.9: View All Received Webhooks

Your app stores webhook events. Check them:

```bash
curl https://YOUR-NGROK-URL.ngrok-free.app/webhooks/events
```

You'll see all GitHub events you've received, each with its `delivery_id`. `POST /webhooks/events/clear` empties the list and forgets the processed delivery IDs.

## Part 3: Team Collaboration (20 minutes)

Now that you understand webhooks, practice sharing your API with teammates (essential for ProManage project!).

### Task 3.1: Share Your API

1. Ensure your API and ngrok are running
2. Share your ngrok URL with a classmate: `https://your-url.ngrok-free.app`
3. Have them test your `/health` and `/info` endpoints

`/info` echoes the request headers back, but it strips `Authorization`, `Cookie`, `X-API-Key` and the signature headers: a public endpoint must never reflect credentials.

### Task 3.2: Call a Teammate's API

1. Get a teammate's ngrok URL
2. Test their endpoints:
   ```bash
   # Health check
   curl https://their-ngrok-url.ngrok-free.app/health

   # See request info
   curl https://their-ngrok-url.ngrok-free.app/info

   # Create a user on their API
   curl -X POST https://their-ngrok-url.ngrok-free.app/users \
     -H "Content-Type: application/json" \
     -d '{"username": "yourname", "email": "you@example.com"}'
   ```

3. Try to send them a fake push without the signature:
   ```bash
   curl -X POST https://their-ngrok-url.ngrok-free.app/webhooks/github \
     -H "Content-Type: application/json" \
     -H "X-GitHub-Delivery: fake-1" \
     -d '{"ref": "refs/heads/main", "commits": []}'
   ```
   **Expected:** `401 Unauthorized`. This is exactly the attack the signature stops.

### Task 3.3: Cross-Team Webhook Testing

**Advanced collaboration**: Configure your GitHub webhook to notify your teammate when you push!

1. Teammate shares their ngrok URL **and** agrees a webhook secret with you (they set it as their `GITHUB_WEBHOOK_SECRET`; share it privately, not in a public chat)
2. In **your** GitHub repo settings:
   - Add a **second webhook**
   - Use your teammate's URL: `https://their-url.ngrok-free.app/webhooks/github`
   - Content type `application/json`, and their secret in the **Secret** field
3. Make a commit to **your** repo
4. Your teammate's API receives the notification!

**This demonstrates microservices communication** - one service notifying another service about events, authenticated with a shared secret.

**Note**: This exercise prepares you for Exercise 15 (ProManage) where you'll use ngrok to share APIs with team members!

## Part 4: Webhook Security Recap (15 minutes)

You already implemented the important parts in Part 2. This section summarises them as the checklist the slides use, so you can apply it to any provider.

### Task 4.1: The Four Rules

| Rule | Why | Where in your code |
|------|-----|--------------------|
| **Verify the HMAC signature on the raw body, in constant time** | Anyone can POST to a public URL; only GitHub knows the secret | `verify_github_signature()` + `await request.body()` + `hmac.compare_digest` |
| **Respond 2xx fast, process afterwards** | GitHub times out after 10 s and retries | Minimal store + `return ..., 200`; real work goes to a queue |
| **Deduplicate by event ID** | Retries and redeliveries send the same event again | `X-GitHub-Delivery` + `processed_deliveries` |
| **Use HTTPS** | Payloads and signatures must not travel in clear text | ngrok's `https://` URL, SSL verification enabled in GitHub |

### Task 4.2: Attack Your Own Endpoint

With the app running locally (and the secret set), try:
1. `python example/send_signed_webhook.py --mode tampered` → **401**
2. `python example/send_signed_webhook.py --mode unsigned` → **401**
3. Stop the app, **unset** the variable (`unset GITHUB_WEBHOOK_SECRET` / `Remove-Item Env:GITHUB_WEBHOOK_SECRET` / `set GITHUB_WEBHOOK_SECRET=`), start it again and send a valid webhook from another terminal → **503**, and the startup warning in the API terminal.
4. Change your secret in GitHub but not in your terminal, then push → GitHub shows a red X with **401** in "Recent Deliveries".

### Task 4.3: Request Inspection and Replay

The ngrok dashboard is incredibly useful:

1. Open `http://localhost:4040`
2. Make a commit to trigger GitHub webhook
3. Click on the webhook request in the dashboard
4. Inspect:
   - **Headers**: See `X-Hub-Signature-256`, `X-GitHub-Delivery` and other GitHub headers
   - **Raw payload**: See the exact JSON GitHub sent (the bytes the signature covers)
   - **Your response**: Confirm you returned 200
5. Click **Replay**: Resends the exact same request → your app answers `"duplicate, ignored"`


## Security Best Practices

### ⚠️ Important Security Warnings

1. **Never expose production databases or sensitive data**
   - ngrok URLs are public - anyone can find them
   - Free tier URLs are not protected by authentication
   - Only expose development/test environments

2. **URLs are temporary**
   - Free tier URLs change every time you restart ngrok
   - Don't hard-code ngrok URLs in your code
   - Use environment variables for URLs

3. **Always validate webhook signatures**
   - Verify `X-Hub-Signature-256` on **every** call, over the raw body, with `hmac.compare_digest`
   - Require the `sha256=` prefix
   - If the secret is not configured, refuse to process (503); never accept unsigned requests
   - See Part 2 (Task 2.3) for the implementation

4. **Deduplicate and respond fast**
   - Use the provider's event/delivery ID (`X-GitHub-Delivery`) to ignore retries
   - Answer 2xx quickly and push slow work to a queue

5. **Rate limiting**
   - Add rate limiting to prevent abuse
   - Use slowapi (see Exercise 14)

6. **Environment variables**
   - Never commit webhook secrets, ngrok URLs or authtokens to Git
   - Generate secrets with `secrets.token_hex(32)`, never with `random` or `Get-Random`

### Recommended Practices

```python
import os

@app.post("/webhooks/github", status_code=200)
async def github_webhook(request: Request) -> dict:
    # The secret comes from the environment only, never from the code
    secret = os.environ.get("GITHUB_WEBHOOK_SECRET")
    if not secret:
        return JSONResponse({"error": "Webhook secret not configured"}, status_code=503)

    signature = request.headers.get("X-Hub-Signature-256")
    if not verify_github_signature(await request.body(), signature, secret):
        return JSONResponse({"error": "Unauthorized"}, status_code=401)
    # Deduplicate, store minimally, answer 2xx...
```

## Common Issues and Solutions

### Issue 1: "ERR_NGROK_108 - You must sign up"
**Solution:** Create free account at ngrok.com and add authtoken

### Issue 2: ngrok URL returns "Invalid Host header"
**Solution:** Some frameworks check Host header. For FastAPI (uvicorn), this shouldn't happen. For other frameworks, configure allowed hosts.

### Issue 3: Can't access from mobile device
**Solution:**
- Ensure you're using the HTTPS URL (not HTTP localhost)
- Check if mobile device has internet connection
- Try accessing from mobile browser first

### Issue 4: Connection timed out
**Solution:**
- Ensure The API is actually running
- Confirm ngrok is pointing to correct port (8000)
- Check firewall settings

### Issue 5: "ERR_NGROK_3200 - Tunnel Limit Reached"
**Solution:** Free plan allows 1 tunnel. Close other ngrok processes with `Ctrl+C`

### Issue 6: Every webhook returns 401
**Solution:**
- The Secret in GitHub and `GITHUB_WEBHOOK_SECRET` must be **identical** (no spaces, no quotes inside the value)
- The variable must be set in the terminal that runs the API, **before** `fastapi dev app.py`
- Make sure you verify `await request.body()` (raw bytes), not re-serialised JSON
- Make sure you compare against the part **after** `sha256=`

### Issue 7: The webhook returns 503
**Solution:** `GITHUB_WEBHOOK_SECRET` is not set in the API terminal. Set it (Task 2.2) and restart the app.

## Testing Checklist

**Part 1: Basic Setup**
- [ ] ngrok installed and authenticated
- [ ] API runs on localhost:8000
- [ ] ngrok exposes app successfully
- [ ] Public URL accessible from browser
- [ ] Public URL accessible from curl
- [ ] ngrok dashboard shows requests (localhost:4040)

**Part 2: Signed GitHub Webhook**
- [ ] Generated a secret with `secrets.token_hex(32)` and set `GITHUB_WEBHOOK_SECRET`
- [ ] Completed the 13 blanks in `app.py`
- [ ] `send_signed_webhook.py`: valid → 200, duplicate → "duplicate, ignored", tampered/unsigned/wrong-prefix → 401
- [ ] Created or selected a GitHub repository
- [ ] Configured webhook in GitHub settings (`application/json`, same Secret)
- [ ] GitHub ping event received successfully (green checkmark)
- [ ] Made a commit to trigger webhook
- [ ] Webhook received and logged in API terminal
- [ ] Saw full commit details in the log
- [ ] Inspected webhook payload and signature headers in ngrok dashboard
- [ ] Replayed a delivery and saw "duplicate, ignored"

**Part 3: Team Collaboration**
- [ ] Shared ngrok URL with teammate
- [ ] Successfully tested teammate's API
- [ ] Created user on teammate's API
- [ ] Confirmed that an unsigned fake push to a teammate's webhook gets 401

**Part 4: Security Recap**
- [ ] Without `GITHUB_WEBHOOK_SECRET` the webhook answers 503 and the app prints a warning
- [ ] A wrong secret in GitHub shows a 401 in "Recent Deliveries"

## Real-World Applications of GitHub Webhooks

Now that you understand webhooks, here are real-world scenarios where they're used:

### 1. Continuous Integration/Deployment (CI/CD)
```
Developer pushes code → GitHub webhook → Your server
                                      ↓
                              Automatically:
                              - Run tests
                              - Build application
                              - Deploy if tests pass
```

**Example tools**: Jenkins, GitHub Actions, CircleCI all use webhooks

### 2. Project Management Automation
```
Push to repo → Webhook → Update Jira ticket status
                      → Post to Slack channel
                      → Update project dashboard
```

### 3. Code Review Workflows
```
Pull Request created → Webhook → Assign reviewers automatically
                               → Run linters
                               → Check for security issues
```

### 4. Documentation Generation
```
Push to main → Webhook → Rebuild documentation site
                      → Update API reference
                      → Deploy to production
```

### 5. Team Notifications
```
Push event → Webhook → Send Discord/Slack notification
                    → Email team members
                    → Update team dashboard
```

### 6. Payments
```
Customer pays → Stripe webhook (Stripe-Signature) → Mark order as paid
                                                  → Send receipt
```
Same rules: verify the signature, deduplicate by event ID, answer 2xx fast.

**In ProManage Project (Exercise 15):**
You could use webhooks to notify team members when:
- A new task is created
- Project status changes
- Assignments are updated

## Preparing for ProManage Team Project

In Exercise 15 (ProManage), you'll work in teams where:
- **Each member develops their own microservice**
- **Services need to communicate with each other**
- **ngrok allows you to share your API without deployment**

Example scenario:
- Student A: User authentication service (port 8000)
- Student B: Project management service (port 5001)
- Student C: Task management service (port 5002)

Each runs their service locally, exposes via ngrok, and shares URLs with the team.

```bash
# Student A's auth service
ngrok http 8000
# Share: https://student-a.ngrok-free.app

# Student B's project service
ngrok http 5001
# Share: https://student-b.ngrok-free.app

# Student C can now call both services:
curl https://student-a.ngrok-free.app/login -d '{"username":"test","password":"pass"}'
curl https://student-b.ngrok-free.app/projects -H "Authorization: Bearer <token>"
```

**This exercise prepares you for exactly this workflow!**

## Additional Resources

### Official Documentation
- **[ngrok Documentation](https://ngrok.com/docs)** - Complete ngrok reference
- **[ngrok Getting Started](https://ngrok.com/docs/getting-started)** - Quick start guide (2025)
- **[GitHub Webhooks](https://docs.github.com/en/webhooks/webhook-events-and-payloads)** - Official webhook documentation
- **[Creating GitHub Webhooks](https://docs.github.com/en/webhooks/using-webhooks/creating-webhooks)** - Setup guide

### Tutorials
- [ngrok + Python Integration](https://ngrok.com/docs/integrations/python/flask) - Official Python guide (written for Flask, same idea)
- [Validating GitHub Webhook Deliveries](https://docs.github.com/en/webhooks/using-webhooks/validating-webhook-deliveries) - Signature verification
- [Best Practices for Using Webhooks (GitHub)](https://docs.github.com/en/webhooks/using-webhooks/best-practices-for-using-webhooks) - Respond fast, handle redeliveries
- [Stripe: Verify Webhook Signatures](https://docs.stripe.com/webhooks#verify-events) - The same idea with `Stripe-Signature`
- [Testing Webhooks Locally](https://ngrok.com/docs/guides/webhooks/local-testing) - Development best practices

### Alternative Tools (for reference)
- [localtunnel](https://localtunnel.me/) - Open source alternative
- [Cloudflare Tunnel](https://www.cloudflare.com/products/tunnel/) - Free, permanent URLs
- [Hookdeck](https://hookdeck.com/) - Webhook testing platform

## Deliverables

When you complete this exercise, you should have:

1. **ngrok Setup**:
   - ngrok installed and authenticated
   - Successfully exposed API with public URL

2. **Real, Signed GitHub Webhook**:
   - GitHub repository with configured webhook (`application/json`, Secret set)
   - API receiving real push events
   - Completed TODOs in `app.py`: signature verification, deduplication and payload handling

3. **Evidence** (screenshots or documentation):
   - ngrok terminal showing public URL
   - GitHub webhook settings page showing active webhook with green checkmark
   - API terminal showing received webhook with commit details
   - `send_signed_webhook.py` output showing 200 / "duplicate, ignored" / 401
   - ngrok dashboard (localhost:4040) showing the GitHub webhook request and its signature header

4. **Team Collaboration**:
   - Successfully shared your API with a teammate
   - Tested a teammate's API endpoints

## Evaluation Criteria

Your work will be evaluated on:

1. **ngrok Setup** (15%):
   - ngrok properly installed and authenticated
   - API successfully exposed with public URL

2. **Real GitHub Webhook** (30%):
   - GitHub webhook properly configured
   - Webhook endpoint correctly handles real GitHub payloads
   - Successfully receives and processes push events
   - Correct extraction of repository, pusher, commits, and ref data

3. **Webhook Security** (25%):
   - HMAC-SHA256 verified on the raw body with `hmac.compare_digest`, `sha256=` prefix required
   - Unsigned, tampered and wrongly prefixed requests rejected with 401
   - No secret configured → the endpoint refuses (503)
   - Duplicate deliveries not stored twice

4. **Code Quality** (15%):
   - All TODOs completed correctly
   - Code follows the established patterns
   - Proper error handling

5. **Team Collaboration** (10%):
   - Successfully shared API with teammate
   - Tested teammate's API endpoints

6. **Documentation/Evidence** (5%):
   - Clear screenshots or notes showing successful webhook delivery
   - Evidence of testing and verification

## Next Steps

After completing this exercise:

1. **Exercise 14**: Swagger Documentation - Document your APIs professionally
2. **Exercise 15**: ProManage Team Project - Use ngrok for team collaboration
3. **Beyond**: Learn about production deployment (Heroku, AWS, Docker) for real applications

**Note**: ngrok is for development/testing only. Production apps should be properly deployed.

## Questions to Consider

1. Why can't you use `localhost` URLs for webhooks from external services?
2. What are the security implications of exposing your development server?
3. When would you use ngrok vs. actual deployment (Heroku, AWS, etc.)?
4. Why must the HMAC be computed over the raw body and not over the parsed JSON?
5. Why `hmac.compare_digest` instead of `==`?
6. What would happen to your data if you didn't deduplicate by `X-GitHub-Delivery` and GitHub retried a delivery?
7. What happens if your ngrok tunnel disconnects during the ProManage project?

Good luck exposing your APIs to the world! 🚀
