import secrets
from typing import Annotated

import bcrypt
from fastapi import Depends, FastAPI, HTTPException
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from pydantic import BaseModel, Field, field_validator

app = FastAPI(title="Users API")

# HTTPBasic reads the Authorization header and decodes username and password.
# If the header is missing it already answers 401 with WWW-Authenticate.
security = HTTPBasic(realm="Authentication Required")

# In-memory database: {username: bcrypt hash}
users: dict[str, str] = {}


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


def get_current_user(creds: Annotated[HTTPBasicCredentials, Depends(security)]) -> str:
    """Dependency: returns the username, or answers 401 if the credentials are wrong."""
    username = next((u for u in users if secrets.compare_digest(u.encode(), creds.username.encode())), None)
    # Always run the bcrypt check, even for an unknown user, so timing does not reveal who exists
    password_ok = verify_password(creds.password, users.get(username, DUMMY_HASH))
    if username is None or not password_ok:
        raise HTTPException(
            status_code=401,
            detail="Invalid credentials",
            headers={"WWW-Authenticate": 'Basic realm="Authentication Required"'},
        )
    return username


@app.post("/users", status_code=201)
def register_user(data: UserCreate) -> dict[str, str]:
    if data.username in users:
        raise HTTPException(status_code=409, detail="User already exists")
    users[data.username] = hash_password(data.password)
    return {"message": "User registered successfully", "username": data.username}


@app.get("/users")
def get_users(user: Annotated[str, Depends(get_current_user)]) -> list[str]:
    return list(users)
