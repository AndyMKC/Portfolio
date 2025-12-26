from fastapi import APIRouter, Query, Path, Depends
from google.cloud import bigquery
from app.books.helpers.bigquery_client_helper import get_bigquery_client
from app.models import CleanedISBN, isbn_from_path

router = APIRouter()

@router.delete("/books/{isbn}", response_model=None, operation_id="RemoveBook")
async def remove_book(
    owner: str = Query(..., example="user@gmail.com"),
    isbn: CleanedISBN = Depends(isbn_from_path)
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
            bigquery.ScalarQueryParameter("isbn", "STRING", isbn.isbn)
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

