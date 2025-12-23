from fastapi import APIRouter, HTTPException
import random
# from app.books.add_book import _BOOK_STORE
from app.models import Book

router = APIRouter()

@router.get("/books/recommendation", response_model=Book, operation_id="GetBookRecommendation")
async def get_recommendation():
    # TODO:  Return books from database
    # from datetime import datetime, timezone
    # utc_now = datetime.now(timezone.utc)
    # book = Book(
    #     id="internal_id",
    #     title="req.title",
    #     author="req.author",
    #     owner_id="req.owner_id",
    #     book_id="req.book_id",
    #     relevant_text="req.relevant_text",
    #     created_at=utc_now,
    #     updated_at=utc_now,
    # )
    # return book
    return None
    # if not _BOOK_STORE:
    #     raise HTTPException(status_code=404, detail="No books available")
    # return random.choice(list(_BOOK_STORE.values()))
