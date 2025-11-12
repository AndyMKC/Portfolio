from fastapi import APIRouter, HTTPException
from datetime import datetime
#from app.books.add_book import _BOOK_STORE

router = APIRouter()

@router.post("/books/{book_id}/mark-read", operation_id="MarkBookRead")
async def mark_book_read(owner_id: str,book_id: str):
    # TODO:  Update and return book info from database
    return "mark_book_read return value"
    # book_id here is the internal UUID stored as key; if you prefer ISBN lookup, adapt logic.
    # book = _BOOK_STORE.get(book_id)
    # if not book:
    #     raise HTTPException(status_code=404, detail="Book not found")
    # book.last_read = datetime.utcnow()
    # book.updated_at = datetime.utcnow()
    # return {"status": "marked as read", "book_id": book_id}
