import secrets
from flask import Flask, request, jsonify, redirect, url_for, session
from authlib.integrations.flask_client import OAuth
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity
from datetime import timedelta
import os

app = Flask(__name__)

# Secret key for session management (Authlib keeps the OAuth 'state' in the session)
# Never hardcode it: read it from the environment, random per run if unset
app.secret_key = os.environ.get('FLASK_SECRET_KEY') or secrets.token_hex(32)

# JWT Configuration
app.config['JWT_SECRET_KEY'] = os.environ.get('JWT_SECRET_KEY') or secrets.token_hex(32)  # from env; random per run if unset
app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(hours=1)
jwt = JWTManager(app)

# OAuth Configuration
oauth = OAuth(app)

# Credentials come ONLY from environment variables — never paste them into this file
# (see readme13.md, 'Part 2: Configure Your App')
for var in ('GITHUB_CLIENT_ID', 'GITHUB_CLIENT_SECRET'):
    if not os.environ.get(var):
        raise SystemExit(f"Missing {var}. Create a GitHub OAuth App and set it as an environment "
                         f"variable (see readme13.md, 'Part 2: Configure Your App').")

# TODO: Register GitHub as an OAuth provider (Authorization Code + PKCE)
# Hint: Use oauth.register() with name='github'
github = oauth.register(
    name='_____',  # TODO: Provider name
    client_id=os.environ['GITHUB_CLIENT_ID'],
    client_secret=os.environ['GITHUB_CLIENT_SECRET'],
    access_token_url='https://github.com/login/oauth/access_token',
    access_token_params=None,
    authorize_url='https://github.com/login/oauth/authorize',
    authorize_params=None,
    api_base_url='https://api.github.com/',
    # 'scope': request email scope
    # 'code_challenge_method': 'S256' turns PKCE on: Authlib creates a random code_verifier,
    # sends SHA-256(code_verifier) as code_challenge in the redirect, keeps the verifier in the
    # session and sends it with the code in the token request (OAuth 2.1 / RFC 9700)
    client_kwargs={'scope': 'user:email', 'code_challenge_method': 'S256'},
)

# In-memory user database, keyed by GitHub's numeric user id (as a string).
# The id never changes; the login (username) can be renamed, so it is only a display attribute.
users = {}

@app.route('/')
def home():
    """
    Home endpoint - provides API information and navigation links.

    Returns:
        200: Welcome message with available endpoints
    """
    return jsonify({
        'message': 'OAuth Authentication API (Authorization Code + PKCE)',
        'endpoints': {
            'GET /': 'This help message',
            'GET /login/github': 'Initiate GitHub OAuth login',
            'GET /callback': 'OAuth callback (handled automatically)',
            'GET /profile': 'Get user profile (requires JWT)',
            'GET /users': 'List all users (requires JWT)',
            'POST /logout': 'Logout (clears session)'
        },
        'flow': [
            '1. Visit /login/github in browser',
            '2. Authorize with GitHub',
            '3. Receive JWT token',
            '4. Use token for protected endpoints'
        ]
    }), 200


@app.route('/login/github')
def login_github():
    """
    Initiate OAuth login flow with GitHub.

    This redirects the user to GitHub's authorization page.
    After authorization, GitHub redirects back to /callback.

    Behind the scenes Authlib adds state (CSRF protection) and the PKCE
    code_challenge + code_challenge_method=S256 to the redirect URL.

    Returns:
        302: Redirect to GitHub authorization page
    """
    # TODO: Generate the redirect URL for the OAuth callback
    # Hint: Use url_for() to get the callback URL, set _external=True
    redirect_uri = url_for('_____', _external=True)

    # TODO: Redirect to GitHub's authorization page
    # Hint: Use github.authorize_redirect() with the redirect_uri
    return github._____(redirect_uri)


