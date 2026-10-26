# Exercise 9: Implementing Pagination in Endpoints (Notes API)

## Quick Start

```bash
cd exercises/09-api-pagination
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
python app.py
```

The API runs at `http://127.0.0.1:5000` and starts with **95 seed notes** (ids 1 to 95), so there is something to paginate.

## Objective

- **Implement Pagination in Endpoints:** split a big collection into pages instead of returning everything at once.
- **Compare two strategies:** offset/limit and cursor, and see with your own eyes why cursors are more stable.
- **Query Parameter Handling:** default and maximum page size, validation, and `next`/`prev` links (in the body and in the `Link` header).

## Description

This exercise builds on the Notes API of exercise 08 (same `/notes` resource, same CRUD, same RFC 9457 errors, **no authentication**). Now `GET /notes` returns the notes **newest first** (by `id`, descending) and supports two pagination modes:

| Mode | Request | Pros / cons |
|------|---------|-------------|
| Offset/limit | `GET /notes?offset=40&limit=20` | Simple, you can jump to any page and you know the `total`. Inconsistent when data changes while you paginate. |
| Cursor | `GET /notes?cursor=<opaque>&limit=20` | Stable: it continues "after the last note you saw". The cursor is an opaque token (here: base64 of the last id). |

Complete the blanks (`_____`) in `app.py`.

## Requirements

1. **Dependencies:**
   - Only `Flask` (see `requirements.txt`). `base64` comes with Python.

2. **API Structure:**
   - `GET /notes`: paginated list (see the rules below).
   - `POST /notes`, `GET /notes/<id>`, `PUT /notes/<id>`, `PATCH /notes/<id>`, `DELETE /notes/<id>`: same as exercise 08 (`POST` returns `201` + `Location`, `DELETE` returns `204`).

3. **Pagination rules for `GET /notes`:**
   - `limit`: default `20`, maximum `100`. **A bigger value is clamped to `100`** (it is not an error); `page.limit` tells you the value that was really used. `limit` that is not an integer or is `< 1` is a `400`.
   - **Offset mode** when you send `offset` (integer `>= 0`). The `page` object includes `total`.
   - **Cursor mode** otherwise: without `cursor` you get the first page; then you send the `next_cursor` you received. The `page` object includes `next_cursor`.
   - Sending `offset` **and** `cursor` together is a `400`. An invalid cursor is a `400`.
   - Response body: `{"data": [...], "page": {...}}`, where `page.next` / `page.prev` are full URLs (or `null`).
   - Header `Link` (RFC 8288) with `rel="next"` and, when there is a previous page, `rel="prev"`.
   - In cursor mode, pagination is forward-only (like an infinite feed): `page.prev` is always `null`. To go back, the client reuses a cursor it already has.

4. **Testing:**
   - Use Postman or `curl` to request different pages and page sizes, follow the `next` links and check the errors.
   - Do the insert experiment below.

## Detailed Steps

1. **Read `app.py`:** the CRUD and the `problem()` helper are the ones from exercise 08. The new code is in the *Pagination helpers* section and in `GET /notes`.

2. **Default and maximum page size (`parse_limit`):** return `min(limit, MAX_LIMIT)`.

3. **Offset mode (`offset_page`):** slice the ordered list with `ordered[offset:offset + limit]` and compute where the next page starts.

4. **Cursor mode (`cursor_page`):**
   - Reject a cursor that cannot be decoded with a `400`.
   - The notes are newest first, so the notes that come *after* the cursor are the ones with a **smaller** id.
   - If there are more notes, `next_cursor` points to the **last** note of the current page.

5. **Mixing modes (`list_notes`):** `offset` + `cursor` together is a `400`.

6. **Navigation links (`paged_response`):** fill in the link relation types for the `Link` header: `next` and `prev`.

## Code Example

The opaque cursor is just base64 (URL-safe, without `=` padding) of the last id the client has seen. The client must not build it or care what is inside: it only sends back what it received.

```python
def encode_cursor(note_id):
    return base64.urlsafe_b64encode(str(note_id).encode()).decode().rstrip('=')   # 91 -> "OTE"


def decode_cursor(cursor):
    try:
        padded = cursor + '=' * (-len(cursor) % 4)
        raw = base64.urlsafe_b64decode(padded).decode('ascii')
    except ValueError:  # bad base64 or non-ASCII content
        return None
    if not raw.isdigit():
        return None
    return int(raw)
```

The `Link` header puts the same `next`/`prev` URLs of the body in a standard place (RFC 8288):

```
Link: <http://127.0.0.1:5000/notes?offset=60&limit=20>; rel="next", <http://127.0.0.1:5000/notes?offset=20&limit=20>; rel="prev"
```

## Testing with Postman or `curl`

> **Windows:** in PowerShell use `curl.exe` (in Windows PowerShell 5.1 `curl` is an alias of `Invoke-WebRequest`), and keep the URL in double quotes because of the `&`. PowerShell 5.1 also removes the inner quotes of `-d '{...}'`, so for the `POST` use the ready-to-run files: `example/commands_cmd.txt` (CMD) and `example/commands_powershell.txt` (PowerShell, which also runs the whole experiment for you).

