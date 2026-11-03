"""
Exercise 15: API Versioning - COMPLETE SOLUTION
Learn to manage API versions and breaking changes
"""

import os
import secrets
from datetime import datetime, timedelta, timezone
from email.utils import format_datetime
from typing import Annotated

import bcrypt
import jwt
from fastapi import APIRouter, Depends, FastAPI, HTTPException, Query, Response
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel, Field, field_validator

app = FastAPI(title="Notes API with versioning")

# JWT Configuration
JWT_SECRET = os.environ.get("JWT_SECRET_KEY") or secrets.token_hex(32)  # from env; random per run if unset
JWT_ALG = "HS256"
ACCESS_TOKEN_HOURS = 1

# HTTPBearer reads "Authorization: Bearer <token>". auto_error=False lets us return our own
# 401 message and WWW-Authenticate header (FastAPI's default is a generic 401 Not authenticated).
bearer = HTTPBearer(auto_error=False)

# In-memory data storage
users: dict[str, str] = {}  # {username: bcrypt hash}
notes: dict[int, dict] = {}
note_id_counter = 1

# API version information
API_VERSIONS = {
    'v1': {
        'status': 'deprecated',
        'deprecation_date': '2026-01-01',  # when v1 was marked as deprecated
        'sunset_date': '2027-06-30',       # after this date v1 will be retired (410 Gone)
        'successor': '/api/v2',
        'deprecation_notice': 'API v1 is deprecated. Please migrate to v2.'
    },
    'v2': {
        'status': 'current',
        'deprecation_date': None,
        'sunset_date': None,
        'successor': None,
        'deprecation_notice': None
    }
}


def to_epoch(iso_date: str) -> int:
    """'2026-01-01' -> 1767225600 (seconds since 1970, UTC)"""
    return int(datetime.fromisoformat(iso_date).replace(tzinfo=timezone.utc).timestamp())


def to_http_date(iso_date: str) -> str:
    """'2027-06-30' -> 'Wed, 30 Jun 2027 00:00:00 GMT' (the date format HTTP headers use)"""
    return format_datetime(datetime.fromisoformat(iso_date).replace(tzinfo=timezone.utc), usegmt=True)


# ==================== Models ====================

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


class NoteCreate(BaseModel):
    """v1 body: {title, content}"""
    title: str
    content: str = ""


class NoteCreateV2(NoteCreate):
    """v2 body: the v1 fields plus optional tags"""
    tags: list[str] = []


class NoteUpdate(BaseModel):
    """v2 PATCH body: send only the fields you want to change"""
    title: str | None = None
    content: str | None = None
    tags: list[str] | None = None


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


def create_access_token(username: str) -> str:
    now = datetime.now(timezone.utc)
    claims = {"sub": username, "iat": now, "exp": now + timedelta(hours=ACCESS_TOKEN_HOURS)}
    return jwt.encode(claims, JWT_SECRET, algorithm=JWT_ALG)


def get_current_user(creds: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer)]) -> str:
    """Dependency: returns the username from the Bearer token, or answers 401."""
    if creds is None:
        raise HTTPException(status_code=401, detail="Missing or invalid token", headers={"WWW-Authenticate": "Bearer"})
    try:
        claims = jwt.decode(creds.credentials, JWT_SECRET, algorithms=[JWT_ALG], options={"require": ["sub", "exp"]})
    except jwt.InvalidTokenError:  # expired, bad signature, malformed...
        raise HTTPException(status_code=401, detail="Invalid token", headers={"WWW-Authenticate": "Bearer"})
    return claims["sub"]


def get_own_note(note_id: int, user: str) -> dict:
    """Return the note, or answer 404 (does not exist) / 403 (belongs to someone else)."""
    if note_id not in notes:
        raise HTTPException(status_code=404, detail="Note not found")
    if notes[note_id]["owner"] != user:
        raise HTTPException(status_code=403, detail="You do not own this note")
    return notes[note_id]


