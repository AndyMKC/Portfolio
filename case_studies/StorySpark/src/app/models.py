from pydantic import BaseModel, Field, AfterValidator, field_validator
from pydantic.types import StringConstraints
from typing import Optional, Annotated, Any
from datetime import datetime
from fastapi import HTTPException, Path

# ISBN-10 or ISBN-13 simple pattern (loose). Adjust validation as needed.
def strip_hyphens(v: str) -> str:
    return v.replace("-", "")

# TODO:  Figure out how to remove duplicates with both ISBN-10 and ISBN-13
class CleanedISBN(BaseModel):
    isbn: str

    @field_validator("isbn", mode="before")
    def normalize(cls, v: str) -> str:
        if v is None:
            raise ValueError("isbn is required")
        # if not isinstance(v, str):
        #     v = str(v)
        # strip whitespace then remove hyphens
        return v.strip().replace("-", "")

async def isbn_from_path(
    isbn: str = Path(..., example="978-0448487311")
    ) -> CleanedISBN:
    try:
        return CleanedISBN(isbn=isbn)
    except Exception as e:
        raise HTTPException(status_code=422, detail=str(e))

# CleanedISBN = Annotated[
#     str,
#     # TODO:  Figure out how to remove duplicates with both ISBN-10 and ISBN-13
#     # TODO:  With different books using different amount of dashes, the max_length may be more than 17.  Watch out for this.
#     StringConstraints(strip_whitespace=True, min_length=10, max_length=17),
#     AfterValidator(strip_hyphens)
# ]

class AddBookRequest(BaseModel):
    owner: str = Field(..., example="user@gmail.com")
    isbns: list[CleanedISBN] = Field(
        ...,
        description="ISBN-10 or ISBN-13",
        example=[{"isbn": "978-0448487311"}, {"isbn": "978-142311411-6"}]
    )
    # tags: Optional[str] = Field(
    #     None,
    #     example="Train; Gifts; Toys",
    #     description="Optional user-provided text for better embedding.  Semicolon-delimited tags (e.g. Tag1; Tag2; Multi word tag3)"
    # )
    # relevant_text: Optional[str] = Field(
    #     None,
    #     example="This is a story about a train who provides the help needed to deliver another train to the next city over the hill.",
    #     description="Optional user-provided text for better embedding.  We will also fetch text from public sources to augment this."
    #     )

class Book(BaseModel):
    id: str
    owner: str
    isbn: CleanedISBN
    title: str
    authors: list[str]
    last_read: Optional[datetime] = None
    created_at: datetime
    
class RecommendedBook(BaseModel):
    id: str
    owner: str
    isbn: CleanedISBN
    title: str
    authors: list[str]
    relevant_text: str
    last_read: Optional[datetime] = None
    created_at: datetime
    cosine_simularity: float

