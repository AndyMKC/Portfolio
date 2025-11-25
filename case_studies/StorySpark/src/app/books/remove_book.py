from fastapi import APIRouter
#from app.books.add_book import _BOOK_STORE
from app.models import Book

router = APIRouter()

@router.delete("/books/{book_id}", response_model=Book, operation_id="RemoveBook")
async def remove_book(book_id: str):
    # TODO:  Remove book from database for this owner and return removed book info
    from datetime import datetime, timezone
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
    # if book_id not in _BOOK_STORE:
    #     raise HTTPException(status_code=404, detail="Book not found")
    # del _BOOK_STORE[book_id]
    # # Optionally enqueue vector deletion from the vector DB
    # return {"status": "removed", "book_id": book_id}
