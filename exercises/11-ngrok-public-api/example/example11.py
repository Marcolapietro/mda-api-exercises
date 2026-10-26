import hashlib
import hmac
import os
from flask import Flask, request, jsonify

app = Flask(__name__)

# In-memory storage for demonstration
users = {}
webhook_events = []

# Delivery IDs already processed. GitHub retries failed deliveries (and you can press
# "Redeliver"), and every retry carries the SAME X-GitHub-Delivery ID.
processed_deliveries = set()


@app.route('/health', methods=['GET'])
def health():
    """
    Health check endpoint to verify the API is running.
    This is useful for testing that ngrok is working correctly.
    """
    return jsonify({
        'status': 'ok',
        'service': 'github-webhook-demo',
        'version': '1.0',
        'message': 'API is running and accessible!'
    }), 200


@app.route('/info', methods=['GET'])
def info():
    """
    Returns information about the incoming request.
    Useful for debugging ngrok forwarding.
    """
    return jsonify({
        'your_ip': request.remote_addr,
        'your_user_agent': request.headers.get('User-Agent'),
        'host': request.host,
        'path': request.path,
        'method': request.method,
        # Never echo credentials back: this endpoint is public once ngrok is running
        'headers': {k: v for k, v in request.headers.items()
                    if k.lower() not in ('authorization', 'cookie', 'x-api-key',
                                         'x-hub-signature', 'x-hub-signature-256')}
    }), 200


@app.route('/users', methods=['GET', 'POST'])
def users_endpoint():
    """
    Simple user management for testing team collaboration.

    GET: List all users
    POST: Create a new user
    """
    if request.method == 'GET':
        return jsonify(list(users.values())), 200

    # POST: Create user
    data = request.get_json()
    if not data:
        return jsonify({'error': 'Invalid JSON'}), 400

    username = data.get('username')
    email = data.get('email')

    if not username:
        return jsonify({'error': 'username is required'}), 400

    if username in users:
        return jsonify({'error': 'User already exists'}), 409

    user = {
        'username': username,
        'email': email,
        'id': len(users) + 1
    }
    users[username] = user

    return jsonify(user), 201


# ============================================================================
# WEBHOOK SIGNATURE VERIFICATION (HMAC-SHA256) - COMPLETE SOLUTION
# ============================================================================

def verify_github_signature(payload_body, signature_header, secret):
    """
    Returns True only if `signature_header` is a valid GitHub signature for `payload_body`.

    GitHub computes HMAC-SHA256(secret, raw request body) and sends it as:
        X-Hub-Signature-256: sha256=<hex digest>

    payload_body:     the RAW bytes of the request body (request.get_data()), not the parsed JSON
    signature_header: the value of the X-Hub-Signature-256 header (may be None)
    secret:           the shared secret you typed in GitHub's webhook "Secret" field
    """
    # Only accept the SHA-256 format. Reject a missing header, the legacy "sha1=..." header
    # format, or anything else.
    if not signature_header or not signature_header.startswith('sha256='):
        return False
    received_signature = signature_header[len('sha256='):]

    # Recompute the signature over the exact bytes we received
    expected_signature = hmac.new(secret.encode(), payload_body, hashlib.sha256).hexdigest()

    # Constant-time comparison: '==' stops at the first different character, which leaks
    # timing information an attacker can use to guess the signature byte by byte
    return hmac.compare_digest(expected_signature, received_signature)


# ============================================================================
# GITHUB WEBHOOK ENDPOINT - COMPLETE SOLUTION
# ============================================================================