def to_v2(note: dict) -> dict:
    """
    The v2 shape of any note. Notes created with v1 have no tags or timestamps, so v2 fills in
    the defaults (empty tags, null timestamps: we never knew when they were created) and every
    v2 note has the same fields. v1 responses are left as they are.
    """
    return {
        'id': note['id'],
        'title': note['title'],
        'content': note['content'],
        'tags': note.get('tags', []),
        'owner': note['owner'],
        'created_at': note.get('created_at'),
        'updated_at': note.get('updated_at'),
    }


def add_deprecation_headers(response: Response) -> None:
    """
    Router dependency: runs on every v1 request.
    Tells clients which version they are using and that it is deprecated.
    """
    info = API_VERSIONS['v1']
    response.headers['API-Version'] = 'v1'
    response.headers['Deprecation'] = f"@{to_epoch(info['deprecation_date'])}"  # RFC 9745
    response.headers['Sunset'] = to_http_date(info['sunset_date'])  # RFC 8594
    response.headers['Link'] = f'<{info["successor"]}>; rel="successor-version"'


def add_v2_header(response: Response) -> None:
    """Router dependency: runs on every v2 request. v2 is current, so no deprecation headers."""
    response.headers['API-Version'] = 'v2'


# One router per version. The prefix is added to every route of the router, and the
# dependencies run for every route of the router (here: authentication + version headers).
v1 = APIRouter(
    prefix="/api/v1",
    tags=["v1 (deprecated)"],
    dependencies=[Depends(get_current_user), Depends(add_deprecation_headers)],
)
v2 = APIRouter(
    prefix="/api/v2",
    tags=["v2"],
    dependencies=[Depends(get_current_user), Depends(add_v2_header)],
)


# ==================== Authentication Routes (Version-agnostic) ====================

@app.post("/auth/register", status_code=201, tags=["auth"])
def register(data: UserCreate) -> dict[str, str]:
    """Register a new user - no versioning needed for auth"""
    if data.username in users:
        raise HTTPException(status_code=409, detail="User already exists")

    users[data.username] = hash_password(data.password)

    return {"message": f"User {data.username} registered successfully"}


@app.post("/auth/login", tags=["auth"])
def login(data: Credentials) -> dict[str, str]:
    """Login - no versioning needed for auth"""
    # Always run the bcrypt check, even for an unknown user, so timing does not reveal who exists
    password_ok = verify_password(data.password, users.get(data.username, DUMMY_HASH))
    if data.username not in users or not password_ok:
        raise HTTPException(status_code=401, detail="Invalid credentials", headers={"WWW-Authenticate": "Bearer"})

    return {
        "access_token": create_access_token(data.username),
        "token_type": "bearer",
        "username": data.username,
    }


# ==================== API Version 1 (Deprecated) ====================

@v1.get("/notes")
def get_notes_v1(user: Annotated[str, Depends(get_current_user)]) -> list[dict]:
    """
    Version 1: Get all notes
    Returns a simple list of notes
    """
    return [note for note in notes.values() if note['owner'] == user]


@v1.post("/notes", status_code=201)
def create_note_v1(data: NoteCreate, user: Annotated[str, Depends(get_current_user)]) -> dict:
    """
    Version 1: Create a new note
    Simple structure: {title, content}
    """
    global note_id_counter

    note = {
        'id': note_id_counter,
        'title': data.title,
        'content': data.content,
        'owner': user
    }

    notes[note_id_counter] = note
    note_id_counter += 1

    return note


@v1.get("/notes/{note_id}")
def get_note_v1(note_id: int, user: Annotated[str, Depends(get_current_user)]) -> dict:
    """
    Version 1: Get a specific note by ID
    """
    return get_own_note(note_id, user)


# ==================== API Version 2 (Current) ====================

