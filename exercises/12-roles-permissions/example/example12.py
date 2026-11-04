import math
import os
import random
import secrets
import string
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Annotated, Callable

import bcrypt
import jwt
from dotenv import load_dotenv
from fastapi import Depends, FastAPI, HTTPException, Query
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel, Field, field_validator

# Load the .env of the exercise folder, one level up (next to .env.example); a variable set in the terminal wins
load_dotenv(Path(__file__).resolve().parent.parent / ".env")

app = FastAPI(title="Roles and Permissions API")

# JWT configuration for token-based authentication
# The secret never lives in the code: it comes from the environment, or is random for this run
JWT_SECRET = os.environ.get("JWT_SECRET_KEY") or secrets.token_hex(32)  # from env; random per run if unset
JWT_ALG = "HS256"
ACCESS_TOKEN_MINUTES = 15

# HTTPBearer reads "Authorization: Bearer <token>" and hands us the token.
# auto_error=False: if the header is missing we get None and return our own 401 message
# and WWW-Authenticate header (FastAPI's default is a generic "401 Not authenticated").
bearer = HTTPBearer(auto_error=False)

VALID_ROLES = ("admin", "student")

# Simulated database for storing users: {username: {"username", "password" (bcrypt hash), "role"}}
users: dict[str, dict[str, str]] = {}


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
    # No "role" field: the role is never taken from the request body
    # (Pydantic ignores extra fields such as "role").
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


class UserUpdate(BaseModel):
    role: str | None = None
    password: str | None = Field(default=None, min_length=8, max_length=72)

    @field_validator("role")
    @classmethod
    def role_is_valid(cls, role: str | None) -> str | None:
        if role is not None and role not in VALID_ROLES:
            raise ValueError(f"Invalid role. Allowed: {', '.join(VALID_ROLES)}.")
        return role

    @field_validator("password")
    @classmethod
    def password_fits_bcrypt(cls, pw: str | None) -> str | None:
        if pw is not None and len(pw.encode()) > 72:  # bcrypt counts bytes, not characters
            raise ValueError("password must be at most 72 bytes")
        return pw


def create_access_token(user: dict[str, str]) -> str:
    now = datetime.now(timezone.utc)
    claims = {
        "sub": user["username"],
        # The role travels inside the token as a claim (informative: permissions are still
        # checked against the current role in the store on every request)
        "role": user["role"],
        "iat": now,
        "exp": now + timedelta(minutes=ACCESS_TOKEN_MINUTES),
    }
    return jwt.encode(claims, JWT_SECRET, algorithm=JWT_ALG)


def get_current_user(creds: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer)]) -> dict[str, str]:
    """Dependency: returns the stored user record, or answers 401 if the token is missing, expired or invalid."""
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
    user = users.get(claims["sub"])
    if user is None:  # the account was deleted after the token was issued
        raise unauthorized
    return user


def require_role(role: str) -> Callable[..., dict[str, str]]:
    """Builds a dependency that only lets users with the given role through.

    The role is read from the users store on every request, NOT from the token: if an
    admin promotes or demotes someone, the change applies to the token they already have.
    """
    def check_role(user: Annotated[dict[str, str], Depends(get_current_user)]) -> dict[str, str]:
        if user["role"] != role:
            raise HTTPException(status_code=403, detail="Permission denied.")
        return user

    return check_role


# Generate test users
def generate_users(total: int) -> None:
    """Generates test users with random roles"""
    # These users only exist to have data to list (nobody logs in with them).
    # Hashing one random password once keeps start-up fast: hashing 100 passwords
    # one by one takes many seconds.
    unusable_hash = hash_password(secrets.token_hex(16))
    for _ in range(total):
        username = "".join(random.choices(string.ascii_letters, k=8))
        users[username] = {"username": username, "password": unusable_hash, "role": random.choice(VALID_ROLES)}


def create_admin_user() -> None:
    """Bootstraps one admin account so the admin-only endpoints can be tested.

    The password comes from the ADMIN_PASSWORD environment variable; if it is not set,
    a random one is generated and printed once in the console.
    """
    password = os.environ.get("ADMIN_PASSWORD")
    generated = not password
    if generated:
        password = secrets.token_urlsafe(12)
        # `fastapi dev` loads this file twice: keeping the password in the environment makes
        # the second load (the reload worker inherits it) reuse it instead of making a new one.
        os.environ["ADMIN_PASSWORD"] = password
    users["admin"] = {"username": "admin", "password": hash_password(password), "role": "admin"}
    if generated:
        print(f"Admin user created -> username: admin  password: {password}", file=sys.stderr)


