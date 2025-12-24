from fastapi import APIRouter
from app.models import Book

router = APIRouter()

@router.get("/books/recommendation", response_model=list[Book], operation_id="GetBookRecommendation")
async def get_recommendation() -> list[Book]:
    return None
