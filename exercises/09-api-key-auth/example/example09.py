import hashlib
import hmac
import secrets
from typing import Annotated

import bcrypt
from fastapi import Depends, FastAPI, HTTPException
from fastapi.security import APIKeyHeader
from pydantic import BaseModel, Field, field_validator

app = FastAPI(title="API Key Auth")

# APIKeyHeader reads the X-API-Key header and hands its value to our dependency.
# auto_error=False: if the header is missing we get None and answer 401 ourselves
# (by default FastAPI would answer 403).
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)

# Recognisable prefix for our keys ("sk_" = secret key).
# Secret scanners (GitHub, GitLab, gitleaks...) search for known prefixes,
# so a leaked key is easier to detect automatically.
API_KEY_PREFIX = "sk_"

# In-memory database: {username: {"password": bcrypt hash, "api_key_hash": SHA-256 hex or None}}
# We NEVER store the API key itself, only its SHA-256 hash (None once revoked).
users: dict[str, dict[str, str | None]] = {}


def hash_password(pw: str) -> str:
    return bcrypt.hashpw(pw.encode(), bcrypt.gensalt()).decode()


class UserCreate(BaseModel):
    username: str = Field(min_length=1)
    password: str = Field(min_length=8, max_length=72)

    @field_validator("password")
    @classmethod
    def password_fits_bcrypt(cls, pw: str) -> str:
        if len(pw.encode()) > 72:  # bcrypt counts bytes, not characters
            raise ValueError("password must be at most 72 bytes")
        return pw


# ============================================================================
# API KEY HELPERS (generate, hash, look up)
# ============================================================================

def generate_api_key() -> str:
    """Generate a new random API key (about 256 bits of entropy)."""
    return API_KEY_PREFIX + secrets.token_urlsafe(32)


def hash_api_key(key: str) -> str:
    """
    Hash an API key with SHA-256.

    A fast hash is fine here because the key is long and random: there is
    nothing to guess. Passwords are short and human-chosen, so they need a
    slow, salted hash (bcrypt) instead.
    """
    return hashlib.sha256(key.encode()).hexdigest()


def find_user_by_api_key(api_key: str) -> str | None:
    """Return the username that owns this API key, or None."""
    candidate_hash = hash_api_key(api_key)

    for username, user_data in users.items():
        stored_hash = user_data["api_key_hash"]
        # Constant-time comparison: takes the same time whether the first
        # character differs or the last one does
        if stored_hash and hmac.compare_digest(stored_hash, candidate_hash):
            return username

    return None


def get_current_user(api_key: Annotated[str | None, Depends(api_key_header)]) -> str:
    """Dependency: returns the username that owns the key, or answers 401."""
    if api_key is None:
        raise HTTPException(
            status_code=401,
            detail="API key missing: include the X-API-Key header",
            headers={"WWW-Authenticate": "ApiKey"},
        )
    username = find_user_by_api_key(api_key)
    if username is None:
        raise HTTPException(
            status_code=401,
            detail="Invalid API key",
            headers={"WWW-Authenticate": "ApiKey"},
        )
    return username


# ============================================================================
# PUBLIC ENDPOINT (no authentication required)
# ============================================================================

@app.post("/register", status_code=201)
def register(data: UserCreate) -> dict[str, str]:
    """Register a new user and return their API key (ONCE)."""
    if data.username in users:
        raise HTTPException(status_code=409, detail="User already exists")

    api_key = generate_api_key()

    # Store the password hash and the HASH of the API key
    users[data.username] = {
        "password": hash_password(data.password),
        "api_key_hash": hash_api_key(api_key),
    }

    # This is the only time the plain key is shown
    return {
        "message": "User registered successfully. Store this API key now: it will not be shown again.",
        "username": data.username,
        "api_key": api_key,
    }


# ============================================================================
# API KEY PROTECTED ENDPOINTS
# ============================================================================

@app.post("/api-key/rotate")
def rotate_api_key(user: Annotated[str, Depends(get_current_user)]) -> dict[str, str]:
    """
    Issue a new API key and invalidate the old one. The key in the header
    identifies the user, so the request needs no body.

    Use it if the key may have leaked or as routine rotation.
    The server cannot "recover" a key: it only has its hash.
    """
    new_api_key = generate_api_key()

    # Overwriting the stored hash invalidates the old key immediately
    users[user]["api_key_hash"] = hash_api_key(new_api_key)

    return {
        "message": "API key rotated. The previous key no longer works. Store the new key now: it will not be shown again.",
        "api_key": new_api_key,
    }


@app.delete("/api-key")
def revoke_api_key(user: Annotated[str, Depends(get_current_user)]) -> dict[str, str]:
    """Revoke the API key that sent this request, without issuing a new one."""
    users[user]["api_key_hash"] = None
    return {"message": "API key revoked", "username": user}


@app.get("/users")
def get_users(user: Annotated[str, Depends(get_current_user)]) -> dict[str, object]:
    """List all users. Clients must send a valid X-API-Key header."""
    return {"users": list(users), "count": len(users)}