@app.route('/webhooks/github', methods=['POST'])
def github_webhook():
    """
    Receives REAL push events from GitHub.

    When you configure a webhook in GitHub repository settings, it sends POST
    requests to this endpoint with information about repository events.

    Security steps, in this order:
    1. Refuse to work without a configured secret (never accept unsigned requests)
    2. Verify X-Hub-Signature-256 over the RAW body          -> 401 if missing/invalid
    3. Deduplicate by X-GitHub-Delivery (retries happen)      -> 200 "duplicate, ignored"
    4. Store a minimal record and answer 2xx quickly

    Official documentation: https://docs.github.com/en/webhooks/webhook-events-and-payloads
    Signature validation:   https://docs.github.com/en/webhooks/using-webhooks/validating-webhook-deliveries
    """
    # 1. The secret comes ONLY from the environment. Without it we cannot verify anything,
    #    so we refuse to process instead of silently accepting unsigned requests.
    secret = os.environ.get('GITHUB_WEBHOOK_SECRET')
    if not secret:
        return jsonify({
            'error': 'Webhook secret not configured',
            'message': 'Set the GITHUB_WEBHOOK_SECRET environment variable and restart the app.'
        }), 503

    # 2. Verify the signature on the RAW body, before parsing or trusting anything in it.
    #    Re-serialising the parsed JSON would change spaces/key order and break the HMAC.
    body = request.get_data()
    signature = request.headers.get('X-Hub-Signature-256')
    if not verify_github_signature(body, signature, secret):
        print("⚠️  Invalid or missing X-Hub-Signature-256 - rejecting webhook")
        return jsonify({
            'error': 'Unauthorized',
            'message': 'Missing or invalid X-Hub-Signature-256 signature'
        }), 401

    # 3. Deduplicate: GitHub may deliver the same event more than once
    delivery_id = request.headers.get('X-GitHub-Delivery')
    if not delivery_id:
        return jsonify({'error': 'Bad Request', 'message': 'Missing X-GitHub-Delivery header'}), 400

    if delivery_id in processed_deliveries:
        print(f"🔁 Duplicate delivery {delivery_id} - ignored")
        return jsonify({'status': 'duplicate, ignored', 'delivery_id': delivery_id}), 200

    # Only now is it safe to parse the payload
    data = request.get_json(silent=True)

    if not data:
        return jsonify({
            'error': 'Invalid payload',
            'message': "Expected a JSON body (set Content type to 'application/json' in GitHub)"
        }), 400

    # Handle GitHub "ping" event (sent when webhook is first created)
    # This confirms your webhook endpoint is reachable
    if 'zen' in data and 'hook_id' in data:
        processed_deliveries.add(delivery_id)
        print(f"\n{'='*60}")
        print(f"📥 GitHub Webhook Ping Received!")
        print(f"   Hook ID: {data.get('hook_id')}")
        print(f"   Zen: {data.get('zen')}")
        print(f"   ✅ Webhook is configured correctly (and the signature is valid)!")
        print(f"{'='*60}\n")
        return jsonify({'status': 'pong'}), 200

    # Extract repository info from real GitHub payload
    repository = data.get('repository', {})
    repo_name = repository.get('full_name', 'unknown') if repository else 'unknown'

    # Extract pusher info (who pushed the code)
    pusher = data.get('pusher', {})
    pusher_name = pusher.get('name', 'unknown') if pusher else 'unknown'

    # Extract commits list
    commits = data.get('commits', [])

    # Extract ref (which branch was pushed)
    ref = data.get('ref', 'unknown')

    # Log the webhook with detailed output
    print(f"\n{'='*60}")
    print(f"🎉 REAL GitHub Webhook Received!")
    print(f"🆔 Delivery: {delivery_id}")
    print(f"📦 Repository: {repo_name}")
    print(f"👤 Pushed by: {pusher_name}")
    print(f"🌿 Branch: {ref}")
    print(f"📝 Commits: {len(commits)}")

    # Show details of each commit
    for i, commit in enumerate(commits, 1):
        commit_msg = commit.get('message', 'No message')
        commit_id = commit.get('id', 'unknown')[:7]  # Short SHA (first 7 chars)
        author = commit.get('author', {}).get('name', 'unknown')
        print(f"   {i}. [{commit_id}] {commit_msg} (by {author})")

    print(f"{'='*60}\n")

    # 4. Store a minimal record (fast). In a real system you would put the event on a
    #    queue here and let a background worker do the slow work (run tests, deploy...).
    webhook_event = {
        'type': 'github_push',
        'delivery_id': delivery_id,
        'repository': repo_name,
        'pusher': pusher_name,
        'ref': ref,
        'commits_count': len(commits),
        'commit_messages': [c.get('message', '') for c in commits]
    }
    webhook_events.append(webhook_event)

    # Remember this delivery so a retry with the same ID is not stored twice
    processed_deliveries.add(delivery_id)

    # GitHub expects a 2xx status quickly (it times out after 10 seconds)
    # If you return non-2xx, GitHub will mark the webhook as failed
    return jsonify({'status': 'received', 'commits_processed': len(commits)}), 200


