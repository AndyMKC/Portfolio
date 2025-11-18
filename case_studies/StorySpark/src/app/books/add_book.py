from fastapi import APIRouter
from datetime import datetime, timezone
from google.cloud.bigquery import TableReference
from typing import Dict, Any

from app.models import AddBookRequest, Book
from app.books.bigquery_client_helper import get_bigquery_client, BigQueryClientHelper

router = APIRouter()

@router.post("/books", response_model=Dict[str, Any], status_code=201, operation_id="AddBook")
async def add_book(req: AddBookRequest):
    bigquery_client_helper = get_bigquery_client()

    try:
        source_table_ref = bigquery_client_helper.client.dataset(bigquery_client_helper.dataset_id).table(bigquery_client_helper.source_table_id)

        # TODO:  This may cause the same book to be considered two different entries since one can be ISBN-13 and one can be ISBN-10
        key = f"{req.owner_id}:{req.book_id}"
    
        utc_now = datetime.now(timezone.utc).isoformat()
        entry = {
            "id": key,
            "title": req.title,
            "author": req.author,
            "metadata_text": req.relevant_text,
            "last_read": None,
            "owner_id": req.owner_id,
            "created_at": utc_now,
            "updated_at": utc_now
        }
        
        # TODO:  Check to see if this owner already has this book_id added
        source_rows_to_insert = [entry]

        errors_source = bigquery_client_helper.client.insert_rows_json(
            source_table_ref,
            source_rows_to_insert
        )

        if errors_source:
            raise Exception(f"Errors in source table insert: {errors_source}")

    except Exception as e:
        print(f"An error occurred: {e}")
        return {
            "status": "error",
            "message": str(e)
        }

    return entry

def book_id_exists(bigquery_client_helper: BigQueryClientHelper, table: TableReference, book_id: str) -> bool:
