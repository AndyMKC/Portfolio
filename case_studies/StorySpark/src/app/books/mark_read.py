import logging
from datetime import datetime, timezone
from fastapi import APIRouter, Depends
from google.cloud import bigquery
from app.books.helpers.bigquery_client_helper import get_bigquery_client
from app.models import CleanedISBN, isbn_from_path
from app.auth import get_current_user

router = APIRouter()
logger = logging.getLogger("app-log")


@router.patch("/books/{isbn}/mark_read", response_model=None, operation_id="MarkBookRead")
async def mark_book_read(
    isbn: CleanedISBN = Depends(isbn_from_path),
    current_user: dict = Depends(get_current_user)
    ):
    """
    Marks a book as read at the current time for the authenticated user.
    """
    owner = current_user["email"]
    logger.info(f"MarkBookRead called by user: {owner}, isbn: {isbn.isbn}")

    bigquery_client_helper = get_bigquery_client()
    source_table_ref = f"{bigquery_client_helper.project_id}.{bigquery_client_helper.dataset_id}.{bigquery_client_helper.source_table_id}"

    transaction_script = f"""
    BEGIN TRANSACTION;

    UPDATE `{source_table_ref}`
    SET last_read = @last_read
    WHERE owner = @owner AND isbn = @isbn;

    COMMIT TRANSACTION;
    """

    utc_now = datetime.now(timezone.utc)

    job_config = bigquery.QueryJobConfig(
        query_parameters=[
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
        logger.error(f"MarkBookRead transaction failed and was rolled back: {e}")
        raise

    return
