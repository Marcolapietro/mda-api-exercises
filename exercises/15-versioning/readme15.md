# Exercise 15: API Versioning

## Quick Start

```bash
cd exercises/15-versioning
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
python app.py
```

## Objective

Learn to manage API versions and handle breaking changes professionally:

- **Version Management**: Understand when and how to create new API versions
- **Breaking vs Non-Breaking Changes**: Identify changes that require new versions
- **URL Path Versioning**: Implement version-specific endpoints (`/api/v1`, `/api/v2`)
- **Deprecation Strategies**: Gracefully sunset old versions with proper warnings
- **Client Migration**: Help clients transition between versions
- **Version Headers**: Communicate version information through HTTP headers

## What is API Versioning?

**API versioning** is the practice of managing multiple versions of your API simultaneously to allow for evolution without breaking existing clients.

**Why API versioning matters:**
- **Backward compatibility**: Old clients continue working while you improve the API
- **Gradual migration**: Clients can upgrade on their schedule
- **Clear communication**: Deprecation warnings give clients time to adapt
- **Innovation freedom**: You can improve the API without fear of breaking clients

**Real-world examples:**
- **Twitter API**: v1.1 → v2 (major redesign, ~2 year migration period)
- **Stripe API**: Uses dated versions (2023-10-16, 2024-06-20)
- **GitHub API**: v3 → v4 (REST → GraphQL)
- **Google Maps API**: v3 (stable), with deprecation warnings for old features

## Prerequisites

Before starting this exercise, complete:
- **Exercise 11**: JWT Authentication (this exercise uses JWT)
- **Exercise 05**: CRUD Endpoints (understanding REST operations)
- **Exercise 06**: API Pagination (v2 includes pagination)

## Breaking vs Non-Breaking Changes

### Non-Breaking Changes (No new version needed)

**Adding optional fields:**
```json
// Old response
{"id": 1, "name": "Alice"}

// New response (backward compatible)
{"id": 1, "name": "Alice", "email": "alice@example.com"}
```
✅ Old clients ignore the new field - no problem!

**Adding new endpoints:**
- `POST /api/v1/notes` (existing)
- `DELETE /api/v1/notes/<id>` (new)

✅ Old clients don't use the new endpoint - no problem!

**Adding optional request parameters:**
```bash
# Old request (still works)
GET /api/v1/notes

# New request with optional filter
GET /api/v1/notes?tag=work
```
✅ Old clients work without the parameter - no problem!

### Breaking Changes (New version required)

**Removing fields:**
```json
// v1 response
{"id": 1, "name": "Alice", "email": "alice@example.com"}

// v2 response (BREAKING - email removed)
{"id": 1, "name": "Alice"}
```
❌ Old clients expecting `email` will break!

**Renaming fields:**
```json
// v1
{"user_id": 1, "user_name": "Alice"}

// v2 (BREAKING - field names changed)
{"id": 1, "name": "Alice"}
```
❌ Old clients looking for `user_id` will break!

**Changing response structure:**
```json
// v1 (array)
[{"id": 1}, {"id": 2}]

// v2 (BREAKING - now an object)
{"data": [{"id": 1}, {"id": 2}], "count": 2}
```
❌ Old clients expecting an array will break!

**Changing data types:**
```json
// v1
{"id": "1", "price": "19.99"}

// v2 (BREAKING - strings → numbers)
{"id": 1, "price": 19.99}
```
❌ Old clients expecting strings will break!

**Making optional fields required:**
```bash
# v1 (email optional)
POST /api/v1/users {"name": "Alice"}

# v2 (BREAKING - email now required)
POST /api/v2/users {"name": "Alice", "email": "alice@example.com"}
```
❌ Old clients not sending email will get errors!

## Versioning Strategies

### 1. URL Path Versioning (This Exercise)

**Format:** `/api/v1/resource` vs `/api/v2/resource`

**Pros:**
- ✅ Very explicit and visible
- ✅ Easy to test (just change the URL)
- ✅ Works with all HTTP clients
- ✅ Can cache different versions separately
- ✅ Simple to understand

**Cons:**
- ❌ Can lead to code duplication
- ❌ URLs change when version changes

