import os
from flask import Flask, request, jsonify, url_for

app = Flask(__name__)
app.json.sort_keys = False  # keep keys in the order we write them (easier to read)

# In-memory data store (simplified)
notes = {}
next_id = 1


def problem(status, title, detail, **extra):
    """Build an error response in RFC 9457 "problem details" format.

    Every error of the API uses this one helper, so clients always get the same shape:
    {"type": "about:blank", "title": "...", "status": 400, "detail": "..."}
    Extra keyword arguments (e.g. errors=[...]) are added as extension members.
    """
    body = {'type': 'about:blank', 'title': title, 'status': status, 'detail': detail}
    body.update(extra)
    response = jsonify(body)
    response.status_code = status
    # TODO: Set the media type for problem details (RFC 9457)
    # Hint: 'application/problem+json'
    response.content_type = '_____'
    return response


@app.route('/health', methods=['_____'])  # TODO: Set the correct HTTP method
# Hint: Use 'GET'
def health():
    """Basic health check endpoint"""
    return jsonify({
        'status': 'ok',
        'service': 'notes-api',
        'version': '1.0'
    }), 200


@app.route('/notes', methods=['_____', '_____'])  # TODO: Provide the methods for list and create (GET, POST)
# Hint: Use 'GET' and 'POST'
def notes_collection():
    """List notes and create a new note (simplified)"""
    # Handle listing
    if request.method == 'GET':
        return jsonify(list(notes.values())), 200

    # Handle creation
    # TODO: Validate Content-Type is JSON; otherwise return 415
    # Hint: request.mimetype is the Content-Type without parameters like '; charset=utf-8'
    if request.mimetype != '_____':
        return problem(415, 'Unsupported Media Type', 'Content-Type must be application/json.')

    # TODO: Parse JSON body
    # Hint: data = request.get_json(silent=True)  -> None if the body is not valid JSON
    data = _____
    if data is None:
        return problem(400, 'Bad Request', 'The request body is not valid JSON.')

    # Valid JSON, but not an object (e.g. [1, 2]): data.get() would crash with a 500
    if not isinstance(data, dict):
        return problem(422, 'Unprocessable Content', 'The request body must be a JSON object.',
                       errors=[{'pointer': '#', 'detail': 'the body must be a JSON object'}])

    # TODO: Validate required fields title and content
    # Hint: title = data.get('title'); content = data.get('content')
    errors = []
    title = _____
    content = _____
    if not isinstance(title, str) or not title.strip():
        errors.append({'pointer': '#/title', 'detail': 'title is required and must be a non-empty string'})
    if not isinstance(content, str) or not content.strip():
        errors.append({'pointer': '#/content', 'detail': 'content is required and must be a non-empty string'})
    if errors:
        # TODO: The JSON is valid but the data is not -> which status code?
        # Hint: 422 Unprocessable Content (400 is for JSON that cannot be parsed)
        return problem(_____, 'Unprocessable Content', 'The note has invalid or missing fields.', errors=errors)

    global next_id
    note_id = next_id
    next_id += 1

    # Build the note object
    note = {
        'id': note_id,
        'title': title.strip(),
        'content': content.strip()
    }
    notes[note_id] = note
    # TODO: 201 Created must say WHERE the new note lives, in the Location header
    # Hint: url_for('note_item', note_id=note_id, _external=True)
    return jsonify(note), 201, {'Location': _____}


@app.route('/notes/<int:note_id>', methods=['_____'])  # TODO: Set the correct HTTP method for retrieval
# Hint: Use 'GET'
def note_item(note_id):
    """Return a single note by id"""
    note = notes.get(note_id)
    if not note:
        return problem(404, 'Not Found', f'Note {note_id} does not exist.')
    return jsonify(note), 200


# Error Handlers (same problem+json shape for errors raised by Flask itself)
@app.errorhandler(404)
def not_found(error):
    return problem(404, 'Not Found', 'The requested URL does not exist.')


@app.errorhandler(405)
def method_not_allowed(error):
    response = problem(405, 'Method Not Allowed', f'{request.method} is not allowed on this URL.')
    response.headers['Allow'] = ', '.join(sorted(error.valid_methods or []))  # which methods ARE allowed
    return response


@app.errorhandler(500)
def internal_error(error):
    app.logger.error(f'Internal server error: {str(error)}')
    return problem(500, 'Internal Server Error', 'An unexpected error occurred.')


if __name__ == '__main__':
    print("\n" + "="*70)
    print("📝 Notes API — Fundamentals (Starter)")
    print("="*70)
    print("Try: GET http://127.0.0.1:5000/health")
    print("Docs: Use readme04.md for steps and curl commands")
    print("="*70 + "\n")
    app.run(debug=os.getenv("FLASK_DEBUG") == "1")
