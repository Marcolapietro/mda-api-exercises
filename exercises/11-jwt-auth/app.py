import os
import secrets
from datetime import timedelta
from flask import Flask, jsonify, request
from werkzeug.security import generate_password_hash, check_password_hash
from flask_jwt_extended import (
    JWTManager, create_access_token, create_refresh_token,
    jwt_required, get_jwt_identity, get_jwt
)

app = Flask(__name__)

# JWT Configuration
# The secret comes from the environment. If it is not set, a random one is
# generated on every start (tokens stop working after a restart).
app.config['JWT_SECRET_KEY'] = os.environ.get('JWT_SECRET_KEY') or secrets.token_hex(32)  # from env; random per run if unset

# Short-lived access tokens + longer-lived refresh tokens
app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(minutes=_____)  # TODO: Access tokens live 15 minutes
app.config['JWT_REFRESH_TOKEN_EXPIRES'] = timedelta(days=1)

# Issuer (iss = who created the token) and audience (aud = who the token is for)
# ENCODE: written into every token we create
# DECODE: required on every token we receive (otherwise 422 "Invalid ...")
JWT_ISSUER = 'mda-api-exercises'
JWT_AUDIENCE = 'mda-api-clients'
app.config['JWT_ENCODE_ISSUER'] = JWT_ISSUER
app.config['_____'] = JWT_ISSUER  # TODO: Which key makes the server REJECT tokens from another issuer?
# Hint: JWT_DECODE_ISSUER
app.config['JWT_ENCODE_AUDIENCE'] = JWT_AUDIENCE
app.config['_____'] = JWT_AUDIENCE  # TODO: Which key makes the server REJECT tokens meant for another API?
# Hint: JWT_DECODE_AUDIENCE

jwt = _____  # TODO: Initialize JWTManager with the app
# Hint: JWTManager(app)

# Simulated database to store users
users = {
    # 'username': {'password': 'hashed_password'}
}

# Revoked tokens (by their unique id, the "jti" claim).
# In memory for this exercise: it is lost on restart. Use Redis or a DB in production.
revoked_tokens = set()

# Hash used when the username does not exist, so that a login attempt with an
# unknown user takes as long as one with a wrong password (no user enumeration)
DUMMY_PASSWORD_HASH = generate_password_hash(secrets.token_urlsafe(16))


@jwt.token_in_blocklist_loader
def is_token_revoked(jwt_header, jwt_payload):
    """Called by @jwt_required() on every request: True means 'reject this token'"""
    return jwt_payload['_____'] in revoked_tokens  # TODO: Which claim is the token's unique id?
    # Hint: 'jti' (JWT ID)


# ============================================================================
# PUBLIC ENDPOINTS (No authentication required)
# ============================================================================

@app.route('/register', methods=['POST'])
def register():
    """Register a new user - Public endpoint"""
    data = request.get_json()

    if not data:
        return jsonify({'error': 'Request body must be JSON'}), 400

    username = data.get('username')
    password = data.get('password')

    # Validate input
    if not username or not password:
        return jsonify({'error': 'Username and password are required'}), 400

    if username in users:
        return jsonify({'error': 'User already exists'}), 409

    # Hash the password before storing it
    users[username] = {
        'password': generate_password_hash(password)
    }

    return jsonify({
        'message': 'User registered successfully',
        'username': username
    }), 201


@app.route('/login', methods=['POST'])
def login():
    """
    Authenticate user and return JWT tokens - Public endpoint

    This is the KEY difference from Basic Auth:
    - User sends username/password ONCE in the request body
    - Server validates credentials and returns an access token + a refresh token
    - Client sends the access token with every request (valid 15 minutes)
    - When it expires, the client uses the refresh token on POST /refresh
    """
    data = request.get_json()

    if not data:
        return jsonify({'error': 'Request body must be JSON'}), 400

    username = data.get('username')
    password = data.get('password')

    # Validate input
    if not username or not password:
        return jsonify({'error': 'Username and password are required'}), 400

    # Always run a password check, even for unknown users, so both failure
    # cases take the same time and an attacker cannot tell which usernames exist
    user = users.get(username)
    password_hash = user['password'] if user else _____  # TODO: Check against a dummy hash if the user is unknown
    # Hint: DUMMY_PASSWORD_HASH
    password_ok = check_password_hash(password_hash, password)

    if not user or not password_ok:
        return jsonify({'error': 'Invalid credentials'}), 401

    # Create JWT tokens with user identity
    access_token = _____(identity=username)  # TODO: Create access token
    # Hint: Use create_access_token(identity=username)
    refresh_token = _____(identity=username)  # TODO: Create refresh token
    # Hint: Use create_refresh_token(identity=username)

    return jsonify({
        'message': 'Login successful',
        'access_token': access_token,
        'refresh_token': refresh_token,
        'token_type': 'Bearer',
        'expires_in': int(app.config['JWT_ACCESS_TOKEN_EXPIRES'].total_seconds())
    }), 200


