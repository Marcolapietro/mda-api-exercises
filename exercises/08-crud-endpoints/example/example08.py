import os
from datetime import datetime, timezone

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


def add_note(title, content=''):
    """Store a new note and return it. The server assigns id and timestamps."""
    global next_id
    timestamp = now_iso()
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


# Seed data, so GET /notes is not empty on the first run
add_note('Welcome', 'This is your Notes API.')
add_note('Shopping list', 'Milk, eggs, coffee')
add_note('API Management', 'Status codes, Location header and RFC 9457 errors')


# ---------------------------------------------------------------------------
# Errors: RFC 9457 "problem details" (Content-Type: application/problem+json)
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
    # 415: the client did not send JSON at all
    if request.mimetype != 'application/json':
        return None, problem(415, 'Unsupported Media Type', 'Content-Type must be application/json.')

    # 400: it says JSON, but the body cannot be parsed
    data = request.get_json(silent=True)
    if data is None:
        return None, problem(400, 'Bad Request', 'The request body is not valid JSON.')

    # 422: valid JSON, but not an object (e.g. [1, 2] or "hello")
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


def parse_limit():
    """Return (limit, None) or (None, error_response). Default 20, values above 100 are clamped."""
    raw = request.args.get('limit', str(DEFAULT_LIMIT))
    try:
        limit = int(raw)
    except ValueError:
        return None, problem(400, 'Bad Request', 'limit must be an integer.')
    if limit < 1:
        return None, problem(400, 'Bad Request', 'limit must be 1 or greater.')
    return min(limit, MAX_LIMIT), None


def note_not_found(note_id):
    return problem(404, 'Not Found', f'Note {note_id} does not exist.')


# ---------------------------------------------------------------------------
# Collection: /notes
# ---------------------------------------------------------------------------

@app.route('/notes', methods=['GET'])
def list_notes():
    """List notes, newest first. ?limit= (default 20, max 100)."""
    limit, error = parse_limit()
    if error:
        return error

    ordered = sorted(notes.values(), key=lambda note: note['id'], reverse=True)
    return jsonify({
        'data': ordered[:limit],
        'page': {'limit': limit, 'total': len(notes)}
    }), 200


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
    # Location tells the client where the new resource lives
    return jsonify(note), 201, {'Location': url_for('get_note', note_id=note['id'], _external=True)}


# ---------------------------------------------------------------------------
# Item: /notes/<id>
# ---------------------------------------------------------------------------

@app.route('/notes/<int:note_id>', methods=['GET'])
def get_note(note_id):
    """Return one note -> 200, or 404 if it does not exist."""
    note = notes.get(note_id)
    if note is None:
        return note_not_found(note_id)
    return jsonify(note), 200


@app.route('/notes/<int:note_id>', methods=['PUT'])
def replace_note(note_id):
    """PUT replaces the WHOLE note: title and content are both required."""
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
    """PATCH changes only the fields that are sent."""
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
    """Delete a note -> 204 No Content (empty body)."""
    if note_id not in notes:
        return note_not_found(note_id)
    del notes[note_id]
    return '', 204


# ---------------------------------------------------------------------------
# Error handlers: the same problem+json shape for errors raised by Flask itself
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
    # Log the details on the server, but don't expose them to the client
    app.logger.error(f'Internal server error: {error}')
    return problem(500, 'Internal Server Error', 'An unexpected error occurred.')


if __name__ == '__main__':
    print("\n" + "=" * 70)
    print("📝 Notes API — CRUD (Solution)")
    print("=" * 70)
    print("Try: GET http://127.0.0.1:5000/notes?limit=10")
    print("Docs: readme07.md (EN) / readme07_es.md (ES)")
    print("=" * 70 + "\n")
    app.run(debug=os.getenv("FLASK_DEBUG") == "1")
