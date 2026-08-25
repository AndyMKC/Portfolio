import logging
from fastapi import APIRouter, Depends
from google.cloud import bigquery
from app.books.helpers.bigquery_client_helper import get_bigquery_client
from app.models import CleanedISBN, isbn_from_path
from app.auth import get_current_user

router = APIRouter()
logger = logging.getLogger("app-log")


@router.delete("/books/{isbn}", response_model=None, operation_id="RemoveBook")
async def remove_book(
    isbn: CleanedISBN = Depends(isbn_from_path),
    current_user: dict = Depends(get_current_user)
    ):
    """
    Remove a book from the authenticated user's collection by its ISBN.
    """
    owner = current_user["email"]
    logger.info(f"RemoveBook called by user: {owner}, isbn: {isbn.isbn}")

    bigquery_client_helper = get_bigquery_client()
    source_table_ref = f"{bigquery_client_helper.project_id}.{bigquery_client_helper.dataset_id}.{bigquery_client_helper.source_table_id}"

    transaction_script = f"""
    BEGIN TRANSACTION;

    DELETE FROM `{source_table_ref}`
    WHERE owner = @owner AND isbn = @isbn;

    COMMIT TRANSACTION;
    """

    job_config = bigquery.QueryJobConfig(
        query_parameters=[
            bigquery.ScalarQueryParameter("owner", "STRING", owner),
            bigquery.ScalarQueryParameter("isbn", "STRING", isbn.isbn)
        ]
    )

    try:
        query_job = bigquery_client_helper.client.query(transaction_script, job_config=job_config)
        # Waiting on the result means we wait for the COMMIT to finish
        query_job.result()

    except Exception as e:
        logger.error(f"RemoveBook transaction failed and was rolled back: {e}")
        raise

    return
