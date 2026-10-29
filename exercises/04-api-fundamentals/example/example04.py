from http import HTTPStatus

from fastapi import FastAPI, HTTPException, Request, Response
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from starlette.exceptions import HTTPException as StarletteHTTPException

app = FastAPI(title="Notes API")


class NoteCreate(BaseModel):
    title: str = Field(min_length=1)
    content: str = ""


class Note(BaseModel):
    id: int
    title: str
    content: str


# In-memory data store (simplified)
notes: dict[int, Note] = {}
next_id = 1


def problem(request: Request, status: int, title: str, detail: str, **extra) -> JSONResponse:
    """RFC 9457 problem details: one error format for the whole API."""
    body = {"type": "about:blank", "title": title, "status": status, "detail": detail,
            "instance": request.url.path, **extra}
    return JSONResponse(body, status_code=status, media_type="application/problem+json")


# Starlette raises the same HTTPException class for unknown URLs (404) and wrong methods (405),
# so registering the handler for it covers our own errors and the router's.
@app.exception_handler(StarletteHTTPException)
def http_error(request: Request, exc: StarletteHTTPException) -> JSONResponse:
    response = problem(request, exc.status_code, HTTPStatus(exc.status_code).phrase, str(exc.detail))
    response.headers.update(exc.headers or {})  # e.g. Allow on a 405
    return response


@app.exception_handler(RequestValidationError)
def validation_error(request: Request, exc: RequestValidationError) -> JSONResponse:
    return problem(request, 422, "Unprocessable Content", "Request body or parameters are invalid.",
                   errors=jsonable_encoder(exc.errors()))


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/notes")
def list_notes() -> list[Note]:
    return list(notes.values())


@app.post("/notes", status_code=201)
def create_note(data: NoteCreate, request: Request, response: Response) -> Note:
    global next_id
    note = Note(id=next_id, title=data.title, content=data.content)
    notes[note.id] = note
    next_id += 1
    # 201 Created must say WHERE the new note lives
    response.headers["Location"] = str(request.url_for("get_note", note_id=note.id))
    return note


@app.get("/notes/{note_id}")
def get_note(note_id: int) -> Note:
    if note_id not in notes:
        raise HTTPException(status_code=404, detail=f"Note {note_id} does not exist.")
    return notes[note_id]
