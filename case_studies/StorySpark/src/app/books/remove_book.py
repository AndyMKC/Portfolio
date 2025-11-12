from fastapi import APIRouter, HTTPException
#from app.books.add_book import _BOOK_STORE

router = APIRouter()

@router.delete("/books/{book_id}", operation_id="RemoveBook")
async def remove_book(book_id: str):
    # TODO:  Remove book from database for this owner and return removed book info
    return "remove_book return value"
    # if book_id not in _BOOK_STORE:
    #     raise HTTPException(status_code=404, detail="Book not found")
    # del _BOOK_STORE[book_id]
    # # Optionally enqueue vector deletion from the vector DB
    # return {"status": "removed", "book_id": book_id}
