from fastapi import APIRouter
#from app.books.add_book import _BOOK_STORE
from app.models import Book

router = APIRouter()

@router.get("/books", response_model=list[Book], operation_id="GetAllBooks")
async def get_all_books(owner_id: str):
    # TODO:  Return all books from this specific owner
    return "get_all_books return value"
    #return list(_BOOK_STORE.values())
