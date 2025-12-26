from fastapi import APIRouter, Query, Path, Depends
from datetime import datetime, timezone
from app.books.helpers.bigquery_client_helper import get_bigquery_client, BigQueryClientHelper
from google.cloud import bigquery
from app.models import CleanedISBN, isbn_from_path

router = APIRouter()

@router.patch("/books/{isbn}/mark_read", response_model=None, operation_id="MarkBookRead")
async def mark_book_read(
    owner: str = Query(..., example="user@gmail.com"),
    isbn: CleanedISBN = Depends(isbn_from_path)
    ):
    """
    Marks a book as read at the current time
    """
    bigquery_client_helper = get_bigquery_client()

    transaction_script = f"""
    BEGIN TRANSACTION;

    UPDATE `{bigquery_client_helper.dataset_id}.{bigquery_client_helper.source_table_id}`
    SET last_read = @last_read
    WHERE owner = @owner AND isbn = @isbn;

    COMMIT TRANSACTION;
    """

    utc_now = datetime.now(timezone.utc)

    job_config = bigquery.QueryJobConfig(
        query_parameters=[
            # Parameters for the source table (Scalar types)
            bigquery.ScalarQueryParameter("owner", "STRING", owner),
            bigquery.ScalarQueryParameter("isbn", "STRING", isbn.isbn),
            bigquery.ScalarQueryParameter("last_read", "TIMESTAMP", utc_now)
        ]
    )

    try:
        query_job = bigquery_client_helper.client.query(transaction_script, job_config=job_config)
        # Waiting on the result means we wait for the COMMIT to finish
        query_job.result()

    except Exception as e:
        print(f"Transaction failed and was rolled back: {e}")
        raise

    return
