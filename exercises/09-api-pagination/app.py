import os
import base64
from datetime import datetime, timedelta, timezone

from flask import Flask, jsonify, request, url_for

app = Flask(__name__)
app.json.sort_keys = False  # keep keys in the order we write them (easier to read)

DEFAULT_LIMIT = 20  # page size when the client does not send ?limit=
MAX_LIMIT = 100     # upper bound: bigger values are clamped to 100

# In-memory "database": {id: note}. Everything is lost when the app restarts.
notes = {}
next_id = 1


def now_iso():
    """Current time in ISO 8601, UTC (e.g. '2026-10-26T09:30:00Z')."""
    return datetime.now(timezone.utc).isoformat(timespec='seconds').replace('+00:00', 'Z')


def add_note(title, content='', timestamp=None):
    """Store a new note and return it. The server assigns id and timestamps."""
    global next_id
    timestamp = timestamp or now_iso()
    note = {
        'id': next_id,
        'title': title,
        'content': content,
        'created_at': timestamp,
        'updated_at': timestamp
    }
    notes[next_id] = note
    next_id += 1
    return note


def seed_notes(total):
    """Create `total` notes (ids 1..total), one minute apart, so there is data to paginate."""
    start = datetime(2026, 1, 1, tzinfo=timezone.utc)
    for i in range(1, total + 1):
        created = (start + timedelta(minutes=i)).isoformat().replace('+00:00', 'Z')
        add_note(f'Note {i}', f'Seed note number {i}', timestamp=created)


seed_notes(95)


# ---------------------------------------------------------------------------
# Errors: RFC 9457 "problem details" (same helper as exercise 08)
# ---------------------------------------------------------------------------

def problem(status, title, detail, **extra):
    """Build an RFC 9457 error response. Extra keyword arguments become extension members."""
    body = {'type': 'about:blank', 'title': title, 'status': status, 'detail': detail}
    body.update(extra)
    response = jsonify(body)
    response.status_code = status
    response.content_type = 'application/problem+json'
    return response


def validation_problem(errors):
    """422: the JSON is valid, but the data inside it is not."""
    return problem(422, 'Unprocessable Content', 'The note has invalid or missing fields.', errors=errors)


def read_json_object():
    """Return (data, None) if the body is a JSON object, otherwise (None, error_response)."""
    if request.mimetype != 'application/json':
        return None, problem(415, 'Unsupported Media Type', 'Content-Type must be application/json.')
    data = request.get_json(silent=True)
    if data is None:
        return None, problem(400, 'Bad Request', 'The request body is not valid JSON.')
    if not isinstance(data, dict):
        return None, validation_problem([{'pointer': '#', 'detail': 'the body must be a JSON object'}])
    return data, None


def validate_note(data, required):
    """Return a list of field errors (an empty list means the data is valid)."""
    errors = []
    for field in required:
        if field not in data:
            errors.append({'pointer': f'#/{field}', 'detail': f'{field} is required'})
    if 'title' in data and (not isinstance(data['title'], str) or not data['title'].strip()):
        errors.append({'pointer': '#/title', 'detail': 'title must be a non-empty string'})
    if 'content' in data and not isinstance(data['content'], str):
        errors.append({'pointer': '#/content', 'detail': 'content must be a string'})
    return errors


def note_not_found(note_id):
    return problem(404, 'Not Found', f'Note {note_id} does not exist.')


# ---------------------------------------------------------------------------
# Pagination helpers
# ---------------------------------------------------------------------------

def parse_limit():
    """Return (limit, None) or (None, error_response). Default 20, values above 100 are clamped."""
    raw = request.args.get('limit', str(DEFAULT_LIMIT))
    try:
        limit = int(raw)
    except ValueError:
        return None, problem(400, 'Bad Request', 'limit must be an integer.')
    if limit < 1:
        return None, problem(400, 'Bad Request', 'limit must be 1 or greater.')
    # TODO: Never return more than the maximum page size (?limit=500 -> 100)
    # Hint: min(limit, MAX_LIMIT)
    return _____, None


