import os
from flask import Flask, request, jsonify, url_for

app = Flask(__name__)
app.json.sort_keys = False  # keep keys in the order we write them (easier to read)

notes = {}
next_id = 1


def problem(status, title, detail, **extra):
    """RFC 9457 problem details: one error format for the whole API."""
    body = {'type': 'about:blank', 'title': title, 'status': status, 'detail': detail}
    body.update(extra)
    response = jsonify(body)
    response.status_code = status
    response.content_type = 'application/problem+json'
    return response


@app.route('/health', methods=['GET'])
def health():
    return jsonify({'status': 'ok', 'service': 'notes-api', 'version': '1.0'}), 200


@app.route('/notes', methods=['GET', 'POST'])
def notes_collection():
    if request.method == 'GET':
        return jsonify(list(notes.values())), 200

    if request.mimetype != 'application/json':  # also accepts 'application/json; charset=utf-8'
        return problem(415, 'Unsupported Media Type', 'Content-Type must be application/json.')

    data = request.get_json(silent=True)
    if data is None:
        return problem(400, 'Bad Request', 'The request body is not valid JSON.')

    # Valid JSON, but not an object (e.g. [1, 2]) -> 422, not a 500
    if not isinstance(data, dict):
        return problem(422, 'Unprocessable Content', 'The request body must be a JSON object.',
                       errors=[{'pointer': '#', 'detail': 'the body must be a JSON object'}])

    errors = []
    title = data.get('title')
    content = data.get('content')
    if not isinstance(title, str) or not title.strip():
        errors.append({'pointer': '#/title', 'detail': 'title is required and must be a non-empty string'})
    if not isinstance(content, str) or not content.strip():
        errors.append({'pointer': '#/content', 'detail': 'content is required and must be a non-empty string'})
    if errors:
        return problem(422, 'Unprocessable Content', 'The note has invalid or missing fields.', errors=errors)

    global next_id
    note_id = next_id
    next_id += 1

    note = {
        'id': note_id,
        'title': title.strip(),
        'content': content.strip()
    }
    notes[note_id] = note
    return jsonify(note), 201, {'Location': url_for('note_item', note_id=note_id, _external=True)}


@app.route('/notes/<int:note_id>', methods=['GET'])
def note_item(note_id):
    note = notes.get(note_id)
    if not note:
        return problem(404, 'Not Found', f'Note {note_id} does not exist.')
    return jsonify(note), 200


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
    app.logger.error(f'Internal server error: {str(error)}')
    return problem(500, 'Internal Server Error', 'An unexpected error occurred.')


if __name__ == '__main__':
    print("\n" + "="*70)
    print("📝 Notes API — Fundamentals (Solution)")
    print("="*70)
    print("Try: GET http://127.0.0.1:5000/health")
    print("="*70 + "\n")
    app.run(debug=os.getenv("FLASK_DEBUG") == "1")
