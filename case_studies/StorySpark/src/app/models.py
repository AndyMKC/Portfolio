from pydantic import BaseModel, Field, constr
from pydantic.types import StringConstraints
from typing import Optional, Annotated
from datetime import datetime

# ISBN-10 or ISBN-13 simple pattern (loose). Adjust validation as needed.
CleanedISBN = Annotated[
    str,
    StringConstraints(strip_whitespace=True, min_length=10, max_length=17)
]

class AddBookRequest(BaseModel):
    owner: str = Field(..., example="user@gmail.com")
    isbn: Annotated[
        CleanedISBN,
        Field(
            description="ISBN-10 or ISBN-13",
            example="978-0448487311"
            )
    ]
    title: str = Field(..., example="The Little Engine That Could")
    author: str = Field(..., example="Watty Piper")
    relevant_text: Optional[str] = Field(
        None,
        example="Train gifts toys children determination perseverance joy fun laughter holidays delivery",
        description="Optional user-provided text for better embedding.  We will also fetch text from public sources to augment this"
        )

class Book(BaseModel):
    id: str
    owner: str
    isbn: str                # ISBN
    title: str
    author: str
    relevant_text: str
    last_read: Optional[datetime] = None
    created_at: datetime
    
