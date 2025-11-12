from fastapi import APIRouter, HTTPException
import random
# from app.books.add_book import _BOOK_STORE
from app.models import Book

router = APIRouter()

@router.get("/books/recommendation", response_model=Book, operation_id="GetBookRecommendation")
async def get_recommendation():
    # TODO:  Return books from database
    return "get_recommendation return value"
    # if not _BOOK_STORE:
    #     raise HTTPException(status_code=404, detail="No books available")
    # return random.choice(list(_BOOK_STORE.values()))