1. **Offset: a page in the middle (`200`):**

   ```bash
   curl -i "http://127.0.0.1:5000/notes?offset=40&limit=20"
   ```

   ```
   HTTP/1.1 200 OK
   Content-Type: application/json
   Link: <http://127.0.0.1:5000/notes?offset=60&limit=20>; rel="next", <http://127.0.0.1:5000/notes?offset=20&limit=20>; rel="prev"
   ```

   ```json
   {
     "data": [
       {"id": 55, "title": "Note 55", "content": "Seed note number 55", "created_at": "2026-01-01T00:55:00Z", "updated_at": "2026-01-01T00:55:00Z"},
       "... 18 more notes ...",
       {"id": 36, "title": "Note 36", "content": "Seed note number 36", "created_at": "2026-01-01T00:36:00Z", "updated_at": "2026-01-01T00:36:00Z"}
     ],
     "page": {
       "mode": "offset",
       "offset": 40,
       "limit": 20,
       "total": 95,
       "next": "http://127.0.0.1:5000/notes?offset=60&limit=20",
       "prev": "http://127.0.0.1:5000/notes?offset=20&limit=20"
     }
   }
   ```

2. **Offset: first and last page:** the first page has `"prev": null` and only `rel="next"`; the last one has `"next": null` and only `rel="prev"`.

   ```bash
   curl -i "http://127.0.0.1:5000/notes?offset=0&limit=5"
   curl -i "http://127.0.0.1:5000/notes?offset=90&limit=5"
   ```

3. **Cursor: first page (`200`):** no `offset`, no `cursor`.

   ```bash
   curl -i "http://127.0.0.1:5000/notes?limit=5"
   ```

   ```json
   {
     "data": ["... notes 95, 94, 93, 92, 91 ..."],
     "page": {
       "mode": "cursor",
       "limit": 5,
       "next_cursor": "OTE",
       "next": "http://127.0.0.1:5000/notes?cursor=OTE&limit=5",
       "prev": null
     }
   }
   ```

4. **Cursor: next page:** send back the `next_cursor` (or simply follow `page.next`). You get notes 90 to 86. On the last page `next_cursor` and `next` are `null`.

   ```bash
   curl -i "http://127.0.0.1:5000/notes?cursor=OTE&limit=5"
   ```

5. **Default and maximum page size:** `GET /notes` returns 20 notes; `?limit=500` is clamped and `page.limit` is `100`.

   ```bash
   curl -i "http://127.0.0.1:5000/notes"
   curl -i "http://127.0.0.1:5000/notes?limit=500"
   ```

6. **Errors (`400`, `application/problem+json`):**

   ```bash
   curl -i "http://127.0.0.1:5000/notes?offset=0&cursor=OTE"         # offset and cursor together
   curl -i "http://127.0.0.1:5000/notes?cursor=not-a-real-cursor"   # invalid cursor
   curl -i "http://127.0.0.1:5000/notes?limit=0"                    # invalid limit
   curl -i "http://127.0.0.1:5000/notes?offset=-1"                  # invalid offset
   ```

   ```json
   {"type": "about:blank", "title": "Bad Request", "status": 400, "detail": "Use either offset or cursor, not both."}
   ```

7. **Create a note (`201` + `Location`)**, needed for the experiment:

   ```bash
   curl -i -X POST http://127.0.0.1:5000/notes -H "Content-Type: application/json" -d '{"title": "Inserted while paginating"}'
   ```

## Experiment: What Happens With Offset If Someone Inserts a Record While You Paginate?

Restart the app (`python app.py`) so you start from the 95 seed notes.

**A. Offset**

1. Read page 1: `curl "http://127.0.0.1:5000/notes?offset=0&limit=5"` → notes **95, 94, 93, 92, 91**.
2. Someone inserts a note: run the `POST` from step 7 → it gets id **96** and goes to the top (newest first).
3. Read page 2: `curl "http://127.0.0.1:5000/notes?offset=5&limit=5"` → notes **91, 90, 89, 88, 87**.

Note **91 appears twice**. The offset counts positions, and the new note pushed everything one position down. It is the slide's diagram with other numbers: there a new item 21 makes item 16 appear twice. (If a note is *deleted* between the two requests, the opposite happens: one note is *skipped* and you never see it. Try it with `DELETE /notes/95`.)

**B. Cursor**

1. Read page 1: `curl "http://127.0.0.1:5000/notes?limit=5"` and copy `page.next_cursor` (after a fresh start it is `OTE`, base64 of 91; if you did part A first, the first page starts at 96 and the cursor is `OTI`).
2. Insert another note with the `POST` from step 7.
3. Read page 2 with **your** cursor: `curl "http://127.0.0.1:5000/notes?cursor=OTE&limit=5"` (replace `OTE` with the value you copied) → it continues right after the last note you saw (90, 89, 88, 87, 86 after a fresh start).

**No duplicates and nothing skipped**: the cursor does not say "skip 5 positions", it says "after id 91", and that does not change when new notes arrive (the slide's "after id 16").

## Points to Consider

- Always have a default and a maximum page size; document whether a bigger value is clamped (as here) or rejected with a `400`.
- Offset is fine for small or static data and for "go to page 7" UIs; for feeds and data that changes, prefer cursors.
- Keep the cursor opaque: clients must not build or decode it, so you can change what is inside without breaking them.
- Pagination needs a stable order. Here it is `id` descending; with offset you also pay for counting `total` and skipping rows on every request.
- The data is in memory: restarting the app brings back the 95 seed notes.
- Debug mode is off by default. To turn it on: `FLASK_DEBUG=1 python app.py` (PowerShell: `$env:FLASK_DEBUG="1"; python app.py`).

Good luck with the implementation! If you have questions, don't hesitate to ask.
