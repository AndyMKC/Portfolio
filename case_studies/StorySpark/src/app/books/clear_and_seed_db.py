from fastapi import APIRouter, HTTPException

router = APIRouter()

@router.get("/books", response_model=None, operation_id="ClearAndSeedDB")
async def clear_and_seed_db():
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
