import os
import hashlib
import hmac
import secrets
from flask import Flask, jsonify, request
from flask_httpauth import HTTPBasicAuth
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps

app = Flask(__name__)
auth = HTTPBasicAuth()

# Recognisable prefix for our keys ("sk_" = secret key).
# Secret scanners (GitHub, GitLab, gitleaks...) search for known prefixes,
# so a leaked key is easier to detect automatically.
API_KEY_PREFIX = 'sk_'

# Simulated database to store users.
# We NEVER store the API key itself, only its SHA-256 hash.
users = {
    # 'username': {
    #     'password': 'hashed_password (werkzeug)',
    #     'api_key_hash': 'sha256_hex_of_the_api_key'  (None if revoked)
    # }
}

# Hash used when the username does not exist, so that a login attempt with an
# unknown user takes as long as one with a wrong password (no user enumeration)
DUMMY_PASSWORD_HASH = generate_password_hash(secrets.token_urlsafe(16))


# ============================================================================
# API KEY HELPERS (generate, hash, look up)
# ============================================================================

def generate_api_key():
    """Generate a new random API key (about 256 bits of entropy)."""
    # TODO: Generate a cryptographically secure, URL-safe random string of 32 bytes
    # Hint: secrets.token_urlsafe(32)  (do NOT use uuid4 or random for secrets)
    return API_KEY_PREFIX + secrets._____(32)


def hash_api_key(api_key):
    """
    Hash an API key with SHA-256.

    A fast hash is fine here because the key is long and random: there is
    nothing to guess. Passwords are short and human-chosen, so they need a
    slow, salted hash (werkzeug's generate_password_hash) instead.
    """
    # TODO: Hash the key with SHA-256 and return it as a hex string
    # Hint: hashlib.sha256(...).hexdigest()
    return hashlib._____(api_key.encode('utf-8')).hexdigest()


def find_user_by_api_key(api_key):
    """Return the username that owns this API key, or None."""
    candidate_hash = hash_api_key(api_key)

    for username, user_data in users.items():
        stored_hash = user_data.get('api_key_hash')
        # TODO: Compare the hashes in constant time (never use == for secrets)
        # Hint: hmac.compare_digest(a, b) takes the same time wherever a and b differ
        if stored_hash and hmac._____(stored_hash, candidate_hash):
            return username

    return None


# ============================================================================
# BASIC AUTH VERIFICATION (for key rotation and revocation only)
# ============================================================================

@auth.verify_password
def verify_password(username, password):
    """Verify username and password for Basic Auth"""
    user = users.get(username)

    # Always run a password check, even for unknown users (same response time)
    password_hash = user['password'] if user else DUMMY_PASSWORD_HASH
    password_ok = check_password_hash(password_hash, password)

    if user and password_ok:
        return username
    return None


# ============================================================================
# API KEY DECORATOR (for protecting endpoints with API keys)
# ============================================================================

def api_key_required(f):
    """
    Decorator to protect routes with API key authentication.

    Checks the 'X-API-Key' header and validates it against the stored hashes.
    This is an ALTERNATIVE to Basic Auth, not used together.
    """
    @wraps(f)
    def decorated(*args, **kwargs):
        # TODO: Get the API key from request headers (header name: 'X-API-Key')
        api_key = request.headers.get('_____')  # Hint: header names are case-insensitive

        if not api_key:
            return jsonify({'error': 'API key missing', 'message': 'Include X-API-Key header'}), 401

        # Look up the key by its hash
        if find_user_by_api_key(api_key) is None:
            return jsonify({'error': 'Invalid API key', 'message': 'API key not recognized'}), 401

        # API key is valid, call the protected function
        return f(*args, **kwargs)

    return decorated


# ============================================================================
# PUBLIC ENDPOINTS (no authentication required)
# ============================================================================

