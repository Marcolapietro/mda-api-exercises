"""
Undocumented Books API
This API has NO documentation - students must figure it out through trial and error.
(FastAPI normally serves /docs and /openapi.json; here they are switched off on purpose.)
"""

from fastapi import FastAPI
from fastapi.responses import JSONResponse

app = FastAPI(docs_url=None, redoc_url=None, openapi_url=None)

# In-memory book storage
books = {
    1: {'id': 1, 'title': '1984', 'author': 'George Orwell', 'year': 1949, 'isbn': '978-0451524935'},
    2: {'id': 2, 'title': 'To Kill a Mockingbird', 'author': 'Harper Lee', 'year': 1960, 'isbn': '978-0061120084'},
    3: {'id': 3, 'title': 'The Great Gatsby', 'author': 'F. Scott Fitzgerald', 'year': 1925, 'isbn': '978-0743273565'}
}
next_id = 4


@app.get('/')
def index():
    return 'Books API is running. But where are the endpoints?'


# Support filtering by author (but students don't know this!)
# Support pagination (but students don't know the param names!)
@app.get('/api/books')
def list_books(author: str | None = None, page: int = 1, limit: int = 10):
    result = list(books.values())

    if author:
        result = [b for b in result if author.lower() in b['author'].lower()]

    # Simple pagination
    start = (page - 1) * limit
    end = start + limit
    paginated = result[start:end]

    return {
        'books': paginated,
        'total': len(result),
        'page': page,
        'limit': limit
    }


@app.post('/api/books', status_code=201)
def create_book(data: dict | None = None):
    global next_id

    # No validation error messages - students must guess what's wrong
    if not data or 'title' not in data or 'author' not in data:
        return JSONResponse({'error': 'Bad request'}, status_code=400)

    book = {
        'id': next_id,
        'title': data['title'],
        'author': data['author'],
        'year': data.get('year'),
        'isbn': data.get('isbn')
    }
    books[next_id] = book
    next_id += 1

    return book


@app.get('/api/books/{book_id}')
def get_book(book_id: int):
    if book_id not in books:
        return JSONResponse({'error': 'Not found'}, status_code=404)
    return books[book_id]


@app.put('/api/books/{book_id}')
def update_book(book_id: int, data: dict | None = None):
    if book_id not in books:
        return JSONResponse({'error': 'Not found'}, status_code=404)

    if not data:
        return JSONResponse({'error': 'Bad request'}, status_code=400)

    # Update fields
    book = books[book_id]
    if 'title' in data:
        book['title'] = data['title']
    if 'author' in data:
        book['author'] = data['author']
    if 'year' in data:
        book['year'] = data['year']
    if 'isbn' in data:
        book['isbn'] = data['isbn']

    return book


@app.delete('/api/books/{book_id}')
def delete_book(book_id: int):
    if book_id not in books:
        return JSONResponse({'error': 'Not found'}, status_code=404)

    deleted = books.pop(book_id)
    return {'message': 'Book deleted', 'book': deleted}
