from fastapi import APIRouter
from datetime import datetime, timezone
#from app.books.add_book import _BOOK_STORE
from app.models import Book

router = APIRouter()

@router.post("/books/{book_id}/mark-read", response_model=Book, operation_id="MarkBookRead")
async def mark_book_read(owner_id: str,book_id: str):
    # TODO:  Update and return book info from database
    
    utc_now = datetime.now(timezone.utc)
    book = Book(
        id="internal_id",
        title="req.title",
        author="req.author",
        owner_id="req.owner_id",
        book_id="req.book_id",
        relevant_text="req.relevant_text",
        created_at=utc_now,
        updated_at=utc_now,
    )
    return book
    # book_id here is the internal UUID stored as key; if you prefer ISBN lookup, adapt logic.
    # book = _BOOK_STORE.get(book_id)
    # if not book:
    #     raise HTTPException(status_code=404, detail="Book not found")
    # book.last_read = datetime.utcnow()
    # book.updated_at = datetime.utcnow()
    # return {"status": "marked as read", "book_id": book_id}