# ============================================================================
# TOKEN MANAGEMENT ENDPOINTS
# ============================================================================

@app.route('/refresh', methods=['POST'])
@jwt_required(refresh=_____)  # TODO: Accept ONLY refresh tokens here
# Hint: refresh=True
def refresh():
    """
    Get a new access token - Requires a REFRESH token

    Authorization: Bearer <refresh_token>
    An access token is rejected here, and a refresh token is rejected everywhere else.
    """
    current_user = get_jwt_identity()
    access_token = create_access_token(identity=current_user)

    return jsonify({
        'access_token': access_token,
        'token_type': 'Bearer',
        'expires_in': int(app.config['JWT_ACCESS_TOKEN_EXPIRES'].total_seconds())
    }), 200


@app.route('/logout', methods=['POST'])
@jwt_required(verify_type=False)
def logout():
    """
    Revoke the token sent in the Authorization header - Requires any JWT

    Call it once with the access token and once with the refresh token
    to fully log out.
    """
    token = get_jwt()
    revoked_tokens.add(token['jti'])

    return jsonify({
        'message': f"{token['type'].capitalize()} token revoked"
    }), 200


# ============================================================================
# PROTECTED ENDPOINTS (JWT authentication required)
# ============================================================================

@app.route('/profile', methods=['GET'])
@_____  # TODO: Add JWT required decorator
# Hint: @jwt_required()
def profile():
    """
    Get current user's profile - Protected endpoint

    This endpoint requires a valid JWT token in the Authorization header:
    Authorization: Bearer <token>
    """
    # Extract the user identity from the JWT token
    current_user = _____  # TODO: Get JWT identity
    # Hint: Use get_jwt_identity()

    # In a real application, you would fetch user data from a database
    user_info = {
        'username': current_user,
        'profile': f'Profile information for {current_user}',
        'account_created': '2025-01-01'  # Example data
    }

    return jsonify(user_info), 200


@app.route('/users', methods=['GET'])
@_____  # TODO: Add JWT required decorator
# Hint: @jwt_required()
def get_users():
    """
    Get list of all users - Protected endpoint

    Requires valid JWT token to access this resource.
    """
    current_user = get_jwt_identity()

    return jsonify({
        'users': list(users.keys()),
        'requested_by': current_user
    }), 200


@app.route('/protected', methods=['GET'])
@jwt_required()
def protected():
    """
    Example protected endpoint - Requires JWT

    This demonstrates that ANY endpoint can be protected with @jwt_required()
    """
    current_user = get_jwt_identity()

    return jsonify({
        'message': f'Hello {current_user}, you have access to this protected resource!',
        'tip': 'This endpoint can only be accessed with a valid JWT token'
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
    print("JWT Authentication API Server")
    print("="*70)
    if not os.environ.get('JWT_SECRET_KEY'):
        print("\nNOTE: JWT_SECRET_KEY not set, using a random secret.")
        print("      Tokens will stop working when the server restarts.")
    print("\nPublic endpoints (no auth required):")
    print("  POST /register  - Register a new user")
    print("  POST /login     - Login and get access + refresh tokens")
    print("\nToken management:")
    print("  POST /refresh   - New access token (requires REFRESH token)")
    print("  POST /logout    - Revoke the token you send")
    print("\nProtected endpoints (access token required):")
    print("  GET  /profile   - Get user profile")
    print("  GET  /users     - Get all users")
    print("  GET  /protected - Example protected resource")
    print("\nServer running at: http://127.0.0.1:5000")
    print("="*70 + "\n")

    app.run(debug=os.getenv("FLASK_DEBUG") == "1")
