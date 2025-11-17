from fastapi import APIRouter, HTTPException
from datetime import datetime, timezone
import google.auth
from google.cloud import bigquery
from typing import List, Dict, Any

from app.models import AddBookRequest, Book

router = APIRouter()
# # in-memory store for dev; replace with persistent DB later
# _BOOK_STORE: dict[str, Book] = {}

# Placeholder for embedding + vector DB upsert.
# Implement actual embedding generation and BigQuery vector upsert later.
def _enqueue_vector_upsert(book: Book) -> None:
    """
    Placeholder: generate embedding from book.relevant_text and upsert into vector index.
    Implement async background task, Pub/Sub, or direct API call in production.
    """
    # Example:
    # embedding = embed_text(book.relevant_text)
    # bigquery_vector_upsert(namespace=book.owner_id, id=book.book_id, vector=embedding, metadata=...)
    return

@router.post("/books", response_model=Book, status_code=201, operation_id="AddBook")
async def add_book(req: AddBookRequest):
    credentials, project = google.auth.default()

    # TODO:  Read these from environment variables
    # Define the constants for your tables
    PROJECT_ID = "storyspark-5555555"
    DATASET_ID = "storyspark_dataset_dev"
    SOURCE_TABLE_ID = "source_table_books_dev"
    EMBEDDINGS_TABLE_ID = "text_embeddings_books_dev"

    client = bigquery.Client(project=PROJECT_ID)

    try:
        # --- 1. Insert into the Source Table (Metadata) ---
        source_table_ref = client.dataset(DATASET_ID).table(SOURCE_TABLE_ID)
        utc_now = datetime.now(timezone.utc).isoformat()
        source_rows_to_insert = [{
            "id": "sample_book_id",
            "title": "sample_title",
            "author": "sample_author",
            "metadata_text": "Train gifts toys children determination perseverance joy fun laughter holidays delivery",
            "last_read": None,
            "owner_id": "owner_123",
            "created_at": utc_now,
            "updated_at": utc_now
        }]

        errors_source = client.insert_rows_json(
            source_table_ref,
            source_rows_to_insert
        )

        if errors_source:
            raise Exception(f"Errors in source table insert: {errors_source}")

        # --- 2. Insert into the Embeddings Table (Vector Data) ---
        # embeddings_table_ref = client.dataset(DATASET_ID).table(EMBEDDINGS_TABLE_ID)
        # embeddings_rows_to_insert = [{
        #     "book_id": book_id,
        #     "embedding_vector": embedding
        # }]

        # errors_embeddings = client.insert_rows_json(
        #     embeddings_table_ref,
        #     embeddings_rows_to_insert
        # )

        # if errors_embeddings:
        #     raise Exception(f"Errors in embeddings table insert: {errors_embeddings}")

        # return {
        #     "status": "success",
        #     "message": f"Book '{title}' with ID '{book_id}' added successfully to both tables."
        # }

    except Exception as e:
        print(f"An error occurred: {e}")
        # return {
        #     "status": "error",
        #     "message": str(e)
        # }


    # Use provided ISBN as canonical book_id; generate internal UUID id for this record
    # Enforce uniqueness per owner + book_id (ISBN)
    key = f"{req.owner_id}:{req.book_id}"
    # TODO:  Check to see if this owner already has this book_id added

    internal_id = str(req.owner_id + req.book_id)
    utc_now = datetime.now(timezone.utc)
    book = Book(
        id=internal_id,
        title=req.title,
        author=req.author,
        owner_id=req.owner_id,
        book_id=req.book_id,
        relevant_text=req.relevant_text,
        created_at=utc_now,
        updated_at=utc_now,
    )

    # non-blocking background work: enqueue vector upsert (placeholder sync call here)
    try:
        _enqueue_vector_upsert(book)
    except Exception:
        # do not fail the request if embedding/upsert pipeline is temporarily failing
        pass

    return book