@app.route('/register', methods=['POST'])
def register():
    """Register a new user and return their API key (ONCE) - Public endpoint"""
    data = request.get_json()

    if not data:
        return jsonify({'error': 'Request body must be JSON'}), 400

    username = data.get('username')
    password = data.get('password')

    if not username or not password:
        return jsonify({'error': 'Username and password are required'}), 400

    if username in users:
        return jsonify({'error': 'User already exists'}), 409

    # Generate a random API key
    api_key = generate_api_key()

    # Store user with hashed password and HASHED API key
    users[username] = {
        'password': generate_password_hash(password),
        'api_key_hash': _____  # TODO: Store the HASH of the key, never the key itself
                               # Hint: hash_api_key(api_key)
    }

    # This is the only time the plain key is shown
    return jsonify({
        'message': 'User registered successfully',
        'username': username,
        'api_key': api_key,
        'warning': 'Store this API key now. It will not be shown again.'
    }), 201


# ============================================================================
# BASIC AUTH PROTECTED ENDPOINTS (key rotation and revocation)
# ============================================================================

@app.route('/api-key/rotate', methods=['_____'])  # TODO: Which HTTP method creates something new?
@auth.login_required
def rotate_api_key():
    """
    Issue a new API key and invalidate the old one - Protected by Basic Auth

    Use it if you lost your key, if it leaked, or as routine rotation.
    The server cannot "recover" a key: it only has its hash.
    """
    current_user = auth.current_user()

    new_api_key = generate_api_key()

    # TODO: Overwrite the stored hash with the hash of the NEW key
    # (this invalidates the old key immediately)
    users[current_user]['api_key_hash'] = _____  # Hint: hash_api_key(new_api_key)

    return jsonify({
        'message': 'API key rotated. The previous key no longer works.',
        'username': current_user,
        'api_key': new_api_key,
        'warning': 'Store this API key now. It will not be shown again.'
    }), 200


@app.route('/api-key', methods=['DELETE'])
@auth.login_required
def revoke_api_key():
    """Revoke the current API key without issuing a new one - Protected by Basic Auth"""
    current_user = auth.current_user()

    users[current_user]['api_key_hash'] = None

    return jsonify({
        'message': 'API key revoked. Use POST /api-key/rotate to get a new one.',
        'username': current_user
    }), 200


# ============================================================================
# API KEY PROTECTED ENDPOINTS (the main pattern to learn)
# ============================================================================

@app.route('/users', methods=['GET'])
@_____  # TODO: Apply the API key decorator to protect this route
def get_users():
    """
    Get list of all users - Protected by API key

    This endpoint demonstrates API key authentication.
    Clients must include 'X-API-Key' header with a valid API key.
    """
    user_list = list(users.keys())
    return jsonify({
        'users': user_list,
        'count': len(user_list)
    }), 200


# ============================================================================
# ERROR HANDLERS
# ============================================================================

@app.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Resource not found'}), 404

@app.errorhandler(405)
def method_not_allowed(error):
    return jsonify({'error': 'Method not allowed'}), 405


if __name__ == '__main__':
    print("\n" + "="*70)
    print("Exercise 5: API Key Authentication")
    print("="*70)
    print("\nPublic endpoints:")
    print("  POST   /register        - Register new user, receive API key (shown once)")
    print("\nBasic Auth protected endpoints:")
    print("  POST   /api-key/rotate  - Get a new API key, old one stops working")
    print("  DELETE /api-key         - Revoke your API key")
    print("\nAPI Key protected endpoints:")
    print("  GET    /users           - List all users (requires X-API-Key header)")
    print("\nExamples:")
    print("  curl -X POST -H 'Content-Type: application/json' \\")
    print("       -d '{\"username\":\"alice\",\"password\":\"secret123\"}' \\")
    print("       http://127.0.0.1:5000/register")
    print("\n  curl -H 'X-API-Key: YOUR_API_KEY' http://127.0.0.1:5000/users")
    print("\nServer running at: http://127.0.0.1:5000")
    print("="*70 + "\n")

    app.run(debug=os.getenv("FLASK_DEBUG") == "1")