# ============================================================================
# MONITORING AND DEBUGGING
# ============================================================================

@app.route('/webhooks/events', methods=['GET'])
def list_webhook_events():
    """
    Returns all received webhook events.
    Useful for debugging and verifying webhooks were received.
    """
    return jsonify({
        'total_events': len(webhook_events),
        'events': webhook_events
    }), 200


@app.route('/webhooks/events/clear', methods=['POST'])
def clear_webhook_events():
    """
    Clears all stored webhook events and the list of processed delivery IDs.
    Useful for testing - start fresh.
    """
    global webhook_events
    count = len(webhook_events)
    webhook_events = []
    processed_deliveries.clear()
    return jsonify({
        'message': f'Cleared {count} webhook events',
        'remaining': 0
    }), 200


# ============================================================================
# REQUEST LOGGING (for debugging)
# ============================================================================

@app.before_request
def log_request():
    """
    Logs all incoming requests.
    This helps you see traffic coming through ngrok.
    """
    # Skip logging for some paths to reduce noise
    if request.path in ['/favicon.ico']:
        return

    print(f"\n{'='*60}")
    print(f"📨 Incoming Request:")
    print(f"   Method: {request.method}")
    print(f"   Path: {request.path}")
    print(f"   From: {request.remote_addr}")
    print(f"   User-Agent: {request.headers.get('User-Agent', 'Unknown')[:50]}")

    # Show request body for POST/PUT requests
    # (get_json caches the raw bytes, so request.get_data() still works in the webhook)
    if request.method in ['POST', 'PUT', 'PATCH']:
        body = request.get_json(silent=True)
        if body:
            print(f"   Body: {body}")

    print(f"{'='*60}\n")


# ============================================================================
# ERROR HANDLERS
# ============================================================================

@app.errorhandler(404)
def not_found(error):
    return jsonify({
        'error': 'Not Found',
        'message': f'The endpoint {request.path} does not exist',
        'tip': 'Try /health to verify the API is running'
    }), 404


@app.errorhandler(405)
def method_not_allowed(error):
    return jsonify({
        'error': 'Method Not Allowed',
        'message': f'{request.method} is not allowed for {request.path}'
    }), 405


@app.errorhandler(500)
def internal_error(error):
    app.logger.error(f'Internal server error: {str(error)}')
    return jsonify({
        'error': 'Internal Server Error',
        'message': 'Something went wrong on the server'
    }), 500


# ============================================================================
# MAIN
# ============================================================================

if __name__ == '__main__':
    print("\n" + "="*70)
    print("🌐 GitHub Webhook Demo - ngrok Exercise (COMPLETE SOLUTION)")
    print("="*70)
    if not os.environ.get('GITHUB_WEBHOOK_SECRET'):
        print("⚠️  WARNING: GITHUB_WEBHOOK_SECRET is not set.")
        print("   /webhooks/github will answer 503 until you set it and restart.")
        print('   Generate one with: python -c "import secrets; print(secrets.token_hex(32))"')
        print("="*70)
    print("Running on: http://127.0.0.1:5000")
    print("\nQuick Start:")
    print("1. Set GITHUB_WEBHOOK_SECRET in this terminal (see readme11.md, Task 2.2)")
    print("2. In another terminal, run: ngrok http 5000")
    print("3. Copy the https://....ngrok-free.app URL")
    print("4. Configure GitHub webhook with that URL + /webhooks/github and the SAME secret")
    print("5. Make a commit to trigger the webhook!")
    print("\nEndpoints available:")
    print("  GET  /health                - Health check")
    print("  GET  /info                  - Request debugging info")
    print("  GET  /users                 - List users")
    print("  POST /users                 - Create user")
    print("  POST /webhooks/github       - GitHub push webhook (MAIN ENDPOINT, signed)")
    print("  GET  /webhooks/events       - List all received webhooks")
    print("  POST /webhooks/events/clear - Clear webhook history")
    print("\nFor detailed instructions, see readme11.md")
    print("="*70 + "\n")

    app.run(debug=os.getenv("FLASK_DEBUG") == "1", port=5000)
