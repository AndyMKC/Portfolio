from fastapi import APIRouter, Request, Query

from app.books.add_book import add_book
from app.books.clear_database import clear_database
from app.models import AddBookRequest, CleanedISBN

router = APIRouter()

@router.post("/reset", response_model=None, operation_id="ClearAndSeedDbForTesting")
async def clear_and_seed_db(
    request: Request,
    owner: str = Query(..., example="user@gmail.com")
    ):
    await clear_database()
    
    add_book_request = AddBookRequest(
        owner=owner,
        isbns=[
            CleanedISBN(isbn="978-0448487311"), # Little Engine that Could
            CleanedISBN(isbn="978-142311411-6"), # Pigs Make Me Sneeze
            CleanedISBN(isbn="978-0763680077"), # The Princess and the Giant
            CleanedISBN(isbn="978-1423199571"), # Waiting is not Easy!
            CleanedISBN(isbn="978-1423106869"), # There is a Bird on your Head!
            CleanedISBN(isbn="978-1423143437"), # Should I Share My Ice Cream?
            CleanedISBN(isbn="978-1423133087"), # We Are in a Book!
            CleanedISBN(isbn="978-1423174912"), # A Big Guy Took My Ball!
            CleanedISBN(isbn="978-1423179580"), # My New Friend Is So Fun!
            CleanedISBN(isbn="978-1423133094"), # I Broke My Trunk!
            CleanedISBN(isbn="978-1423106876"), # I Am Invited to a Party!
            CleanedISBN(isbn="978-1423119906"), # I Am Going!
            CleanedISBN(isbn="978-1423102977") # My Friend is Sad
        ]
    )
    await add_book(
        request=request,
        add_book_request=add_book_request
    )