def parse_offset():
    """Return (offset, None) or (None, error_response). Offset must be an integer >= 0."""
    try:
        offset = int(request.args['offset'])
    except ValueError:
        return None, problem(400, 'Bad Request', 'offset must be an integer.')
    if offset < 0:
        return None, problem(400, 'Bad Request', 'offset must be 0 or greater.')
    return offset, None


def encode_cursor(note_id):
    """Opaque cursor: base64 (URL-safe, without '=' padding) of the last id the client has seen."""
    return base64.urlsafe_b64encode(str(note_id).encode()).decode().rstrip('=')


def decode_cursor(cursor):
    """Return the id inside the cursor, or None if the cursor is not one of ours."""
    try:
        padded = cursor + '=' * (-len(cursor) % 4)
        raw = base64.urlsafe_b64decode(padded).decode('ascii')
    except ValueError:  # bad base64 or non-ASCII content
        return None
    if not raw.isdigit():
        return None
    return int(raw)


def page_url(**params):
    """Absolute URL to /notes with the given query parameters."""
    return url_for('list_notes', _external=True, **params)


def paged_response(data, page):
    """Body {"data": [...], "page": {...}} plus an RFC 8288 Link header."""
    response = jsonify({'data': data, 'page': page})
    links = []
    # TODO: Set the link relation types (RFC 8288)
    # Hint: 'next' and 'prev'
    if page['next']:
        links.append(f'<{page["next"]}>; rel="_____"')
    if page['prev']:
        links.append(f'<{page["prev"]}>; rel="_____"')
    if links:
        response.headers['Link'] = ', '.join(links)
    return response


def offset_page(ordered, limit):
    """?offset=N&limit=M: skip N notes, return the next M. Simple, but shifts when data changes."""
    offset, error = parse_offset()
    if error:
        return error

    total = len(ordered)
    # TODO: Skip `offset` notes and take the next `limit` ones (list slicing)
    # Hint: ordered[offset:offset + limit]
    data = ordered[_____:_____]
    # TODO: Where does the next page start?
    # Hint: offset + limit
    next_url = page_url(offset=_____, limit=limit) if offset + limit < total else None
    prev_url = page_url(offset=max(offset - limit, 0), limit=limit) if offset > 0 else None
    return paged_response(data, {
        'mode': 'offset',
        'offset': offset,
        'limit': limit,
        'total': total,
        'next': next_url,
        'prev': prev_url
    })


def cursor_page(ordered, limit):
    """?cursor=X&limit=M: return the M notes that come right after the note inside the cursor."""
    cursor = request.args.get('cursor')
    if cursor is None:
        remaining = ordered  # no cursor: first page
    else:
        after_id = decode_cursor(cursor)
        if after_id is None:
            # TODO: The client sent a cursor we did not create. Which status code?
            # Hint: 400 Bad Request
            return problem(_____, 'Bad Request', 'The cursor is not valid. Use the next_cursor value from a previous response.')
        # TODO: Newest first: the notes that come "after" a note are the ones with a SMALLER id
        # Hint: note['id'] < after_id
        remaining = [note for note in ordered if _____]

    data = remaining[:limit]
    # TODO: If there are more notes, the next cursor points to the LAST note of this page
    # Hint: data[-1]['id']
    next_cursor = encode_cursor(_____) if len(remaining) > limit else None
    next_url = page_url(cursor=next_cursor, limit=limit) if next_cursor else None
    return paged_response(data, {
        'mode': 'cursor',
        'limit': limit,
        'next_cursor': next_cursor,
        'next': next_url,
        'prev': None  # forward-only: to go back, the client reuses a cursor it already has
    })


# ---------------------------------------------------------------------------
# Collection: /notes
# ---------------------------------------------------------------------------

