"""
OAuth Authentication API (Starter)

Run it with:  fastapi dev app.py
Fill the blanks (_____) from top to bottom. Only blanks 7 and 8 (the /profile decorator and its
Depends) stop the app from starting; the other six fail only when a request reaches them.
"""

import logging
import os
import secrets
from datetime import datetime, timedelta, timezone
from typing import Annotated, Any

import jwt
from authlib.integrations.starlette_client import OAuth
from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from starlette.middleware.sessions import SessionMiddleware

app = FastAPI(title="OAuth Authentication API")

# Same logger that fastapi dev uses, so errors show up in your terminal
logger = logging.getLogger("uvicorn.error")

# SessionMiddleware keeps a signed cookie in the browser. Authlib stores the OAuth 'state'
# and the PKCE code_verifier in it while the user is at GitHub.
# Never hardcode the secret: read it from the environment, random per run if unset
app.add_middleware(SessionMiddleware, secret_key=os.environ.get("SESSION_SECRET") or secrets.token_hex(32))

# JWT Configuration
JWT_SECRET = os.environ.get("JWT_SECRET_KEY") or secrets.token_hex(32)  # from env; random per run if unset
JWT_ALG = "HS256"
ACCESS_TOKEN_MINUTES = 60

# HTTPBearer reads "Authorization: Bearer <token>" and hands us the token.
# auto_error=False lets us return our own 401 message and WWW-Authenticate header
# (FastAPI's default is a generic "401 Not authenticated").
bearer = HTTPBearer(auto_error=False)

# OAuth Configuration
oauth = OAuth()

# Register GitHub as an OAuth provider (Authorization Code + PKCE)
# Credentials come ONLY from environment variables, never commit them to the repo
for var in ("GITHUB_CLIENT_ID", "GITHUB_CLIENT_SECRET"):
    if not os.environ.get(var):
        raise SystemExit(f"Missing {var}. Create a GitHub OAuth App and set it as an environment "
                         f"variable (see readme13.md, 'Part 2: Configure Your App').")

# TODO: Register GitHub as an OAuth provider (Authorization Code + PKCE)
# Hint: oauth.register() needs name="github"; this name is how you reach it later as oauth.github
oauth.register(
    name="_____",  # TODO 1: Provider name
    client_id=os.environ["GITHUB_CLIENT_ID"],
    client_secret=os.environ["GITHUB_CLIENT_SECRET"],
    access_token_url="https://github.com/login/oauth/access_token",
    access_token_params=None,
    authorize_url="https://github.com/login/oauth/authorize",
    authorize_params=None,
    api_base_url="https://api.github.com/",
    # 'code_challenge_method': 'S256' turns PKCE on: Authlib creates a random code_verifier,
    # sends SHA-256(code_verifier) as code_challenge in the redirect, keeps the verifier in the
    # session and sends it with the code in the token request (OAuth 2.1 / RFC 9700)
    client_kwargs={"scope": "user:email", "code_challenge_method": "S256"},
)

# In-memory user database, keyed by GitHub's numeric user id (as a string).
# The id never changes; the login (username) can be renamed, so it is only a display attribute.
users: dict[str, dict[str, Any]] = {}


def create_access_token(user_id: str) -> str:
    now = datetime.now(timezone.utc)
    claims = {"sub": user_id, "iat": now, "exp": now + timedelta(minutes=ACCESS_TOKEN_MINUTES)}
    return jwt.encode(claims, JWT_SECRET, algorithm=JWT_ALG)


def get_current_user(creds: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer)]) -> str:
    """Dependency: returns the GitHub id (string) from the JWT, or answers 401 if it is missing, expired or invalid."""
    unauthorized = HTTPException(
        status_code=401,
        detail="Missing or invalid token",
        headers={"WWW-Authenticate": "Bearer"},
    )
    if creds is None:
        raise unauthorized
    try:
        claims = jwt.decode(creds.credentials, JWT_SECRET, algorithms=[JWT_ALG], options={"require": ["sub", "exp"]})
    except jwt.InvalidTokenError:  # expired, bad signature, malformed...
        raise unauthorized
    return claims["sub"]


# Routes that await Authlib are "async def" (Authlib's FastAPI/Starlette client is asynchronous).
# The others are plain "def", as in the previous exercises.

