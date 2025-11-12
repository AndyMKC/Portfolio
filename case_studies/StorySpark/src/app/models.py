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
    title: str = Field(..., example="The Little Engine")
    author: str = Field(..., example="Anonymous")
    owner_id: str = Field(..., example="user@gmail.com")
    book_id: Annotated[
        CleanedISBN,
        Field(description="ISBN-10 or ISBN-13",
              example="978-0448487311")
    ]
    relevant_text: Optional[str] = Field(None, example="Excerpt or relevant passage used for embeddings", description="Optional user-provided text for better embedding.  We will also fetch text from public sources to augment this")

class Book(BaseModel):
    id: str                     # internal UUID
    title: str
    author: str
    owner_id: str
    book_id: str                # ISBN
    relevant_text: str
    created_at: datetime
    updated_at: datetime
    last_read: Optional[datetime] = None