@app.route('/notes', methods=['GET'])
def list_notes():
    """List notes, newest first. Offset mode (?offset=&limit=) or cursor mode (?cursor=&limit=)."""
    # TODO: offset and cursor are two different strategies: reject requests that mix them
    # Hint: 400 Bad Request
    if 'offset' in request.args and 'cursor' in request.args:
        return problem(_____, 'Bad Request', 'Use either offset or cursor, not both.')

    limit, error = parse_limit()
    if error:
        return error

    ordered = sorted(notes.values(), key=lambda note: note['id'], reverse=True)
    if 'offset' in request.args:
        return offset_page(ordered, limit)
    return cursor_page(ordered, limit)


@app.route('/notes', methods=['POST'])
def create_note():
    """Create a note -> 201 Created + Location header."""
    data, error = read_json_object()
    if error:
        return error

    errors = validate_note(data, required=('title',))
    if errors:
        return validation_problem(errors)

    note = add_note(data['title'].strip(), data.get('content', ''))
    return jsonify(note), 201, {'Location': url_for('get_note', note_id=note['id'], _external=True)}


# ---------------------------------------------------------------------------
# Item: /notes/<id> (same as exercise 08)
# ---------------------------------------------------------------------------

@app.route('/notes/<int:note_id>', methods=['GET'])
def get_note(note_id):
    note = notes.get(note_id)
    if note is None:
        return note_not_found(note_id)
    return jsonify(note), 200


@app.route('/notes/<int:note_id>', methods=['PUT'])
def replace_note(note_id):
    note = notes.get(note_id)
    if note is None:
        return note_not_found(note_id)

    data, error = read_json_object()
    if error:
        return error

    errors = validate_note(data, required=('title', 'content'))
    if errors:
        return validation_problem(errors)

    note['title'] = data['title'].strip()
    note['content'] = data['content']
    note['updated_at'] = now_iso()
    return jsonify(note), 200


@app.route('/notes/<int:note_id>', methods=['PATCH'])
def update_note(note_id):
    note = notes.get(note_id)
    if note is None:
        return note_not_found(note_id)

    data, error = read_json_object()
    if error:
        return error

    errors = validate_note(data, required=())
    if not errors and 'title' not in data and 'content' not in data:
        errors.append({'pointer': '#', 'detail': 'send at least one of: title, content'})
    if errors:
        return validation_problem(errors)

    if 'title' in data:
        note['title'] = data['title'].strip()
    if 'content' in data:
        note['content'] = data['content']
    note['updated_at'] = now_iso()
    return jsonify(note), 200


@app.route('/notes/<int:note_id>', methods=['DELETE'])
def delete_note(note_id):
    if note_id not in notes:
        return note_not_found(note_id)
    del notes[note_id]
    return '', 204


# ---------------------------------------------------------------------------
# Error handlers
# ---------------------------------------------------------------------------

@app.errorhandler(404)
def not_found(error):
    return problem(404, 'Not Found', 'The requested URL does not exist.')


@app.errorhandler(405)
def method_not_allowed(error):
    response = problem(405, 'Method Not Allowed', f'{request.method} is not allowed on this URL.')
    response.headers['Allow'] = ', '.join(sorted(error.valid_methods or []))
    return response


@app.errorhandler(500)
def internal_error(error):
    app.logger.error(f'Internal server error: {error}')
    return problem(500, 'Internal Server Error', 'An unexpected error occurred.')


if __name__ == '__main__':
    print("\n" + "=" * 70)
    print("📝 Notes API — Pagination (Starter)")
    print("=" * 70)
    print("Offset: GET http://127.0.0.1:5000/notes?offset=0&limit=5")
    print("Cursor: GET http://127.0.0.1:5000/notes?limit=5")
    print("Docs: readme08.md (EN) / readme08_es.md (ES)")
    print("=" * 70 + "\n")
    app.run(debug=os.getenv("FLASK_DEBUG") == "1")