**Example:**
```python
@app.route('/api/v1/notes', methods=['GET'])
def get_notes_v1():
    return jsonify([...])  # Simple array

@app.route('/api/v2/notes', methods=['GET'])
def get_notes_v2():
    return jsonify({'data': [...], 'count': 10})  # Wrapped object
```

**Used by:** Stripe, Twilio, Twitter, Shopify

### 2. Header-Based Versioning

**Format:** `Accept: application/vnd.api.v2+json`

**Pros:**
- ✅ URLs stay the same
- ✅ Follows REST principles (resource identification)
- ✅ Flexible (can version per resource)

**Cons:**
- ❌ Less visible (hidden in headers)
- ❌ Harder to test (need to set headers)
- ❌ Caching more complex

**Example:**
```python
@app.route('/api/notes')
def get_notes():
    version = request.headers.get('API-Version', 'v1')
    if version == 'v2':
        return jsonify({'data': [...]})
    return jsonify([...])
```

**Used by:** GitHub API, Azure API

### 3. Query Parameter Versioning

**Format:** `/api/notes?version=2`

**Pros:**
- ✅ Easy to test
- ✅ Works with all clients

**Cons:**
- ❌ Not RESTful (versioning isn't a resource property)
- ❌ Can be forgotten/omitted
- ❌ Clutters query parameters

**Example:**
```bash
GET /api/notes?version=2&page=1&per_page=10
```

**Used by:** Some internal APIs, rarely in public APIs

### 4. Content Negotiation

**Format:** `Accept: application/json; version=2`

**Pros:**
- ✅ Standard HTTP mechanism
- ✅ Flexible

**Cons:**
- ❌ Complex to implement
- ❌ Not intuitive

**Used by:** Some enterprise APIs

## This Exercise: URL Path Versioning

We use **URL path versioning** because it's:
- The most common in real-world APIs
- Easiest to learn and understand
- Most explicit and testable
- Industry standard

## Exercise Structure

This exercise provides:
- `app.py` - Starter file with TODOs for students
- `example/example15.py` - Complete reference solution
- `requirements.txt` - Dependencies
- `readme15.md` - This instruction file

## Part 1: Understanding the Scenario (10 minutes)

### The Evolution Story

**Version 1 (Original):**
You built a simple notes API that returns notes as a plain array:
```json
[
  {"id": 1, "title": "Note 1", "content": "...", "owner": "alice"},
  {"id": 2, "title": "Note 2", "content": "...", "owner": "alice"}
]
```

**Problem:** Clients have been using this for months. You can't just change it!

**Version 2 (Improved):**
You want to add:
- Pagination support
- Metadata (total count, page info)
- Timestamps (created_at, updated_at)
- Tags field
- Wrapped responses for consistency

**New response structure:**
```json
{
  "data": [
    {
      "id": 1,
      "title": "Note 1",
      "content": "...",
      "tags": ["work", "important"],
      "owner": "alice",
      "created_at": "2024-01-01T10:00:00Z",
      "updated_at": "2024-01-01T10:00:00Z"
    }
  ],
  "count": 1,
  "page": 1,
  "per_page": 10
}
```

**Solution:** Keep v1 running while launching v2, then deprecate v1 with warnings.

### Version Headers

We'll use HTTP headers to communicate version information:

**`API-Version` header:**
Tells clients which version they're using
```
API-Version: v2
```

**`Deprecation` header (RFC 9745):**
Tells clients the version is deprecated and since when: `@` followed by a Unix timestamp (here, 1 January 2026)
```
Deprecation: @1767225600
```

**`Sunset` header (RFC 8594):**
Tells clients when the version will stop working, as an HTTP date
```
Sunset: Wed, 30 Jun 2027 00:00:00 GMT
```

**`Link` header with `rel="successor-version"`:**
Points clients to the version that replaces this one
```
Link: </api/v2>; rel="successor-version"
```

> The old `Warning` header (`Warning: 299 - "..."`) is obsolete since RFC 9111 (2022): don't use it in new APIs.

## Part 2: Implementing Version Headers (15 minutes)

### Task 2.1: Complete the `add_version_headers` Function

Open `app.py` and find the `add_version_headers` function:

```python
def add_version_headers(response, version):
    """Add version-related headers to response"""

    # TODO: Add API-Version header with the current version
    # Hint: response.headers['API-Version'] = version
    response.headers['API-Version'] = _____

    if API_VERSIONS[version]['status'] == 'deprecated':
        # TODO: Add Deprecation header (RFC 9745): "@" + when it was deprecated, as a Unix timestamp
        response.headers['Deprecation'] = _____

        # TODO: Add Sunset header (RFC 8594): when the version will stop working, as an HTTP date
        response.headers['Sunset'] = _____

        # TODO: Add Link header pointing clients to the version that replaces this one
        response.headers['Link'] = _____

    return response
```

The helpers `to_epoch()` and `to_http_date()` (defined right after `API_VERSIONS`) convert the dates stored as `'2026-01-01'` into the formats the headers need.

**Your tasks:**
1. Fill in `API-Version` header with the version parameter
2. Add `Deprecation` header: `@` followed by `to_epoch(...)` of the deprecation date
3. Add `Sunset` header: `to_http_date(...)` of the sunset date from `API_VERSIONS`
4. Add `Link` header pointing to the successor version

**Solution:**
```python
response.headers['API-Version'] = version
response.headers['Deprecation'] = f"@{to_epoch(API_VERSIONS[version]['deprecation_date'])}"
response.headers['Sunset'] = to_http_date(API_VERSIONS[version]['sunset_date'])
response.headers['Link'] = f'<{API_VERSIONS[version]["successor"]}>; rel="successor-version"'
```

## Part 3: Implementing Version 1 (20 minutes)

Version 1 is the original, simple API that many clients are already using.

### Task 3.1: Complete `get_notes_v1`

```python
@app.route('/api/v1/notes', methods=['GET'])
@jwt_required()
def get_notes_v1():
    """Version 1: Get all notes - Returns a simple list"""
    current_user = get_jwt_identity()
    user_notes = [note for note in notes.values() if note['owner'] == current_user]

    # TODO: Create response with jsonify and user_notes
    response = make_response(jsonify(_____))

    # TODO: Add version headers to response
    response = add_version_headers(response, _____)

    return response
```

**Your tasks:**
1. Create response with the `user_notes` list
2. Add version headers for 'v1'

**Why make_response?**
We use `make_response()` instead of just `jsonify()` because we need to modify the response headers before returning it.

## Part 4: Implementing Version 2 (30 minutes)

Version 2 introduces breaking changes with improved functionality.

### Task 4.1: Complete `get_notes_v2` with Pagination

```python
@app.route('/api/v2/notes', methods=['GET'])
@jwt_required()
def get_notes_v2():
    """Version 2: Get all notes with pagination"""
    current_user = get_jwt_identity()
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)

    user_notes = [note for note in notes.values() if note['owner'] == current_user]

    # TODO: Calculate pagination
    start = _____
    end = start + per_page
    paginated_notes = user_notes[start:end]

    # TODO: Create v2 response structure
    response_data = {
        'data': _____,
        'count': _____,
        'page': _____,
        'per_page': _____
    }

    response = make_response(jsonify(response_data))
    response = add_version_headers(response, 'v2')

    return response
```

**Your tasks:**
1. Calculate the start index for pagination: `(page - 1) * per_page`
2. Fill in the response structure with paginated data

### Task 4.2: Complete `create_note_v2` with Timestamps

```python
@app.route('/api/v2/notes', methods=['POST'])
@jwt_required()
def create_note_v2():
    """Version 2: Create note with timestamps and tags"""
    global note_id_counter
    current_user = get_jwt_identity()
    data = request.get_json()

    if not data or 'title' not in data:
        return jsonify({'error': 'Missing title'}), 400

    # TODO: Create note with v2 fields
    note = {
        'id': note_id_counter,
        'title': data['title'],
        'content': data.get('content', ''),
        'tags': data.get('tags', []),
        'owner': current_user,
        'created_at': _____,  # TODO: Add timestamp
        'updated_at': _____   # TODO: Add timestamp
    }

    notes[note_id_counter] = note
    note_id_counter += 1

    # TODO: Wrap response in 'data' object for v2
    response_data = _____

    response = make_response(jsonify(response_data), 201)
    response = add_version_headers(response, 'v2')

    return response
```

**Your tasks:**
1. Add `created_at` timestamp using `datetime.utcnow().isoformat()`
2. Add `updated_at` timestamp
3. Wrap the response: `{'data': note, 'message': 'Note created successfully'}`

### Task 4.3: Complete `get_note_v2`

```python
@app.route('/api/v2/notes/<int:note_id>', methods=['GET'])
@jwt_required()
def get_note_v2(note_id):
    """Version 2: Get a specific note with wrapped response"""
    current_user = get_jwt_identity()

    if note_id not in notes:
        return jsonify({'error': 'Note not found'}), 404

    note = notes[note_id]

    if note['owner'] != current_user:
        return jsonify({'error': 'Unauthorized'}), 403

    # TODO: Wrap note in 'data' object for v2 response
    response_data = _____

    response = make_response(jsonify(response_data))
    response = add_version_headers(response, 'v2')

    return response
```

**Your task:**
Wrap the note in a data object: `{'data': note}`

## Part 5: Testing the Versions (40 minutes)

### Step 5.1: Start the Application

```bash
cd exercises/15-versioning
python app.py
```

You should see both v1 and v2 endpoints listed.

### Step 5.2: Register and Login

```bash
# Register a user
curl -X POST http://127.0.0.1:5000/auth/register \
  -H "Content-Type: application/json" \
  -d '{"username":"alice","password":"password123"}'

# Login to get JWT token
curl -X POST http://127.0.0.1:5000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"alice","password":"password123"}'
```

Save the `access_token` from the response.

### Step 5.3: Test Version 1 (Deprecated)

**Create notes using v1:**
```bash
TOKEN="your_access_token_here"

curl -X POST http://127.0.0.1:5000/api/v1/notes \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"title":"My First Note","content":"This is v1"}'
```

**Expected response (v1 format):**
```json
{
  "id": 1,
  "title": "My First Note",
  "content": "This is v1",
  "owner": "alice"
}
```

**Get notes using v1:**
```bash
curl -i http://127.0.0.1:5000/api/v1/notes \
  -H "Authorization: Bearer $TOKEN"
```

**Check the headers - you should see deprecation warnings:**
```
API-Version: v1
Deprecation: @1767225600
Sunset: Wed, 30 Jun 2027 00:00:00 GMT
Link: </api/v2>; rel="successor-version"
```

**Response body (v1 format - simple array):**
```json
[
  {
    "id": 1,
    "title": "My First Note",
    "content": "This is v1",
    "owner": "alice"
  }
]
```

### Step 5.4: Test Version 2 (Current)

**Create notes using v2 (with tags):**
```bash
TOKEN="your_access_token_here"

curl -X POST http://127.0.0.1:5000/api/v2/notes \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"title":"My Second Note","content":"This is v2","tags":["work","important"]}'
```

**Expected response (v2 format - wrapped with timestamps):**
```json
{
  "data": {
    "id": 2,
    "title": "My Second Note",
    "content": "This is v2",
    "tags": ["work", "important"],
    "owner": "alice",
    "created_at": "2024-01-01T10:30:00.123456",
    "updated_at": "2024-01-01T10:30:00.123456"
  },
  "message": "Note created successfully"
}
```

**Get notes using v2 (with pagination):**
```bash
curl -i "http://127.0.0.1:5000/api/v2/notes?page=1&per_page=5" \
  -H "Authorization: Bearer $TOKEN"
```

**Check the headers - NO deprecation warnings:**
```
API-Version: v2
```

**Response body (v2 format - wrapped with metadata):**
```json
{
  "data": [
    {
      "id": 1,
      "title": "My First Note",
      "content": "This is v1",
      "owner": "alice"
    },
    {
      "id": 2,
      "title": "My Second Note",
      "content": "This is v2",
      "tags": ["work", "important"],
      "owner": "alice",
      "created_at": "2024-01-01T10:30:00.123456",
      "updated_at": "2024-01-01T10:30:00.123456"
    }
  ],
  "count": 2,
  "page": 1,
  "per_page": 5
}
```

**Note:** v1 notes don't have timestamps or tags because they were created using v1 endpoints. v2 can read them, but they'll be missing those fields.

### Step 5.5: Test v2-Exclusive Features

**Update a note (only in v2):**
```bash
curl -X PUT http://127.0.0.1:5000/api/v2/notes/2 \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"title":"Updated Note","tags":["work","urgent"]}'
```

**Response:**
```json
{
  "data": {
    "id": 2,
    "title": "Updated Note",
    "content": "This is v2",
    "tags": ["work", "urgent"],
    "owner": "alice",
    "created_at": "2024-01-01T10:30:00.123456",
    "updated_at": "2024-01-01T10:35:00.789012"
  },
  "message": "Note updated successfully"
}
```

Notice `updated_at` changed!

**Try to update using v1 (will fail - endpoint doesn't exist):**
```bash
curl -X PUT http://127.0.0.1:5000/api/v1/notes/2 \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"title":"This will fail"}'
```

**Response:**
```json
{"error": "Method Not Allowed"}
```

### Step 5.6: Check Version Information

```bash
curl http://127.0.0.1:5000/api/versions
```

**Response:**
```json
{
  "versions": {
    "v1": {
      "status": "deprecated",
      "deprecation_date": "2026-01-01",
      "sunset_date": "2027-06-30",
      "successor": "/api/v2",
      "deprecation_notice": "API v1 is deprecated. Please migrate to v2."
    },
    "v2": {
      "status": "current",
      "deprecation_date": null,
      "sunset_date": null,
      "successor": null,
      "deprecation_notice": null
    }
  },
  "current": "v2",
  "deprecated": ["v1"]
}
```

## Part 6: Understanding Breaking Changes (15 minutes)

### Compare the Responses

**v1 GET /api/v1/notes:**
```json
[
  {"id": 1, "title": "Note", "content": "...", "owner": "alice"}
]
```

**v2 GET /api/v2/notes:**
```json
{
  "data": [
    {
      "id": 1,
      "title": "Note",
      "content": "...",
      "tags": [],
      "owner": "alice",
      "created_at": "...",
      "updated_at": "..."
    }
  ],
  "count": 1,
  "page": 1,
  "per_page": 10
}
```

**Why this is BREAKING:**

If you changed v1 to return the v2 format, **every client** would break:

```javascript
// Client code expecting v1
fetch('/api/v1/notes')
  .then(response => response.json())
  .then(notes => {
    notes.forEach(note => {  // Expects an array
      console.log(note.title);
    });
  });
```

After changing to v2 format, this code would crash:
```
TypeError: notes.forEach is not a function
```

Because `notes` is now an object `{data: [...]}`, not an array!

**Solution:** Keep v1 as-is, create v2 with the new format.

## Part 7: Deprecation Strategy (10 minutes)

### The Deprecation Timeline

**Step 1: Launch v2 (Today)**
- Announce v2 availability
- Encourage migration
- v1 still fully supported

**Step 2: Deprecate v1 (1-3 months later)**
- Add deprecation headers to v1
- Set sunset date (e.g., 6 months)
- Update documentation
- Email clients about deprecation

**Step 3: Sunset Warning (3 months before sunset)**
- Increase urgency in warnings
- Offer migration support
- Identify clients still using v1

**Step 4: Remove v1 (Sunset date)**
- v1 endpoints return 410 Gone
- All clients must use v2

### Communicating Deprecation

**In response headers (automatic):**
```
Deprecation: @1767225600
Sunset: Wed, 30 Jun 2027 00:00:00 GMT
Link: </api/v2>; rel="successor-version"
```

**In documentation:**
```markdown
## ⚠️ Deprecation Notice

API v1 is deprecated and will be sunset on **June 30, 2027**.

Please migrate to v2. See migration guide: [link]
```

**Via email:**
```
Subject: Action Required: Migrate to API v2

Dear valued customer,

API v1 will be retired on June 30, 2027. Please migrate to v2
before this date to avoid service interruption.

Migration guide: [link]
Need help? Contact support@example.com
```

## Best Practices

### 1. Version at the Start

Don't wait! Start with `/api/v1` from day one, even if you don't plan changes.

```python
# ✅ Good - versioned from the start
@app.route('/api/v1/users')

# ❌ Bad - hard to version later
@app.route('/api/users')
```

### 2. Version the Namespace, Not Individual Endpoints

```python
# ✅ Good - entire namespace versioned
/api/v1/users
/api/v1/notes
/api/v1/tags

# ❌ Bad - inconsistent versioning
/api/users/v1
/api/v2/notes
```

### 3. Don't Version Authentication

Auth endpoints are usually stable and don't need versioning:

```python
# ✅ Good - auth outside version namespace
/auth/register
/auth/login

# ❌ Bad - unnecessary versioning
/api/v1/auth/login
/api/v2/auth/login
```

### 4. Support Multiple Versions, But Not Forever

**Recommended:**
- Support 2-3 versions maximum
- 6-12 month deprecation period
- Clear sunset dates

**Example timeline:**
- v1: Jan 2023 - Dec 2024 (deprecated June 2024)
- v2: June 2024 - ongoing
- v3: Jan 2025 - ongoing

### 5. Document Breaking Changes Clearly

```markdown
## v2 Migration Guide

### Breaking Changes

1. **Response format**: All list endpoints now return `{data: [...], count: N}`
   - **Before (v1)**: `GET /api/v1/notes` → `[...]`
   - **After (v2)**: `GET /api/v2/notes` → `{data: [...], count: 2}`
   - **Fix**: Update client code to read `response.data` instead of `response`

2. **Timestamps**: All resources now include `created_at` and `updated_at`
   - **Impact**: None (additional fields are backward compatible when reading)

3. **Update endpoint**: New `PUT /api/v2/notes/<id>` endpoint
   - **Before**: No update endpoint in v1
   - **After**: Use PUT to update notes

### Non-Breaking Changes

- New optional `tags` field on notes (can be omitted)
- Pagination query params `page` and `per_page` (optional)
```

### 6. Use Semantic Versioning (Optional)

For complex APIs, consider semantic versioning:

```
v1.0.0 → v1.1.0 (added optional field - backward compatible)
v1.1.0 → v1.2.0 (added new endpoint - backward compatible)
v1.2.0 → v2.0.0 (changed response format - BREAKING)
```

### 7. Monitor Version Usage

Track which clients use which versions:

```python
from collections import Counter

version_usage = Counter()

@app.after_request
def track_version(response):
    version = response.headers.get('API-Version')
    if version:
        version_usage[version] += 1
    return response

@app.route('/api/admin/version-stats')
def version_stats():
    return jsonify(dict(version_usage))
```

This helps you understand when it's safe to sunset old versions.

## Common Mistakes

### Mistake 1: Versioning Too Often

❌ **Bad:**
```
v1 (Jan) → v2 (Feb) → v3 (Mar) → v4 (Apr)
```

Clients can't keep up with constant breaking changes!

✅ **Good:**
```
v1 (Jan 2023) → v2 (Jan 2024)
```

Only version when absolutely necessary.

### Mistake 2: Not Communicating Changes

❌ **Bad:**
- Change response format without warning
- No deprecation headers
- No migration guide

✅ **Good:**
- Announce v2 launch
- Add deprecation headers to v1
- Provide detailed migration guide
- Email clients about changes

### Mistake 3: Removing Old Versions Too Quickly

❌ **Bad:**
```
June 1: Launch v2
June 15: Remove v1 (2 weeks later)
```

Clients need time to migrate!

✅ **Good:**
```
June 1: Launch v2
Sept 1: Deprecate v1 (3 months to adapt)
Dec 1: Sunset v1 (6 months total)
```

### Mistake 4: Treating Non-Breaking Changes as Breaking

❌ **Bad:**
```python
# v1
{"id": 1, "name": "Alice"}

# Unnecessarily created v2 just to add optional field
# v2
{"id": 1, "name": "Alice", "email": "alice@example.com"}
```

This is backward compatible! Just add the field to v1.

✅ **Good:**
```python
# v1 (updated with optional field)
{"id": 1, "name": "Alice", "email": "alice@example.com"}
```

### Mistake 5: Inconsistent Versioning

❌ **Bad:**
```
/api/v1/users (uses v1 conventions)
/api/v2/notes (uses v2 conventions)
/api/comments   (no version - uses ??)
```

✅ **Good:**
```
/api/v1/users
/api/v1/notes
/api/v1/comments

/api/v2/users
/api/v2/notes
/api/v2/comments
```

All resources follow the same versioning strategy.

## Testing Checklist

**Setup:**
- [ ] Flask app installed and runs
- [ ] Can register and login successfully
- [ ] JWT token obtained

**Version 1 (Deprecated):**
- [ ] Can create note using v1 endpoint
- [ ] Can get all notes using v1 (returns array)
- [ ] Can get single note using v1
- [ ] Response includes deprecation headers
- [ ] Response includes sunset date header

**Version 2 (Current):**
- [ ] Can create note using v2 endpoint (with tags)
- [ ] Created note includes timestamps (created_at, updated_at)
- [ ] Can get all notes using v2 (returns wrapped object)
- [ ] v2 response includes count and page metadata
- [ ] Pagination works with page and per_page params
- [ ] Can get single note using v2 (wrapped in data object)
- [ ] Can update note using v2 PUT endpoint
- [ ] Response includes API-Version header
- [ ] Response does NOT include deprecation headers

**Version Information:**
- [ ] `/api/versions` returns info about all versions
- [ ] Can identify current and deprecated versions

**Breaking Changes:**
- [ ] v1 and v2 return different response formats
- [ ] v1 returns simple array, v2 returns wrapped object
- [ ] v2 includes fields not in v1 (timestamps, tags)
- [ ] Both versions work simultaneously

## Real-World API Versioning Examples

### Stripe API

**Approach:** Dated versions (not v1, v2, but dates)

```bash
# Specify version via header
curl https://api.stripe.com/v1/customers \
  -H "Stripe-Version: 2023-10-16"
```

**Why?** Allows Stripe to release updates frequently without forcing migrations. Clients pin to a specific date version.

**Your account defaults to the version when you signed up**, but you can upgrade anytime.

### GitHub API

**Approach:** Major version changes (v3 REST → v4 GraphQL)

```bash
# v3 (REST)
GET https://api.github.com/users/octocat

# v4 (GraphQL)
POST https://api.github.com/graphql
```

**Why?** GraphQL is fundamentally different from REST, requiring a major version change. Both run in parallel.

### Twitter API

**Approach:** Major version changes with long deprecation

```bash
# v1.1 (deprecated 2023)
GET https://api.twitter.com/1.1/statuses/home_timeline.json

# v2 (current)
GET https://api.twitter.com/2/tweets
```

**Why?** Complete API redesign. Gave developers ~2 years to migrate.

### Twilio API

**Approach:** URL path versioning

```bash
# v1 (retired)
POST https://api.twilio.com/2008-08-01/Accounts/{AccountSid}/SMS/Messages

# v2 (current)
POST https://api.twilio.com/2010-04-01/Accounts/{AccountSid}/Messages
```

**Why?** Date-based versions, but uses URL path. Old versions eventually retired.

## Additional Resources

### Official Documentation
- **[RFC 8594 - Sunset HTTP Header](https://www.rfc-editor.org/rfc/rfc8594.html)** - Standard for deprecation
- **[Semantic Versioning](https://semver.org/)** - Version numbering strategy
- **[API Versioning Best Practices](https://www.troyhunt.com/your-api-versioning-is-wrong-which-is/)** - Troy Hunt's article

### Tutorials
- [Stripe API Versioning](https://stripe.com/docs/api/versioning) - Real-world example
- [GitHub API Versioning](https://docs.github.com/en/rest/overview/api-versions) - Major version changes

## Deliverables

When you complete this exercise, you should have:

1. **Completed `app.py`**:
   - All TODOs filled in correctly
   - Version headers implemented
   - v1 and v2 endpoints working
   - Deprecation warnings on v1

2. **Testing Evidence**:
   - Screenshots or logs showing v1 with deprecation headers
   - Screenshots showing v2 without deprecation
   - Examples of different response formats

3. **Understanding**:
   - Explain when to create a new version
   - Identify breaking vs non-breaking changes
   - Describe deprecation strategy
   - Compare v1 and v2 response structures

## Questions to Consider

1. When would adding a new field require a new version?
2. Why do we add deprecation headers to v1 but not v2?
3. How would you handle a client that refuses to migrate from v1?
4. What's the difference between versioning `/api/v1/notes` vs `/api/notes?version=1`?
5. How would you version a single endpoint without versioning the entire API?
6. When would you choose header-based versioning over URL path versioning?

Good luck managing your API versions! 🚀