@v2.get("/notes")
def get_notes_v2(
    user: Annotated[str, Depends(get_current_user)],
    page: Annotated[int, Query(ge=1)] = 1,
    per_page: Annotated[int, Query(ge=1, le=100)] = 10,
) -> dict:
    """
    Version 2: Get all notes with enhanced response structure

    BREAKING CHANGES from v1:
    - Response is now an object with 'data', 'count', and 'version' fields
    - Only the first page is returned (10 notes by default) unless page/per_page are sent

    Also new (non-breaking):
    - Each note includes 'created_at' timestamp
    - Pagination query params: page, per_page
    """
    # Filter notes by owner (in the v2 shape)
    user_notes = [to_v2(note) for note in notes.values() if note['owner'] == user]

    # Calculate pagination
    start = (page - 1) * per_page
    end = start + per_page
    paginated_notes = user_notes[start:end]

    return {
        'data': paginated_notes,
        'count': len(user_notes),
        'page': page,
        'per_page': per_page,
        'version': 'v2'
    }


@v2.post("/notes", status_code=201)
def create_note_v2(data: NoteCreateV2, user: Annotated[str, Depends(get_current_user)]) -> dict:
    """
    Version 2: Create a new note with enhanced fields

    BREAKING CHANGES from v1:
    - Response wrapped in 'data' object

    Also new (non-breaking):
    - Adds 'created_at' and 'updated_at' timestamps
    - Adds 'tags' field (optional array)
    """
    global note_id_counter

    now = datetime.now(timezone.utc).isoformat()  # computed once, so both timestamps are identical
    note = {
        'id': note_id_counter,
        'title': data.title,
        'content': data.content,
        'tags': data.tags,  # New field in v2
        'owner': user,
        'created_at': now,
        'updated_at': now
    }

    notes[note_id_counter] = note
    note_id_counter += 1

    return {'data': note, 'message': 'Note created successfully'}


@v2.get("/notes/{note_id}")
def get_note_v2(note_id: int, user: Annotated[str, Depends(get_current_user)]) -> dict:
    """
    Version 2: Get a specific note with enhanced structure

    BREAKING CHANGES from v1:
    - Response wrapped in 'data' object

    Also new (non-breaking):
    - Includes tags and timestamps (empty tags and null timestamps for notes created with v1)
    """
    return {'data': to_v2(get_own_note(note_id, user))}


@v2.patch("/notes/{note_id}")
def update_note_v2(note_id: int, data: NoteUpdate, user: Annotated[str, Depends(get_current_user)]) -> dict:
    """
    Version 2: Update some fields of a note (PATCH: partial update; new endpoint, not in v1)
    """
    note = get_own_note(note_id, user)

    # Update fields
    if data.title is not None:
        note['title'] = data.title
    if data.content is not None:
        note['content'] = data.content
    if data.tags is not None:
        note['tags'] = data.tags

    # Update timestamp
    note['updated_at'] = datetime.now(timezone.utc).isoformat()

    return {'data': to_v2(note), 'message': 'Note updated successfully'}


# Plug both routers into the app. Do it AFTER the routes above are declared:
# include_router copies the routes the router has at that moment.
app.include_router(v1)
app.include_router(v2)


# ==================== Version Info Endpoint ====================

@app.get("/api/versions")
def get_versions() -> dict:
    """
    Get information about all API versions
    """
    return {
        'versions': API_VERSIONS,
        'current': 'v2',
        'deprecated': ['v1']
    }


# ==================== Root and Health ====================

@app.get("/")
def root() -> dict:
    """API root with version information"""
    return {
        'message': 'Notes API with versioning',
        'current_version': 'v2',
        'available_versions': list(API_VERSIONS.keys()),
        'endpoints': {
            'auth': '/auth/register, /auth/login',
            'v1': '/api/v1/notes',
            'v2': '/api/v2/notes',
            'version_info': '/api/versions'
        }
    }


@app.get("/health")
def health() -> dict[str, str]:
    """Health check endpoint"""
    return {'status': 'ok'}
