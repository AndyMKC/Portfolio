from fastapi import APIRouter, HTTPException
from datetime import datetime, timezone
import uuid

from app.models import AddBookRequest, Book

router = APIRouter()
# # in-memory store for dev; replace with persistent DB later
# _BOOK_STORE: dict[str, Book] = {}

# Placeholder for embedding + vector DB upsert.
# Implement actual embedding generation and BigQuery vector upsert later.
def _enqueue_vector_upsert(book: Book) -> None:
    """
    Placeholder: generate embedding from book.relevant_text and upsert into vector index.
    Implement async background task, Pub/Sub, or direct API call in production.
    """
    # Example:
    # embedding = embed_text(book.relevant_text)
    # bigquery_vector_upsert(namespace=book.owner_id, id=book.book_id, vector=embedding, metadata=...)
    return

@router.post("/books", response_model=Book, status_code=201, operation_id="AddBook")
async def add_book(req: AddBookRequest):
    # Use provided ISBN as canonical book_id; generate internal UUID id for this record
    # Enforce uniqueness per owner + book_id (ISBN)
    key = f"{req.owner_id}:{req.book_id}"
    # TODO:  Check to see if this owner already has this book_id added

    internal_id = str(req.owner_id + req.book_id)
    utc_now = datetime.now(timezone.utc)
    book = Book(
        id=internal_id,
        title=req.title,
        author=req.author,
        owner_id=req.owner_id,
        book_id=req.book_id,
        relevant_text=req.relevant_text,
        created_at=utc_now,
        updated_at=utc_now,
    )

    # non-blocking background work: enqueue vector upsert (placeholder sync call here)
    try:
        _enqueue_vector_upsert(book)
    except Exception:
        # do not fail the request if embedding/upsert pipeline is temporarily failing
        pass

    return book
