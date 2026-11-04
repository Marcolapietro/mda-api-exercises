"""
Exercise 14: Rate Limiting and API Security - STARTER
Learn to protect your API from abuse using slowapi
"""

import os
import secrets
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Annotated

import bcrypt
import jwt
from dotenv import load_dotenv
from fastapi import Depends, FastAPI, HTTPException, Query, Request, Response
from fastapi.responses import JSONResponse
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel, Field, field_validator
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from slowapi.util import get_remote_address

# Load the .env of this folder (next to .env.example); a variable set in the terminal wins
load_dotenv(Path(__file__).resolve().parent / ".env")

app = FastAPI(title="Rate Limiting API")

# JWT Configuration
JWT_SECRET = os.environ.get("JWT_SECRET_KEY") or secrets.token_hex(32)  # from env; random per run if unset
JWT_ALG = "HS256"
ACCESS_TOKEN_HOURS = 1

# HTTPBearer reads "Authorization: Bearer <token>". auto_error=False lets us return our own
# 401 message and WWW-Authenticate header (FastAPI's default is a generic "401 Not authenticated").
bearer = HTTPBearer(auto_error=False)

# TODO: Initialize slowapi
# Hint: limiter = Limiter(key_func=get_remote_address, default_limits=["200/day", "50/hour"])
limiter = Limiter(
    key_func=_____,  # TODO: What function determines who is making the request?
    default_limits=_____,  # TODO: Set default limits (e.g., ["200/day", "50/hour"])
    headers_enabled=True,  # send X-RateLimit-* and Retry-After headers
    storage_uri="memory://",  # in-memory storage (use Redis in production)
)
app.state.limiter = limiter  # slowapi looks the limiter up here
app.add_middleware(SlowAPIMiddleware)  # applies the default limits (and honours @limiter.exempt)

# In-memory data storage
users: dict[str, dict[str, str]] = {}  # {username: {"password": bcrypt hash, "role": "user"}}
api_calls: dict[str, int] = {}  # Track API usage per user


# ==================== Helper Functions ====================

def hash_password(pw: str) -> str:
    return bcrypt.hashpw(pw.encode(), bcrypt.gensalt()).decode()


def verify_password(pw: str, hashed: str) -> bool:
    try:
        return bcrypt.checkpw(pw.encode(), hashed.encode())
    except ValueError:  # bcrypt only accepts passwords of up to 72 bytes
        return False


# Compared against when the user does not exist, so both failures take the same time
DUMMY_HASH = hash_password("not-a-real-password")


class UserCreate(BaseModel):
    username: str = Field(min_length=1)
    password: str = Field(min_length=8, max_length=72)

    @field_validator("password")
    @classmethod
    def password_fits_bcrypt(cls, pw: str) -> str:
        if len(pw.encode()) > 72:  # bcrypt counts bytes, not characters
            raise ValueError("password must be at most 72 bytes")
        return pw


class Credentials(BaseModel):
    # Plain str: wrong credentials must answer 401, never 422
    username: str
    password: str


def create_access_token(username: str, role: str) -> str:
    now = datetime.now(timezone.utc)
    claims = {"sub": username, "role": role, "iat": now, "exp": now + timedelta(hours=ACCESS_TOKEN_HOURS)}
    return jwt.encode(claims, JWT_SECRET, algorithm=JWT_ALG)


def current_user(creds: HTTPAuthorizationCredentials | None) -> str:
    """Return the username from the Bearer token, or answer 401."""
    if creds is None:
        raise HTTPException(status_code=401, detail="Missing or invalid token", headers={"WWW-Authenticate": "Bearer"})
    try:
        claims = jwt.decode(creds.credentials, JWT_SECRET, algorithms=[JWT_ALG], options={"require": ["sub", "exp"]})
    except jwt.InvalidTokenError:  # expired, bad signature, malformed...
        raise HTTPException(status_code=401, detail="Invalid token", headers={"WWW-Authenticate": "Bearer"})
    return claims["sub"]


# ==================== Routes ====================

