from fastapi import APIRouter, Request, Query

from app.books.add_book import add_book
from app.books.clear_database import clear_database
from app.models import AddBookRequest

router = APIRouter()

@router.post("/reset", response_model=None, operation_id="ClearAndSeedDB")
async def clear_and_seed_db(
    request: Request,
    owner: str = Query(..., example="user@gmail.com")
    ):
    await clear_database()
    
    add_book_request = AddBookRequest(
        owner=owner,
        isbns=[
            "978-0448487311", # Little Engine that Could
            "978-142311411-6", # Pigs Make Me Sneeze
            "978-0763680077", # The Princess and the Giant
            "978-1423199571", # Waiting is not Easy!
            "978-1423106869", # There is a Bird on your Head!
            "978-1423143437", # Should I Share My Ice Cream?
            "978-1423133087", # We Are in a Book!
            "978-1423174912", # A Big Guy Took My Ball!"
            "978-1423179580", # My New Friend Is So Fun!"
            "978-1423133094", # I Broke My Trunk!"
            "978-1423106876", # I Am Invited to a Party!"
            "978-1423119906", # I Am Going!"
            "978-1423102977", # My Friend is Sad"
        ]
    )
    await add_book(
        request=request,
        add_book_request=add_book_request
    )