# Generate 100 test users with random roles for testing, plus one known admin
generate_users(100)
create_admin_user()


@app.post("/register", status_code=201)
def register_user(data: UserCreate) -> dict[str, str]:
    """Registers a new user. New users are ALWAYS students.

    Security: the role is never taken from the request body. Accepting it would let anyone
    register as admin (a "mass assignment" vulnerability). Only an admin can change roles
    via PUT /users/{username}.
    """
    if data.username in users:
        raise HTTPException(status_code=409, detail="User already exists.")

    users[data.username] = {"username": data.username, "password": hash_password(data.password), "role": "student"}
    return {"message": "User registered successfully.", "role": users[data.username]["role"]}


@app.post("/login")
def login(data: Credentials) -> dict[str, str]:
    """Authenticates a user and generates a JWT token that includes the role as a claim"""
    user = users.get(data.username)
    # Always run the bcrypt check, even for an unknown user, so timing does not reveal who exists
    password_ok = verify_password(data.password, user["password"] if user else DUMMY_HASH)
    if user is None or not password_ok:
        raise HTTPException(
            status_code=401,
            detail="Invalid username or password.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return {"access_token": create_access_token(user), "token_type": "bearer"}


@app.get("/profile")
def profile(user: Annotated[dict[str, str], Depends(get_current_user)]) -> dict[str, str]:
    """Returns the authenticated user's profile"""
    return {"profile": f"Profile information for {user['username']}"}


@app.get("/users")
def get_users(
    admin: Annotated[dict[str, str], Depends(require_role("admin"))],
    page: Annotated[int, Query(ge=1)] = 1,
    per_page: Annotated[int, Query(ge=1, le=100)] = 10,
) -> dict[str, list[str] | int]:
    """Returns a list of users with pagination (admins only). page=0 or per_page=500 answer 422."""
    total_users = len(users)
    total_pages = math.ceil(total_users / per_page)

    if page > total_pages:
        raise HTTPException(status_code=404, detail="Page not found.")

    start = (page - 1) * per_page
    end = start + per_page
    users_list = list(users.keys())[start:end]

    return {"users": users_list, "total_pages": total_pages, "current_page": page}


@app.put("/users/{username}")
def update_user(
    username: str,
    data: UserUpdate,
    admin: Annotated[dict[str, str], Depends(require_role("admin"))],
) -> dict[str, str]:
    """
    Updates an existing user's information (password and/or role).

    Only administrators can update user information.
    Returns:
        200: User updated successfully
        403: Permission denied (not an admin)
        404: User not found
        409: An admin cannot change their own role
        422: Invalid role or password
    """
    # The admin check is a dependency, so it runs BEFORE this body: answering 404
    # to a non-admin would reveal which usernames exist
    if username not in users:
        raise HTTPException(status_code=404, detail="User not found.")

    # An admin cannot demote themselves: that could leave the API without any admin
    if data.role is not None and username == admin["username"]:
        raise HTTPException(status_code=409, detail="You cannot change your own role")

    if data.password is not None:
        users[username]["password"] = hash_password(data.password)
    if data.role is not None:
        users[username]["role"] = data.role

    return {"message": "User updated successfully."}


@app.delete("/users/{username}")
def delete_user(
    username: str,
    admin: Annotated[dict[str, str], Depends(require_role("admin"))],
) -> dict[str, str]:
    """
    Deletes a user if the requester has administrator permissions.

    The require_role("admin") dependency automatically returns 403
    if the user doesn't have the admin role.

    Returns:
        200: User deleted successfully
        403: Permission denied (not an admin)
        404: User not found
        409: An admin cannot delete their own account
    """
    if username not in users:
        raise HTTPException(status_code=404, detail="User not found.")

    # An admin cannot delete themselves: that could leave the API without any admin
    if username == admin["username"]:
        raise HTTPException(status_code=409, detail="You cannot delete your own account")

    users.pop(username)
    return {"message": "User deleted successfully."}


@app.get("/admin/dashboard")
def admin_dashboard(user: Annotated[dict[str, str], Depends(require_role("admin"))]) -> dict[str, str]:
    """
    Returns the dashboard exclusive to administrators.

    Only users with 'admin' role can access this endpoint.
    """
    return {"message": f"Welcome to the admin dashboard, {user['username']}."}


@app.get("/student/data")
def student_data(user: Annotated[dict[str, str], Depends(require_role("student"))]) -> dict[str, str]:
    """
    Returns specific data for the authenticated student.

    Only users with 'student' role can access this endpoint.
    """
    return {"message": f"Student data for {user['username']}."}
