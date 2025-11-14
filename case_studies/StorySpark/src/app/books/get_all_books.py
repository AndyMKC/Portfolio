from fastapi import APIRouter
#from app.books.add_book import _BOOK_STORE
from app.models import Book

router = APIRouter()

@router.get("/books", response_model=list[Book], operation_id="GetAllBooks")
async def get_all_books(owner_id: str):
    # TODO:  Return all books from this specific owner
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
    return list([book])
    #return list(_BOOK_STORE.values())
