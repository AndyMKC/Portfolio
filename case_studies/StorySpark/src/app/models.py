from pydantic import BaseModel, Field, AfterValidator
from pydantic.types import StringConstraints
from typing import Optional, Annotated
from datetime import datetime

# ISBN-10 or ISBN-13 simple pattern (loose). Adjust validation as needed.
def strip_hyphens(v: str) -> str:
    return v.replace("-", "")

CleanedISBN = Annotated[
    str,
    StringConstraints(strip_whitespace=True, min_length=10, max_length=17),
    AfterValidator(strip_hyphens)
]

class AddBookRequest(BaseModel):
    owner: str = Field(..., example="user@gmail.com")
    isbns: Annotated[
        list[CleanedISBN],
        Field(
            description="ISBN-10 or ISBN-13",
            example=["978-0448487311"]
            )
    ]
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
    author: str
    relevant_text: Optional[str] = None
    last_read: Optional[datetime] = None
    created_at: datetime
    