@app.get("/")
def home() -> dict[str, Any]:
    """
    Home endpoint - provides API information and navigation links.

    Returns:
        200: Welcome message with available endpoints
    """
    return {
        "message": "OAuth Authentication API (Authorization Code + PKCE)",
        "endpoints": {
            "GET /": "This help message",
            "GET /login/github": "Initiate GitHub OAuth login",
            "GET /callback": "OAuth callback (handled automatically)",
            "GET /profile": "Get user profile (requires JWT)",
            "GET /users": "List all users (requires JWT)",
            "POST /logout": "Logout (clears session)"
        },
        "flow": [
            "1. Visit /login/github in browser",
            "2. Authorize with GitHub",
            "3. Receive JWT token",
            "4. Use token for protected endpoints"
        ]
    }


@app.get("/login/github")
async def login_github(request: Request):
    """
    Initiate OAuth login flow with GitHub.

    This redirects the user to GitHub's authorization page.
    After authorization, GitHub redirects back to /callback.

    Behind the scenes Authlib adds state (CSRF protection) and the PKCE
    code_challenge + code_challenge_method=S256 to the redirect URL.

    Returns:
        302: Redirect to GitHub authorization page
    """
    # TODO 2: Generate the redirect URL for the OAuth callback
    # Hint: request.url_for() takes the NAME of the route function that handles the callback
    redirect_uri = str(request.url_for("_____"))

    # TODO 3: Redirect to GitHub's authorization page
    # Hint: oauth.github.authorize_redirect(request, redirect_uri), awaited
    return await oauth.github._____(request, redirect_uri)


@app.get("/callback")
async def callback(request: Request):
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
        # TODO 4: Exchange authorization code (+ PKCE code_verifier) for access token
        # Hint: oauth.github.authorize_access_token(request), awaited. Authlib checks state and sends the verifier
        token = await oauth.github._____(request)

        # TODO 5: Fetch user profile from GitHub API (this client needs the token passed in)
        # Hint: oauth.github.get() with the endpoint "user"
        response = await oauth.github.get("_____", token=token)
        user_info = response.json()

        # Extract user data from GitHub response
        github_id = user_info.get("id")
        username = user_info.get("login")
        email = user_info.get("email")
        name = user_info.get("name")
        avatar_url = user_info.get("avatar_url")

        if github_id is None:
            raise ValueError("GitHub user info has no id")

        # Identify the user by GitHub's stable numeric id, never by login (it can be renamed).
        # JWT 'sub' must be a string, so we use the id's string form as the key and identity.
        user_id = str(github_id)

        # Store or update user in database (login, name... may have changed since last time)
        users[user_id] = {
            "github_id": github_id,
            "username": username,
            "email": email,
            "name": name,
            "avatar_url": avatar_url
        }

        # TODO 6: Create a JWT token for the user
        # Hint: call create_access_token() (defined above) with user_id (GitHub id, not the login)
        access_token = _____(user_id)

        return {
            "message": "Login successful",
            "access_token": access_token,
            "token_type": "Bearer",
            "user": {
                "id": user_id,
                "username": username,
                "email": email,
                "name": name,
                "avatar_url": avatar_url
            }
        }

    except Exception:
        logger.exception("OAuth callback failed")
        return JSONResponse(status_code=400, content={
            "error": "OAuth authentication failed",
            "message": "Could not complete the login with GitHub. Start again at /login/github."
        })


# TODO 7: Set the HTTP method of the decorator (get)
# TODO 8: Depends(...) takes the dependency that reads the user from the JWT
# Hint: it is defined above, near the top of the file
@app._____("/profile")
def profile(current_user: Annotated[str, Depends(_____)]) -> dict[str, Any]:
    """
    Get current user's profile information.

    Requires JWT token in Authorization header:
    Authorization: Bearer <token>

    Returns:
        200: User profile data
        401: Missing or invalid token
        404: User not found
    """
    # current_user is the GitHub id (as a string), read from the JWT by get_current_user
    if current_user not in users:
        raise HTTPException(status_code=404, detail="User profile does not exist")

    return {
        "user_id": current_user,
        "username": users[current_user]["username"],
        "profile": users[current_user]
    }


@app.get("/users")
def get_users(current_user: Annotated[str, Depends(get_current_user)]) -> dict[str, Any]:
    """
    Get list of all registered users.

    Requires JWT token in Authorization header.

    Returns:
        200: List of users (GitHub id + login)
        401: Missing or invalid token
    """
    user_list = [{"id": user_id, "username": user["username"]} for user_id, user in users.items()]
    return {
        "users": user_list,
        "count": len(user_list)
    }


@app.post("/logout")
def logout(request: Request) -> dict[str, str]:
    """
    Logout endpoint (clears session).

    Note: With JWT, true logout requires token blacklisting.
    This is a simplified version that just clears the session.

    Returns:
        200: Logout confirmation
    """
    request.session.clear()
    return {
        "message": "Logged out successfully",
        "note": "JWT tokens remain valid until expiration. Implement token blacklisting for true logout."
    }
