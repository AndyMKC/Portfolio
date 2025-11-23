from fastapi import APIRouter
from datetime import datetime, timezone
from google.cloud import bigquery
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
        key = f"{req.owner}:{req.isbn}"
        if id_exists(bigquery_client_helper=bigquery_client_helper, table=source_table_ref, id=key):
            raise Exception(f"Book with isbn {req.isbn} already exists for owner {req.owner}")
    
        # TODO:  add code to fetch title and author
        utc_now = datetime.now(timezone.utc).isoformat()
        entry = {
            "id": key,
            "owner": req.owner,
            "isbn": req.isbn,
            "title": req.title,
            "author": req.author,
            "relevant_text": req.relevant_text,
            "last_read": None,
            "created_at": utc_now
        }

        errors_source = bigquery_client_helper.client.insert_rows_json(
            source_table_ref,
            [entry]
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

def id_exists(bigquery_client_helper: BigQueryClientHelper, table: TableReference, id: str) -> bool:
    table_ref = f"{bigquery_client_helper.project_id}.{bigquery_client_helper.dataset_id}.{bigquery_client_helper.source_table_id}"
    query = f"""
        SELECT
            COUNT(*) as row_count
        FROM
            `{table_ref}`
        WHERE
            id = @id_param
    """

    job_config = bigquery.QueryJobConfig(
        query_parameters=[
            bigquery.ScalarQueryParameter("id_param", "STRING", id)
        ]
    )

    query_job = bigquery_client_helper.client.query(query, job_config=job_config)

    # We should only get a single row with one column
    row = next(query_job.result())
    row_count = row["row_count"]

    return row_count > 0

def retrieve_relevant_text(isbn: str) -> str:
    return f"Relevant text for book with ISBN {isbn}."