@app.get("/health")
@limiter.exempt  # Health checks should not be rate limited
def health() -> dict[str, str]:
    """Health check endpoint - no rate limiting"""
    return {"status": "ok", "message": "API is running"}


@app.post("/register", status_code=201)
# TODO: Add rate limit to prevent spam registrations
# Hint: @limiter.limit("5/hour")
@limiter.limit(_____)
def register(request: Request, response: Response, data: UserCreate) -> dict[str, str]:
    """
    Register a new user
    Rate limited to prevent automated account creation
    """
    if data.username in users:
        raise HTTPException(status_code=409, detail="User already exists")

    # Store user with hashed password. The role is never taken from the request body
    # (prevents self-registering as admin)
    users[data.username] = {"password": hash_password(data.password), "role": "user"}

    return {"message": f"User {data.username} registered successfully"}


@app.post("/login")
# TODO: Add rate limit to prevent brute force attacks
# Hint: @limiter.limit("10/minute")
@limiter.limit(_____)
def login(request: Request, response: Response, data: Credentials) -> dict[str, str]:
    """
    Login endpoint with rate limiting to prevent brute force attacks
    Limited to 10 attempts per minute per IP address
    """
    user = users.get(data.username)
    # Always run the bcrypt check, even for an unknown user, so timing does not reveal who exists
    password_ok = verify_password(data.password, user["password"] if user else DUMMY_HASH)
    if user is None or not password_ok:
        raise HTTPException(status_code=401, detail="Invalid credentials")

    return {
        "access_token": create_access_token(data.username, user["role"]),
        "token_type": "bearer",
        "username": data.username,
        "role": user["role"],
    }


@app.get("/api/data")
# TODO: Add rate limit for general API usage
# Hint: @limiter.limit("20/minute")
@limiter.limit(_____)
def get_data(
    request: Request,
    response: Response,
    creds: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer)],
) -> dict:
    """
    General data endpoint
    Rate limited to 20 requests per minute per client IP
    """
    user = current_user(creds)  # checked inside: requests with invalid tokens also count

    # Track API usage
    api_calls[user] = api_calls.get(user, 0) + 1

    return {
        "message": "Here is your data",
        "user": user,
        "total_api_calls": api_calls[user],
        "data": [
            {"id": 1, "name": "Item 1"},
            {"id": 2, "name": "Item 2"},
            {"id": 3, "name": "Item 3"},
        ],
    }


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
    """
    Expensive search endpoint
    Strictly rate limited to 5 requests per minute
    This simulates a resource-intensive operation (database query, external API call, etc.)
    """
    user = current_user(creds)  # checked inside: requests with invalid tokens also count

    # Simulate expensive search operation
    results = [{"id": i, "title": f'Result {i} for "{q}"'} for i in range(1, 6)]

    return {
        "query": q,
        "results": results,
        "user": user,
        "note": "This endpoint is rate limited to 5 requests per minute",
    }


@app.get("/api/unlimited")
# TODO: Exempt this endpoint from rate limiting by adding the @limiter.exempt decorator above this line
def unlimited(creds: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer)]) -> dict[str, str]:
    """
    Unlimited endpoint - no rate limiting
    Use this pattern for critical endpoints that should never be rate limited
    """
    user = current_user(creds)

    return {
        "message": "This endpoint has no rate limit",
        "user": user,
        "note": "Use exempt endpoints carefully - only for critical operations",
    }


@app.get("/api/stats")
@limiter.limit("10/minute")
def get_stats(
    request: Request,
    response: Response,
    creds: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer)],
) -> dict:
    """Get API usage statistics for current user"""
    user = current_user(creds)  # checked inside: requests with invalid tokens also count

    return {
        "user": user,
        "total_api_calls": api_calls.get(user, 0),
        "registered_users": len(users),
    }


# ==================== Error Handlers ====================

def rate_limit_handler(request: Request, exc: RateLimitExceeded) -> JSONResponse:
    """
    Custom handler for rate limit exceeded errors
    Returns a custom JSON error body, keeping the Retry-After and X-RateLimit-* headers
    """
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
