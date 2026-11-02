"""
Documented Books API using FastAPI
FastAPI generates the OpenAPI spec (/openapi.json) and Swagger UI (/docs) from the type hints
and models below. Nothing else is needed: the documentation can never drift from the code.
"""

from typing import Annotated

from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel, Field

# API metadata shown at the top of Swagger UI
app = FastAPI(
    title='Books API',
    version='1.0.0',
    description='A well-documented API for managing books. Compare this to the undocumented version!'
)


# What a client sends to create a book.
# Field(description=..., examples=[...]) feeds the schema and the example values in Swagger UI.
class BookCreate(BaseModel):
    title: str = Field(description='Book title', examples=['1984'])
    author: str = Field(description='Book author', examples=['George Orwell'])
    year: int | None = Field(default=None, description='Publication year', examples=[1949])
    isbn: str | None = Field(default=None, description='ISBN number', examples=['978-0451524935'])


# The book as the API returns it: the input fields plus the id that the server assigns
class Book(BookCreate):
    id: int = Field(description='The book unique identifier', examples=[1])


# In-memory book storage
books: dict[int, Book] = {
    1: Book(id=1, title='1984', author='George Orwell', year=1949, isbn='978-0451524935'),
    2: Book(id=2, title='To Kill a Mockingbird', author='Harper Lee', year=1960, isbn='978-0061120084'),
    3: Book(id=3, title='The Great Gatsby', author='F. Scott Fitzgerald', year=1925, isbn='978-0743273565')
}
next_id = 4


@app.get('/api/books', tags=['books'], summary='List all books')
def list_books(
    author: Annotated[str | None, Query(description='Filter books by author name (partial match)')] = None,
    page: Annotated[int, Query(ge=1, description='Page number for pagination')] = 1,
    limit: Annotated[int, Query(ge=1, le=100, description='Number of books per page')] = 10
) -> list[Book]:
    """Returns a list of books with optional filtering and pagination."""
    result = list(books.values())

    # Filter by author if provided
    if author:
        result = [b for b in result if author.lower() in b.author.lower()]

    # Pagination
    start = (page - 1) * limit
    return result[start:start + limit]


@app.post('/api/books', status_code=201, tags=['books'], summary='Create a new book')
def create_book(data: BookCreate) -> Book:
    """Provide title and author (required), year and isbn (optional)."""
    global next_id

    book = Book(id=next_id, **data.model_dump())
    books[next_id] = book
    next_id += 1

    return book


@app.get('/api/books/{book_id}', tags=['books'], summary='Get a book by ID',
         responses={404: {'description': 'Book not found'}})
def get_book(book_id: int) -> Book:
    """Returns a single book if it exists, otherwise returns 404."""
    if book_id not in books:
        raise HTTPException(status_code=404, detail=f'Book {book_id} not found')
    return books[book_id]


@app.put('/api/books/{book_id}', tags=['books'], summary='Replace a book',
         responses={404: {'description': 'Book not found'}})
def update_book(book_id: int, data: BookCreate) -> Book:
    """PUT replaces the whole book: send every field (year and isbn may be null). The id does not change."""
    if book_id not in books:
        raise HTTPException(status_code=404, detail=f'Book {book_id} not found')

    books[book_id] = Book(id=book_id, **data.model_dump())
    return books[book_id]


@app.delete('/api/books/{book_id}', status_code=204, tags=['books'], summary='Delete a book',
            responses={404: {'description': 'Book not found'}})
def delete_book(book_id: int) -> None:
    """Permanently removes the book from the system."""
    if book_id not in books:
        raise HTTPException(status_code=404, detail=f'Book {book_id} not found')

    del books[book_id]
