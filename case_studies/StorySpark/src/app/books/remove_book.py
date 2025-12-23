from fastapi import APIRouter, Query
#from app.books.add_book import _BOOK_STORE
from app.models import Book
from google.cloud import bigquery
from app.books.bigquery_client_helper import get_bigquery_client, BigQueryClientHelper

router = APIRouter()

@router.delete("/books/{book_id}", response_model=None, operation_id="RemoveBook")
async def remove_book(
    owner: str = Query(..., example="user@gmail.com"),
    isbn: str = Query(..., example="978-0448487311")
    ):
    """
    Remove a book from the user's collection by its ISBN
    """
    bigquery_client_helper = get_bigquery_client()

    transaction_script = f"""
    BEGIN TRANSACTION;

    DELETE FROM `{bigquery_client_helper.dataset_id}.{bigquery_client_helper.source_table_id}`
    WHERE owner = @owner AND isbn = @isbn;

    COMMIT TRANSACTION;
    """

    job_config = bigquery.QueryJobConfig(
        query_parameters=[
            # Parameters for the source table (Scalar types)
            bigquery.ScalarQueryParameter("owner", "STRING", owner),
            bigquery.ScalarQueryParameter("isbn", "STRING", isbn)
        ]
    )

    try:
        query_job = bigquery_client_helper.client.query(transaction_script, job_config=job_config)
        # Waiting on the result means we wait for the COMMIT to finish
        rows = query_job.result()
        for row in rows:
            print(row)

    except Exception as e:
        print(f"Transaction failed and was rolled back: {e}")
        # BigQuery automatically rolls back the entire transaction if an error occurs within the script
        raise # Re-raise the error for upstream handling

    return