@app.route('/callback')
def callback():
    """
    OAuth callback endpoint - handles the redirect from GitHub.

    This endpoint:
    1. Receives the authorization code from GitHub (and checks state)
    2. Exchanges code + code_verifier (PKCE) for an access token
    3. Fetches user profile from GitHub API
    4. Creates/updates user in database, keyed by GitHub's stable numeric id
    5. Generates JWT token for our API (sub = that id, as a string)

    Returns:
        200: JWT token and user info on success
        400: Error if OAuth flow fails
    """
    try:
        # TODO: Exchange authorization code (+ PKCE code_verifier) for access token
        # Hint: Use github.authorize_access_token() - Authlib checks state and sends the verifier
        token = github._____()

        # TODO: Fetch user profile from GitHub API
        # Hint: Use github.get() with the endpoint 'user'
        response = github.get('_____')
        user_info = response.json()

        # Extract user data from GitHub response
        github_id = user_info.get('id')
        username = user_info.get('login')
        email = user_info.get('email')
        name = user_info.get('name')
        avatar_url = user_info.get('avatar_url')

        if github_id is None:
            raise ValueError('GitHub user info has no id')

        # Identify the user by GitHub's stable numeric id, never by login (it can be renamed).
        # JWT 'sub' must be a string, so we use the id's string form as the key and identity.
        user_id = str(github_id)

        # Store or update user in database (login, name... may have changed since last time)
        users[user_id] = {
            'github_id': github_id,
            'username': username,
            'email': email,
            'name': name,
            'avatar_url': avatar_url
        }

        # TODO: Create a JWT token for the user
        # Hint: Use create_access_token() with identity=user_id (GitHub id, not the login)
        access_token = _____(identity=user_id)

        return jsonify({
            'message': 'Login successful',
            'access_token': access_token,
            'token_type': 'Bearer',
            'user': {
                'id': user_id,
                'username': username,
                'email': email,
                'name': name,
                'avatar_url': avatar_url
            }
        }), 200

    except Exception:
        app.logger.exception('OAuth callback failed')
        return jsonify({
            'error': 'OAuth authentication failed',
            'message': 'Could not complete the login with GitHub. Start again at /login/github.'
        }), 400


@app.route('/profile', methods=['_____'])  # TODO: Set HTTP method (GET)
@jwt_required()  # Requires valid JWT token
def profile():
    """
    Get current user's profile information.

    Requires JWT token in Authorization header:
    Authorization: Bearer <token>

    Returns:
        200: User profile data
        401: Missing or invalid token
        404: User not found
    """
    # TODO: Get current user identity from JWT token (the GitHub id, as a string)
    # Hint: Use get_jwt_identity()
    current_user = _____()

    if current_user not in users:
        return jsonify({
            'error': 'User not found',
            'message': 'User profile does not exist'
        }), 404

    return jsonify({
        'user_id': current_user,
        'username': users[current_user]['username'],
        'profile': users[current_user]
    }), 200


@app.route('/users', methods=['GET'])
@jwt_required()  # Requires valid JWT token
def get_users():
    """
    Get list of all registered users.

    Requires JWT token in Authorization header.

    Returns:
        200: List of users (GitHub id + login)
        401: Missing or invalid token
    """
    user_list = [{'id': user_id, 'username': user['username']} for user_id, user in users.items()]
    return jsonify({
        'users': user_list,
        'count': len(user_list)
    }), 200


@app.route('/logout', methods=['POST'])
def logout():
    """
    Logout endpoint (clears session).

    Note: With JWT, true logout requires token blacklisting.
    This is a simplified version that just clears the session.

    Returns:
        200: Logout confirmation
    """
    session.clear()
    return jsonify({
        'message': 'Logged out successfully',
        'note': 'JWT tokens remain valid until expiration. Implement token blacklisting for true logout.'
    }), 200


# Error handlers
@app.errorhandler(404)
def not_found(e):
    """Handle 404 Not Found errors"""
    return jsonify({'error': 'Route not found'}), 404


@app.errorhandler(405)
def method_not_allowed(e):
    """Handle 405 Method Not Allowed errors"""
    return jsonify({'error': 'Method not allowed'}), 405


@app.errorhandler(500)
def internal_error(e):
    """Handle 500 Internal Server Error"""
    app.logger.error(f'Internal server error: {str(e)}')
    return jsonify({'error': 'Internal server error'}), 500


if __name__ == '__main__':
    print('='*60)
    print('OAuth Authentication API (Authorization Code + PKCE)')
    print('='*60)
    print('\nBefore running this app, you need to:')
    print('1. Create a GitHub OAuth App at:')
    print('   https://github.com/settings/developers')
    print('2. Set Authorization callback URL to:')
    print('   http://127.0.0.1:5000/callback')
    print('3. Set the environment variables GITHUB_CLIENT_ID and GITHUB_CLIENT_SECRET')
    print('\nStarting server at http://127.0.0.1:5000')
    print('Visit http://127.0.0.1:5000/ for instructions')
    print('='*60)
    app.run(debug=os.getenv("FLASK_DEBUG") == "1")
